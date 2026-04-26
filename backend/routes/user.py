from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from datetime import datetime, timedelta
from models import db, User, Role, Address, Book, BookItem, Reservation, Loan, Debt


user_bp = Blueprint('user', __name__)

#------------Felhasználó-------------


#Könyv előjegyzése
@user_bp.route('/user/reservations', methods=['GET'])
@jwt_required()
def get_my_reservations():
    """
    A bejelentkezett felhasználó saját aktív foglalásainak (várólista) lekérése.
    ---
    tags:
      - Felhasználói műveletek
    security:
      - Bearer: []
    responses:
      200:
        description: A felhasználó foglalásainak listája
      401:
        description: Hiányzó vagy lejárt token
    """
    # Azonosítás a token alapján 
    current_user_id = get_jwt_identity()

    
    # Összekapcsoljuk a Book táblával, hogy lássuk a címeket is
    my_res = db.session.query(Reservation, Book).join(
        Book, Reservation.book_id == Book.id
    ).filter(
        Reservation.user_id == current_user_id,
        Reservation.status == 'active'
    ).all()

    result = []
    for res, book in my_res:
        result.append({
            "reservation_id": res.id,
            "book_id": book.id,
            "title": book.title,
            "author": book.author,
            "reserved_at": res.reserved_at.strftime('%Y-%m-%d %H:%M'),
            "status": res.status
        })

    #Csak a felhasználó saját foglalásait adjuk vissza
    return jsonify(result), 200


