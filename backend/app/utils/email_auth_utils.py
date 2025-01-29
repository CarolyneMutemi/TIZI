"""
Email authentication utilities.
"""
import yagmail
from app.core.config import EMAIL_PASSWORD

def send_email_verification_link(user_email: str, token: str) -> bool:
    """
    Send email verification link to email.
    """
    sender_email = "carolmkaysmamba14@gmail.com"
    subject = "Finish logging in to your account."
    body = f"""\
    Hello there! Just a security measure...\n
    <a href='http://localhost:8000/auth/verify?token={token}'>Click here to verify your email.</a>
    """
    try:
        yag = yagmail.SMTP(sender_email, EMAIL_PASSWORD)
        yag.send(to=user_email, subject=subject, contents=body)
        print("Email sent successfully!")
        yag.close()
        return True
    except Exception as e:
        print("Error sending email: ", e)
        return False

