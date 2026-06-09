import uuid
import logging

from django.db import models


logger = logging.getLogger(__name__)


class EmailProvider(models.Model):
    """Email integration provider configuration (SendGrid, Mailgun, etc.)."""

    PROVIDER_CHOICES = [
        ("sendgrid", "SendGrid"),
        ("mailgun", "Mailgun"),
        ("smtp", "Custom SMTP"),
        ("ses", "Amazon SES"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey("Integration", on_delete=models.CASCADE, related_name="email_providers")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    api_key = models.TextField(blank=True, help_text="Encrypted API key")
    domain = models.CharField(max_length=255, blank=True)
    from_email = models.EmailField()
    from_name = models.CharField(max_length=255, blank=True)
    
    is_verified = models.BooleanField(default=False)
    daily_limit = models.PositiveIntegerField(default=1000)
    daily_sent = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Email: {self.get_provider_display()} ({self.from_email})"


class EmailTemplate(models.Model):
    """Pre-defined email template for workflow email nodes."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="email_templates")
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)
    variables = models.JSONField(default=list, blank=True, help_text="List of template variables")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name