#!/usr/bin/env python3
"""
Test script to debug PDF upload functionality
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.config import settings
from app.services.pdf_service import PDFService

async def test_pdf_service():
    """Test PDF service functionality"""
    print("🧪 [PDF TEST] Testing PDF service functionality...")
    
    # Check OpenAI API key
    if not settings.OPENAI_API_KEY:
        print("❌ [PDF TEST] OPENAI_API_KEY not found!")
        print("💡 [PDF TEST] This is likely the cause of the 500 error")
        return False
    
    print(f"✅ [PDF TEST] OpenAI API key configured (length: {len(settings.OPENAI_API_KEY)})")
    
    # Create PDF service
    pdf_service = PDFService()
    print(f"✅ [PDF TEST] PDF service created")
    print(f"📁 [PDF TEST] Upload directory: {pdf_service.upload_dir}")
    
    # Test directory creation
    if not os.path.exists(pdf_service.upload_dir):
        print(f"📁 [PDF TEST] Upload directory doesn't exist, will be created")
    
    # Test file saving (simulate)
    test_content = b"Test PDF content"
    test_filename = "test_upload.pdf"
    
    try:
        print("📁 [PDF TEST] Testing file save...")
        file_path = await pdf_service.save_uploaded_pdf(test_content, test_filename)
        print(f"✅ [PDF TEST] File save test successful: {file_path}")
        
        # Clean up test file
        if os.path.exists(file_path):
            os.remove(file_path)
            print("🧹 [PDF TEST] Test file cleaned up")
            
    except Exception as e:
        print(f"❌ [PDF TEST] File save failed: {str(e)}")
        return False
    
    print("🎉 [PDF TEST] All tests passed!")
    return True

if __name__ == "__main__":
    print("🚀 [PDF TEST] Starting PDF service test...")
    result = asyncio.run(test_pdf_service())
    
    if result:
        print("✅ [PDF TEST] PDF service is working correctly!")
        print("💡 [PDF TEST] The 500 error might be caused by:")
        print("   1. Invalid PDF file format")
        print("   2. Database connection issues") 
        print("   3. User authentication issues")
    else:
        print("💥 [PDF TEST] PDF service has issues!")
        print("💡 [PDF TEST] Check the error messages above for troubleshooting")