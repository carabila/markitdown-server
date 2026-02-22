from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
from markitdown import MarkItDown
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)

app = FastAPI(
    title="MarkItDown Server",
    description="FastAPI service that converts documents to markdown using MarkItDown.",
    version="0.2.0",
)

markitdown = MarkItDown()


class Base64ConvertRequest(BaseModel):
    content: str
    filename: Optional[str] = None


def detect_office_format(content: bytes) -> str:
    content_str = content[:2000].decode("utf-8", errors="ignore").lower()
    if "word/" in content_str or "document.xml" in content_str:
        return ".docx"
    if "xl/" in content_str or "workbook.xml" in content_str:
        return ".xlsx"
    if "ppt/" in content_str or "presentation.xml" in content_str:
        return ".pptx"
    if "epub" in content_str or "container.xml" in content_str:
        return ".epub"
    return ".zip"


def detect_file_format(content: bytes) -> tuple[str, bool]:
    binary_signatures = {
        b"%PDF": ".pdf",
        b"PK\x03\x04": ".zip",
        b"PK\x05\x06": ".zip",
        b"PK\x07\x08": ".zip",
        b"\xff\xd8\xff": ".jpg",
        b"\x89PNG\r\n\x1a\n": ".png",
        b"GIF8": ".gif",
        b"BM": ".bmp",
        b"\x00\x00\x01\x00": ".ico",
        b"\x00\x00\x02\x00": ".cur",
        b"RIFF": ".wav",
        b"ID3": ".mp3",
        b"\xff\xfb": ".mp3",
        b"\xff\xf3": ".mp3",
        b"\xff\xf2": ".mp3",
        b"ftyp": ".m4a",
        b"OggS": ".ogg",
        b"fLaC": ".flac",
        b"EPUB": ".epub",
        b"ustar\x20\x20\x00": ".tar",
        b"ustar\x00": ".tar",
        b"\x1f\x8b": ".gz",
        b"BZh": ".bz2",
        b"\xfd7zXZ\x00": ".xz",
        b"7z\xbc\xaf\x27\x1c": ".7z",
        b"Rar!\x1a\x07\x00": ".rar",
        b"{\\rtf": ".rtf",
        b"\xff\xe0": ".jpg",
        b"WEBP": ".webp",
        b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a": ".png",
    }

    for signature, extension in binary_signatures.items():
        if content.startswith(signature):
            if extension == ".zip":
                return detect_office_format(content), False
            if extension == ".wav" and len(content) > 12:
                riff_type = content[8:12]
                if riff_type == b"WAVE":
                    return ".wav", False
                if riff_type == b"AVI ":
                    return ".avi", False
                if riff_type == b"WEBP":
                    return ".webp", False
                return ".wav", False
            if extension == ".m4a" and len(content) > 8 and content[4:8] == b"ftyp":
                return ".m4a", False
            return extension, False

    try:
        text_content = content.decode("utf-8")
        text_stripped = text_content.strip()
        if not text_stripped:
            return ".txt", True

        if text_stripped.startswith(("{", "[")) and text_stripped.endswith(("}", "]")):
            try:
                json.loads(text_content)
                return ".json", True
            except ValueError:
                pass

        if text_stripped.startswith("<"):
            lowered = text_content.lower()
            if any(tag in lowered for tag in ["<html", "<head", "<body", "<div", "<p", "<span"]):
                return ".html", True
            if lowered.startswith("<?xml") or "</" in text_content:
                return ".xml", True

        lines = text_content.split("\n")[:5]
        if len(lines) > 1:
            comma_counts = [line.count(",") for line in lines if line.strip()]
            if comma_counts and len(set(comma_counts)) == 1 and comma_counts[0] > 0:
                return ".csv", True
            tab_counts = [line.count("\t") for line in lines if line.strip()]
            if tab_counts and len(set(tab_counts)) == 1 and tab_counts[0] > 0:
                return ".tsv", True

        if any(marker in text_content for marker in ["# ", "## ", "### ", "* ", "- ", "1. ", "```", "[", "](", "**", "__"]):
            return ".md", True

        return ".txt", True
    except UnicodeDecodeError:
        return ".bin", False


