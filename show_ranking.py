import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.load(open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/data/source_ranking.json", "r", encoding="utf-8"))
stats = json.load(open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/data/stats.json", "r", encoding="utf-8"))
src_map = stats.get("source_stats", {})

by_cat = {}
for item in data:
    name = item[0]
    info = item[1]
    count = info["count"] if isinstance(info, dict) else info
    cats = src_map.get(name, {}).get("categories", [])
    cat = cats[0] if cats else "other"
    if cat not in by_cat:
        by_cat[cat] = []
    by_cat[cat].append((name, count))

total = 0
for cat in sorted(by_cat.keys()):
    items = by_cat[cat]
    total += len(items)
    print("=" * 50)
    print("  {}  ({} sources)".format(cat, len(items)))
    print("=" * 50)
    for i, (name, count) in enumerate(sorted(items, key=lambda x: -x[1]), 1):
        print("  {:2}. {}  [{} items]".format(i, name, count))
    print()

print("> Total: {} unique sources".format(total))
