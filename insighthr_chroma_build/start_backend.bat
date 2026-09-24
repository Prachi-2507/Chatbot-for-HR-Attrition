@echo off
cd /d "%~dp0backend"
if not exist venv\Scripts\python.exe (
  python -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python prepare_data.py
python -m uvicorn main:app --reload --port 8000
pause
