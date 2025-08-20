import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_swagger_ui():
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "Swagger UI" in resp.text

def test_redoc():
    resp = client.get("/redoc")
    assert resp.status_code == 200
    assert "<title" in resp.text and "ReDoc" in resp.text