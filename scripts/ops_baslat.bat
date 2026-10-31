@echo off
rem Kontrol sunucusunu baslatir (docs/uzak_kontrol.md). Dogrulayici kuyruklari bash betigi kullanir: WSL2 ya da Git Bash gerekir.
cd /d "%~dp0\.."
py -3 -I -m sinek.ops.server %*
