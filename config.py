import os
from dotenv import load_dotenv

# Load environment variables from .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

class Config:
    # Secrets
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    API_KEY = os.getenv("API_KEY", "my-secure-api-key")
    
    # Basic Auth
    BASIC_AUTH_USERNAME = os.getenv("BASIC_AUTH_USERNAME", "admin")
    BASIC_AUTH_PASSWORD = os.getenv("BASIC_AUTH_PASSWORD", "password")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///chatbot.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail settings
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ("true", "1", "t")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() in ("true", "1", "t")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # 🔹 Tambahan untuk link verifikasi
    BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
