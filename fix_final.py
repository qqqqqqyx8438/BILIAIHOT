src = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "r", encoding="utf-8").read()

# Fix main() - remove the broken getattr line and use the unpacked value correctly
old_main = """    items, src_stats, briefing_data = aggregate(cfg)
    briefing_verified = getattr(aggregate, 'briefing_verified', None) if hasattr(aggregate, 'briefing_verified') else None"""

new_main = """    items, src_stats, briefing_data = aggregate(cfg)"""

src = src.replace(old_main, new_main)

# Fix save call
old_save = "save(items, src_stats, cfg, briefing_verified if 'briefing_verified' in dir() else None)"
new_save = "save(items, src_stats, cfg, briefing_data)"
src = src.replace(old_save, new_save)

# Also improve cross-verify matching: make it more lenient for Chinese text
# The issue is that keyword matching is too strict. Let me add entity matching
old_cross = """    # Build keyword index from main feed titles
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
                main_keywords.add(w.lower())"""

new_cross = """    # Build keyword index from main feed titles AND summaries
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
        for w in re.findall(r"[A-Z][a-zA-Z]+|[\\u4e00-\\u9fff]{2,}", text):
            if len(w) > 2:
                main_keywords.add(w.lower())"""

if old_cross in src:
    src = src.replace(old_cross, new_cross)
    print("Cross-verify matching improved")
else:
    print("Old cross-verify block not found")

# Also improve the verification scoring to use domain matching
old_score = """        # Check keyword overlap
        title_words = set(re.findall(r"[A-Z][a-zA-Z]+|[\\u4e00-\\u9fff]{2,}", title))
        keyword_overlap = len(title_words & main_keywords)
        
        score = 0
        if link_match:
            score = 2  # Direct link match = high confidence
        elif keyword_overlap >= 3:
            score = 1  # Keyword match = medium confidence
        elif keyword_overlap >= 1:
            score = 0.5  # Partial match = low confidence"""

new_score = """        # Check domain overlap (briefing links matching main feed domains)
        domain_match = False
        for link in item.get("source_links", []):
            m = re.match(r"https?://([^/]+)", link)
            if m and m.group(1).replace("www.", "") in main_domains:
                domain_match = True
                break
        
        # Check keyword overlap
        title_words = set(re.findall(r"[A-Z][a-zA-Z]+|[\\u4e00-\\u9fff]{2,}", title.lower()))
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
            score = 0.5  # Partial match = low confidence"""

if old_score in src:
    src = src.replace(old_score, new_score)
    print("Verification scoring improved with domain matching")
else:
    print("Old scoring block not found")

open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "w", encoding="utf-8").write(src)
print("All fixes applied")
