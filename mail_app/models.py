# mail_app/models.py

from django.db import models
import uuid


class Provider(models.TextChoices):
    YANDEX = "yandex", "Yandex"
    MAILRU = "mailru", "Mail.ru"
    GMAIL = "gmail", "Gmail"


class EmailAccount(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    provider = models.CharField(
        max_length=20, choices=Provider.choices, default=Provider.GMAIL
    )

    def __str__(self):
        return f"{self.email} ({self.get_provider_display()})"

    class Meta:
        db_table = "email_account"
        verbose_name = "Email Account"
        verbose_name_plural = "Email Accounts"


class EmailMessage(models.Model):
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
        return f"Subject: {self.subject}, Sent at: {self.sent_at}"


class Attachment(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_message = models.ForeignKey(
        EmailMessage, related_name="attachments", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="/attachments/")
    filename = models.CharField(max_length=255)

    class Meta:
        db_table = "attachments"
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"
        indexes = [
            models.Index(fields=["email_message"]),
        ]

    def __str__(self):
        return self.filename
