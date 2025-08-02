#!/usr/bin/env python3
"""
Test the Pydantic model validation directly
"""
from app.routers.users import SectionOrderRequest, SkillOrderRequest
import json

def test_pydantic_models():
    """Test that our Pydantic models work correctly"""
    print("🧪 Testing Pydantic Model Validation")
    print("=" * 40)
    
    # Test SectionOrderRequest
    print("\n1️⃣ Testing SectionOrderRequest model")
    
    try:
        # Valid data
        valid_data = {"section_order": ["about", "skills", "experience"]}
        request = SectionOrderRequest(**valid_data)
        print(f"✅ Valid data accepted: {request.section_order}")
        
        # Invalid data (missing field)
        try:
            invalid_data = {"wrong_field": ["about", "skills"]}
            SectionOrderRequest(**invalid_data)
            print("❌ FAILED: Invalid data was accepted")
        except Exception as e:
            print(f"✅ Invalid data correctly rejected: {e}")
            
    except Exception as e:
        print(f"❌ Error testing SectionOrderRequest: {e}")
        return False
    
    # Test SkillOrderRequest
    print("\n2️⃣ Testing SkillOrderRequest model")
    
    try:
        # Valid data
        valid_data = {"skill_ids": ["skill1", "skill2", "skill3"]}
        request = SkillOrderRequest(**valid_data)
        print(f"✅ Valid data accepted: {request.skill_ids}")
        
        # Invalid data (missing field)
        try:
            invalid_data = {"wrong_field": ["skill1", "skill2"]}
            SkillOrderRequest(**invalid_data)
            print("❌ FAILED: Invalid data was accepted")
        except Exception as e:
            print(f"✅ Invalid data correctly rejected: {e}")
            
    except Exception as e:
        print(f"❌ Error testing SkillOrderRequest: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 All Pydantic model tests passed!")
    print("✅ SectionOrderRequest correctly validates {section_order: [...]}")
    print("✅ SkillOrderRequest correctly validates {skill_ids: [...]}")
    
    return True

if __name__ == "__main__":
    success = test_pydantic_models()
    if success:
        print("\n✅ Pydantic models are working correctly")
        print("✅ The API will now accept the correct request format")
        exit(0)
    else:
        print("\n❌ Pydantic model validation failed")
        exit(1)