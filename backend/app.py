### Van a requirements.txt file ebben vannak azok a package-k amikre szükségetek van a futtatáshoz
### így tudjátok telepíteni őket : py -m pip install -r requirements.txt
##Ezt a fájlt kell lefuttatnotok ebbe már bele van importálva a DB models 
## Azért ,hogy ne legyen egybe ömlesztve az egész
import os
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, get_jwt_identity
from flasgger import Swagger
from datetime import datetime, timedelta
from flask_cors import CORS

# Itt importáljuk a saját modelleinket
from models import db, User, Role, Address, Book, BookItem, Reservation, Loan, Debt

app = Flask(__name__)
#CORS engedélyezés a frontend számára -> Access-Control-Allow-Origin: *
CORS(app)

# --- ELÉRÉSI UTAK BEÁLLÍTÁSA ---
basedir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(basedir, ".."))

# Az db pontos helye:
db_path = os.path.join(project_root, 'db', 'bibliotar.db')

if not os.path.exists(os.path.dirname(db_path)):
    os.makedirs(os.path.dirname(db_path))

# --- KONFIGURÁCIÓ ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'hihetetlenul_titkos_aron_istvan_gergo_peter_jelszo'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Inicializálás
db.init_app(app)
jwt = JWTManager(app)

template = {
    "swagger": "2.0",
    "info": {"title": "BiblioTár API", "version": "1.0.0"},
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Írd be: 'Bearer <token>'"
        }
    },
    "security": [{"Bearer": []}]
}
swagger = Swagger(app, template=template)
#SWAGGER elérés : http://127.0.0.1:5000/apidocs/ ide kell mennetek

#Na ez úgy működik, hogy rányomsz az Auth /loginra 
# Try it out és akkor már szerkeszthető a json amit beküldenél, de alapjáraton ami benne van az egy admin login 
# és ha execute-olod akkor lefut kapsz egy Http 200-as kódot ami jó neked
#ezután pedig kicsit lejebb kapsz egy access tokent amit ki kell másolnod 
# pl eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3NjAwOTA3OCwianRpIjoiNjdiNjFkMDYtNmNkYy00NDg1LWI5ZjgtYjM2M2NjYmJhOTZmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NzYwMDkwNzgsImNzcmYiOiIzN2E1OTdmMi1iM2Q4LTRiMTAtYTA0ZS0xYjljOWZlMWEzNTgiLCJleHAiOjE3NzYwMTI2NzgsInJvbGUiOiJhZG1pbiJ9.UWGSGixme9oLVMlmqUg6H55-9mZlMeUJcNnVgvjfd1k
#egybe kell kimásolnod és az aposztrófok nélkül csak szűzen
# majd Felül van egy gomb, hogy Authorize arra rányomsz és a Value inputba beírod:
# Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3NjAwOTA3OCwianRpIjoiNjdiNjFkMDYtNmNkYy00NDg1LWI5ZjgtYjM2M2NjYmJhOTZmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NzYwMDkwNzgsImNzcmYiOiIzN2E1OTdmMi1iM2Q4LTRiMTAtYTA0ZS0xYjljOWZlMWEzNTgiLCJleHAiOjE3NzYwMTI2NzgsInJvbGUiOiJhZG1pbiJ9.UWGSGixme9oLVMlmqUg6H55-9mZlMeUJcNnVgvjfd1k
# nyilván azt a tokent kell beírnod amit ad a swagger ez csak példa volt
# ha beléptél akkor szabadon garázdálkodhatsz mint admin pl könyvet is törölhetsz

#NYUGODTAN GARÁZDÁLKODHATTOK A DB-BEN TÖRÖLHETTEK MÓDOSÍTHATTOK
#VEHETTEK FEL ÚJ DOLGOKAT, HA ELRONTJÁTOK AKKOR CSAK A SEED.PY-AL ÚJRA KREÁLJÁTOK A DB-T



# --- API végpontok ---
# teszt, hogy működik-e egyáltalán az api (fronted check)
@app.route('/ping')
def ping():
    """
    API teszt
    ---
    tags:
      - Teszt
    responses:
      200:
        description: API működik
        examples:
          application/json: {"msg": "success"}
    """
    return jsonify({"msg": "success"}), 200

