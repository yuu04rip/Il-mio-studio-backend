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
from app.api.deps import get_db, get_current_user
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.services import Servizio
from app.models.enums import TipoServizio, TipoDipendenteTecnico, StatoServizio

from app.api.routes import gestore_studio as studio_router

from app.models import tables, notaio, cliente_counters, documentazione
from app.services.gestore_studio import GestoreStudio


class StudioServiziExtraApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.TEST_DB_URL = "sqlite:///./test_studio_servizi_extra_api.db"
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

        # In tests, many endpoints depend on get_current_user (auth).
        # Provide a test override that returns the dipendente user (if present).
        def override_get_current_user():
            db = TestingSessionLocal()
            try:
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
            os.remove("./test_studio_servizi_extra_api.db")
        except OSError:
            pass

    def setUp(self):
        db = self.SessionLocal()
        from app.models.dipendente import DipendenteTecnico
        from app.models.notaio import Notaio
        from app.models.cliente_counters import ClienteCounters
        from app.models.documentazione import Documentazione

        db.query(Documentazione).delete()
        db.query(Servizio).delete()
        db.query(ClienteCounters).delete()
        db.query(Notaio).delete()
        db.query(DipendenteTecnico).delete()
        db.query(Cliente).delete()
        db.query(User).delete()
        db.commit()

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

        dip = DipendenteTecnico(
            utente_id=dip_user.id,
            tipo=TipoDipendenteTecnico.DIPENDENTE,
        )
        db.add(dip)
        db.commit()
        db.refresh(dip)

        self.cliente_id = cliente.id
        self.dipendente_id = dip.id

        db.close()

    # ---- helpers ----

    def _crea_servizio(self, tipo: TipoServizio) -> int:
        resp = self.client.post(
            "/studio/servizi",
            json={
                "cliente_id": self.cliente_id,
                "tipo": tipo.value,
                "dipendente_id": self.dipendente_id,
            },
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        return resp.json()["id"]

    # ---- TEST ----

    def test_visualizza_servizi_lista_generale_e_cliente(self):
        s1 = self._crea_servizio(TipoServizio.ATTO)
        s2 = self._crea_servizio(TipoServizio.PREVENTIVO)

        # lista generale
        r_all = self.client.get("/studio/servizi")
        self.assertEqual(r_all.status_code, 200, r_all.text)
        data_all = r_all.json()
        ids = {s["id"] for s in data_all}
        self.assertIn(s1, ids)
        self.assertIn(s2, ids)

        # lista filtrata per cliente
        r_cli = self.client.get("/studio/servizi", params={"cliente_id": self.cliente_id})
        self.assertEqual(r_cli.status_code, 200, r_cli.text)
        data_cli = r_cli.json()
        ids_cli = {s["id"] for s in data_cli}
        self.assertEqual(ids_cli, ids)

    def test_cerca_servizio_per_codice(self):
        servizio_id = self._crea_servizio(TipoServizio.ATTO)
        db = self.SessionLocal()
        servizio = db.get(Servizio, servizio_id)
        codice = servizio.codiceServizio
        db.close()

        resp = self.client.get(f"/studio/servizi/codice/{codice}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["id"], servizio_id)
        self.assertEqual(data["codiceServizio"], codice)

    def test_archivia_e_visualizza_archiviati(self):
        servizio_id = self._crea_servizio(TipoServizio.ATTO)

        # archivia
        r_arch = self.client.post(f"/studio/servizi/{servizio_id}/archivia")
        self.assertEqual(r_arch.status_code, 200, r_arch.text)
        data_arch = r_arch.json()
        self.assertTrue(data_arch.get("archived") or data_arch.get("archiviato") or data_arch.get("is_deleted"))

        # lista archiviati
        r_list = self.client.get("/studio/servizi/archiviati")
        self.assertEqual(r_list.status_code, 200, r_list.text)
        data_list = r_list.json()
        ids = {s["id"] for s in data_list}
        self.assertIn(servizio_id, ids)

    def test_modifica_servizio_patch(self):
        servizio_id = self._crea_servizio(TipoServizio.PREVENTIVO)

        r = self.client.patch(
            f"/studio/servizi/{servizio_id}",
            json={"tipo": TipoServizio.ATTO.value},
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data["tipo"], TipoServizio.ATTO.value)

    def test_elimina_servizio_soft_and_distruggi(self):
        servizio_id = self._crea_servizio(TipoServizio.ATTO)

        # soft delete
        r_del = self.client.delete(f"/studio/servizi/{servizio_id}")
        self.assertEqual(r_del.status_code, 200, r_del.text)

        # non dovrebbe apparire in /servizi (filtra is_deleted)
        r_list = self.client.get("/studio/servizi")
        self.assertEqual(r_list.status_code, 200, r_list.text)
        data = r_list.json()
        ids = {s["id"] for s in data}
        self.assertNotIn(servizio_id, ids)

    def test_servizi_approvati_lista_globale(self):
        servizio_id = self._crea_servizio(TipoServizio.ATTO)
        self.client.post(f"/studio/servizi/{servizio_id}/inizializza")
        self.client.post(f"/studio/servizi/{servizio_id}/inoltra-notaio")
        self.client.post(f"/studio/servizi/{servizio_id}/approva")

        r = self.client.get("/studio/servizi/approvati")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        ids = {s["id"] for s in data}
        self.assertIn(servizio_id, ids)