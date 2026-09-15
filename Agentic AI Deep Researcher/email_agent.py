from agents import Agent, function_tool, ModelSettings
import requests
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv(override = True)

MODEL_NAME = "gpt-5.4-mini"

settings = ModelSettings(tool_choice="required")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"


@function_tool
def send_email_tool(subject: str, text_body: str, html_body: str) -> str:
    """
    Send out an email with the given subject and body

    Args:
        subject: The subject of the email
        text_body: The body of the email as plain text
        html_body: The HTML body of the email
    """
    email_status = "not attempted"
    push_status = "not attempted"

    try:
        msg = EmailMessage()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_ADDRESS
        msg["Subject"] = subject
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(EMAIL_SMTP_SERVER, 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(msg)
        email_status = "sent"
    except Exception as e:
        email_status = f"FAILED: {e}"
        print(f"[send_email_tool] Email send failed: {e}")

    try:
        message = f"Subject: {subject}\n\n{text_body}"
        payload = {"user": pushover_user, "token": pushover_token, "message": message}
        resp = requests.post(pushover_url, data=payload, timeout=10)
        resp.raise_for_status()
        push_status = "sent"
    except Exception as e:
        push_status = f"FAILED: {e}"
        print(f"[send_email_tool] Pushover notification failed: {e}")

    return f"Email: {email_status}. Push notification: {push_status}."

    


INSTRUCTIONS = """
You are provided with a detailed report. Use your tool to send an email, converting the report into
a clean, well presented HTML email with an appropriate subject line.
"""

email_agent = Agent(name = "Email Agent", instructions=INSTRUCTIONS, tools = [send_email_tool],model=MODEL_NAME, model_settings=settings)