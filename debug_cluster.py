import json, re, sys, io
from collections import defaultdict
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

items = json.load(open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/data/ai_feed.json", "r", encoding="utf-8"))
now = datetime.now()
cutoff = now - timedelta(hours=48)
recent = [it for it in items if parsedate_to_datetime(it.get("published", "")).replace(tzinfo=None) >= cutoff]

# Show sample titles to understand data
print("Sample titles from first 20 items:")
for i, it in enumerate(recent[:20]):
    title = it.get("title", "")[:100]
    src = it.get("source_name", "")[:30]
    print("  {} [{}] {}".format(i+1, src, title))
print()

# Simplified approach: use word-level overlap
def get_words(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]", " ", text)
    words = [w for w in text.split() if len(w) > 2]
    # Also add bigrams for context
    if len(words) > 1:
        for j in range(len(words)-1):
            bigram = words[j] + " " + words[j+1]
            words.append(bigram)
    return set(words)

# Group by word overlap >= 3
all_words = {}
for it in recent:
    fp = it.get("fingerprint", "")
    all_words[fp] = get_words(it.get("title", ""))

# Simple greedy clustering
clusters = []
assigned = set()
for it in recent:
    fp = it.get("fingerprint", "")
    if fp in assigned: continue
    cluster = [it]
    assigned.add(fp)
    for other in recent:
        ofp = other.get("fingerprint", "")
        if ofp in assigned: continue
        overlap = len(all_words[fp] & all_words[ofp])
        if overlap >= 4:  # at least 4 matching words/bigrams
            cluster.append(other)
            assigned.add(ofp)
    
    if len(cluster) >= 2:
        # Pick shortest title as event name
        cluster.sort(key=lambda x: len(x.get("title", "")))
        sources = {}
        for it2 in cluster:
            sn = it2.get("source_name", "unknown")
            if sn not in sources:
                sources[sn] = {"name": sn, "url": it2.get("url", ""), "title": it2.get("title", "")[:80]}
        clusters.append({
            "event": cluster[0].get("title", "")[:100],
            "resonance": len(sources),
            "item_count": len(cluster),
            "sources": list(sources.values()),
            "search_query": " ".join(list(all_words[fp])[:4]),
        })

clusters.sort(key=lambda x: -x["resonance"])
clusters = [c for c in clusters if c["resonance"] >= 2][:15]

print("Clusters found: {}".format(len(clusters)))
for i, c in enumerate(clusters):
    print("  {:2}. [{} sources] {}".format(i+1, c["resonance"], c["event"][:80]))
    for s in c["sources"][:3]:
        print("       - {}".format(s["name"][:40]))
