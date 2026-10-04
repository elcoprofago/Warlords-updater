::[Bat To Exe Converter]
::
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdZbB+yURompSBWrnDl
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdafxylax16vXZW1g==
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSddbRGuYDAhu2IMonyRVw==
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdeax6nex8wqHpHiXGXO4mIqxuB
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdQewCkURompSBWrnDl
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdRahemfTAhu2IMonyRVw==
::fBE1pAF6MU+EWHzeyG85O1tQQweXMW60EroP1MXy/Kq3sEIaRuMyeZzn27eaNeEf41/lcZk/6mlVjdkPCSdLbhenYhwLvHxO+HCdI6c=
::YAwzoRdxOk+EWAjk
::fBw5plQjdCqDJFCH+0w/OydeWQGFM3iGJZQwyd7e3cvJq04SNA==
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpSI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+IeA==
::cxY6rQJ7JhzQF1fEqQJhZksaHErVXA==
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCqDJHSN5wI0JxhBQQGMKGSpOpgV+6jL/eWAsEwQVfEDeYzPz7WCKfoS7kr2SYUiw2hZnfctDw9Nfx6idA4wpnwPoCrUeZfS40G2BE2R4ys=
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM =============== CONFIGURACIÓN INICIAL =======================
REM ============================================================

REM Obtener carpeta Descargas del usuario
for /f "usebackq delims=" %%D in (`powershell -command "(New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path"`) do set DOWNLOADS=%%D

REM Crear carpeta interna del actualizador
if not exist "%DOWNLOADS%\W3Updater" mkdir "%DOWNLOADS%\W3Updater"

REM Carpeta del juego (W3_JUEGO solo se define para probar el actualizador contra otra carpeta)
if defined W3_JUEGO (set "JUEGO=%W3_JUEGO%") else (set "JUEGO=C:\Warlords3")

REM Lista de parches publicada (W3_PARCHES_URL solo para pruebas)
if defined W3_PARCHES_URL (set "PARCHES_URL=%W3_PARCHES_URL%") else (set "PARCHES_URL=https://github.com/elcoprofago/Warlords-updater/releases/download/Actualizador/PARCHES.txt")

REM Crear carpeta del juego si no existe
if not exist "%JUEGO%" mkdir "%JUEGO%"

REM Mostrar banner
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
echo 8) PARCHES
color 0C
echo 9) SALIR
color 07
set /p choices="Opciones: "

REM Validación: no permitir combinar 6 con otras
echo %choices% | find "6" >nul
if %errorlevel%==0 (
    for %%x in (%choices%) do (
        if not "%%x"=="6" (
            color 0C
            echo ERROR: La opcion 6 no puede combinarse con otras.
            pause
            goto MENU
        )
    )
)

if "%choices%"=="6" goto FULLUPDATE

REM Procesar opciones
for %%c in (%choices%) do (
    if "%%c"=="1" call :UPDATE ARMY army_url.txt
    if "%%c"=="2" call :UPDATE SPELL spells_url.txt
    if "%%c"=="3" call :UPDATE HERO hero_url.txt
    if "%%c"=="4" call :UPDATE ESCEN escen_url.txt
    if "%%c"=="5" call :UPDATE ITEMS items_url.txt
    if "%%c"=="7" goto :VALIDATOR
    if "%%c"=="8" goto :PARCHES
    if "%%c"=="9" goto :EXIT
)

pause
goto MENU


REM ============================================================
REM =============== FULL UPDATE (TODO EL JUEGO) =================
REM ============================================================

:FULLUPDATE
color 0C
echo --------------------------------
echo Vas a actualizar TODO el juego.
echo Esto reemplazara completamente la carpeta %JUEGO%
echo.
set /p confirm="Confirmas la operacion? (Y/n): "
set confirm=%confirm:"=%

if /I not "%confirm%"=="Y" (
    color 0E
    echo Operacion cancelada.
    pause
    goto MENU
)

color 0B
echo Verificando conexion...
ping -n 1 github.com >nul || (color 0C & echo ERROR: Sin conexion & pause & goto MENU)

