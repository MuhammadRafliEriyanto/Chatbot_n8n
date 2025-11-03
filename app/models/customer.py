from app import db

class Customer(db.Model):
    __tablename__ = 'customer'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nomer = db.Column(db.String(20), nullable=False)

    # relasi ke User
    user = db.relationship('User', backref=db.backref('customers', cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Customer {self.id} - {self.nomer}>"
