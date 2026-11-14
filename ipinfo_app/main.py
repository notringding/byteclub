"""
main.py - Entry point of the Byte Club IP Address Information app.

Run it from the project folder with:
    python -m ipinfo_app.main            (interactive menu)
    python -m ipinfo_app.main --ip 8.8.8.8   (look up one address and exit)
    python -m ipinfo_app.main --me --export json   (my details, saved to reports/)

Flow:
    main.py  -> asks api.py for data (internet)
             -> asks utils.py to validate/classify/export (offline)
             -> asks display.py to print it (colors + tables)
"""

import argparse

from . import api, display, utils


def build_report(ip):
    """Collect online + offline details for one IP and return (details, technical, map_url)."""
    details = api.get_ip_details(ip)
    technical = utils.technical_details(ip)
    map_url = utils.maps_link(details.get("latitude"), details.get("longitude"))
    return details, technical, map_url


def show_report(ip):
    """Look up, print and return the report for one IP (None if it failed)."""
    try:
        details, technical, map_url = build_report(ip)
    except api.APIError as exc:
        display.error(str(exc))
        return None
    display.show_details(details, technical, map_url)
    return {**details, **technical, "map": map_url}


def my_public_ip():
    """Return the best public IP for this computer (IPv4 first, then IPv6)."""
    return api.get_public_ip(4) or api.get_public_ip(6)


def lookup_any_ip():
    """Ask the user for an IP, validate it, and show its report."""
    text = input("Enter an IPv4 or IPv6 address: ")
    if not text.strip():
        display.error("No address entered. Please type an IP address, e.g. 8.8.8.8")
        return None
    ip = utils.validate_ip(text)
    if ip is None:
        display.error(f"'{text.strip()}' is not a valid IPv4 or IPv6 address.")
        return None
    if not ip.is_global:
        # Private/loopback addresses have no public location, so we only
        # show the offline technical details instead of calling the API.
        display.info(f"{ip} is a {utils.classify_ip(ip)} address and has no public location.")
        display.show_details({"ip": str(ip), "source": "offline"}, utils.technical_details(ip))
        return None
    return show_report(str(ip))


def interactive():
    """Main menu loop."""
    display.banner()
    last_report = None
    while True:
        choice = display.menu()
        if choice == "1":
            display.show_addresses(api.get_public_ip(4), api.get_public_ip(6))
        elif choice == "2":
            ip = my_public_ip()
            if ip:
                last_report = show_report(ip) or last_report
            else:
                display.error("Could not get your public IP. Check your internet connection.")
        elif choice == "3":
            last_report = lookup_any_ip() or last_report
        elif choice == "4":
            if not last_report:
                display.info("Nothing to export yet. Run option 2 or 3 first.")
                continue
            fmt = input("Format - json or txt? [json]: ").strip().lower() or "json"
            fmt = fmt if fmt in ("json", "txt") else "json"
            display.success(f"Report saved to {utils.export_report(last_report, fmt)}")
        elif choice == "5":
            display.success("Goodbye from Byte Club!")
            break
        else:
            display.error("Please enter a number from 1 to 5.")


def parse_args():
    parser = argparse.ArgumentParser(description="Byte Club IP Address Information app")
    parser.add_argument("--ip", help="look up one IP address and exit")
    parser.add_argument("--me", action="store_true", help="show details of my public IP and exit")
    parser.add_argument("--export", choices=["json", "txt"], help="also save the report to reports/")
    return parser.parse_args()


def main():
    try:
        run()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C (or Ctrl+Z / Ctrl+D at a prompt) should close the app
        # politely instead of printing a long Python traceback.
        print()
        display.info("Stopped by user. Goodbye from Byte Club!")
    except OSError as exc:
        # e.g. no permission to create the reports/ folder when exporting
        display.error(f"Could not save the report: {exc}")


def run():
    """Read the command-line options and start the menu or a one-time lookup."""
    args = parse_args()
    if not (args.ip or args.me):
        interactive()
        return
    ip = args.ip or my_public_ip()
    if not ip or utils.validate_ip(ip) is None:
        display.error("No valid IP address to look up.")
        return
    report = show_report(ip)
    if report and args.export:
        display.success(f"Report saved to {utils.export_report(report, args.export)}")


if __name__ == "__main__":
    main()
