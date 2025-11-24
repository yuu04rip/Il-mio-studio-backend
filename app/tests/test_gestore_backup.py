import os
import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.db.session import Base
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.enums import TipoServizio, TipoDipendenteTecnico, StatoServizio
from app.models.services import Servizio
from app.services.gestore_backup import GestoreBackup


class GestoreBackupTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # DB di test completamente separato, in memoria
        cls.TEST_DB_URL = "sqlite+pysqlite:///:memory:"
        cls.engine = create_engine(
            cls.TEST_DB_URL,
            echo=False,
            future=True,
        )

        # IMPORTA tutti i moduli che definiscono tabelle,
        # così Base.metadata le conosce prima di create_all
        from app.models import (
            tables,             # tabelle di associazione (dipendente_servizio, ecc.)
            services,           # Servizio
            notaio,             # Notaio
            cliente_counters,   # ClienteCounters
            documentazione,     # Documentazione
            dipendente,         # DipendenteTecnico & co.
            cliente,            # Cliente
            user,               # User
        )

        Base.metadata.create_all(bind=cls.engine)

        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine, future=True
        )
        cls.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.db = self.SessionLocal()
        # pulizia tabelle principali
        from app.models.dipendente import DipendenteTecnico
        from app.models.notaio import Notaio
        from app.models.cliente_counters import ClienteCounters
        from app.models.documentazione import Documentazione

        self.db.query(Documentazione).delete()
        self.db.query(Servizio).delete()
        self.db.query(ClienteCounters).delete()
        self.db.query(Notaio).delete()
        self.db.query(DipendenteTecnico).delete()
        self.db.query(Cliente).delete()
        self.db.query(User).delete()
        self.db.commit()

        # crea cliente + dipendente per associare i servizi
        self.user_cliente = User(
            email="cliente@example.com",
            nome="Mario",
            cognome="Rossi",
            password=hash_password("pwd"),
            ruolo=Role.CLIENTE,
        )
        self.db.add(self.user_cliente)
        self.db.commit()
        self.db.refresh(self.user_cliente)

        self.cliente = Cliente(utente_id=self.user_cliente.id)
        self.db.add(self.cliente)
        self.db.commit()
        self.db.refresh(self.cliente)

        self.user_dip = User(
            email="dip@example.com",
            nome="Gianni",
            cognome="Verdi",
            password=hash_password("pwd"),
            ruolo=Role.DIPENDENTE,
        )
        self.db.add(self.user_dip)
        self.db.commit()
        self.db.refresh(self.user_dip)

        self.dip = DipendenteTecnico(
            utente_id=self.user_dip.id,
            tipo=TipoDipendenteTecnico.DIPENDENTE,
        )
        self.db.add(self.dip)
        self.db.commit()
        self.db.refresh(self.dip)

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def _crea_servizio(self, archived: bool = False) -> Servizio:
        now = datetime.now()
        s = Servizio(
            cliente_id=self.cliente.id,
            creato_da_id=self.dip.id,
            codiceCorrente=1,
            codiceServizio="SERV-000001",
            cliente_nome=self.user_cliente.nome,
            cliente_cognome=self.user_cliente.cognome,
            dataRichiesta=now,
            dataConsegna=now,
            statoServizio=StatoServizio.CREATO,
            tipo=TipoServizio.ATTO,
            is_deleted=False,
            archived=archived,
        )
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def test_archivia_e_mostra_servizi_archiviati(self):
        backup = GestoreBackup(self.db)
        s = self._crea_servizio(archived=False)

        # all'inizio non è archiviato
        self.assertFalse(s.archived)

        # archivia
        s_arch = backup.archivia_servizio(s)
        self.assertTrue(s_arch.archived)

        # lista archiviati
        lst = backup.mostra_servizi_archiviati()
        self.assertEqual(len(lst), 1)
        self.assertEqual(lst[0].id, s.id)

    def test_dearchivia_servizio(self):
        backup = GestoreBackup(self.db)
        s = self._crea_servizio(archived=True)

        self.assertTrue(s.archived)
        s2 = backup.dearchivia_servizio(s)
        self.assertFalse(s2.archived)

    def test_modifica_servizio_archiviato_flag(self):
        backup = GestoreBackup(self.db)
        s = self._crea_servizio(archived=False)

        s2 = backup.modifica_servizio_archiviato(s, archived=True)
        self.assertTrue(s2.archived)

        s3 = backup.modifica_servizio_archiviato(s2, archived=False)
        self.assertFalse(s3.archived)

    def test_elimina_servizio_archiviato(self):
        backup = GestoreBackup(self.db)
        s = self._crea_servizio(archived=True)

        ok = backup.elimina_servizio_archiviato(s.id)
        self.assertTrue(ok)
        # non esiste più
        s_db = self.db.get(Servizio, s.id)
        self.assertIsNone(s_db)

        # ripetere su id inesistente -> False
        ok2 = backup.elimina_servizio_archiviato(s.id)
        self.assertFalse(ok2)

    def test_get_servizio_archiviato(self):
        backup = GestoreBackup(self.db)
        s = self._crea_servizio(archived=True)
        s2 = self._crea_servizio(archived=False)

        found = backup.get_servizio_archiviato(s.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, s.id)

        not_found = backup.get_servizio_archiviato(s2.id)
        self.assertIsNone(not_found)