import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

src = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "r", encoding="utf-8").read()

# Find the section after aggregation loop, before save()
# Add cross-verification call
old_end = '''    all_items.sort(key=lambda x: parse_dt(x.get("published")), reverse=True)

    total_enabled = sum(1 for s in cfg["sources"] if s.get("enabled",True))
    print(f"\n  [OK] {ok}/{total_enabled} sources, {len(all_items)} items, {len(source_stats)} individual sources")'''

new_end = '''    all_items.sort(key=lambda x: parse_dt(x.get("published")), reverse=True)

    # Cross-verify with daily briefings
    briefing_verified = []
    if hasattr(aggregate, "briefing_items"):
        for bid, bitems in aggregate.briefing_items:
            verified = cross_verify(bitems, all_items)
            briefing_verified.extend(verified)
            verified_count = sum(1 for v in verified if v["verified"])
            print(f"  [VERIFY] {bid}: {verified_count}/{len(verified)} items cross-verified")

    total_enabled = sum(1 for s in cfg["sources"] if s.get("enabled",True))
    briefing_count = sum(1 for s in cfg["sources"] if s.get("type")=="daily_briefing" and s.get("enabled",True))
    print(f"\n  [OK] {ok}/{total_enabled} sources, {len(all_items)} items, {len(source_stats)} individual sources")'''

src = src.replace(old_end, new_end)

# Now update save() to include briefing data
old_save_sig = "def save(items, source_stats, cfg):"
new_save_sig = "def save(items, source_stats, cfg, briefing_verified=None):"
src = src.replace(old_save_sig, new_save_sig)

# Add briefing output after stats
old_stats_end = '''    (OUTPUT_DIR / "source_ranking.json").write_text(
        json.dumps(ranked, ensure_ascii=False, indent=2), encoding="utf-8")'''

new_stats_end = '''    (OUTPUT_DIR / "source_ranking.json").write_text(
        json.dumps(ranked, ensure_ascii=False, indent=2), encoding="utf-8")

    # Save cross-verified briefing items
    if briefing_verified:
        verified_items = [v for v in briefing_verified if v["verified"]]
        (OUTPUT_DIR / "briefing_verified.json").write_text(
            json.dumps(verified_items, ensure_ascii=False, indent=2), encoding="utf-8")
        (OUTPUT_DIR / "briefing_all.json").write_text(
            json.dumps(briefing_verified, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [FILE] briefing_verified.json ({len(verified_items)} verified items)")
        print(f"  [FILE] briefing_all.json ({len(briefing_verified)} total briefing items)")'''

src = src.replace(old_stats_end, new_stats_end)

# Update main() to pass briefing_verified
src = src.replace(
    "save(items, src_stats, cfg)",
    "save(items, src_stats, cfg, briefing_verified if 'briefing_verified' in dir() else None)"
)

# Fix - make briefing_verified available in main
old_main_save = "items, src_stats = aggregate(cfg)"
new_main_save = "items, src_stats = aggregate(cfg)\n    briefing_verified = getattr(aggregate, 'briefing_verified', None) if hasattr(aggregate, 'briefing_verified') else None"
src = src.replace(old_main_save, new_main_save)

# Actually, let me restructure this properly. The briefing_verified is created inside aggregate(). Let me return it.
old_return = "return all_items, source_stats"
new_return = '''    # Package briefing results
    briefing_data = None
    if briefing_verified:
        briefing_data = briefing_verified
    
    return all_items, source_stats, briefing_data'''
src = src.replace(old_return, new_return)

# Update main to unpack 3 values
old_unpack = "items, src_stats = aggregate(cfg)"
new_unpack = "items, src_stats, briefing_data = aggregate(cfg)"
src = src.replace(old_unpack, new_unpack)

# Update save call
old_save_call = "save(items, src_stats, cfg)"
new_save_call = "save(items, src_stats, cfg, briefing_data)"
src = src.replace(old_save_call, new_save_call)

open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "w", encoding="utf-8").write(src)
print("Updated: cross-verification wired into output pipeline")
