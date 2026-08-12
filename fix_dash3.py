src = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/build_dashboard.py", "r", encoding="utf-8").read()
# Add "如何" to SKIP_KW
src = src.replace('"公司", "报道", "消息"', '"公司", "报道", "消息", "如何"')
# Filter out single-source topics
src = src.replace('top = clusters[:15]', 'top = [c for c in clusters if c["resonance"] >= 2][:15]')
open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/build_dashboard.py", "w", encoding="utf-8").write(src)
print("Updated")
