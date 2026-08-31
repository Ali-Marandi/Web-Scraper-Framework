import ipaddress
import unittest
from unittest.mock import patch

from core.security import assert_public_destination, safe_path, validate_url


class SecurityTests(unittest.TestCase):
    def test_validate_url_accepts_http_and_https(self):
        self.assertEqual(validate_url("https://example.com/a"), "https://example.com/a")
        self.assertEqual(validate_url("/a", base_url="https://example.com/root"), "https://example.com/a")

    def test_validate_url_rejects_unsafe_schemes_and_credentials(self):
        for value in ("file:///etc/passwd", "javascript:alert(1)", "https://user:pass@example.com"):
            with self.assertRaises(ValueError):
                validate_url(value)

    def test_safe_path_blocks_traversal(self):
        with self.assertRaises(ValueError):
            safe_path("/tmp/export", "../../etc/passwd")

    def test_public_destination_rejects_private_ip(self):
        with patch("core.security.resolve_host_addresses", return_value={ipaddress.ip_address("127.0.0.1")}):
            with self.assertRaises(ValueError):
                assert_public_destination("localhost")

    def test_public_destination_accepts_public_ip(self):
        with patch("core.security.resolve_host_addresses", return_value={ipaddress.ip_address("1.1.1.1")}):
            assert_public_destination("example.com")


if __name__ == "__main__":
    unittest.main()
