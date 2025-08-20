# Il Mio Studio Backend

Backend per la gestione dello studio legale/notarile, basato su FastAPI, SQLAlchemy e Pydantic v2.

## 🏗️ Struttura del progetto

```
Il-mio-studio-backend/
│
├── main.py
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── documents.py
│   │   │   └── ...
│   │   └── deps.py
│   ├── db/
│   │   └── session.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   └── models/
│       ├── user.py
│       ├── tables.py
│       └── ...
├── tests/
│   └── test_app.py
├── .env
└── README.md
```

## 🚀 Avvio rapido

1. **Installa le dipendenze**
    ```bash
    pip install -r requirements.txt
    ```

2. **Crea il file `.env`**
    ```
    SECRET_KEY=la-tua-secret-key-lunga-e-casuale
    DATABASE_URL=sqlite:///./app.db
    ```

3. **Avvia il server**
    ```bash
    uvicorn main:app --reload
    ```

4. **Documentazione API**
    - Interattiva: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🔑 Note Pydantic v2

> Se usi Pydantic v2, nei tuoi schemas metti:
> ```python
> class Config:
>     from_attributes = True
> ```

## 🧪 Test automatici

Metti i test in `tests/test_app.py`.  
Avvia i test con:
```bash
pytest
```

## 📂 Database

Le tabelle vengono create all’avvio tramite:
```python
Base.metadata.create_all(bind=engine)
```
**Per produzione usa Alembic per le migrazioni!**

## 🛠️ Endpoints principali

- `/auth/register` - Registrazione utente
- `/auth/login` - Login e token JWT
- `/users/me` - Info utente autenticato
- `/documents` - Upload e gestione documenti
- `/` - Status app

## 🤝 Contributi

Apri una issue o una pull request!
