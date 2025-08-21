import sys
import os
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_carica_visualizza_documentazione(test_cliente):
    cliente_id = test_cliente.id
    file_content = b"test content"
    print(f"DEBUG TEST: Invio data={{'cliente_id': {cliente_id}, 'tipo': 'atto'}}, files={{'file': ...}}")
    response = client.post(
        "/documentazione/carica",
        data={"cliente_id": cliente_id, "tipo": "atto"},
        files={"file": ("test.txt", BytesIO(file_content), "text/plain")}
    )
    print("DEBUG TEST /carica: status_code =", response.status_code)
    try:
        print("DEBUG TEST /carica: response JSON =", response.json())
    except Exception:
        print("DEBUG TEST /carica: response TEXT =", response.text)
    assert response.status_code == 200
    doc_id = response.json()["id"]

    response = client.get(f"/documentazione/visualizza/{cliente_id}")
    print("DEBUG TEST /visualizza: status_code =", response.status_code)
    print("DEBUG TEST /visualizza: response JSON =", response.json())
    assert response.status_code == 200
    assert any(doc["id"] == doc_id for doc in response.json())

def test_sostituisci_documentazione(test_documentazione):
    doc_id = test_documentazione.id
    file_content = b"new content"
    print(f"DEBUG TEST: Sostituisco doc_id={doc_id}, file='new.txt'")
    response = client.put(
        f"/documentazione/sostituisci/{doc_id}",
        files={"file": ("new.txt", BytesIO(file_content), "text/plain")}
    )
    print("DEBUG TEST /sostituisci: status_code =", response.status_code)
    try:
        print("DEBUG TEST /sostituisci: response JSON =", response.json())
    except Exception:
        print("DEBUG TEST /sostituisci: response TEXT =", response.text)
    assert response.status_code == 200
    assert response.json()["filename"] == "new.txt"