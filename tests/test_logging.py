import io
import logging

from fastapi import FastAPI, File, UploadFile
from fastapi.testclient import TestClient

from markitdown_server.logging import add_request_logging_middleware, configure_logging


def test_configure_logging_accepts_standard_log_level(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setenv("LOG_LEVEL", "WARN")

    configure_logging(stream=stream)

    assert logging.getLogger().level == logging.WARN


def test_configure_logging_defaults_when_log_level_invalid(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setenv("LOG_LEVEL", "verbose")

    configure_logging(stream=stream)
    logging.getLogger("markitdown_server.logging").info("probe")

    assert logging.getLogger().level == logging.INFO
    assert "Invalid LOG_LEVEL 'verbose'; using INFO" in stream.getvalue()


def test_request_logging_logs_json_body_at_debug(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    configure_logging(stream=stream)

    app = FastAPI()
    add_request_logging_middleware(app)

    @app.post("/items")
    async def create_item(payload: dict) -> dict:
        return payload

    response = TestClient(app).post("/items", json={"name": "doc"})

    assert response.status_code == 200
    log_output = stream.getvalue()
    assert "Request body: {\"name\":\"doc\"}" in log_output
    assert "HTTP request completed method=POST path=/items status_code=200" in log_output


def test_request_logging_redacts_base64_content_at_debug(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    configure_logging(stream=stream)

    app = FastAPI()
    add_request_logging_middleware(app)

    @app.post("/convert-base64")
    async def convert_base64(payload: dict) -> dict:
        return {"size": len(payload["content"])}

    response = TestClient(app).post(
        "/convert-base64",
        json={"content": "base64-document", "filename": "sample.pdf"},
    )

    assert response.status_code == 200
    log_output = stream.getvalue()
    assert '"content":"[redacted]"' in log_output
    assert "base64-document" not in log_output
