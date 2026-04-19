### Van a requirements.txt file ebben vannak azok a package-k amikre szükségetek van a futtatáshoz
### így tudjátok telepíteni őket : py -m pip install -r requirements.txt
##Ezt a fájlt kell lefuttatnotok ebbe már bele van importálva a DB models 
## Azért ,hogy ne legyen egybe ömlesztve az egész
import os
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, get_jwt_identity
from flasgger import Swagger
from datetime import timedelta
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
@app.route('/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """
    Könyv előjegyzése (foglalása)
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
          properties:
            book_id:
              type: integer
              example: 1
              description: A könyv általános azonosítója (Book.id)
    responses:
      201:
        description: Sikeres előjegyzés
      400:
        description: Már van aktív előjegyzése erre a könyvre
      404:
        description: A könyv nem található
    """
    data = request.get_json()
    book_id = data.get('book_id')
    user_id = get_jwt_identity() # A tokenből kinyerjük a bejelentkezett user ID-t

    # 1. Ellenőrizzük, létezik-e a könyv
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"msg": "A könyv nem található!"}), 404

    # 2. Ellenőrizzük, nincs-e már aktív foglalása ugyanerre a könyvre
    existing_res = Reservation.query.filter_by(
        user_id=user_id, 
        book_id=book_id, 
        status='active'
    ).first()
    
    if existing_res:
        return jsonify({"msg": "Már van egy aktív előjegyzésed erre a könyvre!"}), 400

    # 3. Foglalás létrehozása
    new_res = Reservation(
        user_id=user_id,
        book_id=book_id,
        status='active'
    )

    db.session.add(new_res)
    db.session.commit()

    return jsonify({
        "msg": f"Sikeresen előjegyezted a(z) '{book.title}' című könyvet!",
        "reservation_id": new_res.id
    }), 201

#felhasználó személyes adat módosítása
@app.route('/update-profile', methods=['PUT'])
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
#Ez különleges mert ADMIN és KÖNYVTÁROS is csinálhatja
#Kölcsönzési idő hosszabbítás:
@app.route('/extend-loan/<int:loan_id>', methods=['POST'])
@jwt_required()
def extend_loan(loan_id):
    """
    Kölcsönzési idő meghosszabbítása (max 2 alkalommal).
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
    responses:
      200:
        description: Sikeres hosszabbítás
      400:
        description: Hiba (pl. már kétszer hosszabbított)
      404:
        description: Kölcsönzés nem található
    """
    current_user_id = get_jwt_identity()
    

    
    
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"msg": "Felhasználó nem található!"}), 404

    #Megnézzük, hogy milyen role-ba van ha admin vagy könyvtáros akkor többször is hosszabbíthat
    role = db.session.get(Role, user.role_id)
    is_staff = role.name in ['librarian', 'admin'] if role else False
    
    if is_staff:
        loan = Loan.query.filter_by(id=loan_id, is_active=True).first()
    else:
        loan = Loan.query.filter_by(id=loan_id, user_id=current_user_id, is_active=True).first()   

    
    # Kikeressük az aktív kölcsönzést, ami ehhez a felhasználóhoz tartozik
    if is_staff:
        loan = Loan.query.filter_by(id=loan_id, is_active=True).first()
    else:    
      loan = Loan.query.filter_by(id=loan_id, user_id=current_user_id, is_active=True).first()
    
    if not loan:
        return jsonify({"msg": "Aktív kölcsönzés nem található ezen az azonosítón!"}), 404
        
    if not is_staff and loan.extension_count >= 2:
        return jsonify({"msg": "Ezt a könyvet már 2 alkalommal meghosszabbítottad, több lehetőség nincs."}), 400
        
    loan.extension_count += 1
    loan.due_date = loan.due_date + timedelta(days=14)
    
    db.session.commit()
    return jsonify({
        "msg": "Sikeres hosszabbítás!",
        "uj_hatarido": loan.due_date.strftime('%Y-%m-%d %H:%M'),
        "hosszabbitasok_szama": loan.extension_count
    }), 200
#-Pénz feltöltése számlára-
@app.route('/add-balance', methods=['POST'])
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

@app.route('/pay-debt/<int:debt_id>', methods=['POST'])
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
@app.route('/books-with-available-item', methods=['GET'])
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
    books = Book.query.all()
    result = []

    for book in books:
        # Megkeressük a legelső olyan példányt, ami ehhez a könyvhöz tartozik ÉS elérhető
        first_available_item = BookItem.query.filter_by(
            book_id=book.id, 
            status='available'
        ).first()

        result.append({
            "book_id": book.id,
            "title": book.title,
            "author": book.author,
            "is_borrowable": book.is_borrowable,
            # Ha van elérhető példány, visszaadjuk az ID-ját, különben null-t
            "available_item_id": first_available_item.id if first_available_item else None,
            "can_be_borrowed_now": book.is_borrowable and first_available_item is not None
        })

    return jsonify(result), 200
#------------Admin-------------
# Könyv példány törlése
@app.route('/book-items/<int:item_id>', methods=['DELETE'])
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


if __name__ == '__main__':
    app.run(debug=True)
