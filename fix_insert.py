src = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "r", encoding="utf-8").read()
lines = src.split("\n")

# Find where to insert - after the sort, before "Package briefing results"
for i, line in enumerate(lines):
    if "Package briefing results" in line:
        # Insert before this line
        insert_at = i
        break

# Insert the cross-verify block
block = [
    "",
    "    # Cross-verify with daily briefings",
    "    briefing_verified = []",
    "    if hasattr(aggregate, \"briefing_items\"):",
    "        for bid, bitems in aggregate.briefing_items:",
    "            verified = cross_verify(bitems, all_items)",
    "            briefing_verified.extend(verified)",
    "            vc = sum(1 for v in verified if v[\"verified\"])",
    '            print("  [VERIFY] {}: {}/{} items cross-verified".format(bid, vc, len(verified)))',
    ""
]

for j, bl in enumerate(block):
    lines.insert(insert_at + j, bl)

open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "w", encoding="utf-8").write("\n".join(lines))
print("Cross-verify call inserted at line {}".format(insert_at))
