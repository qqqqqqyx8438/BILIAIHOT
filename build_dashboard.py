import json, re, sys, io
from pathlib import Path
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE_DIR = Path(__file__).resolve().parent
DATA = BASE_DIR / "data"

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


items = json.loads((DATA / "ai_feed.json").read_text(encoding="utf-8"))
now = datetime.now()
cutoff = now - timedelta(hours=48)
recent = [it for it in items if parse_dt(it.get("published","")) >= cutoff]

# Split Chinese anchors vs English candidates
zh = [it for it in recent if re.search(r'[\u4e00-\u9fff]', it.get("title",""))]
en = [it for it in recent if not re.search(r'[\u4e00-\u9fff]', it.get("title",""))]
print("Chinese anchors: {}, English candidates: {}".format(len(zh), len(en)))

def extract_entities(text):
    """Extract entities: model names, companies, products (bilingual)"""
    ents = set()
    # Model names with version
    for m in re.findall(r'(Nemotron[-\s]?\d+\.?\d*|GPT[-\s]?\d+\.?\d*|Claude\s+\w+|'
                         r'Gemini\s*\d+\.?\d*|Llama[-\s]?\d+\.?\d*|Muse\s+\w+|'
                         r'Grok[-\s]?\d+\.?\d*|Seedance[-\s]?\d+\.?\d*|Qwen[-\s]?\d+[-\w.]*|'
                         r'LTX[-\s]?\d+\.?\d*|Cosmos\s*\d|WeatherNext|IndexTTS[-\s]?\d+\.?\d*|'
                         r'Wan\d+\.?\d*|GLM[-\s]?\d+\.?\d*|Mojo\s*1\.\d|Astra|'
                         r'Opus\s*\d+\.?\d*|Fable\s*\d+|SGLang|OpenClaw|VoiceChat|'
                         r'MAI[-\w]*|DeepSeek[-\s]?\w*|NemotronLabs\s*\w+)', text, re.I):
        ents.add(m.strip().lower())
    # Companies (bilingual)
    for m in re.findall(r'(OpenAI|Anthropic|NVIDIA|英伟达|DeepSeek|Meta|Google|谷歌|微软|Microsoft|'
                         r'xAI|Mistral|Perplexity|Runway|Manus|宇树|智谱|通义千问|千问|'
                         r'百灵|面壁|火山引擎|字节|腾讯|阿里|华为|商汤|SpaceX|Cursor|'
                         r'OpenRouter|紫东太初|擎羽|群青|智象未来|HiDream)', text, re.I):
        ents.add(m.lower())
    return ents

for it in recent:
    it["ents"] = extract_entities(it.get("title","") + " " + it.get("summary","")[:300])

# For each Chinese anchor, find related items (zh + en) sharing entities
clusters = []
used = set()

# Sort zh anchors by title quality (shorter, more specific first)
zh_sorted = sorted(zh, key=lambda x: len(x.get("title","")))

for anchor in zh_sorted:
    fp = anchor.get("fingerprint","")
    if fp in used:
        continue
    ents = anchor["ents"]
    if not ents:
        continue

    # Find related items
    related = [anchor]
    used.add(fp)
    for other in recent:
        ofp = other.get("fingerprint","")
        if ofp in used:
            continue
        if ents & other["ents"]:
            related.append(other)
            used.add(ofp)

    sources = {}
    for c in related:
        sn = c.get("source_name","unknown")
        if sn not in sources:
            sources[sn] = {"name": sn, "url": c.get("url",""), "title": c.get("title","")[:80]}

    # Search query = entities
    search_query = " ".join(sorted(ents, key=lambda x: -len(x))[:2])

    clusters.append({
        "event": anchor.get("title","")[:100],
        "resonance": len(sources),
        "item_count": len(related),
        "sources": list(sources.values()),
        "search_query": search_query,
    })

# Sort by resonance
clusters.sort(key=lambda x: -x["resonance"])

# Take top 10, but ensure min resonance 1
top = clusters[:10]

# If still < 10, add remaining zh anchors as singles
if len(top) < 10:
    for anchor in zh_sorted:
        if len(top) >= 10:
            break
        if anchor.get("fingerprint","") in used:
            continue
        top.append({
            "event": anchor.get("title","")[:100],
            "resonance": 1,
            "item_count": 1,
            "sources": [{"name": anchor.get("source_name",""), "url": anchor.get("url",""), "title": anchor.get("title","")[:80]}],
            "search_query": " ".join(sorted(anchor["ents"], key=lambda x: -len(x))[:2]) or anchor.get("title","")[:30],
        })
    top.sort(key=lambda x: -x["resonance"])

print("\nEvent Topics: {}".format(len(top)))
for i, c in enumerate(top):
    print("  {:2}. [{} src] {}".format(i+1, c["resonance"], c["event"][:70]))
    print("      query: {}".format(c["search_query"]))

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
    } for i, c in enumerate(top, 1)]
}

(DATA / "dashboard.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nSaved {} topics".format(len(top)))
