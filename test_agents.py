#!/usr/bin/env python3
"""
Test script for the 7-agent resume extraction system
"""
import asyncio
import sys
import os
import json

# Add the backend directory to path for imports
sys.path.append('/Users/aksar/Desktop/ideas/ResumeAgentAI/backend')

from app.services.ai_service import AIService

async def test_7_agent_system():
    """Test the comprehensive 7-agent extraction system"""
    
    # Sample resume content that should trigger all agents
    test_resume_content = """
    Muhammad Zaid
    Senior Software Engineer (Backend Developer Nodejs) at Smash Cloud Pakistan
    
    Contact Information:
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
    SMASH CLOUD MEDIA - Lahore, Pakistan | Jul 2022 - Present
    • Led the design and optimization of scalable backend systems using Node.js and NestJS
    • Implemented microservices architecture reducing system response time by 40%
    • Mentored junior developers and conducted code reviews
    
    Backend Developer
    BIZZCLAN | Jun 2022 - Jul 2023
    • Worked part-time building and optimizing APIs using Node.js, Express.js, and MongoDB
    • Developed RESTful APIs serving 10K+ daily active users
    • Integrated third-party payment systems including PayPal and Stripe
    
    Software Engineer
    BIG IMMERSIVE | Jun 2021 - Jul 2022
    • Specialized in developing and optimizing backend systems for NFT marketplace
    • Built blockchain integration using Web3.js and Ethereum smart contracts
    • Optimized database queries resulting in 60% performance improvement
    
    Software Engineer
    DELINE MEDIA, LLC | Sep 2020 - Jun 2021
    • Worked as a Backend Developer developing backend applications for Ovada Apps
    • Implemented real-time messaging systems using Socket.io
    • Managed AWS infrastructure including EC2, RDS, and S3
    
    Full Stack Developer
    APPCRATES | Jan 2019 - Oct 2020
    • Specialized in developing and optimizing backend applications using Node.js and Laravel
    • Built complete web applications from frontend to backend
    • Implemented automated testing and CI/CD pipelines
    
    TECHNICAL SKILLS & EXPERTISE
    
    Programming Languages:
    • Node.js (Expert - 6 years)
    • JavaScript (Expert - 6 years) 
    • TypeScript (Advanced - 4 years)
    • Python (Intermediate - 2 years)
    • PHP (Intermediate - 3 years)
    
    Frameworks & Libraries:
    • Express.js (Expert - 6 years)
    • NestJS (Advanced - 3 years)
    • React (Advanced - 4 years)
    • Angular (Intermediate - 3 years)
    • Laravel (Intermediate - 3 years)
    
    Databases:
    • MySQL (Advanced - 5 years)
    • PostgreSQL (Advanced - 4 years)
    • MongoDB (Advanced - 5 years)
    • Redis (Intermediate - 3 years)
    
    Cloud & DevOps:
    • AWS (Advanced - 3 years)
    • Docker (Advanced - 3 years)
    • Kubernetes (Intermediate - 2 years)
    • Jenkins (Intermediate - 2 years)
    
    EDUCATION
    
    Bachelor of Software Engineering (BSSE)
    University of Sargodha | Computer Science Department
    2014 - 2018 | GPA: 2.9/4.0
    
    Relevant Coursework: Data Structures, Algorithms, Database Systems, Software Engineering, 
    Operating Systems, Computer Networks
    
    Intermediate in Science (FSc)
    Punjab College of Science | Pre-Engineering
    2012 - 2014 | Grade: 67%
    
    Subjects: Physics, Chemistry, Mathematics, Computer Science
    
    KEY PROJECTS
    
    A4A - Analytics for All
    • Backend development of the A4A app, focusing on Admin Panel, Feature Enhancements
    • Implemented real-time analytics dashboard serving 5000+ concurrent users
    • Technologies: Node.js, NestJS, PostgreSQL, Amazon S3, Redis
    • GitHub: https://github.com/zaid/a4a-backend
    
    TeamCap - Team Capacity Management
    • React Native-based SaaS application designed for consulting and advisory firms
    • Built scalable backend APIs handling 50K+ requests per day
    • Technologies: AWS Lambda, Node.js, Express.js, MySQL, Redis
    • URL: https://teamcap.app
    
    BlackBooking - Professional Booking Platform
    • MERN stack-based platform designed to connect users with professionals
    • Implemented secure payment processing with PayPal and Stripe integration
    • Technologies: Node.js, Express.js, PayPal Integration, MongoDB, React
    • GitHub: https://github.com/zaid/blackbooking
    
    Virtua - NFT Marketplace
    • NFT marketplace that enables buying, selling, and trading NFTs
    • Built microservices architecture handling blockchain transactions
    • Technologies: Node.js, MySQL, Express.js, AWS Lambda, Microservices, Web3.js
    • URL: https://virtua.marketplace
    
    CERTIFICATIONS & ACHIEVEMENTS
    
    • AWS Certified Solutions Architect - Associate (2023)
    • MongoDB Certified Developer (2022)
    • Node.js Certified Developer (2021)
    • Google Cloud Platform Fundamentals (2020)
    • Best Employee Award - SMASH CLOUD MEDIA (2023)
    • Innovation Award - BIG IMMERSIVE (2022)
    
    LANGUAGES
    
    • Urdu - Native
    • English - Advanced (Professional working proficiency)
    • Arabic - Beginner
    
    PUBLICATIONS & ARTICLES
    
    • "Microservices Architecture Best Practices" - Medium (2023)
    • "Scaling Node.js Applications" - Dev.to (2022)
    • "Database Optimization Techniques" - Personal Blog (2021)
    
    VOLUNTEER EXPERIENCE
    
    Tech Mentor
    Code for Pakistan | 2021 - Present
    • Mentoring students in web development and backend technologies
    • Conducting workshops on Node.js and API development
    
    INTERESTS & HOBBIES
    
    • Open Source Contribution
    • Technical Writing and Blogging
    • Chess Playing
    • Photography
    • Traveling and Cultural Exploration
    """
    
    print("🤖 Testing 7-Agent Resume Extraction System")
    print("=" * 60)
    
    try:
        ai_service = AIService()
        print("✅ AIService initialized successfully")
        
        print("\n🚀 Starting comprehensive multi-agent extraction...")
        result = await ai_service.process_resume_content(test_resume_content)
        
        if "error" in result:
            print(f"❌ ERROR: {result}")
            return False
        
        print("\n📊 EXTRACTION RESULTS:")
        print("=" * 40)
        
        # Test Agent 1: Personal Info & Contact
        print("\n🤖 Agent 1 - Personal Info & Contact:")
        print(f"   Name: {result.get('name', 'Not extracted')}")
        print(f"   Designation: {result.get('designation', 'Not extracted')}")
        print(f"   Location: {result.get('location', 'Not extracted')}")
        print(f"   Profession: {result.get('profession', 'Not extracted')}")
        print(f"   Summary length: {len(result.get('summary', ''))}")
        
        contact_info = result.get('contact_info', {})
        print(f"   Contact fields: {list(contact_info.keys())}")
        
        # Test Agent 2: Experience & Calculation
        print("\n🤖 Agent 2 - Experience & Calculation:")
        print(f"   Total Experience: {result.get('experience', 'Not calculated')}")
        experience_details = result.get('experience_details', [])
        print(f"   Experience entries: {len(experience_details)}")
        for i, exp in enumerate(experience_details[:3]):  # Show first 3
            print(f"     {i+1}. {exp.get('position', '')} at {exp.get('company', '')}")
        
        # Test Agent 3: Skills
        print("\n🤖 Agent 3 - Skills:")
        skills = result.get('skills', [])
        print(f"   Skills extracted: {len(skills)}")
        for i, skill in enumerate(skills[:5]):  # Show first 5
            print(f"     {i+1}. {skill.get('name', '')} ({skill.get('level', '')}, {skill.get('years', 0)} years)")
        
        # Test Agent 4: Education
        print("\n🤖 Agent 4 - Education:")
        education = result.get('education', [])
        print(f"   Education entries: {len(education)}")
        for i, edu in enumerate(education):
            print(f"     {i+1}. {edu.get('degree', '')} from {edu.get('institution', '')}")
        
        # Test Agent 5: Projects
        print("\n🤖 Agent 5 - Projects:")
        projects = result.get('projects', [])
        print(f"   Projects extracted: {len(projects)}")
        for i, proj in enumerate(projects):
            tech_count = len(proj.get('technologies', []))
            print(f"     {i+1}. {proj.get('name', '')} ({tech_count} technologies)")
        
        # Test Agent 6: Languages
        print("\n🤖 Agent 6 - Languages:")
        languages = result.get('languages', [])
        print(f"   Languages extracted: {len(languages)}")
        for i, lang in enumerate(languages):
            print(f"     {i+1}. {lang.get('name', '')} ({lang.get('proficiency', '')})")
        
        # Test Agent 7: Additional Info
        print("\n🤖 Agent 7 - Additional Info:")
        certifications = result.get('certifications', [])
        awards = result.get('awards', [])
        publications = result.get('publications', [])
        volunteer = result.get('volunteer_experience', [])
        interests = result.get('interests', [])
        
        print(f"   Certifications: {len(certifications)}")
        print(f"   Awards: {len(awards)}")
        print(f"   Publications: {len(publications)}")
        print(f"   Volunteer Experience: {len(volunteer)}")
        print(f"   Interests: {len(interests)}")
        
        # Validate key requirements from the user
        print("\n✅ VALIDATION RESULTS:")
        print("=" * 40)
        
        # Check field mapping quality
        designation = result.get('designation', '')
        location = result.get('location', '')
        
        print(f"🔍 Designation Clean: {'✅' if designation and 'at' not in designation and 'Pakistan' not in designation else '❌'}")
        print(f"   Value: '{designation}'")
        
        print(f"🔍 Location Real: {'✅' if location and 'Cloud' not in location else '❌'}")
        print(f"   Value: '{location}'")
        
        print(f"🔍 Experience Calculated: {'✅' if result.get('experience') and result.get('experience') != '0 years' else '❌'}")
        print(f"   Value: '{result.get('experience')}'")
        
        print(f"🔍 Complete Contact Info: {'✅' if len(contact_info) >= 3 else '❌'}")
        print(f"   Fields: {len(contact_info)}")
        
        print(f"🔍 All Sections Extracted: {'✅' if all([len(skills) > 0, len(experience_details) > 0, len(education) > 0, len(projects) > 0, len(languages) > 0]) else '❌'}")
        
        # Summary
        total_fields = len([v for v in result.values() if v and v != [] and v != {} and v != ""])
        print(f"\n📈 SUMMARY: {total_fields} fields extracted successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_7_agent_system())
    if success:
        print("\n🎉 7-Agent System Test PASSED!")
    else:
        print("\n💥 7-Agent System Test FAILED!")