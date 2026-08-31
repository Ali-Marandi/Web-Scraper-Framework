import os
import unittest
from unittest.mock import patch

from core.config import AppConfig


class ConfigTests(unittest.TestCase):
    def test_defaults_are_conservative(self):
        with patch.dict(os.environ, {}, clear=True):
            cfg = AppConfig.from_env()
        self.assertEqual(cfg.api_host, "127.0.0.1")
        self.assertEqual(cfg.api_port, 8765)
        self.assertEqual(cfg.max_concurrency, 8)
        self.assertEqual(cfg.max_crawl_depth, 3)

    def test_environment_overrides(self):
        values = {
            "WEBSCRAPER_API_HOST": "127.0.0.1",
            "WEBSCRAPER_API_PORT": "9000",
            "WEBSCRAPER_REQUEST_TIMEOUT": "45",
            "WEBSCRAPER_MAX_CONCURRENCY": "16",
            "WEBSCRAPER_MAX_RESPONSE_BYTES": "2097152",
            "WEBSCRAPER_MAX_CRAWL_DEPTH": "5",
        }
        with patch.dict(os.environ, values, clear=True):
            cfg = AppConfig.from_env()
        self.assertEqual(cfg.api_port, 9000)
        self.assertEqual(cfg.request_timeout_seconds, 45.0)
        self.assertEqual(cfg.max_concurrency, 16)
        self.assertEqual(cfg.max_response_bytes, 2097152)
        self.assertEqual(cfg.max_crawl_depth, 5)

    def test_invalid_values_fail_closed(self):
        with patch.dict(os.environ, {"WEBSCRAPER_MAX_CONCURRENCY": "1000"}, clear=True):
            with self.assertRaises(ValueError):
                AppConfig.from_env()


if __name__ == "__main__":
    unittest.main()
