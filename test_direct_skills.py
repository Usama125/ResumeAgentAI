#!/usr/bin/env python3
"""
Direct test of skills extraction issue by processing existing PDF
"""
import asyncio
import sys
import os

# Add the backend directory to path for imports
sys.path.append('/Users/aksar/Desktop/ideas/ResumeAgentAI/backend')

from app.services.pdf_service import DocumentService
from app.services.ai_service import AIService

async def test_skills_extraction():
    """Test skills extraction with existing PDF"""
    try:
        print("🔍 TESTING SKILLS EXTRACTION DIRECTLY")
        print("="*60)
        
        # Use existing PDF
        pdf_path = "/Users/aksar/Desktop/ideas/ResumeAgentAI/backend/uploads/pdfs/0c2adef6-e368-480c-9380-165eddd28a93.pdf"
        
        print(f"📁 Processing PDF: {pdf_path}")
        
        # Initialize services
        doc_service = DocumentService()
        ai_service = AIService()
        
        # Extract text from PDF
        print("📄 Extracting text from PDF...")
        
        # Check if the PDF exists
        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found: {pdf_path}")
            return
        
        # Process the resume document 
        print("🤖 Processing with AI service...")
        result = await doc_service.process_resume_document(pdf_path, "test.pdf")
        
        if result.get('success'):
            extracted_data = result.get('extracted_data', {})
            print(f"✅ Extraction successful!")
            print(f"📊 Total fields extracted: {len(extracted_data)}")
            
            # Check skills specifically
            skills = extracted_data.get('skills', [])
            print(f"🎯 SKILLS ANALYSIS:")
            print(f"   Type: {type(skills)}")
            print(f"   Count: {len(skills) if isinstance(skills, list) else 'Not a list'}")
            
            if isinstance(skills, list) and len(skills) > 0:
                print(f"   First 5 skills:")
                for i, skill in enumerate(skills[:5]):
                    print(f"     {i+1}. {skill}")
            elif len(skills) == 0:
                print("   ❌ NO SKILLS FOUND!")
            else:
                print("   ❌ SKILLS NOT A LIST!")
                
            # Check QA verification
            qa_verification = extracted_data.get('qa_verification', {})
            print(f"📊 QA RESULTS:")
            print(f"   Confidence: {qa_verification.get('confidence_score', 0)}%")
            print(f"   Passed: {qa_verification.get('passed', False)}")
            print(f"   Missing Sections: {qa_verification.get('missing_sections', [])}")
            
        else:
            print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_skills_extraction())