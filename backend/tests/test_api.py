import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import get_session

@pytest.fixture(name="client")
def client_fixture():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(test_engine)

    def get_test_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_api_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_upload_and_list_transactions(client: TestClient):
    csv_bytes = (
        "Data valuta,Data,Parola chiave,Movimento,Importo,Valuta,Disponibile,Valuta,Osservazioni\n"
        "24/03/2026,24/03/2026,Esselunga,Spesa,-45.50,EUR,1000.0,EUR,Spesa alimentare\n"
    ).encode("utf-8")

    files = {"files": ("Patrimonio - BBVA.csv", csv_bytes, "text/csv")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["imported"] == 1

    # Check transactions endpoint
    tx_resp = client.get("/api/transactions")
    assert tx_resp.status_code == 200
    txs = tx_resp.json()["items"]
    assert len(txs) == 1
    assert txs[0]["amount"] == -45.50
    assert txs[0]["payee"] == "Esselunga"

    # Check accounts endpoint
    acc_resp = client.get("/api/accounts")
    assert acc_resp.status_code == 200
    accs = acc_resp.json()
    assert len(accs) == 1
    assert accs[0]["name"] == "BBVA"
    assert accs[0]["current_balance"] == -45.50
