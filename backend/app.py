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

from routes.auth import auth_bp # /ping /me
from routes.user import user_bp # user importálás
from routes.admin import admin_bp # admin importálás
from routes.librarian import librarian_bp #könyvtáros importálása

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
# ki az authentikalt user - ha van (backend check)
app.register_blueprint(auth_bp)



#------------Felhasználó------------

app.register_blueprint(user_bp)
#Login
#Új felhasz regisztálása     
#Könyv előjegyzése    
#Kölcsönzési igény
#felhasználó személyes adat módosítása
#Kölcsönzési idő hosszabbítás:
#-Pénz feltöltése számlára-
#Tartozás kifizetése
#Könyvek lekérdezése
#Lefoglalt könyvek és függőben lévő könyvek checkolása
#Foglalás törlése

#------------Admin-------------

app.register_blueprint(admin_bp)
# Könyv példány törlése
# Könyv hozzáadása
# Új könyvpéldányok hozzáadása


#----- KÖNYVTÁROS ------
app.register_blueprint(librarian_bp)
#kölcsönzési igény jóváhagyás
# Várakozó könyv kölcsönzési igények
#Könyv visszavétel:
#Bírság kiszabása:



if __name__ == '__main__':
    app.run(debug=True)
