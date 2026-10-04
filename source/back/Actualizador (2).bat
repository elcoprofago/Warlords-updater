::[Bat To Exe Converter]
::
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdafxylax16vXZW1g==
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdZbB+yURompSBWrnDl
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdeax6nex8wqHpHiXGXO4mIqxuB
::YAwzoRdxOk+EWAjk
::fBw5plQjdCuDJF2F5kk8JwlQXzaHLFezBboS5/u7oqqFrVkSWucsRKzUyqaBJuEU5QvtdplN
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSTk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+IeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVsFAlTMbCXiZg==
::ZQ05rAF9IAHYFVzEqQIUKQlfQAuQOHj6M6UY6fz+/Yo=
::eg0/rx1wNQPfEVWB+kM9LVsJDCWBKH67CrwG6ez0/aqIpEQeXeMzGA==
::fBEirQZwNQPfEVWB+kM9LVsJDBPRKXu+B6EZ+og=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCqDJHSN5wI0JxhBQQGMKGSpOpgV+6jL/eWAsEwQVfEDeYzPz7WCKfoS7kr2SYUiw2hZnfctDw9Nfx6idA4wpnwMs3yAVw==
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
::[Bat To Exe Converter]
::
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdafxylax16vXZW1g==
::YAwzoRdxOk+EWAjk
::fBw5plQjdCuDJF2F5kk8JwlQXzaHLFezBboS5/u7oqqFrVkSWucsRKzUyqaBJuEU5QvtdplN
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSTk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+IeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVsFAlTMbCXvZg==
::ZQ05rAF9IAHYFVzEqQIUKQlfQAuQOHj6M6UY6fz+/Yo=
::eg0/rx1wNQPfEVWB+kM9LVsJDCWBKH67CrwG6ez0/aqIpEQeXeMzGA==
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCqDJHSN5wI0JxhBQQGMKGSpOpgV+6jL/eWAsEwQVfEDeYzPz7WCKfoS7kr2SYUiw2hZnfctDw9Nfx6idA4wpnwMs3yAVw==
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
color 0C
echo 6) *** ACTUALIZAR TODO EL JUEGO ***
color 0A
echo 7) NUEVA VERSION DEL VALIDATOR
color 0C
echo 8) SALIR
color 07
set /p choices="Opciones: "

REM ============================
REM VALIDACION: NO PERMITIR COMBINAR 6 CON OTRAS
REM ============================
echo %choices% | find "6" >nul
if %errorlevel%==0 (
    for %%x in (%choices%) do (
        if not "%%x"=="6" (
            color 0C
            echo ERROR: La opcion 6 no puede combinarse con otras.
            echo Elegila sola.
            pause
            goto MENU
        )
    )
)

REM ============================
REM SALTO LIMPIO A LA OPCION 6
REM ============================
if "%choices%"=="6" goto FULLUPDATE

REM ============================
REM PROCESAR OTRAS OPCIONES
REM ============================
for %%c in (%choices%) do (
    if "%%c"=="1" call :UPDATE "ARMY" "1Pl0e6EBBFEcOdditoQ7Uau7BYHoKMFQa"
    if "%%c"=="2" call :UPDATE "SPELL" "1qjChLLsqWbk2_bxPegNgDi_hhbqf-SGT"
    if "%%c"=="3" call :UPDATE "HERO" "1_kBR09WOYmy8KkjXSPEFR0ykxglhxBRh"
    if "%%c"=="4" call :UPDATE "ESCENARIOS" "1MGzSrTssVvXGYlpHudWvY_Y4xEaBbG7d"
    if "%%c"=="5" call :UPDATE "ITEMS" "1RzRE_9uPIOSS2BKlp4U1WAOAw6HfxeiG"
    if "%%c"=="7" goto :VALIDATOR
    if "%%c"=="8" goto :EXIT
)

pause
goto MENU


REM ============================================================
REM ===============  ETIQUETA FULLUPDATE  ======================
REM ============================================================

:FULLUPDATE
color 0C
echo --------------------------------
echo Vas a actualizar TODO el juego.
echo Esto reemplazara completamente la carpeta C:\Warlords3
echo.
set /p confirm="Confirmas la operacion? (Y/n): "

set confirm=%confirm:"=%

if /I not "%confirm%"=="Y" (
    color 0E
    echo Operacion cancelada por el usuario.
    pause
    goto MENU
)

color 0B
echo --------------------------------
echo Verificando conexion...
ping -n 1 google.com >nul || (
    color 0C
    echo ERROR: Sin conexion a internet
    pause
    goto MENU
)

REM Leer URL desde archivo externo
if not exist "fullupdate_url.txt" (
    color 0C
    echo ERROR: Falta el archivo fullupdate_url.txt
    echo No se puede descargar el paquete completo.
    pause
    goto MENU
)

for /f "usebackq delims=" %%U in ("fullupdate_url.txt") do set url=%%U

set zipfile=%DOWNLOADS%\W3Updater\Warlords3_FULL.zip

echo Descargando paquete completo Warlords3...
powershell -command "Invoke-WebRequest -Uri '%url%' -OutFile '%zipfile%'"

if not exist "%zipfile%" (
    color 0C
    echo ERROR: No se pudo descargar el paquete completo.
    pause
    goto MENU
)

for %%A in ("%zipfile%") do set size=%%~zA
if "%size%"=="0" (
    color 0C
    echo ERROR: El archivo descargado esta vacio o corrupto.
    del /f /q "%zipfile%"
    pause
    goto MENU
)

echo Descomprimiendo Warlords3_FULL.zip...
powershell -command "Expand-Archive -Force '%zipfile%' 'C:\Warlords3\'"

color 0E
echo Eliminando archivo temporal...
del /f /q "%zipfile%"

color 0A
echo JUEGO COMPLETO ACTUALIZADO EXITOSAMENTE !!
echo [%date% %time%] Juego completo actualizado >> "C:\Warlords3\update_log.txt"
pause
goto MENU



REM ============================================================
REM ====================  UPDATE NORMAL  ========================
REM ============================================================

:UPDATE
set folder=%~1
set fileid=%~2
set zipfile=%DOWNLOADS%\W3Updater\%folder%.zip

color 0B
echo --------------------------------
echo Verificando conexion...
ping -n 1 google.com >nul || (color 0C & echo ERROR: Sin conexion a internet & pause & goto :eof)

echo Descargando %folder% desde Google Drive...

REM Caso especial: ARMY usa un enlace directo estable
if /I "%folder%"=="ARMY" (
    for /f "usebackq delims=" %%U in ("army_url.txt") do set url=%%U
    powershell -command "Invoke-WebRequest -Uri '%url%' -OutFile '%zipfile%'"
) else (
    set url=https://drive.google.com/uc?export=download^&id=%fileid%
    powershell -command "Invoke-WebRequest -Uri '%url%' -OutFile '%zipfile%'"
)

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


REM ============================================================
REM ====================  VALIDATOR  ============================
REM ============================================================

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
