# app/models/order.py
from app import db
import datetime

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_name = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.String(50), nullable=False)  # ubah dari Integer ke String
    status = db.Column(db.String(20), default="pending")  # pending/paid/failed
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship("User", backref="orders")
