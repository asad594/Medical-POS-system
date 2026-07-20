@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
start "" .venv\Scripts\pythonw.exe run_desktop.py
