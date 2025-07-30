#!/usr/bin/env python3
"""
Test the fixed user service with model_dump
"""
import sys
sys.path.append('/Users/aksar/Desktop/ideas/ResumeAgentAI/backend')

from app.models.user import UserUpdate

# Test skills data from AI extraction
test_skills = [
    {'name': 'NestJS', 'level': 'Advanced', 'years': 0},
    {'name': 'MERN stack', 'level': 'Advanced', 'years': 6},
    {'name': 'React.js', 'level': 'Expert', 'years': 6},
    {'name': 'Node.js', 'level': 'Expert', 'years': 6},
    {'name': 'MongoDB', 'level': 'Expert', 'years': 6}
]

def test_model_dump_fix():
    """Test model_dump vs dict for skills data"""
    print("🧪 TESTING MODEL_DUMP FIX")
    print("="*50)
    
    try:
        # Create UserUpdate
        update_data = {
            "name": "Test User",
            "skills": test_skills
        }
        
        user_update = UserUpdate(**update_data)
        print("✅ UserUpdate created successfully!")
        
        # Test deprecated .dict() method
        print("\n🔍 Testing deprecated .dict() method...")
        try:
            old_dict = user_update.dict(exclude_unset=True)
            print(f"   ✅ .dict() works: {len(old_dict.get('skills', []))} skills")
        except Exception as e:
            print(f"   ❌ .dict() failed: {str(e)}")
        
        # Test new .model_dump() method  
        print("\n🔍 Testing new .model_dump() method...")
        try:
            new_dict = user_update.model_dump(exclude_unset=True)
            print(f"   ✅ .model_dump() works: {len(new_dict.get('skills', []))} skills")
            
            # Check skills structure
            skills_in_dump = new_dict.get('skills', [])
            if skills_in_dump:
                print(f"   📊 First skill: {skills_in_dump[0]}")
                print(f"   📊 Skill type: {type(skills_in_dump[0])}")
            
        except Exception as e:
            print(f"   ❌ .model_dump() failed: {str(e)}")
            
        # Simulate user service logic
        print("\n🔍 Simulating user service update_dict creation...")
        update_dict = {}
        for key, value in user_update.model_dump(exclude_unset=True).items():
            if value is not None:
                update_dict[key] = value
                if key == "skills":
                    print(f"   🎯 SKILLS - Type: {type(value)}, Length: {len(value)}")
                    print(f"   🎯 SKILLS - First skill: {value[0] if value else 'None'}")
                    
        print(f"   ✅ Update dict created with {len(update_dict)} fields")
        if "skills" in update_dict:
            print(f"   ✅ Skills preserved in update_dict: {len(update_dict['skills'])} items")
        else:
            print(f"   ❌ Skills missing in update_dict!")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_dump_fix()