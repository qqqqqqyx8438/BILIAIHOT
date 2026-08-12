src = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/build_dashboard.py", "r", encoding="utf-8").read()
src = src.replace(
    "for c in top:\n    print(\"  {:2}. [{}] {} sources\".format(i+1, c[\"keyword\"], c[\"resonance\"]))",
    "for i, c in enumerate(top):\n    print(\"  {:2}. [{}] {} sources\".format(i+1, c[\"keyword\"], c[\"resonance\"]))"
)
open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/build_dashboard.py", "w", encoding="utf-8").write(src)
print("Fixed")
