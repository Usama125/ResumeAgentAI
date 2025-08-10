from typing import List, Optional, Dict, Any
from app.models.user import UserInDB, Skill, Experience, Project, Education, Language, Award, Publication, VolunteerExperience, ContactInfo


class ProfileScoringService:
    """Service to calculate profile completeness and quality scores"""
    
    def __init__(self):
        # Scoring weights for different sections (total should add up to 100)
        self.weights = {
            'basic_info': 15,  # name, email, profession, location, summary
            'contact_info': 10,  # social links, phone
            'skills': 12,  # skills with levels
            'experience': 20,  # work experience
            'education': 12,  # educational background
            'projects': 15,  # personal/professional projects
            'certifications': 6,  # certificates
            'languages': 5,  # language skills
            'additional_sections': 5  # awards, publications, volunteer, interests
        }
    
    def calculate_profile_score(self, user: UserInDB) -> int:
        """Calculate comprehensive profile score based on completeness and quality"""
        total_score = 0
        
        # Basic Information Score (15 points)
        total_score += self._calculate_basic_info_score(user)
        
        # Contact Information Score (10 points)
        total_score += self._calculate_contact_info_score(user)
        
        # Skills Score (12 points)
        total_score += self._calculate_skills_score(user)
        
        # Experience Score (20 points)
        total_score += self._calculate_experience_score(user)
        
        # Education Score (12 points)
        total_score += self._calculate_education_score(user)
        
        # Projects Score (15 points)
        total_score += self._calculate_projects_score(user)
        
        # Certifications Score (6 points)
        total_score += self._calculate_certifications_score(user)
        
        # Languages Score (5 points)
        total_score += self._calculate_languages_score(user)
        
        # Additional Sections Score (5 points)
        total_score += self._calculate_additional_sections_score(user)
        
        return min(100, max(0, round(total_score)))
    
    def _calculate_basic_info_score(self, user: UserInDB) -> float:
        """Calculate score for basic profile information"""
        score = 0
        max_score = self.weights['basic_info']
        
        # Name (required) - 2 points
        if user.name and len(user.name.strip()) > 0:
            score += 2
        
        # Email (required) - 2 points
        if user.email:
            score += 2
        
        # Profession/Designation - 3 points
        if user.profession or user.designation:
            score += 3
        
        # Location - 2 points
        if user.location and len(user.location.strip()) > 0:
            score += 2
        
        # Summary/Bio - 4 points (quality based on length)
        if user.summary and len(user.summary.strip()) > 0:
            summary_length = len(user.summary.strip())
            if summary_length >= 100:  # Good detailed summary
                score += 4
            elif summary_length >= 50:  # Decent summary
                score += 3
            elif summary_length >= 20:  # Basic summary
                score += 2
            else:  # Too short
                score += 1
        
        # Profile picture - 2 points
        if user.profile_picture or user.profile_picture_url:
            score += 2
        
        return min(max_score, score)
    
    def _calculate_contact_info_score(self, user: UserInDB) -> float:
        """Calculate score for contact information completeness"""
        score = 0
        max_score = self.weights['contact_info']
        
        if not user.contact_info:
            return 0
        
        contact_fields = [
            user.contact_info.phone,
            user.contact_info.linkedin,
            user.contact_info.github,
            user.contact_info.portfolio,
            user.contact_info.website,
            user.contact_info.twitter
        ]
        
        filled_fields = sum(1 for field in contact_fields if field and len(field.strip()) > 0)
        
        # Award points based on number of contact methods
        if filled_fields >= 4:
            score = max_score
        elif filled_fields >= 3:
            score = max_score * 0.8
        elif filled_fields >= 2:
            score = max_score * 0.6
        elif filled_fields >= 1:
            score = max_score * 0.4
        
        return score
    
    def _calculate_skills_score(self, user: UserInDB) -> float:
        """Calculate score for skills section"""
        score = 0
        max_score = self.weights['skills']
        
        if not user.skills:
            return 0
        
        skills_count = len(user.skills)
        skills_with_levels = sum(1 for skill in user.skills if skill.level and skill.level != "")
        skills_with_years = sum(1 for skill in user.skills if skill.years and skill.years > 0)
        
        # Base score for having skills
        if skills_count >= 8:
            score += max_score * 0.4
        elif skills_count >= 5:
            score += max_score * 0.3
        elif skills_count >= 3:
            score += max_score * 0.2
        elif skills_count >= 1:
            score += max_score * 0.1
        
        # Additional score for skill levels
        if skills_with_levels >= skills_count * 0.8:  # 80% have levels
            score += max_score * 0.3
        elif skills_with_levels >= skills_count * 0.5:  # 50% have levels
            score += max_score * 0.2
        elif skills_with_levels > 0:
            score += max_score * 0.1
        
        # Additional score for experience years
        if skills_with_years >= skills_count * 0.6:  # 60% have years
            score += max_score * 0.3
        elif skills_with_years >= skills_count * 0.3:  # 30% have years
            score += max_score * 0.2
        elif skills_with_years > 0:
            score += max_score * 0.1
        
        return min(max_score, score)
    
    def _calculate_experience_score(self, user: UserInDB) -> float:
        """Calculate score for work experience"""
        score = 0
        max_score = self.weights['experience']
        
        if not user.experience_details:
            return 0
        
        experience_count = len(user.experience_details)
        detailed_experiences = sum(1 for exp in user.experience_details 
                                 if exp.description and len(exp.description.strip()) > 50)
        experiences_with_dates = sum(1 for exp in user.experience_details 
                                   if exp.start_date or exp.duration)
        
        # Base score for having experience entries
        if experience_count >= 3:
            score += max_score * 0.4
        elif experience_count >= 2:
            score += max_score * 0.3
        elif experience_count >= 1:
            score += max_score * 0.2
        
        # Additional score for detailed descriptions
        if detailed_experiences >= experience_count * 0.8:
            score += max_score * 0.4
        elif detailed_experiences >= experience_count * 0.5:
            score += max_score * 0.3
        elif detailed_experiences > 0:
            score += max_score * 0.2
        
        # Additional score for dates/duration
        if experiences_with_dates >= experience_count * 0.8:
            score += max_score * 0.2
        elif experiences_with_dates > 0:
            score += max_score * 0.1
        
        return min(max_score, score)
    
    def _calculate_education_score(self, user: UserInDB) -> float:
        """Calculate score for education section"""
        score = 0
        max_score = self.weights['education']
        
        if not user.education:
            return 0
        
        education_count = len(user.education)
        detailed_education = sum(1 for edu in user.education 
                               if edu.degree and edu.field_of_study)
        education_with_dates = sum(1 for edu in user.education 
                                 if edu.start_date or edu.end_date)
        
        # Base score for having education entries
        if education_count >= 2:
            score += max_score * 0.5
        elif education_count >= 1:
            score += max_score * 0.4
        
        # Additional score for detailed information
        if detailed_education >= education_count * 0.8:
            score += max_score * 0.3
        elif detailed_education > 0:
            score += max_score * 0.2
        
        # Additional score for dates
        if education_with_dates >= education_count * 0.8:
            score += max_score * 0.2
        elif education_with_dates > 0:
            score += max_score * 0.1
        
        return min(max_score, score)
    
    def _calculate_projects_score(self, user: UserInDB) -> float:
        """Calculate score for projects section"""
        score = 0
        max_score = self.weights['projects']
        
        if not user.projects:
            return 0
        
        projects_count = len(user.projects)
        detailed_projects = sum(1 for proj in user.projects 
                              if proj.description and len(proj.description.strip()) > 30)
        projects_with_tech = sum(1 for proj in user.projects 
                               if proj.technologies and len(proj.technologies) > 0)
        projects_with_links = sum(1 for proj in user.projects 
                                if proj.url or proj.github_url)
        
        # Base score for having projects
        if projects_count >= 3:
            score += max_score * 0.4
        elif projects_count >= 2:
            score += max_score * 0.3
        elif projects_count >= 1:
            score += max_score * 0.2
        
        # Additional score for detailed descriptions
        if detailed_projects >= projects_count * 0.8:
            score += max_score * 0.3
        elif detailed_projects > 0:
            score += max_score * 0.2
        
        # Additional score for technologies
        if projects_with_tech >= projects_count * 0.8:
            score += max_score * 0.2
        elif projects_with_tech > 0:
            score += max_score * 0.1
        
        # Additional score for links (URLs/GitHub)
        if projects_with_links >= projects_count * 0.6:
            score += max_score * 0.1
        
        return min(max_score, score)
    
    def _calculate_certifications_score(self, user: UserInDB) -> float:
        """Calculate score for certifications"""
        score = 0
        max_score = self.weights['certifications']
        
        if not user.certifications:
            return 0
        
        cert_count = len(user.certifications)
        
        if cert_count >= 5:
            score = max_score
        elif cert_count >= 3:
            score = max_score * 0.8
        elif cert_count >= 2:
            score = max_score * 0.6
        elif cert_count >= 1:
            score = max_score * 0.4
        
        return score
    
    def _calculate_languages_score(self, user: UserInDB) -> float:
        """Calculate score for languages section"""
        score = 0
        max_score = self.weights['languages']
        
        if not user.languages:
            return 0
        
        languages_count = len(user.languages)
        languages_with_proficiency = sum(1 for lang in user.languages 
                                       if lang.proficiency and lang.proficiency != "")
        
        # Base score for having languages
        if languages_count >= 3:
            score += max_score * 0.6
        elif languages_count >= 2:
            score += max_score * 0.4
        elif languages_count >= 1:
            score += max_score * 0.3
        
        # Additional score for proficiency levels
        if languages_with_proficiency >= languages_count * 0.8:
            score += max_score * 0.4
        elif languages_with_proficiency > 0:
            score += max_score * 0.2
        
        return min(max_score, score)
    
    def _calculate_additional_sections_score(self, user: UserInDB) -> float:
        """Calculate score for additional sections (awards, publications, volunteer, interests)"""
        score = 0
        max_score = self.weights['additional_sections']
        
        sections_completed = 0
        
        # Awards
        if user.awards and len(user.awards) > 0:
            sections_completed += 1
        
        # Publications
        if user.publications and len(user.publications) > 0:
            sections_completed += 1
        
        # Volunteer Experience
        if user.volunteer_experience and len(user.volunteer_experience) > 0:
            sections_completed += 1
        
        # Interests
        if user.interests and len(user.interests) > 0:
            sections_completed += 1
        
        # Award points based on number of additional sections
        if sections_completed >= 3:
            score = max_score
        elif sections_completed >= 2:
            score = max_score * 0.7
        elif sections_completed >= 1:
            score = max_score * 0.4
        
        return score
    
    def get_profile_analysis(self, user: UserInDB) -> Dict[str, Any]:
        """Get detailed profile analysis for strengths and weaknesses"""
        analysis = {
            'score': self.calculate_profile_score(user),
            'strengths': [],
            'weaknesses': [],
            'section_scores': {}
        }
        
        # Calculate individual section scores
        analysis['section_scores'] = {
            'basic_info': self._calculate_basic_info_score(user),
            'contact_info': self._calculate_contact_info_score(user),
            'skills': self._calculate_skills_score(user),
            'experience': self._calculate_experience_score(user),
            'education': self._calculate_education_score(user),
            'projects': self._calculate_projects_score(user),
            'certifications': self._calculate_certifications_score(user),
            'languages': self._calculate_languages_score(user),
            'additional_sections': self._calculate_additional_sections_score(user)
        }
        
        # Identify strengths (sections scoring >80% of max)
        for section, score in analysis['section_scores'].items():
            max_possible = self.weights[section]
            percentage = (score / max_possible) * 100 if max_possible > 0 else 0
            
            if percentage >= 80:
                analysis['strengths'].append(self._get_section_strength_message(section, percentage))
            elif percentage < 50:
                analysis['weaknesses'].append(self._get_section_weakness_message(section, user))
        
        return analysis
    
    def _get_section_strength_message(self, section: str, percentage: float) -> str:
        """Get strength message for a well-completed section"""
        messages = {
            'basic_info': f"Complete profile information with strong personal summary ({percentage:.0f}%)",
            'contact_info': f"Comprehensive contact information provided ({percentage:.0f}%)",
            'skills': f"Well-detailed skills section with levels and experience ({percentage:.0f}%)",
            'experience': f"Detailed work experience with comprehensive descriptions ({percentage:.0f}%)",
            'education': f"Complete educational background information ({percentage:.0f}%)",
            'projects': f"Impressive project portfolio with detailed descriptions ({percentage:.0f}%)",
            'certifications': f"Strong certification portfolio ({percentage:.0f}%)",
            'languages': f"Multiple language proficiencies documented ({percentage:.0f}%)",
            'additional_sections': f"Enhanced profile with awards, publications, or volunteer work ({percentage:.0f}%)"
        }
        return messages.get(section, f"Strong {section} section ({percentage:.0f}%)")
    
    def _get_section_weakness_message(self, section: str, user: UserInDB) -> str:
        """Get improvement suggestion for weak sections"""
        messages = {
            'basic_info': "Add a compelling professional summary and ensure all basic information is complete",
            'contact_info': "Add more contact methods like LinkedIn, GitHub, or portfolio links",
            'skills': "Add more skills with experience levels and years of experience",
            'experience': "Add detailed job descriptions and ensure all positions have complete information",
            'education': "Include degree, field of study, and dates for educational background",
            'projects': "Add more projects with detailed descriptions, technologies used, and links",
            'certifications': "Add professional certifications to showcase expertise",
            'languages': "Include language skills with proficiency levels",
            'additional_sections': "Consider adding awards, publications, volunteer experience, or interests"
        }
        return messages.get(section, f"Improve your {section} section")