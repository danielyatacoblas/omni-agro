@echo off
cd /d "%~dp0"
echo === OMNI Agro MVP ===
echo Abriendo http://localhost:8020 ...
start "" http://localhost:8020
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8020
pause
