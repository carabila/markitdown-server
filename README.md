# MarkItDown Server

A FastAPI server that converts markdown content using Microsoft's markitdown library.

## Features

- **POST /convert** endpoint that accepts raw binary markdown content
- Converts markdown to HTML using Microsoft's markitdown library
- Comprehensive error handling for invalid inputs
- Health check endpoint
- Full test coverage

## Requirements

- Python 3.8+
- FastAPI
- uvicorn
- markitdown

## Installation

1. Clone or download this project
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

### Option 1: Local Development

Start the server with:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or run directly:

```bash
python main.py
```

### Option 2: Docker (Recommended for Production)

**Quick Start:**
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or using Docker directly
docker build -t markitdown-server .
docker run -d -p 8000:8000 --name markitdown-server markitdown-server
```

**Requirements:**
- Docker and Docker Compose installed
- See `docker-setup.md` for detailed Docker deployment guide

The server will be available at `http://localhost:8000`

## API Endpoints

### GET /
Health check endpoint that returns server status.

**Response:**
```json
{
  "message": "MarkItDown Server is running",
  "status": "healthy"
}
```

### POST /convert
Converts markdown content to HTML.

**Request:**
- Method: POST
- Content-Type: application/octet-stream (or any binary type)
- Body: Raw binary markdown content (UTF-8 encoded)

**Response:**
```json
{
  "success": true,
  "original_length": 45,
  "converted_content": "<h1>Hello World</h1>\n<p>This is a <strong>test</strong>.</p>",
  "converted_length": 58
}
```

**Error Response:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Usage Examples

### Using curl

```bash
# Convert a markdown file
curl -X POST http://localhost:8000/convert \
  --data-binary @example.md \
  -H "Content-Type: application/octet-stream"

# Convert inline markdown
echo "# Hello World" | curl -X POST http://localhost:8000/convert \
  --data-binary @- \
  -H "Content-Type: application/octet-stream"
```

### Using Python requests

```python
import requests

# Convert markdown string
markdown_content = "# Hello World\n\nThis is **bold** text."
response = requests.post(
    "http://localhost:8000/convert",
    data=markdown_content.encode('utf-8'),
    headers={"Content-Type": "application/octet-stream"}
)

result = response.json()
print(result["converted_content"])
```

### Using JavaScript/fetch

```javascript
const markdownContent = "# Hello World\n\nThis is **bold** text.";

fetch('http://localhost:8000/convert', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/octet-stream',
  },
  body: new TextEncoder().encode(markdownContent)
})
.then(response => response.json())
.then(data => console.log(data.converted_content));
```

## Testing

Run the test suite:

```bash
pytest test_server.py -v
```

The tests cover:
- Health check endpoint
- Simple and complex markdown conversion
- Error handling (empty content, invalid encoding)
- Unicode content support
- Large content handling

## Error Handling

The server handles various error conditions:

- **400 Bad Request**: Empty content, invalid encoding, or malformed input
- **500 Internal Server Error**: MarkItDown conversion failures or unexpected errors

All errors include descriptive messages to help diagnose issues.

## Development

For development, install additional dependencies:

```bash
pip install pytest pytest-asyncio httpx
```

The server uses structured logging to help with debugging and monitoring. 