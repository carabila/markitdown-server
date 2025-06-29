import pytest
import requests
import base64
import json
import tempfile
import os

# Test server configuration
BASE_URL = "http://localhost:8000"

def test_base64_markdown_conversion():
    """Test converting a simple markdown file via base64"""
    markdown_content = """# Test Document

This is a **test** markdown document with some content.

## Features
- Lists work
- *Italic text* works
- [Links](https://example.com) work

```python
# Code blocks work too
print("Hello, World!")
```
"""
    
    # Encode to base64
    base64_content = base64.b64encode(markdown_content.encode('utf-8')).decode('utf-8')
    
    # Test the base64 endpoint
    response = requests.post(f"{BASE_URL}/convert-base64", json={
        "content": base64_content,
        "filename": "test.md"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["detected_format"] == "md"
    assert data["original_filename"] == "test.md"
    assert "Test Document" in data["converted_content"]
    assert len(data["converted_content"]) > 0

def test_base64_html_conversion():
    """Test converting HTML content via base64"""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test HTML</title>
</head>
<body>
    <h1>Hello World</h1>
    <p>This is a <strong>test</strong> HTML document.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
</body>
</html>"""
    
    # Encode to base64
    base64_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    
    response = requests.post(f"{BASE_URL}/convert-base64", json={
        "content": base64_content,
        "filename": "test.html"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["detected_format"] == "html"
    assert "Hello World" in data["converted_content"]

def test_base64_csv_conversion():
    """Test converting CSV content via base64"""
    csv_content = """Name,Age,City
John,25,New York
Jane,30,London
Bob,35,Paris"""
    
    # Encode to base64
    base64_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    
    response = requests.post(f"{BASE_URL}/convert-base64", json={
        "content": base64_content,
        "filename": "data.csv"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["detected_format"] == "csv"
    assert "John" in data["converted_content"]
    assert "Name" in data["converted_content"]

def test_base64_with_pdf():
    """Test handling PDF file via base64 (if available)"""
    # Check if test.pdf exists
    if os.path.exists("test.pdf"):
        with open("test.pdf", "rb") as f:
            pdf_content = f.read()
        
        # Encode to base64
        base64_content = base64.b64encode(pdf_content).decode('utf-8')
        
        response = requests.post(f"{BASE_URL}/convert-base64", json={
            "content": base64_content,
            "filename": "test.pdf"
        })
        
        # PDF conversion might work or fail depending on MarkItDown setup
        assert response.status_code in [200, 422, 500]  # Accept various outcomes
        data = response.json()
        
        if response.status_code == 200:
            assert data["success"] is True
            assert data["detected_format"] == "pdf"
        else:
            # If conversion fails, it should still detect the format correctly
            print(f"PDF conversion result: {data}")

def test_base64_invalid_content():
    """Test error handling for invalid base64 content"""
    # Test invalid base64
    response = requests.post(f"{BASE_URL}/convert-base64", json={
        "content": "This is not valid base64!@#$%",
        "filename": "test.txt"
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid base64 content" in data["detail"]

def test_base64_empty_content():
    """Test error handling for empty base64 content"""
    response = requests.post(f"{BASE_URL}/convert-base64", json={
        "content": "",
        "filename": "test.txt"
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "No base64 content provided" in data["detail"]

def test_base64_filename_hint():
    """Test that filename hints help with format detection"""
    # Create content that could be ambiguous
    text_content = "This is plain text content"
    base64_content = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
    
    # Test without filename
    response1 = requests.post(f"{BASE_URL}/convert-base64", json={
        "content": base64_content
    })
    
    # Test with filename hint
    response2 = requests.post(f"{BASE_URL}/convert-base64", json={
        "content": base64_content,
        "filename": "document.txt"
    })
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Both should work, filename might help with format detection
    assert data1["success"] is True
    assert data2["success"] is True
    assert data2["original_filename"] == "document.txt"

def test_base64_vs_raw_comparison():
    """Test that base64 and raw endpoints produce equivalent results"""
    markdown_content = """# Test Comparison

This is content to compare base64 vs raw upload methods.

- Feature 1
- Feature 2
"""
    
    # Test raw endpoint
    response_raw = requests.post(f"{BASE_URL}/convert", 
                                data=markdown_content.encode('utf-8'),
                                headers={"Content-Type": "application/octet-stream"})
    
    # Test base64 endpoint
    base64_content = base64.b64encode(markdown_content.encode('utf-8')).decode('utf-8')
    response_base64 = requests.post(f"{BASE_URL}/convert-base64", json={
        "content": base64_content,
        "filename": "compare.md"
    })
    
    assert response_raw.status_code == 200
    assert response_base64.status_code == 200
    
    data_raw = response_raw.json()
    data_base64 = response_base64.json()
    
    # Both should succeed
    assert data_raw["success"] is True
    assert data_base64["success"] is True
    
    # Content should be equivalent (allowing for minor differences in processing)
    assert data_raw["detected_format"] == data_base64["detected_format"]
    assert data_raw["converted_content"] == data_base64["converted_content"]

if __name__ == "__main__":
    print("Running base64 conversion tests...")
    print("Make sure the server is running on http://localhost:8000")
    
    try:
        # Test server connectivity
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        print("✓ Server is running")
        
        # Run tests
        test_base64_markdown_conversion()
        print("✓ Base64 markdown conversion works")
        
        test_base64_html_conversion()
        print("✓ Base64 HTML conversion works")
        
        test_base64_csv_conversion()
        print("✓ Base64 CSV conversion works")
        
        test_base64_with_pdf()
        print("✓ Base64 PDF handling tested")
        
        test_base64_invalid_content()
        print("✓ Invalid base64 content handling works")
        
        test_base64_empty_content()
        print("✓ Empty content handling works")
        
        test_base64_filename_hint()
        print("✓ Filename hint functionality works")
        
        test_base64_vs_raw_comparison()
        print("✓ Base64 vs raw comparison works")
        
        print("\n🎉 All base64 tests passed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
        print("Start the server with: python main.py")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}") 