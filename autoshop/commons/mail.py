"""Email in py"""
import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.services.message import Email
from .. import settings

async def pymail(mail: Email):
    """Python email"""
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = mail.sender
    message["To"] = mail.receipient
    message["Subject"] = mail.subject

    # Add body to email
    message.attach(MIMEText(mail.message, "plain"))

    if mail.filename:
        part = build_attachment(mail.filename)
        # Add attachment to message and convert message to string
        message.attach(part)

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT, context=context) as server:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_USERNAME, mail.receipient, text)
    except ConnectionError:
        pass
    return mail.receipient

def build_attachment(filename):
    """Get file attachment"""
    # Open PDF file in binary mode
    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename=Monthly.csv",
    )
    return part
