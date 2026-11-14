"""
utils.py - Offline helpers: IP validation, classification and report export.

Owner: John Edcel B. Lansigan (Scrum Leader / integration)

Nothing in this file uses the internet. It relies on Python's built-in
`ipaddress` module, so it can be unit-tested without network access.
"""

import ipaddress
import json
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path("reports")  # exported files are saved here


def validate_ip(text):
    """Return an ipaddress object if `text` is a valid IPv4/IPv6 address, else None."""
    try:
        return ipaddress.ip_address(text.strip())
    except (ValueError, AttributeError):
        return None


def classify_ip(ip):
    """Return a short label describing what kind of address this is.

    Network technicians use this to understand why an address cannot be
    looked up online (e.g. a 192.168.x.x address only exists inside a LAN).
    """
    addr = ip if not isinstance(ip, str) else ipaddress.ip_address(ip)
    if addr.is_loopback:
        return "Loopback"
    if addr.is_private:
        return "Private (RFC 1918 / ULA)" if not addr.is_link_local else "Link-local"
    if addr.is_multicast:
        return "Multicast"
    if addr.is_reserved or addr.is_unspecified:
        return "Reserved"
    if not addr.is_global:
        # e.g. 100.64.0.0/10, the carrier-grade NAT range many PH ISPs use
        return "Shared / CGNAT (special-use)"
    return "Public (global)"


def ipv4_class(ip):
    """Return the classful network class (A-E) of an IPv4 address, for reference."""
    first_octet = int(str(ip).split(".")[0])
    if first_octet < 128:
        return "A"
    if first_octet < 192:
        return "B"
    if first_octet < 224:
        return "C"
    if first_octet < 240:
        return "D (multicast)"
    return "E (experimental)"


def technical_details(ip):
    """Return extra addressing details that are useful to network technicians.

    IPv4 -> binary notation and classful class
    IPv6 -> full (exploded) and compressed forms
    """
    addr = ipaddress.ip_address(ip)
    details = {"Version": f"IPv{addr.version}", "Type": classify_ip(addr)}
    if addr.version == 4:
        details["Binary"] = ".".join(f"{int(octet):08b}" for octet in str(addr).split("."))
        details["Class"] = ipv4_class(addr)
    else:
        details["Expanded"] = addr.exploded
        details["Compressed"] = addr.compressed
    return details


def maps_link(latitude, longitude):
    """Return a Google Maps link for the coordinates, or None if they are missing."""
    if latitude is None or longitude is None:
        return None
    return f"https://www.google.com/maps?q={latitude},{longitude}"


def export_report(report, fmt="json", folder=REPORTS_DIR):
    """Save a report dictionary to reports/ as .json or .txt and return the file path."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Put the IP in the file name so reports are easy to tell apart.
    # ":" (IPv6) and "." are replaced because Windows file names can't use ":".
    ip_part = str(report.get("ip") or "unknown").replace(":", "-").replace(".", "-")
    path = folder / f"ip_report_{ip_part}_{stamp}.{fmt}"
    if fmt == "json":
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    else:
        lines = [f"{key}: {value}" for key, value in report.items()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
