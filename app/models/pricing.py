# app/models/pricing.py
from app import db

class Pricing(db.Model):
    __tablename__ = "pricing"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    price = db.Column(db.String(50), nullable=False)  # ubah dari Integer ke String
    features = db.Column(db.Text)  # simpan JSON string list
