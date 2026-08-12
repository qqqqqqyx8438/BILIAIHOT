# -*- coding: utf-8 -*-
"""AI Hotboard RSS Aggregator v2 - supports aggregate_rss (AIHOT) + native_rss"""
import json, sys, io, time, hashlib, re
from pathlib import Path
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import yaml, feedparser
import urllib.request, urllib.error

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_DIR.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# -- helpers --
def parse_dt(raw):
    if not raw: return datetime.min
    try: return parsedate_to_datetime(raw).replace(tzinfo=None)
    except: return datetime.min

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text).strip()

def fingerprint(title, url):
    return hashlib.md5(f"{title}|{url}".encode()).hexdigest()

def load_cfg():
    with open(BASE_DIR / "sources.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# -- extract source name from AIHOT author field --
def extract_source_name(author_str):
    """Extract source name from AIHOT author format:
    'noreply@aihot.virxact.com (IT之家（RSS）)' -> 'IT之家'
    'noreply@aihot.virxact.com (X：OpenAI (@OpenAI))' -> 'X：OpenAI'
    """
    if not author_str: return "unknown"
    m = re.search(r"\((.+?)\)$", author_str)
    if m:
        raw = m.group(1)
        # Clean up: remove trailing （RSS）/（网页） etc
        raw = re.sub(r"[（(](?:RSS|网页|发表成果|社区热门论文)[）)]", "", raw)
        raw = re.sub(r"\s*·\s*.*$", "", raw)  # remove " · 排除企业/客户案例"
        return raw.strip()
    return author_str

# -- fetch --
def fetch(url, label):
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        feed = feedparser.parse(raw)
        if feed.bozo and not feed.entries:
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

# -- aggregate --
def aggregate(cfg):
    mx = cfg["settings"].get("max_items_per_source", 30)
    total = len(cfg["sources"])

    all_items, seen, ok = [], set(), 0
    source_stats = {}  # per-source hotness tracking

    for i, src in enumerate(cfg["sources"], 1):
        if not src.get("enabled", True): continue
        name, stype = src["name"], src["type"]

        if stype == "native_rss":
            url = src.get("url", "")
        elif stype == "aggregate_rss":
            url = src.get("url", "")
        else:
            continue

        if not url: continue

        print(f"  [{i}/{total}] {name} ... ", end="", flush=True)
        entries = fetch(url, name)
        print(f"{len(entries)} items")
        if entries: ok += 1

        for e in entries[:mx]:
            # For aggregate_rss, extract real source from author field
            if stype == "aggregate_rss":
                real_source = extract_source_name(e.get("author",""))
                # Apply filter
                filt = src.get("source_filter", "all")
                excludes = src.get("exclude_sources", [])
                if filt == "blacklist" and real_source in excludes:
                    continue
            else:
                real_source = name

            fp = fingerprint(e["title"], e["url"])
            if fp in seen: continue
            seen.add(fp)

            item = dict(
                title=e["title"],
                url=e["url"],
                summary=e["summary"],
                published=e["published"],
                source_id=src["id"],
                source_name=real_source,  # ! The real individual source
                aggregate_name=name if stype=="aggregate_rss" else "",
                category=src.get("category",""),
                tags=src.get("tags",[]),
                fingerprint=fp,
                fetched_at=datetime.now().isoformat(),
            )
            all_items.append(item)

            # Per-source hotness
            if real_source not in source_stats:
                source_stats[real_source] = {"count": 0, "last_seen": "", "categories": set()}
            source_stats[real_source]["count"] += 1
            source_stats[real_source]["last_seen"] = max(
                source_stats[real_source]["last_seen"],
                e.get("published","")
            )
            source_stats[real_source]["categories"].add(src.get("category",""))

    all_items.sort(key=lambda x: parse_dt(x.get("published")), reverse=True)

    total_enabled = sum(1 for s in cfg["sources"] if s.get("enabled",True))
    print(f"\n  [OK] {ok}/{total_enabled} sources, {len(all_items)} items, {len(source_stats)} individual sources")

    # Convert sets to lists for JSON
    for k in source_stats:
        source_stats[k]["categories"] = list(source_stats[k]["categories"])

    return all_items, source_stats

# -- save --
def save(items, source_stats, cfg):
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

    # Stats
    recent = sum(1 for item in merged if (now - parse_dt(item.get("published"))).total_seconds() < 86400)
    dist = {}
    for item in merged:
        cat = item.get("category", "other")
        dist[cat] = dist.get(cat, 0) + 1

    stats = dict(
        last_updated=now.isoformat(),
        total_items=len(merged),
        recent_24h=recent,
        unique_sources=len(source_stats),
        categories=dist,
        source_stats=source_stats  # Per-source hotness
    )
    (OUTPUT_DIR / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    # Separate per-source ranking
    ranked = sorted(source_stats.items(), key=lambda x: -x[1]["count"])
    (OUTPUT_DIR / "source_ranking.json").write_text(
        json.dumps(ranked, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  [FILE] ai_feed.json ({min(len(merged),500)} items)")
    print(f"  [FILE] stats.json (24h: {recent}, sources: {len(source_stats)})")
    print(f"  [FILE] source_ranking.json (per-source hotness)")
    print()
    print("  Top 10 sources by volume:")
    for i, (name, st) in enumerate(ranked[:10], 1):
        print(f"    {i:2}. {name}: {st['count']} items")

def main():
    print("=" * 50)
    print("  AI Hotboard v2 - AIHOT + Independent Sources")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    cfg = load_cfg()
    agg_count = sum(1 for s in cfg["sources"] if s.get("type")=="aggregate_rss" and s.get("enabled",True))
    native_count = sum(1 for s in cfg["sources"] if s.get("type")=="native_rss" and s.get("enabled",True))
    print(f"  AIHOT feeds: {agg_count} | Independent: {native_count} | Total: {agg_count+native_count}\n")
    items, src_stats = aggregate(cfg)
    save(items, src_stats, cfg)
    print("\n  Done!")

if __name__ == "__main__":
    main()
