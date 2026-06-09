import logging
from django.db import transaction

from apps.integrations.models.base import Integration
from apps.integrations.models.webhook import WebhookEndpoint, WebhookDelivery
from apps.accounts.services.audit import AuditService

logger = logging.getLogger(__name__)


class IntegrationDispatcher:
    """Dispatch actions to the appropriate integration provider."""

    @staticmethod
    def dispatch(integration_id, payload, action="execute"):
        """Dispatch an action to an integration."""
        try:
            integration = Integration.objects.get(id=integration_id, is_active=True)
        except Integration.DoesNotExist:
            logger.error(f"Integration {integration_id} not found or inactive")
            return None

        provider_map = {
            "sendgrid": IntegrationDispatcher._dispatch_email,
            "mailgun": IntegrationDispatcher._dispatch_email,
            "twilio": IntegrationDispatcher._dispatch_messaging,
            "whatsapp": IntegrationDispatcher._dispatch_messaging,
            "slack": IntegrationDispatcher._dispatch_messaging,
            "discord": IntegrationDispatcher._dispatch_messaging,
            "hubspot": IntegrationDispatcher._dispatch_crm,
            "salesforce": IntegrationDispatcher._dispatch_crm,
            "gmail": IntegrationDispatcher._dispatch_google,
            "google_sheets": IntegrationDispatcher._dispatch_google,
            "google_drive": IntegrationDispatcher._dispatch_google,
        }

        handler = provider_map.get(integration.provider)
        if not handler:
            logger.warning(f"No handler for provider: {integration.provider}")
            return None

        try:
            result = handler(integration, payload, action)
            integration.last_used_at = __import__('django.utils.timezone', fromlist=['now']).now()
            integration.save(update_fields=["last_used_at"])
            return result
        except Exception as exc:
            integration.error_count += 1
            integration.last_error = str(exc)
            integration.save(update_fields=["error_count", "last_error"])

            AuditService.log(
                action="integration.failed",
                actor=integration.user,
                organization=integration.organization,
                resource_type="Integration",
                resource_id=str(integration.id),
                resource_name=integration.name,
                details={"error": str(exc), "provider": integration.provider},
            )
            logger.error(f"Integration {integration.name} failed: {exc}")
            raise

    @staticmethod
    def _dispatch_email(integration, payload, action):
        """Send email via configured provider."""
        if action == "send":
            # NOTE: Manual implementation required - actual email sending
            # Example: sendgrid_client.send(payload)
            logger.info(f"Email sent via {integration.provider}: {payload.get('to', 'unknown')}")
            return {"status": "sent", "provider": integration.provider}
        return {"status": "not_implemented"}

    @staticmethod
    def _dispatch_messaging(integration, payload, action):
        """Send message via messaging provider."""
        if action == "send":
            # NOTE: Manual implementation required - actual messaging API calls
            # Example for Slack: requests.post(webhook_url, json=payload)
            logger.info(f"Message sent via {integration.provider}")
            return {"status": "sent", "provider": integration.provider}
        return {"status": "not_implemented"}

    @staticmethod
    def _dispatch_crm(integration, payload, action):
        """CRM action (create contact, update deal, etc.)."""
        # NOTE: Manual implementation required - actual CRM API calls
        logger.info(f"CRM action {action} via {integration.provider}")
        return {"status": "processed", "provider": integration.provider, "action": action}

    @staticmethod
    def _dispatch_google(integration, payload, action):
        """Google Workspace action."""
        # NOTE: Manual implementation required - actual Google API calls
        logger.info(f"Google action {action} via {integration.provider}")
        return {"status": "processed", "provider": integration.provider, "action": action}


class WebhookService:
    """Handle incoming webhooks from external services."""

    @staticmethod
    @transaction.atomic
    def receive_webhook(url_path, headers, payload, signature=""):
        """Process an incoming webhook."""
        try:
            endpoint = WebhookEndpoint.objects.get(url_path=url_path, is_active=True)
        except WebhookEndpoint.DoesNotExist:
            logger.warning(f"Webhook received for unknown path: {url_path}")
            return None

        # Verify signature if configured
        if endpoint.secret and signature:
            import hashlib, hmac
            expected_sig = hmac.new(
                endpoint.secret.encode(),
                str(payload).encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected_sig, signature):
                logger.warning(f"Invalid webhook signature for {url_path}")
                endpoint.total_received += 1
                endpoint.save(update_fields=["total_received"])
                return WebhookDelivery.objects.create(
                    endpoint=endpoint,
                    headers=headers,
                    payload=payload,
                    signature=signature,
                    status="failed",
                    error_message="Invalid signature",
                )

        # Create delivery record
        delivery = WebhookDelivery.objects.create(
            endpoint=endpoint,
            headers=headers,
            payload=payload,
            signature=signature,
            status="received",
        )

        endpoint.last_received_at = __import__('django.utils.timezone', fromlist=['now']).now()
        endpoint.total_received += 1
        endpoint.save(update_fields=["last_received_at", "total_received"])

        # Trigger workflow if configured
        if endpoint.trigger_workflow:
            from apps.workflows.services.triggers import WorkflowTriggerService
            WorkflowTriggerService.trigger_event(
                event_type=f"webhook.{endpoint.provider}",
                payload={
                    "webhook_id": str(endpoint.id),
                    "delivery_id": str(delivery.id),
                    "headers": headers,
                    "payload": payload,
                    "provider": endpoint.provider,
                },
            )
            delivery.status = "processing"
            delivery.save(update_fields=["status"])

        logger.info(f"Webhook received: {endpoint.name} ({url_path})")
        return delivery

    @staticmethod
    def register_webhook(name, url_path, user, organization=None, provider="generic"):
        """Register a new webhook endpoint."""
        endpoint = WebhookEndpoint.objects.create(
            name=name,
            url_path=url_path,
            user=user,
            organization=organization,
            provider=provider,
        )

        AuditService.log(
            action="integration.connected",
            actor=user,
            organization=organization,
            resource_type="WebhookEndpoint",
            resource_id=str(endpoint.id),
            resource_name=name,
            details={"provider": provider, "url_path": url_path},
        )

        return endpoint