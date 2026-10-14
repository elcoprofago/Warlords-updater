@echo off
rem Tanda de prueba: 3 partidas IA contra IA (ver TAREAS.md). Cerrar esta ventana corta la tanda; se retoma con: python ia\tanda.py seguir
cd /d %~dp0..
python ia\tanda.py nueva --partidas 3
python ia\informe.py
python ia\aviso.py
pause
