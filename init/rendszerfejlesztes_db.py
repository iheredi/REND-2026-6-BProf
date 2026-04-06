#magamnak futtatáshoz:
# $env:FLASK_APP = "rendszerfejlesztes_db.py"
# py -m flask db init
# py -m flask db migrate -m "Minden tabla letrehozasa"
# py -m flask db upgrade

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bibliotar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- USERS & ROLES ---
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False) # admin = 1 , librarian = 2, user = 3

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
        """Jelszó hash-elése és mentése."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Jelszó ellenőrzése a belépésnél."""
        return check_password_hash(self.password_hash, password)
    
    # Kapcsolatok
    loans = db.relationship('Loan', backref='user', lazy=True) 

# --- KÖNYVKEZELÉS ---
class Book(db.Model):
    """ A könyv általános adatai ebből csinálunk majd többet a BookItem táblába """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    is_borrowable = db.Column(db.Boolean, default=True) 
    
    copies = db.relationship('BookItem', backref='master_book', lazy='dynamic')

class BookItem(db.Model):
    """ Fizikai példányok ezek vannak példányosítva a Book táblából"""
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    barcode = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='available') 

# --- KÖLCSÖNZÉS ÉS BÍRSÁGOK ---
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_item_id = db.Column(db.Integer, db.ForeignKey('book_item.id'))
    loan_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=14))
    extension_count = db.Column(db.Integer, default=0) # Max 2 alkalommal lehet hosszabbítani 
    is_active = db.Column(db.Boolean, default=True)

# --- TARTOZÁSOK ÉS BÍRSÁGOK ---
class Debt(db.Model):
    __tablename__ = 'debts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=True) # Opcionális, ha kölcsönzéshez kötődik.Ha késedelmi díj akkor loan.id-t hozzá kell kötni a loan_id-hoz
    
    amount = db.Column(db.Float, nullable=False) # A tartozás összege
    reason = db.Column(db.String(255)) # Pl: "Késedelmi díj: Egri Csillagok", "Rongálás" ha késedelmi díj akkor loan.id-t hozzá kell kötni a loan_id-hoz
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_paid = db.Column(db.Boolean, default=False) # Kifizette-e már?
if __name__ == '__main__':
    app.run(debug=True)

# --- ELŐJEGYZÉSEK ---
class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    reserved_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Státusz: 'active' (vár), 'fulfilled' (kiszolgálva), 'cancelled' (visszavonva)
    status = db.Column(db.String(20), default='active')

    # Kapcsolatok a könnyebb lekérdezéshez
    user = db.relationship('User', backref='reservations')
    book = db.relationship('Book', backref='reservations')    