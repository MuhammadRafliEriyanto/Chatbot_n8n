from app import db
import datetime

class ChatbotLog(db.Model):
    __tablename__ = "chatbot_logs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # nama user atau pengirim
    file_url = db.Column(db.String(255), nullable=False)  # path/URL dokumen yang diupload
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
