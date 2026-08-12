@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   AI 热点看板 · 数据采集
echo ========================================
echo.
echo 1. 安装依赖（首次运行需要）
echo 2. 运行采集
echo.

REM 安装依赖
pip install pyyaml feedparser -q 2>nul

REM 运行聚合器
python aggregator.py

echo.
echo 按任意键查看最新数据摘要...
pause >nul

REM 显示 Top 10
python -c "
import json
with open('data/ai_feed.json', 'r', encoding='utf-8') as f:
    items = json.load(f)
print(f'\n🔥 最近 24h 热点 Top 10（共 {len(items)} 条）\n')
for i, item in enumerate(items[:10], 1):
    print(f'{i:2}. [{item[\"category\"]}] {item[\"title\"][:80]}')
    print(f'     {item[\"url\"][:100]}')
    print()
"

pause
