"""
Is the live demo actually up, awake and quick?

Streamlit Community Cloud puts an app to sleep after a stretch with no
visitors, and a sleeping app does not error -- it answers 200 with a page
asking the visitor to wake it up. Someone opening the link from a CV would
see that, so a plain status check is not enough: this looks at what came
back.

Reads DEMO_URL from the environment. Exits non-zero, with a plain-English
reason, when a visitor would not get the app.
"""

import os
import sys
import time
import urllib.error
import urllib.request

URL = os.environ["DEMO_URL"]
SLOW_SECONDS = 20.0

# What Streamlit's "gone to sleep" holding page says. Matching more than one
# phrase means a wording change on their side does not silently blind us.
ASLEEP_MARKERS = (
    "has gone to sleep",
    "get this app back up",
    "Yes, get this app back up!",
)


def fetch(url: str) -> tuple[int, str, float]:
    request = urllib.request.Request(
        url,
        # Without a normal user agent some hosts answer differently.
        headers={"User-Agent": "Mozilla/5.0 (portfolio health check)"},
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read(200_000).decode("utf-8", errors="replace")
        return response.status, body, time.monotonic() - started


def main() -> int:
    try:
        status, body, seconds = fetch(URL)
    except urllib.error.HTTPError as error:
        print(f"FAIL  {URL} answered {error.code} ({error.reason}).")
        return 1
    except Exception as error:  # DNS, TLS, timeout, connection refused
        print(f"FAIL  {URL} could not be reached: {error}")
        return 1

    if status != 200:
        print(f"FAIL  {URL} answered {status}.")
        return 1

    if any(marker.lower() in body.lower() for marker in ASLEEP_MARKERS):
        print(
            f"FAIL  {URL} is asleep. A visitor sees Streamlit's wake-up screen,\n"
            f"      not the app. Open it once in a browser to bring it back."
        )
        return 1

    if seconds > SLOW_SECONDS:
        print(f"FAIL  {URL} answered, but took {seconds:.1f}s. That reads as broken.")
        return 1

    print(f"OK    {URL} answered in {seconds:.1f}s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
