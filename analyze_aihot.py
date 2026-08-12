import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Manually parse the sources from all 5 feeds we collected
# Each item has a source identifier in the author field (noreply@aihot...)
# The actual source name is in parentheses at the end

all_sources = {}

# Parse from the feed data - each source is like:
# noreply@aihot.virxact.com (IT之家（RSS）)
# noreply@aihot.virxact.com (X：OpenAI (@OpenAI))
# noreply@aihot.virxact.com (公众号：数字生命卡兹克)

# From ai-models feed:
sources_models = [
    ("IT之家", "IT之家（RSS）", "科技媒体"),
    ("LMSYS Blog", "LMSYS：Blog（Chatbot Arena 团队）", "技术博客"),
    ("NVIDIA Blog", "NVIDIA Blog（RSS）", "企业博客"),
    ("蚂蚁百灵", "公众号：蚂蚁百灵（Ling）", "公众号"),
    ("Meta AI", "X：AI at Meta (@AIatMeta)", "X-KOL"),
    ("Alexandr Wang", "X：Alexandr Wang（Scale AI 创始人/Meta 首席 AI 官） (@alexandr_wang)", "X-KOL"),
    ("OpenAI Blog", "OpenAI：官网动态（RSS · 排除企业/客户案例）", "企业博客"),
    ("MarkTechPost", "MarkTechPost（RSS）", "科技媒体"),
]

# From ai-products feed:
sources_products = [
    ("OpenRouter", "X：OpenRouter (@OpenRouter)", "X-产品"),
    ("Hacker News", "Hacker News 热门（buzzing.cc 中文翻译）", "社区"),
    ("Runway", "X：Runway (@runwayml)", "X-产品"),
    ("OpenAI Devs", "X：OpenAI Developers (@OpenAIDevs)", "X-企业"),
    ("Google Cloud", "Google Cloud：Databases（RSS）", "企业博客"),
    ("智谱", "公众号：智谱（GLM）", "公众号"),
    ("Claude Devs", "X：Claude Devs (@ClaudeDevs)", "X-企业"),
    ("通义千问", "X：通义千问 / Qwen (@Alibaba_Qwen)", "X-企业"),
    ("千问APP", "公众号：千问APP（阿里）", "公众号"),
    ("数字生命卡兹克", "公众号：数字生命卡兹克", "公众号"),
    ("OpenRouter Blog", "OpenRouter：Announcements（RSS）", "技术博客"),
    ("Elon Musk", "X：Elon Musk (@elonmusk, xAI)", "X-KOL"),
    ("Suno", "X：Suno (@suno)", "X-产品"),
    ("Krea AI", "X：Krea AI (@krea_ai)", "X-产品"),
    ("火山引擎", "公众号：火山引擎", "公众号"),
    ("Anthropic Newsroom", "Anthropic：Newsroom（网页）", "企业博客"),
    ("Google Developers", "Google Developers Blog（RSS）", "企业博客"),
    ("阿里云", "X：阿里云 / Alibaba Cloud (@alibaba_cloud)", "X-企业"),
    ("LangChain", "LangChain：Blog（RSS）", "技术博客"),
    ("OpenChamber", "Hacker News 热门（buzzing.cc 中文翻译）", "社区"),
    ("ZCode/GLM", "公众号：智谱（GLM）", "公众号"),
]

# From industry feed:
sources_industry = [
    ("The Verge", "The Verge：AI（RSS）", "科技媒体"),
    ("The Decoder", "The Decoder：AI News（RSS）", "科技媒体"),
    ("Sundar Pichai", "X：Sundar Pichai (@sundarpichai)", "X-KOL"),
    ("Jensen Huang", "X：Jensen Huang (@JensenHuang)", "X-KOL"),
    ("TechCrunch", "TechCrunch：AI（RSS）", "科技媒体"),
    ("AI Safety Memes", "X：AI Safety Memes (@AISafetyMemes)", "X-KOL"),
    ("Jeff Dean", "X：Jeff Dean (@JeffDean)", "X-KOL"),
    ("Demis Hassabis", "X：Demis Hassabis (@demishassabis)", "X-KOL"),
    ("阿易 AI Notes", "X：阿易 AI Notes (@AYi_AInotes)", "X-KOL"),
    ("Rohan Paul", "X：Rohan Paul (@rohanpaul_ai)", "X-KOL"),
    ("404 Media", "404 Media", "科技媒体"),
    ("Wired", "Wired", "科技媒体"),
    ("Cloudflare Blog", "Cloudflare Blog", "企业博客"),
]

# From paper feed:
sources_paper = [
    ("Google AI Blog", "Google Blog：AI（RSS）", "企业博客"),
    ("HuggingFace Papers", "HuggingFace Daily Papers（社区热门论文）", "论文"),
    ("Anthropic Research", "Anthropic：Research（发表成果 · 网页）", "企业博客"),
    ("Ars Technica", "Ars Technica：AI（RSS）", "科技媒体"),
    ("Apple ML Research", "Apple Machine Learning Research（RSS）", "企业博客"),
    ("小红书技术", "公众号：小红书技术（dots.llm）", "公众号"),
    ("The Decoder", "The Decoder：AI News（RSS）", "科技媒体"),
]

# From tip feed:
sources_tip = [
    ("Dwarkesh Patel", "Dwarkesh Patel：Podcast & Blog（RSS）", "播客"),
    ("卡尔的AI沃茨", "公众号：卡尔的AI沃茨", "公众号"),
    ("Tomer Tunguz", "Tomer Tunguz 博客（VC 分析）", "技术博客"),
    ("Databricks", "Databricks：Blog（RSS）", "企业博客"),
    ("a16z", "a16z：News（RSS）", "VC/研究"),
    ("Mark Zuckerberg", "X：Mark Zuckerberg (@finkd)", "X-KOL"),
    ("Boris Cherny", "X：Boris Cherny (@bcherny)", "X-KOL"),
    ("Nathan Lambert", "Nathan Lambert：Interconnects（RSS）", "技术博客"),
    ("面壁智能", "公众号：面壁智能（MiniCPM）", "公众号"),
    ("GitHub Blog", "GitHub Blog", "企业博客"),
    ("Simon Willison", "Simon Willison 博客", "技术博客"),
    ("OpenBMB", "X：面壁智能 OpenBMB (@OpenBMB)", "X-企业"),
]

# Merge and deduplicate
all_raw = sources_models + sources_products + sources_industry + sources_paper + sources_tip

seen = set()
for name, full, cat in all_raw:
    if full not in seen:
        seen.add(full)
        if cat not in all_sources:
            all_sources[cat] = []
        all_sources[cat].append((name, full))

print("=" * 60)
print("  AIHOT 信源全景分析")
print("=" * 60)
print()

total = 0
for cat, items in sorted(all_sources.items(), key=lambda x: -len(x[1])):
    print(f"## {cat}  ({len(items)} sources)")
    print("| # | 短名 | 完整来源 |")
    print("|---|------|---------|")
    for i, (name, full) in enumerate(items, 1):
        print(f"| {i} | {name} | {full} |")
        total += 1
    print()

print(f"> 总计: {total} 个不同信源")
print()
print("分类分布:")
for cat, items in sorted(all_sources.items(), key=lambda x: -len(x[1])):
    print(f"  {cat}: {len(items)}")
