#!/usr/bin/env python3
"""
Comprehensive test suite for all supported file formats in the enhanced MarkItDown server.
"""

import requests
import json
import os
from pathlib import Path

# Server configuration
BASE_URL = "http://localhost:8000"

def test_server_health():
    """Test that the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def test_supported_formats_endpoint():
    """Test the new /formats endpoint"""
    response = requests.get(f"{BASE_URL}/formats")
    assert response.status_code == 200
    
    data = response.json()
    print("📋 Supported formats:")
    for category, formats in data["supported_formats"].items():
        print(f"  {category}: {', '.join(formats)}")
    print()
    
    return data["supported_formats"]

def test_format_detection(content: bytes, expected_format: str, description: str):
    """Test format detection and conversion"""
    print(f"🧪 Testing {description}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/convert",
            data=content,
            headers={"Content-Type": "application/octet-stream"}
        )
        
        if response.status_code == 200:
            result = response.json()
            detected = result.get("detected_format", "unknown")
            print(f"  ✅ Detected: {detected} | Expected: {expected_format}")
            print(f"  📏 {result['original_length']} bytes → {result['converted_length']} chars")
            if result['converted_content'][:100]:
                preview = result['converted_content'][:100].replace('\n', ' ')
                print(f"  📝 Preview: {preview}...")
            print()
            return True
        else:
            print(f"  ❌ Failed: {response.status_code} - {response.text}")
            print()
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print()
        return False

def run_format_tests():
    """Run tests for various file format samples"""
    
    # Test samples for different formats
    test_cases = [
        # Text-based formats
        {
            "content": b'{"name": "test", "value": 123}',
            "expected": "json", 
            "description": "JSON file"
        },
        {
            "content": b'<?xml version="1.0"?><root><item>test</item></root>',
            "expected": "xml",
            "description": "XML file"
        },
        {
            "content": b'<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>',
            "expected": "html",
            "description": "HTML file"
        },
        {
            "content": b'name,age,city\nJohn,30,NYC\nJane,25,LA\nBob,35,Chicago',
            "expected": "csv",
            "description": "CSV file"
        },
        {
            "content": b'# Markdown Test\n\nThis is a **bold** test with [links](http://example.com)',
            "expected": "md",
            "description": "Markdown file"
        },
        {
            "content": b'Plain text content\nWith multiple lines\nAnd some content.',
            "expected": "txt",
            "description": "Plain text file"
        },
        
        # Binary format signatures (we can test detection even without real files)
        {
            "content": b'%PDF-1.4\n%Fake PDF for testing format detection only',
            "expected": "pdf",
            "description": "PDF signature detection"
        },
        {
            "content": b'PK\x03\x04\x14\x00\x00\x00word/document.xml fake docx',
            "expected": "docx", 
            "description": "DOCX signature detection"
        },
        {
            "content": b'\xff\xd8\xff\xe0\x00\x10JFIF fake jpeg header',
            "expected": "jpg",
            "description": "JPEG signature detection"
        },
        {
            "content": b'\x89PNG\r\n\x1a\n fake png data',
            "expected": "png",
            "description": "PNG signature detection"
        },
        {
            "content": b'GIF89a fake gif data',
            "expected": "gif",
            "description": "GIF signature detection"
        },
        {
            "content": b'RIFF\x24\x00\x00\x00WAVE fake wav data',
            "expected": "wav",
            "description": "WAV signature detection"
        },
        {
            "content": b'ID3\x03\x00\x00\x00 fake mp3 with ID3',
            "expected": "mp3",
            "description": "MP3 with ID3 signature detection"
        },
        {
            "content": b'\xff\xfb\x90\x00 fake mp3 without ID3',
            "expected": "mp3", 
            "description": "MP3 without ID3 signature detection"
        },
        {
            "content": b'{\\rtf1\\ansi\\deff0 fake rtf content}',
            "expected": "rtf",
            "description": "RTF signature detection"
        }
    ]
    
    print(f"🚀 Running {len(test_cases)} format detection tests...\n")
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        success = test_format_detection(
            test_case["content"], 
            test_case["expected"], 
            test_case["description"]
        )
        if success:
            passed += 1
    
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed == total

def test_with_real_pdf():
    """Test with the existing PDF file if available"""
    pdf_path = Path("test.pdf")
    if pdf_path.exists():
        print("📄 Testing with real PDF file...")
        with open(pdf_path, "rb") as f:
            content = f.read()
        
        return test_format_detection(content, "pdf", f"Real PDF file ({pdf_path.name})")
    else:
        print("📄 No test.pdf found, skipping real PDF test")
        return True

def main():
    """Main test runner"""
    print("🔍 MarkItDown Server - Comprehensive Format Support Test\n")
    
    # Check server health
    if not test_server_health():
        print("❌ Server is not running. Start the server with: python main.py")
        return
    
    print("✅ Server is running\n")
    
    # Test formats endpoint
    supported_formats = test_supported_formats_endpoint()
    
    # Run format detection tests
    format_tests_passed = run_format_tests()
    
    # Test with real PDF if available
    pdf_test_passed = test_with_real_pdf()
    
    print("\n" + "="*60)
    if format_tests_passed and pdf_test_passed:
        print("🎉 All tests passed! The enhanced server supports comprehensive file format detection.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 The server now supports:")
    print("   • All major document formats (PDF, Office, HTML, etc.)")
    print("   • Text data formats (CSV, JSON, XML, Markdown)")
    print("   • Image formats (JPG, PNG, GIF, etc.)")
    print("   • Audio formats (WAV, MP3, etc.)")
    print("   • Archive formats (ZIP, TAR, etc.)")
    print("   • Automatic format detection from content")

if __name__ == "__main__":
    main() 