
# src/agent/tools/email_tool.py
import os
import smtplib
from email.message import EmailMessage
from typing import Dict, Any


class EmailTool:
    """
    Tool to send HTML emails via SMTP.

    Environment variables required:
    - SMTP_SENDER_EMAIL: sender email address (e.g., your Gmail)
    - SMTP_SENDER_PASSWORD: sender password or app password

    Optional environment variables:
    - SMTP_HOST (default: smtp.gmail.com)
    - SMTP_PORT (default: 465 for SSL)
    """

    def __init__(self, smtp_host: str | None = None, smtp_port: int | None = None, use_ssl: bool = True):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "465"))
        self.use_ssl = use_ssl

    def run(self, email: Dict[str, str]) -> Dict[str, Any]:
        """
        Send an email.

        Expected keys in `email`:
        - recipient_email: str
        - subject: str
        - body: str (HTML allowed; a plain-text fallback is added automatically)

        Returns:
        - {"status": "success", "message": "..."} on success
        - {"status": "error", "message": "..."} on failure
        """
        recipient = email.get("recipient_email")
        subject = email.get("subject")
        body = email.get("body")

        if not recipient or not subject or not body:
            return {
                "status": "error",
                "message": "recipient_email, subject, and body are required.",
            }

        sender_email = os.getenv("SMTP_SENDER_EMAIL")
        sender_password = os.getenv("SMTP_SENDER_PASSWORD")

        if not sender_email or not sender_password:
            return {
                "status": "error",
                "message": "SMTP_SENDER_EMAIL or SMTP_SENDER_PASSWORD not set in environment.",
            }

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = recipient

            # Plain-text fallback
            msg.set_content(
                "Please use an HTML compatible email client to view this message."
            )
            # HTML version (your original behavior)
            msg.add_alternative(body, subtype="html")

            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)

            return {
                "status": "success",
                "message": f"Email sent to {recipient}.",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to send email: {e}",
            }