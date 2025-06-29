# MarkItDown Server

A FastAPI server that converts markdown content using Microsoft's markitdown library.

## Features

- **POST /convert** endpoint that accepts raw binary document content
- **POST /convert-base64** endpoint that accepts base64-encoded document content
- Supports multiple file formats: PDF, DOCX, XLSX, PPTX, HTML, CSV, TXT, RTF, EPUB, images, and more
- Uses Microsoft's markitdown library for robust document conversion
- Comprehensive error handling for invalid inputs
- Automatic file format detection from content
- Optional filename hints for better format detection
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
  "status": "healthy",
  "endpoints": {
    "convert": "POST /convert - Upload raw binary file content",
    "convert_base64": "POST /convert-base64 - Upload base64-encoded file content with optional filename",
    "formats": "GET /formats - List supported file formats"
  },
  "version": "1.2.0"
}
```

### GET /formats
Returns information about supported file formats.

**Response:**
```json
{
  "detection_capabilities": {
    "description": "Formats the server can automatically detect from file content",
    "total_detectable": 32,
    "categories": {
      "documents": ["pdf", "docx", "xlsx", "pptx", "html", "txt", "rtf", "epub"],
      "images": ["jpg", "jpeg", "png", "gif", "bmp", "ico", "webp", "tiff"],
      "audio": ["wav", "mp3", "m4a", "flac", "ogg"],
      "text_data": ["csv", "json", "xml", "tsv", "md"],
      "archives": ["zip", "tar", "gz", "bz2", "xz", "7z"]
    }
  },
  "conversion_support": {
    "description": "Formats that MarkItDown can actually convert to markdown",
    "fully_supported": {
      "documents": ["pdf", "docx", "xlsx", "pptx", "html", "txt", "rtf", "epub"],
      "images": ["jpg", "jpeg", "png", "gif", "bmp", "ico", "webp", "tiff"],
      "audio": ["wav", "mp3", "m4a", "flac", "ogg"],
      "text_data": ["csv", "tsv", "md"],
      "archives": ["zip"]
    }
  }
}
```

### POST /convert
Converts document content to markdown using raw binary upload.

**Request:**
- Method: POST
- Content-Type: application/octet-stream (or any binary type)
- Body: Raw binary document content

**Response:**
```json
{
  "success": true,
  "detected_format": "html",
  "original_length": 245,
  "converted_content": "# Hello World\n\nThis is **bold** text.",
  "converted_length": 32,
  "content_type": "text"
}
```

### POST /convert-base64
Converts document content to markdown using base64-encoded upload.

**Request:**
- Method: POST
- Content-Type: application/json
- Body:
```json
{
  "content": "SGVsbG8gV29ybGQ=",
  "filename": "document.txt"
}
```

**Response:**
```json
{
  "success": true,
  "detected_format": "txt",
  "original_filename": "document.txt",
  "original_length": 11,
  "converted_content": "Hello World",
  "converted_length": 11,
  "content_type": "text"
}
```

**Error Response:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Usage Examples

### Using curl (Raw Binary)

```bash
# Convert a document file
curl -X POST http://localhost:8000/convert \
  --data-binary @document.pdf \
  -H "Content-Type: application/octet-stream"

# Convert inline text
echo "# Hello World" | curl -X POST http://localhost:8000/convert \
  --data-binary @- \
  -H "Content-Type: application/octet-stream"
```

### Using curl (Base64)

```bash
# Convert a file using base64
base64_content=$(base64 -i document.pdf)
curl -X POST http://localhost:8000/convert-base64 \
  -H "Content-Type: application/json" \
  -d "{\"content\":\"$base64_content\",\"filename\":\"document.pdf\"}"

# Convert text using base64
base64_content=$(echo "# Hello World" | base64)
curl -X POST http://localhost:8000/convert-base64 \
  -H "Content-Type: application/json" \
  -d "{\"content\":\"$base64_content\",\"filename\":\"hello.md\"}"
```

### Using Python requests (Raw Binary)

```python
import requests

# Convert text content
text_content = "# Hello World\n\nThis is **bold** text."
response = requests.post(
    "http://localhost:8000/convert",
    data=text_content.encode('utf-8'),
    headers={"Content-Type": "application/octet-stream"}
)

result = response.json()
print(result["converted_content"])

# Convert file
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/convert",
        data=f.read(),
        headers={"Content-Type": "application/octet-stream"}
    )
    result = response.json()
    print(f"Detected format: {result['detected_format']}")
    print(result["converted_content"])
```

### Using Python requests (Base64)

```python
import requests
import base64

# Convert text content using base64
text_content = "# Hello World\n\nThis is **bold** text."
base64_content = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')

response = requests.post(
    "http://localhost:8000/convert-base64",
    json={
        "content": base64_content,
        "filename": "hello.md"
    }
)

result = response.json()
print(f"Detected format: {result['detected_format']}")
print(result["converted_content"])

# Convert file using base64
with open("document.pdf", "rb") as f:
    file_content = f.read()
    base64_content = base64.b64encode(file_content).decode('utf-8')
    
    response = requests.post(
        "http://localhost:8000/convert-base64",
        json={
            "content": base64_content,
            "filename": "document.pdf"
        }
    )
    
    result = response.json()
    print(f"Original filename: {result['original_filename']}")
    print(f"Detected format: {result['detected_format']}")
    print(result["converted_content"])
```

### Using JavaScript/fetch (Raw Binary)

```javascript
const textContent = "# Hello World\n\nThis is **bold** text.";

fetch('http://localhost:8000/convert', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/octet-stream',
  },
  body: new TextEncoder().encode(textContent)
})
.then(response => response.json())
.then(data => {
  console.log('Detected format:', data.detected_format);
  console.log('Converted content:', data.converted_content);
});
```

### Using JavaScript/fetch (Base64)

```javascript
const textContent = "# Hello World\n\nThis is **bold** text.";
const base64Content = btoa(textContent);

fetch('http://localhost:8000/convert-base64', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    content: base64Content,
    filename: 'hello.md'
  })
})
.then(response => response.json())
.then(data => {
  console.log('Original filename:', data.original_filename);
  console.log('Detected format:', data.detected_format);
  console.log('Converted content:', data.converted_content);
});

// Convert file using base64
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];

const reader = new FileReader();
reader.onload = function(e) {
  const base64Content = btoa(e.target.result);
  
  fetch('http://localhost:8000/convert-base64', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content: base64Content,
      filename: file.name
    })
  })
  .then(response => response.json())
  .then(data => console.log(data.converted_content));
};
reader.readAsBinaryString(file);
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_server.py test_base64.py -v

# Run specific test files
python test_server.py      # Original functionality tests
python test_base64.py      # Base64 functionality tests
```

The tests cover:
- Health check endpoint
- Raw binary document conversion (all supported formats)
- Base64 document conversion (all supported formats)
- Error handling (empty content, invalid encoding, invalid base64)
- Unicode content support
- File format detection and filename hints
- Comparison between raw binary and base64 endpoints
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