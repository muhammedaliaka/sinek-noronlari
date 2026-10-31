@echo off
rem Sinek kontrol sunucusu (Windows, bash/WSL GEREKMEZ). Kullanim: scripts\ops_baslat.bat --relay origin:ops-relay
rem Python'u once venv'den (.venv), yoksa PATH'teki python'dan, yoksa "py -3" ile bulur.
cd /d "%~dp0\.."
if exist ".venv\Scripts\python.exe" ( ".venv\Scripts\python.exe" -X utf8 -I -m sinek.ops.server %* & goto :eof )
where python >nul 2>nul && ( python -X utf8 -I -m sinek.ops.server %* & goto :eof )
py -3 -X utf8 -I -m sinek.ops.server %*
