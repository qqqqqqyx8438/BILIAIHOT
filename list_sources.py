import yaml, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

cfg = yaml.safe_load(open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/sources.yaml", "r", encoding="utf-8"))

cats = {}
for s in cfg["sources"]:
    cat = s.get("category", "other")
    cats.setdefault(cat, []).append(s)

emoji = {
    "KOL": "🔥", "企业官号": "🏢", "研究机构": "🏛️",
    "媒体": "📰", "论文": "📄", "中文媒体": "🇨🇳",
    "开源": "💻", "官方博客": "📝"
}

total = sum(len(v) for v in cats.values())
enabled = sum(1 for v in cats.values() for s in v if s.get("enabled", True))
print("Total: {} sources ({} enabled)".format(total, enabled))
print()

for cat in sorted(cats.keys(), key=lambda c: -len(cats[c])):
    items = cats[cat]
    en = sum(1 for s in items if s.get("enabled", True))
    print("=" * 50)
    print("  {} {} ({}/{})".format(emoji.get(cat, ""), cat, en, len(items)))
    print("=" * 50)
    for i, s in enumerate(items, 1):
        status = "✅" if s.get("enabled", True) else "⏸"
        name = s["name"]
        stype = s["type"]
        tags = ", ".join(s.get("tags", []))
        print("  {:2}. {} | {} | {} | {}".format(i, status, name, stype, tags))
    print()
