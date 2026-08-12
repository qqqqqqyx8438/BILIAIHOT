import sys, io, re, json, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import yaml

cfg = yaml.safe_load(open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/sources.yaml", "r", encoding="utf-8"))

# Add as daily_briefing type
briefing = {
    "id": "briefing_juya",
    "name": "橘鸦AI早报",
    "type": "daily_briefing",
    "url": "https://daily.juya.uk/rss.xml",
    "category": "AI早报",
    "tags": ["每日精选", "交叉验证", "中文摘要"],
    "enabled": True,
    "cross_verify": True,  # Enable cross-verification
}

# Insert at end
cfg["sources"].append(briefing)

yaml.dump(cfg, open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/sources.yaml", "w", encoding="utf-8"),
          allow_unicode=True, default_flow_style=False)
print("Added: 橘鸦AI早报 [daily_briefing, cross_verify=True]")
print("Total sources: {}".format(len(cfg["sources"])))
