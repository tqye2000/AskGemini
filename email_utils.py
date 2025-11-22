"""
Email utility functions for AskGemini app.
"""
from typing import Optional, Dict, Any
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from io import BytesIO
from datetime import datetime
import streamlit as st
from PIL import Image

def build_email_message(sender_email: str, receive: str, subject: str, message: str, res: Optional[Dict[str, Any]] = None) -> MIMEMultipart:
    """
    Build an email message with optional image attachment.
    """
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receive
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    # Attach image if present (non-blocking)
    if isinstance(res, dict) and "image" in res:
        try:
            with BytesIO() as buffer:
                imageFile = res["image"]
                if isinstance(imageFile, Image.Image):
                    imageFile.save(buffer, format="JPEG")
                    img = MIMEImage(buffer.getvalue())
                    msg.attach(img)
        except Exception as attach_ex:
            print(f"Failed to attach image: {attach_ex}")
    return msg

def send_mail(query: str, res: Any, total_tokens: int) -> None:
    """
    Robust send_mail: timeout, STARTTLS + fallback to SSL, exception handling so UI won't crash.
    """
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    message = f'[{date_time}] {st.session_state.user}:({st.session_state.user_ip}:: {st.session_state.user_location}):\n'
    message += f'Model: {st.session_state.model_version}\n'
    message += f'[You]: {query}\n'
    if isinstance(res, dict) and 'text' in res:
        generated_text = res["text"]
    else:
        generated_text = "No text generated!"
    message += f'[Gemini]: {generated_text}\n'
    message += f'[Tokens]: {total_tokens}\n'

    smtp_server = st.secrets.get("smtp_server", "smtp.gmail.com")
    port = int(st.secrets.get("smtp_port", 587))
    sender_email = st.secrets.get("gmail_user")
    password = st.secrets.get("gmail_passwd")
    receive = st.secrets.get("receive_mail")

    if not (smtp_server and sender_email and password and receive):
        print("Email not sent: SMTP credentials or destination missing in secrets.")
        return

    server = None
    timeout = 10  # seconds
    try:
        # Try STARTTLS (typical for port 587)
        try:
            server = smtplib.SMTP(smtp_server, port, timeout=timeout)
            server.ehlo()
            if port == 587:
                server.starttls()
                server.ehlo()
            server.login(sender_email, password)
        except Exception as e1:
            print(f"STARTTLS failed: {e1!r} — trying SSL fallback")
            try:
                server = smtplib.SMTP_SSL(smtp_server, 465, timeout=timeout)
                server.login(sender_email, password)
            except Exception as e2:
                print(f"SMTP_SSL fallback failed: {e2!r}")
                return

        msg = build_email_message(
            sender_email=sender_email,
            receive=receive,
            subject=f"Gemini chat from {st.session_state.user}",
            message=message,
            res=res
        )
        server.send_message(msg)
        print("Email sent ok.")
    except Exception as ex:
        print(f"send_mail error: {ex!r}")
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
