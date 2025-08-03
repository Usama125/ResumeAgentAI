import os
import base64
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
from typing import Dict, Any, List, Optional

class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.register_fonts()
        self.setup_custom_styles()
    
    def register_fonts(self):
        """Register fonts for PDF generation"""
        try:
            # Try to register Sweet Sans Pro fonts (OTF format)
            font_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'fonts')
            
            # For now, use system fonts that are similar to Sweet Sans Pro
            # These are more reliable with ReportLab
            print("ℹ️ Using system fonts for PDF generation")
            
        except Exception as e:
            print(f"Warning: Could not register custom fonts: {e}")
            # Fallback to default fonts
            pass
    
    def setup_custom_styles(self):
        """Setup custom styles matching the frontend design"""
        # Primary heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=12,
            textColor=HexColor('#1f2937'),  # Gray-800
            fontName='Helvetica-Bold'
        ))
        
        # Secondary heading style (name)
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=8,
            textColor=HexColor('#1f2937'),  # Gray-800
            fontName='Helvetica-Bold',
            alignment=1  # Center alignment
        ))
        
        # Designation style (brand green)
        self.styles.add(ParagraphStyle(
            name='Designation',
            parent=self.styles['Heading3'],
            fontSize=16,
            spaceAfter=8,
            textColor=HexColor('#10a37f'),  # Brand green
            fontName='Helvetica-Bold',
            alignment=1  # Center alignment
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading3'],
            fontSize=16,
            spaceAfter=6,
            textColor=HexColor('#10a37f'),  # Brand green
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=HexColor('#4b5563'),  # Gray-600
            fontName='Helvetica'
        ))
        
        # Small text style
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            textColor=HexColor('#6b7280'),  # Gray-500
            fontName='Helvetica'
        ))
        
        # Skills style
        self.styles.add(ParagraphStyle(
            name='SkillTag',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            textColor=HexColor('#10a37f'),  # Brand green
            fontName='Helvetica'
        ))
        
        # Location style
        self.styles.add(ParagraphStyle(
            name='Location',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=HexColor('#6b7280'),  # Gray-500
            fontName='Helvetica',
            alignment=1  # Center alignment
        ))

    def download_image_from_s3(self, image_url: str) -> Optional[BytesIO]:
        """Download image from S3 URL and return as BytesIO"""
        try:
            if not image_url or image_url == "/placeholder-user.jpg":
                return None
            
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                return BytesIO(response.content)
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def create_circular_image(self, image_data: BytesIO, size: float = 2.0) -> Image:
        """Create a circular profile image with border"""
        try:
            from PIL import Image as PILImage, ImageDraw
            import io
            
            # Open image with PIL and convert to RGB if needed
            pil_image = PILImage.open(image_data)
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Enhance image quality with slight sharpening
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Sharpness(pil_image)
            pil_image = enhancer.enhance(1.1)  # Slight sharpening
            
            # Resize to maximum resolution for ultimate quality
            target_size = int(size * 400)  # Maximum resolution for ultimate crisp images
            pil_image = pil_image.resize((target_size, target_size), PILImage.Resampling.LANCZOS)
            
            # Create smooth circular mask
            mask = PILImage.new('L', pil_image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, pil_image.size[0], pil_image.size[1]), fill=255)
            
            # Apply mask to create circular image
            output = PILImage.new('RGBA', pil_image.size, (0, 0, 0, 0))
            output.paste(pil_image, (0, 0))
            output.putalpha(mask)
            
            # Create border with gap and clear border
            border_size = 8  # 8px border
            gap_size = 3  # 3px gap between image and border
            total_size = output.size[0] + (border_size + gap_size) * 2
            
            # Create final image with border
            final_image = PILImage.new('RGBA', (total_size, total_size), (0, 0, 0, 0))
            
            # Create outer border mask (full circle)
            border_mask = PILImage.new('L', (total_size, total_size), 0)
            border_draw = ImageDraw.Draw(border_mask)
            border_draw.ellipse((0, 0, total_size, total_size), fill=255)
            
            # Create border layer with enhanced clarity
            border_layer = PILImage.new('RGBA', (total_size, total_size), (16, 163, 127, 255))  # #10a37f with full opacity
            border_layer.putalpha(border_mask)
            
            # Create inner mask for the image area (smaller than border)
            image_mask = PILImage.new('L', (total_size, total_size), 0)
            image_draw = ImageDraw.Draw(image_mask)
            image_draw.ellipse((border_size + gap_size, border_size + gap_size, 
                               total_size - border_size - gap_size, total_size - border_size - gap_size), fill=255)
            
            # Create transparent center with gap
            center_layer = PILImage.new('RGBA', (total_size, total_size), (0, 0, 0, 0))
            center_layer.putalpha(image_mask)
            
            # Combine border and center
            final_image = PILImage.alpha_composite(border_layer, center_layer)
            
            # Paste the circular image in the center area (with gap)
            final_image.paste(output, (border_size + gap_size, border_size + gap_size), output)
            
            # Convert back to bytes with maximum quality and no compression
            img_byte_arr = io.BytesIO()
            final_image.save(img_byte_arr, format='PNG', optimize=False, quality=100, dpi=(300, 300))
            img_byte_arr.seek(0)
            
            # Create ReportLab image
            return Image(img_byte_arr, width=size*inch, height=size*inch)
            
        except Exception as e:
            print(f"Error creating circular image: {e}")
            # Fallback to regular image
            image_data.seek(0)
            return Image(image_data, width=size*inch, height=size*inch)

    def create_profile_pdf(self, user_data: Dict[str, Any]) -> BytesIO:
        """Create PDF matching the exact design of the profile view"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Profile picture and basic info (no header)
        story.extend(self.create_profile_header(user_data))
        story.append(Spacer(1, 20))
        
        # About section
        if user_data.get('about'):
            story.extend(self.create_about_section(user_data['about']))
            story.append(Spacer(1, 15))
        
        # Contact section
        if user_data.get('contact_info'):
            story.extend(self.create_contact_section(user_data['contact_info']))
            story.append(Spacer(1, 15))
        
        # Experience section
        if user_data.get('experience') and len(user_data['experience']) > 0:
            story.extend(self.create_experience_section(user_data['experience']))
            story.append(Spacer(1, 15))
        
        # Education section
        if user_data.get('education') and len(user_data['education']) > 0:
            story.extend(self.create_education_section(user_data['education']))
            story.append(Spacer(1, 15))
        
        # Skills section
        if user_data.get('skills') and len(user_data['skills']) > 0:
            story.extend(self.create_skills_section(user_data['skills']))
            story.append(Spacer(1, 15))
        
        # Projects section
        if user_data.get('projects') and len(user_data['projects']) > 0:
            story.extend(self.create_projects_section(user_data['projects']))
            story.append(Spacer(1, 15))
        
        # Languages section
        if user_data.get('languages') and len(user_data['languages']) > 0:
            story.extend(self.create_languages_section(user_data['languages']))
            story.append(Spacer(1, 15))
        
        # Certifications section
        if user_data.get('certifications') and len(user_data['certifications']) > 0:
            story.extend(self.create_certifications_section(user_data['certifications']))
            story.append(Spacer(1, 15))
        
        # Awards section
        if user_data.get('awards') and len(user_data['awards']) > 0:
            story.extend(self.create_awards_section(user_data['awards']))
            story.append(Spacer(1, 15))
        
        # Publications section
        if user_data.get('publications') and len(user_data['publications']) > 0:
            story.extend(self.create_publications_section(user_data['publications']))
            story.append(Spacer(1, 15))
        
        # Volunteer section
        if user_data.get('volunteer_experience') and len(user_data['volunteer_experience']) > 0:
            story.extend(self.create_volunteer_section(user_data['volunteer_experience']))
            story.append(Spacer(1, 15))
        
        # Interests section
        if user_data.get('interests') and len(user_data['interests']) > 0:
            story.extend(self.create_interests_section(user_data['interests']))
            story.append(Spacer(1, 15))
        
        # Footer with signature
        story.extend(self.create_footer())
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    def create_header(self, user_data: Dict[str, Any]) -> List:
        """Create header with centered logo and signature"""
        elements = []
        
        # Logo and title (centered)
        header_elements = []
        
        # CVChatter title (centered)
        title_para = Paragraph("CVChatter", self.styles['CustomHeading1'])
        title_para.alignment = 1  # Center alignment
        header_elements.append(title_para)
        
        # Subtitle (centered)
        subtitle_para = Paragraph("Tailored Resume", self.styles['CustomBody'])
        subtitle_para.alignment = 1  # Center alignment
        header_elements.append(subtitle_para)
        
        elements.extend(header_elements)
        elements.append(Spacer(1, 20))
        
        return elements

    def create_profile_header(self, user_data: Dict[str, Any]) -> List:
        """Create profile header with centered picture and info"""
        elements = []
        
        # Download profile picture
        profile_image = None
        if user_data.get('profile_picture'):
            image_data = self.download_image_from_s3(user_data['profile_picture'])
            if image_data:
                try:
                    # Create circular profile image with border
                    profile_image = self.create_circular_image(image_data, 2.0)
                    profile_image.hAlign = 'CENTER'
                except:
                    profile_image = None
        
        # Create centered header content
        elements.append(Spacer(1, 20))
        
        # Add profile image if available (centered)
        if profile_image:
            elements.append(profile_image)
            elements.append(Spacer(1, 15))
        
        # Add name (centered)
        if user_data.get('name'):
            name_para = Paragraph(f"<b>{user_data['name']}</b>", self.styles['CustomHeading2'])
            name_para.alignment = 1  # Center alignment
            elements.append(name_para)
            elements.append(Spacer(1, 8))
        
        # Add designation (centered, brand green)
        if user_data.get('designation'):
            designation_para = Paragraph(user_data['designation'], self.styles['Designation'])
            designation_para.alignment = 1  # Center alignment
            elements.append(designation_para)
            elements.append(Spacer(1, 8))
        
        # Add location (centered with icon)
        if user_data.get('location'):
            # Use a simple text icon instead of emoji for better compatibility
            location_para = Paragraph(f"• {user_data['location']}", self.styles['Location'])
            location_para.alignment = 1  # Center alignment
            elements.append(location_para)
            elements.append(Spacer(1, 15))
        
        return elements

    def create_about_section(self, about: str) -> List:
        """Create about section"""
        elements = []
        elements.append(Paragraph("About", self.styles['SectionHeading']))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(about, self.styles['CustomBody']))
        elements.append(Spacer(1, 15))
        return elements

    def create_contact_section(self, contact_info: Dict[str, Any]) -> List:
        """Create contact section"""
        elements = []
        elements.append(Paragraph("Contact Information", self.styles['SectionHeading']))
        
        contact_data = []
        if contact_info.get('email'):
            contact_data.append([Paragraph("Email:", self.styles['CustomBody']), 
                              Paragraph(contact_info['email'], self.styles['CustomBody'])])
        if contact_info.get('phone'):
            contact_data.append([Paragraph("Phone:", self.styles['CustomBody']), 
                              Paragraph(contact_info['phone'], self.styles['CustomBody'])])
        if contact_info.get('linkedin'):
            contact_data.append([Paragraph("LinkedIn:", self.styles['CustomBody']), 
                              Paragraph(contact_info['linkedin'], self.styles['CustomBody'])])
        if contact_info.get('website'):
            contact_data.append([Paragraph("Website:", self.styles['CustomBody']), 
                              Paragraph(contact_info['website'], self.styles['CustomBody'])])
        
        if contact_data:
            available_width = A4[0] - 1.5*inch  # 1.5 inch total margins
            contact_table = Table(contact_data, colWidths=[1.5*inch, available_width-1.5*inch])
            contact_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(contact_table)
        
        return elements

    def create_experience_section(self, experience: List[Dict[str, Any]]) -> List:
        """Create experience section"""
        elements = []
        elements.append(Paragraph("Work Experience", self.styles['SectionHeading']))
        
        for exp in experience:
            exp_elements = []
            
            # Title and company
            title_company = f"<b>{exp.get('position', '')}</b>"
            if exp.get('company'):
                title_company += f" at {exp.get('company')}"
            exp_elements.append(Paragraph(title_company, self.styles['CustomBody']))
            
            # Duration and location
            duration_location = []
            if exp.get('start_date') and exp.get('end_date'):
                duration_location.append(f"{exp['start_date']} - {exp['end_date']}")
            elif exp.get('start_date'):
                duration_location.append(f"{exp['start_date']} - Present")
            if exp.get('duration'):
                duration_location.append(exp['duration'])
            
            if duration_location:
                exp_elements.append(Paragraph(" | ".join(duration_location), self.styles['SmallText']))
            
            # Description
            if exp.get('description'):
                exp_elements.append(Paragraph(exp['description'], self.styles['CustomBody']))
            
            elements.extend(exp_elements)
            elements.append(Spacer(1, 8))
        
        return elements

    def create_education_section(self, education: List[Dict[str, Any]]) -> List:
        """Create education section"""
        elements = []
        elements.append(Paragraph("Education", self.styles['SectionHeading']))
        
        for edu in education:
            edu_elements = []
            
            # Degree and institution
            degree_institution = f"<b>{edu.get('degree', '')}</b>"
            if edu.get('institution'):
                degree_institution += f" from {edu.get('institution')}"
            edu_elements.append(Paragraph(degree_institution, self.styles['CustomBody']))
            
            # Duration and field of study
            duration_field = []
            if edu.get('start_date') and edu.get('end_date'):
                duration_field.append(f"{edu['start_date']} - {edu['end_date']}")
            elif edu.get('start_date'):
                duration_field.append(f"{edu['start_date']} - Present")
            if edu.get('field_of_study'):
                duration_field.append(edu['field_of_study'])
            
            if duration_field:
                edu_elements.append(Paragraph(" | ".join(duration_field), self.styles['SmallText']))
            
            # Grade and description
            if edu.get('grade'):
                edu_elements.append(Paragraph(f"Grade: {edu['grade']}", self.styles['SmallText']))
            if edu.get('description'):
                edu_elements.append(Paragraph(edu['description'], self.styles['CustomBody']))
            
            elements.extend(edu_elements)
            elements.append(Spacer(1, 8))
        
        return elements

    def create_skills_section(self, skills: List) -> List:
        """Create skills section with simple design"""
        elements = []
        elements.append(Paragraph("Skills", self.styles['SectionHeading']))
        
        # Handle both string and dictionary formats
        skill_names = []
        for skill in skills:
            if isinstance(skill, dict):
                skill_names.append(skill.get('name', ''))
            elif isinstance(skill, str):
                skill_names.append(skill)
        
        # Filter out empty skills
        skill_names = [name for name in skill_names if name]
        
        # Show maximum 15 skills
        display_skills = skill_names[:15]
        skills_text = ", ".join(display_skills)
        elements.append(Paragraph(skills_text, self.styles['CustomBody']))
        
        if len(skill_names) > 15:
            elements.append(Paragraph(f"... and {len(skill_names) - 15} more skills", self.styles['SmallText']))
        
        elements.append(Spacer(1, 12))
        return elements

    def create_projects_section(self, projects: List[Dict[str, Any]]) -> List:
        """Create projects section"""
        elements = []
        elements.append(Paragraph("Projects", self.styles['SectionHeading']))
        
        for project in projects:
            proj_elements = []
            
            # Title and link
            title_link = f"<b>{project.get('name', '')}</b>"
            if project.get('url'):
                title_link += f" - {project.get('url')}"
            proj_elements.append(Paragraph(title_link, self.styles['CustomBody']))
            
            # Duration
            if project.get('duration'):
                proj_elements.append(Paragraph(project['duration'], self.styles['SmallText']))
            
            # Description
            if project.get('description'):
                proj_elements.append(Paragraph(project['description'], self.styles['CustomBody']))
            
            # Technologies
            if project.get('technologies'):
                tech_text = f"Technologies: {', '.join(project['technologies'])}"
                proj_elements.append(Paragraph(tech_text, self.styles['SmallText']))
            
            elements.extend(proj_elements)
            elements.append(Spacer(1, 8))
        
        return elements

    def create_languages_section(self, languages: List[Dict[str, Any]]) -> List:
        """Create languages section"""
        elements = []
        elements.append(Paragraph("Languages", self.styles['SectionHeading']))
        
        for lang in languages:
            lang_text = f"<b>{lang.get('name', '')}</b>"
            if lang.get('proficiency'):
                lang_text += f" - {lang.get('proficiency')}"
            elements.append(Paragraph(lang_text, self.styles['CustomBody']))
            elements.append(Spacer(1, 4))
        
        return elements

    def create_certifications_section(self, certifications: List[str]) -> List:
        """Create certifications section"""
        elements = []
        elements.append(Paragraph("Certifications", self.styles['SectionHeading']))
        
        for cert in certifications:
            elements.append(Paragraph(f"• {cert}", self.styles['CustomBody']))
            elements.append(Spacer(1, 4))
        
        return elements

    def create_awards_section(self, awards: List[Dict[str, Any]]) -> List:
        """Create awards section"""
        elements = []
        elements.append(Paragraph("Awards & Recognition", self.styles['SectionHeading']))
        
        for award in awards:
            award_elements = []
            
            # Title and issuer
            title_issuer = f"<b>{award.get('title', '')}</b>"
            if award.get('issuer'):
                title_issuer += f" from {award.get('issuer')}"
            award_elements.append(Paragraph(title_issuer, self.styles['CustomBody']))
            
            # Date
            if award.get('date'):
                award_elements.append(Paragraph(f"Date: {award['date']}", self.styles['SmallText']))
            
            # Description
            if award.get('description'):
                award_elements.append(Paragraph(award['description'], self.styles['CustomBody']))
            
            elements.extend(award_elements)
            elements.append(Spacer(1, 8))
        
        return elements

    def create_publications_section(self, publications: List[Dict[str, Any]]) -> List:
        """Create publications section"""
        elements = []
        elements.append(Paragraph("Publications", self.styles['SectionHeading']))
        
        for pub in publications:
            pub_elements = []
            
            # Title
            pub_elements.append(Paragraph(f"<b>{pub.get('title', '')}</b>", self.styles['CustomBody']))
            
            # Authors and journal
            authors_journal = []
            if pub.get('authors'):
                authors_journal.append(pub['authors'])
            if pub.get('journal'):
                authors_journal.append(pub['journal'])
            
            if authors_journal:
                pub_elements.append(Paragraph(" | ".join(authors_journal), self.styles['SmallText']))
            
            # Date
            if pub.get('date'):
                pub_elements.append(Paragraph(f"Date: {pub['date']}", self.styles['SmallText']))
            
            # Description
            if pub.get('description'):
                pub_elements.append(Paragraph(pub['description'], self.styles['CustomBody']))
            
            elements.extend(pub_elements)
            elements.append(Spacer(1, 8))
        
        return elements

    def create_volunteer_section(self, volunteer: List[Dict[str, Any]]) -> List:
        """Create volunteer section"""
        elements = []
        elements.append(Paragraph("Volunteer Experience", self.styles['SectionHeading']))
        
        for vol in volunteer:
            vol_elements = []
            
            # Title and organization
            title_org = f"<b>{vol.get('title', '')}</b>"
            if vol.get('organization'):
                title_org += f" at {vol.get('organization')}"
            vol_elements.append(Paragraph(title_org, self.styles['CustomBody']))
            
            # Duration and location
            duration_location = []
            if vol.get('start_date') and vol.get('end_date'):
                duration_location.append(f"{vol['start_date']} - {vol['end_date']}")
            elif vol.get('start_date'):
                duration_location.append(f"{vol['start_date']} - Present")
            if vol.get('location'):
                duration_location.append(vol['location'])
            
            if duration_location:
                vol_elements.append(Paragraph(" | ".join(duration_location), self.styles['SmallText']))
            
            # Description
            if vol.get('description'):
                vol_elements.append(Paragraph(vol['description'], self.styles['CustomBody']))
            
            elements.extend(vol_elements)
            elements.append(Spacer(1, 8))
        
        return elements

    def create_interests_section(self, interests: List[str]) -> List:
        """Create interests section"""
        elements = []
        elements.append(Paragraph("Interests", self.styles['SectionHeading']))
        
        interests_text = ", ".join(interests)
        elements.append(Paragraph(interests_text, self.styles['CustomBody']))
        
        return elements

    def create_footer(self) -> List:
        """Create footer with signature"""
        elements = []
        elements.append(Spacer(1, 20))
        
        footer_text = "Generated by CVChatter - Tailored Resume Platform"
        elements.append(Paragraph(footer_text, self.styles['SmallText']))
        
        return elements


class DocumentService:
    """Service for processing uploaded documents (PDF, Word, etc.)"""
    
    def __init__(self):
        self.upload_dir = "uploads/documents"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        ext = filename.lower().split('.')[-1]
        if ext == 'pdf':
            return 'pdf'
        elif ext in ['docx', 'doc']:
            return 'word'
        else:
            return 'unknown'
    
    async def save_uploaded_document(self, file_content: bytes, filename: str) -> str:
        """Save uploaded document to disk"""
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        return file_path
    
    async def process_resume_document(self, file_path: str, filename: str, user_id: str = None) -> dict:
        """Process resume document and extract information"""
        try:
            file_type = self.get_file_type(filename)
            
            if file_type == 'pdf':
                return await self._process_pdf(file_path, user_id)
            elif file_type == 'word':
                return await self._process_word(file_path, user_id)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing document: {str(e)}'
            }
    
    async def _process_pdf(self, file_path: str, user_id: str = None) -> dict:
        """Process PDF document"""
        try:
            # This would integrate with the AI service for PDF processing
            # For now, return a basic structure
            return {
                'success': True,
                'extracted_data': {
                    'name': '',
                    'email': '',
                    'phone': '',
                    'experience': [],
                    'education': [],
                    'skills': [],
                    'projects': []
                },
                'qa_verification': {
                    'confidence_score': 0,
                    'missing_sections': []
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing PDF: {str(e)}'
            }
    
    async def _process_word(self, file_path: str, user_id: str = None) -> dict:
        """Process Word document"""
        try:
            # This would integrate with the AI service for Word processing
            # For now, return a basic structure
            return {
                'success': True,
                'extracted_data': {
                    'name': '',
                    'email': '',
                    'phone': '',
                    'experience': [],
                    'education': [],
                    'skills': [],
                    'projects': []
                },
                'qa_verification': {
                    'confidence_score': 0,
                    'missing_sections': []
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing Word document: {str(e)}'
            }