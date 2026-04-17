# REND-2026-6-BProf

Tagok:
Bleier Áron - WM9KYI
Fürész Gergő - COS2VI
Herédi István - G3HF1O
Reiner Péter - EFU0GT

Rendszerfejelsztés haladó módszerei tárgy beszámolójához repository.

## Használat

### DB feltöltése adatokkal
```js
cd init
python3 seed.py
```
ez létrehozza/felülírja a db/Bibliotar.db SQLite adatbázist

### Backend indítása
```js
cd backend
python3 app.py
```

### Frontend indítása (view only mode - fejelsztéshez lásd frontend/Readme.md)
```js
cd frontend/dist
python3 -m http.server
```
ez elindít egy python webserver a tcp 8000 -es porton. A frontend a http://127.0.0.1:8000 -en érhető el.
