from fastapi import APIRouter, HTTPException, Depends, status, Request, UploadFile, File
from typing import List
from app.models.user import UserResponse, UserUpdate, PublicUserResponse
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.file_service import FileService
from app.routers.auth import get_current_user
from app.database import get_database
from app.middleware.debug_rate_limiting import debug_rate_limit_job_matching

router = APIRouter()
user_service = UserService()
auth_service = AuthService()
file_service = FileService()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user's profile"""
    return UserResponse(**current_user.dict())

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user = Depends(get_current_user)
):
    """Update current user's profile"""
    # Check if user has completed onboarding progress before allowing profile updates
    # Allow updates if all onboarding steps are completed OR if onboarding_completed flag is True
    onboarding_truly_completed = (
        current_user.onboarding_completed or 
        (current_user.onboarding_progress and current_user.onboarding_progress.completed)
    )
    
    if not onboarding_truly_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete onboarding first before updating profile"
        )
    
    # If onboarding progress shows completed but flag is False, fix it
    if (current_user.onboarding_progress and 
        current_user.onboarding_progress.completed and 
        not current_user.onboarding_completed):
        update_data.onboarding_completed = True
    
    updated_user = await user_service.update_user(str(current_user.id), update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    return UserResponse(**updated_user.dict())

@router.put("/me/sections/{section_name}", response_model=UserResponse)
async def update_profile_section(
    section_name: str,
    update_data: dict,
    current_user = Depends(get_current_user)
):
    """Update a specific section of the user's profile"""
    # Check if user has completed onboarding progress before allowing profile updates
    onboarding_truly_completed = (
        current_user.onboarding_completed or 
        (current_user.onboarding_progress and current_user.onboarding_progress.completed)
    )
    
    if not onboarding_truly_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete onboarding first before updating profile"
        )
    
    # Validate section name and prepare update data
    valid_sections = {
        "about": ["summary"],
        "experience": ["experience_details"],
        "skills": ["skills"],
        "projects": ["projects"],
        "education": ["education"],
        "contact": ["contact_info"],
        "languages": ["languages"],
        "awards": ["awards"],
        "publications": ["publications"],
        "volunteer": ["volunteer_experience"],
        "interests": ["interests"]
    }
    
    if section_name not in valid_sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid section name. Valid sections: {list(valid_sections.keys())}"
        )
    
    # Create UserUpdate object with only the specified section
    update_dict = {}
    for field in valid_sections[section_name]:
        if field in update_data:
            update_dict[field] = update_data[field]
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid data provided for this section"
        )
    
    # If onboarding progress shows completed but flag is False, fix it
    if (current_user.onboarding_progress and 
        current_user.onboarding_progress.completed and 
        not current_user.onboarding_completed):
        update_dict["onboarding_completed"] = True
    
    update_user_data = UserUpdate(**update_dict)
    updated_user = await user_service.update_user(str(current_user.id), update_user_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile section"
        )
    
    return UserResponse(**updated_user.dict())

@router.put("/me/sections/reorder", response_model=UserResponse)
async def reorder_sections(
    section_order: List[str],
    current_user = Depends(get_current_user)
):
    """Reorder profile sections based on provided section IDs order"""
    # Check if user has completed onboarding progress before allowing profile updates
    onboarding_truly_completed = (
        current_user.onboarding_completed or 
        (current_user.onboarding_progress and current_user.onboarding_progress.completed)
    )
    
    if not onboarding_truly_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete onboarding first before updating profile"
        )
    
    # Validate section IDs
    valid_sections = [
        "about", "contact", "experience", "skills", "education", 
        "projects", "awards", "languages", "publications", "volunteer", "interests"
    ]
    
    for section_id in section_order:
        if section_id not in valid_sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid section ID: {section_id}. Valid sections: {valid_sections}"
            )
    
    # If onboarding progress shows completed but flag is False, fix it
    update_dict = {"section_order": section_order}
    if (current_user.onboarding_progress and 
        current_user.onboarding_progress.completed and 
        not current_user.onboarding_completed):
        update_dict["onboarding_completed"] = True
    
    update_user_data = UserUpdate(**update_dict)
    updated_user = await user_service.update_user(str(current_user.id), update_user_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder sections"
        )
    
    return UserResponse(**updated_user.dict())

@router.put("/me/skills/reorder", response_model=UserResponse)
async def reorder_skills(
    skill_ids: List[str],
    current_user = Depends(get_current_user)
):
    """Reorder skills based on provided skill IDs order"""
    # Check if user has completed onboarding progress before allowing profile updates
    onboarding_truly_completed = (
        current_user.onboarding_completed or 
        (current_user.onboarding_progress and current_user.onboarding_progress.completed)
    )
    
    if not onboarding_truly_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete onboarding first before updating profile"
        )
    
    if not current_user.skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No skills to reorder"
        )
    
    # Create a map of skill IDs to skills for easy lookup
    skills_map = {}
    for i, skill in enumerate(current_user.skills):
        skill_id = skill.id if skill.id else f"skill-{i}"
        skills_map[skill_id] = skill
    
    # Reorder skills based on the provided skill IDs
    reordered_skills = []
    for skill_id in skill_ids:
        if skill_id in skills_map:
            reordered_skills.append(skills_map[skill_id])
    
    # Add any remaining skills that weren't in the skill_ids list
    for i, skill in enumerate(current_user.skills):
        skill_id = skill.id if skill.id else f"skill-{i}"
        if skill_id not in skill_ids:
            reordered_skills.append(skill)
    
    # If onboarding progress shows completed but flag is False, fix it
    update_dict = {"skills": reordered_skills}
    if (current_user.onboarding_progress and 
        current_user.onboarding_progress.completed and 
        not current_user.onboarding_completed):
        update_dict["onboarding_completed"] = True
    
    update_user_data = UserUpdate(**update_dict)
    updated_user = await user_service.update_user(str(current_user.id), update_user_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder skills"
        )
    
    return UserResponse(**updated_user.dict())

