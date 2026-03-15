import sqlite3
import os

def init_db():
    db_dir = os.path.join("..", "db")
    db_path = os.path.join(db_dir, "bibliotar.db")
    
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"DB könyvtár létrehozva: {db_dir}")

    # Connect to the SQLite database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # User tábla
        # Role értékek 'felhasználó', 'könyvtáros', or 'adminisztrátor'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT
            )
        ''')

        # Userek
        users = [
            ('Kovács János', 'felhasználó', 'janos@email.com', 'userpass1', '+36201111111'),
            ('Nagy Anna', 'felhasználó', 'anna@email.com', 'userpass2', '+36202222222'),
            ('Szabó Béla', 'felhasználó', 'bela@email.com', 'userpass3', '+36203333333'),
            ('Kiss Éva', 'felhasználó', 'eva@email.com', 'userpass4', '+36204444444'),
            ('Tóth Gábor', 'felhasználó', 'gabor@email.com', 'userpass5', '+36205555555'),
            ('Könyv Tímea', 'könyvtáros', 'timea@bibliotar.hu', 'libpass1', '+36301111111'),
            ('Olvasó Ottó', 'könyvtáros', 'otto@bibliotar.hu', 'libpass2', '+36302222222'),
            ('Rendszer Gazda', 'adminisztrátor', 'admin@bibliotar.hu', 'adminpass1', '+36301111111')
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO user (name, role, email, password, phone) 
        VALUES (?, ?, ?, ?, ?)
        ''', users)

        conn.commit()
        print(f"DB sikeresen létrehozva és feltöltve teszt adatokkal: {db_path}")
        

    except sqlite3.Error as e:
        print(f"DB error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()