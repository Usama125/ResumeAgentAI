"""
Robust Dummy User Generation Router
Creates realistic, complete dummy users in the background for testing/demo
"""
from fastapi import APIRouter, HTTPException, Path, BackgroundTasks
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from faker import Faker
from datetime import datetime, timedelta
import random
import os

# Use your live DB credentials from environment/config
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://Usama125:yabwj7sYtLD0FifC@cluster0.tfx2doy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ai_resume_builder")

router = APIRouter(prefix="/generatedummyusers", tags=["dummy-users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
fake = Faker()

COUNTRIES = [
    ("US", "en_US"), ("GB", "en_GB"), ("CA", "en_CA"), ("AU", "en_AU"), ("DE", "de_DE"), ("FR", "fr_FR"),
    ("IT", "it_IT"), ("ES", "es_ES"), ("IN", "en_IN"), ("JP", "ja_JP"), ("BR", "pt_BR"), ("MX", "es_MX")
]

PROFESSIONS = [
    "Software Engineer", "Data Scientist", "Product Manager", "UX/UI Designer", "Marketing Manager",
    "Sales Representative", "Business Analyst", "DevOps Engineer", "Frontend Developer", "Backend Developer",
    "Full Stack Developer", "Mobile Developer", "AI/ML Engineer", "Cybersecurity Specialist", "Cloud Architect",
    "Database Administrator", "Project Manager", "Scrum Master", "Quality Assurance Engineer", "Technical Writer",
    "Digital Marketing Specialist", "Content Creator", "Graphic Designer", "Financial Analyst", "HR Manager",
    "Operations Manager", "Customer Success Manager", "Solutions Architect"
]

COMPANIES = [
    "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla", "Uber", "Airbnb", "Spotify",
    "Stripe", "Shopify", "Slack", "Zoom", "Dropbox", "Adobe", "Salesforce", "Oracle", "IBM", "Intel"
]

UNIVERSITIES = [
    "MIT", "Stanford University", "Harvard University", "UC Berkeley", "Carnegie Mellon University",
    "University of Oxford", "University of Cambridge", "Imperial College London", "University of Toronto",
    "University of Waterloo", "ETH Zurich", "Technical University of Munich", "University of Tokyo",
    "National University of Singapore", "IIT Bombay", "University of Melbourne", "University of Sydney",
    "University of Edinburgh"
]

DEGREES = ["Bachelor of Science", "Master of Science", "Bachelor of Arts", "Master of Arts", "PhD", "Bachelor of Engineering", "Master of Engineering"]
FIELDS_OF_STUDY = ["Computer Science", "Data Science", "Software Engineering", "Information Technology", "Business Administration", "Marketing", "Design", "Psychology", "Mathematics", "Physics"]
LANGUAGES = ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Mandarin", "Japanese", "Korean", "Hindi", "Arabic", "Russian"]
PROFICIENCY_LEVELS = ["Native", "Fluent", "Advanced", "Intermediate", "Beginner"]
INTERESTS = ["Photography", "Travel", "Reading", "Cooking", "Hiking", "Gaming", "Music", "Art", "Sports", "Yoga", "Meditation", "Writing", "Blogging", "Volunteering", "Learning Languages", "Technology", "Innovation", "Startups", "Entrepreneurship", "Fitness", "Running", "Cycling", "Swimming", "Rock Climbing", "Surfing"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def generate_username(name: str) -> str:
    base = name.lower().replace(" ", "").replace("'", "").replace("-", "")
    return f"{base}{random.randint(100, 9999)}"

def generate_profile(locale: str) -> Dict[str, Any]:
    local_fake = Faker(locale)
    name = local_fake.name()
    username = generate_username(name)
    email = f"{username}@example.com"
    profession = random.choice(PROFESSIONS)
    years_exp = random.randint(2, 12)
    skills = [
        {"name": "Python", "level": random.choice(["Advanced", "Expert", "Intermediate"]), "years": random.randint(1, years_exp)},
        {"name": "JavaScript", "level": random.choice(["Advanced", "Expert", "Intermediate"]), "years": random.randint(1, years_exp)},
        {"name": "React", "level": random.choice(["Advanced", "Intermediate"]), "years": random.randint(1, years_exp)},
        {"name": "Node.js", "level": random.choice(["Advanced", "Intermediate"]), "years": random.randint(1, years_exp)}
    ]
    experience_details = [
        {
            "company": random.choice(COMPANIES),
            "position": profession,
            "duration": f"{random.randint(1, years_exp)} years",
            "description": f"Worked on {random.choice(['cloud', 'web', 'AI', 'mobile'])} projects using modern technologies.",
            "start_date": str(local_fake.date_between(start_date='-10y', end_date='-2y')),
            "end_date": str(local_fake.date_between(start_date='-2y', end_date='today')),
            "current": False
        }
        for _ in range(random.randint(1, 2))
    ]
    projects = [
        {
            "name": f"{random.choice(['AI', 'Web', 'Mobile', 'Cloud'])} Project {i+1}",
            "description": f"A {random.choice(['cutting-edge', 'scalable', 'innovative'])} project.",
            "technologies": ["React", "Node.js", "MongoDB"],
            "url": "https://github.com/example/project",
            "duration": f"{random.randint(2, 12)} months"
        }
        for i in range(random.randint(1, 2))
    ]
    education = [
        {
            "institution": random.choice(UNIVERSITIES),
            "degree": random.choice(DEGREES),
            "field_of_study": random.choice(FIELDS_OF_STUDY),
            "start_date": str(local_fake.date_between(start_date='-15y', end_date='-10y')),
            "end_date": str(local_fake.date_between(start_date='-10y', end_date='-2y')),
            "grade": f"{random.uniform(3.0, 4.0):.2f}",
            "activities": random.choice(["Robotics Club", "Debate Team", "Coding Bootcamp"]),
            "description": "Participated in various academic and extracurricular activities."
        }
    ]
    languages = [
        {"name": random.choice(LANGUAGES), "proficiency": random.choice(PROFICIENCY_LEVELS)}
        for _ in range(random.randint(1, 2))
    ]
    awards = [
        {"title": f"{random.choice(['Best', 'Top', 'Outstanding'])} {random.choice(['Developer', 'Engineer', 'Student'])}",
         "issuer": random.choice(COMPANIES),
         "date": str(local_fake.date_between(start_date='-5y', end_date='today')),
         "description": "Awarded for exceptional performance."}
    ]
    publications = [
        {"title": f"Research on {random.choice(['AI', 'Web', 'Cloud'])}",
         "publisher": random.choice(UNIVERSITIES),
         "date": str(local_fake.date_between(start_date='-5y', end_date='today')),
         "url": "https://example.com/publication",
         "description": "Published research in a reputed journal."}
    ]
    volunteer_experience = [
        {"organization": random.choice(["Red Cross", "UNICEF", "WWF"]),
         "role": random.choice(["Volunteer", "Coordinator"]),
         "start_date": str(local_fake.date_between(start_date='-5y', end_date='-2y')),
         "end_date": str(local_fake.date_between(start_date='-2y', end_date='today')),
         "description": "Contributed to community service."}
    ]
    interests = random.sample(INTERESTS, k=3)
    contact_info = {
        "email": email,
        "phone": local_fake.phone_number(),
        "linkedin": f"https://linkedin.com/in/{username}",
        "github": f"https://github.com/{username}",
        "portfolio": f"https://{username}.portfolio.com"
    }
    profile_picture = f"https://randomuser.me/api/portraits/{random.choice(['men', 'women'])}/{random.randint(1, 99)}.jpg"
    return {
        "name": name,
        "username": username,
        "email": email,
        "hashed_password": hash_password("dummypassword123"),
        "profession": profession,
        "location": f"{local_fake.city()}, {local_fake.country()} ({locale})",
        "profile_picture": profile_picture,
        "is_looking_for_job": random.choice([True, False]),
        "experience": f"{years_exp} years",
        "summary": f"Experienced {profession.lower()} with expertise in modern technologies.",
        "skills": skills,
        "experience_details": experience_details,
        "projects": projects,
        "certifications": ["Sample Certification"],
        "contact_info": contact_info,
        "education": education,
        "languages": languages,
        "awards": awards,
        "publications": publications,
        "volunteer_experience": volunteer_experience,
        "interests": interests,
        "rating": round(random.uniform(4.0, 5.0), 1),
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

async def background_generate_users(count: int):
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    users_collection = db.users
    locales = [locale for _, locale in COUNTRIES]
    users = []
    for i in range(count):
        locale = random.choice(locales)
        user = generate_profile(locale)
        users.append(user)
        if len(users) >= 10 or i == count - 1:
            await users_collection.insert_many(users)
            users = []
    await client.close()

@router.post("/background/{count}")
async def generate_dummy_users_background(count: int = Path(..., ge=1, le=100, description="Number of users to generate"), background_tasks: BackgroundTasks = None):
    """
    Generate dummy users in the background (non-blocking, recommended for large batches)
    """
    if count < 1 or count > 100:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 100")
    background_tasks.add_task(background_generate_users, count)
    return {"success": True, "message": f"Started background task to generate {count} dummy users."} 