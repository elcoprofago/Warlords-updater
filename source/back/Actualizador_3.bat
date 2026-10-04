::[Bat To Exe Converter]
::
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6ntZjN4NABJCfxakfDM2qGBMs3bLI9+I0w==
::YAwzoRdxOk+EWAjk
::fBw5plQjdCuDJF2F5kk8JwlQXzaHLFezBboS5/u7oqqFrVkSWucsRKzUyqaBJuEU5QvtdplN
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+IeA==
::cxY6rQJ7JhzQF1fEqQJhZksaH2Q=
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQIRKw9BTQiLJmq+Cad8
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCqDJHSN5wI0JxhBQQGMKGSpOpgV+6jL/eWAsEwQVfEDeYzPz7WCKfoS7kr2SZcuwm9blMIWDR9XbC6KbRshqGJLrGWBONXSthfkKg==
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
setlocal

REM Obtener carpeta Descargas del usuario (método infalible)
for /f "usebackq delims=" %%D in (`powershell -command "(New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path"`) do set DOWNLOADS=%%D

REM Crear carpeta interna del actualizador
if not exist "%DOWNLOADS%\W3Updater" mkdir "%DOWNLOADS%\W3Updater"

REM Crear carpeta del juego si no existe
if not exist "C:\Warlords3" mkdir "C:\Warlords3"

REM Mostrar banner desde archivo externo
color 0E
cls
type banner.txt
echo.
pause

:MENU
cls
color 0E
echo =================================
echo ELIGE LAS SIGUIENTES ACTUALIZACIONES
echo (puedes elegir varias separadas por espacio)
echo =================================
color 0A
echo 1) ARMY
echo 2) SPELL
echo 3) HERO
echo 4) ESCENARIOS
echo 5) ITEMS
echo 6) NUEVA VERSION DEL VALIDATOR
color 0C
echo 7) SALIR
color 07
set /p choices="Opciones: "

for %%c in (%choices%) do (
    if "%%c"=="1" call :UPDATE "ARMY" "1Pl0e6EBBFEcOdditoQ7Uau7BYHoKMFQa"
    if "%%c"=="2" call :UPDATE "SPELL" "1qjChLLsqWbk2_bxPegNgDi_hhbqf-SGT"
    if "%%c"=="3" call :UPDATE "HERO" "1_kBR09WOYmy8KkjXSPEFR0ykxglhxBRh"
    if "%%c"=="4" call :UPDATE "ESCENARIOS" "1MGzSrTssVvXGYlpHudWvY_Y4xEaBbG7d"
    if "%%c"=="5" call :UPDATE "ITEMS" "1RzRE_9uPIOSS2BKlp4U1WAOAw6HfxeiG"
    if "%%c"=="6" goto :VALIDATOR
    if "%%c"=="7" goto :EXIT
)

pause
goto MENU

:UPDATE
set folder=%~1
set fileid=%~2
set zipfile=%DOWNLOADS%\W3Updater\%folder%.zip
set url=https://drive.google.com/uc?export=download^&id=%fileid%

color 0B
echo --------------------------------
echo Verificando conexion...
ping -n 1 google.com >nul || (color 0C & echo ERROR: Sin conexion a internet & pause & goto :eof)

echo Descargando %folder% desde Google Drive...
powershell -command "Invoke-WebRequest -Uri '%url%' -OutFile '%zipfile%'"

if not exist "%zipfile%" (
    color 0C
    echo ERROR: No se pudo descargar %folder%.
    pause
    goto :eof
)

echo Descomprimiendo en C:\Warlords3...
powershell -command "Expand-Archive -Force '%zipfile%' 'C:\Warlords3'"

color 0E
echo Eliminando archivo temporal %zipfile%...
del /f /q "%zipfile%"

color 0A
echo Registrando actualizacion en el log...
echo [%date% %time%] Carpeta %folder% actualizada >> "C:\Warlords3\update_log.txt"

echo La carpeta %folder% se actualizo correctamente MUNIECO VICIOSO !!
pause
color 07
goto :eof


:VALIDATOR
color 0B
echo --------------------------------
echo Verificando conexion...
ping -n 1 google.com >nul || (color 0C & echo ERROR: Sin conexion a internet & pause & goto :eof)

set zipfile=%DOWNLOADS%\W3Updater\DarkValidator.zip
set extractfolder=%DOWNLOADS%
set url=https://drive.google.com/uc?export=download^&id=17Y61RSBNyvRPTkmtx0y_BTWHQki7VYlE

echo Descargando nueva version del Validator...
powershell -command "Invoke-WebRequest -Uri '%url%' -OutFile '%zipfile%'"

if not exist "%zipfile%" (
    color 0C
    echo ERROR: No se pudo descargar el Validator.
    pause
    goto MENU
)

echo Descomprimiendo DarkValidator.zip en carpeta DESCARGAS...
powershell -command "Expand-Archive -Force '%zipfile%' '%extractfolder%'"

color 0E
echo Eliminando archivo temporal...
del /f /q "%zipfile%"

color 0A
echo VALIDATOR actualizado en carpeta "%DOWNLOADS%"
pause
color 07
goto MENU


:EXIT
echo Saliendo del actualizador...
pause
exit
