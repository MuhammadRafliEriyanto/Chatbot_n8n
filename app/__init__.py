from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_mail import Mail

# Load .env first
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()  # 🔹 Tambahan

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)  # 🔹 Tambahan
    CORS(app)

    # 🔥 Import semua model agar Flask-Migrate tahu tabel mana yang harus dibuat
    from app.models import user, admin

    # ✅ Register routes
    from app.routes.auth_admin import auth_admin_bp
    from app.routes.auth_user import auth_user_bp

    app.register_blueprint(auth_admin_bp, url_prefix='/api/admin')
    app.register_blueprint(auth_user_bp, url_prefix='/api/user')
    
      # 🔹 Tambahkan route root untuk health check
    @app.route('/')
    def home():
        return "Chatbot Flask app is running!"

    return app
