from datetime import timedelta
from django.utils import timezone
from apps.executions.models import CircuitBreaker

class CircuitBreakerOpen(Exception):
    pass

class CircuitBreakerService:
    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 60
    HALF_OPEN_MAX_REQUESTS = 3  # Allow only 3 test requests

    @classmethod
    def allow_request(cls, service_name):
        breaker, _ = CircuitBreaker.objects.get_or_create(
            service_name=service_name
        )

        # CLOSED state
        if not breaker.is_open and not breaker.is_half_open:
            return True

        # HALF-OPEN state
        if breaker.is_half_open:
            if breaker.half_open_requests_made < cls.HALF_OPEN_MAX_REQUESTS:
                breaker.half_open_requests_made += 1
                breaker.save()
                return True
            else:
                raise CircuitBreakerOpen(f"Half-open max requests reached for {service_name}")

        # OPEN state - check if timeout elapsed
        if breaker.opened_at:
            elapsed = timezone.now() - breaker.opened_at
            if elapsed > timedelta(seconds=cls.RECOVERY_TIMEOUT):
                # Transition to HALF-OPEN (not directly to CLOSED)
                breaker.is_open = False
                breaker.is_half_open = True
                breaker.half_open_requests_made = 1
                breaker.save()

                return True

        raise CircuitBreakerOpen(f"Circuit Open for {service_name}")

    @classmethod
    def record_success(cls, service_name):
        breaker, _ = CircuitBreaker.objects.get_or_create(
            service_name=service_name
        )

        if breaker.is_half_open:
            # Success in half-open → CLOSE the circuit
            breaker.is_open = False
            breaker.is_half_open = False
            breaker.failure_count = 0
            breaker.half_open_requests_made = 0
        else:
            # Normal success in closed state
            breaker.failure_count = 0

        breaker.save()

    @classmethod
    def record_failure(cls, service_name):
        breaker, _ = CircuitBreaker.objects.get_or_create(
            service_name=service_name
        )

        breaker.failure_count += 1

        if breaker.is_half_open:
            # Failure in half-open → RE-OPEN the circuit
            breaker.is_open = True
            breaker.is_half_open = False
            breaker.opened_at = timezone.now()
            breaker.half_open_requests_made = 0
        elif not breaker.is_open and breaker.failure_count >= cls.FAILURE_THRESHOLD:
            # Normal failure threshold reached → OPEN
            breaker.is_open = True
            breaker.opened_at = timezone.now()

        breaker.save()
