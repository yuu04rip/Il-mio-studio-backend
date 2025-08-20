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
    response = client.post(
        "/documentazione/carica",
        data={"cliente_id": cliente_id, "tipo": "contratto"},
        files={"file": ("test.txt", BytesIO(file_content), "text/plain")}
    )
    assert response.status_code == 200
    doc_id = response.json()["id"]

    response = client.get(f"/documentazione/visualizza/{cliente_id}")
    assert response.status_code == 200
    assert any(doc["id"] == doc_id for doc in response.json())

def test_sostituisci_documentazione(test_documentazione):
    doc_id = test_documentazione.id
    file_content = b"new content"
    response = client.put(
        f"/documentazione/sostituisci/{doc_id}",
        files={"file": ("new.txt", BytesIO(file_content), "text/plain")}
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "new.txt"