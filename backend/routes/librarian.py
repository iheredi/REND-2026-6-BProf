from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from models import db, User, Role, Address, Book, BookItem, Reservation, Loan, Debt

from datetime import datetime, timedelta
librarian_bp = Blueprint('librarian', __name__)





#----- KÖNYVTÁROS ------

#kölcsönzési igény jóváhagyás
@librarian_bp.route('/librarian/approve-loan/', methods=['POST'])
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
@librarian_bp.route('/librarian/pending-loans', methods=['GET'])
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
@librarian_bp.route('/librarian/return-loan', methods=['POST'])
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

@librarian_bp.route('/librarian/debts', methods=['POST'])
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