import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestMarkitdownServer:
    """Test suite for the MarkItDown FastAPI server"""
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "MarkItDown Server is running"
        assert data["status"] == "healthy"
    
    def test_convert_simple_markdown(self):
        """Test converting simple markdown content"""
        markdown_content = "# Hello World\n\nThis is a **test** markdown document."
        
        response = client.post(
            "/convert",
            content=markdown_content.encode('utf-8'),
            headers={"Content-Type": "application/octet-stream"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["original_length"] == len(markdown_content)
        assert "converted_content" in data
        assert len(data["converted_content"]) > 0
    
    def test_convert_complex_markdown(self):
        """Test converting markdown with various elements"""
        markdown_content = """# Main Title

## Subtitle

This is a paragraph with **bold** and *italic* text.

### List Example
- Item 1
- Item 2
- Item 3

### Code Example
```python
def hello():
    print("Hello, World!")
```

[Link to Google](https://google.com)

> This is a blockquote

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
"""
        
        response = client.post(
            "/convert",
            content=markdown_content.encode('utf-8'),
            headers={"Content-Type": "application/octet-stream"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["original_length"] == len(markdown_content)
        assert "converted_content" in data
    
    def test_convert_empty_content(self):
        """Test with empty content"""
        response = client.post(
            "/convert",
            content=b"",
            headers={"Content-Type": "application/octet-stream"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "No content provided" in data["detail"]
    
    def test_convert_whitespace_only(self):
        """Test with whitespace-only content"""
        response = client.post(
            "/convert",
            content=b"   \n\t  \n  ",
            headers={"Content-Type": "application/octet-stream"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Empty content provided" in data["detail"]
    
    def test_convert_invalid_encoding(self):
        """Test with invalid UTF-8 encoding"""
        # Create invalid UTF-8 bytes
        invalid_bytes = b'\xff\xfe\x00\x00'
        
        response = client.post(
            "/convert",
            content=invalid_bytes,
            headers={"Content-Type": "application/octet-stream"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid content encoding" in data["detail"]
    
    def test_convert_unicode_content(self):
        """Test with Unicode content"""
        markdown_content = """# Unicode Test 🚀

This document contains various Unicode characters:
- Emoji: 😀 🎉 🔥
- Accented characters: café, naïve, résumé
- Symbols: α β γ δ ε
- Asian characters: 你好世界
"""
        
        response = client.post(
            "/convert",
            content=markdown_content.encode('utf-8'),
            headers={"Content-Type": "application/octet-stream"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["original_length"] == len(markdown_content)
    
    def test_convert_large_content(self):
        """Test with larger content"""
        # Generate a large markdown document
        large_content = "# Large Document\n\n"
        for i in range(100):
            large_content += f"## Section {i+1}\n\n"
            large_content += f"This is paragraph {i+1} with some **bold** and *italic* text. " * 10
            large_content += "\n\n"
        
        response = client.post(
            "/convert",
            content=large_content.encode('utf-8'),
            headers={"Content-Type": "application/octet-stream"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["original_length"] == len(large_content)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 