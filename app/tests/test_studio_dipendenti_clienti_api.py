import os
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.db.session import Base
from app.api.deps import get_db, get_current_user
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.notaio import Notaio
from app.models.enums import TipoDipendenteTecnico

# importa il router gestione studio
from app.api.routes import gestore_studio as studio_router

# registra tutte le tabelle
from app.models import tables, cliente_counters, documentazione, services


class StudioDipendentiClientiApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.TEST_DB_URL = "sqlite:///./test_studio_dip_clienti_api.db"
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

        # Provide a default get_current_user override that returns the dipendente user
        # (the actual user record will be created in setUp). We query by email
        # when the dependency is invoked during tests.
        def override_get_current_user():
            db = TestingSessionLocal()
            try:
                # Return the dipendente user if present; otherwise None
                return db.query(User).filter(User.email == "dip@example.com").first()
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        app.include_router(studio_router.router, prefix="/studio", tags=["gestione-studio"])

        cls.app = app
        cls.client = TestClient(app)
        cls.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        try:
            os.remove("./test_studio_dip_clienti_api.db")
        except OSError:
            pass

    def setUp(self):
        db = self.SessionLocal()
        from app.models.dipendente import DipendenteTecnico
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

        # cliente
        cliente_user = User(
            email="cliente@example.com",
            nome="Mario",
            cognome="Rossi",
            password=hash_password("pwd"),
            ruolo=Role.CLIENTE,
        )
        db.add(cliente_user)
        db.commit()
        db.refresh(cliente_user)

        cliente = Cliente(utente_id=cliente_user.id)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)

        # dipendente tecnico generico
        dip_user = User(
            email="dip@example.com",
            nome="Gianni",
            cognome="Verdi",
            password=hash_password("pwd"),
            ruolo=Role.DIPENDENTE,
        )
        db.add(dip_user)
        db.commit()
        db.refresh(dip_user)

        dipendente = DipendenteTecnico(
            utente_id=dip_user.id,
            tipo=TipoDipendenteTecnico.DIPENDENTE,
        )
        db.add(dipendente)
        db.commit()
        db.refresh(dipendente)

        # notaio
        notaio_user = User(
            email="notaio@example.com",
            nome="Luca",
            cognome="Bianchi",
            password=hash_password("pwd"),
            ruolo=Role.NOTAIO,
        )
        db.add(notaio_user)
        db.commit()
        db.refresh(notaio_user)

        notaio = Notaio(
            utente_id=notaio_user.id,
            tipo=TipoDipendenteTecnico.NOTAIO,
            codice_notarile=1234,
        )
        db.add(notaio)
        db.commit()
        db.refresh(notaio)

        self.cliente_id = cliente.id
        self.cliente_nome = cliente_user.nome
        self.dipendente_id = dipendente.id
        self.dipendente_user_id = dip_user.id
        self.notaio_id = notaio.id

        db.close()

    # ----- DIPENDENTI & NOTAI -----

    def test_get_dipendenti(self):
        resp = self.client.get("/studio/dipendenti/")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(len(data), 2)  # 1 dipendente + 1 notaio, entrambi DipendenteTecnico
        ids = {d["id"] for d in data}
        self.assertIn(self.dipendente_id, ids)
        self.assertIn(self.notaio_id, ids)

    def test_get_notai(self):
        resp = self.client.get("/studio/notai/")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.notaio_id)
        self.assertEqual(data[0]["codice_notarile"], 1234)

    def test_get_dipendente_id_by_user(self):
        resp = self.client.get(f"/studio/dipendente/by_user/{self.dipendente_user_id}")
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json(), self.dipendente_id)

    def test_get_dipendente_dettagli(self):
        resp = self.client.get(f"/studio/dipendente/{self.dipendente_id}/dettagli")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["id"], self.dipendente_id)
        self.assertEqual(data["email"], "dip@example.com")
        self.assertEqual(data["tipo"], TipoDipendenteTecnico.DIPENDENTE)

    # ----- CLIENTI -----

    def test_get_clienti(self):
        resp = self.client.get("/studio/clienti/")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.cliente_id)
        # ClienteOut ha campo "utente" annidato
        self.assertIn("utente", data[0])
        self.assertEqual(data[0]["utente"]["nome"], self.cliente_nome)
        self.assertEqual(data[0]["utente"]["email"], "cliente@example.com")

    def test_search_clienti(self):
        resp = self.client.get("/studio/clienti/search/", params={"q": "Mar"})
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertGreaterEqual(len(data), 1)
        emails = {c["email"] for c in data}
        self.assertIn("cliente@example.com", emails)

    def test_cerca_cliente_per_nome(self):
        resp = self.client.get(f"/studio/clienti/nome/{self.cliente_nome}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["id"], self.cliente_id)
        self.assertIn("utente", data)
        self.assertEqual(data["utente"]["nome"], self.cliente_nome)
        self.assertEqual(data["utente"]["email"], "cliente@example.com")

    def test_get_cliente_dettagli(self):
        resp = self.client.get(f"/studio/clienti/{self.cliente_id}/dettagli")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["id"], self.cliente_id)
        self.assertEqual(data["nome"], self.cliente_nome)
        self.assertEqual(data["email"], "cliente@example.com")