from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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