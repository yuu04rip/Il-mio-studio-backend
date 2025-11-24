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

from app.api.routes import backup as backup_router

from app.models import tables, notaio, cliente_counters, documentazione


class BackupApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.TEST_DB_URL = "sqlite:///./test_backup_api.db"
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
        # Il router ha prefix="/backup" e qui aggiungiamo prefix="/backup":
        # path effettivi = /backup/backup/...
        app.include_router(backup_router.router, prefix="/backup", tags=["backup"])

        cls.app = app
        cls.client = TestClient(app)
        cls.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        try:
            os.remove("./test_backup_api.db")
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

        # cliente + dipendente
        u_cliente = User(
            email="cliente@example.com",
            nome="Mario",
            cognome="Rossi",
            password=hash_password("pwd"),
            ruolo=Role.CLIENTE,
        )
        db.add(u_cliente)
        db.commit()
        db.refresh(u_cliente)

        cliente = Cliente(utente_id=u_cliente.id)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)

        u_dip = User(
            email="dip@example.com",
            nome="Gianni",
            cognome="Verdi",
            password=hash_password("pwd"),
            ruolo=Role.DIPENDENTE,
        )
        db.add(u_dip)
        db.commit()
        db.refresh(u_dip)

        dip = DipendenteTecnico(
            utente_id=u_dip.id,
            tipo=TipoDipendenteTecnico.DIPENDENTE,
        )
        db.add(dip)
        db.commit()
        db.refresh(dip)

        now = datetime.now()
        s1 = Servizio(
            cliente_id=cliente.id,
            creato_da_id=dip.id,
            codiceCorrente=1,
            codiceServizio="SERV-000001",
            cliente_nome=u_cliente.nome,
            cliente_cognome=u_cliente.cognome,
            dataRichiesta=now,
            dataConsegna=now,
            statoServizio=StatoServizio.CREATO,
            tipo=TipoServizio.ATTO,
            is_deleted=False,
            archived=False,
        )
        db.add(s1)
        db.commit()
        db.refresh(s1)

        s2 = Servizio(
            cliente_id=cliente.id,
            creato_da_id=dip.id,
            codiceCorrente=2,
            codiceServizio="SERV-000002",
            cliente_nome=u_cliente.nome,
            cliente_cognome=u_cliente.cognome,
            dataRichiesta=now,
            dataConsegna=now,
            statoServizio=StatoServizio.CREATO,
            tipo=TipoServizio.PREVENTIVO,
            is_deleted=False,
            archived=True,
        )
        db.add(s2)
        db.commit()
        db.refresh(s2)

        self.s1_id = s1.id
        self.s2_id = s2.id

        db.close()

    def test_inizializza_backup(self):
        r = self.client.post("/backup/backup/inizializza")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("Backup inizializzato", r.text)

    def test_archivia_servizio(self):
        r = self.client.post(f"/backup/backup/archivia-servizio/{self.s1_id}")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertTrue(data["archived"])

    def test_dearchivia_servizio(self):
        r = self.client.put(f"/backup/backup/dearchivia-servizio/{self.s2_id}")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertFalse(data["archived"])

    def test_modifica_servizio_archiviato(self):
        r = self.client.put(
            f"/backup/backup/modifica-servizio-archiviato/{self.s1_id}",
            json={"archived": True},
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertTrue(data["archived"])

        r2 = self.client.put(
            f"/backup/backup/modifica-servizio-archiviato/{self.s1_id}",
            json={"archived": False},
        )
        self.assertEqual(r2.status_code, 200, r2.text)
        data2 = r2.json()
        self.assertFalse(data2["archived"])

    def test_elimina_servizio_archiviato(self):
        r = self.client.delete(f"/backup/backup/elimina-servizio-archiviato/{self.s2_id}")
        self.assertEqual(r.status_code, 200, r.text)

        r2 = self.client.delete(f"/backup/backup/elimina-servizio-archiviato/{self.s2_id}")
        self.assertEqual(r2.status_code, 404)

    def test_mostra_servizi_archiviati(self):
        r = self.client.get("/backup/backup/servizi-archiviati")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        ids = {s["id"] for s in data}
        self.assertIn(self.s2_id, ids)
        self.assertNotIn(self.s1_id, ids)