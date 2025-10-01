from flask import Blueprint, request, jsonify, url_for, current_app
import requests
from app import db, mail
from app.models.user import User
from app.models.chatHistory import ChatHistory
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
import uuid
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

N8N_WEBHOOK_URL = "https://n8n.gitstraining.com/webhook/chatbotcb"

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
