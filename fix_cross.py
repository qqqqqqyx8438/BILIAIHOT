src = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "r", encoding="utf-8").read()

# Find the exact location to insert cross-verify call
# After the main loop sorts all_items, before the Package briefing results
marker = "    all_items.sort(key=lambda x: parse_dt(x.get(\"published\")), reverse=True)\n\n    # Package briefing results"
cross_verify_block = """    all_items.sort(key=lambda x: parse_dt(x.get("published")), reverse=True)

    # Cross-verify with daily briefings
    briefing_verified = []
    if hasattr(aggregate, "briefing_items"):
        for bid, bitems in aggregate.briefing_items:
            verified = cross_verify(bitems, all_items)
            briefing_verified.extend(verified)
            vc = sum(1 for v in verified if v["verified"])
            print("  [VERIFY] {}: {}/{} items cross-verified".format(bid, vc, len(verified)))

    # Package briefing results"""

if marker in src:
    src = src.replace(marker, cross_verify_block)
    open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "w", encoding="utf-8").write(src)
    print("Cross-verify call inserted")
else:
    print("Marker not found - checking what's there...")
    # Print lines around where it should be
    for i, line in enumerate(src.split("\n")):
        if "Package briefing" in line:
            print("Line {}: {}".format(i, line))
