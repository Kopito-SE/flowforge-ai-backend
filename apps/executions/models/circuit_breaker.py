from django.db import models

class CircuitBreaker(models.Model):

    service_name = models.CharField(
        max_length=100,
        unique=True
    )

    failure_count = models.IntegerField(
        default=0
    )

    is_open = models.BooleanField(
        default=False
    )

    opened_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    half_open_requests_made = models.IntegerField(
        default=0
    )

    is_half_open = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.service_name
