import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(subject, body, to_email):
    """Send email with error handling"""
    if not os.getenv("EMAIL_USER") or not os.getenv("EMAIL_PASS"):
        return "❌ Email credentials not configured"
    
    try:
        msg = EmailMessage()
        msg["Subject"] = subject.replace('\n', ' ').strip()[:100]
        msg["From"] = os.getenv("EMAIL_USER")
        msg["To"] = to_email
        msg.set_content(body)
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            smtp.send_message(msg)
        return "✅ Email sent successfully"
    except Exception as e:
        return f"❌ Email failed: {str(e)}"