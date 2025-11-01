from app import db
from datetime import datetime

class Broadcast(db.Model):
    __tablename__ = "broadcast"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # relasi ke User
    nomor = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum("pending", "sent", "failed"), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)

    # relasi SQLAlchemy
    user = db.relationship('User', back_populates='broadcasts')

    def __repr__(self):
        return f"<Broadcast {self.id} - {self.nomor} ({self.status})>"