if not exist "fullupdate_url.txt" (
    color 0C
    echo ERROR: Falta fullupdate_url.txt
    pause
    goto MENU
)

set "URL1="
set "URL2="

for /f "usebackq tokens=* delims=" %%A in ("fullupdate_url.txt") do (
    if not defined URL1 (
        set "URL1=%%A"
        set "URL1=!URL1: =!"
    ) else (
        set "URL2=%%A"
        set "URL2=!URL2: =!"
    )
)

set zipfile=%DOWNLOADS%\W3Updater\Warlords3_FULL.zip

echo Descargando paquete completo...
powershell -command "Invoke-WebRequest -Uri '!URL1!' -OutFile '%zipfile%'" 2>nul

if not exist "%zipfile%" (
    if defined URL2 (
        echo URL primaria fallo. Probando alternativa...
        powershell -command "Invoke-WebRequest -Uri '!URL2!' -OutFile '%zipfile%'" 2>nul
    )
)

if not exist "%zipfile%" (
    color 0C
    echo ERROR: No se pudo descargar el paquete completo.
    pause
    goto MENU
)

echo Descomprimiendo...
powershell -command "Expand-Archive -Force '%zipfile%' '%JUEGO%\'"

del /f /q "%zipfile%"

color 0A
echo JUEGO COMPLETO ACTUALIZADO !!
pause
goto MENU


REM ============================================================
REM ==================== UPDATE NORMAL ==========================
REM ============================================================

:UPDATE
set folder=%~1
set urlfile=%~2
set zipfile=%DOWNLOADS%\W3Updater\%folder%.zip

color 0B
echo --------------------------------
echo Actualizando %folder%...
echo Verificando conexion...
ping -n 1 github.com >nul || (color 0C & echo ERROR: Sin conexion & pause & goto :eof)

if not exist "%urlfile%" (
    color 0C
    echo ERROR: Falta el archivo %urlfile%
    pause
    goto :eof
)

set "URL1="
set "URL2="

for /f "usebackq tokens=* delims=" %%A in ("%urlfile%") do (
    if not defined URL1 (
        set "URL1=%%A"
        set "URL1=!URL1: =!"
    ) else (
        set "URL2=%%A"
        set "URL2=!URL2: =!"
    )
)

echo Descargando desde URL primaria...
powershell -command "Invoke-WebRequest -Uri '!URL1!' -OutFile '%zipfile%'" 2>nul

if not exist "%zipfile%" (
    if defined URL2 (
        echo URL primaria fallo. Probando alternativa...
        powershell -command "Invoke-WebRequest -Uri '!URL2!' -OutFile '%zipfile%'" 2>nul
    )
)

if not exist "%zipfile%" (
    color 0C
    echo ERROR: No se pudo descargar %folder%.
    pause
    goto :eof
)

echo Descomprimiendo...
powershell -command "Expand-Archive -Force '%zipfile%' '%JUEGO%'"

del /f /q "%zipfile%"

color 0A
echo %folder% actualizado correctamente !!
pause
goto :eof


REM ============================================================
REM ==================== VALIDATOR ==============================
REM ============================================================

:VALIDATOR
color 0B
echo Verificando conexion...
ping -n 1 github.com >nul || (color 0C & echo ERROR: Sin conexion & pause & goto :eof)

set zipfile=%DOWNLOADS%\W3Updater\DarkValidator.zip
set extractfolder=%DOWNLOADS%
set url=https://github.com/elcoprofago/Warlords-updater/releases/download/Actualizador/DarkValidator.zip

echo Descargando Validator...
powershell -command "Invoke-WebRequest -Uri '%url%' -OutFile '%zipfile%'"

echo Descomprimiendo...
powershell -command "Expand-Archive -Force '%zipfile%' '%extractfolder%'"

del /f /q "%zipfile%"

color 0A
echo VALIDATOR actualizado !!
pause
goto MENU


