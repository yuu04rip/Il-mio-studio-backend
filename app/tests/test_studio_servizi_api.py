import os
import unittest
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.db.session import Base
from app.api.deps import get_db
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.enums import TipoServizio, TipoDipendenteTecnico, StatoServizio
from app.models.services import Servizio

# importa il router di gestione studio (quello che hai incollato)
# se il file è app/api/gestore_studio.py:
from app.api.routes import gestore_studio as studio_router
# se è in un altro path, adatta l'import:
# from app.api.routes import gestore_studio as studio_router

# importa i modelli per registrare tutte le tabelle nel metadata
from app.models import tables
from app.models import notaio
from app.models import cliente_counters
from app.models import documentazione


class StudioServiziApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.TEST_DB_URL = "sqlite:///./test_studio_api.db"
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

        app.dependency_overrides[get_db] = override_get_db
        app.include_router(studio_router.router, prefix="/studio", tags=["gestione-studio"])

        cls.app = app
        cls.client = TestClient(app)
        cls.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        try:
            os.remove("./test_studio_api.db")
        except OSError:
            pass

    def setUp(self):
        db = self.SessionLocal()
        # pulizia tabelle base
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

        # crea cliente + utente
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

        # crea dipendente tecnico
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

        # salva solo gli ID per usarli nei test, non gli oggetti ORM
        self.cliente_id = cliente.id
        self.dipendente_id = dipendente.id

        db.close()

    # ---------- TEST ----------

    def test_crea_servizio_via_api(self):
        payload = {
            "cliente_id": self.cliente_id,
            "tipo": TipoServizio.ATTO.value,
            "dipendente_id": self.dipendente_id,
        }
        resp = self.client.post("/studio/servizi", json=payload)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()

        self.assertIn("id", data)
        self.assertEqual(data["cliente_id"], self.cliente_id)
        self.assertEqual(data["tipo"], TipoServizio.ATTO.value)
        self.assertEqual(data["statoServizio"], StatoServizio.CREATO.value)
        self.assertEqual(data["creato_da_id"], self.dipendente_id)
        self.assertGreater(data["codiceCorrente"], 0)
        self.assertTrue(data["codiceServizio"].startswith("SERV-"))

        db = self.SessionLocal()
        servizio = db.get(Servizio, data["id"])
        self.assertIsNotNone(servizio)
        self.assertEqual(servizio.cliente_id, self.cliente_id)
        db.close()

    def test_flusso_inizializza_inoltra_approva_via_api(self):
        create_resp = self.client.post(
            "/studio/servizi",
            json={
                "cliente_id": self.cliente_id,
                "tipo": TipoServizio.COMPROMESSO.value,
                "dipendente_id": self.dipendente_id,
            },
        )
        self.assertEqual(create_resp.status_code, 200, create_resp.text)
        servizio_id = create_resp.json()["id"]

        r1 = self.client.post(f"/studio/servizi/{servizio_id}/inizializza")
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r1.json()["statoServizio"], StatoServizio.IN_LAVORAZIONE.value)

        r2 = self.client.post(f"/studio/servizi/{servizio_id}/inoltra-notaio")
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertEqual(r2.json()["statoServizio"], StatoServizio.IN_ATTESA_APPROVAZIONE.value)

        r3 = self.client.post(f"/studio/servizi/{servizio_id}/approva")
        self.assertEqual(r3.status_code, 200, r3.text)
        self.assertEqual(r3.json()["statoServizio"], StatoServizio.APPROVATO.value)

    def test_flusso_rifiuta_via_api(self):
        create_resp = self.client.post(
            "/studio/servizi",
            json={
                "cliente_id": self.cliente_id,
                "tipo": TipoServizio.PREVENTIVO.value,
                "dipendente_id": self.dipendente_id,
            },
        )
        self.assertEqual(create_resp.status_code, 200, create_resp.text)
        servizio_id = create_resp.json()["id"]

        self.client.post(f"/studio/servizi/{servizio_id}/inizializza")
        self.client.post(f"/studio/servizi/{servizio_id}/inoltra-notaio")
        r = self.client.post(f"/studio/servizi/{servizio_id}/rifiuta")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["statoServizio"], StatoServizio.RIFIUTATO.value)

    def test_get_servizio_dettaglio(self):
        create_resp = self.client.post(
            "/studio/servizi",
            json={
                "cliente_id": self.cliente_id,
                "tipo": TipoServizio.ATTO.value,
                "dipendente_id": self.dipendente_id,
            },
        )
        servizio_id = create_resp.json()["id"]

        resp = self.client.get(f"/studio/servizi/{servizio_id}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()

        self.assertEqual(data["id"], servizio_id)
        self.assertEqual(data["cliente_id"], self.cliente_id)
        self.assertEqual(data["creato_da_id"], self.dipendente_id)
        if data.get("creato_da"):
            self.assertEqual(data["creato_da"]["id"], self.dipendente_id)

    def test_get_servizi_approvati_cliente(self):
        create_resp = self.client.post(
            "/studio/servizi",
            json={
                "cliente_id": self.cliente_id,
                "tipo": TipoServizio.ATTO.value,
                "dipendente_id": self.dipendente_id,
            },
        )
        servizio_id = create_resp.json()["id"]
        self.client.post(f"/studio/servizi/{servizio_id}/inizializza")
        self.client.post(f"/studio/servizi/{servizio_id}/inoltra-notaio")
        self.client.post(f"/studio/servizi/{servizio_id}/approva")

        resp = self.client.get(f"/studio/clienti/{self.cliente_id}/servizi_approvati")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], servizio_id)
        self.assertEqual(data[0]["statoServizio"], StatoServizio.APPROVATO.value)

    def test_servizi_per_dipendente(self):
        for tipo in (TipoServizio.ATTO, TipoServizio.COMPROMESSO):
            self.client.post(
                "/studio/servizi",
                json={
                    "cliente_id": self.cliente_id,
                    "tipo": tipo.value,
                    "dipendente_id": self.dipendente_id,
                },
            )

        resp = self.client.get(f"/studio/dipendente/{self.dipendente_id}/servizi")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertGreaterEqual(len(data), 2)
        tipi = {s["tipo"] for s in data}
        self.assertIn(TipoServizio.ATTO.value, tipi)
        self.assertIn(TipoServizio.COMPROMESSO.value, tipi)