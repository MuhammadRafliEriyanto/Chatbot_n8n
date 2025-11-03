from flask import Blueprint, request, jsonify, url_for
from app import db, mail
from sqlalchemy import func
from app.models.admin import Admin
from app.models.user import User
from app.models.order import Order  # pastikan sudah ada model Order
from app.models.customer import Customer  
from app.models.broadcast import Broadcast
from flask_jwt_extended import create_access_token, jwt_required
from flask_mail import Message
from app.utils.decorators import api_key_required, basic_auth_required
from app.utils.security_admin import (
    hash_password_scrypt,
    verify_password_scrypt,
    generate_confirmation_token,
    confirm_token
)

from app.models.chatHistory import ChatHistory
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity


auth_admin_bp = Blueprint('auth_admin', __name__)

# =============================
# REHISTER ADMIN 
# =============================
@auth_admin_bp.route('/register', methods=['POST'])
def register_admin():
    data = request.get_json()

    if Admin.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already registered"}), 400

    # Hash password admin pakai Scrypt
    hashed_password = hash_password_scrypt(data['password'])

    new_admin = Admin(
        name=data['name'],
        email=data['email'],
        password_hash=hashed_password,
        is_verified=False,
        role=data.get("role", "admin")   # ✅ default role = admin
    )

    db.session.add(new_admin)
    db.session.commit()

    # Kirim email verifikasi...
    try:
        token = generate_confirmation_token(data['email'])
        confirm_url = url_for('auth_admin.verify_email_admin', token=token, _external=True)

        html = f"""
        <p>Hi {data['name']},</p>
        <p>Akun admin Anda berhasil dibuat. Klik link di bawah ini untuk verifikasi:</p>
        <p><a href="{confirm_url}">Verifikasi Email</a></p>
        <p>Link ini berlaku 1 jam.</p>
        """

        msg = Message(
            subject="Verifikasi Akun Admin",
            recipients=[data['email']],
            html=html
        )
        mail.send(msg)

    except Exception as e:
        return jsonify({
            "msg": "Admin registered, but failed to send verification email",
            "error": str(e)
        }), 201

    return jsonify({"msg": "Admin registered successfully. Please check your email to verify your account."}), 201

# =============================
# ADMIN LOGIN
# =============================
@auth_admin_bp.route('/login', methods=['POST'])
@api_key_required
@basic_auth_required
def login_admin():
    data = request.get_json()
    admin = Admin.query.filter_by(email=data['email']).first()
    
    if admin and verify_password_scrypt(admin.password_hash, data['password']):
        if not admin.is_verified:
            return jsonify({"msg": "Please verify your email before login"}), 403

        # ✅ identity = ID admin, claims = type + role
        access_token = create_access_token(
            identity=str(admin.id),
            additional_claims={
                "type": "admin",
                "role": admin.role
            }
        )
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Invalid credentials"}), 401

# =============================
# VERIFTOKEN ADMIN
# =============================
@auth_admin_bp.route('/verify/<token>', methods=['GET'])
def verify_email_admin(token):
    email = confirm_token(token)
    if not email:
        return jsonify({"msg": "Invalid or expired token"}), 400

    admin = Admin.query.filter_by(email=email).first()
    if not admin:
        return jsonify({"msg": "Admin not found"}), 404

    if admin.is_verified:
        return jsonify({"msg": "Account already verified"}), 200

    admin.is_verified = True
    db.session.commit()
    return jsonify({"msg": "Admin email verified successfully"}), 200


# =============================
# VERIFEMAIL RESEND ADMIN *jika link kadaluarsa*
# =============================
@auth_admin_bp.route('/resend-verification/<int:admin_id>', methods=['POST'])
@jwt_required()
def resend_verification(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    if admin.is_verified:
        return jsonify({"msg": "Admin already verified"}), 400

    token = generate_confirmation_token(admin.email)
    confirm_url = url_for('auth_admin.verify_email_admin', token=token, _external=True)
    html = f"<p>Hi {admin.name}, klik link untuk verifikasi: <a href='{confirm_url}'>Verifikasi Email</a></p>"

    msg = Message("Email Verification", recipients=[admin.email], html=html)
    mail.send(msg)

    return jsonify({"msg": "Verification email resent"}), 200

# =============================
# AMBIL DATA USERS PENGGUNA
# =============================
@auth_admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "is_verified": u.is_verified
        } for u in users
    ]), 200

