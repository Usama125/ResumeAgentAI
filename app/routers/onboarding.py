from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi import status
from typing import Optional
import uuid
import os
import json
from app.services.pdf_service import DocumentService
from app.services.user_service import UserService
from app.services.file_service import FileService
from app.routers.auth import get_current_user
from app.config import settings
from app.models.onboarding import (
    Step1PDFUploadRequest, Step2ProfileInfoRequest, 
    Step3WorkPreferencesRequest, Step4SalaryAvailabilityRequest,
    OnboardingStatusResponse, StepCompletionResponse
)
from app.models.user import UserUpdate, OnboardingStepStatus

router = APIRouter()
document_service = DocumentService()
user_service = UserService()
file_service = FileService()

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
    """Step 1: Upload and process resume document (PDF, Word, etc.) - Enhanced to support multiple formats"""
    
    print(f"🚀 [ONBOARDING] Document upload started for user: {current_user.id}")
    print(f"🔍 [ONBOARDING] Current step: {current_user.onboarding_progress.current_step}")
    print(f"🔍 [ONBOARDING] File: {file.filename}, size: {file.size}")
    
    # Validate current step
    if current_user.onboarding_progress.current_step != 1:
        print(f"❌ [ONBOARDING] Invalid step: {current_user.onboarding_progress.current_step}, expected 1")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Current step is {current_user.onboarding_progress.current_step}, expected step 1"
        )
    
    # Validate file format - support PDF, Word documents
    supported_extensions = ['.pdf', '.docx', '.doc']
    file_extension = '.' + file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    
    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Supported formats: {', '.join(supported_extensions)}"
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
        
        # Save and process document
        print("📁 [ONBOARDING] Saving document file...")
        file_path = await document_service.save_uploaded_document(file_content, unique_filename)
        print(f"✅ [ONBOARDING] Document saved to: {file_path}")
        
        print("⚙️ [ONBOARDING] Starting document processing...")
        result = await document_service.process_resume_document(file_path, file.filename, str(current_user.id))
        print(f"✅ [ONBOARDING] Document processing result: {result.get('success', False)}")
        
        if result.get('success'):
            # Update user with extracted data (even if empty)
            extracted_data = result.get('extracted_data', {})
            qa_verification = extracted_data.get('qa_verification', {}) if extracted_data else {}
            update_data = {}
            
            print(f"📝 [ONBOARDING] Processing extracted data: {len(extracted_data)} fields found")
            print(f"🔍 [ONBOARDING] QA Verification: {qa_verification}")
            
            # Process extracted data - AI provides clean, structured data
            if extracted_data:
                print(f"📝 [ONBOARDING] Processing AI-extracted data with {len(extracted_data)} fields")
                print(f"🔎 [ONBOARDING] Extracted data keys: {list(extracted_data.keys())}")
                
                # DEBUG: Check skills specifically
                if "skills" in extracted_data:
                    skills_data = extracted_data["skills"]
                    print(f"🎯 [ONBOARDING] SKILLS DEBUG - Type: {type(skills_data)}, Value: {skills_data}")
                    if isinstance(skills_data, list):
                        print(f"🎯 [ONBOARDING] SKILLS DEBUG - List length: {len(skills_data)}")
                        if len(skills_data) > 0:
                            print(f"🎯 [ONBOARDING] SKILLS DEBUG - First skill: {skills_data[0]}")
                    else:
                        print(f"🎯 [ONBOARDING] SKILLS DEBUG - Skills is not a list!")
                else:
                    print(f"❌ [ONBOARDING] SKILLS DEBUG - No 'skills' key in extracted_data!")
                
                # DEBUG: Check experience specifically
                if "experience" in extracted_data:
                    experience_data = extracted_data["experience"]
                    print(f"🎯 [ONBOARDING] EXPERIENCE DEBUG - Type: {type(experience_data)}, Value: '{experience_data}'")
                else:
                    print(f"❌ [ONBOARDING] EXPERIENCE DEBUG - No 'experience' key in extracted_data!")
                    print(f"🔍 [ONBOARDING] EXPERIENCE DEBUG - Available keys: {list(extracted_data.keys())}")
                
                # The AI already provides data in the correct format - just map it directly
                # Include all data regardless of QA status (user should not be blocked)
                field_mapping = {
                    "name": "name",
                    "designation": "designation", 
                    "location": "location",
                    "summary": "summary",
                    "profession": "profession",
                    "experience": "experience",
                    "skills": "skills",
                    "experience_details": "experience_details",
                    "projects": "projects",
                    "certifications": "certifications",
                    "contact_info": "contact_info",
                    "education": "education",
                    "languages": "languages",
                    "awards": "awards",
                    "publications": "publications",
                    "volunteer_experience": "volunteer_experience",
                    "interests": "interests"
                }
                
                for ai_field, db_field in field_mapping.items():
                    if ai_field in extracted_data and ai_field != "qa_verification":
                        data_value = extracted_data[ai_field]
                        # Include all data, even if partially empty (user can edit later)
                        if data_value is not None:
                            update_data[db_field] = data_value
                            if ai_field == "skills":
                                print(f"🎯 [ONBOARDING] SKILLS MAPPING - Added skills to update_data: {data_value}")
                            elif ai_field == "experience":
                                print(f"🎯 [ONBOARDING] EXPERIENCE MAPPING - Added experience to update_data: '{data_value}'")
                            print(f"✅ [ONBOARDING] Mapped {ai_field}: {type(data_value).__name__}")
            else:
                print("📝 [ONBOARDING] No data extracted from document, but marking step as completed")
            
            # Update onboarding progress - PDF uploaded, user can continue or skip
            update_data["onboarding_progress"] = {
                "step_1_pdf_upload": OnboardingStepStatus.COMPLETED,
                "step_2_profile_info": current_user.onboarding_progress.step_2_profile_info,
                "step_3_work_preferences": current_user.onboarding_progress.step_3_work_preferences,
                "step_4_salary_availability": current_user.onboarding_progress.step_4_salary_availability,
                "current_step": 2,
                "completed": False  # Don't auto-complete, let user decide
            }
            
            print(f"🔄 [ONBOARDING] Creating user update with data: {list(update_data.keys())}")
            
            # DEBUG: Check skills before UserUpdate validation
            if "skills" in update_data:
                skills_data = update_data["skills"] 
                print(f"🎯 [ONBOARDING] PRE-VALIDATION - Skills type: {type(skills_data)}")
                print(f"🎯 [ONBOARDING] PRE-VALIDATION - Skills count: {len(skills_data) if isinstance(skills_data, list) else 'Not a list'}")
                if isinstance(skills_data, list) and len(skills_data) > 0:
                    print(f"🎯 [ONBOARDING] PRE-VALIDATION - First skill: {skills_data[0]}")
            
            # DEBUG: Check experience before UserUpdate validation  
            if "experience" in update_data:
                experience_data = update_data["experience"]
                print(f"🎯 [ONBOARDING] PRE-VALIDATION - Experience: '{experience_data}' (type: {type(experience_data)})")
            else:
                print(f"❌ [ONBOARDING] PRE-VALIDATION - No experience key in update_data!")
                # FINAL AGGRESSIVE FALLBACK - directly search the file content
                if result.get('file_content'):
                    print(f"🔧 [ONBOARDING] FINAL FALLBACK - Searching file content directly for experience...")
                    import re
                    file_text = result.get('file_content', '')
                    experience_patterns = [
                        r'Experience\s*[-–—:]\s*(\d+(?:\+|\.)?\d*)\s*years?',
                        r'(\d+(?:\+|\.)?\d*)\s*years?\s*of\s*experience',
                        r'(\d+(?:\+|\.)?\d*)\s*years?\s*experience',
                        r'(\d+(?:\+|\.)?\d*)\+\s*years?',
                    ]
                    
                    for i, pattern in enumerate(experience_patterns):
                        match = re.search(pattern, file_text, re.IGNORECASE)
                        if match:
                            fallback_experience = f"{match.group(1)} years"
                            print(f"🎯 [ONBOARDING] FINAL FALLBACK SUCCESS - Pattern {i+1} found: '{fallback_experience}'")
                            update_data["experience"] = fallback_experience
                            break
                    else:
                        print(f"❌ [ONBOARDING] FINAL FALLBACK - No experience patterns found in file content")
                        # As absolute last resort, set a placeholder
                        print(f"🔧 [ONBOARDING] FINAL FALLBACK - Setting experience to '0 years'")
                        update_data["experience"] = "0 years"
            
            # ABSOLUTE FINAL CHECK - Ensure experience is NEVER null
            if "experience" not in update_data or not update_data["experience"]:
                print(f"🚨 [ONBOARDING] EMERGENCY FALLBACK - Experience still missing, forcing '0 years'")
                update_data["experience"] = "0 years"
            
            try:
                user_update = UserUpdate(**update_data)
                print(f"✅ [ONBOARDING] UserUpdate object created successfully")
                
                # DEBUG: Check skills after UserUpdate validation
                if hasattr(user_update, 'skills') and user_update.skills is not None:
                    print(f"🎯 [ONBOARDING] POST-VALIDATION - Skills type: {type(user_update.skills)}")
                    print(f"🎯 [ONBOARDING] POST-VALIDATION - Skills count: {len(user_update.skills)}")
                    if len(user_update.skills) > 0:
                        print(f"🎯 [ONBOARDING] POST-VALIDATION - First skill: {user_update.skills[0]}")
                else:
                    print(f"❌ [ONBOARDING] POST-VALIDATION - No skills in UserUpdate object!")
                    
            except Exception as validation_error:
                print(f"❌ [ONBOARDING] UserUpdate validation failed: {str(validation_error)}")
                print(f"❌ [ONBOARDING] Validation error type: {type(validation_error).__name__}")
                raise validation_error
            
            print(f"💾 [ONBOARDING] Updating user {current_user.id} in database...")
            await user_service.update_user(str(current_user.id), user_update)
            print(f"✅ [ONBOARDING] User updated successfully")
            
            # Determine response message based on QA results
            confidence_score = qa_verification.get("confidence_score", 0)
            qa_passed = qa_verification.get("passed", False)
            retry_attempted = qa_verification.get("retry_attempted", False)
            
            if qa_passed:
                if retry_attempted:
                    message = "Document processed successfully! We were able to extract comprehensive information from your resume."
                    user_message = "success_with_retry"
                else:
                    message = "Document processed successfully! Your profile is now complete with all extracted information."
                    user_message = "success"
            else:
                # Still allow user to proceed but inform about potential review needed
                message = "Document processed! Your profile has been created, though you may want to review and enhance some sections for completeness."
                user_message = "success_with_review_needed"
            
            response_data = {
                "success": True,
                "next_step": 2,
                "message": message,
                "onboarding_completed": False,
                "qa_info": {
                    "confidence_score": confidence_score,
                    "passed": qa_passed,
                    "retry_attempted": retry_attempted,
                    "user_message": user_message
                }
            }
            
            return response_data
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Document processing failed')
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [ONBOARDING] Exception during document upload: {str(e)}")
        print(f"❌ [ONBOARDING] Exception type: {type(e).__name__}")
        print(f"❌ [ONBOARDING] Exception details: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
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
            # Upload to S3 using file service
            profile_picture_url = await file_service.save_profile_picture(profile_picture, current_user.username)
            update_data["profile_picture"] = profile_picture_url
        
        # Update other profile fields
        if name:
            update_data["name"] = name
        if designation:
            update_data["designation"] = designation
        if location:
            update_data["location"] = location
        if summary:
            update_data["summary"] = summary
        if additional_info:
            update_data["additional_info"] = additional_info
        
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
        
        # Only add salary fields if they have values (not empty strings)
        if current_salary and current_salary.strip():
            update_data["current_salary"] = current_salary
        if expected_salary and expected_salary.strip():
            update_data["expected_salary"] = expected_salary
        

        
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

# Legacy endpoint kept for backward compatibility

@router.post("/upload-pdf")
async def upload_linkedin_pdf(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload and process document (Legacy endpoint - use /step-1/document-upload instead)"""
    
    # Validate file format - support PDF, Word documents
    supported_extensions = ['.pdf', '.docx', '.doc']
    file_extension = '.' + file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    
    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Supported formats: {', '.join(supported_extensions)}"
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
        
        # Save and process document
        file_path = await document_service.save_uploaded_document(file_content, unique_filename)
        result = await document_service.process_resume_document(file_path, file.filename)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
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
            # Upload to S3 using file service
            profile_picture_url = await file_service.save_profile_picture(profile_picture, current_user.username)
        
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