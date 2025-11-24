import os
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.db.session import Base
from app.services.gestore_login import GestoreLogin
from app.models.user import User, Role
from app.models.notaio import Notaio
from app.core.security import hash_password, verify_password


class GestoreLoginTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.TEST_DB_URL = "sqlite:///./test_auth.db"
        cls.engine = create_engine(
            cls.TEST_DB_URL,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine, future=True
        )

        # crea tabelle una volta (se non già create)
        Base.metadata.create_all(bind=cls.engine)

        cls.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        try:
            os.remove("./test_auth.db")
        except OSError:
            pass

    def setUp(self):
        self.db = self.SessionLocal()
        # pulizia base
        self.db.query(Notaio).delete()
        self.db.query(User).delete()
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_aggiungi_utente_crea_user(self):
        gestore = GestoreLogin(self.db)

        user = User(
            email="cliente@example.com",
            nome="Mario",
            cognome="Rossi",
            password=hash_password("password123"),
            ruolo=Role.CLIENTE,
        )
        gestore.aggiungi_utente(user)

        fetched = self.db.query(User).filter_by(email="cliente@example.com").first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.email, "cliente@example.com")
        self.assertTrue(verify_password("password123", fetched.password))

    # (gli altri test che avevamo prima: login cliente ok, notaio, change_password, ecc.)