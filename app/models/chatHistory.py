from app import db
from datetime import datetime

class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # relasi ke user
    session_id = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)      # pesan user
    response = db.Column(db.Text, nullable=True)      # balasan chatbot
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relasi balik ke User
    user = db.relationship("User", backref=db.backref("chat_histories", lazy=True))
