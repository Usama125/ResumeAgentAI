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

def calculate_profile_score(user_data: Dict[str, Any]) -> int:
    """Calculate profile score based on completeness and quality of profile data"""
    score = 0
    
    # Basic info (20 points)
    if user_data.get("name"):
        score += 5
    if user_data.get("email"):
        score += 5
    if user_data.get("profession"):
        score += 5
    if user_data.get("location"):
        score += 5
    
    # Profile completeness (30 points)
    if user_data.get("summary"):
        score += 10
    if user_data.get("profile_picture"):
        score += 5
    if user_data.get("experience"):
        score += 10
    if user_data.get("contact_info", {}).get("linkedin"):
        score += 5
    
    # Skills and experience (30 points)
    skills = user_data.get("skills", [])
    if len(skills) >= 3:
        score += 15
    elif len(skills) >= 1:
        score += 10
    
    experience_details = user_data.get("experience_details", [])
    if len(experience_details) >= 2:
        score += 15
    elif len(experience_details) >= 1:
        score += 10
    
    # Additional sections (20 points)
    projects = user_data.get("projects", [])
    if len(projects) >= 2:
        score += 10
    elif len(projects) >= 1:
        score += 5
    
    education = user_data.get("education", [])
    if len(education) >= 1:
        score += 5
    
    if user_data.get("certifications"):
        score += 5
    
    return min(score, 100)  # Cap at 100

def generate_specific_profile(profession: str, locale: str = "en_US") -> Dict[str, Any]:
    """Generate a complete profile for a specific profession"""
    local_fake = Faker(locale)
    
    # Generate profession-specific data
    if "Product Manager" in profession:
        name = local_fake.name()
        skills = [
            {"name": "Product Strategy", "level": "Expert", "years": random.randint(3, 8)},
            {"name": "User Research", "level": "Advanced", "years": random.randint(2, 6)},
            {"name": "Agile/Scrum", "level": "Expert", "years": random.randint(4, 7)},
            {"name": "Data Analysis", "level": "Advanced", "years": random.randint(3, 6)},
            {"name": "Roadmapping", "level": "Expert", "years": random.randint(3, 8)},
            {"name": "Stakeholder Management", "level": "Advanced", "years": random.randint(2, 5)}
        ]
        companies = ["Google", "Microsoft", "Amazon", "Meta", "Airbnb", "Uber", "Stripe"]
        years_exp = random.randint(5, 12)
        
    elif "UX Designer" in profession:
        name = local_fake.name()
        skills = [
            {"name": "Figma", "level": "Expert", "years": random.randint(3, 8)},
            {"name": "Sketch", "level": "Advanced", "years": random.randint(2, 6)},
            {"name": "Adobe Creative Suite", "level": "Expert", "years": random.randint(4, 9)},
            {"name": "User Research", "level": "Advanced", "years": random.randint(3, 6)},
            {"name": "Prototyping", "level": "Expert", "years": random.randint(3, 7)},
            {"name": "Wireframing", "level": "Advanced", "years": random.randint(2, 6)}
        ]
        companies = ["Apple", "Google", "Adobe", "Spotify", "Airbnb", "Netflix", "Uber"]
        years_exp = random.randint(4, 10)
        
    elif "Python Developer" in profession:
        name = local_fake.name()
        skills = [
            {"name": "Python", "level": "Expert", "years": random.randint(4, 8)},
            {"name": "Django", "level": "Advanced", "years": random.randint(3, 6)},
            {"name": "Flask", "level": "Advanced", "years": random.randint(2, 5)},
            {"name": "PostgreSQL", "level": "Advanced", "years": random.randint(3, 6)},
            {"name": "Docker", "level": "Intermediate", "years": random.randint(2, 4)},
            {"name": "AWS", "level": "Advanced", "years": random.randint(2, 5)},
            {"name": "FastAPI", "level": "Advanced", "years": random.randint(1, 4)}
        ]
        companies = ["Google", "Microsoft", "Amazon", "Netflix", "Dropbox", "Instagram", "Reddit"]
        years_exp = random.randint(3, 10)
    else:
        # Fallback
        name = local_fake.name()
        skills = [
            {"name": "Leadership", "level": "Advanced", "years": random.randint(2, 6)},
            {"name": "Communication", "level": "Expert", "years": random.randint(3, 8)}
        ]
        companies = COMPANIES
        years_exp = random.randint(2, 8)
    
    username = generate_username(name)
    email = f"{username}@example.com"
    
    # Generate detailed experience
    experience_details = []
    for i in range(random.randint(2, 3)):
        exp_years = random.randint(1, 4)
        experience_details.append({
            "company": random.choice(companies),
            "position": profession if i == 0 else f"Senior {profession}",
            "duration": f"{exp_years} years",
            "description": f"Led {random.choice(['cross-functional teams', 'product initiatives', 'design systems', 'development projects'])} to deliver high-impact solutions. Collaborated with stakeholders to drive business objectives and improve user experience.",
            "start_date": str(local_fake.date_between(start_date='-10y', end_date='-2y')),
            "end_date": str(local_fake.date_between(start_date='-2y', end_date='today')) if i > 0 else None,
            "current": i == 0,
            "technologies": [skill["name"] for skill in skills[:3]] if "Developer" in profession else []
        })
    
    # Generate projects
    projects = []
    for i in range(random.randint(2, 4)):
        if "Product Manager" in profession:
            project_name = f"{random.choice(['Mobile App', 'Web Platform', 'Analytics Dashboard', 'Customer Portal'])} {i+1}"
            tech_stack = ["React", "Node.js", "PostgreSQL", "AWS"]
        elif "UX Designer" in profession:
            project_name = f"{random.choice(['E-commerce Redesign', 'Mobile App Design', 'Design System', 'User Research'])} {i+1}"
            tech_stack = ["Figma", "Sketch", "Adobe XD", "InVision"]
        elif "Python Developer" in profession:
            project_name = f"{random.choice(['API Development', 'Data Pipeline', 'Web Application', 'Microservice'])} {i+1}"
            tech_stack = ["Python", "Django", "PostgreSQL", "Docker", "AWS"]
        else:
            project_name = f"Project {i+1}"
            tech_stack = ["Various Technologies"]
            
        projects.append({
            "name": project_name,
            "description": f"Delivered a comprehensive {project_name.lower()} that improved user engagement by {random.randint(20, 60)}% and increased business metrics.",
            "technologies": tech_stack,
            "url": f"https://github.com/{username}/{project_name.lower().replace(' ', '-')}",
            "github_url": f"https://github.com/{username}/{project_name.lower().replace(' ', '-')}",
            "duration": f"{random.randint(3, 12)} months"
        })
    
    # Base profile
    base_profile = generate_profile(locale)
    
    # Override with specific data
    profile = {
        **base_profile,
        "name": name,
        "username": username,
        "email": email,
        "profession": profession,
        "designation": profession,
        "experience": f"{years_exp} years",
        "summary": f"Experienced {profession.lower()} with {years_exp} years of expertise in delivering high-quality solutions. Proven track record of leading successful projects and driving business growth through innovative approaches.",
        "skills": skills,
        "experience_details": experience_details,
        "projects": projects,
        "education": [
            {
                "institution": random.choice(UNIVERSITIES),
                "degree": "Master of Science" if years_exp > 5 else "Bachelor of Science",
                "field_of_study": random.choice(["Computer Science", "Business Administration", "Design", "Engineering"]),
                "start_date": str(local_fake.date_between(start_date='-15y', end_date='-10y')),
                "end_date": str(local_fake.date_between(start_date='-10y', end_date='-8y')),
                "grade": f"{random.uniform(3.2, 4.0):.2f}",
                "activities": random.choice(["Tech Club President", "Design Society", "Coding Bootcamp", "Product Management Club"]),
                "description": "Focused on building strong technical and leadership foundations."
            }
        ],
        "certifications": [
            f"Certified {profession}",
            f"Advanced {random.choice(['Leadership', 'Technical Skills', 'Project Management'])}"
        ],
        "location": random.choice([
            "San Francisco, CA, US",
            "New York, NY, US", 
            "Seattle, WA, US",
            "Austin, TX, US",
            "Boston, MA, US",
            "Chicago, IL, US"
        ]),
        "rating": round(random.uniform(4.3, 5.0), 1),
        "is_looking_for_job": random.choice([True, False]),
    }
    
    # Calculate and add profile score
    profile["profile_score"] = calculate_profile_score(profile)
    
    return profile

