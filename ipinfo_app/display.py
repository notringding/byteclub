"""
display.py - Everything the user sees: banner, colors, tables and menu.

Owner: Marc Jherald V. Marcelo (Developer)

Uses:
    * colorama - colored text that also works in the Windows terminal
    * tabulate - neat, aligned tables
"""

from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)  # resets the color after every print (needed on Windows)

TABLE_STYLE = "rounded_outline"
NOT_AVAILABLE = Fore.LIGHTBLACK_EX + "Not available" + Style.RESET_ALL


def banner():
    """Print the app title."""
    line = "=" * 52
    print(Fore.CYAN + line)
    print(Fore.CYAN + Style.BRIGHT + "   BYTE CLUB  |  IP Address Information App")
    print(Fore.CYAN + "   Public IPv4 / IPv6, geolocation, ISP and ASN")
    print(Fore.CYAN + line)


def menu():
    """Print the main menu and return the user's choice as a string."""
    options = [
        ["1", "Show my public IPv4 and IPv6 addresses"],
        ["2", "Show full details of my public IP"],
        ["3", "Look up any IP address"],
        ["4", "Export the last report (JSON / TXT)"],
        ["5", "Exit"],
    ]
    print()
    print(tabulate(options, headers=["#", "Option"], tablefmt=TABLE_STYLE))
    return input(Fore.YELLOW + "Choose an option (1-5): " + Style.RESET_ALL).strip()


def _value(value):
    """Show 'Not available' in gray instead of None or an empty string."""
    return NOT_AVAILABLE if value in (None, "") else value


def show_addresses(ipv4, ipv6):
    """Print the IPv4/IPv6 summary table with a green or red status column."""
    rows = []
    for label, address in (("IPv4", ipv4), ("IPv6", ipv6)):
        status = Fore.GREEN + "Connected" if address else Fore.RED + "No connectivity"
        rows.append([label, _value(address), status + Style.RESET_ALL])
    print()
    print(tabulate(rows, headers=["Version", "Public address", "Status"], tablefmt=TABLE_STYLE))
    if not ipv6:
        info("No IPv6 address found. Your ISP or network may not support IPv6 yet.")


def show_details(details, technical, map_url=None):
    """Print the full details table for one IP address."""
    rows = [
        ["IP address", _value(details.get("ip"))],
        *[[key, value] for key, value in technical.items()],
        ["City", _value(details.get("city"))],
        ["Region", _value(details.get("region"))],
        ["Country", _value(details.get("country"))],
        ["Country code", _value(details.get("country_code"))],
        ["Postal code", _value(details.get("postal"))],
        ["Coordinates", _value(_coords(details))],
        ["Timezone", _value(details.get("timezone"))],
        ["ISP / Organization", _value(details.get("isp"))],
        ["ASN", _value(details.get("asn"))],
        ["Map", _value(map_url)],
    ]
    print()
    print(tabulate(rows, headers=[Fore.CYAN + "Field", "Value" + Style.RESET_ALL], tablefmt=TABLE_STYLE))
    print(Fore.LIGHTBLACK_EX + f"Data source: {details.get('source', 'unknown')}")


def _coords(details):
    lat, lon = details.get("latitude"), details.get("longitude")
    return f"{lat}, {lon}" if lat is not None and lon is not None else None


def success(message):
    print(Fore.GREEN + "[OK] " + message)


def info(message):
    print(Fore.YELLOW + "[i] " + message)


def error(message):
    print(Fore.RED + "[!] " + message)
