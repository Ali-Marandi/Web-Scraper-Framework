"""
WebScraper Pro - Rate Limiter
Advanced rate limiting with multiple algorithms, per-domain tracking, and adaptive throttling.
"""

import time
import threading
from collections import defaultdict, deque
from typing import Optional, Dict
from dataclasses import dataclass, field
from enum import Enum


class LimitStrategy(Enum):
    FIXED = "fixed"           # Fixed delay between requests
    TOKEN_BUCKET = "token_bucket"  # Token bucket algorithm
    SLIDING_WINDOW = "sliding_window"  # Sliding window counter
    ADAPTIVE = "adaptive"     # Adaptive based on response times


@dataclass
class DomainLimits:
    """Per-domain rate limiting configuration."""
    requests_per_second: float = 2.0
    requests_per_minute: float = 60.0
    burst_size: int = 5
    min_delay: float = 0.5
    max_delay: float = 30.0
    adaptive_enabled: bool = False
    backoff_factor: float = 2.0


class TokenBucket:
    """Token bucket rate limiter implementation."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """Try to consume tokens. Returns True if successful."""
        deadline = (time.monotonic() + timeout) if timeout else None

        while True:
            with self._lock:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
                wait_time = (tokens - self.tokens) / self.rate

            if deadline and time.monotonic() + wait_time > deadline:
                return False

            time.sleep(min(wait_time, 0.1))

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now


class SlidingWindowCounter:
    """Sliding window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: deque = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        """Check if a request is allowed under the rate limit."""
        with self._lock:
            now = time.monotonic()
            cutoff = now - self.window_seconds

            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()

            if len(self._timestamps) < self.max_requests:
                self._timestamps.append(now)
                return True
            return False

    def wait_time(self) -> float:
        """Calculate time until next request is allowed."""
        with self._lock:
            if not self._timestamps:
                return 0.0
            oldest = self._timestamps[0]
            return max(0.0, (oldest + self.window_seconds) - time.monotonic())


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies and per-domain tracking.

    Features:
    - Fixed delay, token bucket, sliding window, and adaptive strategies
    - Per-domain rate limiting
    - Automatic backoff on errors
    - Global and per-domain concurrency limits
    - Statistics tracking
    """

    def __init__(self, strategy: LimitStrategy = LimitStrategy.TOKEN_BUCKET):
        self._strategy = strategy
        self._domain_limits: Dict[str, DomainLimits] = {}
        self._domain_buckets: Dict[str, TokenBucket] = {}
        self._domain_windows: Dict[str, SlidingWindowCounter] = {}
        self._domain_last_request: Dict[str, float] = {}
        self._domain_response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self._domain_current_delay: Dict[str, float] = {}
        self._domain_consecutive_errors: Dict[str, int] = defaultdict(int)
        self._global_lock = threading.Lock()
        self._domain_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._global_rps = 10.0
        self._global_bucket: Optional[TokenBucket] = None
        self._total_requests = 0
        self._total_wait_time = 0.0
        self._default_limits = DomainLimits()

        self._update_global_bucket()

    def _update_global_bucket(self):
        self._global_bucket = TokenBucket(self._global_rps, burst_size=int(self._global_rps * 2))

    @property
    def global_rps(self) -> float:
        return self._global_rps

    @global_rps.setter
    def global_rps(self, value: float):
        self._global_rps = max(0.1, value)
        self._update_global_bucket()

    def set_domain_limits(self, domain: str, limits: DomainLimits) -> None:
        """Set rate limits for a specific domain."""
        self._domain_limits[domain] = limits
        self._domain_buckets[domain] = TokenBucket(
            limits.requests_per_second,
            limits.burst_size,
        )
        self._domain_windows[domain] = SlidingWindowCounter(
            int(limits.requests_per_minute),
            60.0,
        )
        self._domain_current_delay[domain] = limits.min_delay

    def _get_domain_limits(self, domain: str) -> DomainLimits:
        return self._domain_limits.get(domain, self._default_limits)

    def _get_domain_bucket(self, domain: str) -> TokenBucket:
        if domain not in self._domain_buckets:
            limits = self._get_domain_limits(domain)
            self._domain_buckets[domain] = TokenBucket(limits.requests_per_second, limits.burst_size)
        return self._domain_buckets[domain]

    def _get_domain_window(self, domain: str) -> SlidingWindowCounter:
        if domain not in self._domain_windows:
            limits = self._get_domain_limits(domain)
            self._domain_windows[domain] = SlidingWindowCounter(int(limits.requests_per_minute), 60.0)
        return self._domain_windows[domain]

    def acquire(self, domain: str = "default", timeout: Optional[float] = 30.0) -> bool:
        """
        Acquire permission to make a request.
        Blocks until permission is granted or timeout expires.
        """
        # Global rate limit
        if self._global_bucket:
            if not self._global_bucket.consume(timeout=timeout):
                return False

        # Domain-specific rate limiting
        if self._strategy == LimitStrategy.FIXED:
            return self._acquire_fixed(domain, timeout)
        elif self._strategy == LimitStrategy.TOKEN_BUCKET:
            return self._acquire_token_bucket(domain, timeout)
        elif self._strategy == LimitStrategy.SLIDING_WINDOW:
            return self._acquire_sliding_window(domain, timeout)
        elif self._strategy == LimitStrategy.ADAPTIVE:
            return self._acquire_adaptive(domain, timeout)
        return True

    def _acquire_fixed(self, domain: str, timeout: Optional[float]) -> bool:
        limits = self._get_domain_limits(domain)
        delay = limits.min_delay

        with self._domain_locks[domain]:
            last = self._domain_last_request.get(domain, 0)
            elapsed = time.monotonic() - last
            if elapsed < delay:
                wait = delay - elapsed
                if timeout and wait > timeout:
                    return False
                time.sleep(wait)

            self._domain_last_request[domain] = time.monotonic()
            self._total_requests += 1
            return True

    def _acquire_token_bucket(self, domain: str, timeout: Optional[float]) -> bool:
        bucket = self._get_domain_bucket(domain)
        success = bucket.consume(timeout=timeout)
        if success:
            with self._domain_locks[domain]:
                self._total_requests += 1
        return success

    def _acquire_sliding_window(self, domain: str, timeout: Optional[float]) -> bool:
        window = self._get_domain_window(domain)
        deadline = (time.monotonic() + timeout) if timeout else None

        while True:
            if window.allow():
                self._total_requests += 1
                return True

            wait = window.wait_time()
            if deadline and time.monotonic() + wait > deadline:
                return False
            time.sleep(min(wait, 0.1))

    def _acquire_adaptive(self, domain: str, timeout: Optional[float]) -> bool:
        limits = self._get_domain_limits(domain)
        current_delay = self._domain_current_delay.get(domain, limits.min_delay)

        with self._domain_locks[domain]:
            last = self._domain_last_request.get(domain, 0)
            elapsed = time.monotonic() - last

            if elapsed < current_delay:
                wait = current_delay - elapsed
                if timeout and wait > timeout:
                    return False
                time.sleep(wait)

            self._domain_last_request[domain] = time.monotonic()
            self._total_requests += 1
            return True

    def report_response_time(self, domain: str, response_time: float) -> None:
        """Report response time for adaptive rate limiting."""
        self._domain_response_times[domain].append(response_time)

        if self._strategy == LimitStrategy.ADAPTIVE:
            limits = self._get_domain_limits(domain)
            if limits.adaptive_enabled:
                times = list(self._domain_response_times[domain])
                if times:
                    avg_time = sum(times) / len(times)
                    # Increase delay if response time is growing
                    new_delay = avg_time * 1.5
                    new_delay = max(limits.min_delay, min(limits.max_delay, new_delay))
                    self._domain_current_delay[domain] = new_delay

    def report_error(self, domain: str) -> None:
        """Report an error for adaptive backoff."""
        self._domain_consecutive_errors[domain] += 1

        if self._strategy == LimitStrategy.ADAPTIVE:
            limits = self._get_domain_limits(domain)
            errors = self._domain_consecutive_errors[domain]
            new_delay = self._domain_current_delay.get(domain, limits.min_delay)
            new_delay = min(limits.max_delay, new_delay * limits.backoff_factor)
            self._domain_current_delay[domain] = new_delay

    def report_success(self, domain: str) -> None:
        """Report a successful request (resets error counter)."""
        self._domain_consecutive_errors[domain] = 0
        if self._strategy == LimitStrategy.ADAPTIVE:
            limits = self._get_domain_limits(domain)
            current = self._domain_current_delay.get(domain, limits.min_delay)
            # Gradually reduce delay on success
            new_delay = max(limits.min_delay, current * 0.9)
            self._domain_current_delay[domain] = new_delay

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        return {
            "strategy": self._strategy.value,
            "global_rps": self._global_rps,
            "total_requests": self._total_requests,
            "tracked_domains": len(self._domain_limits),
            "domains": {
                d: {
                    "current_delay": round(self._domain_current_delay.get(d, 0), 3),
                    "consecutive_errors": self._domain_consecutive_errors[d],
                    "avg_response_time": round(
                        sum(self._domain_response_times[d]) / len(self._domain_response_times[d]), 3
                    ) if self._domain_response_times[d] else 0,
                }
                for d in self._domain_limits
            },
        }

    def reset(self, domain: Optional[str] = None) -> None:
        """Reset rate limiter state."""
        if domain:
            self._domain_consecutive_errors.pop(domain, None)
            self._domain_current_delay.pop(domain, None)
            self._domain_response_times.pop(domain, None)
            self._domain_last_request.pop(domain, None)
        else:
            self._domain_consecutive_errors.clear()
            self._domain_current_delay.clear()
            self._domain_response_times.clear()
            self._domain_last_request.clear()
            self._total_requests = 0
