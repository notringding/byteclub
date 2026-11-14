"""
api.py - Talks to the public REST APIs used by the IP Address Information app.

Owner: Lorenz James M. Morales (Developer)

APIs used (all free, no API key needed):
    * ipify   - returns the computer's current public IP address.
        - https://api.ipify.org   -> IPv4 only
        - https://api6.ipify.org  -> IPv6 only (fails if the network has no IPv6)
    * ipapi.co - PRIMARY source of details for an IP address
                 (geolocation, ISP/organization, ASN, country code, timezone).
        - https://ipapi.co/<ip>/json/
    * ipwho.is - FALLBACK source of details, used only when ipapi.co fails
                 or returns a rate-limit error.
        - https://ipwho.is/<ip>

Every function here returns plain Python data (str / dict / None) so the
display module never has to know which API the data came from.
"""

import requests

# ---------------------------------------------------------------------------
# Settings - change these here instead of inside the functions.
# ---------------------------------------------------------------------------
IPV4_URL = "https://api.ipify.org?format=json"
IPV6_URL = "https://api6.ipify.org?format=json"
IPAPI_URL = "https://ipapi.co/{ip}/json/"
IPWHO_URL = "https://ipwho.is/{ip}"
TIMEOUT = 5  # seconds to wait for each API before giving up
RETRIES = 1  # extra tries when a request times out or the connection drops
HEADERS = {"User-Agent": "ByteClub-IPInfo/1.0"}  # ipapi.co blocks empty user agents


class APIError(Exception):
    """Raised when no API could return usable data."""


def _get(url):
    """GET a URL, trying again up to RETRIES times on a timeout or dropped connection.

    Slow school or mobile networks often fail once and then work on the
    next try, so one retry avoids switching to the fallback API too early.
    Other errors (HTTP 4xx/5xx, bad JSON) are not retried.
    """
    for attempt in range(RETRIES + 1):
        try:
            return requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            if attempt == RETRIES:
                raise


def get_public_ip(version=4):
    """Return the computer's public IPv4 (version=4) or IPv6 (version=6) address.

    Returns None instead of raising when the address is not available.
    This is normal for IPv6, because many home and school networks
    in the Philippines still do not have IPv6 connectivity.
    """
    url = IPV4_URL if version == 4 else IPV6_URL
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json().get("ip")
    except (requests.RequestException, ValueError):
        # ValueError covers a reply that is not valid JSON.
        return None


def _from_ipapi(ip):
    """Ask ipapi.co for details and convert them to our standard dictionary."""
    response = _get(IPAPI_URL.format(ip=ip))
    response.raise_for_status()
    data = response.json()
    # ipapi.co answers HTTP 200 with {"error": true, "reason": ...} when it
    # rate-limits us or the IP is reserved, so we must check the body too.
    if data.get("error"):
        raise APIError(data.get("reason", "ipapi.co returned an error"))
    return {
        "ip": data.get("ip"),
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country_name"),
        "country_code": data.get("country_code"),
        "postal": data.get("postal"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone"),
        "isp": data.get("org"),
        "asn": data.get("asn"),
        "source": "ipapi.co",
    }


def _from_ipwho(ip):
    """Ask ipwho.is for details and convert them to our standard dictionary."""
    response = _get(IPWHO_URL.format(ip=ip))
    response.raise_for_status()
    data = response.json()
    if not data.get("success", False):
        raise APIError(data.get("message", "ipwho.is returned an error"))
    connection = data.get("connection") or {}
    timezone = data.get("timezone") or {}
    asn = connection.get("asn")
    return {
        "ip": data.get("ip"),
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country"),
        "country_code": data.get("country_code"),
        "postal": data.get("postal"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": timezone.get("id"),
        "isp": connection.get("isp") or connection.get("org"),
        "asn": f"AS{asn}" if asn else None,  # ipwho.is gives 9299, ipapi.co gives AS9299
        "source": "ipwho.is",
    }


def get_ip_details(ip):
    """Return a dictionary of details for an IP address.

    Tries ipapi.co first, then ipwho.is. Raises APIError only if BOTH fail,
    with the reason from each API so the user knows what went wrong.
    """
    errors = []
    for provider in (_from_ipapi, _from_ipwho):
        try:
            return provider(ip)
        except (requests.RequestException, ValueError, APIError) as exc:
            errors.append(f"{provider.__name__[6:]}: {exc}")
    raise APIError("All IP information APIs failed -> " + " | ".join(errors))
