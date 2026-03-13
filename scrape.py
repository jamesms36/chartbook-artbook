#!/usr/bin/env python3
"""
Scrape all Top Links artwork from Adam Tooze's Chartbook newsletter.
Writes artworks.json with {issue, artist, title, img, url} for each post.
"""

import json
import re
import time
import sys
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

ARTWORKS_FILE = "artworks.json"


# ── 1. Collect all Top Links post URLs from the Substack API ──────────────────

def get_all_top_links_posts():
    posts = []
    offset = 0
    limit = 12
    seen = set()

    print("Fetching post list from Substack API...")
    while True:
        url = f"https://adamtooze.substack.com/api/v1/archive?sort=new&limit={limit}&offset={offset}"
        try:
            r = SESSION.get(url, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print(f"  API error at offset {offset}: {e}")
            time.sleep(5)
            continue

        data = r.json()
        if not data:
            break

        new = 0
        for post in data:
            slug = post.get("slug", "")
            title = post.get("title", "")
            canonical_url = post.get("canonical_url") or f"https://adamtooze.substack.com/p/{slug}"

            if slug in seen:
                continue
            seen.add(slug)

            if "top-link" in slug.lower() and re.search(r'\d{3,4}', title):
                posts.append({
                    "slug": slug,
                    "title": title,
                    "url": canonical_url,
                })
                new += 1

        print(f"  offset={offset:4d}  batch={len(data):2d}  top_links_found={new:2d}  total={len(posts)}")

        if len(data) < limit:
            break
        offset += limit
        time.sleep(0.3)

    # Sort newest first (highest issue number first)
    def issue_num(p):
        m = re.search(r'(\d{3,4})', p['title'])
        return int(m.group(1)) if m else 0

    posts.sort(key=issue_num, reverse=True)
    print(f"\nFound {len(posts)} Top Links posts total.\n")
    return posts


# ── 2. Extract artwork from a single post page ────────────────────────────────

def extract_artwork(post_url):
    """
    Returns (img_url, artist, artwork_title) or None if not found.

    Substack structure:
      <div class="captioned-image-container">
        <figure><a ...><img src="..."/></a></figure>
      </div>
      <p><strong>Artist Name</strong>, <em><strong>Artwork Title</strong></em></p>
    """
    try:
        r = SESSION.get(post_url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"    Fetch error: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # Find the first captioned-image-container
    container = soup.find("div", class_="captioned-image-container")
    if not container:
        return None

    # Get image URL from the <img> inside
    img_tag = container.find("img")
    if not img_tag:
        return None
    img_url = img_tag.get("src", "")
    if not img_url:
        return None

    # Caption is the first non-empty sibling <p> after the container
    caption_p = None
    for sibling in container.next_siblings:
        if hasattr(sibling, "name") and sibling.name == "p":
            text = sibling.get_text(" ", strip=True)
            if text:
                caption_p = sibling
                break

    artist = "Artist unknown"
    title = "Featured artwork"

    if caption_p:
        # Try structured parse: first <strong> = artist, first <em> = title
        strongs = caption_p.find_all("strong")
        ems = caption_p.find_all("em")

        raw = caption_p.get_text(" ", strip=True)
        raw = re.sub(r'\s+', ' ', raw).strip()

        if strongs and ems:
            artist = strongs[0].get_text(" ", strip=True).rstrip(",").strip()
            title = ems[0].get_text(" ", strip=True).strip()
        elif strongs:
            # Just bold text — treat first strong as artist, rest as title
            artist = strongs[0].get_text(" ", strip=True).rstrip(",").strip()
            if len(strongs) > 1:
                title = " ".join(s.get_text(" ", strip=True) for s in strongs[1:]).strip()
            elif "," in raw:
                parts = raw.split(",", 1)
                artist = parts[0].strip()
                title = parts[1].strip()
        elif raw:
            # Plain text caption — split on first comma
            parts = raw.split(",", 1)
            if len(parts) >= 2:
                artist = parts[0].strip()
                title = parts[1].strip()
            else:
                title = raw

    return img_url, artist, title


# ── 3. Main ───────────────────────────────────────────────────────────────────

def main():
    # Load existing results so we can resume
    try:
        with open(ARTWORKS_FILE) as f:
            existing = json.load(f)
        done_urls = {a["url"] for a in existing}
        print(f"Resuming: {len(existing)} artworks already scraped.\n")
    except FileNotFoundError:
        existing = []
        done_urls = set()

    posts = get_all_top_links_posts()

    results = list(existing)

    for i, post in enumerate(posts):
        if post["url"] in done_urls:
            continue

        # Parse issue number from slug (more reliable than title)
        m = re.search(r'top-links?-(\d+)-', post['slug'])
        issue_num = int(m.group(1)) if m else 0
        issue_label = f"Chartbook Top Links {issue_num}" if issue_num else post['title']

        print(f"[{i+1}/{len(posts)}] Scraping {issue_label} ...")

        result = extract_artwork(post["url"])
        if result:
            img_url, artist, title = result
            entry = {
                "issue": issue_label,
                "issue_num": issue_num,
                "artist": artist,
                "title": title,
                "img": img_url,
                "url": post["url"],
            }
            results.append(entry)
            done_urls.add(post["url"])
            print(f"    ✓  {artist}  —  {title[:60]}")
        else:
            print(f"    ✗  No artwork found")

        # Save progress every 20 posts
        if len(results) % 20 == 0:
            with open(ARTWORKS_FILE, "w") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        time.sleep(0.5)

    # Final save
    results.sort(key=lambda x: x.get("issue_num", 0), reverse=True)
    with open(ARTWORKS_FILE, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(results)} artworks saved to {ARTWORKS_FILE}.")


if __name__ == "__main__":
    main()