async def create_test_profiles():
    """Create specific test profiles for search testing"""
    from app.services.algolia_service import AlgoliaService
    from app.models.user import UserInDB
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    users_collection = db.users
    algolia_service = AlgoliaService()
    
    profiles = []
    
    # Create 10 Product Managers with varying scores
    for i in range(10):
        profile = generate_specific_profile("Product Manager", "en_US")
        # Vary the profile scores between 60-100
        profile['profile_score'] = random.randint(60, 100)
        profiles.append(profile)
    
    # Create 10 UX Designers with varying scores
    for i in range(10):
        profile = generate_specific_profile("UX Designer", "en_US")
        # Vary the profile scores between 65-100
        profile['profile_score'] = random.randint(65, 100)
        profiles.append(profile)
    
    # Create 10 Python Developers with varying scores
    for i in range(10):
        profile = generate_specific_profile("Python Developer", "en_US")
        # Vary the profile scores between 70-100
        profile['profile_score'] = random.randint(70, 100)
        profiles.append(profile)
    
    # Insert all profiles to database
    if profiles:
        result = await users_collection.insert_many(profiles)
        print(f"✅ Inserted {len(result.inserted_ids)} profiles to database")
        
        # Now sync each profile to Algolia
        synced_count = 0
        for i, profile in enumerate(profiles):
            try:
                # Convert to UserInDB and sync to Algolia
                profile['id'] = str(result.inserted_ids[i])
                user = UserInDB(**profile)
                success = await algolia_service.sync_user_to_algolia(user)
                if success:
                    synced_count += 1
                    print(f"✅ Synced profile {i+1}/{len(profiles)} to Algolia")
                else:
                    print(f"❌ Failed to sync profile {i+1}/{len(profiles)} to Algolia")
            except Exception as e:
                print(f"❌ Error syncing profile {i+1}/{len(profiles)}: {str(e)}")
        
        print(f"📊 Final Summary:")
        print(f"  🗄️  Database: {len(result.inserted_ids)} profiles")
        print(f"  🔍 Algolia: {synced_count} profiles")
    
    await client.close()
    return len(profiles)

@router.post("/test-profiles")
async def create_test_search_profiles(background_tasks: BackgroundTasks):
    """
    Create specific test profiles for search functionality testing:
    - 10 Product Managers (scores 60-100)
    - 10 UX Designers (scores 65-100)
    - 10 Python Developers (scores 70-100)
    All with complete profile data and varying profile_scores for testing pagination and search
    """
    background_tasks.add_task(create_test_profiles)
    return {
        "success": True, 
        "message": "Creating test profiles: 10 Product Managers, 10 UX Designers, 10 Python Developers with complete profile data, varying profile scores, and automatic Algolia sync"
    } 