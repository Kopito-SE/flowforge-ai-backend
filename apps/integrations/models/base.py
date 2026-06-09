import uuid
import logging
from django.contrib.auth.models import User
from django.db import models

logger = logging.getLogger(__name__)


class Integration(models.Model):
    """Base integration model for third-party services."""

    CATEGORY_CHOICES = [
        ("email", "Email"),
        ("messaging", "Messaging"),
        ("crm", "CRM"),
        ("google", "Google"),
        ("slack", "Slack / Discord"),
        ("webhook", "Webhook"),
        ("storage", "Storage"),
        ("other", "Other"),
    ]

    PROVIDER_CHOICES = [
        ("sendgrid", "SendGrid"),
        ("mailgun", "Mailgun"),
        ("twilio", "Twilio"),
        ("whatsapp", "WhatsApp"),
        ("hubspot", "HubSpot"),
        ("salesforce", "Salesforce"),
        ("gmail", "Gmail"),
        ("google_sheets", "Google Sheets"),
        ("google_drive", "Google Drive"),
        ("slack", "Slack"),
        ("discord", "Discord"),
        ("generic_webhook", "Generic Webhook"),
        ("custom", "Custom"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="integrations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="integrations")
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    config = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_connected = models.BooleanField(default=False)
    
    last_used_at = models.DateTimeField(null=True, blank=True)
    error_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["provider", "is_active"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"



class IntegrationConnection(models.Model):
    """Tracks connection status and credentials for an integration."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, related_name="connections")
    credentials = models.JSONField(default=dict, help_text="Encrypted connection credentials")
    scopes = models.JSONField(default=list, blank=True)
    
    is_valid = models.BooleanField(default=True)
    last_test_at = models.DateTimeField(null=True, blank=True)
    test_status = models.CharField(max_length=20, blank=True)
    test_error = models.TextField(blank=True)
    
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Connection for {self.integration.name}"


class OAuthToken(models.Model):
    """OAuth tokens for third-party integrations."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, related_name="oauth_tokens")
    access_token = models.TextField(help_text="Encrypted access token")
    refresh_token = models.TextField(blank=True, help_text="Encrypted refresh token")
    token_type = models.CharField(max_length=50, default="Bearer")
    scope = models.TextField(blank=True)
    
    expires_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OAuth for {self.integration.name}"