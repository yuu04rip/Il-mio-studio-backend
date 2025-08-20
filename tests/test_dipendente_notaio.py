import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_add_dipendente(test_user_data):
    response = client.post("/add-dipendente", json={
        "user_data": test_user_data,
        "tipo": "TECNICO"  # Usa il valore ESATTO dell'enum!
    })
    print(response.status_code, response.json()) # Debug
    assert response.status_code == 200

def test_add_notaio(test_notaio_data):
    response = client.post("/add-notaio", json={
        "user_data": test_notaio_data,
        "codiceNotarile": 1001
    })
    print(response.status_code, response.json()) # Debug
    assert response.status_code == 200