def _convert_bytes_to_markdown(file_bytes: bytes, filename: Optional[str] = None) -> str:
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extension, is_text = detect_file_format(file_bytes)
    if filename and "." in filename:
        hinted = "." + filename.rsplit(".", 1)[1].lower()
        if extension in {".bin", ".txt"}:
            extension = hinted

    temp_file_path = None
    try:
        if is_text:
            try:
                text_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise HTTPException(status_code=400, detail="Invalid text encoding for detected text format") from exc
            if not text_content.strip():
                raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            with tempfile.NamedTemporaryFile(mode="w", suffix=extension, delete=False, encoding="utf-8") as temp_file:
                temp_file.write(text_content)
                temp_file_path = temp_file.name
        else:
            with tempfile.NamedTemporaryFile(mode="wb", suffix=extension, delete=False) as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name

        result = markitdown.convert(temp_file_path)
        return (result.text_content or "").strip()
    except HTTPException:
        raise
    except Exception as exc:
        message = str(exc)
        LOGGER.exception("Conversion failed")
        if "not supported" in message.lower() or "UnsupportedFormatException" in message:
            raise HTTPException(status_code=400, detail=f"Conversion failed: {message}") from exc
        raise HTTPException(status_code=500, detail=f"Failed to convert document: {message}") from exc
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                LOGGER.warning("Unable to remove temporary file: %s", temp_file_path)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/convert",
    response_class=PlainTextResponse,
    tags=["conversion"],
    summary="Convert a document to Markdown",
    response_description="Markdown representation of the uploaded document.",
)
async def convert_document(file: UploadFile = File(...)) -> PlainTextResponse:
    data = await file.read()
    markdown = _convert_bytes_to_markdown(data, file.filename)
    if not markdown:
        raise HTTPException(status_code=500, detail="Conversion returned empty markdown output")
    return PlainTextResponse(content=markdown, media_type="text/markdown; charset=utf-8")


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "message": "MarkItDown Server is running",
        "status": "healthy",
        "endpoints": {
            "health": "GET /health - Readiness probe",
            "convert": "POST /convert - Upload document using multipart/form-data field 'file'",
            "convert_base64": "POST /convert-base64 - Upload base64-encoded file content",
            "formats": "GET /formats - List supported file formats",
        },
        "version": "0.2.0",
    }


@app.get("/formats")
async def supported_formats() -> dict[str, object]:
    return {
        "detection_capabilities": {
            "description": "Formats the server can automatically detect from file content",
            "total_detectable": 32,
            "categories": {
                "documents": ["pdf", "docx", "xlsx", "pptx", "html", "txt", "rtf", "epub"],
                "images": ["jpg", "jpeg", "png", "gif", "bmp", "ico", "webp", "tiff"],
                "audio": ["wav", "mp3", "m4a", "flac", "ogg"],
                "text_data": ["csv", "json", "xml", "tsv", "md"],
                "archives": ["zip", "tar", "gz", "bz2", "xz", "7z"],
                "web": ["http_urls", "https_urls"],
            },
        },
        "conversion_support": {
            "description": "Formats that MarkItDown can actually convert to markdown",
            "fully_supported": {
                "documents": ["pdf", "docx", "xlsx", "pptx", "html", "txt", "rtf", "epub"],
                "images": ["jpg", "jpeg", "png", "gif", "bmp", "ico", "webp", "tiff"],
                "audio": ["wav", "mp3", "m4a", "flac", "ogg"],
                "text_data": ["csv", "tsv", "md"],
                "archives": ["zip"],
                "web": ["http_urls", "https_urls"],
            },
            "detection_only": {
                "description": "Detected but not convertible by MarkItDown",
                "formats": ["json", "xml", "tar", "gz", "bz2", "xz", "7z"],
            },
        },
    }


@app.post("/convert-base64")
async def convert_base64_document(request: Base64ConvertRequest) -> JSONResponse:
    if not request.content:
        raise HTTPException(status_code=400, detail="No base64 content provided")
    try:
        raw_content = base64.b64decode(request.content, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64 content: {exc}") from exc

    markdown = _convert_bytes_to_markdown(raw_content, request.filename)
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "original_filename": request.filename,
            "converted_content": markdown,
            "converted_length": len(markdown),
        },
    )


def run() -> None:
    import uvicorn

    uvicorn.run("markitdown_server.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
