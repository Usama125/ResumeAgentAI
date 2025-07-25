import aiosmtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Gmail SMTP settings
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.from_email = settings.GMAIL_EMAIL
        self.app_password = settings.GMAIL_APP_PASSWORD
    
    async def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """Send password reset email using Gmail SMTP"""
        try:
            logger.info(f"🚀 [EMAIL SERVICE] Starting password reset email for: {to_email}")
            
            if not self.from_email or not self.app_password:
                logger.error("❌ [EMAIL SERVICE] Gmail credentials not configured")
                print("❌ [EMAIL SERVICE] Gmail credentials not configured - check GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env file")
                return False
            
            logger.info(f"✅ [EMAIL SERVICE] Gmail SMTP configured for: {self.from_email}")
            print(f"✅ [EMAIL SERVICE] Gmail SMTP configured for: {self.from_email}")
            
            # Create reset link - adjust the domain as needed
            reset_link = f"https://cvchatter.com/auth/reset-password?token={reset_token}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Password Reset - ResumeAgent AI</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        margin: 0;
                        padding: 0;
                        background-color: #f8fafc;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .email-content {{
                        background: white;
                        border-radius: 16px;
                        padding: 40px;
                        border: 1px solid #e2e8f0;
                        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .logo {{
                        font-size: 24px;
                        font-weight: bold;
                        color: #10a37f;
                        margin-bottom: 10px;
                    }}
                    .title {{
                        font-size: 28px;
                        font-weight: bold;
                        color: #1e293b;
                        margin-bottom: 10px;
                    }}
                    .subtitle {{
                        color: #64748b;
                        font-size: 16px;
                    }}
                    .content {{
                        margin: 30px 0;
                    }}
                    .reset-button {{
                        display: inline-block;
                        background: linear-gradient(135deg, #10a37f 0%, #0d8f6f 100%);
                        color: white;
                        text-decoration: none;
                        padding: 16px 32px;
                        border-radius: 12px;
                        font-weight: 600;
                        font-size: 16px;
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .link-fallback {{
                        background: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        padding: 15px;
                        margin: 20px 0;
                        word-break: break-all;
                        font-family: monospace;
                        font-size: 14px;
                        color: #475569;
                    }}
                    .warning {{
                        background: #fef3cd;
                        border: 1px solid #fbbf24;
                        border-radius: 8px;
                        padding: 15px;
                        margin: 20px 0;
                        color: #92400e;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #e2e8f0;
                        color: #64748b;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="email-content">
                        <div class="header">
                            <div class="logo">🤖 ResumeAgent AI</div>
                            <h1 class="title">Password Reset Request</h1>
                            <p class="subtitle">We received a request to reset your password</p>
                        </div>
                        
                        <div class="content">
                            <p>Hi {user_name},</p>
                            
                            <p>We received a request to reset your password for your ResumeAgent AI account. If you didn't make this request, you can safely ignore this email.</p>
                            
                            <p>To reset your password, click the button below:</p>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{reset_link}" class="reset-button">Reset My Password</a>
                            </div>
                            
                            <p>Or copy and paste this link in your browser:</p>
                            <div class="link-fallback">{reset_link}</div>
                            
                            <div class="warning">
                                <strong>Important:</strong> This link will expire in 1 hour for security reasons.
                            </div>
                            
                            <p>Best regards,<br>The ResumeAgent AI Team</p>
                        </div>
                        
                        <div class="footer">
                            <p>This email was sent to {to_email}.</p>
                            <p>© 2024 ResumeAgent AI. All rights reserved.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Text fallback
            text_content = f"""
            Password Reset Request - ResumeAgent AI
            
            Hi {user_name},
            
            We received a request to reset your password for your ResumeAgent AI account.
            
            To reset your password, visit this link: {reset_link}
            
            This link will expire in 1 hour for security reasons.
            
            If you didn't request this, you can safely ignore this email.
            
            Best regards,
            The ResumeAgent AI Team
            """
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Reset Your Password - ResumeAgent AI"
            message["From"] = self.from_email
            message["To"] = to_email
            
            # Attach both text and HTML versions
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            logger.info(f"📧 [EMAIL SERVICE] Sending email via Gmail SMTP: {self.from_email} -> {to_email}")
            print(f"📧 [EMAIL SERVICE] Sending email via Gmail SMTP: {self.from_email} -> {to_email}")
            
            # Send email using Gmail SMTP
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                start_tls=True,
                username=self.from_email,
                password=self.app_password,
            )
            
            logger.info(f"✅ [EMAIL SERVICE] Password reset email sent successfully to {to_email}")
            print(f"✅ [EMAIL SERVICE] Password reset email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [EMAIL SERVICE] Failed to send password reset email to {to_email}: {str(e)}")
            print(f"❌ [EMAIL SERVICE] Failed to send password reset email to {to_email}: {str(e)}")
            print(f"❌ [EMAIL SERVICE] Exception type: {type(e).__name__}")
            print(f"❌ [EMAIL SERVICE] Exception details: {repr(e)}")
            return False
    
    async def send_password_reset_confirmation_email(self, to_email: str, user_name: str) -> bool:
        """Send password reset confirmation email using Gmail SMTP"""
        try:
            if not self.from_email or not self.app_password:
                logger.error("Gmail credentials not configured")
                return False
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Password Updated - ResumeAgent AI</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .logo {{ font-size: 24px; font-weight: bold; color: #10a37f; }}
                    .title {{ font-size: 28px; color: #1e293b; }}
                    .success-icon {{ font-size: 48px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🤖 ResumeAgent AI</div>
                        <div class="success-icon">✅</div>
                        <h1 class="title">Password Successfully Updated</h1>
                    </div>
                    
                    <p>Hi {user_name},</p>
                    <p>This email confirms that your password has been successfully updated for your ResumeAgent AI account.</p>
                    <p>If you didn't make this change, please contact our support team immediately.</p>
                    <p>Best regards,<br>The ResumeAgent AI Team</p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Password Successfully Updated - ResumeAgent AI
            
            Hi {user_name},
            
            This email confirms that your password has been successfully updated.
            If you didn't make this change, please contact support immediately.
            
            Best regards,
            The ResumeAgent AI Team
            """
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Password Successfully Updated - ResumeAgent AI"
            message["From"] = self.from_email
            message["To"] = to_email
            
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                start_tls=True,
                username=self.from_email,
                password=self.app_password,
            )
            
            logger.info(f"Password reset confirmation email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset confirmation email to {to_email}: {str(e)}")
            return False

email_service = EmailService()