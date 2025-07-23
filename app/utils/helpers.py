import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename preserving extension"""
    file_extension = original_filename.split('.')[-1]
    return f"{uuid.uuid4()}.{file_extension}"

def validate_file_type(filename: str, allowed_types: list = None) -> bool:
    """Validate if file type is allowed"""
    if allowed_types is None:
        allowed_types = settings.ALLOWED_FILE_TYPES
    
    file_extension = filename.lower().split('.')[-1]
    return file_extension in allowed_types

def validate_file_size(file_size: int, max_size: int = None) -> bool:
    """Validate if file size is within limits"""
    if max_size is None:
        max_size = settings.MAX_FILE_SIZE
    
    return file_size <= max_size

async def save_upload_file(upload_file: UploadFile, destination_path: str) -> str:
    """Save uploaded file to destination and return path"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Save file
        with open(destination_path, "wb") as buffer:
            content = await upload_file.read()
            buffer.write(content)
        
        return destination_path
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )