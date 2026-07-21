from fastapi.testclient import TestClient

from main import app


def run_smoke():
    client = TestClient(app)

    r = client.get("/")
    assert r.status_code == 200, f"Root endpoint failed: {r.status_code}"

    r2 = client.get("/api/documents")
    assert r2.status_code == 200, f"Documents endpoint failed: {r2.status_code}"

    run_retrieval_checks(client)

    print("OK: backend smoke tests passed")


def run_retrieval_checks(client: TestClient) -> None:
    """Known queries must retrieve their expected source document."""
    cases = [
        ("How does the retriever rank document chunks?", "architecture.md"),
        ("How do I run the backend with a production ASGI server?", "setup-deployment.md"),
        ("Which directory does the retriever scan for local documents?", "sample.md"),
    ]
    for question, expected_source in cases:
        r = client.post("/api/query", json={"question": question, "top_k": 4})
        assert r.status_code == 200, f"Query endpoint failed: {r.status_code}"
        sources = [s["source"] for s in r.json()["sources"]]
        assert expected_source in sources, (
            f"Retrieval regression: {question!r} returned {sources}, expected {expected_source}"
        )


if __name__ == "__main__":
    run_smoke()
