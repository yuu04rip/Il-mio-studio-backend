import os
import unittest

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.db.session import Base
from app.api.deps import get_db, get_current_user
from app.core.security import hash_password
from app.models.user import User, Role

from app.api.routes import users as me_router

# importa moduli per registrare le tabelle
from app.models import cliente, dipendente, notaio, cliente_counters, services, documentazione, tables


class MeApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.TEST_DB_URL = "sqlite:///./test_me_api.db"
        cls.engine = create_engine(
            cls.TEST_DB_URL,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine, future=True
        )

        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        app = FastAPI()

        # override get_db
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

        # includiamo il router /me
        app.include_router(me_router.router, prefix="/users", tags=["users"])

        cls.app = app
        cls.client = TestClient(app)
        cls.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        try:
            os.remove("./test_me_api.db")
        except OSError:
            pass

    def setUp(self):
        db = self.SessionLocal()
        # pulizia tabelle base
        from app.models.cliente import Cliente
        from app.models.dipendente import DipendenteTecnico
        from app.models.notaio import Notaio
        from app.models.cliente_counters import ClienteCounters
        from app.models.services import Servizio
        from app.models.documentazione import Documentazione

        db.query(Documentazione).delete()
        db.query(Servizio).delete()
        db.query(ClienteCounters).delete()
        db.query(Notaio).delete()
        db.query(DipendenteTecnico).delete()
        db.query(Cliente).delete()
        db.query(User).delete()
        db.commit()

        # utente "corrente"
        current_user = User(
            email="user@example.com",
            nome="Mario",
            cognome="Rossi",
            numeroTelefonico="1234567890",
            password=hash_password("pwd"),
            ruolo=Role.CLIENTE,
        )
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

        # secondo utente per test collisione email
        other_user = User(
            email="other@example.com",
            nome="Luigi",
            cognome="Bianchi",
            numeroTelefonico="0987654321",
            password=hash_password("pwd2"),
            ruolo=Role.CLIENTE,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # salviamo SOLO gli id, non le istanze (che sono legate a questa sessione)
        self.current_user_id = current_user.id
        self.other_user_id = other_user.id

        db.close()

        # override di get_current_user che ricarica l'utente dalla sessione CORRENTE
        def override_get_current_user_dep(
                db: Session = Depends(get_db),
        ) -> User:
            user = db.get(User, self.current_user_id)
            return user

        self.app.dependency_overrides[get_current_user] = override_get_current_user_dep

    def tearDown(self):
        # rimuovi override get_current_user
        if get_current_user in self.app.dependency_overrides:
            del self.app.dependency_overrides[get_current_user]

    @property
    def app(self):
        return self.__class__.app

    @property
    def client(self):
        return self.__class__.client

    def test_get_me(self):
        resp = self.client.get("/users/me")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["id"], self.current_user_id)
        self.assertEqual(data["email"], "user@example.com")
        self.assertEqual(data["nome"], "Mario")
        self.assertEqual(data["cognome"], "Rossi")
        self.assertEqual(data.get("numeroTelefonico"), "1234567890")

    def test_update_me_basic_fields(self):
        payload = {
            "nome": "Giovanni",
            "cognome": "Verdi",
            "numeroTelefonico": "111222333",
        }
        resp = self.client.put("/users/me/update", json=payload)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["nome"], "Giovanni")
        self.assertEqual(data["cognome"], "Verdi")
        self.assertEqual(data["numeroTelefonico"], "111222333")
        self.assertEqual(data["email"], "user@example.com")  # non cambiata

        db = self.SessionLocal()
        u = db.get(User, self.current_user_id)
        self.assertEqual(u.nome, "Giovanni")
        self.assertEqual(u.cognome, "Verdi")
        self.assertEqual(u.numeroTelefonico, "111222333")
        db.close()

    def test_update_me_change_email_success(self):
        payload = {"email": "newemail@example.com"}
        resp = self.client.put("/users/me/update", json=payload)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["email"], "newemail@example.com")

        db = self.SessionLocal()
        u = db.get(User, self.current_user_id)
        self.assertEqual(u.email, "newemail@example.com")
        db.close()

    def test_update_me_email_already_registered(self):
        payload = {"email": "other@example.com"}
        resp = self.client.put("/users/me/update", json=payload)
        self.assertEqual(resp.status_code, 400, resp.text)
        data = resp.json()
        self.assertEqual(data["detail"], "Email già registrata")