src = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "r", encoding="utf-8").read()

# Replace the broken snippet with a clean one
old = """    # Package briefing results
    briefing_data = None
    if briefing_verified:
        briefing_data = briefing_verified
    
    return all_items, source_stats, briefing_data"""

new = """    # Package briefing results
    bv = locals().get("briefing_verified", None)
    briefing_data = bv if bv else None
    return all_items, source_stats, briefing_data"""

src = src.replace(old, new)
open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "w", encoding="utf-8").write(src)
print("Fixed")
