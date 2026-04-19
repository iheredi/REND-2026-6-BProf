#Na ezzel hozzuk létre a db-be az adatokat ha elrontod a db-t akkor is csak ezt lefuttatod és 
#újra helyreáll a db-d állapota 
import os
import sys 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from app import app, db, Role, User, Address, Book, BookItem, Loan, Debt, Reservation
from datetime import datetime, timedelta

def seed_data():
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    # 'sqlite:///...' formátumból kinyerjük a mappa útvonalát
        db_path = db_uri.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)

        # Ha nem létezik a mappa (backend/instance), létrehozzuk, különben hiba lesz
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"Mappa létrehozva: {db_dir}")
        # Tisztítás az újrakezdéshez
        db.drop_all()
        db.create_all()

        # 1. SZEREPKÖRÖK
        admin_r = Role(name='admin')
        lib_r = Role(name='librarian')
        user_r = Role(name='user')
        db.session.add_all([admin_r, lib_r, user_r])
        db.session.commit()

        # 2. CÍMEK
        addr1 = Address(city="Veszprém", street="Egyetem utca 10.", zip_code="8200")
        addr2 = Address(city="Budapest", street="Múzeum körút 14.", zip_code="1088")
        db.session.add_all([addr1, addr2])
        db.session.commit()

        # 3. FELHASZNÁLÓK (Regisztrált felhasználók, könyvtárosok, adminok)
        u_admin = User(email="admin@bibliotar.hu",name="Főnök András", phone="061111111", role_id=admin_r.id, address_id=addr1.id)
        u_admin.set_password("admin123")

        u_lib = User(email="konyvtaros@bibliotar.hu",name="Példa Géza", phone="062222222", role_id=lib_r.id, address_id=addr2.id)
        u_lib.set_password("jelszo123")

        u_olvaso1 = User(email="kiss.pista@freemail.hu",name="Kiss Pista", phone="06305554433", role_id=user_r.id, address_id=addr1.id, balance=1200.0)
        u_olvaso1.set_password("jelszo123")

        u_olvaso2 = User(email="nagy.eva@gmail.com",name="Nagy Éva", phone="06708889900", role_id=user_r.id, address_id=addr2.id, balance=0.0)
        u_olvaso2.set_password("jelszo123")

        u_olvaso3 = User(email="teszt.elek@citromail.hu",name="Teszt Elek", phone="06201112233", role_id=user_r.id, address_id=addr1.id, balance=5500.0)
        u_olvaso3.set_password("jelszo123")

        u_olvaso4 = User(email="pelda.geza@gmail.com",name="Példa Géza", phone="06203349406", role_id=user_r.id, address_id=addr2.id, balance=0.0)
        u_olvaso4.set_password("jelszo123")

        u_olvaso5 = User(email="semmikozodhozza@gmail.com",name="Savanyú Zsuzsanna Éva", phone="06708459230", role_id=user_r.id, address_id=addr2.id, balance=0.0)
        u_olvaso5.set_password("jelszo123")

        db.session.add_all([u_admin, u_lib, u_olvaso1, u_olvaso2, u_olvaso3,u_olvaso4,u_olvaso5])
        db.session.commit()

        # 4. KÖNYVEK (Katalógus adatok és kölcsönözhetőség beállítása)
        books = [
            Book(title="Egri csillagok", author="Gárdonyi Géza", is_borrowable=True),
            Book(title="Rendszerfejlesztés Haladó Módszerei", author="Dr. Technika", is_borrowable=True),
            Book(title="Python alapok", author="Guido van Rossum", is_borrowable=True),
            Book(title="A kőszívű ember fiai", author="Jókai Mór", is_borrowable=True),
            Book(title="Ritka Kódex (Nem kölcsönözhető)", author="Ismeretlen", is_borrowable=False) 
        ]
        db.session.add_all(books)
        db.session.commit()

        # 5. PÉLDÁNYOK (Fizikai állapotok: ép, sérült, elveszett) 
        """items = [
            BookItem(book_id=books[0].id, barcode="BC-001", status="available"), 
            BookItem(book_id=books[0].id, barcode="BC-002", status="borrowed"),  
            BookItem(book_id=books[1].id, barcode="BC-003", status="borrowed"),  
            BookItem(book_id=books[2].id, barcode="BC-004", status="damaged"),   
            BookItem(book_id=books[3].id, barcode="BC-005", status="lost"),      
            BookItem(book_id=books[4].id, barcode="BC-006", status="available")  
        ]"""
        
        items = []
        for i in range(5):
            target_book = books[i]
            # 6 példány
            for j in range(1, 7):
                # Vonalkód generálás
                barcode = f"BC-BK{target_book.id}-{j}"
                
                
                status = "available"
                if j == 1: status = "borrowed"
                if j == 2: status = "damaged"
                
                new_item = BookItem(
                    book_id=target_book.id, 
                    barcode=barcode, 
                    status=status
                )
                items.append(new_item)

        
        db.session.add_all(items)
        db.session.commit()

        # 6. KÖLCSÖNZÉSEK (Hosszabbítások és előzmények) 
        now = datetime.utcnow()
        loans = [
            # Aktív kölcsönzés, már 2x hosszabbítva (többször nem lehet!) 
            Loan(user_id=u_olvaso1.id, book_item_id=items[1].id, loan_date=now-timedelta(days=20), due_date=now+timedelta(days=5), extension_count=2, is_active=True),
            # Aktív, lejárt határidő (bírsághoz)
            Loan(user_id=u_olvaso3.id, book_item_id=items[2].id, loan_date=now-timedelta(days=30), due_date=now-timedelta(days=2), is_active=True),
            # Már lezárt kölcsönzés (előzményekhez)
            Loan(user_id=u_olvaso2.id, book_item_id=items[0].id, loan_date=now-timedelta(days=50), due_date=now-timedelta(days=36), is_active=False)
        ]
        db.session.add_all(loans)
        db.session.commit()

        # 7. TARTOZÁSOK (Bírságok felszámolása) 
        debts = [
            Debt(user_id=u_olvaso3.id, loan_id=loans[1].id, amount=1500.0, reason="Késedelmi díj (2 nap)", is_paid=False),
            Debt(user_id=u_olvaso1.id, amount=800.0, reason="Kiszakadt lap pótlása", is_paid=True)
        ]
        db.session.add_all(debts)
        db.session.commit()

        # 8. ELŐJEGYZÉSEK (Várólista kezelése) 
        reservations = [
            Reservation(user_id=u_olvaso2.id, book_id=books[1].id, status='active'), 
            Reservation(user_id=u_olvaso1.id, book_id=books[2].id, status='active')  
        ]
        db.session.add_all(reservations)
        db.session.commit()

        print("--- BiblioTár Adatbázis Sikeresen Feltöltve tesztadattal! ---")

if __name__ == '__main__':
    seed_data()