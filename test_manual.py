#!/usr/bin/env python3
"""
Manual test script for the MarkItDown FastAPI server.
Run this script while the server is running to test functionality.
"""

import requests
import json

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_markdown_conversion():
    """Test markdown conversion endpoint"""
    print("\nTesting markdown conversion...")
    
    markdown_content = """# Hello World

This is a **test** markdown document with:

- List item 1  
- List item 2

```python
def hello():
    print('Hello, World!')
```

> This is a blockquote

[Link to Google](https://google.com)
"""
    
    try:
        response = requests.post(
            "http://localhost:8000/convert",
            data=markdown_content.encode('utf-8'),
            headers={"Content-Type": "application/octet-stream"}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['success']}")
            print(f"Original length: {result['original_length']}")
            print(f"Converted length: {result['converted_length']}")
            print(f"Converted content (first 200 chars): {result['converted_content'][:200]}...")
        else:
            print(f"Error: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Conversion test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with empty content"""
    print("\nTesting error handling...")
    
    try:
        response = requests.post(
            "http://localhost:8000/convert",
            data=b"",
            headers={"Content-Type": "application/octet-stream"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error handling test failed: {e}")
        return False

if __name__ == "__main__":
    print("MarkItDown Server Manual Test")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_health_check),
        ("Markdown Conversion", test_markdown_conversion),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
        print(f"✅ {test_name}: {'PASSED' if success else 'FAILED'}")
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The server is working correctly.")
    else:
        print("❌ Some tests failed. Check the server status.") 