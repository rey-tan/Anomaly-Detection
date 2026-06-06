import random
import string
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()


def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def get_otp_expiration(minutes: int = 10) -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=minutes)


def send_otp_email(email: str, otp_code: str) -> bool:
    """Send OTP via Gmail SMTP."""
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    
    # Fallback to console logging if credentials not configured
    if not gmail_address or not gmail_password:
        print(f"[OTP] Sending OTP to {email}: {otp_code}")
        print("[WARNING] Gmail credentials not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env")
        return False
    
    try:
        # Create email message
        msg = MIMEMultipart()
        msg["From"] = gmail_address
        msg["To"] = email
        msg["Subject"] = "Your Anomaly Engine OTP Code"
        
        body = f"""
        Hello,
        
        Your OTP code is: {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Anomaly Engine Team
        """
        
        msg.attach(MIMEText(body, "plain"))
        
        # Send via Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_address, gmail_password)
        server.send_message(msg)
        server.quit()
        
        print(f"[OTP] Successfully sent OTP to {email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"[OTP ERROR] Gmail authentication failed. Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD")
        print(f"[OTP ERROR] Authentication error: {e}") 
        return False
    except Exception as exc:
        print(f"[OTP ERROR] Failed to send email to {email}: {exc}")
        return False
