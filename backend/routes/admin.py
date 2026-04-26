from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from models import db, User, Role, Address, Book, BookItem, Reservation, Loan, Debt

admin_bp = Blueprint('admin', __name__)

# Könyv példány törlése
@admin_bp.route('/admin/book-items/<int:item_id>', methods=['DELETE'])
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
@admin_bp.route('/admin/books', methods=['POST'])
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
@admin_bp.route('/admin/book-items', methods=['POST'])
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