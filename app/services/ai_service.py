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

    async def process_linkedin_pdf_content(self, pdf_content: str) -> Dict[str, Any]:
        """Process LinkedIn PDF content and return structured profile data"""
        try:
            system_prompt = """You are an expert resume parser. Extract structured information from the LinkedIn PDF content and return it as valid JSON.

            Extract the following information:
            - name: Full name
            - designation: Current job title/role
            - location: Current location
            - summary: Professional summary (2-3 sentences)
            - skills: Array of skills with estimated proficiency levels
            - experience_details: Work experience with company, position, duration, description
            - projects: Notable projects if mentioned
            - certifications: Any certifications or courses
            - experience: Total years of experience (estimated)

            Return only valid JSON without any markdown formatting."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract profile information from this LinkedIn content:\n\n{pdf_content}"}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            result = response.choices[0].message.content.strip()
            
            # Clean the response to ensure it's valid JSON
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error processing PDF content: {str(e)}")
            return {
                "error": "Failed to process PDF content",
                "message": str(e)
            }

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