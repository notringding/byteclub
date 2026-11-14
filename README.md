# Byte Club – IP Address Information App

A Python command-line application that shows a computer's **current public IPv4 and IPv6 addresses** together with their **geolocation, ISP, ASN, country code and timezone**. It was built for network technicians as a prototype for the engineering department.

DEVASC Project Activity 3 – Social Coding, **Option 2: New Application (IPv4/IPv6 Address Application)**
Team: **Byte Club** – University of Santo Tomas

## Features

| # | Feature | Why we added it |
|---|---------|-----------------|
| 1 | Shows public IPv4 **and** IPv6 side by side with a Connected / No connectivity status | Technicians often need to check whether a site has working IPv6 |
| 2 | Full details: city, region, country, country code, postal code, coordinates, timezone | Required by the project brief (geolocation and country code) |
| 3 | ISP / organization and **ASN** | Useful when troubleshooting routing or contacting the provider |
| 4 | Look up **any** IPv4/IPv6 address, with input validation | Lets technicians check addresses they see in logs, not only their own |
| 5 | Offline technical details: IPv4 binary form and class, IPv6 expanded/compressed form, address type (public, private, loopback, link-local, CGNAT, multicast) | Explains why a private address like 192.168.x.x cannot be geolocated |
| 6 | Google Maps link for the coordinates | Quick visual check of the location |
| 7 | Export the report to **JSON or TXT** in `reports/` | So results can be attached to tickets or documentation |
| 8 | Color-coded tables (colorama + tabulate) | Easier to read than plain print statements |
| 9 | **Fallback API**: if ipapi.co fails or is rate-limited, ipwho.is is used | ipapi.co's free tier has a daily limit |
| 10 | Command-line options (`--ip`, `--me`, `--export`) | Lets the app be used in scripts without the menu |

## APIs used

All are free and need **no API key**.

| API | Used for | Endpoint |
|-----|----------|----------|
| ipify | Public IPv4 | `https://api.ipify.org?format=json` |
| ipify | Public IPv6 | `https://api6.ipify.org?format=json` |
| ipapi.co | IP details (primary) | `https://ipapi.co/<ip>/json/` |
| ipwho.is | IP details (fallback) | `https://ipwho.is/<ip>` |

## Setup and running

Requires **Python 3.9+**.

```bash
git clone https://github.com/<your-org>/byteclub-ip-info.git
cd byteclub-ip-info
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

python -m ipinfo_app.main                       # interactive menu
python -m ipinfo_app.main --me                  # my public IP details
python -m ipinfo_app.main --ip 8.8.8.8          # look up one address
python -m ipinfo_app.main --me --export json    # save the report to reports/
```

Run the tests (no internet needed, the API replies are mocked):

```bash
python -m unittest discover -v tests
```

## Project structure

```
byteclub-ip-info/
├── ipinfo_app/
│   ├── main.py      # entry point: menu, command-line options, program flow
│   ├── api.py       # all REST API calls (ipify, ipapi.co, ipwho.is)
│   ├── display.py   # banner, menu, colored tables, messages
│   └── utils.py     # offline helpers: validation, classification, export
├── tests/
│   └── test_app.py  # unit tests (validation, classification, API fallback, export)
├── requirements.txt
└── README.md
```

How the parts work together: `main.py` asks `api.py` for online data, asks `utils.py` to validate, classify and export, and passes everything to `display.py` to print. Every API reply is converted to **one standard dictionary** (`ip, city, region, country, country_code, postal, latitude, longitude, timezone, isp, asn, source`), so a new API can be added without touching the display code.

## How to continue this project (for another team)

- **Add a new data source:** write a `_from_<name>(ip)` function in `api.py` that returns the standard dictionary, then add it to the tuple in `get_ip_details()`.
- **Add a new field:** add the key in each `_from_...` function and one row in `display.show_details()`.
- **Add a menu option:** add a row in `display.menu()` and an `elif` branch in `main.interactive()`.
- Add a test in `tests/test_app.py` for every new feature, and keep all tests passing before opening a pull request.

## Backlog (future enhancements)

1. GUI version (Tkinter or a small Flask web page)
2. Subnet calculator: network/broadcast address, host range, number of hosts from an IP and prefix
3. Bulk lookup from a text/CSV file of addresses, with CSV export
4. Reverse DNS (PTR) lookup and WHOIS summary
5. IP reputation / blacklist check (e.g. AbuseIPDB, needs a free API key)
6. Show the location on an embedded map instead of a link
7. Cache recent lookups to stay under the API rate limits
8. Ping / traceroute to the looked-up address
9. Package as a standalone `.exe` with PyInstaller for technicians without Python

## Team and Git workflow

| Member | Role | Branch | Main files |
|--------|------|--------|-----------|
| John Edcel B. Lansigan | Scrum Leader / integration | `feature/utils-integration` | `main.py`, `utils.py`, README |
| Lorenz James M. Morales | Developer (API) / Recorder | `feature/api` | `api.py` |
| Marc Jherald V. Marcelo | Developer (UI / output) | `feature/display` | `display.py` |
| Miguel Andre F. Naguit | QA Tester (tests, usability) | `qa/tests` | `tests/test_app.py` |
| Lee Joseph J. Caceres | QA Tester (troubleshooting, error handling) | `qa/error-handling` | `tests/test_app.py`, bug fixes |

1. Never commit directly to `main`. Create a branch from `main` for your task.
2. Commit small changes with clear messages, e.g. `Add ipwho.is fallback to api.py`.
3. Push the branch and open a **pull request** into `main`.
4. At least one QA tester reviews the code and runs the tests. The scrum leader merges after approval.
5. Report bugs and track tasks with **GitHub Issues** and the project board.
