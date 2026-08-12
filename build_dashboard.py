import json, re, sys, io
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from email.utils import parsedate_to_datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path("C:/Users/qiyanxi/Bitto/default/ai-hotboard")
DATA = BASE / "data"

items = json.loads((DATA / "ai_feed.json").read_text(encoding="utf-8"))
now = datetime.now()
cutoff = now - timedelta(hours=48)
recent = [it for it in items if parsedate_to_datetime(it.get("published", "")).replace(tzinfo=None) >= cutoff]

# Filter out generic words
SKIP_KW = {"模型", "发布", "支持", "智能", "机器", "提供", "功能", "用户",
           "数据", "技术", "能力", "完成", "发现", "创建", "实现", "推出",
           "公司", "报道", "消息", "如何", "公布", "宣布", "正式", "最新"}

PATTERNS = {
    "OpenAI|GPT-5": r"OpenAI|GPT[-\s]*5",
    "Anthropic|Claude": r"Anthropic|Claude",
    "NVIDIA|Nemotron": r"NVIDIA|Nemotron",
    "DeepSeek": r"DeepSeek",
    "Muse|Glimmer": r"Muse|Glimmer",
    "Gemini": r"Gemini",
    "Meta|Llama": r"Meta|Llama",
    "Mistral": r"Mistral",
    "Qwen|通义千问": r"Qwen|千问",
    "Grok|xAI": r"Grok|xAI",
    "Runway|Seedance": r"Runway|Seedance",
    "Manus": r"Manus",
    "宇树|IPO|上市": r"宇树|IPO|上市|融资",
    "Agent|智能体|MCP": r"Agent|智能体|MCP",
    "开源模型": r"开源.*模型|模型.*开源",
    "视频生成": r"视频生成|Seedance|LTX",
    "语音|TTS": r"语音|TTS|VoiceChat",
    "AI安全|漏洞": r"安全|漏洞|越狱|攻击|网络",
    "芯片|算力|昇腾": r"芯片|昇腾|GPU|算力|数据中心",
    "数学|推理": r"数学|推理|黎曼",
    "机器人|具身": r"机器人|具身",
    "SpaceX": r"SpaceX",
    "Google|谷歌": r"Google|谷歌",
}

kw_items = defaultdict(set)
for name, pat in PATTERNS.items():
    for item in recent:
        text = item.get("title", "") + " " + item.get("summary", "")
        if re.search(pat, text, re.IGNORECASE):
            kw_items[name].add(item.get("fingerprint", ""))

# Add Chinese bigrams (3+ sources)
cn = defaultdict(set)
for item in recent:
    title = item.get("title", "")
    for w in re.findall(r"[\u4e00-\u9fff]{2}", title):
        if w not in SKIP_KW:
            cn[w].add(item.get("fingerprint", ""))
for w, ids in sorted(cn.items(), key=lambda x: -len(x[1])):
    if len(ids) >= 3 and w not in kw_items and w not in SKIP_KW:
        kw_items[""+w+""] = ids  # Use raw Chinese word

# Cluster
clusters, assigned = [], set()
for kw, ids in sorted(kw_items.items(), key=lambda x: -len(x[1])):
    if len(ids) < 2: continue
    cluster_items = [it for it in recent if it.get("fingerprint") in ids and it.get("fingerprint") not in assigned]
    if len(cluster_items) < 2: continue
    for it in cluster_items:
        assigned.add(it.get("fingerprint", ""))
    
    sources = {}
    for it in cluster_items:
        sn = it.get("source_name", "unknown")
        if sn not in sources:
            sources[sn] = {"name": sn, "url": it.get("url", ""), "title": it.get("title", "")[:80]}
    
    clusters.append({
        "keyword": kw.split("|")[0],
        "resonance": len(sources),
        "item_count": len(cluster_items),
        "sources": list(sources.values()),
        "representative_titles": [it.get("title","") for it in cluster_items[:3]],
        "search_query": kw.split("|")[0].replace("\"", ""),
    })

clusters.sort(key=lambda x: -x["resonance"])
top = [c for c in clusters if c["resonance"] >= 2][:15]

dashboard = {
    "generated_at": now.isoformat(),
    "total_recent_items": len(recent),
    "hot_topics": [{
        "rank": i, "keyword": c["keyword"], "resonance": c["resonance"],
        "item_count": c["item_count"],
        "summary": c["representative_titles"][0][:120],
        "titles": c["representative_titles"],
        "sources": c["sources"],
        "search_query": c["search_query"],
    } for i, c in enumerate(top, 1)]
}

(DATA / "dashboard.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
for i, c in enumerate(top):
    print("  {:2}. [{}] {} sources".format(i+1, c["keyword"], c["resonance"]))
print("Done: {} topics saved".format(len(top)))
