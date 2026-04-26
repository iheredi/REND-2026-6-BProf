from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from models import db, User, Role, Address, Book, BookItem, Reservation, Loan, Debt

# Létrehozzuk a Blueprintet prefix nélkül
auth_bp = Blueprint('auth', __name__)

# teszt, hogy működik-e egyáltalán az api (fronted check)
@auth_bp.route('/ping')
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
@auth_bp.route('/me')
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
    # Itt az eredeti .query.get-et használjuk, ahogy a kódodban volt
    user = User.query.get(user_id)
    role = user.role_data.name
        
    return jsonify({
        "msg": "success",
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": role
    }), 200


#Login
@auth_bp.route('/login', methods=['POST'])
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
@auth_bp.route('/register', methods=['POST'])
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
    

#felhasználó személyes profil lekérése:
@auth_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Saját profiladatok lekérése.
    ---
    tags:
      - Általános felhasználói műveletek
    security:
      - Bearer: []
    responses:
      200:
        description: Profiladatok sikeresen lekérve.
      404:
        description: Felhasználó nem található.
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    
    if not user:
        return jsonify({"msg": "Felhasználó nem található"}), 404
        
    address = db.session.get(Address, user.address_id)
    
    return jsonify({
        "msg": "success",
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role_data.name if user.role_data else "user",
        "phone": user.phone,
        "balance": user.balance,
        "address": {
            "city": address.city if address else "",
            "street": address.street if address else "",
            "zip_code": address.zip_code if address else ""
        }
    }), 200


#felhasználó személyes adat módosítása
@auth_bp.route('/user/profile', methods=['POST'])
@jwt_required()
def update_profile():
    """
    Személyes adatok (lakcím, telefonszám) módosítása.
    ---
    tags:
      - Általános felhasználói műveletek
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