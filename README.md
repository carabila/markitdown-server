# MarkItDown Markdown Conversion Service

A FastAPI service that converts documents into Markdown using [Microsoft MarkItDown](https://github.com/microsoft/markitdown).

The primary API contract is compatible with `docling-server`:
- `POST /convert` accepts `multipart/form-data` with `file`
- response body is Markdown (`text/markdown`)
- `GET /health` returns `{"status":"ok"}`

## Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/latest/) >= 0.8
- Docker & Docker Compose (optional)

## Local Development
1. Install dependencies (uses `.venv` in project root):
   ```bash
   uv sync --extra dev
   ```
2. Start the API:
   ```bash
   ./scripts/start_service.sh
   ```

## API Usage
### Primary (Docling-compatible) endpoints
- `POST /convert` — upload a document via `multipart/form-data` field named `file`
- `GET /health` — readiness probe

Example:
```bash
curl -X POST \
  -F "file=@./path/to/document.pdf" \
  http://localhost:8000/convert
```

### Extra endpoints (non-primary compatibility surface)
- `GET /` — extended status response
- `GET /formats` — format detection/conversion matrix
- `POST /convert-base64` — base64 conversion helper

## Scripts
- `scripts/start_service.sh` — starts uvicorn from `.venv`
- `scripts/process_documents.sh` — batch converts files from `documents/` into `response/`
- `scripts/push-docker-variants.sh` — push multi-arch docker images

Batch example:
```bash
./scripts/process_documents.sh
```

Start service with the standard script (same pattern as other services):
```bash
./scripts/start_service.sh
```

Push to your Docker Hub account using the shared multi-arch workflow:
```bash
docker login
./scripts/push-docker-variants.sh --namespace <your-dockerhub-username>
```

Optional: choose a different image name or builder:
```bash
./scripts/push-docker-variants.sh --namespace <your-dockerhub-username> --image markitdown-server --builder <buildx-builder>
```

## Docker
Build and run:
```bash
docker build -t markitdown-server .
docker run --rm -p 8000:8000 markitdown-server
```

Or compose:
```bash
docker compose up --build
```

## Tests
Run tests with project `.venv`:
```bash
.venv/bin/pytest
```
