#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pdf_service import PDFService

def test_pdf_generation():
    """Test PDF generation with sample user data"""
    print("🧪 Testing PDF Generation...")
    
    # Sample user data
    user_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "designation": "Senior Software Engineer",
        "location": "San Francisco, CA",
        "about": "Experienced software engineer with 5+ years of experience in full-stack development.",
        "profile_picture": "",  # No profile picture for test
        "contact_info": {
            "email": "john.doe@example.com",
            "phone": "+1 (555) 123-4567",
            "linkedin": "linkedin.com/in/johndoe",
            "website": "johndoe.dev"
        },
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "start_date": "2022",
                "end_date": "Present",
                "location": "San Francisco, CA",
                "description": "Led development of scalable web applications using React and Node.js."
            },
            {
                "title": "Software Engineer",
                "company": "StartupXYZ",
                "start_date": "2020",
                "end_date": "2022",
                "location": "New York, NY",
                "description": "Developed and maintained multiple web applications."
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "MIT",
                "start_date": "2016",
                "end_date": "2020",
                "location": "Cambridge, MA",
                "gpa": "3.8",
                "description": "Graduated with honors. Focused on software engineering and algorithms."
            }
        ],
        "skills": [
            "JavaScript", "React", "Node.js", "Python", "TypeScript", "AWS", "Docker",
            "MongoDB", "PostgreSQL", "Git", "REST APIs", "GraphQL", "CI/CD", "Agile"
        ],
        "projects": [
            {
                "title": "E-commerce Platform",
                "link": "github.com/johndoe/ecommerce",
                "start_date": "2023",
                "end_date": "2023",
                "description": "Built a full-stack e-commerce platform with React and Node.js.",
                "technologies": ["React", "Node.js", "MongoDB", "Stripe"]
            }
        ],
        "languages": [
            {"language": "English", "proficiency": "Native"},
            {"language": "Spanish", "proficiency": "Intermediate"}
        ],
        "certifications": [
            {
                "title": "AWS Certified Developer",
                "issuer": "Amazon Web Services",
                "date": "2023",
                "description": "Certified in developing and maintaining applications on AWS."
            }
        ],
        "awards": [
            {
                "title": "Best Developer Award",
                "issuer": "TechCorp",
                "date": "2023",
                "description": "Recognized for outstanding contributions to the team."
            }
        ],
        "publications": [],
        "volunteer_experience": [],
        "interests": ["Open Source", "Machine Learning", "Blockchain"]
    }
    
    try:
        # Create PDF service
        pdf_service = PDFService()
        
        # Generate PDF
        print("📄 Generating PDF...")
        pdf_buffer = pdf_service.create_profile_pdf(user_data)
        
        # Save PDF for inspection
        output_path = "test_profile.pdf"
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF generated successfully: {output_path}")
        print(f"📊 PDF size: {len(pdf_buffer.getvalue())} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    if success:
        print("\n🎉 PDF generation test passed!")
    else:
        print("\n❌ PDF generation test failed!")
        sys.exit(1) 