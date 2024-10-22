from email.header import decode_header
from bs4 import BeautifulSoup
from dateutil.parser import parse
from datetime import datetime
from django.core.files.base import ContentFile
from mail_app.models import EmailMessage, Attachment
from asgiref.sync import sync_to_async


def get_imap_server(provider):
    """
    Returns the IMAP server for the given provider.
    Defaults to Gmail if the provider is not recognized.
    """
    return {
        "gmail": "imap.gmail.com",
        "yandex": "imap.yandex.com",
        "mailru": "imap.mail.ru",
    }.get(provider, "imap.gmail.com")


async def process_email(account, email_message, uid):
    """
    Processes an incoming email: extracts body, attachments, and stores in the database.

    Args:
        account (EmailAccount): The email account associated with this message.
        email_message (email.message.EmailMessage): The email message object.
        uid (str): Unique ID of the email message.

    Returns:
        dict: A dictionary with the formatted email data, including subject, body, and attachments.
    """
    if await sync_to_async(
        EmailMessage.objects.filter(email_account=account, uid=uid).exists
    )():
        return None
    email_msg = await sync_to_async(EmailMessage.objects.create)(
        email_account=account,
        uid=uid,
        subject=decode_header_value(email_message.get("Subject", "")),
        from_address=decode_header_value(email_message.get("From", "")),
        sent_at=parse_date(email_message.get("Date", "")) or datetime.now(),
        received_at=datetime.now(),
        body=extract_body_content(email_message),
    )
    attachments = await process_attachments(email_msg, email_message)
    return format_email_data(email_msg, attachments)


def decode_header_value(value):
    """
    Decodes an email header to a readable string, handling encoding issues.

    Args:
        value (str): The header value to decode.

    Returns:
        str: The decoded header string.
    """
    return (
        "".join(
            (
                fragment.decode(charset or "utf-8", errors="ignore")
                if isinstance(fragment, bytes)
                else fragment
            )
            for fragment, charset in decode_header(value)
        )
        .replace('"', "")
        .replace("'", "")
        .strip()
    )


def parse_date(date_str):
    """
    Parses a date string from an email header.

    Args:
        date_str (str): The date string to parse.

    Returns:
        datetime or None: Parsed datetime object or None if parsing fails.
    """
    try:
        return (
            parse(date_str.split("\n")[-1].split(";")[-1].strip()) if date_str else None
        )
    except Exception:
        return None


def extract_body_content(msg):
    """
    Extracts the text or HTML content from an email, preferring plain text if available.

    Args:
        msg (email.message.EmailMessage): The email message object.

    Returns:
        str: The extracted email body text or a fallback to the raw message.
    """
    text, html = [], []

    for part in msg.walk() if msg.is_multipart() else [msg]:
        content_type = part.get_content_type()
        disposition = part.get("Content-Disposition", "").lower()
        if "attachment" in disposition or content_type not in [
            "text/plain",
            "text/html",
        ]:
            continue

        content = part.get_payload(decode=True).decode(
            part.get_content_charset() or "utf-8", errors="ignore"
        )
        (text if content_type == "text/plain" else html).append(content)
    return (
        " ".join(text).strip()
        or BeautifulSoup("".join(html), "html.parser").get_text(separator=" ").strip()
        or msg.as_string()[:200]
    )


async def process_attachments(email_msg, email_message):
    """
    Processes attachments in an email and saves them to the database.

    Args:
        email_msg (EmailMessage): The email message object from the database.
        email_message (email.message.EmailMessage): The email message object from the IMAP server.

    Returns:
        list: A list of dictionaries containing filenames and URLs of saved attachments.
    """
    return [
        {"filename": attachment.filename, "url": attachment.file.url}
        for part in email_message.walk()
        if "attachment" in (part.get("Content-Disposition") or "").lower()
        if (
            attachment := await save_attachment(
                email_msg, part, decode_header_value(part.get_filename())
            )
        )
    ]


async def save_attachment(email_msg, part, filename):
    """
    Saves an email attachment to the file system and database.

    Args:
        email_msg (EmailMessage): The email message object from the database.
        part (email.message.Message): The email part representing the attachment.
        filename (str): The name of the file to save.

    Returns:
        Attachment: The saved attachment object.
    """
    attachment = Attachment(email_message=email_msg, filename=filename)
    await sync_to_async(attachment.file.save)(
        filename, ContentFile(part.get_payload(decode=True))
    )
    await sync_to_async(attachment.save)()
    return attachment


def format_email_data(email_msg, attachments):
    """
    Formats the email data into a dictionary to be returned or displayed.

    Args:
        email_msg (EmailMessage): The email message object from the database.
        attachments (list): A list of attachment data for the email.

    Returns:
        dict: A dictionary containing the email's subject, from address, dates, body, and attachments.
    """
    return {
        "subject": email_msg.subject,
        "from_address": email_msg.from_address,
        "sent_at": (
            email_msg.sent_at.strftime("%Y-%m-%d %H:%M:%S") if email_msg.sent_at else ""
        ),
        "received_at": email_msg.received_at.strftime("%Y-%m-%d %H:%M:%S"),
        "body": email_msg.body[:50],
        "attachments": attachments,
    }
