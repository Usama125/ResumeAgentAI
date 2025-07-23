import PyPDF2
import pdfplumber
import aiofiles
import os
from typing import Dict, Any
from app.config import settings
from app.services.ai_service import AIService

class PDFService:
    def __init__(self):
        self.ai_service = AIService()
        self.upload_dir = os.path.join(settings.UPLOAD_DIR, "pdfs")

    async def save_uploaded_pdf(self, file_content: bytes, filename: str) -> str:
        """Save uploaded PDF file and return file path"""
        print(f"📁 [PDF SERVICE] Save PDF - filename: {filename}")
        print(f"📁 [PDF SERVICE] Upload directory: {self.upload_dir}")
        
        # Ensure upload directory exists
        if not os.path.exists(self.upload_dir):
            print(f"📁 [PDF SERVICE] Creating upload directory: {self.upload_dir}")
            os.makedirs(self.upload_dir, exist_ok=True)
        
        file_path = os.path.join(self.upload_dir, filename)
        print(f"📁 [PDF SERVICE] Full file path: {file_path}")
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            print(f"✅ [PDF SERVICE] File saved successfully: {file_path}")
        except Exception as e:
            print(f"❌ [PDF SERVICE] Failed to save file: {str(e)}")
            raise
        
        return file_path

    def extract_text_pypdf2(self, file_path: str) -> str:
        """Extract text using PyPDF2"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            raise Exception(f"PyPDF2 extraction failed: {str(e)}")

    def extract_text_pdfplumber(self, file_path: str) -> str:
        """Extract text using pdfplumber (more accurate)"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"pdfplumber extraction failed: {str(e)}")

    async def process_linkedin_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process LinkedIn PDF and return structured data"""
        try:
            print(f"⚙️ [PDF SERVICE] Processing LinkedIn PDF: {file_path}")
            
            # Try pdfplumber first (more accurate), fallback to PyPDF2
            try:
                print("📖 [PDF SERVICE] Attempting text extraction with pdfplumber...")
                text_content = self.extract_text_pdfplumber(file_path)
                print("✅ [PDF SERVICE] pdfplumber extraction successful")
            except Exception as e:
                print(f"⚠️ [PDF SERVICE] pdfplumber failed: {str(e)}")
                print("📖 [PDF SERVICE] Falling back to PyPDF2...")
                text_content = self.extract_text_pypdf2(file_path)
                print("✅ [PDF SERVICE] PyPDF2 extraction successful")
            
            print(f"📄 [PDF SERVICE] Extracted text length: {len(text_content)} characters")
            
            # Process with AI regardless of content length - extract whatever is available
            print("🤖 [PDF SERVICE] Processing content with AI service...")
            
            # If no text content, return empty but successful result
            if not text_content or len(text_content.strip()) == 0:
                print("⚠️ [PDF SERVICE] No text content extracted, returning empty data")
                return {
                    "success": True,
                    "extracted_data": {},
                    "raw_text_length": 0
                }
            
            structured_data = await self.ai_service.process_linkedin_pdf_content(text_content)
            print(f"✅ [PDF SERVICE] AI processing completed")
            
            # Always return success, even if AI processing has issues
            if "error" in structured_data:
                print(f"⚠️ [PDF SERVICE] AI processing had issues: {structured_data['error']}")
                print("✅ [PDF SERVICE] Returning empty data but marking as successful")
                return {
                    "success": True,
                    "extracted_data": {},
                    "raw_text_length": len(text_content),
                    "processing_note": "AI processing encountered issues but PDF was processed"
                }
            
            print("✅ [PDF SERVICE] PDF processing completed successfully")
            return {
                "success": True,
                "extracted_data": structured_data,
                "raw_text_length": len(text_content)
            }
            
        except Exception as e:
            print(f"❌ [PDF SERVICE] Exception during PDF processing: {str(e)}")
            print(f"❌ [PDF SERVICE] Exception type: {type(e).__name__}")
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}"
            }
        finally:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)