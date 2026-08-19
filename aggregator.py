# -*- coding: utf-8 -*-
"""AI Hotboard RSS Aggregator v2 - supports aggregate_rss (AIHOT) + native_rss"""
import json, sys, io, time, hashlib, re
from pathlib import Path
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import yaml, feedparser
import urllib.request, urllib.error
import html

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_DIR.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# -- helpers --
def parse_dt(raw):
    if not raw: return datetime.min
    try:
        return parsedate_to_datetime(raw).replace(tzinfo=None)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(raw).replace(tzinfo=None)
    except Exception:
        return datetime.min

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text).strip()

def fingerprint(title, url):
    return hashlib.md5(f"{title}|{url}".encode()).hexdigest()

def load_cfg():
    with open(BASE_DIR / "sources.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# -- extract source name from AIHOT author field --
def extract_source_name(author_str):
    """Normalize AIHOT author -> source name, strip handles/descriptors."""
    if not author_str:
        return "unknown"
    m = re.search(r"\((.+)\)$", author_str)
    raw = m.group(1) if m else author_str
    prev = None
    while prev != raw:
        prev = raw
        raw = re.sub(r"[ \t]*[（(][^（）()]*[）)][ \t]*$", "", raw).strip()
    return raw.strip() or author_str
# -- fetch --
def extract_original_url(entry):
    """Extract original source URL from AIHOT description.
    AIHOT format: '... 🔗 [阅读原文](https://original.url) via AIHOT · [站内](https://aihot...)'
    """
    raw_desc = entry.get("summary", "") + entry.get("description", "")
    # Match markdown link [阅读原文](URL)
    m = re.search(r"阅读原文\]?\(?(https?://[^\s\)]+)", raw_desc)
    if m:
        return m.group(1)
    # Fallback: first non-aihot URL in the description
    for m in re.finditer(r'https?://[^\s"<>)]+', raw_desc):
        u = m.group(0)
        if "aihot.virxact.com" not in u and "daily.juya.uk" not in u:
            return u.rstrip(".,;")
    return entry.get("link", "")

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
            original = extract_original_url(e)
            items.append(dict(
                title=e.get("title",""),
                url=e.get("link",""),
                original_url=original,  # 原始来源 URL
                summary=strip_html(e.get("summary", e.get("description","")))[:500],
                published=e.get("published", e.get("updated","")),
                author=e.get("author",""),
            ))
    except Exception as ex:
        print(f"  [FAIL] {label}: {ex}")
    return items

# -- aggregate --

def parse_daily_briefing(feed, src):
    """Parse a daily briefing RSS (e.g. 橘鸦AI早报).
    Each entry is one daily issue containing multiple news items in HTML.
    Extract individual items with their original source links."""
    items = []
    for entry in feed.entries:
        content = entry.get("summary", "") + entry.get("content", [{}])[0].get("value", "")
        if not content:
            content = entry.get("description", "")
        
        # Remove HTML tags but keep links
        # Extract all linked URLs and their text context
        links = re.findall(r'<a[^>]*href="(https?://[^"]+)"[^>]*>([^<]*)</a>', content)
        
        # Extract news items by matching patterns like:
        # "标题 or 描述 ↗" followed by links
        # Each item starts with a number or section header
        clean = re.sub(r"<[^>]+>", " ", content)
        clean = re.sub(r"\s+", " ", clean).strip()
        
        # Split into sections (要闻, 模型发布, 产品应用, 行业动态, etc.)
        sections = re.split(r"(要闻|模型发布|产品应用|行业动态|开发生态|技术与洞察|前瞻与传闻|论文)", clean)
        
        current_section = ""
        for part in sections:
            if part in ["要闻", "模型发布", "产品应用", "行业动态", "开发生态", "技术与洞察", "前瞻与传闻", "论文"]:
                current_section = part
                continue
            if not current_section:
                continue
            
            # Extract numbered items within each section
            numbered = re.findall(r"(?:#[0-9]+|[0-9]+[.、])\s*([^#\n]+?)(?=\s*(?:#[0-9]+|[0-9]+[.、]|$))", part)
            if not numbered:
                # Try just splitting by #N pattern
                numbered = re.split(r"#[0-9]+\s*", part)
                numbered = [n.strip() for n in numbered if n.strip() and len(n.strip()) > 10]
            
            for snippet in numbered:
                snippet = snippet.strip()
                if len(snippet) < 15:
                    continue
                # Find matching links for this snippet
                snippet_links = []
                for url, text in links:
                    if text and len(text) > 3 and text[:20] in snippet[:200]:
                        snippet_links.append(url)
                
                items.append(dict(
                    title=snippet[:150],
                    url=snippet_links[0] if snippet_links else entry.get("link", ""),
                    summary=snippet[:500],
                    published=entry.get("published", ""),
                    section=current_section,
                    source_links=snippet_links,
                    briefing_date=entry.get("title", ""),
                ))
    
    # Deduplicate within briefing
    seen = set()
    deduped = []
    for item in items:
        fp = hashlib.md5(item["title"][:80].encode()).hexdigest()
        if fp not in seen:
            seen.add(fp)
            deduped.append(item)
    
    return deduped

def cross_verify(briefing_items, main_items):
    """Cross-verify briefing items against main feed.
    Returns briefing items with verification score."""
    import difflib
    
    # Build keyword index from main feed titles AND summaries
    main_keywords = set()
    main_urls = set()
    main_domains = set()
    for item in main_items:
        title = item.get("title", "")
        summary = item.get("summary", "")
        url = item.get("url", "")
        main_urls.add(url)
        # Extract domains from main feed URLs
        m = re.match(r"https?://([^/]+)", url)
        if m:
            main_domains.add(m.group(1).replace("www.", ""))
        # Extract meaningful keywords from title+summary
        text = (title + " " + summary).lower()
        for w in re.findall(r"[A-Z][a-zA-Z]+|[\u4e00-\u9fff]{2,}", text):
            if len(w) > 2:
                main_keywords.add(w.lower())
    
    verified = []
    for item in briefing_items:
        title = item.get("title", "")
        # Check if any source link matches main feed URLs
        link_match = any(link in main_urls for link in item.get("source_links", []))
        
        # Check domain overlap (briefing links matching main feed domains)
        domain_match = False
        for link in item.get("source_links", []):
            m = re.match(r"https?://([^/]+)", link)
            if m and m.group(1).replace("www.", "") in main_domains:
                domain_match = True
                break
        
        # Check keyword overlap
        title_words = set(re.findall(r"[A-Z][a-zA-Z]+|[\u4e00-\u9fff]{2,}", title.lower()))
        keyword_overlap = len(title_words & main_keywords)

        score = 0
        if link_match:
            score = 2  # Direct link match = high confidence
        elif domain_match and keyword_overlap >= 2:
            score = 1.5  # Same domain + keyword overlap
        elif domain_match:
            score = 1  # Same domain = medium confidence
        elif keyword_overlap >= 3:
            score = 1  # Keyword match = medium confidence
        elif keyword_overlap >= 1:
            score = 0.5  # Partial match = low confidence
        
        item["verified"] = score >= 1
        item["verify_score"] = score
        item["verify_method"] = "link" if link_match else ("keyword({})".format(keyword_overlap) if keyword_overlap > 0 else "none")
        verified.append(item)
    
    return verified

def aggregate(cfg):
    mx = cfg["settings"].get("max_items_per_source", 30)
    total = len(cfg["sources"])

    all_items, seen, ok = [], set(), 0
    source_stats = {}  # per-source hotness tracking

    for i, src in enumerate(cfg["sources"], 1):
        if not src.get("enabled", True): continue
        name, stype = src["name"], src["type"]

        if stype == "daily_briefing":
            # Fetch briefing RSS and parse into individual items
            url = src.get("url", "")
            if not url: continue
            print(f"  [{i}/{total}] {name} ... ", end="", flush=True)
            raw_entries = fetch(url, name)
            if raw_entries:
                # Re-fetch as feed object for HTML content
                try:
                    req2 = urllib.request.Request(url, headers={"User-Agent": UA})
                    with urllib.request.urlopen(req2, timeout=15) as resp2:
                        raw2 = resp2.read()
                    feed_obj = feedparser.parse(raw2)
                    briefing_items = parse_daily_briefing(feed_obj, src)
                    print(f"{len(briefing_items)} items (from daily brief)")
                    # Store for cross-verification later
                    if not hasattr(aggregate, "briefing_items"):
                        aggregate.briefing_items = []
                    aggregate.briefing_items.append((src["id"], briefing_items))
                    ok += 1
                except Exception as ex:
                    print(f"FAIL: {ex}")
            else:
                print("0 items")
            continue

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
                url=e.get("original_url") or e["url"],  # 用原始来源URL
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


    # Cross-verify with daily briefings
    briefing_verified = []
    if hasattr(aggregate, "briefing_items"):
        for bid, bitems in aggregate.briefing_items:
            verified = cross_verify(bitems, all_items)
            briefing_verified.extend(verified)
            vc = sum(1 for v in verified if v["verified"])
            print("  [VERIFY] {}: {}/{} items cross-verified".format(bid, vc, len(verified)))

        # Package briefing results
    bv = locals().get("briefing_verified", None)
    briefing_data = bv if bv else None
    return all_items, source_stats, briefing_data

# -- save --
def save(items, source_stats, cfg, briefing_verified=None):
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

    # Save cross-verified briefing items
    if briefing_verified:
        verified_items = [v for v in briefing_verified if v["verified"]]
        (OUTPUT_DIR / "briefing_verified.json").write_text(
            json.dumps(verified_items, ensure_ascii=False, indent=2), encoding="utf-8")
        (OUTPUT_DIR / "briefing_all.json").write_text(
            json.dumps(briefing_verified, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [FILE] briefing_verified.json ({len(verified_items)} verified items)")
        print(f"  [FILE] briefing_all.json ({len(briefing_verified)} total briefing items)")

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
    items, src_stats, briefing_data = aggregate(cfg)
    save(items, src_stats, cfg, briefing_data)
    print("\n  Done!")

if __name__ == "__main__":
    main()
