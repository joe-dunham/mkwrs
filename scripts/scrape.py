#!/usr/bin/env python3
"""Scrape current Mario Kart World WRs from mkwrs.com into wrs.json.

Run by the GitHub Action on a schedule. Writes only if the data changed,
so the Action can skip committing when nothing is new.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

URL = "https://mkwrs.com/mkworld/"
OUT = Path(__file__).resolve().parent.parent / "wrs.json"
TIME_RE = re.compile(r"(\d+)'(\d{2})\"(\d{3})")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def to_ms(m):
    return int(m.group(1)) * 60000 + int(m.group(2)) * 1000 + int(m.group(3))


def cell_text(td):
    if td is None:
        return ""
    txt = td.get_text(" ", strip=True)
    if not txt:  # nation is sometimes just a flag image
        img = td.find("img")
        if img:
            txt = img.get("title") or img.get("alt") or ""
    return txt.strip()


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    tracks, seen = [], set()
    table_idx = -1
    for table in soup.find_all("table"):
        rows_here = []
        for tr in table.find_all("tr"):
            link = tr.find("a", href=re.compile(r"display\.php\?track="))
            if not link:
                continue
            m = TIME_RE.search(tr.get_text(" ", strip=True))
            if not m:
                continue
            cells = tr.find_all(["td", "th"])
            # locate the track cell, then read the columns after it
            i = next((k for k, c in enumerate(cells) if link in c.descendants), 0)
            get = lambda off: cells[i + off] if i + off < len(cells) else None
            track = link.get_text(" ", strip=True)
            video = None
            for a in tr.find_all("a", href=True):
                if "youtu" in a["href"]:
                    video = a["href"]
                    break
            player_a = tr.find("a", href=re.compile(r"profile\.php"))
            date_m = DATE_RE.search(tr.get_text(" ", strip=True))
            rows_here.append({
                "track": track,
                "ms": to_ms(m),
                "time": m.group(0),
                "player": player_a.get_text(" ", strip=True) if player_a else cell_text(get(2)),
                "nation": cell_text(get(3)),
                "date": date_m.group(0) if date_m else "",
                "character": cell_text(get(6)),
                "vehicle": cell_text(get(7)),
                "video": video,
                "url": urljoin(URL, link["href"]),
            })
        if rows_here:
            table_idx += 1
            cat = "base" if table_idx == 0 else "dlc"
            for r in rows_here:
                if r["track"] in seen:  # tied WRs: keep the first listed
                    continue
                seen.add(r["track"])
                r["cat"] = cat
                tracks.append(r)
    return tracks


def main():
    req = Request(URL, headers={"User-Agent": "Mozilla/5.0 (personal WR tracker)"})
    html = urlopen(req, timeout=30).read().decode("utf-8", "replace")
    tracks = parse(html)
    if len(tracks) < 20:
        sys.exit(f"Only parsed {len(tracks)} tracks - page layout may have changed; not overwriting.")
    for n, t in enumerate(tracks, 1):
        t["n"] = n

    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    if old.get("tracks") == tracks:
        print("No changes.")
        return
    OUT.write_text(json.dumps({
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": URL,
        "tracks": tracks,
    }, ensure_ascii=False, indent=1))
    print(f"Wrote {len(tracks)} tracks.")


if __name__ == "__main__":
    main()
