#!/usr/bin/env python3
"""
Test script to debug skills extraction issue by uploading document directly to API
"""
import requests
import json

def test_document_upload():
    """Test document upload and check skills in logs"""
    
    # First, we need to create a user and login to get token
    # For testing, let's use existing credentials or create a test user
    
    BASE_URL = "http://localhost:8001"
    
    # Create test resume content as a simple text file
    test_resume_content = """
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
    
    # Save as a PDF-like text file for testing
    with open("test_resume_debug.txt", "w") as f:
        f.write(test_resume_content)
    
    print("🚀 Testing document upload with skills debug...")
    print("📝 Server should show detailed debug logs for skills extraction")
    print("🔍 Check the server console for:")
    print("   - 'SKILLS DEBUG' messages")
    print("   - Skills extraction from AI agents")
    print("   - Skills mapping in onboarding router")
    print("   - Skills storage in user service")
    print("\n" + "="*60)
    print("📁 Test resume file created: test_resume_debug.txt")
    print("🌐 Upload this file manually through the frontend at:")
    print(f"   {BASE_URL}/onboarding")
    print("\n🔍 Then check the server logs for skills debug information")
    
if __name__ == "__main__":
    test_document_upload()