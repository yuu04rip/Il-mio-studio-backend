import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_add_dipendente(test_user_data):
    # Passa tipo come query param, dati utente direttamente come body
    # Usa un valore valido dell'enum: 'contabile', 'notaio', 'assistente'
    response = client.post("/add-dipendente?tipo=notaio", json=test_user_data)
    print(response.status_code, response.json()) # Debug
    assert response.status_code == 200

def test_add_notaio(test_notaio_data):
    # Passa codiceNotarile come query param, dati utente direttamente come body
    response = client.post("/add-notaio?codice_notarile=1001", json=test_notaio_data)
    print(response.status_code, response.json()) # Debug
    assert response.status_code == 200