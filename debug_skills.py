#!/usr/bin/env python3
"""
Debug script to find why skills are empty
"""
import asyncio
import sys
import os
import json

# Add the backend directory to path for imports
sys.path.append('/Users/aksar/Desktop/ideas/ResumeAgentAI/backend')

from app.services.ai_service import AIService

async def debug_skills_extraction():
    """Debug the complete skills extraction pipeline"""
    
    print("🔍 DEBUGGING SKILLS EXTRACTION ISSUE")
    print("=" * 60)
    
    # Resume with clear skills section
    test_resume = """
    Muhammad Zaid
    Senior Software Engineer
    Email: muhammadzaid435@gmail.com
    Phone: 03034006155
    Location: Gujranwala, Pakistan
    
    PROFESSIONAL SUMMARY
    I'm an experienced Backend Software Engineer with over 6 years of experience.
    
    WORK EXPERIENCE
    Senior Software Engineer
    SMASH CLOUD MEDIA | Jul 2022 - Present
    • Led backend systems development
    
    Backend Developer
    BIZZCLAN | Jun 2022 - Jul 2023
    • Built APIs using Node.js and Express.js
    
    TECHNICAL SKILLS & EXPERTISE
    
    Programming Languages:
    • Node.js (Expert - 6 years)
    • JavaScript (Expert - 6 years) 
    • TypeScript (Advanced - 4 years)
    • Python (Intermediate - 2 years)
    
    Frameworks & Libraries:
    • Express.js (Expert - 6 years)
    • NestJS (Advanced - 3 years)
    • React (Advanced - 4 years)
    
    Databases:
    • MySQL (Advanced - 5 years)
    • PostgreSQL (Advanced - 4 years)
    • MongoDB (Advanced - 5 years)
    
    EDUCATION
    University of Sargodha | BSSE Computer Science | 2014-2018
    
    LANGUAGES
    • Urdu - Native
    • English - Advanced
    """
    
    try:
        ai_service = AIService()
        print("✅ AIService initialized")
        
        print("\n🚀 TESTING COMPLETE PIPELINE...")
        result = await ai_service.process_resume_content(test_resume)
        
        if "error" in result:
            print(f"❌ ERROR: {result}")
            return
        
        # Check each step
        print("\n📊 EXTRACTION RESULTS:")
        print(f"   Name: {result.get('name', 'MISSING')}")
        print(f"   Designation: {result.get('designation', 'MISSING')}")
        print(f"   Skills: {len(result.get('skills', []))} items")
        
        skills = result.get('skills', [])
        if len(skills) == 0:
            print("❌ SKILLS ARE EMPTY!")
            print("\n🔍 DEBUGGING STEPS:")
            
            # Test individual agent
            print("\n1. Testing Skills Agent directly...")
            skills_data = await ai_service._extract_skills(test_resume)
            print(f"   Direct Skills Agent Result: {skills_data}")
            
            # Test QA and see what missing sections it identifies
            qa_verification = result.get('qa_verification', {})
            print(f"\n2. QA Verification Results:")
            print(f"   Confidence: {qa_verification.get('confidence_score', 0)}%")
            print(f"   Missing Sections: {qa_verification.get('missing_sections', [])}")
            print(f"   Retry Attempted: {qa_verification.get('retry_attempted', False)}")
            
            # Check if skills were lost during retry
            if qa_verification.get('retry_attempted'):
                print(f"   ⚠️ RETRY WAS ATTEMPTED - Skills might have been lost during merge!")
            
        else:
            print("✅ SKILLS FOUND:")
            for i, skill in enumerate(skills[:10]):
                print(f"   {i+1}. {skill.get('name', '')} ({skill.get('level', '')})")
            
            # Still check QA details
            qa_verification = result.get('qa_verification', {})
            print(f"\n📊 QA Results:")
            print(f"   Confidence: {qa_verification.get('confidence_score', 0)}%")
            print(f"   Retry Attempted: {qa_verification.get('retry_attempted', False)}")
        
        # Check all field counts
        print(f"\n📈 ALL FIELD COUNTS:")
        print(f"   Skills: {len(result.get('skills', []))}")
        print(f"   Experience Details: {len(result.get('experience_details', []))}")
        print(f"   Education: {len(result.get('education', []))}")
        print(f"   Projects: {len(result.get('projects', []))}")
        print(f"   Languages: {len(result.get('languages', []))}")
        print(f"   Certifications: {len(result.get('certifications', []))}")
        
        return len(skills) > 0
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    skills_working = asyncio.run(debug_skills_extraction())
    if skills_working:
        print("\n✅ SKILLS EXTRACTION: WORKING")
    else:
        print("\n❌ SKILLS EXTRACTION: BROKEN - NEEDS FIX")