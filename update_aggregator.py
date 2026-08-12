import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Read current aggregator
src = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "r", encoding="utf-8").read()

# 1. Add import for HTML parsing
src = src.replace(
    "import urllib.request, urllib.error",
    "import urllib.request, urllib.error\nimport html"
)

# 2. Add daily briefing parser BEFORE "def aggregate"
briefing_handler = '''
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
        clean = re.sub(r"\\s+", " ", clean).strip()
        
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
            numbered = re.findall(r"(?:#[0-9]+|[0-9]+[.、])\\s*([^#\\n]+?)(?=\\s*(?:#[0-9]+|[0-9]+[.、]|$))", part)
            if not numbered:
                # Try just splitting by #N pattern
                numbered = re.split(r"#[0-9]+\\s*", part)
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
    
    # Build keyword index from main feed titles
    main_keywords = set()
    main_urls = set()
    for item in main_items:
        title = item.get("title", "")
        url = item.get("url", "")
        main_urls.add(url)
        # Extract meaningful keywords (nouns, entities)
        words = re.findall(r"[A-Z][a-zA-Z]+|[\\u4e00-\\u9fff]{2,}", title)
        for w in words:
            if len(w) > 2:
                main_keywords.add(w.lower())
    
    verified = []
    for item in briefing_items:
        title = item.get("title", "")
        # Check if any source link matches main feed URLs
        link_match = any(link in main_urls for link in item.get("source_links", []))
        
        # Check keyword overlap
        title_words = set(re.findall(r"[A-Z][a-zA-Z]+|[\\u4e00-\\u9fff]{2,}", title))
        keyword_overlap = len(title_words & main_keywords)
        
        score = 0
        if link_match:
            score = 2  # Direct link match = high confidence
        elif keyword_overlap >= 3:
            score = 1  # Keyword match = medium confidence
        elif keyword_overlap >= 1:
            score = 0.5  # Partial match = low confidence
        
        item["verified"] = score >= 1
        item["verify_score"] = score
        item["verify_method"] = "link" if link_match else ("keyword({})".format(keyword_overlap) if keyword_overlap > 0 else "none")
        verified.append(item)
    
    return verified
'''

# Insert briefing handler after strip_html function
src = src.replace(
    "def aggregate(cfg):",
    briefing_handler + "\ndef aggregate(cfg):"
)

# 3. Add daily_briefing processing in aggregate() 
# Find the fetch loop and add briefing handling
old_fetch = '''        if stype == "native_rss":
            url = src.get("url", "")
        elif stype == "aggregate_rss":
            url = src.get("url", "")
        else:
            continue

        if not url: continue

        print(f"  [{i}/{total}] {name} ... ", end="", flush=True)
        entries = fetch(url, name)
        print(f"{len(entries)} items")
        if entries: ok += 1'''

new_fetch = '''        if stype == "daily_briefing":
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
        if entries: ok += 1'''

src = src.replace(old_fetch, new_fetch)

open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "w", encoding="utf-8").write(src)
print("aggregator.py updated with daily_briefing + cross_verify support")
