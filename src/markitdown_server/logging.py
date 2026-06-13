"""Shared logging helpers for the MarkItDown service."""
import json
import logging
import os
import sys
import time
from typing import IO

from fastapi import FastAPI, Request


_DEFAULT_LOG_LEVEL = "INFO"
_LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.FATAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "WARN": logging.WARN,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}
_TEXT_CONTENT_TYPES = ("application/json", "application/x-www-form-urlencoded", "application/xml", "text/")
_MAX_BODY_LOG_BYTES = 16_384
_REDACTED_JSON_FIELDS = {"content", "file", "password", "token", "api_key", "apikey", "secret"}


def _resolve_log_level() -> tuple[int, str | None]:
    raw_level = os.getenv("LOG_LEVEL") or _read_dotenv_value("LOG_LEVEL")
    if raw_level is None or not raw_level.strip():
        return _LOG_LEVELS[_DEFAULT_LOG_LEVEL], "LOG_LEVEL not set; using INFO"
    normalized = raw_level.strip().upper()
    if normalized in _LOG_LEVELS:
        return _LOG_LEVELS[normalized], None
    accepted = ", ".join(_LOG_LEVELS)
    return _LOG_LEVELS[_DEFAULT_LOG_LEVEL], f"Invalid LOG_LEVEL '{raw_level}'; using INFO. Accepted values: {accepted}"


def _read_dotenv_value(key: str) -> str | None:
    if not os.path.exists(".env"):
        return None
    try:
        with open(".env", encoding="utf-8") as env_file:
            for line in env_file:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                name, value = stripped.split("=", 1)
                if name.strip() == key:
                    return value.strip().strip('"').strip("'")
    except OSError:
        return None
    return None


def configure_logging(level: int | None = None, stream: IO[str] | None = None) -> None:
    resolved_level, startup_message = (level, None) if level is not None else _resolve_log_level()
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root = logging.getLogger()
    root.setLevel(resolved_level)
    root.handlers.clear()
    root.addHandler(handler)
    if startup_message:
        logging.getLogger(__name__).info(startup_message)


def add_request_logging_middleware(app: FastAPI) -> None:
    logger = logging.getLogger("markitdown_server.request")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
        started = time.perf_counter()
        body = await _read_loggable_body(logger, request)
        _log_request_start(logger, request, body)

        if body is not None:
            async def receive() -> dict:
                # Replays the consumed body so FastAPI handlers can still parse it.
                return {"type": "http.request", "body": body, "more_body": False}

            request._receive = receive  # type: ignore[attr-defined]
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.exception("HTTP request failed method=%s path=%s duration_ms=%.2f", request.method, request.url.path, duration_ms)
            raise
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "HTTP request completed method=%s path=%s status_code=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


async def _read_loggable_body(logger: logging.Logger, request: Request) -> bytes | None:
    content_type = request.headers.get("content-type", "")
    if not logger.isEnabledFor(logging.DEBUG) or not _is_text_content_type(content_type):
        return None
    return await request.body()


def _log_request_start(logger: logging.Logger, request: Request, body: bytes | None) -> None:
    content_type = request.headers.get("content-type", "")
    content_length = request.headers.get("content-length", str(len(body or b"")))
    logger.info(
        "HTTP request started method=%s path=%s query=%s client=%s content_type=%s content_length=%s",
        request.method,
        request.url.path,
        request.url.query,
        request.client.host if request.client else "unknown",
        content_type or "unknown",
        content_length,
    )
    if not logger.isEnabledFor(logging.DEBUG):
        return
    if body is not None and _is_text_content_type(content_type):
        logger.debug("Request body: %s", _format_body(body, content_type))
    else:
        logger.debug("Request body summary: content_type=%s content_length=%s body_bytes=%d", content_type or "unknown", content_length, len(body or b""))


def _is_text_content_type(content_type: str) -> bool:
    lowered = content_type.lower()
    return any(token in lowered for token in _TEXT_CONTENT_TYPES)


def _format_body(body: bytes, content_type: str) -> str:
    trimmed = body[:_MAX_BODY_LOG_BYTES]
    text = trimmed.decode("utf-8", errors="replace")
    if "application/json" in content_type.lower():
        try:
            text = json.dumps(_redact_json(json.loads(text)), separators=(",", ":"), ensure_ascii=False)
        except json.JSONDecodeError:
            pass
    if len(body) > _MAX_BODY_LOG_BYTES:
        text = f"{text}... [truncated {len(body) - _MAX_BODY_LOG_BYTES} bytes]"
    return text


def _redact_json(value: object) -> object:
    if isinstance(value, dict):
        return {key: "[redacted]" if key.lower() in _REDACTED_JSON_FIELDS else _redact_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_json(item) for item in value]
    return value
