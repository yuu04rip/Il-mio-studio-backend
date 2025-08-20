import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_register_and_login(test_user_data):
    # test_user_data è una fixture che restituisce i dati di un utente NON registrato
    email = test_user_data["email"]
    password = test_user_data["password"]
    resp = client.post("/auth/register", json=test_user_data)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    resp = client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

def test_get_me(test_user_data):
    resp = client.post("/auth/register", json=test_user_data)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == test_user_data["email"]