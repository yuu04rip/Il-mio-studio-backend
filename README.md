# Il Mio Studio Backend

Backend per la gestione di uno studio legale/notarile, basato su **FastAPI**, **SQLAlchemy** e **Pydantic v2**.  
Questo backend espone le API consumate dal frontend:  
[Il-mio-studio-frontend](https://github.com/yuu04rip/Il-mio-studio-frontend).

---

## 🏗️ Struttura del progetto

```text
Il-mio-studio-backend/
├── .env
├── .gitignore
├── Il-mio-studio-backend.iml
├── README.md
├── alembic.ini
├── main.py
├── requirements.txt
├── storage/
├── test.db
├── test_gestore_backup.db
├── .idea/               # file di configurazione IDE (PyCharm/IntelliJ)
│   └── ...              # vari file di progetto IDE
├── alembic/
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── ...          # file di migration (es. aggiunta_codice_notarile_a_notai.py, ecc.)
└── app/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── deps.py
    │   └── routes/
    │       ├── __init__.py
    │       ├── auth.py
    │       ├── backup.py
    │       ├── documents.py
    │       ├── gestore_studio.py
    │       ├── services_init.py
    │       ├── users.py
    │       └── ...      # altri router eventuali
    ├── core/
    │   ├── __init__.py
    │   ├── config.py
    │   └── security.py
    ├── db/
    │   ├── __init__.py
    │   └── session.py
    ├── models/
    │   ├── __init__.py
    │   ├── cliente.py
    │   ├── cliente_counters.py
    │   ├── dipendente.py
    │   ├── documentazione.py
    │   ├── enums.py
    │   ├── notaio.py
    │   ├── services.py
    │   ├── tables.py
    │   └── user.py
    ├── schemas/
    │   ├── __init__.py
    │   ├── auth.py
    │   ├── cliente.py
    │   ├── dipendente.py
    │   ├── document.py
    │   ├── enums.py
    │   ├── notaio.py
    │   ├── services.py
    │   └── user.py
    ├── scripts/
    │   └── ...          # eventuali script di manutenzione/utilità
    ├── services/
    │   ├── __init__.py
    │   ├── gestore_backup.py
    │   ├── gestore_studio.py
    │   └── gestore_login.py         # altri service/controller
    ├── tests/
    │   ├── __init__.py
    │   ├── conftest.py
    │   ├── test_app.py
    │   ├── test_auth_api.py
    │   ├── test_backup_api.py
    │   ├── test_documentazione_api.py
    │   ├── test_gestore_backup.py
    │   ├── test_studio_dipendenti_clienti_api.py
    │   ├── test_studio_servizi_extra_api.py
    │   └── test_me_api.py
    └── utils/
        ├── __init__.py
        ├── serializers.py
        └── ...          # eventuali helper/utility
```

---

## 🚀 Avvio rapido

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Configura variabili d'ambiente

Crea il file `.env` con, ad esempio:

```env
SECRET_KEY=la-tua-secret-key-lunga-e-casuale
DATABASE_URL=mysql+mysqlconnector://user:password@localhost:3306/utenti
```

> Puoi usare anche SQLite per sviluppo (`sqlite:///test.db`), ma per produzione è raccomandato **MySQL** o **PostgreSQL**.

### 3. Applica le migrazioni (consigliato in produzione)

```bash
alembic upgrade head
```

### 4. Avvia il server

```bash
uvicorn main:app --reload
```

L’API sarà raggiungibile di default su:  
[http://localhost:8000](http://localhost:8000)

### 5. Documentazione API

- Interattiva (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Test automatici

Avvia i test con:

```bash
pytest app/tests -vv
```

---

## 📂 Database

Le tabelle possono essere create all’avvio tramite:

```python
Base.metadata.create_all(bind=engine)
```

**Per produzione usa Alembic per le migrazioni:**

- Genera una nuova migration:

```bash
alembic revision --autogenerate -m "Messaggio"
```

- Applica le migration:

```bash
alembic upgrade head
```

---

## 📦 Reset database (dev)

Se vuoi azzerare tutti i dati e gli auto_increment in MySQL/MariaDB:

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
> In sviluppo con SQLite puoi anche semplicemente cancellare il file `test.db`.

---

## 🔗 Frontend collegato

Questo backend è pensato per lavorare con il frontend:  
[Il-mio-studio-frontend](https://github.com/yuu04rip/Il-mio-studio-frontend).

- Avvia prima il backend (questa repo) su `http://localhost:8000`.
- Poi avvia il frontend seguendo le istruzioni nel suo README, assicurandoti che l’URL del backend (es. `BACKEND_URL`) punti a `http://localhost:8000`.

---

## 🤝 Contributi

- Apri una **issue** per segnalare bug, domande o proposte.
- Fai una **pull request** per proporre modifiche o nuove funzionalità.
- **Commenta i tuoi file e le tue funzioni** per aiutare il team a collaborare meglio!