# ki az authentikalt user - ha van (backend check)
@app.route('/me')
@jwt_required()
def me():
    """
    Authentikált felhasználó teszt, adatlekérés
    ---
    tags:
      - Teszt
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: "JWT token Bearer formátumban (pl: Bearer eyJ...)"
    responses:
      200:
        description: Felhasználó authentikált, json adatokat ad vissza
      401:
        description: Felhasználó nem authentikált
    """
    
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    role = user.role_data.name
        
    return jsonify({
        "msg": "success",
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": role
    }), 200




#------------Felhasználó-------------
#Login
@app.route('/login', methods=['POST'])
def login():
    """
    Bejelentkezés a BiblioTár rendszerbe
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: LoginInput
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: "admin@bibliotar.hu"
            password:
              type: string
              example: "admin123"
    responses:
      200:
        description: Sikeres belépés, JWT tokent ad vissza
      401:
        description: Hibás email vagy jelszó
    """
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Hiányzó JSON adatok"}), 400

    user = User.query.filter_by(email=data.get('email')).first()

    if user and user.check_password(data.get('password')):
        token = create_access_token(
            identity=str(user.id), 
            additional_claims={"role": user.role_data.name}
        )
        return jsonify({
            "access_token": token,
            "role": user.role_data.name,
            "user": user.email
        }), 200

    return jsonify({"msg": "Hibás email vagy jelszó"}), 401

