from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import tempfile
import os
from markitdown import MarkItDown

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MarkItDown Server",
    description="A FastAPI server that converts markdown content using Microsoft's markitdown library",
    version="1.0.0"
)

# Initialize MarkItDown converter
markitdown = MarkItDown()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MarkItDown Server is running", "status": "healthy"}

@app.post("/convert")
async def convert_markdown(request: Request):
    """
    Convert markdown content to HTML using markitdown.
    
    Accepts raw binary markdown content in the request body.
    Returns the converted HTML content.
    """
    try:
        # Read raw binary data from request body
        raw_content = await request.body()
        
        if not raw_content:
            raise HTTPException(status_code=400, detail="No content provided in request body")
        
        # Determine if content is text or binary and handle accordingly
        temp_file_path = None
        content_length = 0
        is_text_content = False
        
        # First try to decode as UTF-8 (for text content like markdown)
        try:
            text_content = raw_content.decode('utf-8')
            if not text_content.strip():
                raise HTTPException(status_code=400, detail="Empty content provided")
            
            # Create temporary file for text content (markdown)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(text_content)
                temp_file_path = temp_file.name
            
            content_length = len(text_content)
            is_text_content = True
            logger.info(f"Processing text content ({content_length} characters)")
            
        except UnicodeDecodeError:
            # Check if this looks like random/invalid bytes (not a real binary file)
            # If the content is very short and doesn't start with known binary file signatures, treat as invalid encoding
            if len(raw_content) < 100:
                # Check if it starts with known binary file signatures
                known_signatures = [
                    b'%PDF',  # PDF
                    b'PK',    # ZIP/Office files
                    b'\xff\xd8\xff',  # JPEG
                    b'\x89PNG',       # PNG
                    b'GIF8',          # GIF
                    b'\x00\x00\x01\x00',  # ICO
                    b'BM',            # BMP
                    b'RIFF',          # WAV/AVI
                ]
                
                is_known_binary = any(raw_content.startswith(sig) for sig in known_signatures)
                
                if not is_known_binary:
                    logger.error(f"Invalid content encoding detected")
                    raise HTTPException(
                        status_code=400, 
                        detail="Invalid content encoding. Expected UTF-8 encoded text."
                    )
            
            # Content is binary (like PDF, DOCX, etc.) - handle as binary file
            logger.info(f"Processing binary content ({len(raw_content)} bytes)")
            
            # Try to detect file type from content
            file_extension = '.bin'  # default
            if raw_content.startswith(b'%PDF'):
                file_extension = '.pdf'
            elif raw_content.startswith(b'PK'):  # ZIP-based formats (DOCX, XLSX, etc.)
                if b'word/' in raw_content[:1000]:
                    file_extension = '.docx'
                elif b'xl/' in raw_content[:1000]:
                    file_extension = '.xlsx'
                elif b'ppt/' in raw_content[:1000]:
                    file_extension = '.pptx'
                else:
                    file_extension = '.zip'
            elif raw_content.startswith((b'\xff\xd8\xff', b'\x89PNG')):
                file_extension = '.jpg' if raw_content.startswith(b'\xff\xd8\xff') else '.png'
            
            # Create temporary file for binary content
            with tempfile.NamedTemporaryFile(mode='wb', suffix=file_extension, delete=False) as temp_file:
                temp_file.write(raw_content)
                temp_file_path = temp_file.name
                
            content_length = len(raw_content)
            is_text_content = False
        
        # Convert using markitdown
        try:
            # Convert the temporary file
            result = markitdown.convert(temp_file_path)
            converted_content = result.text_content
            
            logger.info(f"Successfully converted {content_length} {'characters' if is_text_content else 'bytes'}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "original_length": content_length,
                    "converted_content": converted_content,
                    "converted_length": len(converted_content)
                }
            )
            
        except Exception as e:
            logger.error(f"MarkItDown conversion failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to convert content: {str(e)}"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 