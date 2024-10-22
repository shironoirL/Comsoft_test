from django.shortcuts import render
from .models import EmailMessage


def email_list(request):
    emails = EmailMessage.objects.all()
    return render(request, "mail_app/email_list.html", {"emails": emails})
