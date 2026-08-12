# Find the cross-verify section in aggregator.py
lines = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/aggregator.py", "r", encoding="utf-8").readlines()
for i, line in enumerate(lines):
    if "briefing_verified" in line or "cross_verify" in line or "VERIFY" in line:
        print("{}: {}".format(i+1, line.rstrip()))
