<#
Deja la PC lista para jugar Warlords III Darklords Rising por Radmin VPN:

  1. Radmin VPN: si no esta instalado, ofrece bajarlo de la pagina oficial (www.radmin-vpn.com) e
     instalarlo. El enlace se lee de la pagina cada vez (lleva la version en el nombre y cambia con cada
     version de Radmin) y el instalador solo se abre si tiene firma digital valida de Famatech Corp.
  2. Firewall de Windows Defender (Windows 10 u 11): para cada programa del juego y de
     C:\Warlords3\HERRAMIENTAS deja una sola regla de ENTRADA que lo permite en el perfil Privada, que es
     lo mismo que marcar solo la columna "Privada" en "Permitir que una aplicacion se comunique a traves
     del Firewall de Windows".
  3. Pasa la red "Radmin VPN" a Privada (ver abajo por que hace falta).

  .\tools\configurar-firewall.ps1                    aplica los cambios (se eleva solo, pide permisos)
  .\tools\configurar-firewall.ps1 -Simular           muestra lo que haria, sin tocar nada
  .\tools\configurar-firewall.ps1 -DejarRedComoEsta  no cambia la categoria de la red Radmin VPN
  .\tools\configurar-firewall.ps1 -Pausa             espera ENTER antes de cerrar (lo usa el actualizador)

Antes de crear cada regla borra las que hoy apunten a ese mismo .exe, en cualquier perfil y direccion:

  - las que deja el aviso "Alerta de seguridad de Windows" la primera vez que se abre el programa
    (aparecen con el nombre del juego y permiten o bloquean Privada y Publica),
  - las que agrega el propio Radmin VPN en su grupo "Radmin VPN" para el juego, que lo habilitan
    tambien en Publica.

Con una sola de esas reglas que permita Publica el programa quedaria habilitado en las redes publicas y
el resultado no seria "solo privada", por eso se borran todas y se crea una sola, propia, en el grupo
"Warlords 3" (asi se ven juntas en wf.msc). Las reglas del servicio de Radmin VPN (RvControlSvc.exe) no
se tocan: son de Radmin y las necesita para conectarse.

El juego juega en red por DirectPlay (DPLAYX.dll): quien crea la partida recibe las conexiones en
dplaysvr.exe (puerto 47624) y despues en el juego (puertos 2300-2400). Por eso dplaysvr.exe va en la
lista junto con Darklord.exe y DarklordAV.exe.

Por que la red Radmin VPN tiene que ser Privada: una regla de perfil Privada solo se aplica al trafico
que llega por una red que Windows tiene clasificada como Privada, y Windows deja la red de Radmin VPN
como Publica. Si queda Publica, despues de este script el juego NO recibe conexiones por Radmin VPN
(antes andaba gracias a la regla de Radmin que se borra). Por eso el script la pasa a Privada salvo que
se use -DejarRedComoEsta, y en ese caso lo avisa. Si la red Radmin VPN no aparece (Radmin cerrado o sin
unirse a ninguna red), lo avisa: hay que abrir Radmin, unirse a la red y volver a correrlo.

Requiere ser administrador: si no lo estas, el script se vuelve a abrir solo (UAC) y sigue ahi.
Codigo de salida: 0 todo bien, 1 algo quedo mal (se explica en pantalla).

Para deshacer las reglas: en una consola de administrador,
  Remove-NetFirewallRule -Group 'Warlords 3'
