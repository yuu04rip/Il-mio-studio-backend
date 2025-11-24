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
from app.api.deps import get_db
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.enums import TipoDipendenteTecnico, TipoServizio, StatoServizio, TipoDocumentazione
from app.models.services import Servizio
from app.models.documentazione import Documentazione

from app.api.routes import documents as documentazione_router

from app.models import tables, notaio, cliente_counters, services as services_module, documentazione as documentazione_module


class DocumentazioneApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.TEST_DB_URL = "sqlite:///./test_documentazione_api.db"
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
        app.include_router(documentazione_router.router, prefix="/documentazione", tags=["documentazione-download"])

        cls.app = app
        cls.client = TestClient(app)
        cls.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        try:
            os.remove("./test_documentazione_api.db")
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

        # cliente
        user_cli = User(
            email="cliente@example.com",
            nome="Mario",
            cognome="Rossi",
            password=hash_password("pwd"),
            ruolo=Role.CLIENTE,
        )
        db.add(user_cli)
        db.commit()
        db.refresh(user_cli)

        cliente = Cliente(utente_id=user_cli.id)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)

        # dipendente per creato_da
        user_dip = User(
            email="dip@example.com",
            nome="Gianni",
            cognome="Verdi",
            password=hash_password("pwd"),
            ruolo=Role.DIPENDENTE,
        )
        db.add(user_dip)
        db.commit()
        db.refresh(user_dip)

        dip = DipendenteTecnico(
            utente_id=user_dip.id,
            tipo=TipoDipendenteTecnico.DIPENDENTE,
        )
        db.add(dip)
        db.commit()
        db.refresh(dip)

        from datetime import datetime
        now = datetime.now()
        servizio = Servizio(
            cliente_id=cliente.id,
            creato_da_id=dip.id,
            codiceCorrente=1,
            codiceServizio="SERV-000001",
            cliente_nome=user_cli.nome,
            cliente_cognome=user_cli.cognome,
            dataRichiesta=now,
            dataConsegna=now,
            statoServizio=StatoServizio.CREATO,
            tipo=TipoServizio.ATTO,
            is_deleted=False,
            archived=False,
        )
        db.add(servizio)
        db.commit()
        db.refresh(servizio)

        self.cliente_id = cliente.id
        self.servizio_id = servizio.id

        db.close()

    def test_carica_visualizza_e_elimina_documentazione_servizio(self):
        file_content = b"contenuto di prova"
        files = {
            "file": ("test.txt", file_content, "text/plain"),
        }
        data = {
            "tipo": TipoDocumentazione.CARTA_IDENTITA.value,
        }

        resp = self.client.post(
            f"/documentazione/servizi/{self.servizio_id}/documenti/carica",
            files=files,
            data=data,
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        doc = resp.json()
        doc_id = doc["id"]
        self.assertEqual(doc["filename"], "test.txt")

        # verifica nel DB che sia legato a servizio e cliente corretti
        db = self.SessionLocal()
        d_db = db.get(Documentazione, doc_id)
        self.assertIsNotNone(d_db)
        self.assertEqual(d_db.servizio_id, self.servizio_id)
        self.assertEqual(d_db.cliente_id, self.cliente_id)
        db.close()

        r_list = self.client.get(f"/documentazione/servizi/{self.servizio_id}/documenti")
        self.assertEqual(r_list.status_code, 200, r_list.text)
        data_list = r_list.json()
        self.assertEqual(len(data_list), 1)
        self.assertEqual(data_list[0]["id"], doc_id)

        r_down = self.client.get(f"/documentazione/download/{doc_id}")
        self.assertEqual(r_down.status_code, 200, r_down.text)
        self.assertEqual(r_down.content, file_content)

        r_del = self.client.delete(f"/documentazione/servizi/{self.servizio_id}/documenti/{doc_id}")
        self.assertEqual(r_del.status_code, 200, r_del.text)

        r_list2 = self.client.get(f"/documentazione/servizi/{self.servizio_id}/documenti")
        self.assertEqual(r_list2.status_code, 200, r_list2.text)
        self.assertEqual(r_list2.json(), [])

    def test_sostituisci_documentazione_servizio(self):
        file_content = b"prima versione"
        files = {
            "file": ("test.txt", file_content, "text/plain"),
        }
        data = {"tipo": TipoDocumentazione.CARTA_IDENTITA.value}
        resp = self.client.post(
            f"/documentazione/servizi/{self.servizio_id}/documenti/carica",
            files=files,
            data=data,
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        doc_id = resp.json()["id"]

        file_content2 = b"seconda versione"
        files2 = {
            "file": ("test2.txt", file_content2, "text/plain"),
        }
        r_put = self.client.put(
            f"/documentazione/servizi/{self.servizio_id}/documenti/{doc_id}/sostituisci",
            files=files2,
        )
        self.assertEqual(r_put.status_code, 200, r_put.text)
        doc2 = r_put.json()
        self.assertEqual(doc2["id"], doc_id)
        self.assertEqual(doc2["filename"], "test2.txt")

        r_down = self.client.get(f"/documentazione/download/{doc_id}")
        self.assertEqual(r_down.status_code, 200, r_down.text)
        self.assertEqual(r_down.content, file_content2)

    def test_carica_visualizza_sostituisci_documentazione_cliente(self):
        file_content = b"doc cliente 1"
        files = {
            "file": ("cliente1.pdf", file_content, "application/pdf"),
        }
        data = {
            "cliente_id": str(self.cliente_id),
            "tipo": TipoDocumentazione.CARTA_IDENTITA.value,
        }

        resp = self.client.post(
            "/documentazione/documenti/carica",
            files=files,
            data=data,
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        doc = resp.json()
        doc_id = doc["id"]
        self.assertEqual(doc["filename"], "cliente1.pdf")

        db = self.SessionLocal()
        d_db = db.get(Documentazione, doc_id)
        self.assertIsNotNone(d_db)
        self.assertEqual(d_db.cliente_id, self.cliente_id)
        self.assertIsNone(d_db.servizio_id)
        db.close()

        r_list = self.client.get(f"/documentazione/documenti/visualizza/{self.cliente_id}")
        self.assertEqual(r_list.status_code, 200, r_list.text)
        data_list = r_list.json()
        self.assertEqual(len(data_list), 1)
        self.assertEqual(data_list[0]["id"], doc_id)

        file_content2 = b"doc cliente 1 - nuova versione"
        files2 = {
            "file": ("cliente1_v2.pdf", file_content2, "application/pdf"),
        }
        r_put = self.client.put(
            f"/documentazione/documenti/sostituisci/{doc_id}",
            files=files2,
        )
        self.assertEqual(r_put.status_code, 200, r_put.text)
        doc2 = r_put.json()
        self.assertEqual(doc2["id"], doc_id)
        self.assertEqual(doc2["filename"], "cliente1_v2.pdf")

        r_down = self.client.get(f"/documentazione/download/{doc_id}")
        self.assertEqual(r_down.status_code, 200, r_down.text)
        self.assertEqual(r_down.content, file_content2)