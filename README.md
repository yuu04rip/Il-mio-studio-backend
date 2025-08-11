# Il-mio-studio-backend
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
- DB: SQLite per sviluppo. Cambia `DATABASE_URL` in `.env` per usare Postgres (es. `postgresql+psycopg://user:pwd@localhost:5432/db`).
- Storage: cartella `./storage`. In produzione usa uno storage esterno (S3, Azure Blob).
- Per migrazioni DB in produzione, aggiungi Alembic.
