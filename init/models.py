from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()

# --- USERS & ROLES ---
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100))
    street = db.Column(db.String(100))
    zip_code = db.Column(db.String(20)) 

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20)) 
    balance = db.Column(db.Float, default=0.0) 
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'))
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    role_data = db.relationship('Role', backref='users')
    loans = db.relationship('Loan', backref='user', lazy=True) 

# --- KÖNYVKEZELÉS ---
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    is_borrowable = db.Column(db.Boolean, default=True) 
    copies = db.relationship('BookItem', backref='master_book', lazy='dynamic')

class BookItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    barcode = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='available') 

# --- KÖLCSÖNZÉS & ELŐJEGYZÉS ---
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_item_id = db.Column(db.Integer, db.ForeignKey('book_item.id'))
    loan_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=14))
    extension_count = db.Column(db.Integer, default=0) 
    is_active = db.Column(db.Boolean, default=True)
# --- DÍJ FELSZÁMOLÁS ---    
class Debt(db.Model):
    __tablename__ = 'debts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_paid = db.Column(db.Boolean, default=False)
# --- KÖNYV FOGLALÁS ---
class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    reserved_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

    user = db.relationship('User', backref='reservations_list')
    book = db.relationship('Book', backref='reservations_list')