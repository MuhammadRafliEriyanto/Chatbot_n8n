from flask import Blueprint, request, jsonify, url_for, current_app
import requests
import re
import hmac
import hashlib
from app import db, mail
from app.models.user import User
from app.models.chatHistory import ChatHistory
from app.models.order import Order
from app.models.pricing import Pricing
from app.models.chatbot_log import ChatbotLog
from flask_jwt_extended import create_access_token
from flask_mail import Message
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import api_key_required, basic_auth_required
from app.utils.security import (
    hash_password_scrypt,
    verify_password_scrypt,
    generate_confirmation_token,
    confirm_token,
    generate_reset_token,
    confirm_reset_token
)
import json
import time
import uuid
import os
from flask_jwt_extended import create_access_token

auth_user_bp = Blueprint('auth_user', __name__)

# ===== REGISTER USER =====
@auth_user_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()

    # Validasi input wajib
    if not all(k in data for k in ("name", "email", "phone_number", "password")):
        return jsonify({"msg": "Missing required fields"}), 400

    # Cek email dan nomor telepon unik
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already registered"}), 400
    if User.query.filter_by(phone_number=data['phone_number']).first():
        return jsonify({"msg": "Phone number already registered"}), 400

    # Hash password
    hashed_password = hash_password_scrypt(data['password'])

    # Simpan user baru
    new_user = User(
        name=data['name'],
        email=data['email'],
        phone_number=data['phone_number'],
        password_hash=hashed_password,
        is_verified=False
    )
    db.session.add(new_user)
    db.session.commit()

    # Kirim email verifikasi
    token = generate_confirmation_token(data['email'])
    base_url = current_app.config.get("BASE_URL", request.url_root.rstrip('/'))
    confirm_url = f"{base_url}{url_for('auth_user.verify_email', token=token)}"

    html = f"""
        <p>Hi {data['name']},</p>
        <p>Please confirm your email by clicking the link below:</p>
        <p><a href="{confirm_url}">Verify Email</a></p>
    """
    msg = Message("Email Verification", recipients=[data['email']], html=html)
    mail.send(msg)

    return jsonify({"msg": "User registered, please check your email"}), 201

# ===== VERIFY EMAIL =====
@auth_user_bp.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    email = confirm_token(token)
    if not email:
        return jsonify({"msg": "Invalid or expired token"}), 400

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_verified:
        return jsonify({"msg": "Account already verified"}), 200

    user.is_verified = True
    db.session.commit()
    return jsonify({"msg": "Email verified successfully"}), 200

# ===== LOGIN USER =====
@auth_user_bp.route('/login', methods=['POST'])
@api_key_required
@basic_auth_required
def login_user():
    data = request.get_json()
    if not all(k in data for k in ("email", "password")):
        return jsonify({"msg": "Missing email or password"}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not user.is_verified:
        return jsonify({"msg": "Please verify your email before logging in"}), 403

    if verify_password_scrypt(user.password_hash, data['password']):
        # ✅ identity harus string
        token = create_access_token(identity=str(user.id))
        
        # ✅ Buat session_id baru
        session_id = str(uuid.uuid4())

        return jsonify(
            access_token=token,
            session_id=session_id,
            user_id=user.id,
            name=user.name
        ), 200

    return jsonify({"msg": "Invalid credentials"}), 401

# ===== FORGOT PASSWORD =====
@auth_user_bp.route('/forgot-password', methods=['POST'])
@api_key_required
def forgot_password():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"msg": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "If the email is registered, a reset link will be sent"}), 200

    token = generate_reset_token(email)
    base_url = current_app.config.get("BASE_URL", request.url_root.rstrip('/'))
    reset_url = f"{base_url}/reset-password?token={token}"

    html = f"""
        <p>Hi {user.name},</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
    """
    msg = Message("Password Reset Request", recipients=[email], html=html)
    mail.send(msg)

    return jsonify({"msg": "If the email is registered, a reset link will be sent"}), 200

