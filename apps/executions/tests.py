from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.executions.models import CircuitBreaker, CircuitBreakerState
from apps.executions.services.circuit_breaker import (
    CircuitBreakerOpen,
    CircuitBreakerService,
)


class CircuitBreakerServiceTests(TestCase):
    def setUp(self):
        self.service_name = "webhook_service"
        CircuitBreakerService.reset(self.service_name)

    def _get_breaker(self):
        return CircuitBreaker.objects.get(service_name=self.service_name)

    def test_opens_after_three_failures_and_allows_three_half_open_requests(self):
        for _ in range(3):
            CircuitBreakerService.record_failure(self.service_name)

        breaker = self._get_breaker()

        self.assertEqual(breaker.status, CircuitBreakerState.OPEN)
        self.assertEqual(breaker.failure_count, 3)

        with self.assertRaises(CircuitBreakerOpen):
            CircuitBreakerService.allow_request(self.service_name)

        breaker.opened_at = timezone.now() - timedelta(seconds=61)
        breaker.save(update_fields=["opened_at"])

        self.assertTrue(CircuitBreakerService.allow_request(self.service_name))
        breaker.refresh_from_db()
        self.assertEqual(breaker.status, CircuitBreakerState.HALF_OPEN)
        self.assertEqual(breaker.half_open_requests_made, 1)

        self.assertTrue(CircuitBreakerService.allow_request(self.service_name))
        self.assertTrue(CircuitBreakerService.allow_request(self.service_name))

        breaker.refresh_from_db()
        self.assertEqual(breaker.half_open_requests_made, 3)

        with self.assertRaises(CircuitBreakerOpen):
            CircuitBreakerService.allow_request(self.service_name)

    def test_half_open_success_closes_the_circuit(self):
        for _ in range(3):
            CircuitBreakerService.record_failure(self.service_name)

        breaker = self._get_breaker()
        breaker.opened_at = timezone.now() - timedelta(seconds=61)
        breaker.save(update_fields=["opened_at"])

        self.assertTrue(CircuitBreakerService.allow_request(self.service_name))
        CircuitBreakerService.record_success(self.service_name)

        breaker.refresh_from_db()
        self.assertEqual(breaker.status, CircuitBreakerState.CLOSED)
        self.assertEqual(breaker.failure_count, 0)
        self.assertEqual(breaker.half_open_requests_made, 0)
        self.assertIsNone(breaker.opened_at)

    def test_half_open_failure_reopens_the_circuit(self):
        for _ in range(3):
            CircuitBreakerService.record_failure(self.service_name)

        breaker = self._get_breaker()
        breaker.opened_at = timezone.now() - timedelta(seconds=61)
        breaker.save(update_fields=["opened_at"])

        self.assertTrue(CircuitBreakerService.allow_request(self.service_name))
        CircuitBreakerService.record_failure(self.service_name)

        breaker.refresh_from_db()
        self.assertEqual(breaker.status, CircuitBreakerState.OPEN)
        self.assertEqual(breaker.failure_count, 3)
        self.assertEqual(breaker.half_open_requests_made, 0)
        self.assertIsNotNone(breaker.opened_at)
