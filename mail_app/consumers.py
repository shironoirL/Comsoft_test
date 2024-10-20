# mail_app/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import EmailAccount, EmailMessage, Attachment
from asgiref.sync import sync_to_async
import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
from dateutil.parser import parse
from datetime import datetime
from django.core.files.base import ContentFile


class EmailConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.user = self.scope["user"]

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("action") == "start_fetching":
            await self.fetch_emails()

    async def fetch_emails(self):
        # Assume only one email account for simplicity
        email_account = await sync_to_async(EmailAccount.objects.first)()
        if not email_account:
            await self.send(json.dumps({"error": "No email account configured."}))
            return

        # Call the email fetching function
        await self.fetch_emails_for_account(email_account)

        # Notify client that fetching is complete
        await self.send(json.dumps({"status": "complete"}))

    async def fetch_emails_for_account(self, account):
        try:
            mail = imaplib.IMAP4_SSL(self.get_imap_server(account.provider))
            mail.login(account.email, account.password)
            mail.select("inbox")

            # Fetch all emails
            result, data = mail.search(None, "ALL")
            if result != "OK":
                await self.send(json.dumps({"error": "Failed to search messages."}))
                return

            email_ids = data[0].split()
            total_emails = len(email_ids)
            if total_emails == 0:
                await self.send(
                    json.dumps({"status": "complete", "message": "No new messages."})
                )
                return

            # Process emails in batches
            batch_size = 50
            processed_emails = 0
            for i in range(0, total_emails, batch_size):
                batch_ids = email_ids[i : i + batch_size]
                for email_id in batch_ids:
                    result, msg_data = mail.fetch(email_id, "(RFC822)")
                    if result != "OK":
                        await self.send(
                            json.dumps(
                                {"error": f"Failed to fetch email with ID {email_id}."}
                            )
                        )
                        continue

                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)

                    # Process and save the email
                    await self.process_email(account, email_message, email_id.decode())

                    processed_emails += 1
                    progress = int((processed_emails / total_emails) * 100)
                    await self.send(
                        json.dumps({"status": "processing", "progress": progress})
                    )

            mail.logout()

        except Exception as e:
            await self.send(json.dumps({"error": f"An error occurred: {e}"}))

    def get_imap_server(self, provider):
        servers = {
            "gmail": "imap.gmail.com",
            "yandex": "imap.yandex.com",
            "mailru": "imap.mail.ru",
        }
        return servers.get(provider, "imap.gmail.com")

    async def process_email(self, account, email_message, uid):
        # Check if email already exists
        exists = await sync_to_async(
            EmailMessage.objects.filter(email_account=account, uid=uid).exists
        )()
        if exists:
            return

        subject = self.decode_header_value(email_message.get("Subject", ""))
        from_address = self.decode_header_value(email_message.get("From", ""))
        date_sent = email_message.get("Date", "")
        date_sent_parsed = self.parse_date(date_sent)
        date_sent_formatted = date_sent_parsed or datetime.now()

        body = self.extract_text_from_email(email_message)

        email_msg = await sync_to_async(EmailMessage.objects.create)(
            email_account=account,
            uid=uid,
            subject=subject,
            sent_at=date_sent_formatted,
            received_at=datetime.now(),
            body=body,
            from_address=from_address,
        )

        # Process attachments
        for part in email_message.walk():
            content_disposition = str(part.get("Content-Disposition") or "")
            if "attachment" in content_disposition.lower():
                filename = part.get_filename()
                if filename:
                    filename_decoded = self.decode_header_value(filename)
                    await self.save_attachment(email_msg, part, filename_decoded)

    def decode_header_value(self, value):
        if value:
            decoded_fragments = decode_header(value)
            decoded_string = ""
            for fragment, charset in decoded_fragments:
                if isinstance(fragment, bytes):
                    charset = charset or "utf-8"
                    fragment = fragment.decode(charset, errors="ignore")
                decoded_string += fragment
            cleaned_value = (
                decoded_string.replace('"', "")
                .replace("'", "")
                .replace("<", "")
                .replace(">", "")
                .replace("\x00", "")
            )
            return cleaned_value
        return ""

    def parse_date(self, date_str):
        try:
            if date_str:
                cleaned_date = date_str.split("\n")[-1].split(";")[-1].strip()
                return parse(cleaned_date)
        except Exception:
            return None
        return None

    def extract_text_from_email(self, msg):
        text = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition") or "")
                if (
                    content_type in ["text/plain", "text/html"]
                    and "attachment" not in content_disposition.lower()
                ):
                    part_text = part.get_payload(decode=True)
                    if part_text:
                        charset = part.get_content_charset() or "utf-8"
                        part_text = part_text.decode(charset, errors="ignore")
                        text += part_text
        else:
            part_text = msg.get_payload(decode=True)
            if part_text:
                charset = msg.get_content_charset() or "utf-8"
                text = part_text.decode(charset, errors="ignore")
        text = (
            BeautifulSoup(text, "html.parser").get_text().strip()
            or text
            or msg.as_string()
        )
        text = "".join(char for char in text if char.isprintable())
        text = " ".join(text.split())
        return text

    async def save_attachment(self, email_msg, part, filename):
        attachment = Attachment(email_message=email_msg, filename=filename)
        file_content = part.get_payload(decode=True)
        await sync_to_async(attachment.file.save)(filename, ContentFile(file_content))
        await sync_to_async(attachment.save)()
