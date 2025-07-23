import os
import aiofiles
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings
from app.utils.helpers import generate_unique_filename, validate_file_type, validate_file_size

class FileService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.max_file_size = settings.MAX_FILE_SIZE

    async def save_profile_picture(self, file: UploadFile, user_id: str) -> str:
        """Save profile picture and return URL"""
        # Validate file
        if not validate_file_type(file.filename, ["jpg", "jpeg", "png"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPG, JPEG, PNG files are allowed"
            )
        
        if not validate_file_size(file.size):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size must be less than {self.max_file_size // (1024*1024)}MB"
            )
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"profile_{user_id}_{generate_unique_filename(file.filename)}"
        
        # Create profile directory
        profile_dir = os.path.join(self.upload_dir, "profiles")
        os.makedirs(profile_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(profile_dir, unique_filename)
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            return f"/uploads/profiles/{unique_filename}"
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save profile picture: {str(e)}"
            )

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