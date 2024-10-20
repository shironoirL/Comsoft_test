from django.contrib import admin
from .models import EmailAccount, EmailMessage, Attachment, Provider


# Register your models here.
@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "provider",
    )


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "body")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("uuid", "filename")


# @admin.register(Attachment)
# class AttachmentAdmin(admin.ModelAdmin):
#     list_display = ("name", "file")
#     search_fields = ("name", "file")
#     list_filter = ("name", "file")
