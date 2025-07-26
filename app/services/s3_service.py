import boto3
import os
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings
from app.utils.helpers import validate_file_type, validate_file_size
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.max_file_size = settings.MAX_FILE_SIZE

    async def upload_profile_picture(self, file: UploadFile, username: str) -> str:
        """Upload profile picture to S3 using username as key and return public URL"""
        
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
        
        try:
            # Get file extension
            file_extension = file.filename.split('.')[-1].lower()
            
            # Use username as the key to ensure only one picture per user
            s3_key = f"profile-pictures/{username}.{file_extension}"
            
            # Read file content
            file_content = await file.read()
            
            # Check if user already has a profile picture and delete it
            await self._delete_existing_profile_picture(username)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=f"image/{file_extension}"
                # Removed ACL since the bucket is already configured for public access
            )
            
            # Generate public URL
            public_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            
            logger.info(f"Successfully uploaded profile picture for user {username} to S3: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload profile picture to S3 for user {username}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload profile picture: {str(e)}"
            )

    async def _delete_existing_profile_picture(self, username: str) -> bool:
        """Delete existing profile picture for user (check all possible extensions)"""
        try:
            # List all objects with the username prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"profile-pictures/{username}."
            )
            
            # Delete existing files
            if 'Contents' in response:
                for obj in response['Contents']:
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    logger.info(f"Deleted existing profile picture: {obj['Key']}")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not delete existing profile picture for user {username}: {str(e)}")
            return False

    async def delete_profile_picture(self, username: str) -> bool:
        """Delete profile picture for user"""
        try:
            return await self._delete_existing_profile_picture(username)
        except Exception as e:
            logger.error(f"Failed to delete profile picture for user {username}: {str(e)}")
            return False

    def get_profile_picture_url(self, username: str) -> Optional[str]:
        """Get profile picture URL for user if it exists"""
        try:
            # Check for common image extensions
            extensions = ['jpg', 'jpeg', 'png']
            
            for ext in extensions:
                s3_key = f"profile-pictures/{username}.{ext}"
                try:
                    # Check if object exists
                    self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                    # If we get here, the object exists
                    return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
                except self.s3_client.exceptions.NoSuchKey:
                    continue
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get profile picture URL for user {username}: {str(e)}")
            return None