#>
param(
    [string]$Juego = 'C:\Warlords3',
    [switch]$Simular,
    [switch]$DejarRedComoEsta,
    [switch]$Pausa,
    [switch]$RedPrivada   # de versiones anteriores: hoy pasar la red a Privada es lo normal; no hace nada
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Grupo = 'Warlords 3'
$PaginaRadmin = 'https://www.radmin-vpn.com/'

function Salir([int]$codigo) {
    if ($Pausa) { Write-Host ''; Read-Host 'ENTER para cerrar' | Out-Null }
    exit $codigo
}
function Falla($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; Salir 1 }
function Aviso($msg) { Write-Host "AVISO: $msg" -ForegroundColor Yellow }
function Titulo($msg) { Write-Host ''; Write-Host $msg -ForegroundColor Cyan }

# Ruta normalizada para comparar: las reglas pueden guardar %SystemRoot% y similares, y en
# minusculas o mayusculas.
function Normal($ruta) { [Environment]::ExpandEnvironmentVariables($ruta).TrimEnd('\').ToLowerInvariant() }

# Reglas (de cualquier perfil y direccion) cuyo programa sea este .exe. En el filtro de aplicacion
# el InstanceID es el Name de la regla.
function ReglasDe($exe) {
    $buscada = Normal $exe
    Get-NetFirewallApplicationFilter -PolicyStore ActiveStore |
        Where-Object { $_.Program -and (Normal $_.Program) -eq $buscada } |
        ForEach-Object { Get-NetFirewallRule -Name $_.InstanceID -ErrorAction SilentlyContinue }
}

# Donde esta instalado Radmin VPN: lo dice su desinstalador en el registro; si no, la ruta de siempre.
function CarpetaRadmin {
    $claves = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
              'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
    $r = Get-ItemProperty $claves -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -like 'Radmin VPN*' -and $_.InstallLocation } | Select-Object -First 1
    $carpetas = @()
    if ($r) { $carpetas += $r.InstallLocation }
    $carpetas += 'C:\Program Files (x86)\Radmin VPN', 'C:\Program Files\Radmin VPN'
    foreach ($c in $carpetas) { if (Test-Path -LiteralPath (Join-Path $c 'RvControlSvc.exe')) { return $c } }
    return $null
}

# ---------------------------------------------------------------- administrador
$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $esAdmin -and -not $Simular) {
    $argumentos = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Juego', "`"$Juego`"", '-Pausa')
    if ($DejarRedComoEsta) { $argumentos += '-DejarRedComoEsta' }
    Write-Host 'Hace falta ser administrador: se vuelve a abrir pidiendo permisos...' -ForegroundColor Yellow
    try {
        $p = Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -PassThru -ArgumentList $argumentos
        exit $p.ExitCode
    }
    catch { Falla 'no se pudieron obtener permisos de administrador (se cancelo el pedido de UAC?)' }
}

if ($Simular) { Write-Host 'SIMULACION: no se cambia nada.' -ForegroundColor Cyan }
$fallos = 0

# ---------------------------------------------------------------- Radmin VPN instalado
Titulo 'Radmin VPN'
$radminDir = CarpetaRadmin
if ($radminDir) {
    $v = (Get-Item -LiteralPath (Join-Path $radminDir 'RvControlSvc.exe')).VersionInfo.FileVersion
    Write-Host "  instalado en $radminDir (version $v)" -ForegroundColor Green
}
elseif ($Simular) { Aviso 'Radmin VPN no esta instalado: se ofreceria bajarlo e instalarlo.' }
else {
    Aviso 'Radmin VPN no esta instalado en esta PC. Hace falta para jugar en red con los demas.'
    $r = Read-Host '  Bajarlo de la pagina oficial e instalarlo ahora? (S/N)'
    if ($r -match '^\s*(s|si|y|yes)\s*$') {
        $instalador = $null
        try {
            Write-Host "  buscando la version actual en $PaginaRadmin ..."
            $pagina = (Invoke-WebRequest -UseBasicParsing -Uri $PaginaRadmin -TimeoutSec 30).Content
            $m = [regex]::Match($pagina, 'https://download\.radmin-vpn\.com/download/files/Radmin_VPN_[0-9.]+\.exe')
            if (-not $m.Success) { throw 'la pagina no tiene el enlace de descarga donde se esperaba' }
            $instalador = Join-Path $env:TEMP (Split-Path -Leaf $m.Value)
            Write-Host "  bajando $($m.Value) (unos 55 MB)..."
            Invoke-WebRequest -UseBasicParsing -Uri $m.Value -OutFile $instalador -TimeoutSec 600
            $firma = Get-AuthenticodeSignature -LiteralPath $instalador
            if ($firma.Status -ne 'Valid' -or $firma.SignerCertificate.Subject -notmatch 'O=Famatech Corp\.') {
                Remove-Item -Force -LiteralPath $instalador -ErrorAction SilentlyContinue
                throw "el archivo bajado no tiene la firma de Famatech (estado: $($firma.Status)); no se abre"
            }
            Write-Host '  firma de Famatech Corp. verificada. Se abre el instalador: segui sus pasos.' -ForegroundColor Green
            Start-Process -FilePath $instalador -Wait
            Remove-Item -Force -LiteralPath $instalador -ErrorAction SilentlyContinue
        }
        catch {
            Aviso "no se pudo instalar automaticamente: $($_.Exception.Message)"
            Write-Host "  Bajalo a mano de $PaginaRadmin (boton de descarga), instalalo y volve a correr esto."
            try { Start-Process $PaginaRadmin } catch { }
        }
        $radminDir = CarpetaRadmin
        if ($radminDir) { Write-Host "  Radmin VPN instalado en $radminDir" -ForegroundColor Green }
        else { Aviso 'Radmin VPN sigue sin estar instalado.'; $fallos++ }
    }
    else {
        Write-Host "  Cuando quieras: $PaginaRadmin (boton de descarga). El firewall se configura igual."
        $fallos++
    }
}

# ---------------------------------------------------------------- la lista
# Etiqueta = como se muestra la regla; Ruta = el .exe exacto que se habilita.
$Programas = @(
    @{ Etiqueta = 'Darklords Rising';         Ruta = Join-Path $Juego 'Darklord.exe' }
    @{ Etiqueta = 'Darklords Rising AV';      Ruta = Join-Path $Juego 'DarklordAV.exe' }
    @{ Etiqueta = 'DirectPlay';               Ruta = Join-Path ([Environment]::GetFolderPath('SystemX86')) 'dplaysvr.exe' }
    @{ Etiqueta = 'Sorteo';                   Ruta = Join-Path $Juego 'HERRAMIENTAS\sorteo.exe' }
    @{ Etiqueta = 'Comparador';               Ruta = Join-Path $Juego 'HERRAMIENTAS\DarkCompare.exe' }
    @{ Etiqueta = 'Votacion';                 Ruta = Join-Path $Juego 'HERRAMIENTAS\votacion.exe' }
    @{ Etiqueta = 'Editor bandos';            Ruta = Join-Path $Juego 'HERRAMIENTAS\EditorPGS.exe' }
    @{ Etiqueta = 'Validator';                Ruta = Join-Path $Juego 'HERRAMIENTAS\DarklordsValidator.exe' }
)

Titulo "Programas (juego en $Juego)"
$faltan = @($Programas | Where-Object { -not (Test-Path -LiteralPath $_.Ruta) })
$objetivo = @($Programas | Where-Object { Test-Path -LiteralPath $_.Ruta })
foreach ($p in $faltan) {
    if ($p.Etiqueta -eq 'DirectPlay') {
        Aviso "no esta $($p.Ruta): falta DirectPlay de Windows, sin el cual el juego no juega en red."
        Write-Host '  Se activa en "Activar o desactivar las caracteristicas de Windows" > Componentes heredados > DirectPlay.'
        $fallos++
    }
    else { Write-Host "  (no instalado, se saltea: $($p.Ruta))" -ForegroundColor DarkGray }
}
if (-not $objetivo) { Falla "no existe ninguno de los programas de la lista: el juego esta en $Juego?" }

# ---------------------------------------------------------------- borrar y crear, programa por programa
$creadas = 0
foreach ($p in $objetivo) {
    Titulo "=== $($p.Etiqueta): $($p.Ruta)"

    $previas = @(ReglasDe $p.Ruta)
    if (-not $previas) { Write-Host '  (no tenia reglas)' }
    foreach ($r in $previas) {
        $txt = "`"{0}`" ({1}, {2}, perfil {3}, habilitada {4})" -f $r.DisplayName, $r.Direction, $r.Action, $r.Profile, $r.Enabled
        if ($Simular) { Write-Host "  [simulado] borrar $txt" }
        else {
            try {
                Remove-NetFirewallRule -Name $r.Name -ErrorAction Stop
                Write-Host "  borrada $txt"
            }
            catch {
                # p.ej. una regla que viene de una directiva de grupo: no se puede borrar desde aca
                Aviso "no se pudo borrar $txt : $($_.Exception.Message)"
                $fallos++
            }
        }
    }

    $nombre = "Warlords 3 - $($p.Etiqueta) (privada)"
    $descripcion = "Regla de configurar-firewall.ps1: $($p.Ruta) habilitado solo en la red privada."
    if ($Simular) { Write-Host "  [simulado] crear `"$nombre`": entrada, permitir, perfil Privada" }
    else {
        try {
            New-NetFirewallRule -DisplayName $nombre -Group $Grupo -Description $descripcion `
                -Direction Inbound -Action Allow -Profile Private -Program $p.Ruta -Enabled True -ErrorAction Stop | Out-Null
            Write-Host "  creada `"$nombre`": entrada, permitir, perfil Privada"
            $creadas++
        }
        catch {
            Aviso "no se pudo crear `"$nombre`": $($_.Exception.Message)"
            $fallos++
        }
    }
}

# ---------------------------------------------------------------- verificar leyendo de nuevo
$malas = 0
if (-not $Simular) {
    Titulo 'Verificacion (leido otra vez del firewall):'
    foreach ($p in $objetivo) {
        $r = @(ReglasDe $p.Ruta)
        $ok = $r.Count -eq 1 -and [string]$r[0].Enabled -eq 'True' -and [string]$r[0].Action -eq 'Allow' -and
              [string]$r[0].Direction -eq 'Inbound' -and [string]$r[0].Profile -eq 'Private' -and [string]$r[0].Group -eq $Grupo
        if ($ok) { Write-Host "  OK  $($p.Etiqueta)" -ForegroundColor Green }
        else {
            $malas++
            Aviso "$($p.Etiqueta) quedo con $($r.Count) regla(s), no es una sola de entrada, permitir, perfil Privada:"
            foreach ($x in $r) { Write-Host ("      `"{0}`" {1} {2} perfil {3} habilitada {4}" -f $x.DisplayName, $x.Direction, $x.Action, $x.Profile, $x.Enabled) }
        }
    }
}

# ---------------------------------------------------------------- la red Radmin VPN
Titulo 'Redes que ve Windows (adaptador, red, categoria):'
$perfiles = @(Get-NetConnectionProfile)
foreach ($n in $perfiles) { Write-Host ("  {0,-24} {1,-24} {2}" -f $n.InterfaceAlias, $n.Name, $n.NetworkCategory) }

$radmin = @($perfiles | Where-Object { $_.InterfaceAlias -like '*Radmin VPN*' })
if (-not $radmin) {
    Aviso 'no veo la red "Radmin VPN": abri Radmin VPN, unite a la red de la partida y volve a correr esto.'
    $fallos++
}
elseif ([string]$radmin[0].NetworkCategory -eq 'Private') {
    Write-Host '  Radmin VPN esta en Privada: las reglas se aplican al juego por Radmin VPN.' -ForegroundColor Green
}
elseif ($DejarRedComoEsta) {
    Aviso "Radmin VPN esta en $($radmin[0].NetworkCategory) y se dejo asi (-DejarRedComoEsta): el juego NO va a recibir conexiones por Radmin VPN."
    $fallos++
}
elseif ($Simular) { Write-Host "  [simulado] pasar la red Radmin VPN ($($radmin[0].NetworkCategory)) a Privada" }
else {
    try {
        Set-NetConnectionProfile -InterfaceAlias $radmin[0].InterfaceAlias -NetworkCategory Private -ErrorAction Stop
        $ahora = [string](Get-NetConnectionProfile -InterfaceAlias $radmin[0].InterfaceAlias).NetworkCategory
        if ($ahora -ne 'Private') { throw "sigue en $ahora" }
        Write-Host '  Red Radmin VPN pasada a Privada (verificado).' -ForegroundColor Green
    }
    catch { Aviso "no se pudo pasar Radmin VPN a Privada: $($_.Exception.Message)"; $fallos++ }
}

# ---------------------------------------------------------------- resumen
Write-Host ''
if ($Simular) { Write-Host "Simulacion terminada: no se cambio nada ($($objetivo.Count) programas)." -ForegroundColor Cyan; Salir 0 }
if ($fallos -or $malas) {
    Write-Host "Termino con problemas: $fallos aviso(s) y $malas programa(s) sin verificar (ver arriba)." -ForegroundColor Red
    Salir 1
}
Write-Host "Listo: $creadas programa(s) habilitados solo en la red privada (grupo `"$Grupo`") y Radmin VPN en Privada." -ForegroundColor Green
Salir 0
