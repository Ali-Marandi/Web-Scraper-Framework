"""
WebScraper Pro - Proxy Manager
Manages proxy rotation, validation, and health monitoring for commercial-grade scraping.
"""

import random
import time
import threading
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum


class ProxyType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


@dataclass
class ProxyConfig:
    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    max_fails: int = 3
    timeout: float = 10.0

    @property
    def url(self) -> str:
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type.value}://{self.host}:{self.port}"

    @property
    def display_name(self) -> str:
        auth = f"***:***@" if self.username else ""
        return f"{self.proxy_type.value}://{auth}{self.host}:{self.port}"

    @property
    def requests_proxy(self) -> Dict[str, str]:
        base = f"{self.proxy_type.value}://{self.host}:{self.port}"
        if self.username and self.password:
            base = f"{self.proxy_type.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return {"http": base, "https": base}


@dataclass
class ProxyStats:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    last_used: float = 0.0
    consecutive_fails: int = 0
    is_healthy: bool = True
    banned: bool = False

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


class ProxyManager:
    """
    Advanced proxy manager with rotation, health checking, and failover.
    
    Features:
    - Multiple rotation strategies (round-robin, random, least-used, fastest)
    - Automatic health monitoring and failover
    - Proxy testing and validation
    - Support for HTTP, HTTPS, SOCKS4, SOCKS5
    - Thread-safe operations
    - Configurable fail thresholds and recovery
    """

    def __init__(self):
        self._proxies: Dict[str, ProxyConfig] = {}
        self._stats: Dict[str, ProxyStats] = {}
        self._lock = threading.RLock()
        self._current_index = 0
        self._rotation_strategy = "random"
        self._test_url = "https://httpbin.org/ip"
        self._test_timeout = 10.0
        self._auto_remove_banned = True
        self._max_consecutive_fails = 5

    @property
    def proxy_count(self) -> int:
        with self._lock:
            return len(self._proxies)

    @property
    def healthy_proxy_count(self) -> int:
        with self._lock:
            return sum(1 for s in self._stats.values() if s.is_healthy and not s.banned)

    @property
    def rotation_strategy(self) -> str:
        return self._rotation_strategy

    @rotation_strategy.setter
    def rotation_strategy(self, strategy: str):
        valid = ["random", "round_robin", "least_used", "fastest"]
        if strategy not in valid:
            raise ValueError(f"Invalid strategy. Must be one of: {valid}")
        self._rotation_strategy = strategy

    def add_proxy(self, config: ProxyConfig) -> None:
        """Add a proxy to the pool."""
        with self._lock:
            key = config.display_name
            self._proxies[key] = config
            if key not in self._stats:
                self._stats[key] = ProxyStats()

    def add_proxy_from_string(self, proxy_string: str, proxy_type: ProxyType = ProxyType.HTTP) -> None:
        """
        Add proxy from string format: host:port or user:pass@host:port
        """
        username, password = None, None

        if "@" in proxy_string:
            auth, host_port = proxy_string.rsplit("@", 1)
            if ":" in auth:
                username, password = auth.split(":", 1)
        else:
            host_port = proxy_string

        if ":" not in host_port:
            raise ValueError(f"Invalid proxy format: {proxy_string}")

        host, port_str = host_port.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            raise ValueError(f"Invalid port in proxy: {proxy_string}")

        config = ProxyConfig(
            host=host.strip(),
            port=port,
            proxy_type=proxy_type,
            username=username,
            password=password,
        )
        self.add_proxy(config)

    def add_proxies_from_file(self, file_path: str, proxy_type: ProxyType = ProxyType.HTTP) -> int:
        """Load proxies from a file (one per line)."""
        count = 0
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        self.add_proxy_from_string(line, proxy_type)
                        count += 1
                    except ValueError:
                        continue
        return count

    def remove_proxy(self, display_name: str) -> bool:
        """Remove a proxy from the pool."""
        with self._lock:
            if display_name in self._proxies:
                del self._proxies[display_name]
                if display_name in self._stats:
                    del self._stats[display_name]
                return True
            return False

    def clear_all(self) -> None:
        """Remove all proxies."""
        with self._lock:
            self._proxies.clear()
            self._stats.clear()
            self._current_index = 0

    def get_proxy(self) -> Optional[ProxyConfig]:
        """Get the next proxy based on rotation strategy."""
        with self._lock:
            healthy = [
                (k, v) for k, v in self._proxies.items()
                if self._stats.get(k, ProxyStats()).is_healthy
                and not self._stats.get(k, ProxyStats()).banned
            ]

            if not healthy:
                return None

            if self._rotation_strategy == "random":
                key, config = random.choice(healthy)
            elif self._rotation_strategy == "round_robin":
                idx = self._current_index % len(healthy)
                key, config = healthy[idx]
                self._current_index = (self._current_index + 1) % len(healthy)
            elif self._rotation_strategy == "least_used":
                key, config = min(healthy, key=lambda x: self._stats[x[0]].total_requests)
            elif self._rotation_strategy == "fastest":
                key, config = min(
                    healthy,
                    key=lambda x: self._stats[x[0]].avg_response_time if self._stats[x[0]].avg_response_time > 0 else 999,
                )
            else:
                key, config = healthy[0]

            return config

    def report_success(self, proxy_config: ProxyConfig, response_time: float) -> None:
        """Report a successful request through this proxy."""
        key = proxy_config.display_name
        with self._lock:
            if key in self._stats:
                stats = self._stats[key]
                stats.total_requests += 1
                stats.successful_requests += 1
                stats.total_response_time += response_time
                stats.avg_response_time = stats.total_response_time / stats.successful_requests
                stats.last_used = time.time()
                stats.consecutive_fails = 0
                stats.is_healthy = True

    def report_failure(self, proxy_config: ProxyConfig) -> None:
        """Report a failed request through this proxy."""
        key = proxy_config.display_name
        with self._lock:
            if key in self._stats:
                stats = self._stats[key]
                stats.total_requests += 1
                stats.failed_requests += 1
                stats.last_used = time.time()
                stats.consecutive_fails += 1

                if stats.consecutive_fails >= self._max_consecutive_fails:
                    stats.is_healthy = False
                    stats.banned = True
                    if self._auto_remove_banned:
                        self._proxies.pop(key, None)

    def test_proxy(self, proxy_config: ProxyConfig, timeout: Optional[float] = None) -> Dict:
        """
        Test a single proxy and return results.
        Returns dict with: success, response_time, ip, error
        """
        timeout = timeout or self._test_timeout
        result = {
            "proxy": proxy_config.display_name,
            "success": False,
            "response_time": 0.0,
            "ip": None,
            "error": None,
        }

        try:
            start = time.time()
            resp = requests.get(
                self._test_url,
                proxies=proxy_config.requests_proxy,
                timeout=timeout,
            )
            elapsed = time.time() - start

            if resp.status_code == 200:
                result["success"] = True
                result["response_time"] = round(elapsed, 3)
                try:
                    data = resp.json()
                    result["ip"] = data.get("origin", "unknown")
                except Exception:
                    pass
            else:
                result["error"] = f"HTTP {resp.status_code}"
        except requests.exceptions.Timeout:
            result["error"] = "Timeout"
        except requests.exceptions.ConnectionError as e:
            result["error"] = "Connection error"
        except Exception as e:
            result["error"] = str(e)[:100]

        return result

    def test_all_proxies(self, callback=None, max_workers: int = 10) -> List[Dict]:
        """
        Test all proxies concurrently and return results.
        Optional callback receives progress updates.
        """
        results = []
        proxies_to_test = []

        with self._lock:
            proxies_to_test = list(self._proxies.values())

        total = len(proxies_to_test)
        completed = [0]
        lock = threading.Lock()

        def _test(p: ProxyConfig):
            r = self.test_proxy(p)
            with lock:
                results.append(r)
                completed[0] += 1
                if callback:
                    callback(completed[0], total, r)

        threads = []
        for proxy in proxies_to_test:
            t = threading.Thread(target=_test, args=(proxy,))
            threads.append(t)
            t.start()
            if len(threads) >= max_workers:
                threads[0].join()
                threads.pop(0)

        for t in threads:
            t.join()

        # Update health based on test results
        with self._lock:
            for r in results:
                key = r["proxy"]
                if key in self._stats:
                    if r["success"]:
                        self._stats[key].is_healthy = True
                        self._stats[key].banned = False
                    else:
                        self._stats[key].is_healthy = False

        return sorted(results, key=lambda x: x["response_time"] if x["success"] else 999)

    def get_all_stats(self) -> List[Dict]:
        """Get statistics for all proxies."""
        with self._lock:
            stats = []
            for key, proxy in self._proxies.items():
                s = self._stats.get(key, ProxyStats())
                stats.append({
                    "proxy": key,
                    "type": proxy.proxy_type.value,
                    "total_requests": s.total_requests,
                    "successful": s.successful_requests,
                    "failed": s.failed_requests,
                    "success_rate": round(s.success_rate, 1),
                    "avg_time": round(s.avg_response_time, 3),
                    "healthy": s.is_healthy,
                    "banned": s.banned,
                })
            return stats

    def get_summary(self) -> Dict:
        """Get overall proxy pool summary."""
        with self._lock:
            total_reqs = sum(s.total_requests for s in self._stats.values())
            total_succ = sum(s.successful_requests for s in self._stats.values())
            return {
                "total_proxies": len(self._proxies),
                "healthy_proxies": self.healthy_proxy_count,
                "total_requests": total_reqs,
                "total_successful": total_succ,
                "overall_success_rate": round((total_succ / total_reqs * 100) if total_reqs > 0 else 0, 1),
                "rotation_strategy": self._rotation_strategy,
            }
