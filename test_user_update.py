#!/usr/bin/env python3
"""
Test UserUpdate validation with skills data
"""
import sys
sys.path.append('/Users/aksar/Desktop/ideas/ResumeAgentAI/backend')

from app.models.user import UserUpdate, Skill

# Test skills data from AI extraction (exact format)
test_skills = [
    {'name': 'NestJS', 'level': 'Advanced', 'years': 0},
    {'name': 'MERN stack', 'level': 'Advanced', 'years': 6},
    {'name': 'React.js', 'level': 'Expert', 'years': 6},
    {'name': 'Node.js', 'level': 'Expert', 'years': 6},
    {'name': 'MongoDB', 'level': 'Expert', 'years': 6}
]

def test_user_update_validation():
    """Test UserUpdate validation with skills"""
    print("🧪 TESTING USERUPDATE VALIDATION")
    print("="*50)
    
    print(f"📊 Input skills: {len(test_skills)} items")
    print(f"📊 First skill: {test_skills[0]}")
    
    try:
        # Create UserUpdate with skills
        print("\n🔍 Creating UserUpdate with skills...")
        update_data = {
            "name": "Test User",
            "skills": test_skills
        }
        
        user_update = UserUpdate(**update_data)
        print("✅ UserUpdate created successfully!")
        
        print(f"\n📊 UserUpdate skills validation:")
        print(f"   Skills type: {type(user_update.skills)}")
        print(f"   Skills count: {len(user_update.skills) if user_update.skills else 0}")
        
        if user_update.skills and len(user_update.skills) > 0:
            print(f"   First skill: {user_update.skills[0]}")
            print(f"   First skill type: {type(user_update.skills[0])}")
        
        # Test dictionary export
        print(f"\n🔍 Testing dict export...")
        dict_data = user_update.dict(exclude_unset=True)
        print(f"   Dict keys: {list(dict_data.keys())}")
        
        if "skills" in dict_data:
            skills_in_dict = dict_data["skills"]
            print(f"   Skills in dict: {len(skills_in_dict)} items")
            print(f"   First skill in dict: {skills_in_dict[0] if skills_in_dict else 'None'}")
        else:
            print("   ❌ NO SKILLS IN DICT!")
            
    except Exception as e:
        print(f"❌ UserUpdate validation failed: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_update_validation()