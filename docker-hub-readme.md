# MarkItDown Server

A FastAPI-based document conversion server that converts various document formats to Markdown using Microsoft's [markitdown](https://github.com/microsoft/markitdown) library.

## 🚀 Quick Start

```bash
# Run the server
docker run -d -p 8000:8000 --name markitdown-server YOUR_USERNAME/markitdown-server

# Test the server
curl http://localhost:8000/

# Convert a document
curl -X POST http://localhost:8000/convert \
  --data-binary @your-document.pdf \
  -H "Content-Type: application/octet-stream"
```

## 📋 Supported Formats

- ✅ **PDF** (.pdf) - Extract text from PDF documents
- ✅ **Word Documents** (.docx) - Microsoft Word files
- ✅ **Excel Spreadsheets** (.xlsx) - Microsoft Excel files  
- ✅ **PowerPoint** (.pptx) - Microsoft PowerPoint files
- ✅ **Images** (various formats) - OCR text extraction
- ✅ **Markdown** (.md) - Direct text processing

## 🔧 API Endpoints

### Health Check
```http
GET /
```
Returns server health status.

### Document Conversion
```http
POST /convert
Content-Type: application/octet-stream
```

Send document content as binary data in the request body.

**Response:**
```json
{
  "success": true,
  "original_length": 131997,
  "converted_content": "# Document Title\n\nExtracted content...",
  "converted_length": 4262
}
```

## 🐳 Docker Usage

### Basic Usage
```bash
docker run -d \
  --name markitdown-server \
  -p 8000:8000 \
  YOUR_USERNAME/markitdown-server
```

### With Docker Compose
```yaml
version: '3.8'
services:
  markitdown-server:
    image: YOUR_USERNAME/markitdown-server:latest
    container_name: markitdown-server
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### With File Uploads
```bash
# Create uploads directory
mkdir uploads

# Run with volume mount
docker run -d \
  --name markitdown-server \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads:ro \
  YOUR_USERNAME/markitdown-server
```

## 🔍 Examples

### Convert PDF
```bash
curl -X POST http://localhost:8000/convert \
  --data-binary @document.pdf \
  -H "Content-Type: application/octet-stream" \
  | jq .converted_content
```

### Convert DOCX
```bash
curl -X POST http://localhost:8000/convert \
  --data-binary @document.docx \
  -H "Content-Type: application/octet-stream"
```

### Convert Markdown Text
```bash
curl -X POST http://localhost:8000/convert \
  --data-binary "# Hello World\n\nThis is **bold** text." \
  -H "Content-Type: application/octet-stream"
```

## 🔒 Security Features

- **Non-root User**: Container runs as `appuser` for security
- **Health Checks**: Built-in container health monitoring
- **Input Validation**: Comprehensive error handling
- **Temporary Files**: Automatic cleanup of processed files

## 📊 Performance

- **Memory Usage**: ~50-100MB baseline, scales with file size
- **Processing Speed**: Fast text processing, depends on markitdown for binary files
- **Concurrent Requests**: FastAPI async support for multiple simultaneous conversions
- **File Size**: Tested with files up to 1MB+

## 🛠️ Configuration

### Environment Variables
```bash
docker run -e PYTHONUNBUFFERED=1 YOUR_USERNAME/markitdown-server
```

### Resource Limits
```bash
docker run -m 2g --cpus="1.0" YOUR_USERNAME/markitdown-server
```

## 🏥 Health Monitoring

The container includes built-in health checks:

```bash
# Check container health
docker ps
docker inspect markitdown-server | grep Health -A 5
```

## 🐞 Troubleshooting

### View Logs
```bash
docker logs markitdown-server
```

### Debug Mode
```bash
docker run -e LOG_LEVEL=DEBUG YOUR_USERNAME/markitdown-server
```

### Interactive Shell
```bash
docker exec -it markitdown-server /bin/bash
```

## 🔗 Links

- **GitHub Repository**: [Link to your repo]
- **API Documentation**: `http://localhost:8000/docs` (when running)
- **Microsoft MarkItDown**: https://github.com/microsoft/markitdown

## 📝 License

[Add your license information]

## 🤝 Contributing

[Add contribution guidelines]

---

**Built with FastAPI + Microsoft MarkItDown** 