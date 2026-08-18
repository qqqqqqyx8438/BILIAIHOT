@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo   AI Hotboard local dashboard
 echo   1. Collect RSS data...
echo ==========================================

python -m pip install -r requirements.txt -q
python aggregator.py
if errorlevel 1 (
    echo RSS collection failed. Check your network.
    pause
    exit /b 1
)

python build_dashboard.py
python build_bilibili_data.py
if errorlevel 1 (
    echo Bilibili static data build failed. The dashboard can still show the hot topics.
)

echo.
echo Starting local server: http://localhost:8765/dashboard.html
echo Press Ctrl+C to stop.
start http://localhost:8765/dashboard.html
python server.py
