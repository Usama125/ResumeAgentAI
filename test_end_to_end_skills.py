#!/usr/bin/env python3
"""
End-to-end test of skills extraction through the complete onboarding flow
"""
import asyncio
import sys
import os
import tempfile

# Add the backend directory to path for imports
sys.path.append('/Users/aksar/Desktop/ideas/ResumeAgentAI/backend')

from app.services.pdf_service import DocumentService
from app.services.user_service import UserService
from app.models.user import UserUpdate

async def test_end_to_end_skills():
    """Test complete skills flow from PDF to database"""
    try:
        print("🔍 END-TO-END SKILLS TEST")
        print("="*60)
        
        # Use existing PDF
        pdf_path = "/Users/aksar/Desktop/ideas/ResumeAgentAI/backend/uploads/pdfs/779519e4-60d3-4f00-a487-65a7f21ef8b0.pdf"
        
        print(f"📁 Processing PDF: {pdf_path}")
        
        # Step 1: Document Service Processing
        print("\n🔍 STEP 1: Document Service Processing")
        doc_service = DocumentService()
        result = await doc_service.process_resume_document(pdf_path, "test.pdf")
        
        if not result.get('success'):
            print(f"❌ Document processing failed: {result.get('error')}")
            return False
            
        extracted_data = result.get('extracted_data', {})
        print(f"✅ Document processed: {len(extracted_data)} fields")
        
        # Check skills after document processing
        skills = extracted_data.get('skills', [])
        print(f"📊 Skills from document service: {len(skills)} items")
        if len(skills) > 0:
            print(f"   First skill: {skills[0]}")
        
        # Step 2: Onboarding Router Data Mapping
        print("\n🔍 STEP 2: Onboarding Router Data Mapping")
        
        # Simulate onboarding router logic
        update_data = {}
        field_mapping = {
            "name": "name",
            "designation": "designation", 
            "location": "location",
            "summary": "summary",
            "profession": "profession",
            "experience": "experience",
            "skills": "skills",
            "experience_details": "experience_details",
            "projects": "projects",
            "certifications": "certifications",
            "contact_info": "contact_info",
            "education": "education",
            "languages": "languages",
            "awards": "awards",
            "publications": "publications",
            "volunteer_experience": "volunteer_experience",
            "interests": "interests"
        }
        
        for ai_field, db_field in field_mapping.items():
            if ai_field in extracted_data and ai_field != "qa_verification":
                data_value = extracted_data[ai_field]
                if data_value is not None:
                    update_data[db_field] = data_value
                    if ai_field == "skills":
                        print(f"🎯 MAPPING - Skills mapped: {len(data_value)} items")
                        print(f"🎯 MAPPING - First skill: {data_value[0] if data_value else 'None'}")
        
        # Step 3: UserUpdate Validation
        print("\n🔍 STEP 3: UserUpdate Validation")
        
        try:
            user_update = UserUpdate(**update_data)
            print("✅ UserUpdate created successfully")
            
            if hasattr(user_update, 'skills') and user_update.skills is not None:
                print(f"🎯 VALIDATION - Skills validated: {len(user_update.skills)} items")
                print(f"🎯 VALIDATION - First skill: {user_update.skills[0]}")
            else:
                print("❌ VALIDATION - No skills in UserUpdate!")
                
        except Exception as validation_error:
            print(f"❌ UserUpdate validation failed: {str(validation_error)}")
            return False
        
        # Step 4: User Service Processing
        print("\n🔍 STEP 4: User Service Processing")
        
        # Simulate user service logic
        update_dict = {}
        for key, value in user_update.model_dump(exclude_unset=True).items():
            if value is not None:
                update_dict[key] = value
                if key == "skills":
                    print(f"🎯 USER_SERVICE - Skills in update_dict: {len(value)} items")
                    print(f"🎯 USER_SERVICE - Type: {type(value)}")
                    print(f"🎯 USER_SERVICE - First skill: {value[0] if value else 'None'}")
        
        print(f"✅ User service update_dict created with {len(update_dict)} fields")
        
        # Step 5: Final Verification
        print("\n🔍 STEP 5: Final Verification")
        
        if "skills" in update_dict:
            final_skills = update_dict["skills"]
            print(f"✅ FINAL CHECK - Skills preserved: {len(final_skills)} items")
            print(f"✅ FINAL CHECK - Skills type: {type(final_skills)}")
            if len(final_skills) > 0:
                print(f"✅ FINAL CHECK - First skill: {final_skills[0]}")
                print(f"✅ FINAL CHECK - First skill type: {type(final_skills[0])}")
            return True
        else:
            print("❌ FINAL CHECK - Skills lost somewhere in the pipeline!")
            return False
            
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_end_to_end_skills())
    if success:
        print("\n✅ END-TO-END SKILLS TEST: SUCCESS")
        print("🎉 Skills are preserved through the entire pipeline!")
    else:
        print("\n❌ END-TO-END SKILLS TEST: FAILED")
        print("🔍 There's still an issue in the pipeline")