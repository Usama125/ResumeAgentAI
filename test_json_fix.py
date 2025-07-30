#!/usr/bin/env python3
"""
Test the JSON parsing fix specifically
"""
import re
import json

# Sample broken JSON from the logs
broken_json = """{
  "skills": [
    {
      "name": "Node.js",
      "level": "Expert",
      "years": 6
    },
    {
      "name": "Express.js",
      "level": "Expert",
      "years": 6
    },
    {
      "name": "NestJS",
      "level": "Expert",
      "years": 4
    },
    {
      "name": "React",
      "level": "Intermediate",
      "years": 3
    },
    {
      "name": "Angular",
      "level": "Intermediate",
      "years": 3
    },
    {
      "name": "PHP",
      "level": "Intermediate",
      "years":"""

def test_json_fix():
    """Test the JSON fixing logic"""
    print("🧪 Testing JSON fix logic")
    print("="*50)
    
    result = broken_json
    
    try:
        # First attempt
        return json.loads(result)
    except json.JSONDecodeError as json_error:
        print(f"❌ JSON decode error: {str(json_error)}")
        print(f"Raw result length: {len(result)}")
        
        # Try to fix common JSON issues
        try:
            # Fix trailing commas and other common issues
            fixed_result = re.sub(r',(\s*[}\]])', r'\1', result)  # Remove trailing commas
            fixed_result = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', fixed_result)  # Quote unquoted keys
            
            # Try to fix incomplete JSON by finding the last complete object
            if not fixed_result.strip().endswith('}') and not fixed_result.strip().endswith(']'):
                print("🔧 Attempting to fix incomplete JSON...")
                # Find the last complete object or array
                brace_count = 0
                last_complete = 0
                for i, char in enumerate(fixed_result):
                    if char == '{' or char == '[':
                        brace_count += 1
                    elif char == '}' or char == ']':
                        brace_count -= 1
                        if brace_count == 0:
                            last_complete = i + 1
                
                if last_complete > 0:
                    fixed_result = fixed_result[:last_complete]
                    print(f"✂️ Truncated to {last_complete} characters")
                else:
                    # Try to complete the JSON manually
                    print("🔧 Attempting manual completion...")
                    # Add missing closing braces
                    open_braces = result.count('{') - result.count('}')
                    open_brackets = result.count('[') - result.count(']')
                    
                    # Complete the current skill object
                    if result.strip().endswith('"years":'):
                        fixed_result = result + ' 0'
                    elif result.strip().endswith('years":'):
                        fixed_result = result + '0'
                    
                    # Close any open objects/arrays
                    for _ in range(open_braces):
                        fixed_result += '}'
                    for _ in range(open_brackets):
                        fixed_result += ']'
            
            print(f"🔧 Fixed result preview: {fixed_result[-100:]}")
            return json.loads(fixed_result)
            
        except Exception as fix_error:
            print(f"❌ JSON fix failed: {str(fix_error)}")
            
            # Try manual extraction
            print("🔧 Attempting manual extraction...")
            skills = []
            skill_patterns = [
                r'"name":\s*"([^"]+)"[^}]*"level":\s*"([^"]+)"[^}]*"years":\s*(\d+)',
                r'"name":\s*"([^"]+)"[^}]*"level":\s*"([^"]+)"',
                r'"name":\s*"([^"]+)"'
            ]
            
            for pattern in skill_patterns:
                matches = re.findall(pattern, result)
                print(f"Pattern '{pattern}' found {len(matches)} matches")
                for match in matches:
                    if len(match) == 3:
                        skills.append({
                            "name": match[0],
                            "level": match[1],
                            "years": int(match[2]) if match[2].isdigit() else 0
                        })
                    elif len(match) == 2:
                        skills.append({
                            "name": match[0],
                            "level": match[1],
                            "years": 0
                        })
                    elif isinstance(match, str):
                        skills.append({
                            "name": match,
                            "level": "Intermediate",
                            "years": 0
                        })
                if skills:
                    break
            
            if skills:
                print(f"✅ Manual extraction successful: found {len(skills)} skills")
                for i, skill in enumerate(skills[:5]):
                    print(f"   {i+1}. {skill}")
                return {"skills": skills}
            else:
                print("❌ Manual extraction failed")
                return {"skills": []}

if __name__ == "__main__":
    result = test_json_fix()
    print(f"\n🎯 Final result: {len(result.get('skills', []))} skills extracted")
    for skill in result.get('skills', [])[:3]:
        print(f"   - {skill}")