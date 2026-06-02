from datetime import timedelta

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.executions.models import CircuitBreaker, CircuitBreakerState


class CircuitBreakerOpen(Exception):
    pass


class CircuitBreakerService:
    FAILURE_THRESHOLD = 3
    RECOVERY_TIMEOUT = 60
    HALF_OPEN_MAX_REQUESTS = 3

    @classmethod
    def _cache_key(cls, service_name):
        return f"circuit_breaker:{service_name}:open"

    @classmethod
    def _get_breaker(cls, service_name, for_update=False):
        """Helper to get circuit breaker with optional lock."""
        queryset = (
            CircuitBreaker.objects.select_for_update()
            if for_update
            else CircuitBreaker.objects
        )
        breaker, _ = queryset.get_or_create(
            service_name=service_name,
            defaults={"status": CircuitBreakerState.CLOSED},
        )
        return breaker

    @classmethod
    def allow_request(cls, service_name):
        cache_key = cls._cache_key(service_name)

        if cache.get(cache_key):
            breaker = cls._get_breaker(service_name)
            if breaker.status == CircuitBreakerState.OPEN and breaker.opened_at:
                elapsed = timezone.now() - breaker.opened_at
                if elapsed < timedelta(seconds=cls.RECOVERY_TIMEOUT):
                    raise CircuitBreakerOpen(f"Circuit Open for {service_name}")

            cache.delete(cache_key)

        with transaction.atomic():
            breaker = cls._get_breaker(service_name, for_update=True)

            if breaker.status == CircuitBreakerState.CLOSED:
                cache.delete(cache_key)
                return True

            if breaker.status == CircuitBreakerState.HALF_OPEN:
                if breaker.half_open_requests_made >= cls.HALF_OPEN_MAX_REQUESTS:
                    raise CircuitBreakerOpen(
                        f"Half-open max requests reached for {service_name}"
                    )

                breaker.half_open_requests_made += 1
                breaker.save()
                return True

            if breaker.status == CircuitBreakerState.OPEN and breaker.opened_at:
                elapsed = timezone.now() - breaker.opened_at

                if elapsed >= timedelta(seconds=cls.RECOVERY_TIMEOUT):
                    breaker.status = CircuitBreakerState.HALF_OPEN
                    breaker.half_open_requests_made = 1
                    breaker.opened_at = None
                    breaker.save()
                    cache.delete(cache_key)
                    return True

        raise CircuitBreakerOpen(f"Circuit Open for {service_name}")

    @classmethod
    def record_success(cls, service_name):
        with transaction.atomic():
            breaker = cls._get_breaker(service_name, for_update=True)

            breaker.status = CircuitBreakerState.CLOSED
            breaker.failure_count = 0
            breaker.half_open_requests_made = 0
            breaker.opened_at = None
            breaker.save()
            cache.delete(cls._cache_key(service_name))

    @classmethod
    def record_failure(cls, service_name):
        with transaction.atomic():
            breaker = cls._get_breaker(service_name, for_update=True)

            if breaker.status == CircuitBreakerState.OPEN:
                return

            if breaker.status == CircuitBreakerState.HALF_OPEN:
                breaker.status = CircuitBreakerState.OPEN
                breaker.failure_count = cls.FAILURE_THRESHOLD
                breaker.half_open_requests_made = 0
                breaker.opened_at = timezone.now()
                breaker.save()
                cache.set(
                    cls._cache_key(service_name),
                    True,
                    timeout=cls.RECOVERY_TIMEOUT,
                )
                return

            breaker.failure_count += 1

            if breaker.failure_count >= cls.FAILURE_THRESHOLD:
                breaker.status = CircuitBreakerState.OPEN
                breaker.opened_at = timezone.now()
                breaker.half_open_requests_made = 0
                cache.set(
                    cls._cache_key(service_name),
                    True,
                    timeout=cls.RECOVERY_TIMEOUT,
                )

            breaker.save()

    @classmethod
    def reset(cls, service_name):
        """Manually reset a circuit breaker to closed state."""
        with transaction.atomic():
            breaker = cls._get_breaker(service_name, for_update=True)
            breaker.status = CircuitBreakerState.CLOSED
            breaker.failure_count = 0
            breaker.half_open_requests_made = 0
            breaker.opened_at = None
            breaker.save()
            cache.delete(cls._cache_key(service_name))

    @classmethod
    def get_state(cls, service_name):
        """Get current state without modifying anything."""
        breaker = cls._get_breaker(service_name)
        return breaker.status
