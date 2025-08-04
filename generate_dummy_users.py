#!/usr/bin/env python3
"""
Dummy User Generation Script for ResumeAgentAI
Creates realistic users with complete profile data for all sections.
"""

import asyncio
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import uuid
from faker import Faker
import json

# Database configuration - Update these with your live database credentials
MONGODB_URL = "mongodb://localhost:27017"  # Replace with your live MongoDB URL
DATABASE_NAME = "ai_resume_builder"

# Initialize faker for different locales to get diverse names
fake = Faker(['en_US', 'en_GB', 'en_AU', 'en_CA'])
fake_countries = {
    'US': Faker('en_US'),
    'GB': Faker('en_GB'), 
    'CA': Faker('en_CA'),
    'AU': Faker('en_AU'),
    'DE': Faker('de_DE'),
    'FR': Faker('fr_FR'),
    'IT': Faker('it_IT'),
    'ES': Faker('es_ES'),
    'IN': Faker('en_IN'),
    'JP': Faker('ja_JP'),
    'BR': Faker('pt_BR'),
    'MX': Faker('es_MX')
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Sample data for generating realistic profiles
PROFESSIONS = [
    "Software Engineer", "Data Scientist", "Product Manager", "UX/UI Designer",
    "Marketing Manager", "Sales Representative", "Business Analyst", "DevOps Engineer",
    "Frontend Developer", "Backend Developer", "Full Stack Developer", "Mobile Developer",
    "AI/ML Engineer", "Cybersecurity Specialist", "Cloud Architect", "Database Administrator",
    "Project Manager", "Scrum Master", "Quality Assurance Engineer", "Technical Writer",
    "Digital Marketing Specialist", "Content Creator", "Graphic Designer", "Financial Analyst",
    "HR Manager", "Operations Manager", "Customer Success Manager", "Solutions Architect"
]

SKILLS_BY_PROFESSION = {
    "Software Engineer": ["Python", "JavaScript", "Java", "C++", "Git", "Docker", "AWS", "React", "Node.js", "SQL"],
    "Data Scientist": ["Python", "R", "Machine Learning", "SQL", "Pandas", "NumPy", "TensorFlow", "PyTorch", "Tableau", "Power BI"],
    "Product Manager": ["Product Strategy", "Market Research", "Agile", "Scrum", "Analytics", "User Research", "Roadmapping", "Jira", "Figma"],
    "UX/UI Designer": ["Figma", "Adobe XD", "Sketch", "User Research", "Prototyping", "Wireframing", "Adobe Creative Suite", "CSS", "HTML"],
    "Marketing Manager": ["Digital Marketing", "SEO", "SEM", "Social Media Marketing", "Content Marketing", "Google Analytics", "HubSpot", "Email Marketing"],
    "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "Azure", "Jenkins", "Terraform", "Ansible", "Linux", "Python", "Bash"],
    "Frontend Developer": ["React", "Vue.js", "Angular", "JavaScript", "TypeScript", "CSS", "HTML", "Sass", "Webpack", "npm"],
    "Backend Developer": ["Node.js", "Python", "Java", "Express.js", "Django", "Spring Boot", "MongoDB", "PostgreSQL", "Redis", "API Development"]
}

COMPANIES = [
    "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla", "Uber", "Airbnb", "Spotify",
    "Stripe", "Shopify", "Slack", "Zoom", "Dropbox", "Adobe", "Salesforce", "Oracle", "IBM", "Intel",
    "NVIDIA", "PayPal", "eBay", "Twitter", "LinkedIn", "GitHub", "Atlassian", "Palantir", "Snowflake",
    "Datadog", "MongoDB", "Redis Labs", "Elastic", "HashiCorp", "Docker", "Kubernetes", "GitLab"
]

UNIVERSITIES = [
    "MIT", "Stanford University", "Harvard University", "University of California, Berkeley", "Carnegie Mellon University",
    "University of Oxford", "University of Cambridge", "Imperial College London", "University of Toronto", "University of Waterloo",
    "ETH Zurich", "Technical University of Munich", "University of Tokyo", "National University of Singapore",
    "Indian Institute of Technology", "University of Melbourne", "University of Sydney", "University of Edinburgh"
]

DEGREES = ["Bachelor of Science", "Master of Science", "Bachelor of Arts", "Master of Arts", "PhD", "Bachelor of Engineering", "Master of Engineering"]
FIELDS_OF_STUDY = ["Computer Science", "Data Science", "Software Engineering", "Information Technology", "Business Administration", "Marketing", "Design", "Psychology", "Mathematics", "Physics"]

LANGUAGES = ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Mandarin", "Japanese", "Korean", "Hindi", "Arabic", "Russian"]
PROFICIENCY_LEVELS = ["Native", "Fluent", "Advanced", "Intermediate", "Beginner"]

INTERESTS = [
    "Photography", "Travel", "Reading", "Cooking", "Hiking", "Gaming", "Music", "Art", "Sports", "Yoga",
    "Meditation", "Writing", "Blogging", "Volunteering", "Learning Languages", "Technology", "Innovation",
    "Startups", "Entrepreneurship", "Fitness", "Running", "Cycling", "Swimming", "Rock Climbing", "Surfing"
]

COUNTRIES = ["United States", "United Kingdom", "Canada", "Australia", "Germany", "France", "Italy", "Spain", "India", "Japan", "Brazil", "Mexico"]

async def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def generate_username(name: str) -> str:
    """Generate a unique username from name"""
    base_username = name.lower().replace(" ", "").replace("'", "").replace("-", "")
    # Add random numbers to make it unique
    return f"{base_username}{random.randint(10, 999)}"

def generate_email(name: str) -> str:
    """Generate email from name"""
    username = generate_username(name)
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "protonmail.com", "icloud.com"]
    return f"{username}@{random.choice(domains)}"

