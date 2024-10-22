import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import EmailAccount
from asgiref.sync import sync_to_async
from mail_app.utils.email_service import fetch_emails_for_account


class EmailConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling email fetching actions.
    Fetches emails for all accounts upon receiving a start command from the client.
    """

    async def connect(self):
        """Accepts the WebSocket connection and sets the user from the request scope."""
        await self.accept()
        self.user = self.scope["user"]

    async def receive(self, text_data):
        """Handles incoming WebSocket messages and triggers email fetching if requested."""
        data = json.loads(text_data)
        if data.get("action") == "start_fetching":
            await self.fetch_emails()

    async def fetch_emails(self):
        """
        Fetches emails for all configured email accounts.
        Sends progress updates via WebSocket as each account is processed.
        """
        email_accounts = await sync_to_async(list)(EmailAccount.objects.all())

        if not email_accounts:
            await self.send(json.dumps({"error": "No email accounts configured."}))
            return
        await asyncio.gather(
            *[
                fetch_emails_for_account(account, self.send)
                for account in email_accounts
            ]
        )
        await self.send(json.dumps({"status": "complete"}))