@router.get("/{user_id}", response_model=PublicUserResponse)
async def get_user_profile(user_id: str):
    """Get public user profile"""
    user = await user_service.get_public_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.get("/username/{username}", response_model=PublicUserResponse)
async def get_user_profile_by_username(username: str):
    """Get public user profile by username"""
    user = await auth_service.get_user_by_username(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert to public user response
    public_user = await user_service.get_public_user(str(user.id))
    if not public_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return public_user

@router.post("/me/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload or update profile picture"""
    try:
        # Upload to S3
        profile_picture_url = await file_service.save_profile_picture(file, current_user.username)
        
        # Update user profile with new picture URL
        update_data = UserUpdate(profile_picture=profile_picture_url)
        updated_user = await user_service.update_user(str(current_user.id), update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile picture"
            )
        
        return {
            "success": True,
            "message": "Profile picture updated successfully",
            "profile_picture_url": profile_picture_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )

@router.delete("/me/profile-picture")
async def delete_profile_picture(current_user = Depends(get_current_user)):
    """Delete profile picture"""
    try:
        # Delete from S3
        deleted = await file_service.delete_profile_picture(current_user.username)
        
        if deleted:
            # Update user profile to remove picture URL
            update_data = UserUpdate(profile_picture=None)
            updated_user = await user_service.update_user(str(current_user.id), update_data)
            
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user profile"
                )
        
        return {
            "success": True,
            "message": "Profile picture deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile picture: {str(e)}"
        )

@router.get("/", response_model=List[PublicUserResponse])
async def get_featured_users(limit: int = 12, skip: int = 0):
    """Get featured users for homepage"""
    users = await user_service.get_featured_users(limit, skip)
    return users

@router.delete("/admin/clear-all")
async def clear_all_users(db = Depends(get_database)):
    """
    ADMIN ONLY: Delete all users from database for testing purposes
    WARNING: This will permanently delete ALL user data!
    """
    try:
        # Delete all users
        result = await db.users.delete_many({})
        
        return {
            "message": f"Successfully deleted {result.deleted_count} users",
            "deleted_count": result.deleted_count,
            "success": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete users: {str(e)}"
        )

@router.post("/admin/create-dummy-users")
async def create_dummy_users(db = Depends(get_database)):
    """
    ADMIN ONLY: Create realistic dummy users for testing
    """
    from app.utils.security import get_password_hash
    from datetime import datetime
    from app.models.user import OnboardingProgress, OnboardingStepStatus, WorkPreferences
    
    dummy_users = [
        {
            "email": "sarah.johnson@email.com",
            "password": "Password123!",
            "name": "Sarah Johnson",
            "designation": "Senior Software Engineer",
            "location": "San Francisco, CA",
            "is_looking_for_job": True,
            "expected_salary": "$140,000 - $160,000",
            "current_salary": "$125,000",
            "experience": "7 years",
            "summary": "Experienced full-stack developer with expertise in React, Node.js, and cloud technologies. Passionate about building scalable web applications and leading development teams.",
            "skills": [
                {"name": "React", "level": "Expert", "years": 5},
                {"name": "Node.js", "level": "Expert", "years": 6},
                {"name": "TypeScript", "level": "Advanced", "years": 4},
                {"name": "AWS", "level": "Advanced", "years": 3},
                {"name": "MongoDB", "level": "Advanced", "years": 4},
                {"name": "Docker", "level": "Intermediate", "years": 2}
            ],
            "experience_details": [
                {
                    "company": "TechCorp Solutions",
                    "position": "Senior Software Engineer",
                    "duration": "Jan 2021 - Present",
                    "description": "Lead development of microservices architecture, mentor junior developers, and implement CI/CD pipelines."
                },
                {
                    "company": "StartupXYZ",
                    "position": "Full Stack Developer",
                    "duration": "Mar 2019 - Dec 2020",
                    "description": "Built customer-facing web applications using React and Node.js, integrated payment systems and APIs."
                },
                {
                    "company": "WebDev Agency",
                    "position": "Frontend Developer",
                    "duration": "Jun 2017 - Feb 2019",
                    "description": "Developed responsive websites and web applications for various clients using modern JavaScript frameworks."
                }
            ],
            "projects": [
                {
                    "name": "E-commerce Platform",
                    "description": "Built a scalable e-commerce platform handling 10K+ daily transactions",
                    "technologies": ["React", "Node.js", "PostgreSQL", "Redis"],
                    "duration": "6 months"
                },
                {
                    "name": "Real-time Chat Application",
                    "description": "Developed a real-time messaging app with video calls and file sharing",
                    "technologies": ["React", "Socket.io", "WebRTC", "MongoDB"],
                    "duration": "3 months"
                }
            ],
            "certifications": ["AWS Certified Developer", "React Professional Certification"]
        },
        {
            "email": "michael.chen@email.com",
            "password": "Password123!",
            "name": "Michael Chen",
            "designation": "DevOps Engineer",
            "location": "Seattle, WA",
            "is_looking_for_job": False,
            "expected_salary": "$130,000 - $150,000",
            "current_salary": "$135,000",
            "experience": "5 years",
            "summary": "DevOps engineer specializing in cloud infrastructure, automation, and CI/CD pipelines. Experience with Kubernetes, Terraform, and multi-cloud deployments.",
            "skills": [
                {"name": "Kubernetes", "level": "Expert", "years": 4},
                {"name": "AWS", "level": "Expert", "years": 5},
                {"name": "Terraform", "level": "Advanced", "years": 3},
                {"name": "Docker", "level": "Expert", "years": 4},
                {"name": "Python", "level": "Advanced", "years": 4},
                {"name": "Jenkins", "level": "Advanced", "years": 3}
            ],
            "experience_details": [
                {
                    "company": "CloudTech Inc",
                    "position": "Senior DevOps Engineer",
                    "duration": "Aug 2021 - Present",
                    "description": "Manage multi-cloud infrastructure, implement monitoring solutions, and optimize deployment pipelines."
                },
                {
                    "company": "DataFlow Systems",
                    "position": "DevOps Engineer",
                    "duration": "Jan 2020 - Jul 2021",
                    "description": "Automated deployment processes, managed AWS infrastructure, and implemented security best practices."
                },
                {
                    "company": "TechStart Solutions",
                    "position": "Junior DevOps Engineer",
                    "duration": "Sep 2019 - Dec 2019",
                    "description": "Supported CI/CD pipeline development and assisted with cloud migration projects."
                }
            ],
            "projects": [
                {
                    "name": "Multi-Cloud Migration",
                    "description": "Led migration of legacy applications to hybrid AWS-Azure environment",
                    "technologies": ["AWS", "Azure", "Terraform", "Kubernetes"],
                    "duration": "8 months"
                }
            ],
            "certifications": ["AWS Solutions Architect", "Certified Kubernetes Administrator"]
        },
        {
            "email": "emma.rodriguez@email.com",
            "password": "Password123!",
            "name": "Emma Rodriguez",
            "designation": "UX/UI Designer",
            "location": "New York, NY",
            "is_looking_for_job": True,
            "expected_salary": "$90,000 - $110,000",
            "current_salary": "$85,000",
            "experience": "4 years",
            "summary": "Creative UX/UI designer with a passion for user-centered design and accessibility. Experienced in design systems, prototyping, and user research.",
            "skills": [
                {"name": "Figma", "level": "Expert", "years": 4},
                {"name": "Adobe Creative Suite", "level": "Advanced", "years": 5},
                {"name": "Prototyping", "level": "Advanced", "years": 4},
                {"name": "User Research", "level": "Advanced", "years": 3},
                {"name": "HTML/CSS", "level": "Intermediate", "years": 3}
            ],
            "experience_details": [
                {
                    "company": "Design Studios Pro",
                    "position": "Senior UX Designer",
                    "duration": "May 2022 - Present",
                    "description": "Lead design for mobile and web applications, conduct user research, and maintain design systems."
                },
                {
                    "company": "Creative Agency NYC",
                    "position": "UX/UI Designer",
                    "duration": "Aug 2020 - Apr 2022",
                    "description": "Designed user interfaces for various client projects, created wireframes and prototypes."
                }
            ],
            "projects": [
                {
                    "name": "Mobile Banking App Redesign",
                    "description": "Redesigned mobile banking app improving user satisfaction by 40%",
                    "technologies": ["Figma", "Principle", "User Testing"],
                    "duration": "4 months"
                }
            ],
            "certifications": ["Google UX Design Certificate"]
        },
        {
            "email": "david.kim@email.com",
            "password": "Password123!",
            "name": "David Kim",
            "designation": "Data Scientist",
            "location": "Austin, TX",
            "is_looking_for_job": True,
            "expected_salary": "$120,000 - $140,000",
            "current_salary": "$105,000",
            "experience": "6 years",
            "summary": "Data scientist with expertise in machine learning, statistical analysis, and big data technologies. Experienced in building predictive models and data pipelines.",
            "skills": [
                {"name": "Python", "level": "Expert", "years": 6},
                {"name": "Machine Learning", "level": "Expert", "years": 5},
                {"name": "SQL", "level": "Expert", "years": 6},
                {"name": "TensorFlow", "level": "Advanced", "years": 4},
                {"name": "Apache Spark", "level": "Advanced", "years": 3},
                {"name": "R", "level": "Intermediate", "years": 3}
            ],
            "experience_details": [
                {
                    "company": "AI Innovations Corp",
                    "position": "Senior Data Scientist",
                    "duration": "Feb 2021 - Present",
                    "description": "Develop machine learning models for customer segmentation and recommendation systems."
                },
                {
                    "company": "Analytics Plus",
                    "position": "Data Scientist",
                    "duration": "Jun 2019 - Jan 2021",
                    "description": "Built predictive models for business intelligence and automated reporting systems."
                },
                {
                    "company": "Data Insights LLC",
                    "position": "Junior Data Analyst",
                    "duration": "Sep 2018 - May 2019",
                    "description": "Performed statistical analysis and created data visualizations for business stakeholders."
                }
            ],
            "projects": [
                {
                    "name": "Customer Churn Prediction",
                    "description": "Built ML model reducing customer churn by 25%",
                    "technologies": ["Python", "Scikit-learn", "PostgreSQL"],
                    "duration": "3 months"
                }
            ],
            "certifications": ["AWS Machine Learning Specialty", "Google Data Analytics Certificate"]
        },
        {
            "email": "jessica.martinez@email.com",
            "password": "Password123!",
            "name": "Jessica Martinez",
            "designation": "Product Manager",
            "location": "Los Angeles, CA",
            "is_looking_for_job": False,
            "expected_salary": "$130,000 - $150,000",
            "current_salary": "$140,000",
            "experience": "8 years",
            "summary": "Strategic product manager with experience leading cross-functional teams and launching successful digital products. Expert in agile methodologies and user-centric product development.",
            "skills": [
                {"name": "Product Strategy", "level": "Expert", "years": 7},
                {"name": "Agile/Scrum", "level": "Expert", "years": 8},
                {"name": "User Research", "level": "Advanced", "years": 6},
                {"name": "Data Analysis", "level": "Advanced", "years": 5},
                {"name": "Roadmap Planning", "level": "Expert", "years": 7}
            ],
            "experience_details": [
                {
                    "company": "ProductTech Solutions",
                    "position": "Senior Product Manager",
                    "duration": "Mar 2020 - Present",
                    "description": "Lead product strategy for B2B SaaS platform, manage product roadmap, and coordinate with engineering teams."
                },
                {
                    "company": "InnovateCorp",
                    "position": "Product Manager",
                    "duration": "Jul 2018 - Feb 2020",
                    "description": "Managed product lifecycle for mobile applications, conducted market research, and defined product requirements."
                },
                {
                    "company": "StartupFlow",
                    "position": "Associate Product Manager",
                    "duration": "Jan 2016 - Jun 2018",
                    "description": "Supported product development initiatives and collaborated with design and engineering teams."
                }
            ],
            "projects": [
                {
                    "name": "SaaS Platform Launch",
                    "description": "Successfully launched B2B platform reaching 10,000+ users in first year",
                    "technologies": ["Jira", "Confluence", "Analytics"],
                    "duration": "12 months"
                }
            ],
            "certifications": ["Certified Scrum Product Owner", "Google Analytics Certified"]
        },
        {
            "email": "alex.thompson@email.com",
            "password": "Password123!",
            "name": "Alex Thompson",
            "designation": "Backend Developer",
            "location": "Denver, CO",
            "is_looking_for_job": True,
            "expected_salary": "$110,000 - $130,000",
            "current_salary": "$95,000",
            "experience": "4 years",
            "summary": "Backend developer specializing in API development, database design, and microservices architecture. Passionate about building robust and scalable server-side applications.",
            "skills": [
                {"name": "Java", "level": "Expert", "years": 4},
                {"name": "Spring Boot", "level": "Advanced", "years": 3},
                {"name": "PostgreSQL", "level": "Advanced", "years": 4},
                {"name": "REST APIs", "level": "Expert", "years": 4},
                {"name": "Microservices", "level": "Advanced", "years": 2},
                {"name": "Redis", "level": "Intermediate", "years": 2}
            ],
            "experience_details": [
                {
                    "company": "ServerTech Inc",
                    "position": "Backend Developer",
                    "duration": "Jan 2021 - Present",
                    "description": "Develop and maintain REST APIs, optimize database queries, and implement caching strategies."
                },
                {
                    "company": "CodeCraft Solutions",
                    "position": "Junior Backend Developer",
                    "duration": "Aug 2020 - Dec 2020",
                    "description": "Built backend services for web applications and integrated third-party APIs."
                }
            ],
            "projects": [
                {
                    "name": "Payment Processing API",
                    "description": "Built secure payment processing system handling $1M+ monthly transactions",
                    "technologies": ["Java", "Spring Boot", "PostgreSQL", "Redis"],
                    "duration": "4 months"
                }
            ],
            "certifications": ["Oracle Java SE Certification"]
        },
        {
            "email": "maria.garcia@email.com",
            "password": "Password123!",
            "name": "Maria Garcia",
            "designation": "Frontend Developer",
            "location": "Miami, FL",
            "is_looking_for_job": True,
            "expected_salary": "$85,000 - $105,000",
            "current_salary": "$80,000",
            "experience": "3 years",
            "summary": "Frontend developer with strong skills in modern JavaScript frameworks and responsive design. Focused on creating beautiful and performant user interfaces.",
            "skills": [
                {"name": "React", "level": "Advanced", "years": 3},
                {"name": "JavaScript", "level": "Advanced", "years": 4},
                {"name": "CSS/SCSS", "level": "Expert", "years": 4},
                {"name": "Vue.js", "level": "Intermediate", "years": 2},
                {"name": "Webpack", "level": "Intermediate", "years": 2}
            ],
            "experience_details": [
                {
                    "company": "WebSolutions Pro",
                    "position": "Frontend Developer",
                    "duration": "Jun 2021 - Present",
                    "description": "Develop responsive web applications, implement design systems, and optimize performance."
                },
                {
                    "company": "Digital Creative Studio",
                    "position": "Junior Frontend Developer",
                    "duration": "Mar 2021 - May 2021",
                    "description": "Created interactive websites and collaborated with design teams on UI implementation."
                }
            ],
            "projects": [
                {
                    "name": "E-learning Platform Frontend",
                    "description": "Built interactive frontend for online learning platform with 5,000+ students",
                    "technologies": ["React", "TypeScript", "Material-UI"],
                    "duration": "5 months"
                }
            ],
            "certifications": ["Meta Frontend Developer Certificate"]
        },
        {
            "email": "robert.wilson@email.com",
            "password": "Password123!",
            "name": "Robert Wilson",
            "designation": "Mobile App Developer",
            "location": "Chicago, IL",
            "is_looking_for_job": False,
            "expected_salary": "$100,000 - $120,000",
            "current_salary": "$110,000",
            "experience": "5 years",
            "summary": "Mobile app developer with expertise in both iOS and Android development. Experienced in React Native, Swift, and Kotlin for building cross-platform and native applications.",
            "skills": [
                {"name": "React Native", "level": "Expert", "years": 4},
                {"name": "Swift", "level": "Advanced", "years": 3},
                {"name": "Kotlin", "level": "Advanced", "years": 3},
                {"name": "iOS Development", "level": "Advanced", "years": 4},
                {"name": "Android Development", "level": "Advanced", "years": 4}
            ],
            "experience_details": [
                {
                    "company": "MobileFirst Technologies",
                    "position": "Senior Mobile Developer",
                    "duration": "Apr 2020 - Present",
                    "description": "Lead mobile app development team, architect cross-platform solutions, and mentor junior developers."
                },
                {
                    "company": "AppDev Studios",
                    "position": "Mobile Developer",
                    "duration": "Jul 2019 - Mar 2020",
                    "description": "Developed native iOS and Android applications for various client projects."
                }
            ],
            "projects": [
                {
                    "name": "Fitness Tracking App",
                    "description": "Cross-platform fitness app with 50,000+ downloads and 4.8 App Store rating",
                    "technologies": ["React Native", "Firebase", "Redux"],
                    "duration": "6 months"
                }
            ],
            "certifications": ["iOS App Development with Swift"]
        },
        {
            "email": "lisa.anderson@email.com",
            "password": "Password123!",
            "name": "Lisa Anderson",
            "designation": "QA Engineer",
            "location": "Boston, MA",
            "is_looking_for_job": True,
            "expected_salary": "$80,000 - $100,000",
            "current_salary": "$75,000",
            "experience": "4 years",
            "summary": "Quality assurance engineer with expertise in automated testing, test strategy development, and bug tracking. Passionate about ensuring software quality and user satisfaction.",
            "skills": [
                {"name": "Automated Testing", "level": "Advanced", "years": 3},
                {"name": "Selenium", "level": "Advanced", "years": 3},
                {"name": "API Testing", "level": "Advanced", "years": 4},
                {"name": "Test Planning", "level": "Expert", "years": 4},
                {"name": "Cypress", "level": "Intermediate", "years": 2}
            ],
            "experience_details": [
                {
                    "company": "QualityFirst Solutions",
                    "position": "Senior QA Engineer",
                    "duration": "Sep 2021 - Present",
                    "description": "Design test strategies, implement automated test suites, and lead quality assurance processes."
                },
                {
                    "company": "TestPro Agency",
                    "position": "QA Engineer",
                    "duration": "Feb 2020 - Aug 2021",
                    "description": "Performed manual and automated testing for web and mobile applications."
                }
            ],
            "projects": [
                {
                    "name": "Test Automation Framework",
                    "description": "Built comprehensive test automation framework reducing testing time by 60%",
                    "technologies": ["Selenium", "TestNG", "Maven"],
                    "duration": "3 months"
                }
            ],
            "certifications": ["ISTQB Foundation Level"]
        },
        {
            "email": "james.brown@email.com",
            "password": "Password123!",
            "name": "James Brown",
            "designation": "Cybersecurity Analyst",
            "location": "Washington, DC",
            "is_looking_for_job": False,
            "expected_salary": "$110,000 - $130,000",
            "current_salary": "$115,000",
            "experience": "6 years",
            "summary": "Cybersecurity analyst specializing in threat detection, incident response, and security architecture. Experienced in implementing security frameworks and conducting risk assessments.",
            "skills": [
                {"name": "Penetration Testing", "level": "Expert", "years": 5},
                {"name": "SIEM", "level": "Advanced", "years": 4},
                {"name": "Incident Response", "level": "Expert", "years": 6},
                {"name": "Risk Assessment", "level": "Advanced", "years": 5},
                {"name": "Network Security", "level": "Expert", "years": 6}
            ],
            "experience_details": [
                {
                    "company": "SecureNet Consulting",
                    "position": "Senior Cybersecurity Analyst",
                    "duration": "Jan 2020 - Present",
                    "description": "Lead security assessments, develop security policies, and respond to security incidents."
                },
                {
                    "company": "CyberGuard Solutions",
                    "position": "Cybersecurity Analyst",
                    "duration": "Jun 2018 - Dec 2019",
                    "description": "Monitored security events, conducted vulnerability assessments, and implemented security controls."
                }
            ],
            "projects": [
                {
                    "name": "Security Framework Implementation",
                    "description": "Implemented enterprise security framework reducing security incidents by 70%",
                    "technologies": ["NIST Framework", "Splunk", "Wireshark"],
                    "duration": "8 months"
                }
            ],
            "certifications": ["CISSP", "CEH", "Security+"]
        },
        {
            "email": "ahmed.hassan@gmail.com",
            "password": "Password123!",
            "name": "Ahmed Hassan",
            "designation": "Senior Full Stack Developer",
            "location": "Karachi, Pakistan",
            "is_looking_for_job": True,
            "expected_salary": "$80,000 - $100,000",
            "current_salary": "$75,000",
            "experience": "6 years",
            "summary": "Experienced full-stack developer from Pakistan with expertise in MERN stack and cloud technologies. Strong background in building scalable web applications for international clients.",
            "skills": [
                {"name": "React", "level": "Expert", "years": 5},
                {"name": "Node.js", "level": "Expert", "years": 6},
                {"name": "MongoDB", "level": "Advanced", "years": 4},
                {"name": "Express.js", "level": "Expert", "years": 5},
                {"name": "AWS", "level": "Advanced", "years": 3},
                {"name": "TypeScript", "level": "Advanced", "years": 3}
            ],
            "experience_details": [
                {
                    "company": "TechLogix Pakistan",
                    "position": "Senior Full Stack Developer",
                    "duration": "Jun 2021 - Present",
                    "description": "Lead development team for international clients, architected microservices solutions, and mentored junior developers."
                },
                {
                    "company": "Systems Limited",
                    "position": "Full Stack Developer",
                    "duration": "Aug 2019 - May 2021",
                    "description": "Developed enterprise web applications using MERN stack, integrated payment gateways, and optimized application performance."
                },
                {
                    "company": "Netsol Technologies",
                    "position": "Software Developer",
                    "duration": "Jan 2018 - Jul 2019",
                    "description": "Built responsive web applications and RESTful APIs for automotive finance solutions."
                }
            ],
            "projects": [
                {
                    "name": "E-commerce Marketplace",
                    "description": "Built multi-vendor e-commerce platform serving 50,000+ users across Pakistan",
                    "technologies": ["React", "Node.js", "MongoDB", "Stripe"],
                    "duration": "8 months"
                },
                {
                    "name": "Digital Banking Solution",
                    "description": "Developed secure banking web application with real-time transactions",
                    "technologies": ["React", "Express.js", "PostgreSQL", "Redis"],
                    "duration": "6 months"
                }
            ],
            "certifications": ["AWS Certified Developer", "MongoDB Professional"]
        },
        {
            "email": "fatima.ali@outlook.com",
            "password": "Password123!",
            "name": "Fatima Ali",
            "designation": "UI/UX Designer",
            "location": "Lahore, Pakistan",
            "is_looking_for_job": True,
            "expected_salary": "$60,000 - $80,000",
            "current_salary": "$55,000",
            "experience": "4 years",
            "summary": "Creative UI/UX designer passionate about creating intuitive digital experiences. Specialized in mobile-first design and user research with experience in both local and international projects.",
            "skills": [
                {"name": "Figma", "level": "Expert", "years": 4},
                {"name": "Adobe XD", "level": "Advanced", "years": 4},
                {"name": "Photoshop", "level": "Advanced", "years": 5},
                {"name": "User Research", "level": "Advanced", "years": 3},
                {"name": "Prototyping", "level": "Expert", "years": 4},
                {"name": "Wireframing", "level": "Expert", "years": 4}
            ],
            "experience_details": [
                {
                    "company": "Techlogix Digital",
                    "position": "Senior UI/UX Designer",
                    "duration": "Mar 2022 - Present",
                    "description": "Lead design for mobile and web applications, conduct user research, and collaborate with international clients."
                },
                {
                    "company": "Arbisoft",
                    "position": "UI/UX Designer",
                    "duration": "Sep 2020 - Feb 2022",
                    "description": "Designed user interfaces for EdTech platforms, created design systems, and improved user engagement by 35%."
                },
                {
                    "company": "VentureDive",
                    "position": "Junior UI Designer",
                    "duration": "Jun 2020 - Aug 2020",
                    "description": "Created wireframes and visual designs for mobile applications and web platforms."
                }
            ],
            "projects": [
                {
                    "name": "Educational App Redesign",
                    "description": "Redesigned mobile learning app increasing user retention by 45%",
                    "technologies": ["Figma", "Principle", "InVision"],
                    "duration": "3 months"
                },
                {
                    "name": "E-commerce Mobile App",
                    "description": "Designed complete mobile shopping experience with 4.7 app store rating",
                    "technologies": ["Figma", "Sketch", "Zeplin"],
                    "duration": "4 months"
                }
            ],
            "certifications": ["Google UX Design Certificate", "Adobe Certified Expert"]
        },
        {
            "email": "muhammad.shahid@yahoo.com",
            "password": "Password123!",
            "name": "Muhammad Shahid",
            "designation": "DevOps Engineer",
            "location": "Islamabad, Pakistan",
            "is_looking_for_job": False,
            "expected_salary": "$90,000 - $110,000",
            "current_salary": "$95,000",
            "experience": "5 years",
            "summary": "DevOps engineer with strong expertise in cloud infrastructure and automation. Experienced in deploying scalable applications and managing CI/CD pipelines for remote international teams.",
            "skills": [
                {"name": "AWS", "level": "Expert", "years": 5},
                {"name": "Docker", "level": "Expert", "years": 4},
                {"name": "Kubernetes", "level": "Advanced", "years": 3},
                {"name": "Jenkins", "level": "Advanced", "years": 4},
                {"name": "Terraform", "level": "Advanced", "years": 3},
                {"name": "Python", "level": "Advanced", "years": 4}
            ],
            "experience_details": [
                {
                    "company": "10Pearls",
                    "position": "Senior DevOps Engineer",
                    "duration": "Jan 2021 - Present",
                    "description": "Manage cloud infrastructure for US clients, implement CI/CD pipelines, and lead DevOps best practices adoption."
                },
                {
                    "company": "Invozone",
                    "position": "DevOps Engineer",
                    "duration": "Jul 2019 - Dec 2020",
                    "description": "Automated deployment processes, managed AWS infrastructure, and reduced deployment time by 60%."
                },
                {
                    "company": "TkXel",
                    "position": "Junior DevOps Engineer",
                    "duration": "May 2019 - Jun 2019",
                    "description": "Assisted with cloud migrations and infrastructure monitoring setup."
                }
            ],
            "projects": [
                {
                    "name": "Multi-Region AWS Migration",
                    "description": "Led migration of legacy applications to AWS across multiple regions",
                    "technologies": ["AWS", "Terraform", "Docker", "Kubernetes"],
                    "duration": "10 months"
                }
            ],
            "certifications": ["AWS Solutions Architect", "Docker Certified Associate"]
        },
        {
            "email": "ayesha.khan@hotmail.com",
            "password": "Password123!",
            "name": "Ayesha Khan",
            "designation": "Data Scientist",
            "location": "Karachi, Pakistan",
            "is_looking_for_job": True,
            "expected_salary": "$70,000 - $90,000",
            "current_salary": "$65,000",
            "experience": "4 years",
            "summary": "Data scientist with expertise in machine learning and statistical analysis. Passionate about extracting insights from data to drive business decisions in fintech and e-commerce domains.",
            "skills": [
                {"name": "Python", "level": "Expert", "years": 4},
                {"name": "Machine Learning", "level": "Advanced", "years": 4},
                {"name": "pandas", "level": "Expert", "years": 4},
                {"name": "TensorFlow", "level": "Advanced", "years": 3},
                {"name": "SQL", "level": "Expert", "years": 4},
                {"name": "Tableau", "level": "Advanced", "years": 3}
            ],
            "experience_details": [
                {
                    "company": "Tez Financial Services",
                    "position": "Data Scientist",
                    "duration": "Feb 2021 - Present",
                    "description": "Build ML models for fraud detection and risk assessment, analyze customer behavior patterns, and create dashboards for business insights."
                },
                {
                    "company": "Careem",
                    "position": "Data Analyst",
                    "duration": "Aug 2020 - Jan 2021",
                    "description": "Analyzed ride patterns and customer data, created predictive models for demand forecasting, and optimized pricing strategies."
                },
                {
                    "company": "Oraan",
                    "position": "Junior Data Analyst",
                    "duration": "Jun 2020 - Jul 2020",
                    "description": "Performed statistical analysis on financial data and created reports for business stakeholders."
                }
            ],
            "projects": [
                {
                    "name": "Fraud Detection System",
                    "description": "Built ML model detecting fraudulent transactions with 95% accuracy",
                    "technologies": ["Python", "Scikit-learn", "PostgreSQL"],
                    "duration": "4 months"
                }
            ],
            "certifications": ["Google Data Analytics Certificate", "IBM Data Science Professional"]
        },
        {
            "email": "omar.rashid@live.com",
            "password": "Password123!",
            "name": "Omar Rashid",
            "designation": "Mobile App Developer",
            "location": "Lahore, Pakistan",
            "is_looking_for_job": False,
            "expected_salary": "$75,000 - $95,000",
            "current_salary": "$85,000",
            "experience": "5 years",
            "summary": "Mobile app developer specializing in React Native and Flutter. Experienced in building high-performance mobile applications for both iOS and Android platforms serving international markets.",
            "skills": [
                {"name": "React Native", "level": "Expert", "years": 4},
                {"name": "Flutter", "level": "Advanced", "years": 3},
                {"name": "JavaScript", "level": "Expert", "years": 5},
                {"name": "Dart", "level": "Advanced", "years": 3},
                {"name": "Firebase", "level": "Advanced", "years": 4},
                {"name": "Redux", "level": "Advanced", "years": 4}
            ],
            "experience_details": [
                {
                    "company": "Cubix",
                    "position": "Senior Mobile Developer",
                    "duration": "May 2021 - Present",
                    "description": "Lead mobile development for international clients, architect cross-platform solutions, and optimize app performance."
                },
                {
                    "company": "Ropstam Solutions",
                    "position": "Mobile Developer",
                    "duration": "Jan 2020 - Apr 2021",
                    "description": "Developed React Native applications for e-commerce and social platforms, integrated payment systems and push notifications."
                },
                {
                    "company": "Nextbridge",
                    "position": "Junior Mobile Developer",
                    "duration": "Sep 2019 - Dec 2019",
                    "description": "Built mobile apps using React Native and assisted with app store submissions and maintenance."
                }
            ],
            "projects": [
                {
                    "name": "Food Delivery App",
                    "description": "Cross-platform food delivery app with real-time tracking and 100,000+ downloads",
                    "technologies": ["React Native", "Firebase", "Google Maps API"],
                    "duration": "7 months"
                }
            ],
            "certifications": ["React Native Certified Developer"]
        },
        {
            "email": "sara.ahmed@protonmail.com",
            "password": "Password123!",
            "name": "Sara Ahmed",
            "designation": "Backend Developer",
            "location": "Faisalabad, Pakistan",
            "is_looking_for_job": True,
            "expected_salary": "$65,000 - $85,000",
            "current_salary": "$60,000",
            "experience": "3 years",
            "summary": "Backend developer with strong skills in Node.js and Python. Focused on building robust APIs and microservices architecture for fintech and healthcare applications.",
            "skills": [
                {"name": "Node.js", "level": "Advanced", "years": 3},
                {"name": "Python", "level": "Advanced", "years": 3},
                {"name": "Express.js", "level": "Advanced", "years": 3},
                {"name": "PostgreSQL", "level": "Advanced", "years": 3},
                {"name": "MongoDB", "level": "Advanced", "years": 2},
                {"name": "REST APIs", "level": "Expert", "years": 3}
            ],
            "experience_details": [
                {
                    "company": "Lums Technology",
                    "position": "Backend Developer",
                    "duration": "Mar 2021 - Present",
                    "description": "Develop REST APIs for healthcare management system, implement authentication and authorization, and optimize database queries."
                },
                {
                    "company": "Educative.io Pakistan",
                    "position": "Junior Backend Developer",
                    "duration": "Jul 2021 - Feb 2021",
                    "description": "Built backend services for educational platform, integrated third-party APIs, and implemented caching strategies."
                }
            ],
            "projects": [
                {
                    "name": "Hospital Management API",
                    "description": "Built comprehensive REST API for hospital management with appointment scheduling",
                    "technologies": ["Node.js", "Express.js", "PostgreSQL", "JWT"],
                    "duration": "5 months"
                }
            ],
            "certifications": ["Node.js Application Development"]
        },
        {
            "email": "hassan.malik@icloud.com",
            "password": "Password123!",
            "name": "Hassan Malik",
            "designation": "Frontend Developer",
            "location": "Rawalpindi, Pakistan",
            "is_looking_for_job": True,
            "expected_salary": "$55,000 - $75,000",
            "current_salary": "$50,000",
            "experience": "3 years",
            "summary": "Frontend developer passionate about creating modern web applications using React and Vue.js. Experienced in responsive design and performance optimization for international clients.",
            "skills": [
                {"name": "React", "level": "Advanced", "years": 3},
                {"name": "Vue.js", "level": "Advanced", "years": 2},
                {"name": "JavaScript", "level": "Advanced", "years": 3},
                {"name": "CSS/SCSS", "level": "Expert", "years": 3},
                {"name": "HTML5", "level": "Expert", "years": 4},
                {"name": "Bootstrap", "level": "Advanced", "years": 3}
            ],
            "experience_details": [
                {
                    "company": "Techlogix",
                    "position": "Frontend Developer",
                    "duration": "Jan 2022 - Present",
                    "description": "Develop responsive web applications using React, implement modern UI/UX designs, and optimize application performance."
                },
                {
                    "company": "DevBatch",
                    "position": "Junior Frontend Developer",
                    "duration": "Jun 2021 - Dec 2021",
                    "description": "Created interactive web components, collaborated with design team, and maintained existing web applications."
                }
            ],
            "projects": [
                {
                    "name": "Real Estate Portal",
                    "description": "Built property listing website with advanced search and filtering capabilities",
                    "technologies": ["React", "Redux", "Material-UI", "API Integration"],
                    "duration": "4 months"
                }
            ],
            "certifications": ["React Developer Certification"]
        },
        {
            "email": "zainab.hussain@gmail.pk",
            "password": "Password123!",
            "name": "Zainab Hussain",
            "designation": "Product Manager",
            "location": "Karachi, Pakistan",
            "is_looking_for_job": False,
            "expected_salary": "$85,000 - $105,000",
            "current_salary": "$90,000",
            "experience": "6 years",
            "summary": "Strategic product manager with experience in fintech and e-commerce domains. Expert in agile methodologies and cross-functional team leadership with a track record of successful product launches.",
            "skills": [
                {"name": "Product Strategy", "level": "Expert", "years": 6},
                {"name": "Agile/Scrum", "level": "Expert", "years": 6},
                {"name": "Market Research", "level": "Advanced", "years": 5},
                {"name": "Data Analysis", "level": "Advanced", "years": 4},
                {"name": "User Research", "level": "Advanced", "years": 5},
                {"name": "Roadmap Planning", "level": "Expert", "years": 6}
            ],
            "experience_details": [
                {
                    "company": "Tez Financial Services",
                    "position": "Senior Product Manager",
                    "duration": "Apr 2020 - Present",
                    "description": "Lead product strategy for digital wallet platform, manage cross-functional teams, and drive product roadmap execution."
                },
                {
                    "company": "Daraz Pakistan",
                    "position": "Product Manager",
                    "duration": "Jun 2018 - Mar 2020",
                    "description": "Managed e-commerce platform features, conducted user research, and improved conversion rates by 25%."
                },
                {
                    "company": "Rozee.pk",
                    "position": "Associate Product Manager",
                    "duration": "Jan 2018 - May 2018",
                    "description": "Supported product development for job portal platform and analyzed user behavior patterns."
                }
            ],
            "projects": [
                {
                    "name": "Digital Wallet Launch",
                    "description": "Successfully launched digital payment platform reaching 500,000+ users in first year",
                    "technologies": ["Product Analytics", "User Research", "A/B Testing"],
                    "duration": "12 months"
                }
            ],
            "certifications": ["Certified Scrum Product Owner", "Product Management Certification"]
        },
        {
            "email": "ali.raza@techlogix.com",
            "password": "Password123!",
            "name": "Ali Raza",
            "designation": "QA Engineer",
            "location": "Lahore, Pakistan",
            "is_looking_for_job": True,
            "expected_salary": "$50,000 - $70,000",
            "current_salary": "$45,000",
            "experience": "4 years",
            "summary": "Quality assurance engineer with expertise in both manual and automated testing. Passionate about ensuring software quality and user satisfaction across web and mobile applications.",
            "skills": [
                {"name": "Selenium", "level": "Advanced", "years": 3},
                {"name": "Manual Testing", "level": "Expert", "years": 4},
                {"name": "API Testing", "level": "Advanced", "years": 3},
                {"name": "Test Planning", "level": "Advanced", "years": 4},
                {"name": "Postman", "level": "Advanced", "years": 3},
                {"name": "JIRA", "level": "Advanced", "years": 4}
            ],
            "experience_details": [
                {
                    "company": "Systems Limited",
                    "position": "Senior QA Engineer",
                    "duration": "Aug 2021 - Present",
                    "description": "Lead testing efforts for enterprise applications, design test strategies, and mentor junior QA team members."
                },
                {
                    "company": "Genetech Solutions",
                    "position": "QA Engineer",
                    "duration": "Feb 2020 - Jul 2021",
                    "description": "Performed comprehensive testing for web and mobile applications, created automated test suites, and improved testing efficiency."
                }
            ],
            "projects": [
                {
                    "name": "Banking App Testing",
                    "description": "Comprehensive testing of mobile banking application ensuring 99.9% uptime",
                    "technologies": ["Selenium", "Appium", "TestNG"],
                    "duration": "6 months"
                }
            ],
            "certifications": ["ISTQB Foundation Level", "Selenium WebDriver Certification"]
        },
        {
            "email": "bilal.sheikh@systems.com",
            "password": "Password123!",
            "name": "Bilal Sheikh",
            "designation": "Software Architect",
            "location": "Islamabad, Pakistan",
            "is_looking_for_job": False,
            "expected_salary": "$110,000 - $130,000",
            "current_salary": "$120,000",
            "experience": "8 years",
            "summary": "Experienced software architect with expertise in designing scalable systems and leading technical teams. Specialized in microservices architecture and cloud-native applications for international clients.",
            "skills": [
                {"name": "System Design", "level": "Expert", "years": 6},
                {"name": "Microservices", "level": "Expert", "years": 5},
                {"name": "AWS", "level": "Expert", "years": 6},
                {"name": "Java", "level": "Expert", "years": 8},
                {"name": "Spring Boot", "level": "Expert", "years": 6},
                {"name": "Docker", "level": "Expert", "years": 5}
            ],
            "experience_details": [
                {
                    "company": "10Pearls",
                    "position": "Principal Software Architect",
                    "duration": "Jan 2020 - Present",
                    "description": "Design enterprise-level solutions for Fortune 500 clients, lead technical teams, and establish architectural best practices."
                },
                {
                    "company": "Netsol Technologies",
                    "position": "Senior Software Engineer",
                    "duration": "Mar 2017 - Dec 2019",
                    "description": "Architected microservices solutions for automotive finance platform and mentored development teams."
                },
                {
                    "company": "TRG Pakistan",
                    "position": "Software Engineer",
                    "duration": "Jul 2016 - Feb 2017",
                    "description": "Developed enterprise applications using Java Spring framework and optimized system performance."
                }
            ],
            "projects": [
                {
                    "name": "Enterprise Microservices Platform",
                    "description": "Architected scalable microservices platform handling 1M+ daily transactions",
                    "technologies": ["Java", "Spring Boot", "AWS", "Kubernetes"],
                    "duration": "12 months"
                }
            ],
            "certifications": ["AWS Solutions Architect Professional", "Oracle Java Architect"]
        }
    ]
    
    created_users = []
    
    try:
        for user_data in dummy_users:
            # Hash password
            password = user_data.pop("password")
            hashed_password = get_password_hash(password)
            
            # Create completed onboarding progress
            onboarding_progress = {
                "step_1_pdf_upload": "completed",
                "step_2_profile_info": "completed", 
                "step_3_work_preferences": "completed",
                "step_4_salary_availability": "completed",
                "current_step": 5,
                "completed": True
            }
            
            # Create work preferences
            work_preferences = {
                "current_employment_mode": ["full-time"],
                "preferred_work_mode": ["remote", "hybrid"],
                "preferred_employment_type": ["full-time"],
                "preferred_location": user_data["location"],
                "notice_period": "2 weeks",
                "availability": "immediate"
            }
            
            # Prepare user document
            user_doc = {
                **user_data,
                "hashed_password": hashed_password,
                "rating": 4.5,
                "onboarding_completed": True,
                "onboarding_progress": onboarding_progress,
                "work_preferences": work_preferences,
                "daily_requests": 0,
                "last_request_reset": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert user
            result = await db.users.insert_one(user_doc)
            created_users.append({
                "email": user_data["email"],
                "password": password,
                "name": user_data["name"],
                "designation": user_data["designation"],
                "id": str(result.inserted_id)
            })
        
        return {
            "message": f"Successfully created {len(created_users)} dummy users",
            "users": created_users,
            "success": True
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dummy users: {str(e)}"
        )