def generate_phone() -> str:
    """Generate a realistic phone number"""
    return fake.phone_number()

def generate_linkedin_url(name: str) -> str:
    """Generate LinkedIn URL"""
    username = name.lower().replace(" ", "-").replace("'", "").replace(".", "")
    return f"https://linkedin.com/in/{username}-{random.randint(100, 999)}"

def generate_github_url(name: str) -> str:
    """Generate GitHub URL"""
    username = generate_username(name)
    return f"https://github.com/{username}"

def generate_portfolio_url(name: str) -> str:
    """Generate portfolio URL"""
    username = name.lower().replace(" ", "").replace("'", "")
    return f"https://{username}portfolio.com"

def generate_skills_for_profession(profession: str) -> List[Dict[str, Any]]:
    """Generate skills based on profession"""
    base_skills = SKILLS_BY_PROFESSION.get(profession, ["Communication", "Problem Solving", "Leadership", "Teamwork"])
    
    # Add some random additional skills
    all_skills = []
    for skill_lists in SKILLS_BY_PROFESSION.values():
        all_skills.extend(skill_lists)
    
    additional_skills = random.choices([s for s in all_skills if s not in base_skills], k=random.randint(2, 5))
    all_skills_list = base_skills + additional_skills
    
    skills = []
    for skill in all_skills_list[:random.randint(8, 15)]:
        skills.append({
            "name": skill,
            "level": random.choice(["Beginner", "Intermediate", "Advanced", "Expert"]),
            "years": random.randint(1, 10),
            "id": str(uuid.uuid4())
        })
    
    return skills

