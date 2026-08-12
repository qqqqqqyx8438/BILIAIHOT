# AI 热点看板 · 多源 RSS 聚合器

> 一次配置，多源聚合，一键生成 AI 热点数据 feed。

## 信源覆盖

| 分类 | 来源 | 数量 |
|------|------|------|
| 🔥 X KOL | Karpathy / Sam Altman / Yann LeCun / Jim Fan / Andrew Ng ... | 9 |
| 🏢 AI 企业 | OpenAI / Anthropic / DeepMind / NVIDIA / DeepSeek / Cursor ... | 12 |
| 🏛️ 研究机构 | Stanford HAI / MIT CSAIL / Berkeley AI ... | 3 |
| 📰 科技媒体 | MIT Tech Review / TLDR / AlphaSignal ... | 3 |
| 📄 学术论文 | arXiv CS.AI / CS.CL / CS.CV | 3 |
| 📝 官方博客 | OpenAI / DeepMind / Anthropic / Meta AI | 4 |
| 🇨🇳 中文媒体 | 量子位 | 1 |
| 💻 开源 | GitHub Trending | 1 |

## 快速上手

### 1. 安装依赖
```bash
pip install pyyaml feedparser
```

### 2. 运行采集
```bash
python aggregator.py
```

### 3. 查看结果
```
data/ai_feed.json       # 最新 500 条
data/ai_feed_full.json   # 完整历史（7天）
data/stats.json          # 采集统计
```

## 信源管理

编辑 `sources.yaml`：

```yaml
# 新增 X 账号
- id: x_kol_newaccount
  name: 显示名称
  type: native_rss
  url: https://nitter.net/用户名/rss
  category: KOL
  tags: [AI]
  enabled: true

# 新增普通 RSS
- id: blog_newsource
  name: 源名称
  type: native_rss
  url: https://example.com/feed.xml
  category: 官方博客
  tags: [AI]
  enabled: true

# 临时停用
  enabled: false

# 删除：直接删掉对应块
```

改完运行 `python aggregator.py` 即刻生效。

## 定时采集（Windows 可选）

创建计划任务，每 30 分钟自动跑一次：
```powershell
schtasks /create /tn "AI-Hotboard" /tr "python C:\...\aggregator.py" /sc minute /mo 30
```
