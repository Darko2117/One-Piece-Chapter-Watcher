import json
import os
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://tcbonepiecechapters.com/mangas/5/one-piece"
STATE_PATH = Path("state/latest.json")


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


def main():
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

        # For now, just save the new state.
        # In the next step, we will add phone notifications here.
        save_state(latest)
    else:
        print("No new chapter.")


if __name__ == "__main__":
    main()