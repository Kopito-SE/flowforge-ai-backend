from django.db import models


class CircuitBreakerState(models.TextChoices):
    CLOSED = 'closed', 'Closed'
    OPEN = 'open', 'Open'
    HALF_OPEN = 'half_open', 'Half Open'

class CircuitBreaker(models.Model):

    service_name = models.CharField(
        max_length=100,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=CircuitBreakerState.choices,
        default=CircuitBreakerState.CLOSED
    )

    failure_count = models.IntegerField(
        default=0
    )

    opened_at = models.DateTimeField(
        null=True,
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    half_open_requests_made = models.IntegerField(
        default=0
    )

    """class Meta:
        indexes = [
            models.Index(fields=['service_name', 'status']),
        ]
    """

    def __str__(self):
        return f"{self.service_name} - {self.get_status_display()}"

    @property
    def is_open(self):
        return self.status == CircuitBreakerState.OPEN

    @property
    def is_half_open(self):
        return self.status == CircuitBreakerState.HALF_OPEN

    @property
    def is_closed(self):
        return self.status == CircuitBreakerState.CLOSED
