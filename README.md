# AI 热点看板

多源 RSS 聚合、事件导向热点榜、信源原文跳转，以及 B 站近 48 小时高播视频精选。

## 在线看板

GitHub Pages 部署完成后，访问：

```text
https://qqqqqqyx8438.github.io/BILIAIHOT/
```

仓库的 **Actions** 会按约 30 分钟运行一次：采集 RSS、生成 TOP10 热点、抓取 B 站视频及封面，并将静态结果发布到 Pages。

## 本地运行

```powershell
python -m pip install -r requirements.txt
python aggregator.py
python build_dashboard.py
python build_bilibili_data.py
python server.py
```

然后打开 <http://localhost:8765/dashboard.html>。

也可以双击 `run_dashboard.bat` 一键执行以上流程。

## 信源管理

日常只编辑 `sources.yaml`：

- `enabled: true/false`：启用或暂停信源；
- `native_rss`：单个 RSS/Atom 信源；
- `aggregate_rss`：AIHOT 分类聚合源，会按条目来源拆分；
- `daily_briefing`：橘鸦 AI 早报，用于交叉验证，不作为单条主信源；
- 新增、删除或调整后，提交并推送到 `main`，Actions 会自动重新构建。

## GitHub Pages 首次开启

在仓库中打开：

1. `Settings` → `Pages`；
2. `Build and deployment` → `Source` 选择 `GitHub Actions`；
3. 回到 `Actions` 手动运行 `Deploy AI Hotboard to GitHub Pages`；
4. 等待 `deploy` job 成功后，用仓库的 Pages URL 访问。

如果仓库为 Private，GitHub Pages 是否可用取决于账号/组织套餐；若 Pages 页面不允许部署，需要将仓库改为 Public 或使用支持私有 Pages 的套餐。

## 注意

B 站抓取由 Actions 在构建阶段完成，前端只读取 `data/bilibili.json`，因此在线页面不依赖你的本地电脑和 `server.py`。B 站接口可能对云端 IP 限流；若某轮抓取失败，热点榜仍会正常发布，B 站卡片会显示为空，下一轮会自动重试。
