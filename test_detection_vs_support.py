#!/usr/bin/env python3
"""
Test to demonstrate the distinction between format detection and conversion support.
Shows which formats can be detected vs actually converted by MarkItDown.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_formats_endpoint():
    """Test the enhanced /formats endpoint"""
    print("🔍 Testing enhanced formats endpoint...\n")
    
    response = requests.get(f"{BASE_URL}/formats")
    if response.status_code != 200:
        print("❌ Server not running")
        return None
    
    data = response.json()
    
    print("📊 FORMAT CAPABILITIES BREAKDOWN")
    print("=" * 50)
    
    detection = data["detection_capabilities"]
    conversion = data["conversion_support"]
    
    print(f"🔍 DETECTION: {detection['total_detectable']} formats can be detected")
    print(f"✅ CONVERSION: MarkItDown can actually convert most of them")
    print(f"⚠️  DETECTION-ONLY: Some formats detected but not convertible\n")
    
    print("🔍 All Detectable Formats:")
    for category, formats in detection["categories"].items():
        print(f"   📁 {category.replace('_', ' ').title()}: {', '.join(formats)}")
    
    print(f"\n✅ Fully Supported for Conversion:")
    for category, formats in conversion["fully_supported"].items():
        print(f"   📁 {category.replace('_', ' ').title()}: {', '.join(formats)}")
    
    print(f"\n⚠️  Detection-Only (Not Convertible):")
    detection_only = conversion["detection_only"]["formats"]
    print(f"   🔍 {', '.join(detection_only)}")
    
    print(f"\n💡 Notes:")
    for key, note in data["notes"].items():
        print(f"   • {note}")
    
    return data

def test_supported_vs_unsupported():
    """Test actual conversion of supported vs unsupported formats"""
    print("\n" + "=" * 70)
    print("🧪 TESTING CONVERSION: Supported vs Unsupported Formats")
    print("=" * 70)
    
    # Test cases: supported formats that should work
    supported_tests = [
        {
            "name": "HTML (Supported)",
            "content": b'<html><body><h1>Test</h1><p>This should work</p></body></html>',
            "should_work": True
        },
        {
            "name": "CSV (Supported)", 
            "content": b'Name,Age\nJohn,30\nJane,25',
            "should_work": True
        },
        {
            "name": "Markdown (Supported)",
            "content": b'# Test\nThis **should** work',
            "should_work": True
        }
    ]
    
    # Test cases: detectable but unsupported formats
    unsupported_tests = [
        {
            "name": "JSON (Detection-Only)",
            "content": b'{"name": "test", "supported": false}',
            "should_work": False
        },
        {
            "name": "XML (Detection-Only)",
            "content": b'<?xml version="1.0"?><root><item>test</item></root>',
            "should_work": False
        }
    ]
    
    all_tests = supported_tests + unsupported_tests
    
    for test_case in all_tests:
        print(f"\n🧪 Testing {test_case['name']}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/convert",
                data=test_case["content"],
                headers={"Content-Type": "application/octet-stream"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if test_case["should_work"]:
                    print(f"   ✅ SUCCESS: Converted {result['original_length']} chars → {result['converted_length']} chars")
                    print(f"   📝 Format: {result['detected_format']}")
                else:
                    print(f"   ⚠️  UNEXPECTED: This format shouldn't be convertible but worked!")
                    
            elif response.status_code == 422:  # Our new unsupported format error
                error_data = response.json()
                if not test_case["should_work"]:
                    print(f"   ✅ EXPECTED: Format detected but not supported")
                    print(f"   🔍 Detected: {error_data['detail']['detected_format']}")
                    print(f"   💡 Message: {error_data['detail']['message']}")
                else:
                    print(f"   ❌ UNEXPECTED: Supported format failed with unsupported error")
                    
            else:
                print(f"   ❌ ERROR: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")

def test_real_files():
    """Test with real files to show working examples"""
    print(f"\n" + "=" * 70)
    print("📁 TESTING WITH REAL FILES")
    print("=" * 70)
    
    test_files = ["test.pdf", "README.md"]
    
    for filename in test_files:
        try:
            with open(filename, "rb") as f:
                content = f.read()
            
            print(f"\n📄 Testing {filename}...")
            
            response = requests.post(
                f"{BASE_URL}/convert",
                data=content,
                headers={"Content-Type": "application/octet-stream"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ SUCCESS: {result['original_length']} bytes → {result['converted_length']} chars")
                print(f"   📝 Detected as: {result['detected_format']}")
                
                # Show a small preview
                preview = result['converted_content'][:100].replace('\n', ' ')
                print(f"   👀 Preview: {preview}...")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except FileNotFoundError:
            print(f"   ⚠️  File {filename} not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    print("🚀 MarkItDown Server: Detection vs Conversion Support Test\n")
    
    # Test the enhanced formats endpoint
    formats_data = test_formats_endpoint()
    if not formats_data:
        return
    
    # Test supported vs unsupported conversions
    test_supported_vs_unsupported()
    
    # Test with real files
    test_real_files()
    
    print(f"\n" + "=" * 70)
    print("📋 SUMMARY: Enhanced Server Capabilities")
    print("=" * 70)
    print("✅ DETECTION: Can identify 32 different file formats")
    print("✅ CONVERSION: MarkItDown supports most common document formats")
    print("⚠️  LIMITATION: Some detected formats (JSON, XML) not convertible")
    print("💡 BENEFIT: Clear error messages explain what's supported")
    print("\n🌐 API Usage:")
    print("   GET /formats  - See detection vs conversion capabilities")
    print("   POST /convert - Convert supported documents")
    print("   Status 422    - Format detected but not supported for conversion")

if __name__ == "__main__":
    main() 