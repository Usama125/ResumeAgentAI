from typing import List, Dict, Any, Optional
from algoliasearch.search.client import SearchClient
from app.config import settings
from app.models.user import UserInDB
import logging

logger = logging.getLogger(__name__)

class AlgoliaService:
    """Service to manage Algolia search index synchronization (Backend sync only)"""
    
    def __init__(self):
        self.client = SearchClient(
            settings.ALGOLIA_APPLICATION_ID,
            settings.ALGOLIA_API_KEY
        )
        self.index_name = settings.ALGOLIA_INDEX_NAME
    
    def _format_user_for_algolia(self, user: UserInDB) -> Dict[str, Any]:
        """Format user data for Algolia indexing with optimized searchable fields"""
        
        # Extract skills as searchable array
        skills = []
        if user.skills:
            for skill in user.skills:
                if skill.name:
                    skills.append(skill.name.lower())
                    # Add variations for common terms
                    skill_name = skill.name.lower()
                    if 'react' in skill_name and 'reactjs' not in skills:
                        skills.append('reactjs')
                    elif 'node' in skill_name and 'nodejs' not in skills:
                        skills.append('nodejs')
                    elif 'javascript' in skill_name and 'js' not in skills:
                        skills.append('js')
                    elif 'typescript' in skill_name and 'ts' not in skills:
                        skills.append('ts')
        
        # Extract experience details for search
        experience_companies = []
        experience_positions = []
        experience_descriptions = []
        
        if user.experience_details:
            for exp in user.experience_details:
                if exp.company:
                    experience_companies.append(exp.company.lower())
                if exp.position:
                    experience_positions.append(exp.position.lower())
                if exp.description:
                    experience_descriptions.append(exp.description.lower())
        
        # Extract project names and technologies
        project_names = []
        project_technologies = []
        project_descriptions = []
        
        if user.projects:
            for project in user.projects:
                if project.name:
                    project_names.append(project.name.lower())
                if project.technologies:
                    project_technologies.extend([tech.lower() for tech in project.technologies])
                if project.description:
                    project_descriptions.append(project.description.lower())
        
        # Extract education details
        education_institutions = []
        education_degrees = []
        education_fields = []
        
        if user.education:
            for edu in user.education:
                if edu.institution:
                    education_institutions.append(edu.institution.lower())
                if edu.degree:
                    education_degrees.append(edu.degree.lower())
                if edu.field_of_study:
                    education_fields.append(edu.field_of_study.lower())
        
        # Extract certifications
        certifications = []
        if user.certifications:
            certifications = [cert.lower() for cert in user.certifications if cert]
        
        # Extract languages
        languages = []
        if user.languages:
            languages = [lang.name.lower() for lang in user.languages if lang.name]
        
        # Extract interests
        interests = []
        if user.interests:
            interests = [interest.lower() for interest in user.interests if interest]
        
        # Contact info for search
        contact_links = []
        if user.contact_info:
            if user.contact_info.linkedin:
                contact_links.append('linkedin')
            if user.contact_info.github:
                contact_links.append('github')
            if user.contact_info.portfolio:
                contact_links.append('portfolio')
            if user.contact_info.website:
                contact_links.append('website')
        
        # Create comprehensive searchable text
        searchable_text_parts = []
        
        # Add basic info
        if user.name:
            searchable_text_parts.append(user.name.lower())
        if user.username:
            searchable_text_parts.append(user.username.lower())
        if user.email:
            searchable_text_parts.append(user.email.lower())
        if user.designation:
            searchable_text_parts.append(user.designation.lower())
        if user.profession:
            searchable_text_parts.append(user.profession.lower())
        if user.location:
            searchable_text_parts.append(user.location.lower())
        if user.summary:
            searchable_text_parts.append(user.summary.lower())
        
        # Add all extracted arrays
        searchable_text_parts.extend(skills)
        searchable_text_parts.extend(experience_companies)
        searchable_text_parts.extend(experience_positions)
        searchable_text_parts.extend(project_names)
        searchable_text_parts.extend(project_technologies)
        searchable_text_parts.extend(education_institutions)
        searchable_text_parts.extend(education_degrees)
        searchable_text_parts.extend(education_fields)
        searchable_text_parts.extend(certifications)
        searchable_text_parts.extend(languages)
        searchable_text_parts.extend(interests)
        
        # Create the Algolia record
        algolia_record = {
            'objectID': str(user.id),  # Required by Algolia
            'user_id': str(user.id),
            'name': user.name or '',
            'username': user.username or '',
            'email': user.email or '',
            'designation': user.designation or '',
            'profession': user.profession or '',
            'location': user.location or '',
            'summary': user.summary or '',
            'experience': user.experience or '',
            'is_looking_for_job': user.is_looking_for_job or False,
            'profile_picture': user.profile_picture or user.profile_picture_url or '',
            'rating': user.rating or 4.5,
            'profile_score': getattr(user, 'profile_score', 0),
            
            # Searchable arrays
            'skills': skills,
            'experience_companies': experience_companies,
            'experience_positions': experience_positions,
            'project_names': project_names,
            'project_technologies': project_technologies,
            'education_institutions': education_institutions,
            'education_degrees': education_degrees,
            'education_fields': education_fields,
            'certifications': certifications,
            'languages': languages,
            'interests': interests,
            'contact_links': contact_links,
            
            # Full searchable text for general queries
            'searchable_text': ' '.join(filter(None, searchable_text_parts)),
            
            # Additional metadata for filtering
            'onboarding_completed': getattr(user, 'onboarding_completed', False),
            'created_at': user.created_at.timestamp() if hasattr(user, 'created_at') and user.created_at else 0,
            'updated_at': user.updated_at.timestamp() if hasattr(user, 'updated_at') and user.updated_at else 0
        }
        
        return algolia_record
    
    async def sync_user_to_algolia(self, user: UserInDB) -> bool:
        """Sync a single user to Algolia index"""
        try:
            print(f"🔄 [ALGOLIA] Starting sync for user {user.id}")
            print(f"🔄 [ALGOLIA] Index name: {self.index_name}")
            print(f"🔄 [ALGOLIA] User name: {user.name}")
            print(f"🔄 [ALGOLIA] User profile_score: {getattr(user, 'profile_score', 'NOT_SET')}")
            
            algolia_record = self._format_user_for_algolia(user)
            print(f"🔄 [ALGOLIA] Record objectID: {algolia_record.get('objectID')}")
            print(f"🔄 [ALGOLIA] Record profile_score: {algolia_record.get('profile_score')}")
            
            # Save to Algolia
            print(f"🔄 [ALGOLIA] Calling save_object...")
            response = await self.client.save_object(
                index_name=self.index_name,
                body=algolia_record
            )
            print(f"🔄 [ALGOLIA] Response: {response}")
            
            logger.info(f"✅ [ALGOLIA] User {user.id} synced to Algolia successfully")
            print(f"✅ [ALGOLIA] User {user.id} synced to Algolia successfully")
            return True
            
        except Exception as e:
            error_msg = f"❌ [ALGOLIA] Failed to sync user {user.id} to Algolia: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            print(f"❌ [ALGOLIA] Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
    
    async def delete_user_from_algolia(self, user_id: str) -> bool:
        """Delete a user from Algolia index"""
        try:
            await self.client.delete_object(
                index_name=self.index_name,
                object_id=user_id
            )
            logger.info(f"✅ [ALGOLIA] User {user_id} deleted from Algolia")
            return True
            
        except Exception as e:
            logger.error(f"❌ [ALGOLIA] Failed to delete user {user_id} from Algolia: {str(e)}")
            return False
    
    async def configure_index_settings(self) -> bool:
        """Configure Algolia index settings for optimal search"""
        try:
            settings_config = {
                'searchableAttributes': [
                    'name',
                    'username', 
                    'email',
                    'designation',
                    'profession',
                    'location',
                    'skills',
                    'experience_companies',
                    'experience_positions',
                    'project_names',
                    'project_technologies',
                    'education_institutions',
                    'education_degrees',
                    'education_fields',
                    'certifications',
                    'languages',
                    'interests',
                    'searchable_text'
                ],
                'attributesForFaceting': [
                    'is_looking_for_job',
                    'location',
                    'skills',
                    'profession'
                ],
                'customRanking': [
                    'desc(profile_score)',  # Primary: Profile score descending
                    'desc(rating)',         # Secondary: Rating descending
                    'desc(onboarding_completed)', # Tertiary: Completed profiles first
                    'desc(updated_at)'      # Last: Recently updated first
                ],
                'ranking': [
                    'typo',
                    'geo',
                    'words',
                    'filters',
                    'proximity',
                    'attribute',
                    'exact',
                    'custom'
                ],
                'typoTolerance': True,
                'minWordSizefor1Typo': 3,
                'minWordSizefor2Typos': 7,
                'allowTyposOnNumericTokens': False,
                'ignorePlurals': True,
                'removeStopWords': True,
                'queryType': 'prefixAll',
                'removeWordsIfNoResults': 'lastWords',
                'advancedSyntax': True,
                'exactOnSingleWordQuery': 'attribute'
            }
            
            # Use the client to set settings - check if method exists first
            if hasattr(self.client, 'set_settings'):
                await self.client.set_settings(
                    index_name=self.index_name,
                    index_settings=settings_config
                )
            else:
                logger.warning("⚠️ [ALGOLIA] set_settings method not available in this version")
                
            logger.info("✅ [ALGOLIA] Index settings configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ [ALGOLIA] Failed to configure index settings: {str(e)}")
            return False