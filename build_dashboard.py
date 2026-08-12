import json, re, sys, io
from pathlib import Path
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
DATA = Path("C:/Users/qiyanxi/Bitto/default/ai-hotboard/data")

items = json.loads((DATA / "ai_feed.json").read_text(encoding="utf-8"))
now = datetime.now()
cutoff = now - timedelta(hours=48)
recent = [it for it in items if parsedate_to_datetime(it.get("published","")).replace(tzinfo=None) >= cutoff]
print("Recent (48h): {}".format(len(recent)))

# Filter out garbage items
good = []
bad_patterns = [
    r'^RT\s*@', r'^R\s+to\s+@', r'^Pinned:', r'^(Just|Check|Try)\s',
    r'^\s*$', r'^🤔', r'^🔥', r'^\d+%', r'^@\w+$',
]
for it in recent:
    title = it.get("title","").strip()
    skip = False
    for pat in bad_patterns:
        if re.search(pat, title):
            skip = True
            break
    if not skip and len(title) > 10:
        good.append(it)
print("Good items: {}".format(len(good)))

# Use summaries for matching - they are cleaner
def extract_named_entities(text):
    """Extract named entities: companies, products, models"""
    ents = set()
    # Companies
    companies = ["OpenAI","Anthropic","NVIDIA","英伟达","DeepSeek","Meta","Google","谷歌",
                 "Microsoft","微软","xAI","Mistral","Perplexity","Runway","Manus",
                 "宇树科技","智谱","通义千问","千问","百灵","面壁","火山引擎",
                 "字节跳动","腾讯","阿里","华为","商汤","SpaceX","Tesla"]
    text_lower = text.lower()
    for c in companies:
        if c.lower() in text_lower:
            ents.add(c)
    # Models/Products
    models = re.findall(r'(GPT[-\s]?\d+\.?\d*\s*\w*|Claude\s*[A-Z]\w*\s*\d+\.?\d*|Gemini\s*\d+\.?\d*|'
                         r'Nemotron[-\s]?\d+\.?\d*\s*\w*|Llama[-\s]?\d+|Muse\s*\w+|Grok[-\s]?\d+\.?\d*|'
                         r'Seedance[-\s]?\d+\.?\d*|Qwen[-\s]?\d+\.?\d*|LTX[-\s]?\d+\.?\d*|'
                         r'Cosmos\s*\d|WeatherNext|IndexTTS|Wan\d+\.?\d+|GLM[-\s]?\d+\.?\d*|'
                         r'Mojo\s*1\.\d|Astra|Opus\s*\d+\.?\d*|Fable\s*\d+|SGLang|OpenClaw)', text, re.I)
    for m in models:
        ents.add(m.strip())
    return ents

# For each good item: extract entities from summary
for it in good:
    it["ents"] = extract_named_entities(it.get("summary","") + " " + it.get("title",""))

# Cluster: group items sharing >= 2 named entities
clusters = []
assigned = set()
for it in good:
    fp = it.get("fingerprint","")
    if fp in assigned: continue
    if not it["ents"]: continue  # skip items without identifiable entities
    
    cluster = [it]
    assigned.add(fp)
    for other in good:
        ofp = other.get("fingerprint","")
        if ofp in assigned: continue
        shared = it["ents"] & other["ents"]
        if len(shared) >= 2:
            cluster.append(other)
            assigned.add(ofp)
    
    if len(cluster) >= 2:
        # Pick best event name: prefer item with most descriptive title
        # Score: Chinese > English, shorter > longer, has company name
        def score_title(x):
            t = x.get("title","")
            s = 0
            if re.search(r'[\u4e00-\u9fff]', t): s += 100
            s -= len(t)  # shorter is better
            if any(c.lower() in t.lower() for c in ["发布","推出","开源","上市","发布","突破","达成"]): s += 50
            return s
        
        cluster.sort(key=score_title, reverse=True)
        event_name = cluster[0].get("title","")[:100]
        
        sources = {}
        for c in cluster:
            sn = c.get("source_name","unknown")
            if sn not in sources:
                sources[sn] = {"name": sn, "url": c.get("url",""), "title": c.get("title","")[:80]}
        
        # Search query from shared entities
        sq = " ".join(list(it["ents"])[:3])
        
        clusters.append({
            "event": event_name,
            "resonance": len(sources),
            "item_count": len(cluster),
            "sources": list(sources.values()),
            "search_query": sq,
        })

clusters.sort(key=lambda x: -x["resonance"])
clusters = [c for c in clusters if c["resonance"] >= 2][:15]

print("\nEvent Topics: {}".format(len(clusters)))
for i, c in enumerate(clusters):
    print("  {:2}. [{} src] {}".format(i+1, c["resonance"], c["event"][:90]))
    for s in c["sources"][:3]:
        print("       - {}".format(s["name"][:45]))

dashboard = {
    "generated_at": now.isoformat(),
    "total_recent_items": len(recent),
    "hot_topics": [{
        "rank": i,
        "event": c["event"],
        "resonance": c["resonance"],
        "item_count": c["item_count"],
        "sources": c["sources"],
        "search_query": c["search_query"],
    } for i, c in enumerate(clusters, 1)]
}

(DATA / "dashboard.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nSaved {} topics".format(len(clusters)))