# =============================
# AMBIL DATA HISTORI CHATS
# =============================
@auth_admin_bp.route('/chats', methods=['GET'])
@jwt_required()
def get_all_chats():
    claims = get_jwt()

    # ✅ cek role
    if claims.get("type") != "admin":
        return jsonify({"msg": "Admins only"}), 403

    if claims.get("role") not in ["admin", "superadmin"]:
        return jsonify({"msg": "Forbidden"}), 403

    # ✅ langsung pakai relasi, ga perlu manual join
    chats = ChatHistory.query.order_by(ChatHistory.created_at.desc()).all()

    return jsonify([
        {
            "id": c.id,
            "user_id": c.user_id,
            "user_name": c.user.name if c.user else None,  # ✅ ambil nama user
            "session_id": c.session_id,
            "message": c.message,
            "response": c.response,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for c in chats
    ]), 200

# =============================
# AMBIL DATA chats per tanggal Total chat per tanggal (OPSIONAL)
# =============================
@auth_admin_bp.route("/chats/per-day", methods=["GET"])
def chats_per_day():
    results = (
        db.session.query(
            func.date(ChatHistory.created_at).label("tanggal"),
            func.count(ChatHistory.id).label("total_chat")
        )
        .group_by(func.date(ChatHistory.created_at))
        .order_by(func.date(ChatHistory.created_at))
        .all()
    )

    data = [
        {"tanggal": str(r.tanggal), "total_chat": r.total_chat}
        for r in results
    ]
    return jsonify(data)

# =============================
# AMBIL DATA chats per jam Total chat per jam (OPSIONAL)
# =============================
@auth_admin_bp.route("/chats/per-hour", methods=["GET"])
def chats_per_hour():
    results = (
        db.session.query(
            func.extract("hour", ChatHistory.created_at).label("jam"),
            func.count(ChatHistory.id).label("total_chat")
        )
        .group_by("jam")
        .order_by("jam")
        .all()
    )

    data = [
        {"jam": int(r.jam), "total_chat": r.total_chat}
        for r in results
    ]
    return jsonify(data)

# =============================
# AMBIL DATA chats Perbandingan chat dari tamu & user terdaftar (OPSIONAL)
# =============================
@auth_admin_bp.route("/chats/guest-vs-registered", methods=["GET"])
def guest_vs_registered():
    results = (
        db.session.query(
            User.is_verified, 
            func.count(ChatHistory.id).label("total_chat")
        )
        .join(User, User.id == ChatHistory.user_id)
        .group_by(User.is_verified)
        .all()
    )

    data = [
        {
            "kategori": "Registered" if r.is_verified else "Guest",
            "total_chat": r.total_chat
        }
        for r in results
    ]
    return jsonify(data)

# =============================
# AMBIL DATA customer wa 
# =============================
@auth_admin_bp.route("/customer/wa", methods=["GET"])
def get_customer():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer;")
    rows = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()

    data = [dict(zip(colnames, row)) for row in rows]
    return jsonify(data)

# =============================
# AMBIL DATA histori wa 
# =============================
@auth_admin_bp.route("/history/wa", methods=["GET"])
def get_history():
    conn = get_connection()
    cursor = conn.cursor()

    # 🔹 Join history_wa dengan customer
    cursor.execute("""
        SELECT 
            h.id, 
            h.session_id, 
            h.message, 
            h.created_at,
            c.customer_id AS customer_id,
            c.nama AS customer_name,
            c.email AS customer_email,
            c.nomor AS customer_phone
        FROM history_wa h
        LEFT JOIN customer c ON h.customer_id = c.customer_id
        ORDER BY h.session_id, h.id
    """)
    
    rows = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()

    data = [dict(zip(colnames, row)) for row in rows]

    # 🔹 Group by session_id
    grouped = {}
    for row in data:
        session_id = row["session_id"]
        if session_id not in grouped:
            grouped[session_id] = {
                "session_id": session_id,
                "customer": {
                    "customer_id": row["customer_id"],
                    "nama": row["customer_name"],
                    "email": row["customer_email"],
                    "phone": row["customer_phone"]
                },
                "history": []
            }
        grouped[session_id]["history"].append({
            "id": row["id"],
            "message": row["message"],
            "created_at": row["created_at"]
        })

    return jsonify(list(grouped.values()))


# =============================
# Admin mengirim pesan broadcast ke banyak customer
# =============================
@auth_admin_bp.route("/broadcast/add", methods=["POST"])
def add_broadcast():
    data = request.get_json()
    customer_ids = data.get("customer_ids", [])
    message = data.get("message")

    if not customer_ids:
        return jsonify({"success": False, "message": "Customer harus dipilih"}), 400

    # 🔹 ambil data nomor dari Supabase (pakai psycopg2 atau raw connection tetap)
    conn_supabase = get_connection()  
    cursor_supa = conn_supabase.cursor()
    cursor_supa.execute(
        "SELECT customer_id, nomor FROM customer WHERE customer_id IN %s",
        (tuple(customer_ids),)
    )
    customers = cursor_supa.fetchall()
    cursor_supa.close()
    conn_supabase.close()

    # 🔹 simpan ke MySQL (pakai SQLAlchemy ORM)
    ids = []
    try:
        for cust in customers:
            customer_id, nomor = cust
            new_broadcast = Broadcast(
                nomor=nomor,
                message=message,
                status="pending"
            )
            db.session.add(new_broadcast)
            db.session.flush()   # supaya bisa ambil id sebelum commit
            ids.append(new_broadcast.id)

        db.session.commit()

        return jsonify({
            "success": True,
            "broadcast_ids": ids,
            "message": "Broadcast berhasil disimpan ke MySQL (status pending)"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# =============================
# ADMIN AMBIL DATA BROADCAST
# =============================
@auth_admin_bp.route("/broadcast", methods=["GET"])
def get_broadcasts():
    # Ambil query param status (default pending)
    status = request.args.get("status", "pending")

    try:
        broadcasts = Broadcast.query.filter_by(status=status).all()

        result = []
        for b in broadcasts:
            result.append({
                "id": b.id,
                "nomor": b.nomor,
                "message": b.message,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "sent_at": b.sent_at.isoformat() if b.sent_at else None
            })

        return jsonify({
            "success": True,
            "count": len(result),
            "broadcasts": result
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

# =============================
# ADMIN AMBIL DATA semua order dari semua user.
# =============================    
@auth_admin_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_all_orders():
    claims = get_jwt()
    if claims.get("type") != "admin":
        return jsonify({"msg": "Admins only"}), 403

    status = request.args.get("status")
    query = db.session.query(Order).join(User, User.id == Order.user_id)

    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify([
        {
            "order_id": o.order_id,
            "user_name": o.user.name if o.user else None,
            "amount": o.amount,
            "status": o.status,
            "created_at": o.created_at.isoformat()
        }
        for o in orders
    ]), 200

# =============================
# ADMIN AMBIL DATA daftar customer milik user tertentu..
# =============================  
@auth_admin_bp.route('/users/<int:user_id>/customers', methods=['GET'])
@jwt_required()
def get_customers_by_user(user_id):
    claims = get_jwt()
    if claims.get("type") != "admin":
        return jsonify({"msg": "Admins only"}), 403

    customers = Customer.query.filter_by(user_id=user_id).all()
    return jsonify([
        {"id": c.id, "nomer": c.nomer}
        for c in customers
    ]), 200

# =============================
# ADMIN AMBIL DATA semua broadcast yang dibuat oleh user tertentu
# =============================  
@auth_admin_bp.route('/users/<int:user_id>/broadcasts', methods=['GET'])
@jwt_required()
def get_broadcasts_by_user(user_id):
    claims = get_jwt()
    if claims.get("type") != "admin":
        return jsonify({"msg": "Admins only"}), 403

    broadcasts = Broadcast.query.filter_by(user_id=user_id).order_by(Broadcast.created_at.desc()).all()
    return jsonify([
        {
            "id": b.id,
            "nomor": b.nomor,
            "message": b.message,
            "status": b.status,
            "created_at": b.created_at.isoformat()
        }
        for b in broadcasts
    ]), 200
   