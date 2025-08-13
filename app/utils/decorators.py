import hashlib
import os
import base64
from functools import wraps
from flask import request, jsonify

# 🔐 Hash password dengan scrypt
def hash_password_scrypt(password: str) -> str:
    salt = os.urandom(16)
    hashed = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=16384,
        r=8,
        p=1
    )
    # simpan salt dan hash jadi satu string (dipisahkan tanda $)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(hashed).decode()

# 🔐 Verifikasi password
def verify_password_scrypt(password: str, stored: str) -> bool:
    try:
        salt_b64, hash_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        stored_hash = base64.b64decode(hash_b64)

        new_hash = hashlib.scrypt(
            password.encode('utf-8'),
            salt=salt,
            n=16384,
            r=8,
            p=1
        )
        return new_hash == stored_hash
    except Exception:
        return False


# 🔒 Contoh decorator API key
def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if api_key != "your_api_key":
            return jsonify({"error": "Invalid API Key"}), 401
        return f(*args, **kwargs)
    return decorated_function


# 🔒 Contoh decorator Basic Auth
def basic_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == 'admin' and auth.password == 'secret'):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function
