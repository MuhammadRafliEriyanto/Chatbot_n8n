import os
import base64
import hashlib
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# ===== Password Hashing (Scrypt) =====
def hash_password_scrypt(password: str) -> str:
    """Hash password admin menggunakan Scrypt."""
    salt = os.urandom(16)
    key = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=64
    )
    return "scrypt:" + base64.b64encode(salt).decode() + '$' + base64.b64encode(key).decode()

def verify_password_scrypt(stored_password: str, provided_password: str) -> bool:
    """Verifikasi password admin dengan hash yang disimpan."""
    if stored_password.startswith("scrypt:"):
        stored_password = stored_password[len("scrypt:"):]
    salt_b64, key_b64 = stored_password.split('$')
    salt = base64.b64decode(salt_b64)
    key = base64.b64decode(key_b64)

    new_key = hashlib.scrypt(
        provided_password.encode('utf-8'),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=64
    )
    return new_key == key

# ===== Email Verification Token =====
def generate_confirmation_token(email: str) -> str:
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="admin-email-confirmation-salt")

def confirm_token(token: str, expiration: int = 3600):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return s.loads(token, salt="admin-email-confirmation-salt", max_age=expiration)
    except (SignatureExpired, BadSignature):
        return None

# ===== Password Reset Token =====
def generate_reset_token(email: str) -> str:
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="admin-password-reset-salt")

def confirm_reset_token(token: str, expiration: int = 3600):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return s.loads(token, salt="admin-password-reset-salt", max_age=expiration)
    except (SignatureExpired, BadSignature):
        return None
