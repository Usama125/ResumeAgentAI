import json
import logging
import openai
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def _parse_json_response(self, response_content: str, default_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Robust JSON parsing with error handling and fixes"""
        try:
            result = response_content.strip()
            
            # Clean up various markdown formats
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            elif result.startswith("```"):
                result = result.replace("```", "").strip()
            
            # Try to extract JSON from the response if it's wrapped in text
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                result = json_match.group()
            
            # First attempt at parsing
            try:
                return json.loads(result)
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON decode error: {str(json_error)}")
                logger.warning(f"Raw result: {result[:500]}...")
                
                # Try to fix common JSON issues
                try:
                    # Fix trailing commas and other common issues
                    fixed_result = re.sub(r',(\s*[}\]])', r'\1', result)  # Remove trailing commas
                    fixed_result = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', fixed_result)  # Quote unquoted keys
                    
                    # Try to fix incomplete JSON by finding the last complete object
                    if not fixed_result.strip().endswith('}') and not fixed_result.strip().endswith(']'):
                        # Find the last complete object or array
                        brace_count = 0
                        last_complete = 0
                        for i, char in enumerate(fixed_result):
                            if char == '{' or char == '[':
                                brace_count += 1
                            elif char == '}' or char == ']':
                                brace_count -= 1
                                if brace_count == 0:
                                    last_complete = i + 1
                        
                        if last_complete > 0:
                            fixed_result = fixed_result[:last_complete]
                    
                    return json.loads(fixed_result)
                except Exception as fix_error:
                    # If JSON is still malformed, try to extract data manually
                    logger.warning(f"JSON fix failed: {str(fix_error)}")
                    logger.warning(f"Attempting manual extraction from: {result[:200]}...")
                    
                    # Try to extract skills manually using regex
                    if "skills" in default_structure:
                        skills = []
                        skill_patterns = [
                            r'"name":\s*"([^"]+)"[^}]*"level":\s*"([^"]+)"[^}]*"years":\s*(\d+)',
                            r'"name":\s*"([^"]+)"'
                        ]
                        
                        for pattern in skill_patterns:
                            matches = re.findall(pattern, result)
                            for match in matches:
                                if len(match) == 3:
                                    skills.append({
                                        "name": match[0],
                                        "level": match[1],
                                        "years": int(match[2]) if match[2].isdigit() else 0
                                    })
                                elif len(match) == 1:
                                    skills.append({
                                        "name": match[0],
                                        "level": "Intermediate",
                                        "years": 0
                                    })
                            if skills:
                                break
                        
                        if skills:
                            logger.info(f"Manual extraction successful: found {len(skills)} skills")
                            return {"skills": skills}
                    
                    # Return default structure if all fails
                    logger.error(f"Could not parse JSON, returning default structure")
                    return default_structure
                    
        except Exception as e:
            logger.error(f"Error in JSON response parsing: {str(e)}")
            return default_structure

    async def process_resume_content(self, resume_content: str, user_id: str = None) -> Dict[str, Any]:
        """Process resume content using 8 specialized agents with quality assurance verification"""
        try:
            logger.info("Starting comprehensive multi-section extraction...")
            
            # Track AI resume processing for onboarding
            try:
                from app.services.analytics_service import get_analytics_service
                from app.models.admin import ActionType
                from app.database import get_database
                
                # Get database instance
                async for db in get_database():
                    analytics = get_analytics_service(db)
                    await analytics.track_action(
                        action_type=ActionType.AI_RESUME_ANALYSIS,
                        user_id=user_id,
                        username=None,  # User may not have username yet during onboarding
                        details={
                            "processing_type": "onboarding_extraction",
                            "content_length": len(resume_content),
                            "agent_count": 8
                        },
                        ip_address="server",
                        user_agent="onboarding_service"
                    )
                    break
            except Exception as tracking_error:
                logger.error(f"Analytics tracking failed: {str(tracking_error)}")
            
            # Import progress update function
            from app.routers.websocket import send_progress_update
            
            if user_id:
                await send_progress_update(user_id, "initialization", 5, "Starting AI extraction...", "Preparing 8 specialized agents")
            
            # Initialize result structure
            result = {
                "name": None,
                "designation": None,
                "location": None,
                "summary": None,
                "profession": None,
                "experience": None,
                "skills": [],
                "experience_details": [],
                "projects": [],
                "education": [],
                "certifications": [],
                "languages": [],
                "awards": [],
                "publications": [],
                "volunteer_experience": [],
                "interests": [],
                "contact_info": {}
            }
            
            # Agent 1: Personal Info & Contact
            logger.info("Agent 1: Extracting personal info and contact details...")
            if user_id:
                await send_progress_update(user_id, "agent_1", 15, "Extracting personal information...", "Name, designation, location, and contact details")
            
            personal_data = await self._extract_personal_info(resume_content)
            if personal_data and not personal_data.get("error"):
                result.update({
                    "name": personal_data.get("name"),
                    "designation": personal_data.get("designation"),
                    "location": personal_data.get("location"),
                    "summary": personal_data.get("summary"),
                    "profession": personal_data.get("profession"),
                    "contact_info": personal_data.get("contact_info", {})
                })
            
            # Agent 2: Work Experience & Experience Calculation
            logger.info("Agent 2: Extracting work experience and calculating total experience...")
            if user_id:
                await send_progress_update(user_id, "agent_2", 25, "Extracting work experience...", "Job history and calculating total experience")
            
            experience_data = await self._extract_experience(resume_content)
            if experience_data and not experience_data.get("error"):
                result["experience_details"] = experience_data.get("experience_details", [])
                
                # First try to use direct experience from resume text
                direct_experience = experience_data.get("total_experience_from_resume")
                if direct_experience and direct_experience.lower() != "null":
                    logger.info(f"🎯 EXPERIENCE DEBUG - Using direct experience from resume: {direct_experience}")
                    result["experience"] = direct_experience
                else:
                    # Try manual regex extraction for experience patterns
                    import re
                    logger.info(f"🎯 EXPERIENCE DEBUG - AI extraction returned null, trying manual regex patterns")
                    logger.info(f"🎯 EXPERIENCE DEBUG - Resume content preview: {resume_content[:500]}...")
                    
                    experience_patterns = [
                        r'Experience\s*[-–—:]\s*(\d+(?:\+|\.)?\d*)\s*years?',  # Experience - 6 years
                        r'Total\s*Experience\s*[-–—:]\s*(\d+(?:\+|\.)?\d*)\s*years?',
                        r'(\d+(?:\+|\.)?\d*)\s*years?\s*of\s*experience',
                        r'Over\s*(\d+(?:\+|\.)?\d*)\s*years?',
                        r'(\d+(?:\+|\.)?\d*)\+\s*years?',
                        r'(\d+(?:\+|\.)?\d*)\s*years?\s*experience',  # 6 years experience
                        r'Experience:\s*(\d+(?:\+|\.)?\d*)\s*years?',  # Experience: 6 years
                    ]
                    
                    manual_experience = None
                    for i, pattern in enumerate(experience_patterns):
                        match = re.search(pattern, resume_content, re.IGNORECASE)
                        if match:
                            manual_experience = f"{match.group(1)} years"
                            logger.info(f"🎯 EXPERIENCE DEBUG - Manual regex pattern {i+1} matched: '{pattern}' -> {manual_experience}")
                            break
                        else:
                            logger.info(f"🎯 EXPERIENCE DEBUG - Pattern {i+1} no match: '{pattern}'")
                    
                    if manual_experience:
                        result["experience"] = manual_experience
                        logger.info(f"🎯 EXPERIENCE DEBUG - Using manual regex result: {manual_experience}")
                    else:
                        # Fallback to calculation from job dates
                        logger.info(f"🎯 EXPERIENCE DEBUG - No manual regex matches found, calculating from job dates")
                        calculated_experience = self._calculate_total_experience(result["experience_details"])
                        if calculated_experience and calculated_experience != "0 years":
                            result["experience"] = calculated_experience
                        else:
                            # Final safety fallback - set a placeholder
                            logger.warning(f"🎯 EXPERIENCE DEBUG - All extraction methods failed, setting default")
                            result["experience"] = "0 years"
            
            # DEDICATED EXPERIENCE AGENT - Final attempt with specialized agent
            if not result.get("experience") or result.get("experience") in ["0 years", "null", None]:
                logger.info("🤖 Running DEDICATED EXPERIENCE AGENT as final attempt...")
                if user_id:
                    await send_progress_update(user_id, "agent_experience", 30, "Running dedicated experience agent...", "Specialized AI focusing only on experience extraction")
                
                dedicated_experience = await self._extract_experience_dedicated(resume_content)
                if dedicated_experience and dedicated_experience != "0 years":
                    result["experience"] = dedicated_experience
                    logger.info(f"🎯 DEDICATED EXPERIENCE AGENT SUCCESS - Final result: '{dedicated_experience}'")
            
            # Agent 3: Skills
            logger.info("Agent 3: Extracting skills...")
            if user_id:
                await send_progress_update(user_id, "agent_3", 35, "Extracting technical skills...", "Programming languages, frameworks, and technologies")
            
            skills_data = await self._extract_skills(resume_content)
            if skills_data and not skills_data.get("error"):
                result["skills"] = skills_data.get("skills", [])
            
            # Agent 4: Education
            logger.info("Agent 4: Extracting education...")
            if user_id:
                await send_progress_update(user_id, "agent_4", 45, "Extracting education...", "Degrees, institutions, and academic achievements")
            
            education_data = await self._extract_education(resume_content)
            if education_data and not education_data.get("error"):
                result["education"] = education_data.get("education", [])
            
            # Agent 5: Projects (comprehensive extraction)
            logger.info("Agent 5: Extracting all projects...")
            if user_id:
                await send_progress_update(user_id, "agent_5", 55, "Extracting projects...", "Work projects, personal projects, and portfolio items")
            
            projects_data = await self._extract_projects(resume_content)
            if projects_data and not projects_data.get("error"):
                result["projects"] = projects_data.get("projects", [])
            
            # Agent 6: Languages
            logger.info("Agent 6: Extracting languages...")
            if user_id:
                await send_progress_update(user_id, "agent_6", 65, "Extracting languages...", "Spoken languages and proficiency levels")
            
            languages_data = await self._extract_languages(resume_content)
            if languages_data and not languages_data.get("error"):
                result["languages"] = languages_data.get("languages", [])
            
            # Agent 7: Certifications & Additional Info
            logger.info("Agent 7: Extracting certifications, awards, and additional info...")
            if user_id:
                await send_progress_update(user_id, "agent_7", 75, "Extracting certifications & awards...", "Certifications, awards, publications, and interests")
            
            additional_data = await self._extract_additional_info(resume_content)
            if additional_data and not additional_data.get("error"):
                result.update({
                    "certifications": additional_data.get("certifications", []),
                    "awards": additional_data.get("awards", []),
                    "publications": additional_data.get("publications", []),
                    "volunteer_experience": additional_data.get("volunteer_experience", []),
                    "interests": additional_data.get("interests", [])
                })
            
            # Agent 8: Quality Assurance & Verification Agent
            logger.info("Agent 8: Starting quality assurance and verification...")
            if user_id:
                await send_progress_update(user_id, "agent_8", 85, "Quality assurance verification...", "Analyzing extraction quality and identifying missing sections")
            
            qa_result = await self._quality_assurance_agent(result, resume_content)
            
            # Apply any corrections suggested by QA agent first
            if qa_result.get("corrections"):
                logger.info("Applying QA corrections...")
                for field, corrected_value in qa_result.get("corrections", {}).items():
                    if corrected_value is not None:
                        result[field] = corrected_value
                        logger.info(f"Applied QA correction for {field}")

            # Check confidence level with 80% threshold
            confidence_score = qa_result.get("confidence_score", 0)
            
            if confidence_score >= 80:
                logger.info(f"✅ QA PASSED - Confidence: {confidence_score}%")
                result["qa_verification"] = {
                    "passed": True,
                    "confidence_score": confidence_score,
                    "completeness_score": qa_result.get("completeness_score"),
                    "accuracy_score": qa_result.get("accuracy_score"),
                    "missing_sections": qa_result.get("missing_sections", []),
                    "verification_notes": qa_result.get("verification_notes", ""),
                    "retry_attempted": False
                }
                
            else:
                logger.warning(f"⚠️ QA BELOW 80% - Confidence: {confidence_score}% - Attempting incremental retry...")
                
                # Attempt incremental extraction for missing sections only (ONE TIME ONLY)
                missing_sections = qa_result.get("missing_sections", [])
                if missing_sections:
                    logger.info(f"🔄 Starting incremental extraction for missing sections: {missing_sections}")
                    improved_result = await self._incremental_extraction_agent(result, resume_content, missing_sections)
                    
                    if improved_result and not improved_result.get("error"):
                        # Merge improved data without overwriting existing good data
                        result = self._merge_extraction_results(result, improved_result)
                        logger.info("✅ Incremental extraction completed")
                        
                        # Re-run QA on improved result
                        logger.info("🔄 Re-running QA after incremental extraction...")
                        final_qa_result = await self._quality_assurance_agent(result, resume_content)
                        final_confidence = final_qa_result.get("confidence_score", 0)
                        
                        if final_confidence >= 80:
                            logger.info(f"✅ QA PASSED after retry - Final Confidence: {final_confidence}%")
                            result["qa_verification"] = {
                                "passed": True,
                                "confidence_score": final_confidence,
                                "completeness_score": final_qa_result.get("completeness_score"),
                                "accuracy_score": final_qa_result.get("accuracy_score"),
                                "missing_sections": final_qa_result.get("missing_sections", []),
                                "verification_notes": final_qa_result.get("verification_notes", ""),
                                "retry_attempted": True,
                                "retry_successful": True,
                                "original_confidence": confidence_score
                            }
                        else:
                            logger.warning(f"⚠️ QA STILL BELOW 80% after retry - Final Confidence: {final_confidence}%")
                            result["qa_verification"] = {
                                "passed": False,
                                "confidence_score": final_confidence,
                                "completeness_score": final_qa_result.get("completeness_score"),
                                "accuracy_score": final_qa_result.get("accuracy_score"),
                                "missing_sections": final_qa_result.get("missing_sections", []),
                                "verification_notes": final_qa_result.get("verification_notes", ""),
                                "issues": final_qa_result.get("issues", []),
                                "retry_attempted": True,
                                "retry_successful": False,
                                "original_confidence": confidence_score
                            }
                    else:
                        logger.warning("❌ Incremental extraction failed")
                        result["qa_verification"] = {
                            "passed": False,
                            "confidence_score": confidence_score,
                            "completeness_score": qa_result.get("completeness_score"),
                            "accuracy_score": qa_result.get("accuracy_score"),
                            "missing_sections": missing_sections,
                            "verification_notes": qa_result.get("verification_notes", ""),
                            "issues": qa_result.get("issues", []),
                            "retry_attempted": True,
                            "retry_successful": False
                        }
                else:
                    logger.info("No missing sections identified for incremental extraction")
                    result["qa_verification"] = {
                        "passed": False,
                        "confidence_score": confidence_score,
                        "completeness_score": qa_result.get("completeness_score"),
                        "accuracy_score": qa_result.get("accuracy_score"),
                        "missing_sections": [],
                        "verification_notes": qa_result.get("verification_notes", ""),
                        "issues": qa_result.get("issues", []),
                        "retry_attempted": False
                    }
            
            logger.info("8-Agent extraction pipeline completed successfully")
            
            # Send completion update
            if user_id:
                from app.routers.websocket import send_completion_update
                qa_verification = result.get("qa_verification", {})
                confidence_score = qa_verification.get("confidence_score", 0)
                
                # Use the new function to determine truly missing sections based on actual data
                truly_missing_sections = self._determine_truly_missing_sections(result)
                
                await send_progress_update(user_id, "completion", 100, "Processing complete!", f"Extraction finished with {confidence_score}% confidence")
                await send_completion_update(user_id, True, confidence_score, truly_missing_sections)
            
            return self._clean_extracted_data(result)
            
        except Exception as e:
            logger.error(f"Error in multi-agent resume processing: {str(e)}")
            return {
                "error": "Failed to process resume content",
                "message": str(e)
            }

    async def _extract_experience_dedicated(self, resume_content: str) -> str:
        """Dedicated agent ONLY for extracting years of experience"""
        try:
            system_prompt = """You are a SPECIALIST agent that ONLY extracts total years of experience.

CRITICAL TASK: Find the TOTAL YEARS OF EXPERIENCE mentioned in this resume.

Look for these EXACT patterns:
- "Experience - 6 years" 
- "6 years of experience"
- "5+ years experience"
- "Over 4 years"
- "3 years in software development"
- "Total Experience: 6 years"
- "6 years experience"

INSTRUCTIONS:
1. Search the ENTIRE resume text for experience mentions
2. Return ONLY the number + "years" (e.g., "6 years", "5+ years")
3. If you find multiple mentions, use the HIGHEST number
4. If no direct mention found, calculate from job history dates
5. NEVER return null or empty

Return ONLY the experience in this format: "X years" where X is the number.
Examples: "6 years", "3 years", "5+ years", "0 years"

DO NOT return JSON. ONLY return the experience text."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ONLY the total years of experience from this resume:\n\n{resume_content}"}
                ],
                temperature=0,
                max_tokens=50  # Very small since we only need "X years"
            )

            result = response.choices[0].message.content.strip()
            logger.info(f"🎯 DEDICATED EXPERIENCE AGENT - Raw result: '{result}'")
            
            # Clean up the result - extract just the "X years" part
            import re
            experience_match = re.search(r'(\d+(?:\+|\.)?\d*)\s*years?', result, re.IGNORECASE)
            if experience_match:
                clean_experience = f"{experience_match.group(1)} years"
                logger.info(f"🎯 DEDICATED EXPERIENCE AGENT - Cleaned result: '{clean_experience}'")
                return clean_experience
            else:
                logger.warning(f"🎯 DEDICATED EXPERIENCE AGENT - Could not parse result, using raw: '{result}'")
                return result if result else "0 years"

        except Exception as e:
            logger.error(f"Error in dedicated experience extraction: {str(e)}")
            return "0 years"

    async def _extract_personal_info(self, resume_content: str) -> Dict[str, Any]:
        """Agent 1: Extract personal information and contact details"""
        try:
            system_prompt = """You are a personal information extraction specialist. Extract ONLY personal details and contact information.

            CRITICAL DESIGNATION CLEANING RULES:
            ❌ WRONG: "Senior Software Engineer (Backend Developer Nodejs) at Smash Cloud Pakistan"
            ✅ CORRECT: "Senior Software Engineer" 
            
            ❌ WRONG: "Backend Developer at Company Name"
            ✅ CORRECT: "Backend Developer"
            
            ❌ WRONG: "Full Stack Developer (React/Node.js) - Tech Company"
            ✅ CORRECT: "Full Stack Developer"

            FOCUS ON:
            1. **NAME**: Person's full name only (NO job titles, companies, or locations)
            2. **DESIGNATION**: CLEAN job title ONLY - remove everything in parentheses, remove company names, remove locations
            3. **LOCATION**: Real geographic location (city, country - NO company names)
            4. **SUMMARY**: Professional summary, objective, or about section
            5. **PROFESSION**: Primary field (e.g., "Software Engineer", "Data Scientist")
            6. **CONTACT INFO**: Extract ALL contact details including:
               - Email addresses
               - Phone numbers
               - LinkedIn profiles
               - GitHub profiles
               - Portfolio websites
               - Personal websites
               - Social media profiles
               - Any other contact links

            DESIGNATION EXTRACTION EXAMPLES:
            Input: "Senior Software Engineer (Backend Developer Nodejs) at Smash Cloud Pakistan"
            Output: "Senior Software Engineer"
            
            Input: "Full Stack Developer - React/Node.js at TechCorp"
            Output: "Full Stack Developer"
            
            Input: "Backend Developer (Node.js Specialist)"
            Output: "Backend Developer"

            Return JSON:
            {
              "name": "Full name only",
              "designation": "Clean job title only - no parentheses, no company names",
              "location": "Real geographic location",
              "summary": "Professional summary text",
              "profession": "Primary profession field",
              "contact_info": {
                "email": "email@example.com",
                "phone": "phone number",
                "linkedin": "LinkedIn URL",
                "github": "GitHub URL", 
                "portfolio": "Portfolio URL",
                "website": "Personal website URL",
                "twitter": "Twitter URL",
                "dribbble": "Dribbble URL",
                "behance": "Behance URL",
                "medium": "Medium URL",
                "instagram": "Instagram URL"
              }
            }"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract personal info and contact details:\n\n{resume_content}"}
                ],
                temperature=0.1,
                max_tokens=1500
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in personal info extraction: {str(e)}")
            return {"error": "Personal info extraction failed"}

    async def _extract_experience(self, resume_content: str) -> Dict[str, Any]:
        """Agent 2: Extract work experience with proper date parsing"""
        try:
            system_prompt = """You are a work experience extraction specialist. Extract ALL work experience details.

            CRITICAL: Extract EVERY job mentioned in the resume. Look for:
            - Current and past positions
            - Full-time, part-time, contract work
            - Internships and freelance work
            - Any work experience sections

            CRITICAL: Extract total experience directly from the resume first!
            Look for phrases like:
            - "Experience - 6 years"
            - "6 years of experience"
            - "5+ years experience" 
            - "Over 4 years"
            - "3 years in software development"
            - "Experience: 6 years"
            - "Total Experience - 6 years"
            
            For each position, extract:
            1. **COMPANY**: Company name only (NO locations, NO job titles)
            2. **POSITION**: Job title only (NO company names)
            3. **DURATION**: Full duration text (e.g., "Jul 2022 - Present")
            4. **START_DATE**: Start date (extract month/year)
            5. **END_DATE**: End date (null if current)
            6. **CURRENT**: true/false if currently working there
            7. **DESCRIPTION**: Complete job description

            Return JSON:
            {
              "total_experience_from_resume": "Extract exact experience text from resume (e.g., '6 years', '5+ years', 'Over 4 years') or null if not found",
              "experience_details": [
                {
                  "company": "Company name only",
                  "position": "Job title only",
                  "duration": "Jul 2022 - Present",
                  "start_date": "Jul 2022",
                  "end_date": null,
                  "current": true,
                  "description": "Complete job description with responsibilities and achievements"
                }
              ]
            }"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ALL work experience:\n\n{resume_content}"}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            result = response.choices[0].message.content
            parsed_result = self._parse_json_response(result, {"experience_details": []})
            
            # Debug logging for experience extraction
            if "experience_details" in parsed_result:
                experience_details = parsed_result["experience_details"]
                logger.info(f"🎯 EXPERIENCE DEBUG - Extracted {len(experience_details)} experiences")
                for i, exp in enumerate(experience_details[:3]):  # Log first 3
                    logger.info(f"   Experience {i+1}: {exp.get('company', 'N/A')} - {exp.get('position', 'N/A')} ({exp.get('duration', 'N/A')})")
            else:
                logger.warning(f"❌ EXPERIENCE DEBUG - No experience_details in parsed result")
                
            return parsed_result

        except Exception as e:
            logger.error(f"Error in experience extraction: {str(e)}")
            return {"error": "Experience extraction failed"}

    def _calculate_total_experience(self, experience_details: List[Dict]) -> str:
        """Calculate total experience from first job to present"""
        logger.info(f"🎯 EXPERIENCE CALC DEBUG - Input: {len(experience_details) if experience_details else 0} experiences")
        
        if not experience_details:
            logger.warning(f"❌ EXPERIENCE CALC DEBUG - No experience details provided")
            return "0 years"
        
        try:
            from datetime import datetime
            import re
            
            earliest_date = None
            latest_date = datetime.now()
            
            for exp in experience_details:
                start_date_str = exp.get("start_date", "")
                end_date_str = exp.get("end_date", "")
                
                # Parse start date
                if start_date_str:
                    try:
                        # Try different date formats
                        date_patterns = [
                            r'(\w+)\s+(\d{4})',  # "Jul 2022" 
                            r'(\d{1,2})/(\d{4})',  # "07/2022"
                            r'(\d{4})-(\d{1,2})',  # "2022-07"
                            r'(\d{4})'  # Just year
                        ]
                        
                        for pattern in date_patterns:
                            match = re.search(pattern, start_date_str)
                            if match:
                                if len(match.groups()) == 2:
                                    month_year = match.groups()
                                    if month_year[0].isdigit():
                                        year = int(match.group(1)) if match.group(1).isdigit() and len(match.group(1)) == 4 else int(match.group(2))
                                        month = int(match.group(2)) if match.group(2).isdigit() else 1
                                    else:
                                        # Month name
                                        year = int(month_year[1])
                                        month_map = {
                                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                                        }
                                        month = month_map.get(month_year[0][:3].lower(), 1)
                                else:
                                    year = int(match.group(1))
                                    month = 1
                                
                                start_date = datetime(year, month, 1)
                                if earliest_date is None or start_date < earliest_date:
                                    earliest_date = start_date
                                break
                    except:
                        continue
                
                # Parse end date
                if end_date_str and not exp.get("current", False):
                    try:
                        # Similar parsing for end date
                        for pattern in date_patterns:
                            match = re.search(pattern, end_date_str)
                            if match:
                                if len(match.groups()) == 2:
                                    month_year = match.groups()
                                    if month_year[0].isdigit():
                                        year = int(match.group(1)) if match.group(1).isdigit() and len(match.group(1)) == 4 else int(match.group(2))
                                        month = int(match.group(2)) if match.group(2).isdigit() else 12
                                    else:
                                        year = int(month_year[1])
                                        month_map = {
                                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                                        }
                                        month = month_map.get(month_year[0][:3].lower(), 12)
                                else:
                                    year = int(match.group(1))
                                    month = 12
                                
                                end_date = datetime(year, month, 1)
                                if end_date > latest_date:
                                    latest_date = end_date
                                break
                    except:
                        continue
            
            if earliest_date:
                total_months = (latest_date.year - earliest_date.year) * 12 + (latest_date.month - earliest_date.month)
                years = total_months // 12
                months = total_months % 12
                
                logger.info(f"🎯 EXPERIENCE CALC DEBUG - Earliest: {earliest_date}, Latest: {latest_date}")
                logger.info(f"🎯 EXPERIENCE CALC DEBUG - Total months: {total_months}, Years: {years}, Months: {months}")
                
                if years > 0 and months > 0:
                    result = f"{years}.{months} years"
                    logger.info(f"✅ EXPERIENCE CALC DEBUG - Result: {result}")
                    return result
                elif years > 0:
                    result = f"{years} years"
                    logger.info(f"✅ EXPERIENCE CALC DEBUG - Result: {result}")
                    return result
                else:
                    result = f"{months} months"
                    logger.info(f"✅ EXPERIENCE CALC DEBUG - Result: {result}")
                    return result
            
            logger.warning(f"❌ EXPERIENCE CALC DEBUG - No earliest date found, returning 0 years")
            return "0 years"
            
        except Exception as e:
            logger.error(f"Error calculating experience: {str(e)}")
            return "0 years"

    async def _extract_skills(self, resume_content: str) -> Dict[str, Any]:
        """Agent 3: Extract all skills and technologies"""
        try:
            system_prompt = """You are a skills extraction specialist. Extract ALL skills, technologies, and tools mentioned anywhere in the resume.

            EXTRACT EVERYTHING:
            - Programming languages
            - Frameworks and libraries
            - Databases
            - Tools and software
            - Cloud platforms
            - Methodologies
            - Soft skills
            - Domain expertise

            For each skill, provide:
            1. **NAME**: Individual skill/technology name
            2. **LEVEL**: Estimate proficiency level
            3. **YEARS**: Estimate years of experience (default 0 if unclear)

            Return JSON:
            {
              "skills": [
                {
                  "name": "Individual skill name",
                  "level": "Expert|Advanced|Intermediate|Beginner",
                  "years": 0
                }
              ]
            }"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ALL skills and technologies:\n\n{resume_content}"}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            result = response.choices[0].message.content
            return self._parse_json_response(result, {"skills": []})

        except Exception as e:
            logger.error(f"Error in skills extraction: {str(e)}")
            return {"error": "Skills extraction failed"}

    async def _extract_education(self, resume_content: str) -> Dict[str, Any]:
        """Agent 4: Extract education details"""
        try:
            system_prompt = """You are an education extraction specialist. Extract ALL educational qualifications, degrees, certifications, and academic achievements.

            EXTRACT EVERYTHING:
            - Universities and colleges
            - Degrees and diplomas
            - High school education
            - Online courses
            - Bootcamps
            - Academic achievements

            For each education entry:
            1. **INSTITUTION**: School/University name
            2. **DEGREE**: Degree or qualification type
            3. **FIELD_OF_STUDY**: Major/field of study
            4. **START_DATE**: Start year/date
            5. **END_DATE**: End year/date
            6. **GRADE**: GPA, percentage, or grade
            7. **ACTIVITIES**: Extracurricular activities
            8. **DESCRIPTION**: Additional details

            Return JSON:
            {
              "education": [
                {
                  "institution": "University/School name",
                  "degree": "Degree type",
                  "field_of_study": "Field of study",
                  "start_date": "Start year",
                  "end_date": "End year", 
                  "grade": "GPA/Grade",
                  "activities": "Activities",
                  "description": "Additional details"
                }
              ]
            }"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ALL education details:\n\n{resume_content}"}
                ],
                temperature=0.1,
                max_tokens=1500
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in education extraction: {str(e)}")
            return {"error": "Education extraction failed"}

    async def _extract_projects(self, resume_content: str) -> Dict[str, Any]:
        """Agent 5: Extract ALL projects comprehensively"""
        try:
            system_prompt = """You are a project extraction specialist. Extract EVERY project mentioned anywhere in the resume, regardless of where it appears.

            COMPREHENSIVE PROJECT SEARCH:
            - Look in dedicated "Projects" sections
            - Look in work experience descriptions
            - Look in portfolio sections
            - Look throughout the entire resume content
            - Extract personal projects, work projects, academic projects
            - Don't miss any project regardless of format or location

            For each project:
            1. **NAME**: Project name
            2. **DESCRIPTION**: Detailed project description
            3. **TECHNOLOGIES**: Array of technologies used
            4. **URL**: Project URL if available
            5. **GITHUB_URL**: GitHub repository URL if available
            6. **DURATION**: Project duration if mentioned

            Return JSON:
            {
              "projects": [
                {
                  "name": "Project name",
                  "description": "Detailed project description with features and accomplishments",
                  "technologies": ["tech1", "tech2", "tech3"],
                  "url": "Project URL",
                  "github_url": "GitHub URL",
                  "duration": "Duration"
                }
              ]
            }"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ALL projects from everywhere in the resume:\n\n{resume_content}"}
                ],
                temperature=0.1,
                max_tokens=3000
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in projects extraction: {str(e)}")
            return {"error": "Projects extraction failed"}

    async def _extract_languages(self, resume_content: str) -> Dict[str, Any]:
        """Agent 6: Extract language proficiencies"""
        try:
            system_prompt = """You are a language extraction specialist. Extract ALL languages mentioned in the resume.

            EXTRACT:
            - Native languages
            - Foreign languages learned
            - Programming languages (if in a languages section, not skills)
            - Language proficiency levels

            For each language:
            1. **NAME**: Language name
            2. **PROFICIENCY**: Proficiency level (use standard levels)

            Return JSON:
            {
              "languages": [
                {
                  "name": "Language name", 
                  "proficiency": "Native|Fluent|Advanced|Intermediate|Beginner"
                }
              ]
            }"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ALL languages:\n\n{resume_content}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in languages extraction: {str(e)}")
            return {"error": "Languages extraction failed"}

    async def _extract_additional_info(self, resume_content: str) -> Dict[str, Any]:
        """Agent 7: Extract certifications, awards, publications, and other info"""
        try:
            system_prompt = """You are a comprehensive additional information extraction specialist. Extract ALL additional information including:

            1. **CERTIFICATIONS**: All certificates, licenses, professional certifications
            2. **AWARDS**: All awards, honors, recognitions
            3. **PUBLICATIONS**: All publications, papers, articles, blogs
            4. **VOLUNTEER_EXPERIENCE**: All volunteer work and community service
            5. **INTERESTS**: All hobbies, interests, personal activities

            Return JSON:
            {
              "certifications": ["cert1", "cert2", "cert3"],
              "awards": [
                {
                  "title": "Award title",
                  "issuer": "Who gave the award",
                  "date": "When received",
                  "description": "Award details"
                }
              ],
              "publications": [
                {
                  "title": "Publication title",
                  "publisher": "Where published",
                  "date": "Publication date", 
                  "url": "URL if available",
                  "description": "Publication details"
                }
              ],
              "volunteer_experience": [
                {
                  "organization": "Organization name",
                  "role": "Volunteer role",
                  "start_date": "Start date",
                  "end_date": "End date",
                  "description": "What they did"
                }
              ],
              "interests": ["interest1", "interest2", "interest3"]
            }"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ALL additional information:\n\n{resume_content}"}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in additional info extraction: {str(e)}")
            return {"error": "Additional info extraction failed"}

    async def _quality_assurance_agent(self, extracted_data: Dict[str, Any], original_resume: str) -> Dict[str, Any]:
        """Agent 8: Quality Assurance & Verification Agent - Ensures 90%+ confidence before completion"""
        try:
            system_prompt = """You are a STRICT Quality Assurance specialist for resume data extraction. Your job is to verify the accuracy and completeness of extracted resume data and provide a confidence score. BE VERY STRICT - only high-quality extractions should score above 90%.

            QUALITY ASSURANCE CHECKLIST (BE STRICT):

            **1. COMPLETENESS VERIFICATION (40 points) - STRICT REQUIREMENTS:**
            - ✅ Personal Info: Name, designation, location, summary ALL present and meaningful (10 points) - DEDUCT 10 if ANY missing
            - ✅ Contact Info: Email, phone, and at least 2 other contact methods (5 points) - DEDUCT 5 if fewer than 4 contact fields
            - ✅ Work Experience: At least 2 complete work experiences with company, position, dates (10 points) - DEDUCT 5 per missing experience
            - ✅ Skills: At least 8 relevant technical skills extracted (5 points) - DEDUCT 3 if fewer than 8 skills
            - ✅ Education: At least 1 education entry with institution and degree (5 points) - DEDUCT 5 if missing
            - ✅ Additional Sections: Projects, languages, certifications if mentioned in resume (5 points) - DEDUCT 2 per missing section

            **2. ACCURACY VERIFICATION (40 points) - ZERO TOLERANCE:**
            - ✅ Name Accuracy: Clean name without job titles or companies (10 points) - DEDUCT 10 if contains job titles/companies
            - ✅ Designation Accuracy: Clean job title without company names or locations (10 points) - DEDUCT 10 if contains company info
            - ✅ Location Accuracy: Real geographic location, not company names (10 points) - DEDUCT 10 if fake/company location
            - ✅ Experience Calculation: Realistic total experience years matching work history (10 points) - DEDUCT 10 if unrealistic

            **3. FIELD MAPPING QUALITY (20 points) - STRICT VALIDATION:**
            - ✅ No Mixed Data: Job titles don't contain company info (5 points) - DEDUCT 5 if mixed
            - ✅ No Fake Locations: Locations are real places, not company names (5 points) - DEDUCT 5 if fake
            - ✅ Clean Skills: Individual skills, not sentences or descriptions (5 points) - DEDUCT 3 if contains sentences
            - ✅ Proper Formatting: Data properly structured and consistent (5 points) - DEDUCT 3 if poorly formatted

            **STRICT SCORING RULES:**
            - If name contains job titles: AUTOMATIC -10 points
            - If designation contains company names: AUTOMATIC -10 points  
            - If location is clearly a company name: AUTOMATIC -10 points
            - If skills are sentences instead of keywords: AUTOMATIC -5 points
            - If fewer than 5 total skills: AUTOMATIC -5 points
            - If no work experience: AUTOMATIC -15 points
            - If missing basic contact info (email/phone): AUTOMATIC -10 points

            **CRITICAL VALIDATION EXAMPLES:**

            ❌ **FAIL Examples (Deduct Points):**
            - Name: "John Doe Senior Engineer" (should be "John Doe")
            - Designation: "Software Engineer at TechCorp" (should be "Software Engineer")
            - Location: "Google California" (should be "California, USA")
            - Skills: ["Python programming with 5 years"] (should be ["Python"])

            ✅ **PASS Examples:**
            - Name: "John Doe"
            - Designation: "Software Engineer" 
            - Location: "San Francisco, California"
            - Skills: ["Python", "JavaScript", "React"]

            **MISSING SECTION DETECTION:**
            Compare the original resume with extracted data and identify what's missing.

            **CRITICAL VALIDATION EXAMPLES - BE STRICT:**

            ❌ **AUTOMATIC FAILURES (Score <90%):**
            - Name: "John Doe Senior Engineer" (contains job title)
            - Designation: "Software Engineer at TechCorp" (contains company)
            - Location: "Google California" (company name, not real location)
            - Skills: ["Python programming with 5 years experience"] (sentence, not skill)
            - Missing email or phone number
            - Fewer than 5 skills extracted
            - No work experience entries
            - No education information

            ✅ **PASS Examples (Score 90%+):**
            - Name: "John Doe" (clean name only)
            - Designation: "Software Engineer" (clean job title only)
            - Location: "San Francisco, California" (real geographic location)
            - Skills: ["Python", "JavaScript", "React"] (individual keywords)
            - At least 8 skills, 2+ work experiences, education, contact info

            **QUALITY THRESHOLDS:**
            - 95-100%: Perfect extraction, all sections complete, clean mapping
            - 85-94%: Good extraction, minor issues but acceptable quality  
            - 80-84%: Moderate quality, some issues but acceptable for production
            - 70-79%: Below average quality, needs incremental extraction retry
            - <70%: Poor quality, major issues, may need manual review

            **MISSING SECTIONS DETECTION:**
            Identify specific sections that are completely missing or have insufficient data:
            - "personal_info" - if name, designation, or location missing
            - "contact_info" - if fewer than 2 contact methods
            - "work_experience" - if no work experience entries
            - "skills" - if fewer than 5 skills
            - "education" - if no education entries
            - "projects" - if projects mentioned but not extracted
            - "languages" - if languages mentioned but not extracted
            - "certifications" - if certifications mentioned but not extracted
            - "awards" - if awards mentioned but not extracted
            - "publications" - if publications mentioned but not extracted
            - "volunteer_experience" - if volunteer work mentioned but not extracted
            - "interests" - if interests mentioned but not extracted

            **OUTPUT FORMAT:**
            Return JSON with exact scores and analysis:
            {
              "confidence_score": <0-100 total score>,
              "completeness_score": <0-40 points>,
              "accuracy_score": <0-40 points>,
              "field_mapping_score": <0-20 points>,
              "missing_sections": ["specific_sections_that_need_extraction"],
              "issues": [
                "Specific issue 1",
                "Specific issue 2"
              ],
              "corrections": {
                "designation": "corrected clean designation if needed",
                "location": "corrected real location if needed"
              },
              "verification_notes": "Detailed analysis explaining the confidence score"
            }

            REMEMBER: Scores 80% and above are acceptable. Be thorough in identifying missing sections for incremental extraction."""

            # Create a summary of what was extracted for comparison
            extracted_summary = {
                "name": extracted_data.get("name"),
                "designation": extracted_data.get("designation"),
                "location": extracted_data.get("location"),
                "experience": extracted_data.get("experience"),
                "skills_count": len(extracted_data.get("skills", [])),
                "experience_details_count": len(extracted_data.get("experience_details", [])),
                "education_count": len(extracted_data.get("education", [])),
                "projects_count": len(extracted_data.get("projects", [])),
                "languages_count": len(extracted_data.get("languages", [])),
                "certifications_count": len(extracted_data.get("certifications", [])),
                "contact_info_fields": len(extracted_data.get("contact_info", {})),
                "awards_count": len(extracted_data.get("awards", [])),
                "publications_count": len(extracted_data.get("publications", [])),
                "volunteer_count": len(extracted_data.get("volunteer_experience", [])),
                "interests_count": len(extracted_data.get("interests", []))
            }

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""
                    VERIFY THE QUALITY OF THIS EXTRACTION:

                    ORIGINAL RESUME (first 2000 chars):
                    {original_resume[:2000]}

                    EXTRACTED DATA SUMMARY:
                    {json.dumps(extracted_summary, indent=2)}

                    DETAILED EXTRACTED DATA:
                    {json.dumps(extracted_data, indent=2)[:3000]}

                    Provide a strict quality assessment with confidence score (must be 90+ to pass).
                    """}
                ],
                temperature=0.1,
                max_tokens=1500
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in quality assurance agent: {str(e)}")
            return {
                "confidence_score": 0,
                "completeness_score": 0,
                "accuracy_score": 0,
                "field_mapping_score": 0,
                "missing_sections": ["QA_AGENT_ERROR"],
                "issues": [f"Quality assurance failed: {str(e)}"],
                "corrections": {},
                "verification_notes": "Quality assurance agent encountered an error during verification"
            }

    async def _incremental_extraction_agent(self, existing_data: Dict[str, Any], resume_content: str, missing_sections: List[str]) -> Dict[str, Any]:
        """Incremental extraction agent - extracts only missing sections without disturbing existing data"""
        try:
            # Map missing sections to extraction functions
            section_mapping = {
                "personal_info": ["name", "designation", "location", "summary", "profession"],
                "contact_info": ["contact_info"],
                "work_experience": ["experience_details", "experience"],
                "skills": ["skills"],
                "education": ["education"],
                "projects": ["projects"],
                "languages": ["languages"],
                "certifications": ["certifications"],
                "awards": ["awards"],
                "publications": ["publications"],
                "volunteer_experience": ["volunteer_experience"],
                "interests": ["interests"]
            }

            system_prompt = f"""You are an incremental data extraction specialist. Your job is to extract ONLY the missing sections from a resume without disturbing already extracted data.

            MISSING SECTIONS TO EXTRACT: {missing_sections}

            CRITICAL INSTRUCTIONS:
            1. Focus ONLY on the missing sections listed above
            2. Extract comprehensive information for these sections only
            3. Return ONLY the fields that are missing - do not return existing data
            4. Be thorough and aggressive in extracting the requested sections
            5. If a section is not in the resume, return empty array/null for that field

            EXTRACTION RULES:
            - **personal_info**: Extract name, designation, location, summary, profession if missing
            - **contact_info**: Extract email, phone, LinkedIn, GitHub, portfolio, websites, social media
            - **work_experience**: Extract ALL job experiences with companies, positions, dates, descriptions
            - **skills**: Extract ALL technical and soft skills with levels and years
            - **education**: Extract ALL educational background with institutions, degrees, dates
            - **projects**: Extract ALL projects from anywhere in resume with descriptions and technologies
            - **languages**: Extract ALL languages with proficiency levels
            - **certifications**: Extract ALL certificates, licenses, credentials
            - **awards**: Extract ALL awards, honors, recognitions
            - **publications**: Extract ALL publications, articles, papers
            - **volunteer_experience**: Extract ALL volunteer work and community service
            - **interests**: Extract ALL hobbies, interests, personal activities

            Return JSON with ONLY the missing fields:
            {{
              // Only include fields that are in missing_sections
              "field_name": "extracted_data"
            }}

            Be comprehensive and don't miss any information for the requested sections."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ONLY these missing sections: {missing_sections}\n\nResume Content:\n{resume_content}"}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in incremental extraction agent: {str(e)}")
            return {"error": "Incremental extraction failed"}

    def _merge_extraction_results(self, existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge new extraction results with existing data without overwriting good data"""
        try:
            merged_result = existing_data.copy()
            
            for field, new_value in new_data.items():
                if field == "error":
                    continue
                    
                existing_value = existing_data.get(field)
                
                # Only update if existing data is empty/null/missing
                if field not in existing_data or existing_value is None or existing_value == "" or existing_value == []:
                    merged_result[field] = new_value
                    logger.info(f"Updated missing field: {field}")
                elif isinstance(existing_value, list) and len(existing_value) == 0:
                    merged_result[field] = new_value
                    logger.info(f"Updated empty list field: {field}")
                elif isinstance(existing_value, dict) and len(existing_value) == 0:
                    merged_result[field] = new_value
                    logger.info(f"Updated empty dict field: {field}")
                else:
                    # Keep existing data if it has content
                    logger.info(f"Preserved existing data for field: {field}")
            
            return merged_result
            
        except Exception as e:
            logger.error(f"Error merging extraction results: {str(e)}")
            return existing_data

    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize extracted data to prevent validation errors"""
        if not isinstance(data, dict):
            return data
            
        # Clean skills array
        if "skills" in data and isinstance(data["skills"], list):
            cleaned_skills = []
            for skill in data["skills"]:
                if isinstance(skill, dict) and "name" in skill:
                    cleaned_skill = {
                        "name": skill.get("name", ""),
                        "level": skill.get("level") or "Intermediate",
                        "years": skill.get("years") if isinstance(skill.get("years"), int) else 0
                    }
                    cleaned_skills.append(cleaned_skill)
                elif isinstance(skill, str):
                    # Handle simple string skills
                    cleaned_skills.append({
                        "name": skill,
                        "level": "Intermediate",
                        "years": 0
                    })
            data["skills"] = cleaned_skills
        
        # Clean experience_details array
        if "experience_details" in data and isinstance(data["experience_details"], list):
            cleaned_experience = []
            for exp in data["experience_details"]:
                if isinstance(exp, dict) and "company" in exp:
                    cleaned_exp = {
                        "company": exp.get("company", ""),
                        "position": exp.get("position", ""),
                        "duration": exp.get("duration", ""),
                        "description": exp.get("description") or "No description provided",
                        "start_date": exp.get("start_date"),
                        "end_date": exp.get("end_date"),
                        "current": exp.get("current", False)
                    }
                    cleaned_experience.append(cleaned_exp)
            data["experience_details"] = cleaned_experience
        
        # Clean projects array
        if "projects" in data and isinstance(data["projects"], list):
            cleaned_projects = []
            for proj in data["projects"]:
                if isinstance(proj, dict) and "name" in proj:
                    cleaned_proj = {
                        "name": proj.get("name", ""),
                        "description": proj.get("description") or "No description provided",
                        "technologies": proj.get("technologies", []),
                        "url": proj.get("url"),
                        "github_url": proj.get("github_url"),
                        "duration": proj.get("duration")
                    }
                    cleaned_projects.append(cleaned_proj)
            data["projects"] = cleaned_projects
        
        # Clean languages array
        if "languages" in data and isinstance(data["languages"], list):
            cleaned_languages = []
            valid_proficiencies = ["Native", "Fluent", "Advanced", "Intermediate", "Beginner"]
            
            for lang in data["languages"]:
                if isinstance(lang, dict) and "name" in lang:
                    proficiency = lang.get("proficiency", "Intermediate")
                    
                    # Map common variations to valid proficiencies
                    proficiency_mapping = {
                        "Native or Bilingual": "Native",
                        "Professional Working": "Advanced",
                        "Limited Proficiency": "Beginner",
                        "Full Professional": "Fluent",
                        "Elementary Proficiency": "Beginner"
                    }
                    
                    if proficiency in proficiency_mapping:
                        proficiency = proficiency_mapping[proficiency]
                    elif proficiency not in valid_proficiencies:
                        proficiency = "Intermediate"
                    
                    cleaned_lang = {
                        "name": lang.get("name", ""),
                        "proficiency": proficiency
                    }
                    cleaned_languages.append(cleaned_lang)
            data["languages"] = cleaned_languages
        
        # Ensure contact_info is properly structured
        if "contact_info" in data and data["contact_info"]:
            if not isinstance(data["contact_info"], dict):
                data["contact_info"] = {}
        
        # Clean other arrays to ensure they don't contain None values
        for field in ["education", "awards", "publications", "volunteer_experience", "interests", "certifications"]:
            if field in data and isinstance(data[field], list):
                data[field] = [item for item in data[field] if item is not None]
        
        return data

    def _determine_truly_missing_sections(self, user_data: Dict[str, Any]) -> List[str]:
        """Determine sections that have no data at all (empty arrays, null, or empty strings)"""
        missing_sections = []
        
        # Check personal info - if any of name, designation, location, summary are missing
        if not user_data.get("name") or not user_data.get("designation") or not user_data.get("location"):
            missing_sections.append("personal_info")
        
        # Check contact info - if fewer than 2 contact methods
        contact_info = user_data.get("contact_info", {})
        contact_fields = [v for v in contact_info.values() if v and v.strip()]
        if len(contact_fields) < 2:
            missing_sections.append("contact_info")
        
        # Check work experience - if no experience entries
        experience_details = user_data.get("experience_details", [])
        if not experience_details or len(experience_details) == 0:
            missing_sections.append("work_experience")
        
        # Check skills - if fewer than 3 skills
        skills = user_data.get("skills", [])
        if not skills or len(skills) < 3:
            missing_sections.append("skills")
        
        # Check education - if no education entries
        education = user_data.get("education", [])
        if not education or len(education) == 0:
            missing_sections.append("education")
        
        # Check projects - if no projects
        projects = user_data.get("projects", [])
        if not projects or len(projects) == 0:
            missing_sections.append("projects")
        
        # Check languages - if no languages
        languages = user_data.get("languages", [])
        if not languages or len(languages) == 0:
            missing_sections.append("languages")
        
        # Check certifications - if no certifications
        certifications = user_data.get("certifications", [])
        if not certifications or len(certifications) == 0:
            missing_sections.append("certifications")
        
        # Check awards - if no awards
        awards = user_data.get("awards", [])
        if not awards or len(awards) == 0:
            missing_sections.append("awards")
        
        # Check publications - if no publications
        publications = user_data.get("publications", [])
        if not publications or len(publications) == 0:
            missing_sections.append("publications")
        
        # Check volunteer experience - if no volunteer experience
        volunteer_experience = user_data.get("volunteer_experience", [])
        if not volunteer_experience or len(volunteer_experience) == 0:
            missing_sections.append("volunteer_experience")
        
        # Check interests - if no interests
        interests = user_data.get("interests", [])
        if not interests or len(interests) == 0:
            missing_sections.append("interests")
        
        return missing_sections

    # Keep the old method for backward compatibility
    async def process_linkedin_pdf_content(self, pdf_content: str) -> Dict[str, Any]:
        """Legacy method - use process_resume_content instead"""
        return await self.process_resume_content(pdf_content)

    async def generate_chat_response(self, user_profile: Dict[str, Any], user_message: str) -> str:
        """Generate AI chat response about the user's profile (max 3-4 lines)"""
        try:
            # Create context from user profile
            profile_context = f"""
            Name: {user_profile.get('name', 'N/A')}
            Role: {user_profile.get('designation', 'N/A')}
            Experience: {user_profile.get('experience', 'N/A')} years
            Skills: {', '.join([skill.get('name', '') for skill in user_profile.get('skills', [])])}
            Summary: {user_profile.get('summary', 'N/A')}
            """

            system_prompt = f"""You are an AI assistant helping recruiters learn about a candidate. 
            
            Candidate Profile:
            {profile_context}
            
            Rules:
            - Keep responses to maximum 3-4 lines
            - Be professional and informative
            - Focus on the candidate's qualifications and fit
            - If asked about skills, highlight relevant experience
            - If asked about projects, mention specific examples from their profile
            - Keep it concise and valuable for recruiters"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=150  # Limit tokens to ensure short responses
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return "I'm having trouble processing your question right now. Please try again later."

    def generate_suggestion_chips(self, user_profile: Dict[str, Any]) -> List[str]:
        """Generate contextual suggestion chips based on user's profile"""
        designation = user_profile.get('designation', '').lower()
        skills = [skill.get('name', '').lower() for skill in user_profile.get('skills', [])]
        
        # Default suggestions
        base_suggestions = [
            "Tell me about their experience",
            "What are their key skills?",
            "Are they suitable for this role?",
            "What projects have they worked on?"
        ]
        
        # Role-specific suggestions
        if any(term in designation for term in ['developer', 'engineer', 'programmer']):
            base_suggestions.extend([
                "What programming languages do they know?",
                "Do they have backend experience?",
                "What frameworks have they used?"
            ])
        elif any(term in designation for term in ['designer', 'ui', 'ux']):
            base_suggestions.extend([
                "What design tools do they use?",
                "Do they have UX experience?",
                "Can you show their portfolio?"
            ])
        elif any(term in designation for term in ['manager', 'lead', 'director']):
            base_suggestions.extend([
                "What teams have they managed?",
                "Do they have leadership experience?",
                "What's their management style?"
            ])
        
        # Skill-specific suggestions
        if any('react' in skill for skill in skills):
            base_suggestions.append("Tell me about their React experience")
        if any('python' in skill for skill in skills):
            base_suggestions.append("What Python projects have they done?")
        if any('node' in skill for skill in skills):
            base_suggestions.append("Do they have Node.js experience?")
        
        # Return up to 6 suggestions
        return base_suggestions[:6]

    async def analyze_professional_fit(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze professional suitability and fit for the candidate's profession.
        Provides brief, targeted analysis for employers and recruiters.
        """
        try:
            # Extract key profile information
            name = user_profile.get('name', 'Unknown')
            designation = user_profile.get('designation', '')
            profession = user_profile.get('profession', '')
            skills = user_profile.get('skills', [])
            experience_details = user_profile.get('experience_details', [])
            projects = user_profile.get('projects', [])
            education = user_profile.get('education', [])
            summary = user_profile.get('summary', '')
            
            # Determine the profession to analyze
            target_profession = profession or designation or 'professional'
            
            # Create a comprehensive prompt for professional analysis
            analysis_prompt = f"""
            You are an expert HR recruiter and career analyst. Analyze this candidate's professional profile and provide a brief, targeted assessment for employers and recruiters.

            CANDIDATE PROFILE:
            Name: {name}
            Current Role: {designation}
            Profession: {target_profession}
            
            Summary: {summary}
            
            Skills: {[skill.get('name', '') for skill in skills]}
            
            Experience: {len(experience_details)} positions
            {chr(10).join([f"- {exp.get('position', '')} at {exp.get('company', '')} ({exp.get('duration', '')})" for exp in experience_details[:3]])}
            
            Projects: {len(projects)} projects
            {chr(10).join([f"- {proj.get('name', '')}: {proj.get('description', '')[:100]}..." for proj in projects[:2]])}
            
            Education: {[edu.get('degree', '') for edu in education]}

            ANALYSIS REQUIREMENTS:
            1. Provide a brief professional assessment (2-3 sentences)
            2. List 3-4 key strengths relevant to their profession
            3. List 2-3 areas for improvement or concerns
            4. Give a professional fit score (1-10) with brief reasoning
            5. Provide hiring recommendation (Strong Yes/Yes/Maybe/No) with brief explanation

            Focus on:
            - Professional competence and expertise
            - Industry relevance and experience
            - Skill alignment with their profession
            - Career progression and growth potential
            - Red flags or concerns for employers

            Respond in JSON format:
            {{
                "professional_assessment": "Brief 2-3 sentence assessment",
                "key_strengths": ["strength1", "strength2", "strength3"],
                "areas_for_improvement": ["area1", "area2"],
                "professional_fit_score": 8,
                "fit_score_reasoning": "Brief explanation of the score",
                "hiring_recommendation": "Strong Yes/Yes/Maybe/No",
                "recommendation_reasoning": "Brief explanation of recommendation"
            }}
            """

            # Get AI response
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert HR recruiter and career analyst. Provide professional, objective assessments for employers and recruiters."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )

            # Parse the response
            response_content = response.choices[0].message.content
            analysis_result = self._parse_json_response(response_content, {
                "professional_assessment": "Professional analysis not available",
                "key_strengths": [],
                "areas_for_improvement": [],
                "professional_fit_score": 5,
                "fit_score_reasoning": "Analysis incomplete",
                "hiring_recommendation": "Maybe",
                "recommendation_reasoning": "Insufficient data for complete assessment"
            })

            return analysis_result

        except Exception as e:
            logger.error(f"Error in professional fit analysis: {str(e)}")
            return {
                "professional_assessment": "Unable to complete professional analysis at this time.",
                "key_strengths": ["Analysis temporarily unavailable"],
                "areas_for_improvement": ["Analysis temporarily unavailable"],
                "professional_fit_score": 5,
                "fit_score_reasoning": "Analysis could not be completed",
                "hiring_recommendation": "Maybe",
                "recommendation_reasoning": "Technical issues prevented complete assessment"
            }