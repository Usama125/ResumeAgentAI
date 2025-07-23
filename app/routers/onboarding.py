from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi import status
from typing import Optional
import uuid
import os
import json
from app.services.pdf_service import PDFService
from app.services.user_service import UserService
from app.routers.auth import get_current_user
from app.config import settings
from app.models.onboarding import (
    Step1PDFUploadRequest, Step2ProfileInfoRequest, 
    Step3WorkPreferencesRequest, Step4SalaryAvailabilityRequest,
    OnboardingStatusResponse, StepCompletionResponse
)
from app.models.user import UserUpdate, OnboardingStepStatus

router = APIRouter()
pdf_service = PDFService()
user_service = UserService()

@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(current_user = Depends(get_current_user)):
    """Get current onboarding status"""
    return OnboardingStatusResponse(
        current_step=current_user.onboarding_progress.current_step,
        completed=current_user.onboarding_progress.completed,
        step_1_pdf_upload=current_user.onboarding_progress.step_1_pdf_upload,
        step_2_profile_info=current_user.onboarding_progress.step_2_profile_info,
        step_3_work_preferences=current_user.onboarding_progress.step_3_work_preferences,
        step_4_salary_availability=current_user.onboarding_progress.step_4_salary_availability
    )

@router.post("/step-1/pdf-upload", response_model=StepCompletionResponse)
async def step_1_pdf_upload(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Step 1: Upload and process LinkedIn PDF"""
    
    print(f"🚀 [ONBOARDING] PDF upload started for user: {current_user.id}")
    print(f"🔍 [ONBOARDING] Current step: {current_user.onboarding_progress.current_step}")
    print(f"🔍 [ONBOARDING] File: {file.filename}, size: {file.size}")
    
    # Validate current step
    if current_user.onboarding_progress.current_step != 1:
        print(f"❌ [ONBOARDING] Invalid step: {current_user.onboarding_progress.current_step}, expected 1")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Current step is {current_user.onboarding_progress.current_step}, expected step 1"
        )
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    if not file.size or file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must be less than {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    try:
        print("✅ [ONBOARDING] File validation passed")
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        print(f"🔍 [ONBOARDING] Generated filename: {unique_filename}")
        
        # Read file content
        file_content = await file.read()
        print(f"✅ [ONBOARDING] File content read: {len(file_content)} bytes")
        
        # Save and process PDF
        print("📁 [ONBOARDING] Saving PDF file...")
        file_path = await pdf_service.save_uploaded_pdf(file_content, unique_filename)
        print(f"✅ [ONBOARDING] PDF saved to: {file_path}")
        
        print("⚙️ [ONBOARDING] Starting PDF processing...")
        result = await pdf_service.process_linkedin_pdf(file_path)
        print(f"✅ [ONBOARDING] PDF processing result: {result.get('success', False)}")
        
        if result.get('success'):
            # Update user with extracted data (even if empty)
            extracted_data = result.get('extracted_data', {})
            update_data = {}
            
            print(f"📝 [ONBOARDING] Processing extracted data: {len(extracted_data)} fields found")
            
            # Process extracted data if available, otherwise just mark step as completed
            if extracted_data:
                if "name" in extracted_data:
                    update_data["name"] = extracted_data["name"]
                if "designation" in extracted_data:
                    update_data["designation"] = extracted_data["designation"]
                if "location" in extracted_data:
                    update_data["location"] = extracted_data["location"]
                if "summary" in extracted_data:
                    update_data["summary"] = extracted_data["summary"]
                if "skills" in extracted_data and extracted_data["skills"]:
                    # Transform skills to correct format
                    skills_data = extracted_data["skills"]
                    transformed_skills = []
                    
                    # Ensure skills_data is iterable
                    if not isinstance(skills_data, (list, tuple)):
                        skills_data = [skills_data] if skills_data else []
                    
                    for skill_item in skills_data:
                        if isinstance(skill_item, dict):
                            skill_name = skill_item.get("skill", skill_item.get("name", ""))
                            proficiency = skill_item.get("proficiency", "")
                            
                            # Map proficiency to level
                            level = "Intermediate"  # default
                            if "✔️" in proficiency or "expert" in proficiency.lower():
                                level = "Advanced"
                            elif "beginner" in proficiency.lower():
                                level = "Beginner"
                            elif "advanced" in proficiency.lower() or "senior" in proficiency.lower():
                                level = "Expert"
                            
                            # Estimate years based on level
                            years = 2  # default
                            if level == "Beginner":
                                years = 1
                            elif level == "Intermediate":
                                years = 3
                            elif level == "Advanced":
                                years = 5
                            elif level == "Expert":
                                years = 7
                            
                            if skill_name:
                                transformed_skills.append({
                                    "name": skill_name,
                                    "level": level,
                                    "years": years
                                })
                    
                    update_data["skills"] = transformed_skills
                if "experience_details" in extracted_data:
                    update_data["experience_details"] = extracted_data["experience_details"]
                if "projects" in extracted_data and extracted_data["projects"]:
                    # Transform projects to correct format
                    projects_data = extracted_data["projects"]
                    transformed_projects = []
                    
                    # Ensure projects_data is iterable
                    if not isinstance(projects_data, (list, tuple)):
                        projects_data = [projects_data] if projects_data else []
                    
                    for project_item in projects_data:
                        if isinstance(project_item, dict):
                            project_name = project_item.get("name", project_item.get("title", "Untitled Project"))
                            project_description = project_item.get("description", "No description provided")
                            project_technologies = project_item.get("technologies", project_item.get("tech", []))
                            
                            # Ensure technologies is a list
                            if isinstance(project_technologies, str):
                                project_technologies = [tech.strip() for tech in project_technologies.split(",") if tech.strip()]
                            elif not isinstance(project_technologies, list):
                                project_technologies = []
                            
                            transformed_projects.append({
                                "name": project_name,
                                "description": project_description,
                                "technologies": project_technologies
                            })
                        elif isinstance(project_item, str):
                            # If project is just a string, create a basic project
                            transformed_projects.append({
                                "name": project_item,
                                "description": "No description provided",
                                "technologies": []
                            })
                    
                    update_data["projects"] = transformed_projects
                    
                if "certifications" in extracted_data and extracted_data["certifications"]:
                    # Transform certifications to correct format (list of strings)
                    certifications_data = extracted_data["certifications"]
                    transformed_certifications = []
                    
                    # Ensure certifications_data is iterable
                    if not isinstance(certifications_data, (list, tuple)):
                        certifications_data = [certifications_data] if certifications_data else []
                    
                    for cert_item in certifications_data:
                        if isinstance(cert_item, dict):
                            cert_name = cert_item.get("name", cert_item.get("title", cert_item.get("certification", "Unknown Certification")))
                            transformed_certifications.append(cert_name)
                        elif isinstance(cert_item, str):
                            transformed_certifications.append(cert_item)
                    
                    update_data["certifications"] = transformed_certifications
                if "experience" in extracted_data:
                    update_data["experience"] = extracted_data["experience"]
            else:
                print("📝 [ONBOARDING] No data extracted from PDF, but marking step as completed")
            
            # Update onboarding progress - PDF uploaded, user can continue or skip
            # Profile is considered complete with PDF, but user can continue onboarding
            update_data["onboarding_progress"] = {
                "step_1_pdf_upload": OnboardingStepStatus.COMPLETED,
                "step_2_profile_info": current_user.onboarding_progress.step_2_profile_info,
                "step_3_work_preferences": current_user.onboarding_progress.step_3_work_preferences,
                "step_4_salary_availability": current_user.onboarding_progress.step_4_salary_availability,
                "current_step": 2,
                "completed": False  # Don't auto-complete, let user decide
            }
            
            print(f"🔄 [ONBOARDING] Creating user update with data: {list(update_data.keys())}")
            user_update = UserUpdate(**update_data)
            print(f"✅ [ONBOARDING] UserUpdate object created successfully")
            
            print(f"💾 [ONBOARDING] Updating user {current_user.id} in database...")
            await user_service.update_user(str(current_user.id), user_update)
            print(f"✅ [ONBOARDING] User updated successfully")
            
            return StepCompletionResponse(
                success=True,
                next_step=2,
                message="PDF processed successfully! Your profile is now ready. You can continue adding details or skip to your profile.",
                onboarding_completed=False  # Don't auto-complete, normal flow
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'PDF processing failed')
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [ONBOARDING] Exception during PDF upload: {str(e)}")
        print(f"❌ [ONBOARDING] Exception type: {type(e).__name__}")
        print(f"❌ [ONBOARDING] Exception details: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF: {str(e)}"
        )

@router.post("/step-2/profile-info", response_model=StepCompletionResponse)
async def step_2_profile_info(
    profile_picture: Optional[UploadFile] = File(None),
    name: str = Form(None),
    designation: str = Form(None),
    location: str = Form(None),
    summary: str = Form(None),
    is_looking_for_job: bool = Form(True),
    additional_info: str = Form(""),
    current_user = Depends(get_current_user)
):
    """Step 2: Update profile information"""
    
    # Validate current step
    if current_user.onboarding_progress.current_step != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Current step is {current_user.onboarding_progress.current_step}, expected step 2"
        )
    
    try:
        update_data = {}
        
        # Handle profile picture upload
        if profile_picture:
            # Validate image file
            if not any(profile_picture.filename.lower().endswith(ext) for ext in ['jpg', 'jpeg', 'png']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only JPG, JPEG, PNG files are allowed for profile pictures"
                )
            
            # Save profile picture
            file_extension = profile_picture.filename.split('.')[-1]
            unique_filename = f"profile_{current_user.id}_{uuid.uuid4()}.{file_extension}"
            profile_dir = os.path.join(settings.UPLOAD_DIR, "profiles")
            
            if not os.path.exists(profile_dir):
                os.makedirs(profile_dir)
            
            file_path = os.path.join(profile_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                content = await profile_picture.read()
                buffer.write(content)
            
            update_data["profile_picture"] = f"/uploads/profiles/{unique_filename}"
        
        # Update other profile fields
        if name:
            update_data["name"] = name
        if designation:
            update_data["designation"] = designation
        if location:
            update_data["location"] = location
        if summary:
            update_data["summary"] = summary
        
        update_data["is_looking_for_job"] = is_looking_for_job
        
        # Update onboarding progress
        update_data["onboarding_progress"] = {
            "step_1_pdf_upload": current_user.onboarding_progress.step_1_pdf_upload,
            "step_2_profile_info": OnboardingStepStatus.COMPLETED,
            "step_3_work_preferences": current_user.onboarding_progress.step_3_work_preferences,
            "step_4_salary_availability": current_user.onboarding_progress.step_4_salary_availability,
            "current_step": 3,
            "completed": False
        }
        
        user_update = UserUpdate(**update_data)
        await user_service.update_user(str(current_user.id), user_update)
        
        return StepCompletionResponse(
            success=True,
            next_step=3,
            message="Profile information updated successfully, proceed to step 3",
            onboarding_completed=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )

@router.post("/step-3/work-preferences", response_model=StepCompletionResponse)
async def step_3_work_preferences(
    current_employment_mode: str = Form(""),
    preferred_work_mode: str = Form(""),
    preferred_employment_type: str = Form(""),
    preferred_location: str = Form(""),
    notice_period: str = Form(None),
    availability: str = Form("immediate"),
    current_user = Depends(get_current_user)
):
    """Step 3: Set work preferences"""
    
    # Validate current step
    if current_user.onboarding_progress.current_step != 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Current step is {current_user.onboarding_progress.current_step}, expected step 3"
        )
    
    try:
        # Prepare work preferences
        work_preferences = {
            "current_employment_mode": current_employment_mode.split(",") if current_employment_mode else [],
            "preferred_work_mode": preferred_work_mode.split(",") if preferred_work_mode else [],
            "preferred_employment_type": preferred_employment_type.split(",") if preferred_employment_type else [],
            "preferred_location": preferred_location,
            "notice_period": notice_period,
            "availability": availability
        }
        
        update_data = {
            "work_preferences": work_preferences,
            "onboarding_progress": {
                "step_1_pdf_upload": current_user.onboarding_progress.step_1_pdf_upload,
                "step_2_profile_info": current_user.onboarding_progress.step_2_profile_info,
                "step_3_work_preferences": OnboardingStepStatus.COMPLETED,
                "step_4_salary_availability": current_user.onboarding_progress.step_4_salary_availability,
                "current_step": 4,
                "completed": False
            }
        }
        
        user_update = UserUpdate(**update_data)
        await user_service.update_user(str(current_user.id), user_update)
        
        return StepCompletionResponse(
            success=True,
            next_step=4,
            message="Work preferences updated successfully, proceed to step 4",
            onboarding_completed=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating work preferences: {str(e)}"
        )

@router.post("/step-4/salary-availability", response_model=StepCompletionResponse)
async def step_4_salary_availability(
    current_salary: str = Form(None),
    expected_salary: str = Form(None),
    availability: str = Form("immediate"),
    notice_period: str = Form(None),
    current_user = Depends(get_current_user)
):
    """Step 4: Set salary and availability - Final step"""
    
    # Validate current step
    if current_user.onboarding_progress.current_step != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Current step is {current_user.onboarding_progress.current_step}, expected step 4"
        )
    
    try:
        update_data = {
            "current_salary": current_salary,
            "expected_salary": expected_salary,
            "onboarding_completed": True,
            "onboarding_progress": {
                "step_1_pdf_upload": current_user.onboarding_progress.step_1_pdf_upload,
                "step_2_profile_info": current_user.onboarding_progress.step_2_profile_info,
                "step_3_work_preferences": current_user.onboarding_progress.step_3_work_preferences,
                "step_4_salary_availability": OnboardingStepStatus.COMPLETED,
                "current_step": 4,
                "completed": True
            }
        }
        
        # Update work preferences with availability if provided
        if current_user.work_preferences:
            work_preferences = current_user.work_preferences.dict()
            work_preferences["availability"] = availability
            if notice_period:
                work_preferences["notice_period"] = notice_period
            update_data["work_preferences"] = work_preferences
        
        user_update = UserUpdate(**update_data)
        updated_user = await user_service.update_user(str(current_user.id), user_update)
        
        return StepCompletionResponse(
            success=True,
            next_step=None,
            message="Onboarding completed successfully!",
            onboarding_completed=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing onboarding: {str(e)}"
        )

@router.post("/skip-to-profile", response_model=StepCompletionResponse)
async def skip_to_profile(
    current_user = Depends(get_current_user)
):
    """Skip onboarding and go directly to profile (only available after PDF upload)"""
    
    # Ensure PDF has been uploaded (step 1 completed)
    if current_user.onboarding_progress.step_1_pdf_upload != OnboardingStepStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must complete PDF upload before skipping to profile"
        )
    
    try:
        # Mark onboarding as completed
        update_data = {
            "onboarding_completed": True,
            "onboarding_progress": {
                "step_1_pdf_upload": OnboardingStepStatus.COMPLETED,
                "step_2_profile_info": OnboardingStepStatus.COMPLETED,
                "step_3_work_preferences": OnboardingStepStatus.COMPLETED,
                "step_4_salary_availability": OnboardingStepStatus.COMPLETED,
                "current_step": 4,
                "completed": True
            }
        }
        
        user_update = UserUpdate(**update_data)
        await user_service.update_user(str(current_user.id), user_update)
        
        return StepCompletionResponse(
            success=True,
            next_step=None,
            message="Onboarding completed! Redirecting to your profile.",
            onboarding_completed=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing onboarding: {str(e)}"
        )

@router.post("/resume/{step}", response_model=OnboardingStatusResponse)
async def resume_onboarding(
    step: int,
    current_user = Depends(get_current_user)
):
    """Resume onboarding from a specific step"""
    
    if step < 1 or step > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Step must be between 1 and 4"
        )
    
    # Validate that user can resume from this step
    if step > current_user.onboarding_progress.current_step + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume from step {step}. Current step is {current_user.onboarding_progress.current_step}"
        )
    
    try:
        # Update current step
        update_data = {
            "onboarding_progress": {
                "step_1_pdf_upload": current_user.onboarding_progress.step_1_pdf_upload,
                "step_2_profile_info": current_user.onboarding_progress.step_2_profile_info,
                "step_3_work_preferences": current_user.onboarding_progress.step_3_work_preferences,
                "step_4_salary_availability": current_user.onboarding_progress.step_4_salary_availability,
                "current_step": step,
                "completed": current_user.onboarding_progress.completed
            }
        }
        
        user_update = UserUpdate(**update_data)
        await user_service.update_user(str(current_user.id), user_update)
        
        # Return updated status
        return OnboardingStatusResponse(
            current_step=step,
            completed=current_user.onboarding_progress.completed,
            step_1_pdf_upload=current_user.onboarding_progress.step_1_pdf_upload,
            step_2_profile_info=current_user.onboarding_progress.step_2_profile_info,
            step_3_work_preferences=current_user.onboarding_progress.step_3_work_preferences,
            step_4_salary_availability=current_user.onboarding_progress.step_4_salary_availability
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resuming onboarding: {str(e)}"
        )

# Keep the old upload-pdf endpoint for backward compatibility
@router.post("/upload-pdf")
async def upload_linkedin_pdf(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload and process LinkedIn PDF (Legacy endpoint - use /step-1/pdf-upload instead)"""
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    if not file.size or file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must be less than {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Read file content
        file_content = await file.read()
        
        # Save and process PDF
        file_path = await pdf_service.save_uploaded_pdf(file_content, unique_filename)
        result = await pdf_service.process_linkedin_pdf(file_path)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF: {str(e)}"
        )

# Legacy endpoint - marked for deprecation
@router.post("/complete")
async def complete_onboarding(
    profile_picture: Optional[UploadFile] = File(None),
    additional_info: str = Form(""),
    is_looking_for_job: bool = Form(True),
    current_employment_mode: str = Form(""),
    preferred_work_mode: str = Form(""),
    preferred_employment_type: str = Form(""),
    preferred_location: str = Form(""),
    current_salary: str = Form(""),
    expected_salary: str = Form(""),
    notice_period: str = Form(""),
    availability: str = Form("immediate"),
    extracted_data: str = Form("{}"),  # JSON string from PDF processing
    current_user = Depends(get_current_user)
):
    """Complete user onboarding (Legacy endpoint - use step-by-step endpoints instead)"""
    
    try:
        # Parse extracted data from PDF
        try:
            pdf_data = json.loads(extracted_data) if extracted_data != "{}" else {}
        except:
            pdf_data = {}
        
        # Handle profile picture upload
        profile_picture_url = None
        if profile_picture:
            # Validate image file
            if not any(profile_picture.filename.lower().endswith(ext) for ext in ['jpg', 'jpeg', 'png']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only JPG, JPEG, PNG files are allowed for profile pictures"
                )
            
            # Save profile picture
            file_extension = profile_picture.filename.split('.')[-1]
            unique_filename = f"profile_{current_user.id}_{uuid.uuid4()}.{file_extension}"
            profile_dir = os.path.join(settings.UPLOAD_DIR, "profiles")
            
            if not os.path.exists(profile_dir):
                os.makedirs(profile_dir)
            
            file_path = os.path.join(profile_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                content = await profile_picture.read()
                buffer.write(content)
            
            profile_picture_url = f"/uploads/profiles/{unique_filename}"
        
        # Prepare update data
        update_data = {
            "profile_picture": profile_picture_url,
            "is_looking_for_job": is_looking_for_job,
            "expected_salary": expected_salary,
            "current_salary": current_salary,
            "onboarding_completed": True
        }
        
        # Add data from PDF processing
        if pdf_data:
            if "name" in pdf_data:
                update_data["name"] = pdf_data["name"]
            if "designation" in pdf_data:
                update_data["designation"] = pdf_data["designation"]
            if "location" in pdf_data:
                update_data["location"] = pdf_data["location"]
            if "summary" in pdf_data:
                update_data["summary"] = pdf_data["summary"]
            if "skills" in pdf_data:
                update_data["skills"] = pdf_data["skills"]
            if "experience_details" in pdf_data:
                update_data["experience_details"] = pdf_data["experience_details"]
            if "projects" in pdf_data:
                update_data["projects"] = pdf_data["projects"]
            if "certifications" in pdf_data:
                update_data["certifications"] = pdf_data["certifications"]
            if "experience" in pdf_data:
                update_data["experience"] = pdf_data["experience"]
        
        # Add work preferences
        work_preferences = {
            "current_employment_mode": current_employment_mode.split(",") if current_employment_mode else [],
            "preferred_work_mode": preferred_work_mode.split(",") if preferred_work_mode else [],
            "preferred_employment_type": preferred_employment_type.split(",") if preferred_employment_type else [],
            "preferred_location": preferred_location,
            "notice_period": notice_period,
            "availability": availability
        }
        update_data["work_preferences"] = work_preferences
        
        # Update onboarding progress to completed
        update_data["onboarding_progress"] = {
            "step_1_pdf_upload": OnboardingStepStatus.COMPLETED,
            "step_2_profile_info": OnboardingStepStatus.COMPLETED,
            "step_3_work_preferences": OnboardingStepStatus.COMPLETED,
            "step_4_salary_availability": OnboardingStepStatus.COMPLETED,
            "current_step": 4,
            "completed": True
        }
        
        # Update user
        user_update = UserUpdate(**update_data)
        updated_user = await user_service.update_user(str(current_user.id), user_update)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to complete onboarding"
            )
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "user_id": str(updated_user.id),
            "profile_url": f"/profile/{updated_user.id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing onboarding: {str(e)}"
        )