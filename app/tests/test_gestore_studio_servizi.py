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
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.enums import TipoServizio, StatoServizio, TipoDipendenteTecnico
from app.services.gestore_studio import GestoreStudio
from app.core.security import hash_password

# IMPORT CRITICI per registrare tutte le tabelle nel Base.metadata
from app.models import tables  # dipendente_servizio, servizio_documentazione, ...
from app.models import services  # Servizio
from app.models import notaio    # Notaio
from app.models import cliente_counters  # ClienteCounters
from app.models import documentazione    # Documentazione

class GestoreStudioServiziTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.TEST_DB_URL = "sqlite:///./test_studio_servizi.db"
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
        cls.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        try:
            os.remove("./test_studio_servizi.db")
        except OSError:
            pass

    def setUp(self):
        self.db = self.SessionLocal()
        # pulizia base
        from app.models.dipendente import DipendenteTecnico
        from app.models.notaio import Notaio
        from app.models.cliente_counters import ClienteCounters
        from app.models.services import Servizio
        from app.models.documentazione import Documentazione

        self.db.query(Documentazione).delete()
        self.db.query(Servizio).delete()
        self.db.query(ClienteCounters).delete()
        self.db.query(Notaio).delete()
        self.db.query(DipendenteTecnico).delete()
        self.db.query(Cliente).delete()
        self.db.query(User).delete()
        self.db.commit()

        # crea utente cliente + Cliente
        self.cliente_user = User(
            email="cliente@example.com",
            nome="Mario",
            cognome="Rossi",
            password=hash_password("pwd"),
            ruolo=Role.CLIENTE,
        )
        self.db.add(self.cliente_user)
        self.db.commit()
        self.db.refresh(self.cliente_user)

        self.cliente = Cliente(utente_id=self.cliente_user.id)
        self.db.add(self.cliente)
        self.db.commit()
        self.db.refresh(self.cliente)

        # crea dipendente tecnico (che sarà creatore del servizio)
        self.dip_user = User(
            email="dip@example.com",
            nome="Gianni",
            cognome="Verdi",
            password=hash_password("pwd"),
            ruolo=Role.DIPENDENTE,
        )
        self.db.add(self.dip_user)
        self.db.commit()
        self.db.refresh(self.dip_user)

        self.dipendente = DipendenteTecnico(
            utente_id=self.dip_user.id,
            tipo=TipoDipendenteTecnico.DIPENDENTE,
        )
        self.db.add(self.dipendente)
        self.db.commit()
        # non è strettamente necessario fare refresh qui
        # self.db.refresh(self.dipendente)

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_aggiungi_servizio_minimo(self):
        gestore = GestoreStudio(self.db)
        now = datetime.now()

        servizio = gestore.aggiungi_servizio(
            cliente_id=self.cliente.id,
            tipo=TipoServizio.ATTO,
            codiceCorrente=None,      # verrà generato
            codiceServizio=None,      # verrà generato
            dataRichiesta=now,
            dataConsegna=now,
            dipendente_id=self.dipendente.id,
        )

        self.assertIsNotNone(servizio)
        self.assertIsNotNone(servizio.id)
        self.assertEqual(servizio.cliente_id, self.cliente.id)
        self.assertEqual(servizio.tipo, TipoServizio.ATTO)
        self.assertEqual(servizio.statoServizio, StatoServizio.CREATO)

        # il creatore è il dipendente passato
        self.assertEqual(servizio.creato_da_id, self.dipendente.id)

        # snapshot corretti del cliente
        self.assertEqual(servizio.cliente_nome, self.cliente_user.nome)
        self.assertEqual(servizio.cliente_cognome, self.cliente_user.cognome)

        # codiceCorrente e codiceServizio generati
        self.assertGreater(servizio.codiceCorrente, 0)
        self.assertTrue(servizio.codiceServizio.startswith("SERV-"))


    def test_flusso_stati_inizializza_inoltra_approva(self):
        gestore = GestoreStudio(self.db)
        now = datetime.now()

        servizio = gestore.aggiungi_servizio(
            cliente_id=self.cliente.id,
            tipo=TipoServizio.COMPROMESSO,
            codiceCorrente=None,
            codiceServizio=None,
            dataRichiesta=now,
            dataConsegna=now,
            dipendente_id=self.dipendente.id,
        )
        self.db.commit()
        self.db.refresh(servizio)

        # 1) CREATO -> IN_LAVORAZIONE
        servizio = gestore.inizializza_servizio(servizio.id)
        self.assertIsNotNone(servizio)
        self.assertEqual(servizio.statoServizio, StatoServizio.IN_LAVORAZIONE)

        # 2) IN_LAVORAZIONE -> IN_ATTESA_APPROVAZIONE
        servizio = gestore.inoltra_servizio_notaio(servizio.id)
        self.assertIsNotNone(servizio)
        self.assertEqual(servizio.statoServizio, StatoServizio.IN_ATTESA_APPROVAZIONE)

        # 3) IN_ATTESA_APPROVAZIONE -> APPROVATO
        servizio = gestore.approva_servizio(servizio.id)
        self.assertIsNotNone(servizio)
        self.assertEqual(servizio.statoServizio, StatoServizio.APPROVATO)

    def test_flusso_rifiuta_servizio(self):
        gestore = GestoreStudio(self.db)
        now = datetime.now()

        servizio = gestore.aggiungi_servizio(
            cliente_id=self.cliente.id,
            tipo=TipoServizio.PREVENTIVO,
            codiceCorrente=None,
            codiceServizio=None,
            dataRichiesta=now,
            dataConsegna=now,
            dipendente_id=self.dipendente.id,
        )
        self.db.commit()
        self.db.refresh(servizio)

        servizio = gestore.inizializza_servizio(servizio.id)
        servizio = gestore.inoltra_servizio_notaio(servizio.id)
        servizio = gestore.rifiuta_servizio(servizio.id)

        self.assertIsNotNone(servizio)
        self.assertEqual(servizio.statoServizio, StatoServizio.RIFIUTATO)

    def test_visualizza_servizi_cliente(self):
        gestore = GestoreStudio(self.db)
        now = datetime.now()

        s1 = gestore.aggiungi_servizio(
            cliente_id=self.cliente.id,
            tipo=TipoServizio.ATTO,
            codiceCorrente=None,
            codiceServizio=None,
            dataRichiesta=now,
            dataConsegna=now,
            dipendente_id=self.dipendente.id,
        )
        s2 = gestore.aggiungi_servizio(
            cliente_id=self.cliente.id,
            tipo=TipoServizio.PREVENTIVO,
            codiceCorrente=None,
            codiceServizio=None,
            dataRichiesta=now,
            dataConsegna=now,
            dipendente_id=self.dipendente.id,
        )
        self.db.commit()

        servizi = gestore.visualizza_servizi_cliente(self.cliente.id)
        self.assertEqual(len(servizi), 2)
        tipi = {s.tipo for s in servizi}
        self.assertIn(TipoServizio.ATTO, tipi)
        self.assertIn(TipoServizio.PREVENTIVO, tipi)

    def test_visualizza_lavoro_da_svolgere_e_inizializzati(self):
        gestore = GestoreStudio(self.db)
        now = datetime.now()

        s1 = gestore.aggiungi_servizio(
            cliente_id=self.cliente.id,
            tipo=TipoServizio.ATTO,
            codiceCorrente=None,
            codiceServizio=None,
            dataRichiesta=now,
            dataConsegna=now,
            dipendente_id=self.dipendente.id,
        )
        s2 = gestore.aggiungi_servizio(
            cliente_id=self.cliente.id,
            tipo=TipoServizio.COMPROMESSO,
            codiceCorrente=None,
            codiceServizio=None,
            dataRichiesta=now,
            dataConsegna=now,
            dipendente_id=self.dipendente.id,
        )
        self.db.commit()

        # all'inizio entrambi in CREATO
        da_svolgere = gestore.visualizza_lavoro_da_svolgere(self.dipendente.id)
        self.assertEqual({s.id for s in da_svolgere}, {s1.id, s2.id})

        gestore.inizializza_servizio(s1.id)

        da_svolgere = gestore.visualizza_lavoro_da_svolgere(self.dipendente.id)
        self.assertEqual({s.id for s in da_svolgere}, {s2.id})

        inizializzati = gestore.visualizza_servizi_inizializzati(self.dipendente.id)
        self.assertEqual({s.id for s in inizializzati}, {s1.id})