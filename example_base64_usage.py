#!/usr/bin/env python3
"""
Example usage of the MarkItDown Server base64 endpoint.

This demonstrates how to convert various file types to markdown using base64 encoding.
"""

import base64
import requests
import json

def convert_file_base64(file_path, server_url="http://localhost:8000"):
    """
    Convert a file to markdown using the base64 endpoint.
    
    Args:
        file_path: Path to the file to convert
        server_url: URL of the MarkItDown server
    
    Returns:
        dict: Response from the server
    """
    try:
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Encode to base64
        base64_content = base64.b64encode(file_content).decode('utf-8')
        
        # Prepare request
        request_data = {
            "content": base64_content,
            "filename": file_path.split('/')[-1]  # Extract filename
        }
        
        # Send request
        response = requests.post(f"{server_url}/convert-base64", json=request_data)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Error converting file: {e}")
        return None

def convert_text_base64(text_content, filename="document.txt", server_url="http://localhost:8000"):
    """
    Convert text content to markdown using the base64 endpoint.
    
    Args:
        text_content: Text content to convert
        filename: Optional filename hint for format detection
        server_url: URL of the MarkItDown server
    
    Returns:
        dict: Response from the server
    """
    try:
        # Encode to base64
        base64_content = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        
        # Prepare request
        request_data = {
            "content": base64_content,
            "filename": filename
        }
        
        # Send request
        response = requests.post(f"{server_url}/convert-base64", json=request_data)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Error converting text: {e}")
        return None

if __name__ == "__main__":
    print("MarkItDown Server Base64 Usage Examples")
    print("=" * 40)
    
    # Example 1: Convert HTML content
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Sample HTML</title>
</head>
<body>
    <h1>Welcome</h1>
    <p>This is a <strong>sample</strong> HTML document.</p>
    <ul>
        <li>Feature 1</li>
        <li>Feature 2</li>
    </ul>
</body>
</html>"""
    
    print("\n1. Converting HTML content:")
    result = convert_text_base64(html_content, "sample.html")
    if result:
        print(f"   Detected format: {result['detected_format']}")
        print(f"   Original length: {result['original_length']} bytes")
        print(f"   Converted length: {result['converted_length']} characters")
        print(f"   Converted content preview: {result['converted_content'][:100]}...")
    
    # Example 2: Convert CSV content
    csv_content = """Name,Age,City,Country
John Doe,25,New York,USA
Jane Smith,30,London,UK
Bob Johnson,35,Paris,France"""
    
    print("\n2. Converting CSV content:")
    result = convert_text_base64(csv_content, "sample.csv")
    if result:
        print(f"   Detected format: {result['detected_format']}")
        print(f"   Converted content preview: {result['converted_content'][:100]}...")
    
    # Example 3: Convert file (if test.pdf exists)
    print("\n3. Converting PDF file (if available):")
    try:
        result = convert_file_base64("test.pdf")
        if result:
            print(f"   Detected format: {result['detected_format']}")
            print(f"   Original filename: {result['original_filename']}")
            print(f"   Converted content preview: {result['converted_content'][:100]}...")
        else:
            print("   PDF file not found or conversion failed")
    except:
        print("   PDF file not available")
    
    # Example 4: JSON content (detection only)
    json_content = """{
    "name": "John Doe",
    "age": 30,
    "skills": ["Python", "JavaScript", "SQL"],
    "active": true
}"""
    
    print("\n4. Converting JSON content (detection only):")
    result = convert_text_base64(json_content, "sample.json")
    if result:
        print(f"   Detected format: {result['detected_format']}")
        print(f"   Note: JSON is detected but may not be fully convertible by MarkItDown")
    
    print("\nAll examples completed!") 