import os
import aiofiles
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings
from app.utils.helpers import generate_unique_filename, validate_file_type, validate_file_size
from app.services.s3_service import S3Service

class FileService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.max_file_size = settings.MAX_FILE_SIZE
        self.s3_service = S3Service()

    async def save_profile_picture(self, file: UploadFile, username: str) -> str:
        """Save profile picture to S3 and return public URL"""
        return await self.s3_service.upload_profile_picture(file, username)
    
    async def delete_profile_picture(self, username: str) -> bool:
        """Delete profile picture from S3"""
        return await self.s3_service.delete_profile_picture(username)
    
    def get_profile_picture_url(self, username: str) -> Optional[str]:
        """Get profile picture URL from S3"""
        return self.s3_service.get_profile_picture_url(username)


    async def save_pdf_file(self, file: UploadFile) -> str:
        """Save PDF file and return file path"""
        # Validate file
        if not validate_file_type(file.filename, ["pdf"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        if not validate_file_size(file.size):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size must be less than {self.max_file_size // (1024*1024)}MB"
            )
        
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)
        
        # Create PDF directory
        pdf_dir = os.path.join(self.upload_dir, "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(pdf_dir, unique_filename)
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            return file_path
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save PDF file: {str(e)}"
            )

    def delete_file(self, file_path: str) -> bool:
        """Delete file from filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False