import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

from main import app
from app.api.deps import get_db
from app.db.session import Base
from app.models.user import User
from app.models.cliente import Cliente
from app.models.documentazione import Documentazione
from app.models.services import Servizio
from app.models.enums import Role

TEST_DATABASE_URL = "sqlite:///./test.db"  # usa file, NON memory!
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(create_test_db):
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(autouse=True)
def override_get_db(db_session):
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_db

@pytest.fixture
def test_user_data():
    return {
        "email": f"user_test_{uuid.uuid4().hex}@example.com",
        "password": "testpass123",
        "nome": "Test",
        "cognome": "User",
        "numeroTelefonico": "123456789",
        "ruolo": "cliente"
    }

@pytest.fixture
def test_notaio_data():
    return {
        "email": f"notaio_test_{uuid.uuid4().hex}@example.com",
        "password": "testpass123",
        "nome": "Notaio",
        "cognome": "Test",
        "numeroTelefonico": "987654321",
        "ruolo": "notaio"
    }

@pytest.fixture
def test_cliente(db_session):
    random_email = f"cliente_{uuid.uuid4().hex}@example.com"
    user = User(email=random_email, password="hashed", nome="Cliente", cognome="Fixture", ruolo=Role.CLIENTE)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    cliente = Cliente(utente_id=user.id)
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente

@pytest.fixture
def test_documentazione(db_session, test_cliente):
    # Usa un valore valido dell'enum come tipo!
    doc = Documentazione(cliente_id=test_cliente.id, filename="test.txt", tipo="CARTA_IDENTITA", path="/tmp/test.txt")
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc

@pytest.fixture
def test_servizio(db_session, test_cliente):
    now = datetime.now()
    servizio = Servizio(
        cliente_id=test_cliente.id,
        tipo="ATTO",  # oppure "COMPROMESSO", "PREVENTIVO"
        codiceCorrente=123,
        codiceServizio=456,
        statoServizio=False,
        dataRichiesta=now,
        dataConsegna=now
    )
    db_session.add(servizio)
    db_session.commit()
    db_session.refresh(servizio)
    return servizio