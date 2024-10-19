from django.db import models


class EmailMessage(models.Model):
    """1) id
    2) Тема сообщения (наименование)
    3) Дата отправки
    4) Дата получения
    5) Описание или текст сообщения
    6) Поле для хранения списка прикреплённых файлов к письму"""

    subject = models.CharField(max_length=255)
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    body = models.TextField()
    attachments_names = models.JSONField(null=True, blank=True)
    attachment_ids = models.JSONField(null=True, blank=True)
    from_inbox_address = models.JSONField(null=True, blank=True)
    # email_account = models.ForeignKey("Email_Account")

    def __str__(self):
        return f"Subject: {self.subject}, Sent at: {self.sent_at}"

    class Meta:
        ordering = ["received_at"]


class Attachment(models.Model):
    uuid = models.UUIDField(primary_key=True)
    email = models.ForeignKey(
        EmailMessage, related_name="attachments", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="attachments/")
    filename = models.CharField(max_length=255)


class Provider(models.TextChoices):
    YANDEX = "yandex", "Yandex"
    MAILRU = "mailru", "Mail.ru"
    GMAIL = "gmail.com", "Gmail"


class EmailAccount(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    provider = models.CharField(
        max_length=50, choices=Provider.choices, default=Provider.GMAIL
    )

    def __str__(self):
        return f"{self.email} ({self.provider})"
