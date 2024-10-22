from django.db import models
import uuid


class Provider(models.TextChoices):
    """
    Enum-like class for email providers.

    Provides choices for popular email providers, such as Yandex, Mail.ru, and Gmail.
    """

    YANDEX = "yandex", "Yandex"
    MAILRU = "mailru", "Mail.ru"
    GMAIL = "gmail", "Gmail"


class EmailAccount(models.Model):
    """
    Model representing an email account for a user.

    Attributes:
        email (EmailField): The email address for the account.
        password (CharField): The account password (stored securely).
        provider (CharField): The email provider (e.g., Yandex, Mail.ru, Gmail).
    """

    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    provider = models.CharField(
        max_length=20, choices=Provider.choices, default=Provider.GMAIL
    )

    def __str__(self):
        """Returns a human-readable string representation of the email account."""
        return f"{self.email} ({self.get_provider_display()})"

    class Meta:
        db_table = "email_account"
        verbose_name = "Email Account"
        verbose_name_plural = "Email Accounts"


class EmailMessage(models.Model):
    """
    Model representing an email message.

    Attributes:
        email_account (ForeignKey): The email account to which the message belongs.
        uid (CharField): Unique ID of the email in the context of the email account.
        subject (CharField): The subject of the email.
        sent_at (DateTimeField): The time when the email was sent.
        received_at (DateTimeField): The time when the email was received.
        body (TextField): The body of the email.
        from_address (EmailField): The sender's email address.
    """

    email_account = models.ForeignKey(
        EmailAccount, related_name="messages", on_delete=models.CASCADE
    )
    uid = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    body = models.TextField(blank=True, null=True)
    from_address = models.EmailField(blank=True, null=True)

    class Meta:
        db_table = "email_message"
        ordering = ["-received_at"]
        unique_together = ("email_account", "uid")
        indexes = [
            models.Index(fields=["email_account", "uid"]),
            models.Index(fields=["received_at"]),
        ]

    def __str__(self):
        """Returns a human-readable string representation of the email message."""
        return f"Subject: {self.subject}, Sent at: {self.sent_at}"


class Attachment(models.Model):
    """
    Model representing an email attachment.

    Attributes:
        uuid (UUIDField): The unique identifier for the attachment.
        email_message (ForeignKey): The email message to which this attachment belongs.
        file (FileField): The file associated with the attachment.
        filename (CharField): The original name of the file.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_message = models.ForeignKey(
        EmailMessage, related_name="attachments", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="attachments/")
    filename = models.CharField(max_length=255)

    class Meta:
        db_table = "attachments"
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"
        indexes = [
            models.Index(fields=["email_message"]),
        ]

    def __str__(self):
        """Returns a human-readable string representation of the attachment."""
        return self.filename
