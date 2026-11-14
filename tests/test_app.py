"""
test_app.py - Automated tests for the IP Address Information app.

Owners: Miguel Andre F. Naguit and Lee Joseph J. Caceres (QA Testers)

Run from the project folder with:
    python -m unittest discover -v tests

The API tests use `unittest.mock` to fake the internet replies, so they
pass even without a connection and never use up the APIs' rate limits.
"""

import json
import tempfile
import unittest
from unittest import mock

import requests

from ipinfo_app import api, utils

IPAPI_SAMPLE = {
    "ip": "8.8.8.8", "city": "Mountain View", "region": "California",
    "country_name": "United States", "country_code": "US", "postal": "94043",
    "latitude": 37.42, "longitude": -122.08, "timezone": "America/Los_Angeles",
    "org": "GOOGLE", "asn": "AS15169",
}
IPWHO_SAMPLE = {
    "ip": "8.8.8.8", "success": True, "city": "Mountain View", "region": "California",
    "country": "United States", "country_code": "US", "postal": "94043",
    "latitude": 37.42, "longitude": -122.08,
    "timezone": {"id": "America/Los_Angeles"},
    "connection": {"asn": 15169, "isp": "Google LLC"},
}


def fake_response(payload, status=200):
    """Build a fake requests.Response-like object."""
    response = mock.Mock()
    response.status_code = status
    response.json.return_value = payload
    response.raise_for_status.side_effect = (
        None if status < 400 else requests.HTTPError(f"HTTP {status}")
    )
    return response


class TestValidation(unittest.TestCase):
    def test_valid_ipv4_and_ipv6(self):
        self.assertIsNotNone(utils.validate_ip("8.8.8.8"))
        self.assertIsNotNone(utils.validate_ip("2001:4860:4860::8888"))

    def test_invalid_input(self):
        for bad in ("", "abc", "256.1.1.1", "1.2.3", "8.8.8.8.8"):
            self.assertIsNone(utils.validate_ip(bad), bad)

    def test_whitespace_is_ignored(self):
        self.assertEqual(str(utils.validate_ip("  1.1.1.1 ")), "1.1.1.1")


class TestClassification(unittest.TestCase):
    def test_types(self):
        self.assertEqual(utils.classify_ip("8.8.8.8"), "Public (global)")
        self.assertEqual(utils.classify_ip("192.168.1.10"), "Private (RFC 1918 / ULA)")
        self.assertEqual(utils.classify_ip("127.0.0.1"), "Loopback")
        self.assertEqual(utils.classify_ip("169.254.1.1"), "Link-local")
        self.assertEqual(utils.classify_ip("224.0.0.1"), "Multicast")
        self.assertEqual(utils.classify_ip("100.64.0.1"), "Shared / CGNAT (special-use)")

    def test_other_private_ranges(self):
        # RFC 1918 has three private blocks, not just 192.168.0.0/16.
        self.assertEqual(utils.classify_ip("10.0.0.5"), "Private (RFC 1918 / ULA)")
        self.assertEqual(utils.classify_ip("172.16.0.1"), "Private (RFC 1918 / ULA)")

    def test_ipv6_types(self):
        self.assertEqual(utils.classify_ip("::1"), "Loopback")
        self.assertEqual(utils.classify_ip("fe80::1"), "Link-local")
        self.assertEqual(utils.classify_ip("fd00::1"), "Private (RFC 1918 / ULA)")
        self.assertEqual(utils.classify_ip("2001:4860:4860::8888"), "Public (global)")

    def test_ipv4_classes(self):
        self.assertEqual(utils.ipv4_class("10.0.0.5"), "A")
        self.assertEqual(utils.ipv4_class("172.16.0.1"), "B")
        self.assertEqual(utils.ipv4_class("230.0.0.1"), "D (multicast)")

    def test_ipv4_technical_details(self):
        details = utils.technical_details("192.168.1.1")
        self.assertEqual(details["Binary"], "11000000.10101000.00000001.00000001")
        self.assertEqual(details["Class"], "C")

    def test_ipv6_technical_details(self):
        details = utils.technical_details("2001:db8::1")
        self.assertEqual(details["Expanded"], "2001:0db8:0000:0000:0000:0000:0000:0001")
        self.assertEqual(details["Version"], "IPv6")


class TestAPI(unittest.TestCase):
    @mock.patch("ipinfo_app.api.requests.get")
    def test_public_ipv4(self, get):
        get.return_value = fake_response({"ip": "203.177.1.1"})
        self.assertEqual(api.get_public_ip(4), "203.177.1.1")

    @mock.patch("ipinfo_app.api.requests.get", side_effect=requests.ConnectionError)
    def test_no_ipv6_returns_none(self, _get):
        self.assertIsNone(api.get_public_ip(6))

    @mock.patch("ipinfo_app.api.requests.get")
    def test_primary_api(self, get):
        get.return_value = fake_response(IPAPI_SAMPLE)
        details = api.get_ip_details("8.8.8.8")
        self.assertEqual(details["asn"], "AS15169")
        self.assertEqual(details["source"], "ipapi.co")

    @mock.patch("ipinfo_app.api.requests.get")
    def test_fallback_when_rate_limited(self, get):
        get.side_effect = [
            fake_response({"error": True, "reason": "RateLimited"}),
            fake_response(IPWHO_SAMPLE),
        ]
        details = api.get_ip_details("8.8.8.8")
        self.assertEqual(details["source"], "ipwho.is")
        self.assertEqual(details["asn"], "AS15169")  # same format as ipapi.co
        self.assertEqual(details["timezone"], "America/Los_Angeles")

    @mock.patch("ipinfo_app.api.requests.get")
    def test_fallback_when_server_error(self, get):
        # ipapi.co returns HTTP 500, so ipwho.is should be used instead.
        get.side_effect = [fake_response({}, status=500), fake_response(IPWHO_SAMPLE)]
        self.assertEqual(api.get_ip_details("8.8.8.8")["source"], "ipwho.is")

    @mock.patch("ipinfo_app.api.requests.get", side_effect=requests.Timeout)
    def test_all_apis_down(self, _get):
        with self.assertRaises(api.APIError):
            api.get_ip_details("8.8.8.8")


class TestExport(unittest.TestCase):
    def test_json_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = utils.export_report({"ip": "8.8.8.8"}, "json", folder)
            self.assertEqual(json.loads(path.read_text())["ip"], "8.8.8.8")

    def test_txt_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = utils.export_report({"ip": "8.8.8.8"}, "txt", folder)
            self.assertIn("ip: 8.8.8.8", path.read_text())

    def test_maps_link(self):
        self.assertEqual(utils.maps_link(14.6, 120.98), "https://www.google.com/maps?q=14.6,120.98")
        self.assertIsNone(utils.maps_link(None, 120.98))


if __name__ == "__main__":
    unittest.main()
