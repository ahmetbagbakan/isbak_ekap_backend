@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo [%DATE% %TIME%] Daily Scraper baslatiliyor... >> scraper_daily.log
docker start isbak_postgres > nul 2>&1
".venv\Scripts\python.exe" run_scraper.py --daily >> scraper_daily.log 2>&1
echo [%DATE% %TIME%] Daily Scraper tamamlandi. >> scraper_daily.log
