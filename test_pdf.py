#!/usr/bin/env python3
"""
Test script to verify PDF to markdown conversion using the MarkItDown FastAPI server.
"""

import requests
import json

def test_pdf_conversion():
    """Test PDF to markdown conversion"""
    print("Testing PDF to Markdown conversion...")
    print("=" * 50)
    
    # Read the PDF file as binary
    try:
        with open('test.pdf', 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        print(f"✅ Successfully read test.pdf ({len(pdf_content):,} bytes)")
        
    except FileNotFoundError:
        print("❌ test.pdf file not found")
        return False
    except Exception as e:
        print(f"❌ Error reading PDF file: {e}")
        return False
    
    # Send PDF to conversion endpoint
    try:
        print("📤 Sending PDF to server for conversion...")
        response = requests.post(
            "http://localhost:8000/convert",
            data=pdf_content,
            headers={"Content-Type": "application/octet-stream"},
            timeout=30  # 30 second timeout for PDF processing
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Conversion successful!")
            print(f"📊 Success: {result['success']}")
            print(f"📏 Original size: {result['original_length']:,} bytes")
            print(f"📄 Converted size: {result['converted_length']:,} characters")
            
            converted_content = result['converted_content']
            
            # Check if content looks like markdown
            markdown_indicators = [
                ('Headers', '#' in converted_content),
                ('Lists', ('-' in converted_content or '*' in converted_content)),
                ('Bold text', '**' in converted_content),
                ('Links', '[' in converted_content and ']' in converted_content),
                ('Non-empty', len(converted_content.strip()) > 0)
            ]
            
            print("\n📋 Markdown Format Analysis:")
            for indicator, present in markdown_indicators:
                status = "✅" if present else "⚠️"
                print(f"  {status} {indicator}: {'Present' if present else 'Not detected'}")
            
            # Show first 500 characters of converted content
            print(f"\n📝 First 500 characters of converted markdown:")
            print("-" * 50)
            print(converted_content[:500])
            if len(converted_content) > 500:
                print("...")
            print("-" * 50)
            
            # Save converted content to file
            try:
                with open('test_pdf_converted.md', 'w', encoding='utf-8') as md_file:
                    md_file.write(converted_content)
                print("💾 Converted content saved to 'test_pdf_converted.md'")
            except Exception as e:
                print(f"⚠️ Could not save to file: {e}")
            
            return True
            
        else:
            print(f"❌ Conversion failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - PDF processing took too long")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on http://localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_server_health():
    """Quick health check before PDF test"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False

if __name__ == "__main__":
    print("MarkItDown Server PDF Test")
    print("=" * 50)
    
    # First check if server is running
    if test_server_health():
        print()
        success = test_pdf_conversion()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 PDF conversion test PASSED!")
            print("📄 The server successfully converted PDF to markdown format.")
        else:
            print("❌ PDF conversion test FAILED!")
            print("🔧 Check server logs for more details.")
    else:
        print("\n❌ Cannot test PDF conversion - server is not accessible.")
        print("💡 Make sure to start the server with:")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000") 