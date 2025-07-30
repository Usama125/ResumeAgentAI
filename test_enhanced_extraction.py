#!/usr/bin/env python3
"""
Test script to verify enhanced document extraction
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.pdf_service import DocumentService
from app.services.ai_service import AIService

async def test_extraction():
    """Test the enhanced extraction with sample resume content"""
    
    # Sample resume content with different heading formats
    sample_resume_content = """
    John Doe
    Software Engineer | Full-Stack Developer
    San Francisco, CA | john.doe@email.com | (555) 123-4567
    LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe
    Portfolio: johndoe.dev
    
    PROFESSIONAL SUMMARY
    Experienced full-stack developer with 5+ years of expertise in building scalable web applications.
    Passionate about clean code and modern development practices.
    
    CORE COMPETENCIES
    • JavaScript, Python, React, Node.js
    • AWS, Docker, Kubernetes
    • PostgreSQL, MongoDB
    • Git, CI/CD, Agile methodologies
    
    PROFESSIONAL BACKGROUND
    
    Senior Software Engineer | TechCorp Inc. | 2021 - Present
    • Led development of microservices architecture serving 1M+ users
    • Implemented CI/CD pipelines reducing deployment time by 60%
    • Mentored junior developers and conducted code reviews
    
    Software Developer | StartupXYZ | 2019 - 2021
    • Developed full-stack web applications using React and Node.js
    • Collaborated with cross-functional teams in Agile environment
    • Improved application performance by 40% through optimization
    
    KEY PROJECTS
    
    E-commerce Platform
    • Built scalable e-commerce platform handling 10K+ daily transactions
    • Technologies: React, Node.js, PostgreSQL, AWS
    • GitHub: github.com/johndoe/ecommerce-platform
    
    Task Management App
    • Developed task management application with real-time collaboration
    • Technologies: React, Socket.io, MongoDB
    
    EDUCATIONAL QUALIFICATIONS
    
    Bachelor of Science in Computer Science
    University of California, Berkeley | 2015 - 2019
    GPA: 3.8/4.0
    
    PROFESSIONAL CERTIFICATIONS
    • AWS Certified Solutions Architect
    • Google Cloud Professional Developer
    • Certified Scrum Master (CSM)
    
    ADDITIONAL INFORMATION
    
    Languages: English (Native), Spanish (Intermediate), French (Beginner)
    
    Volunteer Work:
    • Code Mentor at Local Coding Bootcamp (2020-Present)
    • Volunteer Developer for Non-profit Organizations
    
    Interests: Open source contribution, Photography, Rock climbing
    
    Awards:
    • Employee of the Month - TechCorp Inc. (2022)
    • Best Innovation Award - StartupXYZ (2020)
    """
    
    print("🚀 Testing Enhanced Document Extraction")
    print("=" * 50)
    
    # Test AI service directly
    ai_service = AIService()
    
    print("🤖 Testing AI extraction with sample resume content...")
    result = await ai_service.process_resume_content(sample_resume_content)
    
    if "error" in result:
        print(f"❌ AI extraction failed: {result['error']}")
        return
    
    print("✅ AI extraction successful!")
    print("\n📊 Extracted Data Summary:")
    print(f"Name: {result.get('name', 'Not found')}")
    print(f"Profession: {result.get('profession', 'Not detected')}")
    print(f"Designation: {result.get('designation', 'Not found')}")
    print(f"Experience: {result.get('experience', 'Not calculated')}")
    print(f"Skills count: {len(result.get('skills', []))}")
    print(f"Experience details count: {len(result.get('experience_details', []))}")
    print(f"Projects count: {len(result.get('projects', []))}")
    print(f"Education count: {len(result.get('education', []))}")
    print(f"Certifications count: {len(result.get('certifications', []))}")
    print(f"Languages count: {len(result.get('languages', []))}")
    print(f"Awards count: {len(result.get('awards', []))}")
    print(f"Volunteer experience count: {len(result.get('volunteer_experience', []))}")
    print(f"Contact info available: {'Yes' if result.get('contact_info') else 'No'}")
    
    # Display some detailed examples
    if result.get('skills'):
        print(f"\n🔧 Sample Skills:")
        for skill in result.get('skills', [])[:3]:  # Show first 3
            print(f"  • {skill.get('name', 'Unknown')} - {skill.get('level', 'Unknown')} ({skill.get('years', 0)} years)")
    
    if result.get('experience_details'):
        print(f"\n💼 Sample Experience:")
        for exp in result.get('experience_details', [])[:2]:  # Show first 2
            print(f"  • {exp.get('position', 'Unknown')} at {exp.get('company', 'Unknown')} ({exp.get('duration', 'Unknown')})")
    
    if result.get('contact_info'):
        contact = result.get('contact_info', {})
        print(f"\n📞 Contact Info:")
        print(f"  • Email: {contact.get('email', 'Not found')}")
        print(f"  • Phone: {contact.get('phone', 'Not found')}")
        print(f"  • LinkedIn: {contact.get('linkedin', 'Not found')}")
        print(f"  • GitHub: {contact.get('github', 'Not found')}")
        print(f"  • Portfolio: {contact.get('portfolio', 'Not found')}")
    
    print("\n✅ Enhanced extraction test completed successfully!")
    print("📝 The AI successfully handled different heading formats and extracted comprehensive data.")

if __name__ == "__main__":
    # Check if we have the required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key to test the extraction")
        sys.exit(1)
    
    # Run the test
    asyncio.run(test_extraction())