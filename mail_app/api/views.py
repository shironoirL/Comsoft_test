from ..models import EmailMessage
from .serializers import EmailMessageSerializer
from rest_framework.response import Response
from rest_framework.views import APIView


class ProcessedEmailListAPIView(APIView):
    """
    API View to retrieve the list of processed emails.
    """

    def get(self, request):
        emails = EmailMessage.objects.all()
        total_emails = emails.count()
        processed_emails = EmailMessage.objects.filter(
            received_at__isnull=False
        ).count()  # Example condition

        serializer = EmailMessageSerializer(emails, many=True)
        return Response(
            {
                "total_emails": total_emails,
                "processed_emails": processed_emails,
                "emails": serializer.data,
            }
        )
