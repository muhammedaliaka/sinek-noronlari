@echo off
rem Sinek TEST EKRANI (Windows; sunucu/port/bash YOK). Kullanim: scripts\ekran_ac.bat --relay origin:ops-relay --auto
rem Python'u once venv'den (.venv), yoksa PATH'teki python'dan, yoksa "py -3" ile bulur.
title Sinek Test Ekrani
cd /d "%~dp0\.."
if exist ".venv\Scripts\python.exe" ( ".venv\Scripts\python.exe" -X utf8 -I -m sinek.ops.ekran %* & goto :eof )
where python >nul 2>nul && ( python -X utf8 -I -m sinek.ops.ekran %* & goto :eof )
py -3 -X utf8 -I -m sinek.ops.ekran %*
