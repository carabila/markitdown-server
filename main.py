from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import tempfile
import os
import mimetypes
import json
import base64
from markitdown import MarkItDown

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MarkItDown Server",
    description="A FastAPI server that converts documents to markdown using Microsoft's markitdown library",
    version="1.1.0"
)

# Initialize MarkItDown converter
markitdown = MarkItDown()

# Pydantic models for request validation
class Base64ConvertRequest(BaseModel):
    content: str  # Base64 encoded file content
    filename: str = None  # Optional original filename for better format detection

def detect_file_format(content: bytes) -> tuple[str, bool]:
    """
    Detect file format from content and return (extension, is_text_format).
    Returns appropriate file extension and whether it's a text-based format.
    """
    
    # Binary format signatures (magic bytes)
    binary_signatures = {
        b'%PDF': '.pdf',
        b'PK\x03\x04': '.zip',  # ZIP/Office files (more specific)
        b'PK\x05\x06': '.zip',  # ZIP empty archive
        b'PK\x07\x08': '.zip',  # ZIP spanned archive
        b'\xff\xd8\xff': '.jpg',
        b'\x89PNG\r\n\x1a\n': '.png',
        b'GIF8': '.gif',
        b'BM': '.bmp',
        b'\x00\x00\x01\x00': '.ico',
        b'\x00\x00\x02\x00': '.cur',  # Cursor files
        b'RIFF': '.wav',  # WAV/AVI/WebP (need further detection)
        b'ID3': '.mp3',
        b'\xff\xfb': '.mp3',  # MP3 without ID3
        b'\xff\xf3': '.mp3',  # MP3 MPEG-1 Layer 3
        b'\xff\xf2': '.mp3',  # MP3 MPEG-2 Layer 3
        b'ftyp': '.m4a',  # M4A/MP4 (offset 4)
        b'OggS': '.ogg',
        b'fLaC': '.flac',
        b'EPUB': '.epub',  # EPUB files
        # TAR formats
        b'ustar\x20\x20\x00': '.tar',  # TAR POSIX
        b'ustar\x00': '.tar',  # TAR GNU
        # Compressed archives
        b'\x1f\x8b': '.gz',
        b'BZh': '.bz2',
        b'\xfd7zXZ\x00': '.xz',
        b'7z\xbc\xaf\x27\x1c': '.7z',
        b'Rar!\x1a\x07\x00': '.rar',
        # RTF
        b'{\\rtf': '.rtf',
        # Other image formats
        b'\xff\xe0': '.jpg',  # JPEG variant
        b'WEBP': '.webp',  # WebP (after RIFF)
        b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a': '.png',  # Full PNG signature
    }
    
    # Check for binary signatures
    for signature, extension in binary_signatures.items():
        if content.startswith(signature):
            # Special handling for Office files (ZIP-based)
            if extension == '.zip':
                return detect_office_format(content), False
            # Special handling for RIFF containers
            elif extension == '.wav' and len(content) > 12:
                riff_type = content[8:12]
                if riff_type == b'WAVE':
                    return '.wav', False
                elif riff_type == b'AVI ':
                    return '.avi', False
                elif riff_type == b'WEBP':
                    return '.webp', False
                else:
                    return '.wav', False  # Default to WAV for unknown RIFF
            # Special handling for M4A (MP4 container)
            elif extension == '.m4a' and len(content) > 8:
                if content[4:8] == b'ftyp':
                    return '.m4a', False
            return extension, False
    
    # Check for text-based formats by trying to decode as UTF-8
    try:
        text_content = content.decode('utf-8')
        
        # Detect text-based formats by content analysis
        text_stripped = text_content.strip()
        if not text_stripped:
            return '.txt', True
            
        # JSON detection
        if (text_stripped.startswith(('{', '[')) and text_stripped.endswith(('}', ']'))):
            try:
                json.loads(text_content)
                return '.json', True
            except:
                pass
        
        # XML/HTML detection
        if text_stripped.startswith('<'):
            if any(tag in text_content.lower() for tag in ['<html', '<head', '<body', '<div', '<p', '<span']):
                return '.html', True
            elif text_content.lower().startswith('<?xml') or '</' in text_content:
                return '.xml', True
        
        # CSV detection (simple heuristic)
        lines = text_content.split('\n')[:5]  # Check first 5 lines
        if len(lines) > 1:
            # Check if multiple lines have the same number of commas/separators
            comma_counts = [line.count(',') for line in lines if line.strip()]
            if len(set(comma_counts)) == 1 and comma_counts[0] > 0:
                return '.csv', True
            # Check for other common separators
            tab_counts = [line.count('\t') for line in lines if line.strip()]
            if len(set(tab_counts)) == 1 and tab_counts[0] > 0:
                return '.tsv', True
        
        # Markdown detection
        if any(marker in text_content for marker in ['# ', '## ', '### ', '* ', '- ', '1. ', '```', '[', '](', '**', '__']):
            return '.md', True
            
        # Default to plain text
        return '.txt', True
        
    except UnicodeDecodeError:
        # If we can't decode as UTF-8 and no binary signature matched, it might be a binary format we don't recognize
        return '.bin', False

