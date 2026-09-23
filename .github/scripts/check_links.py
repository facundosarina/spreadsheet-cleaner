"""
Do the links in the README still go anywhere?

A dead link in a portfolio README is the kind of thing nobody notices for
months. This walks every http(s) link in the README and reports the ones
that are genuinely gone.

Being wrong in the noisy direction is worse than not checking at all: an
alert that cries wolf gets ignored, and then the real one gets ignored too.
So sites that simply refuse robots -- LinkedIn and Workana both answer 403
or 999 to anything that is not a browser -- count as "could not verify",
not as broken. Only a definitive 404/410 or a host that does not resolve
fails the run.
"""

import pathlib
import re
import sys
import urllib.error
import urllib.request

README = pathlib.Path("README.md")
LINK = re.compile(r"\]\((https?://[^)\s]+)\)|<(https?://[^>\s]+)>|(?<![(<])\b(https?://[^\s)<>\]]+)")
HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio link check)"}
UNVERIFIABLE = {401, 403, 405, 429, 999}


def links_in(text: str) -> list[str]:
    found = []
    for match in LINK.finditer(text):
        url = next(group for group in match.groups() if group)
        url = url.rstrip(".,;:`'\"")
        # A localhost URL is the "run it yourself" instruction, not a link.
        if "localhost" in url or "127.0.0.1" in url:
            continue
        if url not in found:
            found.append(url)
    return found


def status_of(url: str) -> tuple[str, str]:
    """Returns (verdict, detail) where verdict is ok / unknown / broken."""
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return "ok", str(response.status)
    except urllib.error.HTTPError as error:
        if error.code in UNVERIFIABLE:
            return "unknown", f"{error.code}, refuses automated checks"
        if error.code in (404, 410):
            return "broken", f"{error.code}, the page is gone"
        return "unknown", str(error.code)
    except Exception as error:
        message = str(error)
        if "Name or service not known" in message or "nodename nor servname" in message:
            return "broken", "the domain does not resolve"
        return "unknown", message


def main() -> int:
    if not README.exists():
        print("FAIL  there is no README.md to check.")
        return 1

    broken = []
    for url in links_in(README.read_text(encoding="utf-8")):
        verdict, detail = status_of(url)
        if verdict == "broken":
            broken.append((url, detail))
            print(f"BROKEN   {url}  ({detail})")
        elif verdict == "unknown":
            print(f"skipped  {url}  ({detail})")
        else:
            print(f"ok       {url}")

    if broken:
        print(f"\nFAIL  {len(broken)} link(s) in the README lead nowhere.")
        return 1

    print("\nOK    every link that could be checked works.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
