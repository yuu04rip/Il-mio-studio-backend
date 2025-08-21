import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_archivia_servizio(test_servizio):
    print("DEBUG TEST: test_servizio.id =", test_servizio.id)
    print("DEBUG TEST: test_servizio.tipo =", getattr(test_servizio, 'tipo', None))
    print("DEBUG TEST: test_servizio.cliente_id =", getattr(test_servizio, 'cliente_id', None))
    response = client.post(f"/archivia?servizio_id={test_servizio.id}")
    print("DEBUG TEST: archivia response.status_code =", response.status_code)
    print("DEBUG TEST: archivia response.json =", response.json())
    assert response.status_code == 200
    assert response.json()["statoServizio"] is True

def test_inizializza_servizio(test_cliente):
    print("DEBUG TEST: test_cliente.id =", test_cliente.id)
    print("DEBUG TEST: test_cliente.utente =", test_cliente.utente)
    print("DEBUG TEST: test_cliente.utente.id =", getattr(test_cliente.utente, 'id', None))
    print("DEBUG TEST: test_cliente.utente.nome =", getattr(test_cliente.utente, 'nome', None))
    print("DEBUG TEST: test_cliente.utente.email =", getattr(test_cliente.utente, 'email', None))
    print("DEBUG TEST: test_cliente.utente.cognome =", getattr(test_cliente.utente, 'cognome', None))
    response = client.post("/inizializza", data={
        "cliente_nome": test_cliente.utente.nome,
        "tipo": "atto",  # <-- Valore valido dell'enum!
        "codiceCorrente": 123,
        "codiceServizio": 456
    })
    print("DEBUG TEST: inizializza response.status_code =", response.status_code)
    try:
        print("DEBUG TEST: inizializza response.json =", response.json())
    except Exception:
        print("DEBUG TEST: inizializza response.text =", response.text)
    assert response.status_code == 200
    assert response.json()["tipo"] == "atto"