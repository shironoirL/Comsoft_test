from django.urls import path
from . import views
from .api.views import ProcessedEmailListAPIView

urlpatterns = [
    path("", views.email_list, name="email_list"),
    path(
        "api/processed_emails/",
        ProcessedEmailListAPIView.as_view(),
        name="processed-emails",
    ),
]
