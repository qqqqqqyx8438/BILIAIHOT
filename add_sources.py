import sys, io, yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

cfg = yaml.safe_load(open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/sources.yaml", "r", encoding="utf-8"))

insert_idx = None
for i, s in enumerate(cfg["sources"]):
    if s["id"] == "cn_qbitai":
        insert_idx = i + 1
        break
if insert_idx is None:
    insert_idx = len(cfg["sources"])

new_sources = [
    {
        "id": "cn_infoq", "name": "InfoQ 中国", "type": "native_rss",
        "url": "https://www.infoq.cn/feed", "category": "中文媒体",
        "tags": ["AI", "开发", "架构"], "enabled": True,
    },
    {
        "id": "cn_latepost", "name": "晚点LatePost", "type": "native_rss",
        "url": "https://feedpress.me/wx-postlate", "category": "中文媒体",
        "tags": ["商业", "科技", "深度"], "enabled": True,
    },
    {
        "id": "cn_jiqizhixin", "name": "机器之心", "type": "native_rss",
        "url": "https://www.jiqizhixin.com/rss", "category": "中文媒体",
        "tags": ["AI", "产业", "技术"], "enabled": False,
    },
    {
        "id": "cn_techqq", "name": "腾讯科技", "type": "native_rss",
        "url": "https://tech.qq.com/web/feed.xml", "category": "中文媒体",
        "tags": ["科技", "互联网", "深度"], "enabled": False,
    },
]

for s in new_sources:
    cfg["sources"].insert(insert_idx, s)
    insert_idx += 1
    status = "enabled" if s["enabled"] else "disabled"
    print("+ {} [{}]".format(s["name"], status))

yaml.dump(cfg, open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/sources.yaml", "w", encoding="utf-8"),
          allow_unicode=True, default_flow_style=False)
print("\nTotal sources: {}".format(len(cfg["sources"])))