def generate_experience(profession: str, years_experience: int) -> List[Dict[str, Any]]:
    """Generate work experience"""
    experiences = []
    current_date = datetime.now()
    
    # Generate 2-4 experiences based on years of experience
    num_experiences = min(4, max(1, years_experience // 2))
    
    for i in range(num_experiences):
        is_current = (i == 0)  # First experience is current
        
        if is_current:
            start_date = current_date - timedelta(days=random.randint(365, 365*3))
            end_date = None
            duration = f"{(current_date - start_date).days // 30} months"
        else:
            end_date = current_date - timedelta(days=random.randint(30, 365*2))
            start_date = end_date - timedelta(days=random.randint(365, 365*3))
            duration = f"{(end_date - start_date).days // 30} months"
            current_date = start_date  # For next iteration
        
        # Generate job titles based on seniority
        seniority_levels = ["Junior", "Mid-level", "Senior", "Lead", "Principal"] if i == 0 else ["Junior", "Mid-level", "Senior"]
        seniority = seniority_levels[min(len(seniority_levels)-1, i)]
        
        position = f"{seniority} {profession}" if seniority != "Mid-level" else profession
        
        experiences.append({
            "company": random.choice(COMPANIES),
            "position": position,
            "duration": duration,
            "description": fake.text(max_nb_chars=200),
            "start_date": start_date.strftime("%Y-%m") if start_date else None,
            "end_date": end_date.strftime("%Y-%m") if end_date else None,
            "current": is_current
        })
    
    return experiences

def generate_projects(profession: str) -> List[Dict[str, Any]]:
    """Generate projects based on profession"""
    project_names = {
        "Software Engineer": ["E-commerce Platform", "Task Management App", "Social Media Dashboard", "API Gateway", "Microservices Architecture"],
        "Data Scientist": ["Customer Churn Prediction", "Sales Forecasting Model", "Recommendation System", "Fraud Detection System", "Market Analysis Dashboard"],
        "UX/UI Designer": ["Mobile Banking App", "E-learning Platform", "Healthcare Dashboard", "Travel Booking Site", "Productivity Tool"],
        "Product Manager": ["Mobile App Launch", "Feature Roadmap Planning", "User Acquisition Strategy", "Product Analytics Dashboard", "Market Expansion"]
    }
    
    names = project_names.get(profession, ["Innovative Solution", "Digital Platform", "Management System", "Analytics Tool", "Automation Framework"])
    
    projects = []
    for i in range(random.randint(2, 5)):
        project_name = random.choice(names) + f" v{random.randint(1, 3)}.{random.randint(0, 9)}"
        
        # Generate technologies based on profession
        base_skills = SKILLS_BY_PROFESSION.get(profession, ["JavaScript", "Python", "React"])
        technologies = random.choices(base_skills, k=random.randint(3, 6))
        
        projects.append({
            "name": project_name,
            "description": fake.text(max_nb_chars=150),
            "technologies": technologies,
            "url": f"https://{project_name.lower().replace(' ', '-')}.com" if random.choice([True, False]) else None,
            "github_url": f"https://github.com/{generate_username(fake.name())}/{project_name.lower().replace(' ', '-')}" if random.choice([True, False]) else None,
            "duration": f"{random.randint(1, 12)} months"
        })
    
    return projects

def generate_education() -> List[Dict[str, Any]]:
    """Generate education history"""
    education = []
    current_year = datetime.now().year
    
    # Generate 1-3 education entries
    for i in range(random.randint(1, 3)):
        end_year = current_year - random.randint(1, 15)
        start_year = end_year - random.randint(2, 4)
        
        education.append({
            "institution": random.choice(UNIVERSITIES),
            "degree": random.choice(DEGREES),
            "field_of_study": random.choice(FIELDS_OF_STUDY),
            "start_date": f"{start_year}-09",
            "end_date": f"{end_year}-06",
            "grade": f"{random.uniform(3.0, 4.0):.2f} GPA" if random.choice([True, False]) else None,
            "activities": fake.text(max_nb_chars=100) if random.choice([True, False]) else None,
            "description": fake.text(max_nb_chars=150) if random.choice([True, False]) else None
        })
    
    return education

def generate_languages() -> List[Dict[str, Any]]:
    """Generate language proficiencies"""
    languages = []
    
    # Always include English
    languages.append({
        "name": "English",
        "proficiency": random.choice(["Native", "Fluent", "Advanced"])
    })
    
    # Add 1-3 additional languages
    additional_langs = random.choices([l for l in LANGUAGES if l != "English"], k=random.randint(1, 3))
    for lang in additional_langs:
        languages.append({
            "name": lang,
            "proficiency": random.choice(PROFICIENCY_LEVELS[1:])  # Exclude Native for non-English
        })
    
    return languages

def generate_awards() -> List[Dict[str, Any]]:
    """Generate awards and recognitions"""
    award_types = [
        "Employee of the Month", "Innovation Award", "Best Project Award", "Excellence in Performance",
        "Leadership Recognition", "Customer Success Award", "Technical Excellence Award", "Team Player Award"
    ]
    
    awards = []
    for _ in range(random.randint(1, 4)):
        award_date = fake.date_between(start_date='-5y', end_date='today')
        awards.append({
            "title": random.choice(award_types),
            "issuer": random.choice(COMPANIES),
            "date": award_date.strftime("%Y-%m"),
            "description": fake.text(max_nb_chars=100) if random.choice([True, False]) else None
        })
    
    return awards

def generate_publications() -> List[Dict[str, Any]]:
    """Generate publications"""
    if random.choice([True, False, False]):  # 33% chance of having publications
        publications = []
        for _ in range(random.randint(1, 3)):
            pub_date = fake.date_between(start_date='-3y', end_date='today')
            publications.append({
                "title": fake.sentence(nb_words=6),
                "publisher": random.choice(["IEEE", "ACM", "Springer", "Nature", "Medium", "Dev.to", "LinkedIn"]),
                "date": pub_date.strftime("%Y-%m"),
                "url": fake.url() if random.choice([True, False]) else None,
                "description": fake.text(max_nb_chars=120)
            })
        return publications
    return []

def generate_volunteer_experience() -> List[Dict[str, Any]]:
    """Generate volunteer experience"""
    if random.choice([True, False]):  # 50% chance of having volunteer experience
        volunteer_orgs = [
            "Red Cross", "Habitat for Humanity", "Local Food Bank", "Animal Shelter", "Community Center",
            "Environmental Foundation", "Youth Mentorship Program", "Literacy Program", "Tech for Good"
        ]
        
        experiences = []
        for _ in range(random.randint(1, 2)):
            start_date = fake.date_between(start_date='-3y', end_date='-1y')
            end_date = fake.date_between(start_date=start_date, end_date='today')
            
            experiences.append({
                "organization": random.choice(volunteer_orgs),
                "role": random.choice(["Volunteer", "Team Leader", "Coordinator", "Mentor", "Organizer"]),
                "start_date": start_date.strftime("%Y-%m"),
                "end_date": end_date.strftime("%Y-%m") if random.choice([True, False]) else None,
                "description": fake.text(max_nb_chars=120)
            })
        
        return experiences
    return []

def generate_work_preferences() -> Dict[str, Any]:
    """Generate work preferences"""
    return {
        "current_employment_mode": random.choices(["Full-time", "Part-time", "Contract", "Freelance"], k=random.randint(1, 2)),
        "preferred_work_mode": random.choices(["Remote", "Hybrid", "On-site"], k=random.randint(1, 3)),
        "preferred_employment_type": random.choices(["Full-time", "Part-time", "Contract"], k=random.randint(1, 2)),
        "preferred_location": random.choice(COUNTRIES),
        "notice_period": random.choice(["Immediate", "2 weeks", "1 month", "2 months", "3 months"]),
        "availability": random.choice(["immediate", "within_month", "within_3_months"])
    }

def generate_contact_info(name: str) -> Dict[str, Any]:
    """Generate contact information"""
    contact = {
        "email": generate_email(name),
        "phone": generate_phone(),
        "linkedin": generate_linkedin_url(name),
    }
    
    # Randomly add optional fields
    if random.choice([True, False]):
        contact["github"] = generate_github_url(name)
    if random.choice([True, False]):
        contact["portfolio"] = generate_portfolio_url(name)
    if random.choice([True, False]):
        contact["website"] = f"https://{name.lower().replace(' ', '')}.dev"
    
    return contact

async def generate_dummy_user(country_code: str = "US") -> Dict[str, Any]:
    """Generate a single dummy user with complete profile data"""
    
    # Use country-specific faker
    country_fake = fake_countries.get(country_code, fake)
    
    # Generate basic info
    name = country_fake.name()
    profession = random.choice(PROFESSIONS)
    years_experience = random.randint(1, 15)
    
    # Generate location based on country
    if country_code == "US":
        location = f"{country_fake.city()}, {country_fake.state()}, USA"
    elif country_code == "GB":
        location = f"{country_fake.city()}, UK"
    elif country_code == "CA":
        location = f"{country_fake.city()}, Canada"
    else:
        location = f"{country_fake.city()}, {COUNTRIES[list(fake_countries.keys()).index(country_code)]}"
    
    # Create user document
    user_data = {
        "email": generate_email(name),
        "name": name,
        "username": generate_username(name),
        "designation": profession,
        "location": location,
        "profile_picture": None,  # Will be set to placeholder
        "profile_picture_url": None,
        "is_looking_for_job": random.choice([True, False]),
        "expected_salary": f"${random.randint(60, 200)}k",
        "current_salary": f"${random.randint(50, 180)}k",
        "experience": f"{years_experience} years",
        "summary": country_fake.text(max_nb_chars=300),
        "additional_info": country_fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
        "profession": profession,
        
        # Detailed sections
        "skills": generate_skills_for_profession(profession),
        "experience_details": generate_experience(profession, years_experience),
        "projects": generate_projects(profession),
        "certifications": [f"{random.choice(['AWS', 'Google', 'Microsoft', 'Oracle'])} Certified {random.choice(['Developer', 'Administrator', 'Architect'])}" for _ in range(random.randint(0, 3))],
        "education": generate_education(),
        "languages": generate_languages(),
        "awards": generate_awards(),
        "publications": generate_publications(),
        "volunteer_experience": generate_volunteer_experience(),
        "interests": random.choices(INTERESTS, k=random.randint(3, 8)),
        
        # Contact and preferences
        "contact_info": generate_contact_info(name),
        "work_preferences": generate_work_preferences(),
        
        # System fields
        "hashed_password": await hash_password("dummypassword123"),
        "rating": round(random.uniform(3.5, 5.0), 1),
        "onboarding_completed": True,
        "onboarding_progress": {
            "step_1_pdf_upload": "completed",
            "step_2_profile_info": "completed", 
            "step_3_work_preferences": "completed",
            "step_4_salary_availability": "completed",
            "current_step": 4,
            "completed": True
        },
        "daily_requests": 0,
        "last_request_reset": datetime.utcnow(),
        "job_matching_request_timestamps": [],
        "chat_request_timestamps": [],
        "refresh_token_jti": None,
        "refresh_token_expires_at": None,
        "password_reset_token": None,
        "password_reset_expires_at": None,
        "google_id": None,
        "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 365)),
        "updated_at": datetime.utcnow(),
        "section_order": ["about", "experience", "skills", "projects", "education", "contact", "languages", "awards", "publications", "volunteer", "interests", "preferences"]
    }
    
    return user_data

async def create_dummy_users(count: int = 50) -> None:
    """Create dummy users and insert them into the database"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        users_collection = db.users
        
        print(f"Connected to MongoDB: {MONGODB_URL}")
        print(f"Database: {DATABASE_NAME}")
        print(f"Generating {count} dummy users...")
        
        users = []
        countries = list(fake_countries.keys())
        
        for i in range(count):
            # Distribute users across different countries
            country = countries[i % len(countries)]
            user = await generate_dummy_user(country)
            users.append(user)
            
            if (i + 1) % 10 == 0:
                print(f"Generated {i + 1}/{count} users...")
        
        # Insert users in batches
        batch_size = 10
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            try:
                result = await users_collection.insert_many(batch)
                print(f"Inserted batch {i//batch_size + 1}: {len(result.inserted_ids)} users")
            except Exception as e:
                print(f"Error inserting batch {i//batch_size + 1}: {e}")
                continue
        
        print(f"\n✅ Successfully created {len(users)} dummy users!")
        print("Users have been distributed across multiple countries with realistic data.")
        print("All users have the password: 'dummypassword123'")
        
        # Show some sample usernames
        print("\nSample usernames created:")
        for i in range(min(10, len(users))):
            print(f"  - {users[i]['username']} ({users[i]['name']}) - {users[i]['profession']}")
        
        await client.close()
        
    except Exception as e:
        print(f"Error creating dummy users: {e}")
        raise

async def main():
    """Main function to run the script"""
    import sys
    
    # Get count from command line argument or use default
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    
    print("🚀 Starting Dummy User Generation Script")
    print("=" * 50)
    
    await create_dummy_users(count)
    
    print("\n" + "=" * 50)
    print("✨ Dummy user generation completed!")

if __name__ == "__main__":
    # Install required packages if not already installed
    try:
        import faker
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(["pip", "install", "faker"])
        import faker
    
    asyncio.run(main())