def detect_office_format(content: bytes) -> str:
    """Detect specific Office format from ZIP-based content."""
    # Look for Office-specific paths in the ZIP structure
    content_str = content[:2000].decode('utf-8', errors='ignore').lower()
    
    if 'word/' in content_str or 'document.xml' in content_str:
        return '.docx'
    elif 'xl/' in content_str or 'workbook.xml' in content_str:
        return '.xlsx'  
    elif 'ppt/' in content_str or 'presentation.xml' in content_str:
        return '.pptx'
    elif 'epub' in content_str or 'container.xml' in content_str:
        return '.epub'
    else:
        return '.zip'

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "MarkItDown Server is running", 
        "status": "healthy",
        "endpoints": {
            "convert": "POST /convert - Upload raw binary file content",
            "convert_base64": "POST /convert-base64 - Upload base64-encoded file content with optional filename",
            "formats": "GET /formats - List supported file formats"
        },
        "version": "1.2.0"
    }

@app.get("/formats")
async def supported_formats():
    """Return list of supported file formats with clear distinction between detection and conversion support"""
    return {
        "detection_capabilities": {
            "description": "Formats the server can automatically detect from file content",
            "total_detectable": 32,
            "categories": {
                "documents": ["pdf", "docx", "xlsx", "pptx", "html", "txt", "rtf", "epub"],
                "images": ["jpg", "jpeg", "png", "gif", "bmp", "ico", "webp", "tiff"],
                "audio": ["wav", "mp3", "m4a", "flac", "ogg"],
                "text_data": ["csv", "json", "xml", "tsv", "md"],
                "archives": ["zip", "tar", "gz", "bz2", "xz", "7z"],
                "web": ["http_urls", "https_urls"]
            }
        },
        "conversion_support": {
            "description": "Formats that MarkItDown can actually convert to markdown",
            "fully_supported": {
                "documents": ["pdf", "docx", "xlsx", "pptx", "html", "txt", "rtf", "epub"],
                "images": ["jpg", "jpeg", "png", "gif", "bmp", "ico", "webp", "tiff"],
                "audio": ["wav", "mp3", "m4a", "flac", "ogg"],
                "text_data": ["csv", "tsv", "md"],
                "archives": ["zip"],
                "web": ["http_urls", "https_urls"]
            },
            "detection_only": {
                "description": "Detected but not convertible by MarkItDown",
                "formats": ["json", "xml", "tar", "gz", "bz2", "xz", "7z"]
            }
        },
        "notes": {
            "images_audio": "Require LLM integration for optimal results (OCR/transcription)",
            "plugins": "Additional formats available via MarkItDown plugins",
            "archives": "ZIP files are processed, compressed archives are detected only"
        }
    }

@app.post("/convert")
async def convert_document(request: Request):
    """
    Convert document content to markdown using markitdown.
    
    Accepts raw binary document content in the request body.
    Supports all MarkItDown-compatible formats including:
    - Documents: PDF, DOCX, XLSX, PPTX, HTML, TXT, RTF, EPUB
    - Images: JPG, PNG, GIF, BMP, ICO, WebP, TIFF
    - Audio: WAV, MP3, M4A, FLAC, OGG
    - Text data: CSV, JSON, XML, TSV, Markdown
    - Archives: ZIP, TAR, and compressed variants
    """
    try:
        # Read raw binary data from request body
        raw_content = await request.body()
        
        if not raw_content:
            raise HTTPException(status_code=400, detail="No content provided in request body")
        
        # Detect file format
        file_extension, is_text_format = detect_file_format(raw_content)
        logger.info(f"Detected format: {file_extension} ({'text' if is_text_format else 'binary'})")
        
        temp_file_path = None
        content_length = len(raw_content)
        
        try:
            if is_text_format:
                # Handle text-based formats
                try:
                    text_content = raw_content.decode('utf-8')
                    if not text_content.strip():
                        raise HTTPException(status_code=400, detail="Empty content provided")
                    
                    # Create temporary file for text content
                    with tempfile.NamedTemporaryFile(mode='w', suffix=file_extension, delete=False, encoding='utf-8') as temp_file:
                        temp_file.write(text_content)
                        temp_file_path = temp_file.name
                    
                    logger.info(f"Processing text content ({len(text_content)} characters, format: {file_extension})")
                    
                except UnicodeDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid text encoding for detected text format")
            else:
                # Handle binary formats
                with tempfile.NamedTemporaryFile(mode='wb', suffix=file_extension, delete=False) as temp_file:
                    temp_file.write(raw_content)
                    temp_file_path = temp_file.name
                
                logger.info(f"Processing binary content ({content_length} bytes, format: {file_extension})")
            
            # Convert using markitdown
            result = markitdown.convert(temp_file_path)
            converted_content = result.text_content
            
            logger.info(f"Successfully converted {content_length} {'characters' if is_text_format else 'bytes'} to {len(converted_content)} characters")
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "detected_format": file_extension.lstrip('.'),
                    "original_length": content_length,
                    "converted_content": converted_content,
                    "converted_length": len(converted_content),
                    "content_type": "text" if is_text_format else "binary"
                }
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"MarkItDown conversion failed: {e}")
            
            # Check if it's an unsupported format error
            if "not supported" in error_msg.lower() or "UnsupportedFormatException" in error_msg:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "Unsupported format for conversion",
                        "detected_format": file_extension.lstrip('.'),
                        "message": f"Format '{file_extension.lstrip('.')}' was detected correctly but MarkItDown cannot convert it to markdown",
                        "suggestion": "This format is detected but not supported by MarkItDown. Check GET /formats for supported vs detection-only formats.",
                        "supported_alternatives": ["pdf", "docx", "xlsx", "pptx", "html", "csv", "tsv", "md"]
                    }
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to convert {file_extension} content: {str(e)}"
                )
        finally:
            # Clean up the temporary file
            if temp_file_path:
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore errors if file was already deleted
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in convert endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during conversion"
        )

