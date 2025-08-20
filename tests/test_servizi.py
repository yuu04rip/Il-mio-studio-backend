import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_archivia_servizio(test_servizio):
    response = client.post("/archivia", data={"servizio_id": test_servizio.id})
    assert response.status_code == 200
    assert response.json()["statoServizio"] is True

def test_inizializza_servizio(test_cliente):
    response = client.post("/inizializza", data={
        "cliente_nome": test_cliente.utente.nome,
        "tipo": "base",
        "codiceCorrente": 123,
        "codiceServizio": 456
    })
    assert response.status_code == 200
    assert response.json()["tipo"] == "base"