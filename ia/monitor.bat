@echo off
rem Elige el monitor donde se abre el juego en las tandas (se guarda en ia\tanda.ini).
cd /d %~dp0..
python ia\tanda.py monitor
pause
