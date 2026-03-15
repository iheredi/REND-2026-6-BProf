from flask import Flask, jsonify, request, abort
import sqlite3
import os
import secrets

app = Flask(__name__)
DB_PATH = os.path.join("..", "db", "bibliotar.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_authenticated_user(): 
    token = request.headers.get('Authorization')

    if token is None:
        abort(401, description="Hibajelzés! Hitelesítés szükséges")

    conn = get_db_connection()
    cursor = conn.cursor()

    # a token alapján keressük a usert
    cursor.execute("SELECT id, name, role, email FROM user WHERE token = ?", (token,))
    user = cursor.fetchone()

    if user is None:        
        abort(401, description="Hibajelzés! Helytelen adatok")
    
    conn.close()
    
    return user



######### API hívások #########

# CURL kérés curl http://127.0.0.1:5000/ping
@app.route('/ping')
def ping():
    return jsonify({
        "status": "success",
        "message": "Szerver elérhető"
    })

# CURL kérés (nem authentikált): curl -i -X GET http://127.0.0.1:5000/users
# CURL kérés (nem authentikált): curl -i -X GET http://127.0.0.1:5000/users -H "Authorization: 6ba81d2b9bcc27bff232dea40c11"
@app.route('/users', methods=['GET'])
def get_users():
    authenticated_user = get_authenticated_user()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, role, email, phone FROM user")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(users)


# CURL kérés: curl -i -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d '{"email": "janos@email.com", "password": "userpass1"}'
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Hiányzó adatok"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query for the user by email
    cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    # Hitelesítés (Authentication)
    if user and user['password'] == password:
        # Sikeres bejelentkezés

        # létrehozzuk a tokent és eltároljuk, amit a továbbiakban küld a frontend
        new_token = secrets.token_hex(14)    
        cursor.execute("UPDATE user SET token = ? WHERE id = ?", (new_token, user['id']))
        conn.commit()
    
        return jsonify({
            "status": "success",
            "message": "Sikeres bejelentkezés",
            "token": new_token
        }), 200
    else:
        # Sikeretelen bejelentkeézs
        return jsonify({
            "status": "error",
            "message": "Hibajelzés! Helytelen adatok"
        }), 401

    # db bezar
    conn.close()



# http hibakódok alapján válasz
@app.errorhandler(401)
def unauthorized(error):    
    return jsonify({
        "status": "error",
        "message": error.description
    }), 401

@app.errorhandler(403)
def unauthorized(error):    
    return jsonify({
        "status": "error",
        "message": error.description
    }), 403



if __name__ == '__main__':
    app.run(debug=True)
