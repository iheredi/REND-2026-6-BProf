from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from models import db, User, Role, Address, Book, BookItem, Reservation, Loan, Debt

admin_bp = Blueprint('admin', __name__)

# Könyv törlése
@admin_bp.route('/admin/books/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    """
    Konkrét könyvpéldány törlése (Csak Admin)
    ---
    tags:
      - Admin műveletek
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
    if claims.get('role') != 'admin':
        return jsonify({"msg": "Csak admin törölhet könyvet!"}), 403

    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"msg": "A könyv nem található!"}), 404

    # Van-e kölcsönzés alatt álló példány?
    #active_loans = Loan.query.join(BookItem).filter(
    #    BookItem.book_id == book_id,
    #    Loan.is_active == True
    #).first() 
    active_loans = db.session.query(
        db.session.query(Loan).filter(
            Loan.is_active == True,
            Loan.book_item_id.in_(
                db.session.query(BookItem.id).filter_by(book_id=book_id)
            )
        ).exists()
    ).scalar()
    if active_loans:
        return jsonify({"msg":"A könyv nem törölhető, mert van kölcsönzés alatt álló példánya!"}), 400

    res_exists = db.session.query(
      db.session.query(Reservation).filter_by(book_id=book_id).exists()
    ).scalar()
    if res_exists:
        return jsonify({"msg":"A könyv nem törölhető, mert vannak foglalások."}), 400

    # Töröljük a példányokat
    BookItem.query.filter_by(book_id=book_id).delete()

    # Töröljük magát a könyvet
    db.session.delete(book)
    db.session.commit()

    return jsonify({"msg": "Könyv és példányai sikeresen törölve!"}), 200

# Könyv hozzáadása
@admin_bp.route('/admin/books', methods=['POST'])
@jwt_required()
def create_book():
    """
    Új könyv felvétele (ADMIN)
    ---
    tags:
      - Admin műveletek
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
@admin_bp.route('/admin/book-items', methods=['POST'])
@jwt_required()
def add_book_items():
    """
    Új könyvpéldányok hozzáadása (Csak Admin)
    ---
    tags:
      - Admin műveletek
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
            status="available",
            barcode="TEMP" 
        )
        db.session.add(new_item)
        db.session.flush()  
        #new_item.barcode = f"TESTBOKKITEM-{new_item.id}"
        new_item.barcode = f"BC-BK{book_id}-{new_item.id}"
        created_items.append(new_item.barcode)

    db.session.commit()

    return jsonify({
        "msg": f"{count} példány sikeresen hozzáadva!",
        "barcodes": created_items
    }), 201


# Könyv adatainak módosítása
@admin_bp.route('/admin/books/<int:book_id>', methods=['PUT'])
@jwt_required()
def update_book(book_id):
    """
    Könyv adatainak módosítása (Csak Admin)
    ---
    tags:
      - Admin műveletek
    security:
      - Bearer: []
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
        description: A módosítandó könyv azonosítója
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "Új könyvcím"
            is_borrowable:
              type: boolean
              example: true
    responses:
      200:
        description: Könyv sikeresen frissítve
      403:
        description: Nincs admin jogosultság
      404:
        description: A könyv nem található
      400:
        description: Hibás adatok
    """
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"msg": "Csak admin módosíthat könyvet!"}), 403

    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"msg": "A könyv nem található!"}), 404

    data = request.get_json() or {}
    title = data.get('title')
    is_borrowable = data.get('is_borrowable')

    if title is not None:
        if not title.strip():
            return jsonify({"msg": "A könyv címe nem lehet üres!"}), 400
        book.title = title.strip()

    if is_borrowable is not None:
        book.is_borrowable = bool(is_borrowable)

    if title is None and is_borrowable is None:
        return jsonify({"msg": "Nem adtál meg módosítandó mezőt!"}), 400

    db.session.commit()

    return jsonify({"msg": "Könyv adatai sikeresen frissítve!", "book_id": book.id}), 200


# Könyvpéldány státuszának módosítása
@admin_bp.route('/admin/book-items/<int:item_id>/status', methods=['PUT'])
@jwt_required()
def update_book_item_status(item_id):
    """
    Könyvpéldány státuszának módosítása (Csak Admin)
    ---
    tags:
      - Admin műveletek
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        type: integer
        required: true
        description: A módosítandó példány azonosítója
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              example: "available"
    responses:
      200:
        description: Státusz frissítve
      403:
        description: Nincs admin jogosultság
      404:
        description: A példány nem található
      400:
        description: Hibás státusz
    """
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"msg": "Csak admin módosíthat példány státuszt!"}), 403

    data = request.get_json() or {}
    status = data.get('status')
    if not status or status not in ('available', 'damaged', 'lost'):
        return jsonify({"msg": "Érvénytelen státusz. Használd: available, damaged, lost."}), 400

    book_item = db.session.get(BookItem, item_id)
    if not book_item:
        return jsonify({"msg": "A példány nem található!"}), 404

    book_item.status = status
    db.session.commit()

    return jsonify({"msg": "A könyvpéldány státusza frissítve lett.", "status": book_item.status}), 200