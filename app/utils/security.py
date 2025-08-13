import os
import base64
import hashlib
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# ===== Password Hashing =====
def hash_password_scrypt(password):
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

def verify_password_scrypt(stored_password, provided_password):
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
def generate_confirmation_token(email):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="email-confirmation-salt")

def confirm_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return s.loads(token, salt="email-confirmation-salt", max_age=expiration)
    except Exception:
        return False

# ===== Password Reset Token =====
def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="password-reset-salt")

def confirm_reset_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return s.loads(token, salt="password-reset-salt", max_age=expiration)
    except (SignatureExpired, BadSignature):
        return None
