# ===== app/__init__.py =====
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()
oauth = OAuth()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # ✅ Set secret_key supaya session berjalan untuk CSRF state
    app.secret_key = app.config['SECRET_KEY']

    # Init ekstensi
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Import models
    from app.models import user, admin

    # Register blueprints
    from app.routes.auth_admin import auth_admin_bp
    from app.routes.auth_user import auth_user_bp
    app.register_blueprint(auth_admin_bp, url_prefix='/api/admin')
    app.register_blueprint(auth_user_bp, url_prefix='/api/user')

    # Root
    @app.route('/')
    def home():
        return "Chatbot Flask app is running!"

    return app
