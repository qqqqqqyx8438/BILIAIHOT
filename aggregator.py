# -*- coding: utf-8 -*-
"""AI Hotboard RSS Aggregator - reads sources.yaml, outputs ai_feed.json"""
import json, sys, io, time, hashlib, re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import yaml, feedparser
import urllib.request, urllib.error

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_DIR.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# --- helpers ---
def parse_dt(raw):
    """Parse any date string to timezone-naive datetime"""
    if not raw:
        return datetime.min
    try:
        return parsedate_to_datetime(raw).replace(tzinfo=None)
    except:
        return datetime.min

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text).strip()

def fingerprint(title, url):
    return hashlib.md5(f"{title}|{url}".encode()).hexdigest()

def load_cfg():
    with open(BASE_DIR / "sources.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# --- fetch ---
def fetch(url, label):
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
        feed = feedparser.parse(raw)
        if feed.bozo and not feed.entries:
            print(f"  [WARN] {label}: {feed.bozo_exception}")
            return items
        for e in feed.entries:
            items.append(dict(
                title=e.get("title",""),
                url=e.get("link",""),
                summary=strip_html(e.get("summary", e.get("description","")))[:500],
                published=e.get("published", e.get("updated","")),
                author=e.get("author",""),
            ))
    except Exception as ex:
        print(f"  [FAIL] {label}: {ex}")
    return items

# --- aggregate ---
def aggregate(cfg):
    rsshub = cfg["settings"]["rsshub_base"]
    mx = cfg["settings"].get("max_items_per_source", 20)
    total = len(cfg["sources"])

    # Quick check: is RSSHub alive?
    rsshub_ok = False
    try:
        urllib.request.urlopen(f"{rsshub}/", timeout=3)
        rsshub_ok = True
    except:
        print(f"  [WARN] RSSHub ({rsshub}) not reachable - skipping all rsshub-type sources\n")

    all_items, seen, ok = [], set(), 0

    for i, src in enumerate(cfg["sources"], 1):
        if not src.get("enabled", True):
            continue
        name, stype = src["name"], src["type"]

        # Skip rsshub sources if RSSHub is down
        if stype == "rsshub" and not rsshub_ok:
            continue

        if stype == "rsshub":
            url = f"{rsshub.rstrip('/')}/{src['route'].lstrip('/')}"
        elif stype == "native_rss":
            url = src.get("url", "")
        else:
            continue

        if not url:
            continue

        print(f"  [{i}/{total}] {name} ... ", end="", flush=True)
        entries = fetch(url, name)
        print(f"{len(entries)} items")
        if entries: ok += 1

        for e in entries[:mx]:
            fp = fingerprint(e["title"], e["url"])
            if fp in seen: continue
            seen.add(fp)
            e.update(source_id=src["id"], source_name=name,
                     category=src.get("category",""), tags=src.get("tags",[]),
                     fingerprint=fp, fetched_at=datetime.now().isoformat())
            all_items.append(e)

    all_items.sort(key=lambda x: parse_dt(x.get("published")), reverse=True)
    rsshub_count = sum(1 for s in cfg["sources"] if s.get("type")=="rsshub" and s.get("enabled",True))
    total_enabled = sum(1 for s in cfg["sources"] if s.get("enabled",True))
    print(f"\n  [OK] {ok}/{total_enabled - (rsshub_count if not rsshub_ok else 0)} sources succeeded, {len(all_items)} items total")
    return all_items

# --- save ---
def save(items, cfg):
    retention = cfg["settings"].get("retention_days", 7)
    cutoff = datetime.now() - timedelta(days=retention)
    now = datetime.now()

    # Merge with existing
    fp_full = OUTPUT_DIR / "ai_feed_full.json"
    existing = {}
    if fp_full.exists():
        try:
            old = json.loads(fp_full.read_text(encoding="utf-8"))
            for item in old:
                existing[item.get("fingerprint","")] = item
        except: pass

    for item in items:
        existing[item["fingerprint"]] = item

    merged = [item for item in existing.values() if parse_dt(item.get("published")) >= cutoff]
    merged.sort(key=lambda x: parse_dt(x.get("published")), reverse=True)

    fp_full.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "ai_feed.json").write_text(
        json.dumps(merged[:500], ensure_ascii=False, indent=2), encoding="utf-8")

    # stats
    recent = sum(1 for item in merged if (now - parse_dt(item.get("published"))).total_seconds() < 86400)
    dist = {}
    for item in merged:
        cat = item.get("category", "other")
        dist[cat] = dist.get(cat, 0) + 1
    stats = dict(last_updated=now.isoformat(), total_items=len(merged),
                 recent_24h=recent, categories=dist)
    (OUTPUT_DIR / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  [FILE] ai_feed.json ({min(len(merged),500)} items)")
    print(f"  [FILE] ai_feed_full.json ({len(merged)} items)")
    print(f"  [FILE] stats.json (24h: {recent} items)")
    for k, v in sorted(dist.items(), key=lambda x: -x[1]):
        print(f"         {k}: {v}")

# --- main ---
def main():
    print("=" * 50)
    print("  AI Hotboard - RSS Aggregator")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    cfg = load_cfg()
    print(f"  Sources: {len(cfg['sources'])} | RSSHub: {cfg['settings']['rsshub_base']}\n")
    items = aggregate(cfg)
    save(items, cfg)
    print("\n  Done!")

if __name__ == "__main__":
    main()
