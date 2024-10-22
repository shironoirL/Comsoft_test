from rest_framework import serializers
from ..models import EmailMessage, Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["uuid", "file", "filename"]


class EmailMessageSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = EmailMessage
        fields = [
            "subject",
            "from_address",
            "sent_at",
            "received_at",
            "body",
            "attachments",
        ]
