import hashlib
import logging
import time
from enum import Enum
from typing import Optional, Dict, Any

import redis
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# =========================
# Queue Priorities
# =========================

class QueuePriority(str, Enum):
    """Priority levels for task queues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def celery_queue(self):
        return f"celery_{self.value}"

    @property
    def weight(self):
        weights = {
            "critical": 100,
            "high": 10,
            "medium": 1,
            "low": 0.1,
        }
        return weights.get(self.value, 1)


class QueuePrioritizer:
    """Service for managing queue priorities and routing."""

    QUEUE_MAP = {
        "email": QueuePriority.LOW,
        "webhook": QueuePriority.MEDIUM,
        "ai": QueuePriority.HIGH,
        "notification": QueuePriority.HIGH,
        "default": QueuePriority.MEDIUM,
    }

    @staticmethod
    def get_queue_for_task(task_name: str) -> str:
        """Determine the appropriate queue for a task."""
        for keyword, priority in QueuePrioritizer.QUEUE_MAP.items():
            if keyword in task_name.lower():
                return priority.celery_queue
        return QueuePriority.MEDIUM.celery_queue

    @staticmethod
    def get_priority_for_task(task_name: str) -> QueuePriority:
        """Get the priority for a task."""
        for keyword, priority in QueuePrioritizer.QUEUE_MAP.items():
            if keyword in task_name.lower():
                return priority
        return QueuePriority.MEDIUM

    @staticmethod
    def route_task(task_name: str, args=None, kwargs=None):
        """Route a task to the appropriate queue with priority."""
        queue = QueuePrioritizer.get_queue_for_task(task_name)
        return {
            "queue": queue,
            "routing_key": queue,
        }


class QueuePartitionService:
    """Service for managing queue partitioning."""

    PARTITIONS = {
        "email": "email_queue",
        "webhook": "webhook_queue",
        "ai": "ai_queue",
        "default": "default_queue",
    }

    @staticmethod
    def get_partition(task_type: str) -> str:
        """Get the partition for a task type."""
        return QueuePartitionService.PARTITIONS.get(task_type, QueuePartitionService.PARTITIONS["default"])

    @staticmethod
    def get_queue_health() -> Dict[str, Any]:
        """Get health status for all queues."""
        import redis as redis_client
        try:
            client = redis_client.from_url(settings.CELERY_BROKER_URL)
            queues = {}
            for partition in QueuePartitionService.PARTITIONS.values():
                queue_key = f"celery@{partition}"
                length = client.llen(queue_key)
                queues[partition] = {
                    "length": length,
                    "status": "healthy" if length < 1000 else "backlogged",
                }
            return queues
        except Exception as exc:
            logger.error(f"Failed to get queue health: {exc}")
            return {}


# =========================
# Rate Limiting
# =========================

class RateLimiter:
    """Token bucket rate limiter using Redis."""

    def __init__(self, key: str, max_requests: int = 100, window_seconds: int = 3600):
        self.key = f"ratelimit:{key}"
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def allow_request(self) -> bool:
        """Check if a request is allowed under the rate limit."""
        try:
            client = redis.from_url(settings.CELERY_BROKER_URL)
            current = client.get(self.key)
            
            if current is None:
                # First request - set counter
                client.setex(self.key, self.window_seconds, 1)
                return True

            count = int(current)
            if count >= self.max_requests:
                return False

            client.incr(self.key)
            return True

        except Exception as exc:
            logger.error(f"Rate limiter error: {exc}")
            return True  # Fallback: allow on error

    def get_remaining(self) -> int:
        """Get remaining requests in the current window."""
        try:
            client = redis.from_url(settings.CELERY_BROKER_URL)
            current = client.get(self.key)
            if current is None:
                return self.max_requests
            return max(0, self.max_requests - int(current))
        except Exception:
            return self.max_requests


class RateLimitService:
    """Service for managing rate limits across the system."""

    @staticmethod
    def check_api_rate_limit(user_id: str, endpoint: str) -> bool:
        """Check API rate limit for a user on an endpoint."""
        # Rate limit: 1000 requests per hour per endpoint per user
        limiter = RateLimiter(
            key=f"api:{user_id}:{endpoint}",
            max_requests=1000,
            window_seconds=3600,
        )
        return limiter.allow_request()

    @staticmethod
    def check_webhook_rate_limit(webhook_id: str) -> bool:
        """Check webhook rate limit."""
        # Rate limit: 100 webhooks per minute
        limiter = RateLimiter(
            key=f"webhook:{webhook_id}",
            max_requests=100,
            window_seconds=60,
        )
        return limiter.allow_request()

    @staticmethod
    def check_execution_rate_limit(workflow_id: str) -> bool:
        """Check workflow execution rate limit."""
        # Rate limit: 100 executions per minute per workflow
        limiter = RateLimiter(
            key=f"execution:{workflow_id}",
            max_requests=100,
            window_seconds=60,
        )
        return limiter.allow_request()

    @staticmethod
    def get_remaining_api_calls(user_id: str, endpoint: str) -> int:
        """Get remaining API calls for a user."""
        limiter = RateLimiter(key=f"api:{user_id}:{endpoint}")
        return limiter.get_remaining()


# =========================
# Distributed Locks
# =========================

class DistributedLock:
    """Distributed lock using Redis to prevent duplicate operations."""

    def __init__(self, lock_name: str, timeout: int = 60):
        self.lock_key = f"lock:{lock_name}"
        self.timeout = timeout

    def acquire(self, token: Optional[str] = None) -> bool:
        """Acquire the distributed lock."""
        try:
            client = redis.from_url(settings.CELERY_BROKER_URL)
            token = token or str(time.time())
            acquired = client.setnx(self.lock_key, token)
            if acquired:
                client.expire(self.lock_key, self.timeout)
                return True
            return False
        except Exception as exc:
            logger.error(f"Lock acquire error: {exc}")
            return True  # Fallback: allow on error

    def release(self, token: Optional[str] = None) -> bool:
        """Release the distributed lock."""
        try:
            client = redis.from_url(settings.CELERY_BROKER_URL)
            current = client.get(self.lock_key)
            if current and token and current.decode() == token:
                client.delete(self.lock_key)
                return True
            return False
        except Exception as exc:
            logger.error(f"Lock release error: {exc}")
            return True

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class DistributedLockService:
    """Service for managing distributed locks."""

    @staticmethod
    def prevent_duplicate_execution(workflow_id: str, context_hash: str) -> bool:
        """
        Prevent duplicate workflow executions with the same context.
        Returns True if execution should proceed, False if duplicate.
        """
        lock_key = f"workflow_execution:{workflow_id}:{context_hash}"
        lock = DistributedLock(lock_name=lock_key, timeout=300)  # 5 minute lock
        
        if lock.acquire():
            return True  # Not a duplicate
        return False  # Duplicate detected

    @staticmethod
    def lock_workflow(workflow_id: str) -> bool:
        """Lock a workflow to prevent concurrent modifications."""
        lock = DistributedLock(lock_name=f"workflow_edit:{workflow_id}", timeout=60)
        return lock.acquire()

    @staticmethod
    def unlock_workflow(workflow_id: str) -> bool:
        """Unlock a workflow after editing."""
        client = redis.from_url(settings.CELERY_BROKER_URL)
        return client.delete(f"lock:workflow_edit:{workflow_id}") > 0