# Könyv előjegyzése (Létrehozás)
@user_bp.route('/user/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """
    Új előjegyzés létrehozása egy könyvhöze, ha nincs elérhető példány.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    book_id = data.get('book_id')

    # Ellenőrizzük, van-e egyáltalán szabad példány (mert akkor kölcsönözni kellene, nem előjegyezni)
    available_item = BookItem.query.filter_by(book_id=book_id, status='available').first()
    if available_item:
        return jsonify({"msg": "Van elérhető példány, használd a kölcsönzés funkciót!"}), 400

    # Ellenőrizzük, nincs-e már aktív előjegyzése erre a könyvre
    existing_res = Reservation.query.filter_by(user_id=current_user_id, book_id=book_id, status='active').first()
    if existing_res:
        return jsonify({"msg": "Már van aktív előjegyzésed erre a könyvre!"}), 400

    new_res = Reservation(
        user_id=current_user_id,
        book_id=book_id,
        status='active'
    )
    db.session.add(new_res)
    db.session.commit()

    return jsonify({"msg": "Sikeres előjegyzés! Értesítünk, ha felszabadul egy példány."}), 201


# Előjegyzés törlése (lemondása)
@user_bp.route('/user/reservations/<int:res_id>', methods=['DELETE'])
@jwt_required()
def delete_reservation(res_id):
    """
    Saját aktív előjegyzés törlése/visszavonása.
    """
    current_user_id = get_jwt_identity()
    
    # Megkeressük az előjegyzést
    res = db.session.get(Reservation, res_id)

    if not res:
        return jsonify({"msg": "Az előjegyzés nem található!"}), 404

    # Ellenőrizzük a jogosultságot
    if str(res.user_id) != str(current_user_id):
        return jsonify({"msg": "Nincs jogosultságod más előjegyzését törölni!"}), 403

    db.session.delete(res)
    db.session.commit()

    return jsonify({"msg": "Az előjegyzést sikeresen visszavontad."}), 200

#Kölcsönzési igény
@user_bp.route('/user/request-loan', methods=['POST'])
@jwt_required()
def request_loan():
    """
    Kölcsönzési igény indítása egy konkrét példányra (Pending állapot).
    ---
    tags:
      - Felhasználói műveletek
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            book_item_id:
              type: integer
              example: 10
              description: A konkrét könyvpéldány azonosítója (BookItem.id)
    responses:
      201:
        description: Igény sikeresen rögzítve (Pending)
      400:
        description: A példány nem elérhető vagy már foglalt
      404:
        description: A példány nem található
    """
    data = request.get_json()
    item_id = data.get('book_item_id') 
    user_id = get_jwt_identity()

    # 1. Példány ellenőrzése
    item = db.session.get(BookItem, item_id)
    if not item:
        return jsonify({"msg": "A példány nem található!"}), 404
    
    if item.status != 'available':
        return jsonify({"msg": "Ez a példány jelenleg nem kölcsönözhető!"}), 400

    # 2. Van-e már kérés erre?
    existing_loan = Loan.query.filter_by(
        user_id=user_id, 
        book_item_id=item_id, 
        is_active=False
    ).first()
    
    if existing_loan:
        return jsonify({"msg": "Már elküldtél egy igényt erre a példányra!"}), 400

    # 3. Kölcsönzési igény létrehozása (is_active=False = PENDING)
    new_loan = Loan(
        user_id=user_id,
        book_item_id=item_id,
        is_active=False,
        extension_count=0
    )

    # 4. A példányt "reserved" állapotba tesszük, hogy más ne lássa elérhetőnek
    item.status = 'reserved'

    db.session.add(new_loan)
    db.session.commit()

    return jsonify({
        "msg": "Igény rögzítve! Keresd fel a könyvtárost a jóváhagyáshoz.",
        "loan_id": new_loan.id
    }), 201


#Kölcsönzési idő hosszabbítás:
@user_bp.route('/user/loan', methods=['POST'])
@jwt_required()
def user_extend_loan():
    """
    Kölcsönzés hosszabbítása az olvasó által (Body-ban küldött ID-val).
    ---
    tags:
      - Felhasználói műveletek
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            loan_id:
              type: integer
              example: 1
    responses:
      200:
        description: Sikeres hosszabbítás
    """
    data = request.get_json()
    loan_id = data.get('loan_id') 

    if not loan_id:
        return jsonify({"msg": "Hiányzó loan_id a kérésből!"}), 400

    current_user_id = get_jwt_identity()
    loan = db.session.get(Loan, loan_id)

    if not loan or not loan.is_active:
        return jsonify({"msg": "Aktív kölcsönzés nem található!"}), 404

  
    if str(loan.user_id) != str(current_user_id):
        return jsonify({"msg": "Nincs jogosultságod más kölcsönzését hosszabbítani!"}), 403

    #  Limit: Max 2
    if loan.extension_count >= 2:
        return jsonify({"msg": "Ezt a könyvet már kétszer meghosszabbítottad!"}), 400

    #  Hosszabbítás
    loan.due_date += timedelta(days=14)
    loan.extension_count += 1
    
    db.session.commit()

    return jsonify({
        "msg": "Sikeres hosszabbítás!",
        "uj_hatarido": loan.due_date.strftime('%Y-%m-%d'),
        "hosszabbitasok_szama": loan.extension_count
    }), 200

#-Pénz feltöltése számlára-
@user_bp.route('/user/add-balance', methods=['POST'])
@jwt_required()
def add_balance():
    """
    Egyenleg feltöltése a bejelentkezett felhasználó számára.
    ---
    tags:
      - Felhasználói műveletek
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            amount:
              type: number
              example: 5000
    responses:
      200:
        description: Sikeres feltöltés
      400:
        description: Érvénytelen összeg
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    
    if not user:
        return jsonify({"msg": "Felhasználó nem található!"}), 404

    # Adatok kinyerése a kérésből
    data = request.get_json()
    amount = data.get('amount')

    # Ellenőrizzük, hogy az összeg érvényes szám-e és pozitív
    if amount is None or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"msg": "Kérlek, adj meg egy érvényes pozitív összeget!"}), 400

    # Egyenleg frissítése (alapértelmezett értéket is kezelve)
    if user.balance is None:
        user.balance = 0.0
        
    user.balance += float(amount)
    
    db.session.commit()

    return jsonify({
        "msg": "Sikeres feltöltés!",
        "uj_egyenleg": user.balance,
        "hozzaadott_osszeg": amount
    }), 200


# Saját tartozások lekérése
@user_bp.route('/user/debts', methods=['GET'])
@jwt_required()
def get_my_debts():
    """
    Saját kifizetetlen tartozások (bírságok) lekérése.
    ---
    tags:
      - Felhasználói műveletek
    security:
      - Bearer: []
    responses:
      200:
        description: A tartozások listája
    """
    current_user_id = get_jwt_identity()
    
    # Csak a kifizetetlen tartozásokat kérjük le
    my_debts = Debt.query.filter_by(user_id=current_user_id, is_paid=False).all()
    
    result = []
    for d in my_debts:
        result.append({
            "id": d.id,
            "amount": d.amount,
            "reason": d.reason,
            "loan_id": d.loan_id,
            "created_at": d.created_at.strftime('%Y-%m-%d %H:%M') if d.created_at else "Nincs adat"
        })
        
    return jsonify(result), 200

#Tartozás kifizetése
@user_bp.route('/user/pay-debt/<int:debt_id>', methods=['POST'])
@jwt_required()
def pay_debt(debt_id):
    """
    Tartozás kifizetése az egyenlegből
    ---
    tags:
      - Felhasználói műveletek
    security:
      - Bearer: []
    parameters:
      - name: debt_id
        in: path
        type: integer
        required: true
        description: A tartozás egyedi azonosítója
    responses:
      200:
        description: Sikeres fizetés
    """

    
    current_user_id = get_jwt_identity()

    current_user_id = get_jwt_identity()
    debt = db.session.get(Debt, debt_id)

    print(f"--- DEBUG INFO ---")
    print(f"Bejelentkezett User ID (tokenből): {current_user_id}")
    print(f"Tartozás ID-ja amit fizetnél: {debt_id}")
    if debt:
        print(f"Tartozás gazdájának User ID-ja: {debt.user_id}")
    print(f"------------------")
    user = db.session.get(User, current_user_id)
    
    # Tartozás megkeresése
    #debt = db.session.get(Debt, debt_id)
    
    if not debt:
        return jsonify({"msg": "A megadott tartozás nem létezik!"}), 404
        
    # Jogosultság megnézése
    if int(debt.user_id) != int(current_user_id):
      return jsonify({"msg": "Nincs jogosultságod más tartozását kifizetni!"}), 403
    
    # Fizetve van?
    if debt.is_paid:
        return jsonify({"msg": "Ez a tartozás már rendezve van."}), 400

    # Van pízed?
    if user.balance < debt.amount:
        return jsonify({
            "msg": "Nincs elegendő fedezet!",
            "hianyzik": debt.amount - user.balance
        }), 400

    # 5. Levonás és státusz frissítés
    user.balance -= debt.amount
    debt.is_paid = True
    
    db.session.commit()

    return jsonify({
        "msg": "Tartozás sikeresen rendezve!",
        "osszeg": debt.amount,
        "maradek_egyenleg": user.balance
    }), 200


#Könyvek lekérdezése - okosítva lehet keresni cím és szerző szerint
@user_bp.route('/user/books', methods=['GET'])
@jwt_required()
def get_books_with_item():
    """
    Az összes könyv listázása a legelső elérhető példány azonosítójával.
    ---
    tags:
      - Felhasználói műveletek
    responses:
      200:
        description: Könyvek listája az első elérhető példány ID-jával
    """
    current_user_id = get_jwt_identity()
    
    # 1. Keresési kulcsszó kinyerése az URL-ből (?search=valami)
    search_query = request.args.get('search', '').strip()
    
    # 2. Lekérjük a user összes aktív vagy pending kölcsönzését
    user_loans = Loan.query.filter(Loan.user_id == current_user_id).all()
    
    user_book_status = {}
    for loan in user_loans:
        item = db.session.get(BookItem, loan.book_item_id)
        if item:
            # JAVÍTÁS: Csak az aktívakat és a tényleg függőben lévőket nézzük!
            if loan.is_active:
                user_book_status[item.book_id] = "Már nálad van"
            elif not loan.is_active and item.status == 'reserved':
                user_book_status[item.book_id] = "Jóváhagyásra vár"
            # A régen visszahozott könyvekkel nem foglalkozunk, azokat újra ki lehet kérni!

    # 3. Lekérjük a könyveket - ha van keresés, szűrünk!
    query = Book.query
    if search_query:
        # Keresünk a címben VAGY a szerzőben (kis-nagybetű nem számít az ilike miatt)
        query = query.filter(
            (Book.title.ilike(f'%{search_query}%')) | 
            (Book.author.ilike(f'%{search_query}%'))
        )
    
    books = query.all()
    result = []

    for book in books:
        # Megkeressük a legelső elérhető példányt
        first_available_item = BookItem.query.filter_by(
            book_id=book.id, 
            status='available'
        ).first()

        user_status = user_book_status.get(book.id, "Kölcsönözhető")
        
        is_actually_available = (
            book.id not in user_book_status and 
            first_available_item is not None and 
            book.is_borrowable
        )

        result.append({
            "book_id": book.id,
            "title": book.title,
            "author": book.author,
            "is_borrowable": book.is_borrowable,
            "available_item_id": first_available_item.id if first_available_item else None,
            "user_specific_status": user_status,
            "can_be_borrowed_now": is_actually_available
        })

    return jsonify(result), 200


#Lefoglalt könyvek és függőben lévő könyvek checkolása
@user_bp.route('/user/loans', methods=['GET'])
@jwt_required()
def get_my_loans():
    """
    A bejelentkezett felhasználó aktív és függőben lévő kölcsönzéseinek lekérése.
    ---
    tags:
      - Felhasználói műveletek
    security:
      - Bearer: []
    responses:
      200:
        description: A felhasználó kölcsönzéseinek listája (tartalmazza a loan_id-t)
    """
    current_user_id = get_jwt_identity()

    # Itt azokat listázzuk, amik vagy aktívak, vagy függőben vannak
    my_loans = db.session.query(Loan, BookItem, Book).join(
        BookItem, Loan.book_item_id == BookItem.id
    ).join(
        Book, BookItem.book_id == Book.id
    ).filter(
        Loan.user_id == current_user_id
    ).all()

    result = []
    for loan, item, book in my_loans:
        
        if loan.is_active:
            status_text = "Kikölcsönözve (Aktív)"
        else:
            # Ha a loan is_active=False, és az item 'reserved', akkor még a könyvtárosra vár.
            # Ha az item már 'available' (vagy más), akkor ez egy már visszahozott, régi kölcsönzés!
            if item.status == 'reserved':
                status_text = "Jóváhagyásra vár (Pending)"
            else:
                status_text = "Visszahozva (Előzmény)"

        days_left_text = "-"
        if loan.is_active and loan.due_date:
            delta = loan.due_date.date() - datetime.now().date()
            if delta.days > 0:
                days_left_text = f"{delta.days} nap van hátra"
            elif delta.days == 0:
                days_left_text = "Ma jár le!"
            else:
                days_left_text = f"Lejárt {abs(delta.days)} napja!"
            
        result.append({
            "loan_id": loan.id,
            "book_title": book.title,
            "author": book.author,
            "barcode": item.barcode,
            "loan_date": loan.loan_date.strftime('%Y-%m-%d %H:%M') if loan.loan_date else "Függőben",
            "due_date": loan.due_date.strftime('%Y-%m-%d %H:%M') if loan.due_date else "Függőben",
            "status": status_text,
            "is_active": loan.is_active,
            "days_remaining": days_left_text
        })

    return jsonify(result), 200


#Foglalás törlése
@user_bp.route('/user/loan/<int:loan_id>', methods=['DELETE'])
@jwt_required()
def delete_loan_request(loan_id):
    """
    Függőben lévő (Pending) kölcsönzési kérelem törlése a Loan táblából.
    ---
    tags:
      - Felhasználói műveletek
    security:
      - Bearer: []
    parameters:
      - name: loan_id
        in: path
        type: integer
        required: true
        description: A törlendő kölcsönzés azonosítója
    responses:
      200:
        description: Kérelem sikeresen törölve, a könyv újra elérhető
      403:
        description: Nincs jogosultságod más kérését törölni
      400:
        description: Aktív kölcsönzést nem lehet törölni
      404:
        description: A kölcsönzés nem található
    """
    current_user_id = get_jwt_identity()
    
    # Megkeressük a kölcsönzést
    loan = db.session.get(Loan, loan_id)

    if not loan:
        return jsonify({"msg": "A kölcsönzési kérelem nem található!"}), 404

    if str(loan.user_id) != str(current_user_id):
        return jsonify({"msg": "Nincs jogosultságod más kérését törölni!"}), 403

    # Csak a PENDING (is_active=False) kérést szabad törölni!
    if loan.is_active:
        return jsonify({"msg": "Az aktív kölcsönzést nem lehet törölni! Kérlek hozd vissza a könyvet."}), 400

  
    # Mivel a könyv 'reserved' lett a státusza, most vissza kell tenni 'available'-re
    item = db.session.get(BookItem, loan.book_item_id)
    if item:
        item.status = 'available'

    # Törlés Loan táblából
    db.session.delete(loan)
    db.session.commit()

    return jsonify({"msg": "A kölcsönzési kérelmet sikeresen törölted, a könyv újra szabad."}), 200


# Egy konkrét könyv részletes adatai
@user_bp.route('/user/books/<int:book_id>', methods=['GET'])
@jwt_required()
def get_book_details(book_id):
    """
    Egy konkrét könyv részletes adatainak megtekintése.
    ---
    tags:
      - Felhasználói műveletek
    security:
      - Bearer: []
    """
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"msg": "A könyv nem található!"}), 404

    # Statisztika a példányokról
    total_copies = book.copies.count()
    available_copies = book.copies.filter_by(status='available').count()

    return jsonify({
        "book_id": book.id,
        "title": book.title,
        "author": book.author,
        "is_borrowable": book.is_borrowable,
        "total_copies": total_copies,
        "available_copies": available_copies
    }), 200