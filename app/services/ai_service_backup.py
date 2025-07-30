import openai
from typing import Dict, List, Any
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    async def process_resume_content(self, resume_content: str) -> Dict[str, Any]:
        """Process resume content using a multi-agent approach for better accuracy"""
        try:
            # Step 1: Raw data extraction
            logger.info("Step 1: Starting raw data extraction...")
            raw_data = await self._extraction_agent(resume_content)
            
            if "error" in raw_data:
                return raw_data
            
            # Step 2: Intelligent field mapping
            logger.info("Step 2: Starting intelligent field mapping...")
            mapped_data = await self._mapping_agent(raw_data, resume_content)
            
            if "error" in mapped_data:
                return mapped_data
            
            # Step 3: Data validation and correction
            logger.info("Step 3: Starting data validation and correction...")
            validated_data = await self._validation_agent(mapped_data, resume_content)
            
            if "error" in validated_data:
                return validated_data
            
            # Final cleanup
            return self._clean_extracted_data(validated_data)
            
        except Exception as e:
            logger.error(f"Error in multi-agent resume processing: {str(e)}")
            return {
                "error": "Failed to process resume content",
                "message": str(e)
            }

    async def _extraction_agent(self, resume_content: str) -> Dict[str, Any]:
        """Agent 1: Raw data extraction - extracts everything without strict formatting"""
        try:
            system_prompt = """You are an expert data extraction agent. Your ONLY job is to extract ALL raw information from the resume without worrying about proper formatting or field mapping. Just gather everything you can find.

            Extract every piece of text, dates, names, companies, skills, technologies, education details, contact information, etc. Don't worry about categorization - just capture everything.

            Return a JSON with these raw sections:
            {
              "personal_info": {
                "raw_text": "all text that looks like name, title, summary, bio, objective",
                "contact_raw": "all email, phone, links, social media, addresses found anywhere"
              },
              "work_sections": [
                {
                  "section_heading": "exact heading found (e.g., Experience, Work History, etc.)",
                  "raw_content": "all text under this section exactly as written"
                }
              ],
              "education_sections": [
                {
                  "section_heading": "exact heading found (e.g., Education, Academic Background)",  
                  "raw_content": "all text under this section exactly as written"
                }
              ],
              "skills_sections": [
                {
                  "section_heading": "exact heading found (e.g., Skills, Technologies, Core Competencies)",
                  "raw_content": "all text under this section exactly as written"
                }
              ],
              "other_sections": [
                {
                  "section_heading": "heading name",
                  "raw_content": "content"
                }
              ]
            }

            Just extract - don't interpret or clean anything yet."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ALL raw information from this resume:\n\n{resume_content}"}
                ],
                temperature=0.1,
                max_tokens=2500
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in extraction agent: {str(e)}")
            return {"error": "Extraction failed", "message": str(e)}

    async def _mapping_agent(self, raw_data: Dict[str, Any], original_content: str) -> Dict[str, Any]:
        """Agent 2: Intelligent field mapping - maps raw data to proper structured fields"""
        try:
            system_prompt = """You are an intelligent field mapping specialist. Your job is to take raw extracted data and intelligently map it to proper structured fields.

            CRITICAL INTELLIGENCE RULES:
            1. **NAME**: Extract only the person's actual name, not job titles or company names
            2. **DESIGNATION/TITLE**: Extract clean job title only (e.g., "Senior Software Engineer" or "Backend Developer"), remove company names and locations  
            3. **LOCATION**: Extract only real geographic locations (city, state, country), ignore company names that sound like locations
            4. **COMPANIES**: Separate company names from job titles and locations
            5. **SKILLS**: Extract individual skills/technologies, not sentences or descriptions
            6. **EXPERIENCE CALCULATION**: Calculate total years from work history dates

            COMMON MAPPING ERRORS TO AVOID:
            - ❌ "Senior Software Engineer at ABC Company in New York" → designation should be "Senior Software Engineer" only
            - ❌ "Cloud Pakistan" → this is not a real location  
            - ❌ "Node.js developer with 5 years experience" → skill should be "Node.js" only
            - ❌ Including company names in job titles
            - ❌ Including locations in company names

            Map the raw data to this EXACT structure:
            {
              "name": "person's full name only",
              "designation": "clean job title only (e.g., Senior Software Engineer, Backend Developer)",
              "location": "real geographic location only (e.g., Gujranwala, Pakistan)",
              "profession": "primary profession field",
              "experience": "total years calculated from work history",
              "summary": "professional summary/objective",
              "skills": [
                {
                  "name": "individual skill/technology name",
                  "level": "Expert|Advanced|Intermediate|Beginner",
                  "years": 0
                }
              ],
              "experience_details": [
                {
                  "company": "company name only (e.g., SMASH CLOUD MEDIA)",
                  "position": "job title only (e.g., Senior Software Engineer)",
                  "duration": "time period",
                  "description": "job description",
                  "start_date": "start date",
                  "end_date": "end date",
                  "current": false
                }
              ],
              "education": [
                {
                  "institution": "school/university name only",
                  "degree": "degree name",
                  "field_of_study": "field of study",
                  "start_date": "start year",
                  "end_date": "end year",
                  "grade": "GPA/grade",
                  "activities": "activities",
                  "description": "additional details"
                }
              ],
              "contact_info": {
                "email": "email address",
                "phone": "phone number",
                "linkedin": "linkedin profile url",
                "github": "github profile url",
                "portfolio": "portfolio website",
                "website": "personal website"
              },
              "languages": [
                {
                  "name": "language name",
                  "proficiency": "Native|Fluent|Advanced|Intermediate|Beginner"
                }
              ],
              "projects": [],
              "certifications": [],
              "awards": [],
              "publications": [],
              "volunteer_experience": [],
              "interests": []
            }

            CRITICAL: Be very careful with location extraction. Real locations only!"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Intelligently map this raw data to structured fields:\n\nRaw Data: {json.dumps(raw_data, indent=2)}\n\nOriginal Resume (for context): {original_content[:1000]}..."}
                ],
                temperature=0.1,
                max_tokens=3000
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in mapping agent: {str(e)}")
            return {"error": "Mapping failed", "message": str(e)}

    async def _validation_agent(self, mapped_data: Dict[str, Any], original_content: str) -> Dict[str, Any]:
        """Agent 3: Data validation and correction - verifies accuracy and fixes errors"""
        try:
            system_prompt = """You are a data validation specialist. Your job is to review the mapped data and fix any obvious errors or inconsistencies.

            VALIDATION CHECK LIST:
            1. **NAME VALIDATION**: 
               - Should be person's actual name only
               - Remove any job titles, company names, locations
               - Example: ❌ "Muhammad Zaid Senior Software Engineer" → ✅ "Muhammad Zaid"

            2. **DESIGNATION VALIDATION**:
               - Should be clean job title only  
               - Remove company names and locations
               - Example: ❌ "Senior Software Engineer (Backend Developer Nodejs) at Smash Cloud Pakistan" → ✅ "Senior Software Engineer" or "Backend Developer"

            3. **LOCATION VALIDATION**:
               - Should be real geographic locations only
               - Remove company names that sound like locations
               - Example: ❌ "Cloud Pakistan" → ✅ "Gujranwala, Pakistan"
               - Example: ❌ "Smash Cloud Media Lahore" → ✅ "Lahore, Pakistan"

            4. **COMPANY VALIDATION**: 
               - Should be company names only
               - Remove locations and job titles
               - Example: ❌ "SMASH CLOUD MEDIA - Lahore, Pakistan" → ✅ "SMASH CLOUD MEDIA"

            5. **SKILLS VALIDATION**:
               - Should be individual technologies/skills only
               - Remove descriptions and sentences
               - Example: ❌ "Node.js developer with 5 years" → ✅ "Node.js"

            6. **EXPERIENCE CALCULATION**:
               - Calculate total experience from work history dates
               - Should be realistic number (0-50 years)

            7. **CONTACT INFO VALIDATION**:
               - Email should be valid email format
               - Phone should be clean phone number
               - URLs should be proper URLs

            Review the mapped data and fix any errors. Return the corrected data in the same JSON structure.

            If you find errors, fix them intelligently. If location data is completely wrong, try to extract the correct location from the original resume content."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Review and fix any errors in this mapped data:\n\nMapped Data: {json.dumps(mapped_data, indent=2)}\n\nOriginal Resume (for reference): {original_content[:1500]}..."}
                ],
                temperature=0.1,
                max_tokens=3000
            )

            result = response.choices[0].message.content.strip()
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in validation agent: {str(e)}")
            return {"error": "Validation failed", "message": str(e)}
            - "Certifications", "Certificates", "Professional Certifications", "Licenses", "Credentials", "Qualifications", etc.

            Your task is to intelligently extract and structure ALL information into this standardized JSON format:

            {
              "name": "Full name from anywhere in document",
              "designation": "Current job title/role",
              "location": "Current location",
              "summary": "Professional summary/objective/about section",
              "profession": "Primary profession field auto-detected from experience and title",
              "experience": "Total years of experience (calculate/estimate from work history)",
              "skills": [
                {
                  "name": "skill name",
                  "level": "Expert|Advanced|Intermediate|Beginner",
                  "years": 0
                }
              ],
              "experience_details": [
                {
                  "company": "company name",
                  "position": "job title",
                  "duration": "duration text",
                  "description": "job description",
                  "start_date": "start date if available",
                  "end_date": "end date if available",
                  "current": true/false
                }
              ],
              "projects": [
                {
                  "name": "project name",
                  "description": "project description",
                  "technologies": ["tech1", "tech2"],
                  "url": "project url if available",
                  "github_url": "github url if available",
                  "duration": "project duration if available"
                }
              ],
              "education": [
                {
                  "institution": "school/university name",
                  "degree": "degree type",
                  "field_of_study": "major/field",
                  "start_date": "start date",
                  "end_date": "end date",
                  "grade": "GPA/grade if available",
                  "activities": "activities if mentioned",
                  "description": "additional details"
                }
              ],
              "certifications": ["cert1", "cert2", "cert3"],
              "languages": [
                {
                  "name": "language name",
                  "proficiency": "Native|Fluent|Advanced|Intermediate|Beginner"
                }
              ],
              "awards": [
                {
                  "title": "award title",
                  "issuer": "who gave it",
                  "date": "when received",
                  "description": "award details"
                }
              ],
              "publications": [
                {
                  "title": "publication title",
                  "publisher": "where published",
                  "date": "publication date",
                  "url": "link if available",
                  "description": "publication details"
                }
              ],
              "volunteer_experience": [
                {
                  "organization": "org name",
                  "role": "volunteer role",
                  "start_date": "start date",
                  "end_date": "end date",
                  "description": "what they did"
                }
              ],
              "interests": ["interest1", "interest2", "interest3"],
              "contact_info": {
                "email": "email address",
                "phone": "phone number",
                "linkedin": "linkedin profile url",
                "github": "github profile url",
                "portfolio": "portfolio website",
                "website": "personal website",
                "twitter": "twitter handle/url",
                "dribbble": "dribbble profile",
                "behance": "behance profile",
                "medium": "medium profile",
                "instagram": "instagram handle",
                "facebook": "facebook profile",
                "youtube": "youtube channel"
              }
            }

            CRITICAL INSTRUCTIONS:
            1. Extract EVERY piece of information available - don't miss anything
            2. Be smart about grouping similar information regardless of section headings
            3. If information appears in multiple sections, consolidate intelligently
            4. Calculate/estimate years of experience from work history dates
            5. Auto-detect profession from job titles and experience
            6. Extract ALL contact information from anywhere in the document
            7. If data is missing, use null or empty arrays - never skip fields
            8. Be comprehensive and thorough - this is critical for user satisfaction

            Return ONLY valid JSON without markdown formatting."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ALL profile information from this resume content, being intelligent about different heading formats:\n\n{resume_content}"}
                ],
                temperature=0.1,  # Lower temperature for more consistent extraction
                max_tokens=3000  # Increased for comprehensive extraction
            )

            result = response.choices[0].message.content.strip()
            
            # Clean the response to ensure it's valid JSON
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            extracted_data = json.loads(result)
            
            # Clean and normalize the extracted data
            return self._clean_extracted_data(extracted_data)

        except Exception as e:
            logger.error(f"Error processing resume content: {str(e)}")
            return {
                "error": "Failed to process resume content",
                "message": str(e)
            }
    
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
            "Are they a good fit for senior roles?",
            "What's their technical background?"
        ]
        
        # Role-specific suggestions
        if any(term in designation for term in ['developer', 'engineer', 'programmer']):
            return [
                "What programming languages do they know?",
                "Tell me about their technical projects",
                "How many years of coding experience?",
                "Are they good with system design?"
            ]
        elif any(term in designation for term in ['manager', 'lead', 'director']):
            return [
                "What's their leadership style?",
                "How do they handle team management?",
                "Tell me about their strategic experience",
                "Are they good with stakeholder management?"
            ]
        elif any(term in designation for term in ['designer', 'ui', 'ux']):
            return [
                "What design tools do they use?",
                "Show me their design process",
                "Tell me about their portfolio",
                "How do they approach user research?"
            ]
        elif any(term in designation for term in ['marketing', 'growth', 'digital']):
            return [
                "What marketing channels do they know?",
                "Tell me about their campaign experience",
                "How do they measure ROI?",
                "Are they good with analytics?"
            ]
        
        return base_suggestions

    def analyze_job_match(self, user_profile: Dict[str, Any], job_query: str) -> Dict[str, Any]:
        """Analyze how well a user profile matches a job description using AI"""
        try:
            # Create comprehensive profile summary
            profile_summary = self._create_profile_summary(user_profile)
            
            system_prompt = """You are an expert HR analyst. Analyze how well a candidate matches a job description and return ONLY percentages.

            Provide analysis in this exact JSON format:
            {
                "overall_match": <percentage 0-100>,
                "skills_match": <percentage 0-100>,
                "experience_match": <percentage 0-100>,
                "location_match": <percentage 0-100>,
                "certification_match": <percentage 0-100>
            }

            Be objective and realistic. Consider:
            - Technical skills alignment
            - Experience level and years
            - Certifications and qualifications
            - Location preferences

            Return ONLY the JSON object, no explanations."""

            user_prompt = f"""
            CANDIDATE PROFILE:
            {profile_summary}
            
            JOB REQUIREMENT/SEARCH QUERY:
            {job_query}
            
            Analyze the match between this candidate and the job requirements."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=150  # Reduced tokens for percentage-only response
            )

            result = response.choices[0].message.content.strip()
            
            # Clean the response to ensure it's valid JSON
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            import json
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error analyzing job match: {str(e)}")
            return {
                "overall_match": 0.0,
                "skills_match": 0.0,
                "experience_match": 0.0,
                "location_match": 0.0,
                "certification_match": 0.0
            }

    def _create_profile_summary(self, user_profile: Dict[str, Any]) -> str:
        """Create a comprehensive profile summary for AI analysis"""
        
        # Extract key information
        name = user_profile.get('name', 'Unknown')
        designation = user_profile.get('designation', 'Not specified')
        location = user_profile.get('location', 'Not specified')
        experience = user_profile.get('experience', 'Not specified')
        summary = user_profile.get('summary', 'No summary provided')
        
        # Format skills
        skills = user_profile.get('skills', [])
        skills_text = ", ".join([f"{skill.get('name', '')} ({skill.get('level', 'Unknown')} - {skill.get('years', 0)} years)" 
                               for skill in skills])
        
        # Format experience details
        experience_details = user_profile.get('experience_details', [])
        experience_text = ""
        for exp in experience_details:
            experience_text += f"• {exp.get('position', '')} at {exp.get('company', '')} ({exp.get('duration', '')}): {exp.get('description', '')}\n"
        
        # Format projects
        projects = user_profile.get('projects', [])
        projects_text = ""
        for project in projects:
            tech_stack = ", ".join(project.get('technologies', []))
            projects_text += f"• {project.get('name', '')}: {project.get('description', '')} (Tech: {tech_stack})\n"
        
        # Format certifications
        certifications = user_profile.get('certifications', [])
        certifications_text = ", ".join(certifications) if certifications else "None"
        
        # Format work preferences
        work_prefs = user_profile.get('work_preferences', {})
        location_pref = work_prefs.get('preferred_location', 'Not specified')
        work_mode = ", ".join(work_prefs.get('preferred_work_mode', []))
        
        profile_summary = f"""
        Name: {name}
        Current Role: {designation}
        Location: {location}
        Experience: {experience}
        
        Professional Summary:
        {summary}
        
        Technical Skills:
        {skills_text}
        
        Work Experience:
        {experience_text}
        
        Key Projects:
        {projects_text}
        
        Certifications:
        {certifications_text}
        
        Work Preferences:
        - Preferred Location: {location_pref}
        - Work Mode: {work_mode}
        - Looking for Job: {user_profile.get('is_looking_for_job', 'Unknown')}
        """
        
        return profile_summary