# ===== RESET PASSWORD =====
@auth_user_bp.route('/reset-password', methods=['POST'])
@api_key_required
def reset_password():
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("password")

    if not token or not new_password:
        return jsonify({"msg": "Token and new password are required"}), 400

    email = confirm_reset_token(token)
    if not email:
        return jsonify({"msg": "Invalid or expired token"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.password_hash = hash_password_scrypt(new_password)
    db.session.commit()

    return jsonify({"msg": "Password updated successfully"}), 200

N8N_WEBHOOK_URL = "https://n8n.gitstraining.com/webhook/chatbotgenius"

@auth_user_bp.route('/chatbot', methods=['POST'])
@jwt_required()
def chat_with_bot():
    data = request.get_json()
    message = data.get("message")
    
    if not message:
        return jsonify({"msg": "Message is required"}), 400

    # Ambil identity dari JWT
    identity = get_jwt_identity()
    user_id = int(identity)

    # Cek apakah session_id dikirim, jika tidak buat baru
    session_id = data.get("session_id")
    if not session_id:
        # Bisa juga ambil session_id terakhir dari DB jika ingin konsisten
        session_id = str(uuid.uuid4())

    bot_response = "No response"
    try:
        # Kirim ke N8N sesuai format yang workflow harapkan
        resp = requests.post(
            N8N_WEBHOOK_URL,
            json={
                "chatInput": message,   # field wajib
                "sessionId": session_id  # pastikan huruf besar "I"
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if resp.ok:
            try:
                resp_json = resp.json()
                # ambil message dari N8N
                bot_response = resp_json.get("message") or resp_json.get("reply") or "No response"
            except ValueError:
                bot_response = resp.text
        else:
            bot_response = f"Webhook returned {resp.status_code}: {resp.text}"

    except Exception as e:
        bot_response = f"Error connecting to webhook: {e}"

    # Simpan chat history di DB MySQL
    chat = ChatHistory(
        user_id=user_id,
        session_id=session_id,
        message=message,
        response=bot_response
    )
    db.session.add(chat)
    db.session.commit()

    return jsonify({
        "session_id": session_id,
        "user_id": user_id,
        "message": message,
        "response": bot_response
    }), 200
    
    
GUEST_LIMIT = 10  # maksimal 5x chat per session_id

@auth_user_bp.route('/chatbot/guest', methods=['POST'])
def chat_with_bot_guest():
    data = request.get_json()
    message = data.get("message")
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not message:
        return jsonify({"msg": "Message is required"}), 400

    bot_response = "No response"
    try:
        resp = requests.post(
            N8N_WEBHOOK_URL,
            json={"chatInput": message, "session_id": session_id, "user_id": "guest"},
            headers={"Content-Type": "application/json"},
            timeout=100
        )
        if resp.ok:
            try:
                resp_json = resp.json()
                bot_response = (
                    resp_json.get("message")
                    or resp_json.get("reply")
                    or "No response"
                )
            except ValueError:
                bot_response = resp.text
        else:
            bot_response = f"Webhook returned {resp.status_code}: {resp.text}"

    except Exception as e:
        bot_response = f"Error connecting to webhook: {e}"

    # simpan ke DB → user_id default untuk guest
    chat = ChatHistory(
        user_id=300,   # 👈 guest pakai 0
        session_id=session_id,
        message=message,
        response=bot_response
    )
    db.session.add(chat)
    db.session.commit()

    return jsonify({
        "session_id": session_id,
        "user_id": "guest",
        "message": message,
        "response": bot_response
    }), 200 
    
# ================= Pricing =================
@auth_user_bp.route('/pricing', methods=['GET'])
def get_pricing():
    plans = Pricing.query.all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "price": f"Rp {p.price:,.0f}".replace(",", "."),
            "raw_price": p.price,  # tambahkan juga harga mentah (opsional)
            "features": json.loads(p.features) if p.features else []
        } for p in plans
    ]), 200

# ================= Helper =================
def format_rupiah(amount: int) -> str:
    """Format integer menjadi Rupiah string: 250000 -> Rp250.000"""
    return f"Rp{amount:,}".replace(",", ".")

# ================= Checkout user login =================
@auth_user_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    data = request.get_json()
    plan_id = data.get("plan_id")

    plan = Pricing.query.get(plan_id)
    if not plan:
        return jsonify({"msg": "Invalid plan"}), 400

    user_id = int(get_jwt_identity())
    order_id = f"ORDER-{user_id}-{int(time.time())}"

    # Parsing harga untuk Duitku (hapus Rp, koma, spasi)
    try:
        cleaned_price = re.sub(r'[^0-9]', '', str(plan.price))
        payment_amount = int(cleaned_price)

        if payment_amount < 10000:
            return jsonify({"msg": "Plan price must be at least 10,000 IDR"}), 400
    except Exception as e:
        return jsonify({"msg": f"Invalid plan price format: {plan.price} ({str(e)})"}), 400

    # Simpan order di DB tetap format Rp
    new_order = Order(
        order_id=order_id,
        user_id=user_id,
        plan_name=plan.name,
        amount=plan.price,  # VARCHAR, tetap "Rp250.000"
        status="pending"
    )
    db.session.add(new_order)
    db.session.commit()

    # Payload Duitku
    merchant_code = current_app.config['DUITKU_MERCHANT_CODE']
    api_key = current_app.config['DUITKU_API_KEY']
    payment_url = current_app.config['DUITKU_PAYMENT_URL']

    signature_str = merchant_code + order_id + str(payment_amount) + api_key
    signature = hashlib.md5(signature_str.encode('utf-8')).hexdigest()

    payload = {
        "merchantCode": merchant_code,
        "paymentAmount": payment_amount,
        "paymentMethod": "VC",
        "merchantOrderId": order_id,
        "productDetails": plan.name,
        "email": "user@example.com",
        "phoneNumber": "08123456789",
        "customerVaName": "Dapin",
        "callbackUrl": f"{current_app.config['BASE_URL']}/api/auth/duitku/callback",
        "returnUrl": f"{current_app.config['BASE_URL']}/payment-success",
        "signature": signature,
        "expiryPeriod": 60
    }

    try:
        resp = requests.post(payment_url, json=payload, timeout=30)
        resp_json = resp.json()
    except Exception as e:
        return jsonify({"msg": f"Error connecting to Duitku: {str(e)}"}), 500

    if resp.status_code == 200 and resp_json.get("statusCode") == "00":
        return jsonify({
            "order_id": new_order.order_id,
            "user_id": new_order.user_id,
            "plan_name": new_order.plan_name,
            "amount": new_order.amount,  # tetap string Rp
            "status": new_order.status,
            "payment_url": resp_json.get("paymentUrl")
        }), 200
    else:
        return jsonify({"msg": "Failed to create payment", "response": resp_json}), 400

# ================= Checkout guest =================
@auth_user_bp.route('/checkout/guest', methods=['POST'])
def guest_checkout():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    plan_name = data.get('plan_name')
    amount_str = data.get('amount')  # misal "Rp250.000"

    if not all([name, email, plan_name, amount_str]):
        return jsonify({"msg": "Missing required fields"}), 400

    try:
        cleaned_amount = re.sub(r'[^0-9]', '', str(amount_str))
        payment_amount = int(cleaned_amount)

        if payment_amount < 10000:
            return jsonify({"msg": "Plan price must be at least 10,000 IDR"}), 400
    except Exception as e:
        return jsonify({"msg": f"Invalid amount format: {amount_str} ({str(e)})"}), 400

    order_id = f"ORDER-GUEST-{int(datetime.now().timestamp())}"

    signature = hashlib.md5(
        f"{os.getenv('DUITKU_MERCHANT_CODE')}{order_id}{payment_amount}{os.getenv('DUITKU_API_KEY')}".encode()
    ).hexdigest()

    payload = {
        "merchantCode": os.getenv("DUITKU_MERCHANT_CODE"),
        "paymentAmount": payment_amount,
        "merchantOrderId": order_id,
        "productDetails": plan_name,
        "email": email,
        "callbackUrl": "https://yourdomain.com/api/auth/duitku/callback",
        "returnUrl": "https://yourdomain.com/payment/success",
        "signature": signature
    }

    try:
        resp = requests.post(os.getenv("DUITKU_PAYMENT_URL"), json=payload,
                             headers={"Content-Type": "application/json"}, timeout=30)
        res_data = resp.json()
    except Exception as e:
        return jsonify({"msg": f"Error connecting to Duitku: {str(e)}"}), 500

    if resp.status_code == 200 and "paymentUrl" in res_data:
        order = Order(
            order_id=order_id,
            plan_name=plan_name,
            email=email,
            amount=amount_str,  # tetap Rp di DB
            status="pending"
        )
        db.session.add(order)
        db.session.commit()

        return jsonify({
            "payment_url": res_data["paymentUrl"],
            "order_id": order_id,
            "status": "pending",
            "amount": order.amount  # selalu "Rp250.000"
        })
    else:
        return jsonify({"msg": "Failed to create guest payment", "response": res_data}), 400

# ================= Orders History =================
@auth_user_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = int(get_jwt_identity())
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify([
        {
            "order_id": o.order_id,
            "plan_name": o.plan_name,
            "amount": o.amount,
            "status": o.status,
            "created_at": o.created_at.isoformat()
        } for o in orders
    ]), 200

# ================= Chatbot =================
@auth_user_bp.route('/chatbot/upload', methods=['POST'])
@jwt_required()
def chatbot_upload():
    data_name = request.form.get("name")
    file = request.files.get("file")

    if not data_name or not file:
        return jsonify({"msg": "Name and file are required"}), 400

    # Buat folder uploads kalau belum ada
    upload_folder = os.path.join(current_app.root_path, "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # Simpan file
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    # URL file (pastikan /uploads di-serve static)
    file_url = f"/uploads/{filename}"

    # Simpan ke DB
    log = ChatbotLog(
        name=data_name,
        file_url=file_url
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "id": log.id,
        "name": log.name,
        "file_url": log.file_url,
        "created_at": log.created_at.isoformat()
    }), 201