@app.post("/convert-base64")
async def convert_base64_document(request: Base64ConvertRequest):
    """
    Convert base64-encoded document content to markdown using markitdown.
    
    Accepts a JSON payload with base64-encoded file content.
    Supports all MarkItDown-compatible formats including:
    - Documents: PDF, DOCX, XLSX, PPTX, HTML, TXT, RTF, EPUB
    - Images: JPG, PNG, GIF, BMP, ICO, WebP, TIFF
    - Audio: WAV, MP3, M4A, FLAC, OGG
    - Text data: CSV, JSON, XML, TSV, Markdown
    - Archives: ZIP, TAR, and compressed variants
    """
    try:
        if not request.content:
            raise HTTPException(status_code=400, detail="No base64 content provided")
        
        # Decode base64 content
        try:
            raw_content = base64.b64decode(request.content, validate=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {str(e)}")
        
        if not raw_content:
            raise HTTPException(status_code=400, detail="Decoded content is empty")
        
        # Detect file format
        file_extension, is_text_format = detect_file_format(raw_content)
        
        # If filename is provided, try to use its extension as a hint
        if request.filename:
            filename_lower = request.filename.lower()
            if '.' in filename_lower:
                filename_ext = '.' + filename_lower.split('.')[-1]
                # Use filename extension if it seems reasonable and we detected generic format
                if file_extension in ['.bin', '.txt'] and filename_ext in [
                    '.pdf', '.docx', '.xlsx', '.pptx', '.html', '.txt', '.rtf', '.epub',
                    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp', '.tiff',
                    '.wav', '.mp3', '.m4a', '.flac', '.ogg', '.csv', '.json', '.xml', '.tsv', '.md'
                ]:
                    file_extension = filename_ext
                    logger.info(f"Using filename extension hint: {filename_ext}")
        
        logger.info(f"Detected format: {file_extension} ({'text' if is_text_format else 'binary'})")
        
        temp_file_path = None
        content_length = len(raw_content)
        
        try:
            if is_text_format:
                # Handle text-based formats
                try:
                    text_content = raw_content.decode('utf-8')
                    if not text_content.strip():
                        raise HTTPException(status_code=400, detail="Empty content provided")
                    
                    # Create temporary file for text content
                    with tempfile.NamedTemporaryFile(mode='w', suffix=file_extension, delete=False, encoding='utf-8') as temp_file:
                        temp_file.write(text_content)
                        temp_file_path = temp_file.name
                    
                    logger.info(f"Processing text content ({len(text_content)} characters, format: {file_extension})")
                    
                except UnicodeDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid text encoding for detected text format")
            else:
                # Handle binary formats
                with tempfile.NamedTemporaryFile(mode='wb', suffix=file_extension, delete=False) as temp_file:
                    temp_file.write(raw_content)
                    temp_file_path = temp_file.name
                
                logger.info(f"Processing binary content ({content_length} bytes, format: {file_extension})")
            
            # Convert using markitdown
            result = markitdown.convert(temp_file_path)
            converted_content = result.text_content
            
            logger.info(f"Successfully converted {content_length} {'characters' if is_text_format else 'bytes'} to {len(converted_content)} characters")
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "detected_format": file_extension.lstrip('.'),
                    "original_filename": request.filename,
                    "original_length": content_length,
                    "converted_content": converted_content,
                    "converted_length": len(converted_content),
                    "content_type": "text" if is_text_format else "binary"
                }
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"MarkItDown conversion failed: {e}")
            
            # Check if it's an unsupported format error
            if "not supported" in error_msg.lower() or "UnsupportedFormatException" in error_msg:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "Unsupported format for conversion",
                        "detected_format": file_extension.lstrip('.'),
                        "original_filename": request.filename,
                        "message": f"Format '{file_extension.lstrip('.')}' was detected correctly but MarkItDown cannot convert it to markdown",
                        "suggestion": "This format is detected but not supported by MarkItDown. Check GET /formats for supported vs detection-only formats.",
                        "supported_alternatives": ["pdf", "docx", "xlsx", "pptx", "html", "csv", "tsv", "md"]
                    }
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to convert {file_extension} content: {str(e)}"
                )
        finally:
            # Clean up the temporary file
            if temp_file_path:
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore errors if file was already deleted
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in convert-base64 endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during base64 conversion"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 