#!/usr/bin/env python3
"""
Test script to verify the new missing sections functionality
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai_service import AIService

async def test_missing_sections_detection():
    """Test the new _determine_truly_missing_sections function"""
    
    ai_service = AIService()
    
    # Test case 1: Complete profile (no missing sections)
    complete_profile = {
        "name": "John Doe",
        "designation": "Software Engineer",
        "location": "San Francisco, CA",
        "contact_info": {
            "email": "john@example.com",
            "phone": "123-456-7890",
            "linkedin": "linkedin.com/in/johndoe"
        },
        "experience_details": [
            {"company": "Tech Corp", "position": "Software Engineer", "duration": "2020-2023"}
        ],
        "skills": [{"name": "Python"}, {"name": "JavaScript"}, {"name": "React"}],
        "education": [{"institution": "University", "degree": "BS Computer Science"}],
        "projects": [{"name": "Project 1", "description": "A web app"}],
        "languages": [{"name": "English", "proficiency": "Native"}],
        "certifications": ["AWS Certified"],
        "awards": [{"title": "Best Developer"}],
        "publications": [{"title": "Research Paper"}],
        "volunteer_experience": [{"organization": "Charity", "role": "Volunteer"}],
        "interests": ["Reading", "Hiking"]
    }
    
    missing_sections = ai_service._determine_truly_missing_sections(complete_profile)
    print(f"✅ Complete profile - Missing sections: {missing_sections}")
    assert len(missing_sections) == 0, "Complete profile should have no missing sections"
    
    # Test case 2: Profile with missing sections
    incomplete_profile = {
        "name": "Jane Doe",
        "designation": "Developer",
        "location": "New York, NY",
        "contact_info": {
            "email": "jane@example.com"
            # Missing phone and other contact methods
        },
        "experience_details": [],  # No experience
        "skills": [{"name": "Python"}],  # Only 1 skill (less than 3)
        "education": [],  # No education
        "projects": [],  # No projects
        "languages": [],  # No languages
        "certifications": [],  # No certifications
        "awards": [],  # No awards
        "publications": [],  # No publications
        "volunteer_experience": [],  # No volunteer experience
        "interests": []  # No interests
    }
    
    missing_sections = ai_service._determine_truly_missing_sections(incomplete_profile)
    print(f"⚠️ Incomplete profile - Missing sections: {missing_sections}")
    assert len(missing_sections) > 0, "Incomplete profile should have missing sections"
    assert "contact_info" in missing_sections, "Should detect missing contact info"
    assert "work_experience" in missing_sections, "Should detect missing work experience"
    assert "skills" in missing_sections, "Should detect insufficient skills"
    assert "education" in missing_sections, "Should detect missing education"
    
    # Test case 3: Profile with some sections but not others
    partial_profile = {
        "name": "Bob Smith",
        "designation": "Data Scientist",
        "location": "Boston, MA",
        "contact_info": {
            "email": "bob@example.com",
            "phone": "987-654-3210"
        },
        "experience_details": [
            {"company": "Data Corp", "position": "Data Scientist", "duration": "2021-2023"}
        ],
        "skills": [{"name": "Python"}, {"name": "SQL"}, {"name": "Machine Learning"}],
        "education": [{"institution": "MIT", "degree": "MS Data Science"}],
        "projects": [],  # No projects
        "languages": [],  # No languages
        "certifications": [],  # No certifications
        "awards": [],  # No awards
        "publications": [],  # No publications
        "volunteer_experience": [],  # No volunteer experience
        "interests": []  # No interests
    }
    
    missing_sections = ai_service._determine_truly_missing_sections(partial_profile)
    print(f"📊 Partial profile - Missing sections: {missing_sections}")
    assert "projects" in missing_sections, "Should detect missing projects"
    assert "languages" in missing_sections, "Should detect missing languages"
    assert "certifications" in missing_sections, "Should detect missing certifications"
    assert "work_experience" not in missing_sections, "Should NOT detect work experience as missing"
    assert "skills" not in missing_sections, "Should NOT detect skills as missing"
    assert "education" not in missing_sections, "Should NOT detect education as missing"
    
    print("🎉 All tests passed! The missing sections detection is working correctly.")

if __name__ == "__main__":
    asyncio.run(test_missing_sections_detection()) 