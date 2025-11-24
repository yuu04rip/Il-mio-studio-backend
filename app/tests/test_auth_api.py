import os
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.dipendente import DipendenteTecnico
# Assicura che la root del progetto sia nel path
import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.db.session import Base
from app.api.deps import get_db
from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User, Role
from app.models.notaio import Notaio
from app.models.cliente import Cliente


from app.api.routes import auth



class AuthApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Usa un file SQLite dedicato ai test, per evitare problemi di thread con :memory:
        cls.TEST_DB_URL = "sqlite:///./test_auth.db"

        # connect_args per SQLite + poolclass SingletonThreadPool per gestire più thread
        cls.engine = create_engine(
            cls.TEST_DB_URL,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine, future=True
        )

        # Crea tutte le tabelle una volta sola
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        # Costruisci l'app FastAPI con override di get_db
        app = FastAPI()

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.include_router(auth.router, prefix="/auth", tags=["auth"])

        cls.app = app
        cls.client = TestClient(app)
        cls.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        # opzionale: cancella il file di test
        try:
            os.remove("./test_auth.db")
        except OSError:
            pass

    def setUp(self):
        db = self.SessionLocal()
        # Cancella nell'ordine giusto per evitare vincoli FK
        db.query(Notaio).delete()
        db.query(DipendenteTecnico).delete()
        db.query(Cliente).delete()
        db.query(User).delete()
        db.commit()
        db.close()

    # -------- TEST --------

    def test_register_cliente_crea_user_e_cliente(self):
        payload = {
            "email": "cliente@example.com",
            "password": "secret",
            "nome": "Mario",
            "cognome": "Rossi",
            "numeroTelefonico": "123456789",
            "ruolo": "cliente",
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)

        db = self.SessionLocal()
        user = db.query(User).filter_by(email="cliente@example.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.ruolo, Role.CLIENTE)
        # dovrebbe esistere anche il Cliente
        cliente = db.query(Cliente).filter_by(utente_id=user.id).first()
        self.assertIsNotNone(cliente)
        db.close()

    def test_register_notaio_endpoint_dedicato_ok(self):
        payload = {
            "email": "notaio2@example.com",
            "password": "secret",
            "nome": "Luigi",
            "cognome": "Verdi",
            "numeroTelefonico": "987654321",
            "codice_notarile": 1234,
        }
        resp = self.client.post("/auth/register-notaio", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)

        db = self.SessionLocal()
        user = db.query(User).filter_by(email="notaio2@example.com").first()
        notaio = db.query(Notaio).filter_by(utente_id=user.id).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.ruolo, Role.NOTAIO)
        self.assertIsNotNone(notaio)
        self.assertEqual(notaio.codice_notarile, 1234)
        db.close()

    def test_login_cliente_ok(self):
        # registra prima un cliente
        self.client.post(
            "/auth/register",
            json={
                "email": "logincliente@example.com",
                "password": "mypw",
                "nome": "Mario",
                "cognome": "Rossi",
                "ruolo": "cliente",
            },
        )

        resp = self.client.post(
            "/auth/login",
            json={"email": "logincliente@example.com", "password": "mypw"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)

    def test_login_cliente_password_errata(self):
        self.client.post(
            "/auth/register",
            json={
                "email": "wrongpw@example.com",
                "password": "correct",
                "nome": "Mario",
                "cognome": "Rossi",
                "ruolo": "cliente",
            },
        )

        resp = self.client.post(
            "/auth/login",
            json={"email": "wrongpw@example.com", "password": "bad"}
        )
        self.assertEqual(resp.status_code, 401)

    def test_login_notaio_con_ruolo_errato(self):
        # registra un notaio
        self.client.post(
            "/auth/register-notaio",
            json={
                "email": "notaio_role@example.com",
                "password": "secret",
                "nome": "Luigi",
                "cognome": "Verdi",
                "numeroTelefonico": "111",
                "codice_notarile": 5555,
            },
        )

        # prova login con ruolo CLIENTE invece di NOTAIO
        resp = self.client.post(
            "/auth/login",
            json={
                "email": "notaio_role@example.com",
                "password": "secret",
                "codice_notarile": 5555,
                "ruolo": "cliente",
            },
        )
        self.assertEqual(resp.status_code, 403)

    def test_change_password_ok(self):
        # registra un cliente
        self.client.post(
            "/auth/register",
            json={
                "email": "changepw@example.com",
                "password": "oldpw",
                "nome": "Mario",
                "cognome": "Rossi",
                "ruolo": "cliente",
            },
        )

        resp = self.client.post(
            "/auth/change-password",
            json={
                "email": "changepw@example.com",
                "old_password": "oldpw",
                "new_password": "newpw",
            },
        )
        self.assertEqual(resp.status_code, 200)

        # verifica che la nuova password funzioni nel login
        resp2 = self.client.post(
            "/auth/login",
            json={"email": "changepw@example.com", "password": "newpw"}
        )
        self.assertEqual(resp2.status_code, 200)

    def test_change_email_password_errata(self):
        # registra un cliente
        register_resp = self.client.post(
            "/auth/register",
            json={
                "email": "oldemail@example.com",
                "password": "mypw",
                "nome": "Mario",
                "cognome": "Rossi",
                "ruolo": "cliente",
            },
        )
        token = register_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = self.client.post(
            "/auth/change-email",
            json={
                "email": "oldemail@example.com",
                "new_email": "newemail@example.com",
                "password": "wrongpw",
            },
            headers=headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["detail"], "Password errata")

    def test_change_email_ok(self):
        register_resp = self.client.post(
            "/auth/register",
            json={
                "email": "old2@example.com",
                "password": "mypw",
                "nome": "Mario",
                "cognome": "Rossi",
                "ruolo": "cliente",
            },
        )
        token = register_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = self.client.post(
            "/auth/change-email",
            json={
                "email": "old2@example.com",
                "new_email": "new2@example.com",
                "password": "mypw",
            },
            headers=headers,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["email"], "new2@example.com")