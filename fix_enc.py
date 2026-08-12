src = open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/write_html.py", "r", encoding="utf-8").read()
src = src.replace("utf-8-sig", "utf-8")
open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/write_html.py", "w", encoding="utf-8").write(src)
print("Fixed encoding")
