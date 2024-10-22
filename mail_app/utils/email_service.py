import imaplib
import email
from mail_app.utils.email_utils import get_imap_server, process_email
import json
from ..models import EmailMessage
from asgiref.sync import sync_to_async


async def fetch_emails_for_account(account, send_callback):
    """
    Fetches new emails for the specified account and processes them if they are not already in the database.

    Args:
        account (EmailAccount): The email account to fetch emails from.
        send_callback (function): Callback to send progress or errors during the fetching process.

    Returns:
        None
    """
    try:
        # Set up IMAP connection
        mail = imaplib.IMAP4_SSL(get_imap_server(account.provider))
        mail.login(account.email, account.password)
        mail.select("inbox")

        # Search for all emails
        result, data = mail.uid("search", None, "ALL")
        if result != "OK":
            return await _send_error(
                send_callback, account.email, "Failed to search messages."
            )

        email_uids = data[0].split()

        if not email_uids:
            return await _send_complete(send_callback, account.email)

        # Fetch UIDs already present in the database for this account
        existing_uids = await sync_to_async(list)(
            EmailMessage.objects.filter(email_account=account).values_list(
                "uid", flat=True
            )
        )

        # Filter out emails that have already been fetched
        new_email_uids = [
            uid for uid in email_uids if uid.decode() not in existing_uids
        ]

        if not new_email_uids:
            return await _send_complete(send_callback, account.email)

        # Process new emails
        await _process_emails(account, mail, new_email_uids, send_callback)

        mail.logout()

    except Exception as e:
        await _send_error(send_callback, account.email, str(e))


async def _process_emails(account, mail, email_uids, send_callback):
    """
    Fetches and processes emails by UID.

    Args:
        account (EmailAccount): The email account to process emails for.
        mail (IMAP4_SSL): The IMAP connection object.
        email_uids (list): List of UIDs for the emails to be processed.
        send_callback (function): Callback to send progress during the process.

    Returns:
        None
    """
    total = len(email_uids)
    for idx, email_uid in enumerate(email_uids, 1):
        result, msg_data = mail.uid("fetch", email_uid, "(RFC822)")
        if result == "OK":
            email_message = email.message_from_bytes(msg_data[0][1])
            email_data = await process_email(account, email_message, email_uid.decode())
            await _send_progress(send_callback, email_data, idx, total, account.email)


async def _send_progress(send_callback, email_data, processed, total, account_email):
    """
    Sends progress information during email fetching.

    Args:
        send_callback (function): Callback to send progress information.
        email_data (dict): The processed email data.
        processed (int): The number of processed emails so far.
        total (int): The total number of emails to be processed.
        account_email (str): The email address of the account.

    Returns:
        None
    """
    progress = int((processed / total) * 100)
    await send_callback(
        json.dumps(
            {
                "status": "processing",
                "progress": progress,
                "processed_emails": processed,
                "total_emails": total,
                "account": account_email,
                "email": email_data,
            }
        )
    )


async def _send_error(send_callback, account_email, error_message):
    """
    Sends an error message via the callback.

    Args:
        send_callback (function): Callback to send error information.
        account_email (str): The email address of the account.
        error_message (str): The error message to be sent.

    Returns:
        None
    """
    await send_callback(
        json.dumps(
            {"error": f"An error occurred for account {account_email}: {error_message}"}
        )
    )


async def _send_complete(send_callback, account_email):
    """
    Sends a completion message when all emails have been processed.

    Args:
        send_callback (function): Callback to send completion information.
        account_email (str): The email address of the account.

    Returns:
        None
    """
    await send_callback(
        json.dumps(
            {
                "status": "complete",
                "message": f"No new messages for account {account_email}.",
                "account": account_email,
            }
        )
    )