#Új felhasz regisztálása 
@app.route('/register', methods=['POST'])
def register():
    """
    Új felhasználó regisztrációja lakcímmel
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: RegisterInput
          required:
            - name
            - email
            - password
            - city
            - street
            - zip_code
          properties:
            name:
              type: string
              example: "Arthas Menethil"
            email:
              type: string
              example: "olvaso@pelda.hu"
            password:
              type: string
              example: "titkos123"
            phone:
              type: string
              example: "+36201112222"
            city:
              type: string
              example: "Budapest"
            street:
              type: string
              example: "Fő utca 1."
            zip_code:
              type: string
              example: "1011"
    responses:
      201:
        description: Felhasználó és lakcím sikeresen létrehozva
      400:
        description: Hiányzó adatok vagy foglalt email
    """
    data = request.get_json()
    
    # Adatok kinyerése
    email = data.get('email')
    name = data.get('name')  
    password = data.get('password')
    phone = data.get('phone')
    city = data.get('city')
    street = data.get('street')
    zip_code = data.get('zip_code')

    # Alapvető ellenőrzés ha létezik az email akkor kuka
    if not email or not name or not password or not city or not street or not zip_code:
        return jsonify({"msg": "Minden adat kitöltése kötelező (email, név jelszó, lakcím)!"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Ez az email cím már foglalt!"}), 400

    try:
        # 1. LÉPÉS: Cím létrehozása
        new_address = Address(
            city=city,
            street=street,
            zip_code=zip_code
        )
        db.session.add(new_address)
        db.session.flush() # Ez legenerálja az ID-t, de még nem véglegesíti a tranzakciót

        # 2. LÉPÉS: Szerepkör keresése új regisztráltat nyilván 3-asra állítjuk mert ő user
        user_role = Role.query.filter_by(name='user').first()
        role_id = user_role.id if user_role else 3

        # 3. LÉPÉS: Felhasználó létrehozása az új address_id-val
        new_user = User(
            email=email,
            name=name,
            phone=phone,
            role_id=role_id,
            address_id=new_address.id, 
            balance=0.0
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit() # Itt mentünk el mindent egyszerre

        return jsonify({
            "msg": "Sikeres regisztráció!",
            "user_id": new_user.id,
            "address_id": new_address.id
        }), 201

    except Exception as e:
        db.session.rollback() # Hiba esetén visszavonjuk a változtatásokat
        return jsonify({"msg": f"Hiba történt: {str(e)}"}), 500
    
#Könyv előjegyzése    
@app.route('/user/reservations', methods=['GET'])
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
#Kölcsönzési igény
@app.route('/user/request-loan', methods=['POST'])
@jwt_required()
def request_loan():
    """
    Kölcsönzési igény indítása egy konkrét példányra (Pending állapot).
    ---
    tags:
      - Kölcsönzés
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

#felhasználó személyes adat módosítása
@app.route('/user/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Személyes adatok (lakcím, telefonszám) módosítása.
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
            phone:
              type: string
              example: "+36301234567"
            city:
              type: string
              example: "Budapest"
            street:
              type: string
              example: "Példa utca 1."
            zip_code:
              type: string
              example: "1111"
    responses:
      200:
        description: Sikeres módosítás
      404:
        description: Felhasználó nem található
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    
    if not user:
        return jsonify({"msg": "Felhasználó nem található"}), 404
        
    data = request.get_json()
    
    if 'phone' in data:
        user.phone = data['phone']
        
    if any(k in data for k in ('city', 'street', 'zip_code')):
        address = db.session.get(Address, user.address_id)
        if address:
            if 'city' in data:
                address.city = data['city']
            if 'street' in data:
                address.street = data['street']
            if 'zip_code' in data:
                address.zip_code = data['zip_code']
                
    db.session.commit()
    return jsonify({"msg": "Profil adatok sikeresen frissítve"}), 200

#Kölcsönzési idő hosszabbítás:
@app.route('/user/loan', methods=['POST'])
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
@app.route('/user/add-balance', methods=['POST'])
@jwt_required()
def add_balance():
    """
    Egyenleg feltöltése a bejelentkezett felhasználó számára.
    ---
    tags:
      - Pénzügyek
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
#Tartozás kifizetése
@app.route('/user/pay-debt/<int:debt_id>', methods=['POST'])
@jwt_required()
def pay_debt(debt_id):
    """
    Tartozás kifizetése az egyenlegből
    ---
    tags:
      - Pénzügyek
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
#Könyvek lekérdezése
@app.route('/user/books', methods=['GET'])
@jwt_required()
def get_books_with_item():
    """
    Az összes könyv listázása a legelső elérhető példány azonosítójával.
    ---
    tags:
      - Könyvkezelés
    responses:
      200:
        description: Könyvek listája az első elérhető példány ID-jával
    """
    current_user_id = get_jwt_identity()
    
    # 1. Lekérjük a user összes aktív vagy pending kölcsönzését
    user_loans = Loan.query.filter(Loan.user_id == current_user_id).all()
    
    # Készítünk egy szótárat: book_id -> loan_status (hogy könnyen keressünk)
    user_book_status = {}
    for loan in user_loans:
        item = db.session.get(BookItem, loan.book_item_id)
        if item:
            # Ha is_active True, akkor már nála van, ha False, akkor még csak kérte (pending)
            status_text = "Már nálad van" if loan.is_active else "Jóváhagyásra vár"
            user_book_status[item.book_id] = status_text

    # 2. Lekérjük az összes könyvet
    books = Book.query.all()
    result = []

    for book in books:
        # Megkeressük a legelső elérhető példányt
        first_available_item = BookItem.query.filter_by(
            book_id=book.id, 
            status='available'
        ).first()

        # Meghatározzuk a könyv aktuális állapotát a user számára
        user_status = user_book_status.get(book.id, "Kölcsönözhető")
        
        # Csak akkor engedjük a gombot, ha se nem pending, se nem borrowed a usernek, 
        # ÉS van szabad példány, ÉS a könyv alapból kölcsönözhető
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
            "user_specific_status": user_status, # "Már nálad van", "Jóváhagyásra vár" vagy "Kölcsönözhető"
            "can_be_borrowed_now": is_actually_available
        })

    return jsonify(result), 200

#Lefoglalt könyvek és függőben lévő könyvek checkolása
@app.route('/user/loans', methods=['GET'])
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
        result.append({
            "loan_id": loan.id,
            "book_title": book.title,
            "author": book.author,
            "barcode": item.barcode,
            "loan_date": loan.loan_date.strftime('%Y-%m-%d %H:%M') if loan.loan_date else "Függőben",
            "due_date": loan.due_date.strftime('%Y-%m-%d %H:%M') if loan.due_date else "Függőben",
            "status": "Aktív" if loan.is_active else "Jóváhagyásra vár (Pending)",
            "is_active": loan.is_active
        })

    return jsonify(result), 200
#Foglalás törlése

@app.route('/user/loan/<int:loan_id>', methods=['DELETE'])
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
#------------Admin-------------
# Könyv példány törlése
@app.route('/admin/book-items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_book_item(item_id):
    """
    Konkrét könyvpéldány törlése (Csak Admin)
    ---
    tags:
      - Admin Műveletek
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        type: integer
        required: true
        description: A törölni kívánt példány (BookItem) egyedi azonosítója
    responses:
      200:
        description: Példány sikeresen törölve
      403:
        description: Nincs admin jogosultságod
      404:
        description: A példány nem található
    """
    claims = get_jwt()
    if claims.get('role') != 'admin': # Itt adjuk meg,hogy csak admin joggal törölhetünk
        return jsonify({"msg": "Csak adminisztrátor törölhet példányt!"}), 403

    item = db.session.get(BookItem, item_id)
    if not item: # Nyilván ha nincs benne a db-ben akkor nem tudod törölni
        return jsonify({"msg": "Ez a példány nem létezik az adatbázisban."}), 404

    if item.status == 'borrowed': # És nyilván kölcsönzött példányt se tudsz törölni 
        return jsonify({"msg": "A példány nem törölhető, mert jelenleg kölcsönzés alatt áll!"}), 400

    db.session.delete(item)
    db.session.commit()
    
    return jsonify({"msg": f"A(z) {item.barcode} vonalkódú példány sikeresen eltávolítva."}), 200

# Könyv hozzáadása
@app.route('/admin/books', methods=['POST'])
@jwt_required()
def create_book():
    """
    Új könyv felvétele (ADMIN)
    ---
    tags:
      - Admin Műveletek
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "Vének háborúja"
            author:
              type: string
              example: "John Scalzi"
            is_borrowable:
              type: boolean
              example: true
    responses:
      201:
        description: Könyv sikeresen létrehozva
      403:
        description: Nincs admin jogosultság
      400:
        description: Hibás vagy hiányzó adatok
    """
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"msg": "Csak admin adhat hozzá új könyvet!"}), 403

    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    is_borrowable = data.get('is_borrowable', True)

    if not title:
        return jsonify({"msg": "A könyv címe kötelező!"}), 400

    new_book = Book(
        title=title,
        author=author,
        is_borrowable=is_borrowable
    )

    db.session.add(new_book)
    db.session.commit()

    return jsonify({
        "msg": "Könyv sikeresen felvéve!",
        "book_id": new_book.id
    }), 201


# Új könyvpéldányok hozzáadása
@app.route('/admin/book-items', methods=['POST'])
@jwt_required()
def add_book_items():
    """
    Új könyvpéldányok hozzáadása (Csak Admin)
    ---
    tags:
      - Admin Műveletek
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            book_id:
              type: integer
              example: 1
            count:
              type: integer
              example: 2
    responses:
      201:
        description: Példányok sikeresen létrehozva
      403:
        description: Nincs admin jogosultság
      404:
        description: Könyv nem található
    """
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"msg": "Csak admin adhat hozzá új példányokat!"}), 403

    data = request.get_json()
    book_id = data.get('book_id')
    count = data.get('count', 1)

    # Könyv ellenőrzése
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"msg": "A könyv nem található!"}), 404

    created_items = []

    for _ in range(count):
        new_item = BookItem(
            book_id=book_id,
            status='available'
        )
        db.session.add(new_item)
        db.session.flush()  # generál ID-t

        new_item.barcode = f"BOOKITEM-{new_item.id}"
        created_items.append(new_item.barcode)

    db.session.commit()

    return jsonify({
        "msg": f"{count} példány sikeresen hozzáadva!",
        "barcodes": created_items
    }), 201

#----- KÖNYVTÁROS ------
@app.route('/librarian/approve-loan/', methods=['POST'])
@jwt_required()
def approve_loan(loan_id):
    """
    Kölcsönzési igény jóváhagyása és aktiválása (Csak könyvtáros/admin).
    ---
    tags:
      - Kölcsönzés
    security:
      - Bearer: []
    parameters:
      - name: loan_id
        in: path
        type: integer
        required: true
        description: A jóváhagyandó kölcsönzés (Loan) azonosítója
    responses:
      200:
        description: Kölcsönzés sikeresen aktiválva
      403:
        description: Nincs jogosultságod a művelethez
      404:
        description: A kölcsönzési igény nem található vagy már aktív
    """
    current_user_id = get_jwt_identity()
    
    # Jogosultság ellenőrzése
    staff = db.session.get(User, current_user_id)
    if not staff or not staff.role_data or staff.role_data.name not in ['librarian', 'admin']:
        return jsonify({"msg": "Ehhez a művelethez könyvtárosi jogosultság szükséges!"}), 403

    # A kölcsönzési igény (Loan) kikeresése
    loan = db.session.get(Loan, loan_id)
    
    # Csak akkor aktiválhatjuk, ha létezik és még NEM aktív (is_active=False)
    if not loan or loan.is_active:
        return jsonify({"msg": "Nem található jóváhagyásra váró igény ezen az azonosítón!"}), 404

    #  AKTIVÁLÁS 
    loan.is_active = True
    loan.loan_date = datetime.utcnow() # A kölcsönzés most indul
    loan.due_date = datetime.utcnow() + timedelta(days=14) # 2 hét határidő
    
    # A könyv példányának státuszát 'borrowed' lesz
    item = db.session.get(BookItem, loan.book_item_id)
    if item:
        item.status = 'borrowed'

    db.session.commit()

    return jsonify({
        "msg": "Kölcsönzés sikeresen jóváhagyva!",
        "loan_id": loan.id,
        "uj_hatarido": loan.due_date.strftime('%Y-%m-%d %H:%M'),
        "konyv_peldany": item.barcode if item else "Ismeretlen"
    }), 200
# Várakozó könyv kölcsönzési igények
@app.route('/librarian/pending-loans', methods=['GET'])
@jwt_required()
def get_pending_loans():
    """
    Várakozó (Pending) kölcsönzési igények listázása könyvtárosoknak.
    ---
    tags:
      - Kölcsönzés
    security:
      - Bearer: []
    responses:
      200:
        description: A várakozó igények listája
      403:
        description: Nincs jogosultság (csak könyvtáros/admin)
    """
    current_user_id = get_jwt_identity()
    staff = db.session.get(User, current_user_id)
    
    # Jogosultság ellenőrzése
    if not staff or not staff.role_data or staff.role_data.name not in ['librarian', 'admin']:
        return jsonify({"msg": "Ehhez a művelethez könyvtárosi jogosultság szükséges!"}), 403

    # Csak azok kellenek amik nem aktívak 
    pending_loans = Loan.query.filter_by(is_active=False).all()
    
    result = []
    for loan in pending_loans:
        # Adatok lekérése
        user_info = db.session.get(User, loan.user_id)
        item_info = db.session.get(BookItem, loan.book_item_id)
        book_info = db.session.get(Book, item_info.book_id) if item_info else None

        result.append({
            "loan_id": loan.id,
            "user_name": user_info.name if user_info else "Ismeretlen",
            "user_email": user_info.email if user_info else "",
            "book_title": book_info.title if book_info else "Ismeretlen",
            "barcode": item_info.barcode if item_info else "Nincs",
            "request_date": loan.loan_date.strftime('%Y-%m-%d %H:%M') if loan.loan_date else "Nincs adat"
        })

    return jsonify(result), 200

#Könyv visszavétel:
@app.route('/librarian/return-loan', methods=['POST'])
@jwt_required()
def return_loan():
    """
    Könyv visszavétele vonalkód alapján (Kizárólag könyvtáros).
    ---
    tags:
      - Kölcsönzés
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            barcode:
              type: string
              example: "BC-BK1-1"
              description: "A visszahozott fizikai példány vonalkódja"
    responses:
      200:
        description: Könyv sikeresen visszavéve
      400:
        description: Hiányzó vonalkód, vagy a könyv nincs kikölcsönözve
      403:
        description: Nincs jogosultságod a művelethez (kizárólag könyvtáros)
      404:
        description: A példány nem található a rendszerben
    """
    current_user_id = get_jwt_identity()
    staff = db.session.get(User, current_user_id)
    
    # Szigorúan CSAK könyvtáros (librarian) csinálhatja!
    if not staff or not staff.role_data or staff.role_data.name != 'librarian':
        return jsonify({"msg": "Ehhez a művelethez könyvtárosi jogosultság szükséges!"}), 403

    data = request.get_json()
    barcode = data.get('barcode')
    
    if not barcode:
        return jsonify({"msg": "Hiányzó vonalkód a kérésből!"}), 400

    # 2. Megkeressük a fizikai példányt a vonalkód alapján
    item = BookItem.query.filter_by(barcode=barcode).first()
    if not item:
        return jsonify({"msg": "Nem található példány ezzel a vonalkóddal az adatbázisban!"}), 404

    # 3. Megkeressük az ehhez a példányhoz tartozó AKTÍV kölcsönzést
    loan = Loan.query.filter_by(book_item_id=item.id, is_active=True).first()
    if not loan:
        return jsonify({"msg": "Ez a példány jelenleg nincs kikölcsönözve (nincs aktív kölcsönzés rajta)."}), 400

    # 4. Lezárjuk a kölcsönzést és felszabadítjuk a fizikai példányt
    loan.is_active = False
    item.status = 'available'
    
    # Kikeressük a könyv címét a válaszüzenethez
    book = db.session.get(Book, item.book_id)
    
    db.session.commit()

    return jsonify({
        "msg": "A könyv sikeresen visszavéve, a kölcsönzés lezárva!",
        "konyv_cime": book.title if book else "Ismeretlen könyv",
        "vonalkod": item.barcode
    }), 200


#Bírság kiszabása:

@app.route('/librarian/debts', methods=['POST'])
@jwt_required()
def create_debt():
    """
    Bírság kiszabása (Kizárólag könyvtáros).
    ---
    tags:
      - Pénzügyek
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
              example: 3
              description: "A felhasználó ID-ja, akire a bírságot kivetjük"
            amount:
              type: number
              example: 1500.0
              description: "A bírság összege (Ft)"
            reason:
              type: string
              example: "Késedelmi díj"
              description: "A bírság indoka"
            loan_id:
              type: integer
              example: 12
              description: "Opcionális: A kapcsolódó kölcsönzés azonosítója"
    responses:
      201:
        description: Bírság sikeresen rögzítve
      400:
        description: Adateltérés (pl. a loan nem ehhez a felhasználóhoz tartozik)
      403:
        description: Nincs jogosultság (csak könyvtáros)
      404:
        description: A felhasználó vagy a kölcsönzés nem található
    """
    current_user_id = get_jwt_identity()
    staff = db.session.get(User, current_user_id)

    # 1. Jogosultság ellenőrzése: Szigorúan csak könyvtáros
    if not staff or not staff.role_data or staff.role_data.name != 'librarian':
        return jsonify({"msg": "Ehhez a művelethez könyvtárosi jogosultság szükséges!"}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    reason = data.get('reason')
    loan_id = data.get('loan_id')

    # 2. Kötelező mezők ellenőrzése
    if not user_id or amount is None or not reason:
        return jsonify({"msg": "Hiányzó adatok! A user_id, amount és reason kötelező."}), 400

    # 3. Felhasználó létezésének ellenőrzése
    target_user = db.session.get(User, user_id)
    if not target_user:
        return jsonify({"msg": "A megadott felhasználó nem található!"}), 404

    # 4. KRITIKUS KERESTELLENŐRZÉS: Ha van megadva loan_id
    if loan_id:
        loan = db.session.get(Loan, loan_id)
        if not loan:
            return jsonify({"msg": "A megadott kölcsönzés azonosító nem létezik!"}), 404
        
        # Ellenőrizzük, hogy a kölcsönzés tényleg a célszemélyé-e
        if loan.user_id != user_id:
            return jsonify({
                "msg": f"Hiba! A(z) {loan_id} ID-jú kölcsönzés nem a(z) {user_id} ID-jú felhasználóhoz tartozik."
            }), 400

    # 5. Tartozás mentése
    new_debt = Debt(
        user_id=user_id,
        loan_id=loan_id,
        amount=float(amount),
        reason=reason,
        is_paid=False
    )

    db.session.add(new_debt)
    db.session.commit()

    return jsonify({
        "msg": "Bírság sikeresen kiszabva!",
        "debt_id": new_debt.id,
        "felhasznalo": target_user.name
    }), 201










if __name__ == '__main__':
    app.run(debug=True)
