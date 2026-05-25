from fastapi.testclient import TestClient

from main import app


def run_smoke():
    client = TestClient(app)

    r = client.get("/")
    assert r.status_code == 200, f"Root endpoint failed: {r.status_code}"

    r2 = client.get("/api/documents")
    assert r2.status_code == 200, f"Documents endpoint failed: {r2.status_code}"

    print("OK: backend smoke tests passed")


if __name__ == "__main__":
    run_smoke()
