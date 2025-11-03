# Il Mio Studio Backend

Backend per la gestione di uno studio legale/notarile, basato su **FastAPI**, **SQLAlchemy** e **Pydantic v2**.

---

## 🏗️ Struttura del progetto

```
Il-mio-studio-backend/
│
├── main.py
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── dipendente.py
│   │   │   ├── documents.py
│   │   │   ├── services.py
│   │   │   ├── services_init.py
│   │   │   ├── users.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   └── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── cliente.py
│   │   ├── dipendente.py
│   │   ├── documentazione.py
│   │   ├── enums.py
│   │   ├── notaio.py
│   │   ├── services.py
│   │   ├── tables.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── cliente.py
│   │   ├── dipendente.py
│   │   ├── document.py
│   │   ├── enums.py
│   │   ├── notaio.py
│   │   ├── services.py
│   │   └── user.py
├── storage/
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_dipendente_notaio.py
│   ├── test_docs.py
│   ├── test_documentazione.py
│   ├── test_servizi.py
│   └── test_users.py
├── alembic/
│   ├── versions/
│   │   └── 45d1d2fc98b0_aggiunta_codice_notarile_a_notai.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── .env
├── alembic.ini
├── Il-mio-studio-backend.iml
├── README.md
├── requirements.txt
├── test.db
```

---

## 🚀 Avvio rapido

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Configura variabili d'ambiente

Crea il file `.env` con:
```
SECRET_KEY=la-tua-secret-key-lunga-e-casuale
DATABASE_URL=mysql+mysqlconnector://user:password@localhost:3306/utenti
```
> Puoi usare anche SQLite per sviluppo (`sqlite:///test.db`), ma per produzione raccomandato **MySQL** o **PostgreSQL**.

### 3. Applica le migrazioni (consigliato in produzione)

```bash
alembic upgrade head
```

### 4. Avvia il server

```bash
uvicorn main:app --reload
```

### 5. Documentazione API

- Interattiva: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🗂️ Suddivisione delle responsabilità (consigliata)

Organizza il lavoro tra i membri del team, ad esempio:

- **API & routes:** gestione endpoints, autenticazione, servizi, documenti, utenti
- **Models:** DB, tabelle, relazioni, enums
- **Schemas:** validazione input/output API
- **Alembic:** gestione migrazioni database
- **Tests:** test automatici per endpoints e modelli

Scrivi nei commenti dei file chi è responsabile di una sezione (`# Responsabile: nome`).

---

## 🔑 Note Pydantic v2

Se usi Pydantic v2 nei tuoi schemas, ricorda di aggiungere:
```python
class Config:
    from_attributes = True
```

---

## 🧪 Test automatici

Metti i test in `tests/` (es: `tests/test_app.py`).
Avvia i test con:
```bash
pytest
```

---

## 📂 Database

Le tabelle vengono create all’avvio tramite:
```python
Base.metadata.create_all(bind=engine)
```

**Per produzione usa Alembic per le migrazioni!**
- Genera una nuova migration:
  ```bash
  alembic revision --autogenerate -m "Messaggio"
  ```
- Applica le migration:
  ```bash
  alembic upgrade head
  ```

---

## 🛠️ Endpoints principali

- `/auth/register` - Registrazione utente
- `/auth/login` - Login e token JWT
- `/users/me` - Info utente autenticato
- `/documents` - Upload e gestione documenti
- `/` - Status app

---

## 📦 Reset database (dev)

Se vuoi azzerare tutti i dati e gli auto_increment:
```sql
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE servizio_documentazione;
TRUNCATE TABLE dipendente_servizio;
TRUNCATE TABLE dipendente_cliente;
TRUNCATE TABLE documentazioni;
TRUNCATE TABLE servizi;
TRUNCATE TABLE clienti;
TRUNCATE TABLE dipendenti_tecnici;
TRUNCATE TABLE notai;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;
```
> **Attenzione:** Incolla tutto il blocco su phpMyAdmin o nel client MySQL, **non riga per riga**.

---

## 🤝 Contributi

- Apri una **issue** per segnalare bug, domande o proposte.
- Fai una **pull request** per proporre modifiche o nuove funzionalità.
- **Commenta i tuoi file e le tue funzioni** per aiutare il team a collaborare meglio!

---

**Buon lavoro backend!**