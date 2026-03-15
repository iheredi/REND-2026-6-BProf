# Flask Backend + API

Egyszerű **Flask REST API**, amely felhasználókat kezel egy **SQLite adatbázisban**.

## Követelmények

- Python 3
- Flask
- SQLite

Flask telepítése:

```bash
pip install flask
```

## CURL használata teszteléshez

A `curl` egy parancssori eszköz, amellyel HTTP kéréseket lehet küldeni egy API felé.  
Segítségével egyszerűen lehet tesztelni a szerver végpontjait.

### Alap szintaxis

```bash
curl -X METHOD URL
```
Például egy GET kérés
```bash
curl -X GET http://127.0.0.1:5000/users
```
Szerver tesztelés (ping végpont)
```bash
curl -X GET http://127.0.0.1:5000/ping
```


Header küldése
```bash
curl -X GET http://127.0.0.1:5000/users -H "Authorization: TOKEN"
```

POST kérés JSON adatokkal
```bash
curl -X POST http://127.0.0.1:5000/login \
-H "Content-Type: application/json" \
-d '{"email":"janos@email.com","password":"userpass1"}'
```

