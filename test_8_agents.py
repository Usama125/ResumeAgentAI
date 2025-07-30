#!/usr/bin/env python3
"""
Test script for the 8-agent resume extraction system with Quality Assurance
"""
import asyncio
import sys
import os
import json

# Add the backend directory to path for imports
sys.path.append('/Users/aksar/Desktop/ideas/ResumeAgentAI/backend')

from app.services.ai_service import AIService

async def test_8_agent_system_with_qa():
    """Test the comprehensive 8-agent extraction system with QA verification"""
    
    # High-quality resume content that should pass QA
    high_quality_resume = """
    Muhammad Zaid
    Senior Software Engineer
    Email: muhammadzaid435@gmail.com
    Phone: 03034006155
    Location: Gujranwala, Pakistan
    LinkedIn: https://linkedin.com/in/muhammadzaid
    GitHub: https://github.com/zaid123
    Portfolio: https://zaidportfolio.com
    
    PROFESSIONAL SUMMARY
    I'm an experienced Backend Software Engineer specializing in Node.js, Express.js, and NestJS 
    with over 6 years of hands-on experience in developing scalable backend systems, APIs, and 
    microservices architectures.
    
    WORK EXPERIENCE
    
    Senior Software Engineer
    SMASH CLOUD MEDIA | Jul 2022 - Present
    • Led the design and optimization of scalable backend systems using Node.js and NestJS
    • Implemented microservices architecture reducing system response time by 40%
    • Mentored junior developers and conducted code reviews
    
    Backend Developer
    BIZZCLAN | Jun 2022 - Jul 2023
    • Worked part-time building and optimizing APIs using Node.js, Express.js, and MongoDB
    • Developed RESTful APIs serving 10K+ daily active users
    
    Software Engineer
    BIG IMMERSIVE | Jun 2021 - Jul 2022
    • Specialized in developing and optimizing backend systems for NFT marketplace
    • Built blockchain integration using Web3.js and Ethereum smart contracts
    
    Full Stack Developer
    APPCRATES | Jan 2019 - Oct 2020
    • Specialized in developing and optimizing backend applications using Node.js and Laravel
    • Built complete web applications from frontend to backend
    
    TECHNICAL SKILLS
    • Node.js
    • Express.js
    • NestJS
    • JavaScript
    • TypeScript
    • MySQL
    • PostgreSQL
    • MongoDB
    • AWS
    • Docker
    
    EDUCATION
    
    Bachelor of Software Engineering (BSSE)
    University of Sargodha | 2014 - 2018 | GPA: 2.9/4.0
    
    Intermediate in Science (FSc)
    Punjab College of Science | 2012 - 2014 | Grade: 67%
    
    KEY PROJECTS
    
    A4A - Analytics Platform
    • Backend development focusing on real-time analytics dashboard
    • Technologies: Node.js, NestJS, PostgreSQL, Amazon S3
    
    TeamCap - Team Management SaaS
    • React Native-based SaaS application for consulting firms
    • Technologies: AWS Lambda, Node.js, Express.js, MySQL
    
    BlackBooking - Professional Platform
    • MERN stack platform connecting users with professionals
    • Technologies: Node.js, Express.js, MongoDB, React
    
    CERTIFICATIONS
    • AWS Certified Solutions Architect - Associate (2023)
    • MongoDB Certified Developer (2022)
    • Node.js Certified Developer (2021)
    
    LANGUAGES
    • Urdu - Native
    • English - Advanced
    • Arabic - Beginner
    
    AWARDS
    • Best Employee Award - SMASH CLOUD MEDIA (2023)
    • Innovation Award - BIG IMMERSIVE (2022)
    
    INTERESTS
    • Open Source Contribution
    • Technical Writing
    • Chess
    • Photography
    """
    
    # Poor quality resume content that should fail QA
    poor_quality_resume = """
    John Smith Software Engineer at TechCorp California
    Contact: john@email.com
    
    I work at TechCorp doing software development things.
    
    Experience:
    - Did some coding stuff
    - Made websites
    
    Skills: Programming, computers, technology
    """
    
    print("🤖 Testing 8-Agent Resume Extraction System with Quality Assurance")
    print("=" * 70)
    
    try:
        ai_service = AIService()
        print("✅ AIService initialized successfully")
        
        # Test 1: High Quality Resume (should pass QA)
        print("\n🚀 TEST 1: High Quality Resume (should PASS QA with 90%+ confidence)")
        print("=" * 60)
        
        result1 = await ai_service.process_resume_content(high_quality_resume)
        
        if "error" in result1:
            print(f"❌ ERROR in Test 1: {result1}")
        else:
            qa_verification = result1.get('qa_verification', {})
            confidence = qa_verification.get('confidence_score', 0)
            passed = qa_verification.get('passed', False)
            
            print(f"📊 QA Results:")
            print(f"   Confidence Score: {confidence}%")
            print(f"   Completeness Score: {qa_verification.get('completeness_score', 0)}/40")
            print(f"   Accuracy Score: {qa_verification.get('accuracy_score', 0)}/40") 
            print(f"   Field Mapping Score: {qa_verification.get('field_mapping_score', 0)}/20")
            print(f"   QA Status: {'✅ PASSED' if passed else '❌ FAILED'}")
            
            if qa_verification.get('missing_sections'):
                print(f"   Missing Sections: {qa_verification.get('missing_sections')}")
            
            if qa_verification.get('issues'):
                print(f"   Issues Found: {qa_verification.get('issues')}")
            
            print(f"   Verification Notes: {qa_verification.get('verification_notes', '')}")
            
            # Show key extracted data
            print(f"\n📝 Key Extracted Data:")
            print(f"   Name: {result1.get('name')}")
            print(f"   Designation: {result1.get('designation')}")
            print(f"   Location: {result1.get('location')}")
            print(f"   Experience: {result1.get('experience')}")
            print(f"   Skills Count: {len(result1.get('skills', []))}")
            print(f"   Contact Fields: {len(result1.get('contact_info', {}))}")
        
        # Test 2: Poor Quality Resume (should fail QA)
        print("\n🚀 TEST 2: Poor Quality Resume (should FAIL QA with <90% confidence)")
        print("=" * 60)
        
        result2 = await ai_service.process_resume_content(poor_quality_resume)
        
        if "error" in result2:
            print(f"❌ ERROR in Test 2: {result2}")
        else:
            qa_verification = result2.get('qa_verification', {})
            confidence = qa_verification.get('confidence_score', 0)
            passed = qa_verification.get('passed', False)
            
            print(f"📊 QA Results:")
            print(f"   Confidence Score: {confidence}%")
            print(f"   Completeness Score: {qa_verification.get('completeness_score', 0)}/40")
            print(f"   Accuracy Score: {qa_verification.get('accuracy_score', 0)}/40")
            print(f"   Field Mapping Score: {qa_verification.get('field_mapping_score', 0)}/20")
            print(f"   QA Status: {'✅ PASSED' if passed else '❌ FAILED (Expected)'}")
            
            if qa_verification.get('missing_sections'):
                print(f"   Missing Sections: {qa_verification.get('missing_sections')}")
            
            if qa_verification.get('issues'):
                print(f"   Issues Found: {qa_verification.get('issues')}")
        
        # Summary
        print("\n📈 SYSTEM VALIDATION SUMMARY:")
        print("=" * 40)
        
        test1_passed = result1.get('qa_verification', {}).get('passed', False)
        test2_failed = not result2.get('qa_verification', {}).get('passed', True)
        
        print(f"✅ Test 1 (High Quality): {'PASSED' if test1_passed else 'FAILED'}")
        print(f"✅ Test 2 (Poor Quality): {'FAILED (Expected)' if test2_failed else 'UNEXPECTEDLY PASSED'}")
        
        overall_success = test1_passed and test2_failed
        
        if overall_success:
            print("\n🎉 8-AGENT SYSTEM WITH QA: ALL TESTS PASSED!")
            print("✅ System correctly identifies high-quality vs poor-quality extractions")
            print("✅ Quality Assurance Agent working perfectly")
            print("✅ 90% confidence threshold functioning correctly")
        else:
            print("\n💥 8-AGENT SYSTEM WITH QA: TESTS FAILED!")
            print("❌ System needs adjustment in quality detection")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_8_agent_system_with_qa())
    if success:
        print("\n🎉 8-Agent System with QA Test PASSED!")
        print("🚀 System ready for production with quality assurance!")
    else:
        print("\n💥 8-Agent System with QA Test FAILED!")
        print("🔧 System needs refinement before production use")