# Studio Service API (FastAPI)

MVP per autenticazione, profilo utente e gestione documenti.

## Avvio rapido

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # poi modifica SECRET_KEY se vuoi
uvicorn app.main:app --reload
```

Visita http://127.0.0.1:8000/docs per testare le API.

## Endpoints principali
- POST /auth/register, POST /auth/login
- GET /users/me, PUT /users/me, PUT /users/me/password
- POST /documents (upload), GET /documents (list), GET /documents/{id}/download

## Note
- DB: MySQL su porta 3310 (vedi `.env.example`), puoi cambiare `DATABASE_URL` per usare altri DB.
- Storage: cartella `./storage`. In produzione usa uno storage esterno (S3, Azure Blob).
- Per migrazioni DB in produzione, aggiungi Alembic.