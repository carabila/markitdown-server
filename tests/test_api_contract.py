from __future__ import annotations

from fastapi.testclient import TestClient

from markitdown_server.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_convert_multipart_returns_text_markdown() -> None:
    payload = b"# Hello\n\nThis is a test document."
    response = client.post(
        "/convert",
        files={"file": ("sample.md", payload, "text/markdown")},
    )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.text.strip()


def test_convert_empty_file_returns_400() -> None:
    response = client.post(
        "/convert",
        files={"file": ("empty.md", b"", "text/markdown")},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_legacy_base64_endpoint_is_still_available() -> None:
    import base64

    content = base64.b64encode(b"# Hello from base64").decode("ascii")
    response = client.post("/convert-base64", json={"content": content, "filename": "sample.md"})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert "converted_content" in data
