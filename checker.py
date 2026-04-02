import json
import os
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://tcbonepiecechapters.com/mangas/5/one-piece"
STATE_PATH = Path("state/latest.json")

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
NTFY_BASE_URL = os.environ.get("NTFY_BASE_URL", "https://ntfy.sh").rstrip("/")
FORCE_TEST_NOTIFY = os.environ.get("FORCE_TEST_NOTIFY", "0") == "1"


def fetch_latest_chapter():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; onepiece-watcher/1.0)"
    }

    response = requests.get(PAGE_URL, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):
        title = " ".join(a.get_text(" ", strip=True).split())
        if title.startswith("One Piece Chapter "):
            return {
                "title": title,
                "url": urljoin(PAGE_URL, a["href"]),
            }

    raise RuntimeError("Could not find a chapter link on the page.")


def load_state():
    if not STATE_PATH.exists():
        return None

    with STATE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(data):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def send_ntfy(title, message, click_url=None, priority="high", tags="bell"):
    if not NTFY_TOPIC:
        print("NTFY_TOPIC is not set. Skipping notification.")
        return

    url = f"{NTFY_BASE_URL}/{NTFY_TOPIC}"
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": tags,
    }

    if click_url:
        headers["Click"] = click_url

    response = requests.post(
        url,
        data=message.encode("utf-8"),
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()
    print("Notification sent.")


def main():
    if FORCE_TEST_NOTIFY:
        send_ntfy(
            title="One Piece watcher test",
            message="If you got this, GitHub -> ntfy -> phone is working.",
            click_url=PAGE_URL,
            priority="default",
            tags="test_tube",
        )
        return

    latest = fetch_latest_chapter()
    previous = load_state()

    print(f"Latest on site: {latest['title']}")
    print(f"URL: {latest['url']}")

    if previous is None:
        print("No saved state yet. Initializing without notification.")
        save_state(latest)
        return

    if latest["url"] != previous.get("url"):
        print("NEW CHAPTER DETECTED")
        print(f"Old: {previous.get('title')}")
        print(f"New: {latest['title']}")

        send_ntfy(
            title="New One Piece chapter",
            message=f"{latest['title']}\n{latest['url']}",
            click_url=latest["url"],
            priority="high",
            tags="book",
        )

        save_state(latest)
    else:
        print("No new chapter.")


if __name__ == "__main__":
    main()