REM ============================================================
REM ==================== PARCHES ================================
REM ============================================================
REM PARCHES.txt (asset de la release "Actualizador"), una linea por parche:
REM   ID|VERSION|SHA256 del zip|URL del zip|DESCRIPCION
REM La version instalada de cada parche queda en %JUEGO%\PARCHES\<ID>.txt

:PARCHES
color 0B
echo Verificando conexion...
ping -n 1 github.com >nul || (color 0C & echo ERROR: Sin conexion & pause & goto MENU)

set "manifest=%DOWNLOADS%\W3Updater\PARCHES.txt"
if exist "%manifest%" del /f /q "%manifest%"
echo Descargando lista de parches...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Headers @{'Cache-Control'='no-cache'} -Uri '%PARCHES_URL%' -OutFile '%manifest%'" 2>nul
if not exist "%manifest%" (
    color 0C
    echo ERROR: No se pudo descargar la lista de parches.
    pause
    goto MENU
)

:PARCHES_MENU
cls
color 0E
echo =================================
echo PARCHES DISPONIBLES
echo =================================
set n=0
for /f "usebackq eol=# tokens=1-5 delims=|" %%a in ("%manifest%") do (
    set /a n+=1
    set "P_ID_!n!=%%a"
    set "P_VER_!n!=%%b"
    set "P_SHA_!n!=%%c"
    set "P_URL_!n!=%%d"
    set "estado=no instalado"
    if exist "%JUEGO%\PARCHES\%%a.txt" (
        set "inst="
        set /p inst=<"%JUEGO%\PARCHES\%%a.txt"
        if "!inst!"=="%%b" (set "estado=instalado") else (set "estado=instalada la v!inst!, hay version nueva")
    )
    echo !n!^) %%e  [v%%b - !estado!]
)
if %n%==0 (
    echo No hay parches publicados todavia.
    pause
    goto MENU
)
echo 0) VOLVER
set "sel="
set /p sel="Parche a instalar: "
if "%sel%"=="0" goto MENU
set "valido="
for /l %%i in (1,1,%n%) do if "%sel%"=="%%i" set valido=1
if not defined valido (
    color 0C
    echo Opcion invalida.
    pause
    goto PARCHES_MENU
)
call :INSTALAR_PARCHE %sel%
pause
goto PARCHES_MENU

:INSTALAR_PARCHE
set "id=!P_ID_%1!"
set "ver=!P_VER_%1!"
set "sha=!P_SHA_%1!"
set "url=!P_URL_%1!"
set "zipfile=%DOWNLOADS%\W3Updater\PARCHE-!id!.zip"

color 0B
echo --------------------------------
echo Descargando parche !id! v!ver!...
if exist "!zipfile!" del /f /q "!zipfile!"
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Headers @{'Cache-Control'='no-cache'} -Uri '!url!' -OutFile '!zipfile!'" 2>nul
if not exist "!zipfile!" (
    color 0C
    echo ERROR: No se pudo descargar el parche.
    goto :eof
)

REM El zip tiene que ser exactamente el publicado: si no coincide no se toca el juego
set "got="
for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '!zipfile!').Hash"`) do set "got=%%H"
if /I not "!got!"=="!sha!" (
    color 0C
    echo ERROR: El archivo descargado no coincide con el publicado. No se instala.
    del /f /q "!zipfile!"
    goto :eof
)

echo Instalando en %JUEGO%...
powershell -NoProfile -Command "try { Expand-Archive -Force -LiteralPath '!zipfile!' -DestinationPath '%JUEGO%' -ErrorAction Stop } catch { Write-Host $_; exit 1 }"
if errorlevel 1 (
    color 0C
    echo ERROR: No se pudo descomprimir el parche.
    del /f /q "!zipfile!"
    goto :eof
)
del /f /q "!zipfile!"

if not exist "%JUEGO%\PARCHES" mkdir "%JUEGO%\PARCHES"
>"%JUEGO%\PARCHES\!id!.txt" echo !ver!
color 0A
echo Parche !id! v!ver! instalado correctamente.
goto :eof


:EXIT
echo Saliendo...
pause
exit
