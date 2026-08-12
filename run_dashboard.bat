@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo   AI 热点看板 · 本地服务器
echo   http://localhost:8765
echo ==========================================
echo.
start http://localhost:8765
python -m http.server 8765
