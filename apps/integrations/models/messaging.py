import uuid
import logging

from django.db import models

logger = logging.getLogger(__name__)


class MessagingProvider(models.Model):
    """Messaging integration (Twilio, WhatsApp, etc.)."""

    PROVIDER_CHOICES = [
        ("twilio_sms", "Twilio SMS"),
        ("twilio_whatsapp", "Twilio WhatsApp"),
        ("slack", "Slack"),
        ("discord", "Discord"),
        ("telegram", "Telegram"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey("Integration", on_delete=models.CASCADE, related_name="messaging_providers")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    config = models.JSONField(default=dict, blank=True)
    
    phone_number = models.CharField(max_length=50, blank=True, help_text="For SMS/WhatsApp")
    webhook_url = models.URLField(blank=True, help_text="For Slack/Discord incoming webhooks")
    channel_id = models.CharField(max_length=255, blank=True, help_text="Slack channel or Discord channel ID")
    bot_token = models.TextField(blank=True, help_text="Encrypted bot token")
    
    is_active = models.BooleanField(default=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    total_sent = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Messaging: {self.get_provider_display()}"