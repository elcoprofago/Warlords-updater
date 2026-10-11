<#
Configura en el Firewall de Windows Defender (Windows 10 u 11) los programas del juego y de
C:\Warlords3\HERRAMIENTAS como aplicaciones de la red privada: para cada .exe deja una sola regla
de ENTRADA que lo permite en el perfil Privada, que es lo mismo que marcar solo la columna "Privada"
en "Permitir que una aplicacion se comunique a traves del Firewall de Windows".

  .\tools\configurar-firewall.ps1              aplica los cambios (se eleva solo, pide permisos)
  .\tools\configurar-firewall.ps1 -Simular     muestra lo que haria, sin tocar el firewall
  .\tools\configurar-firewall.ps1 -RedPrivada  ademas pasa la red "Radmin VPN" a Privada

Antes de crear cada regla borra las que hoy apunten a ese mismo .exe, en cualquier perfil y
direccion. Hacen falta borrar:

  - las que deja el aviso "Windows Security Alert" la primera vez que se abre el programa
    (aparecen con el nombre del juego y permiten o bloquean Private y Public),
  - las que agrega el propio Radmin VPN en su grupo "Radmin VPN", que habilitan el .exe tambien en
    Publica.

Con una sola de esas reglas que permita Publica el programa quedaria habilitado en las redes
publicas y el resultado no seria "solo privada", por eso se borran todas y se crea una sola, propia,
en el grupo "Warlords 3" (asi se ven juntas en wf.msc).

No se crean reglas de salida: Windows ya permite la salida por defecto y el panel del firewall
tampoco las crea al habilitar una aplicacion.

Ojo con Radmin VPN: una regla de perfil Privada solo se aplica cuando el trafico va por una red que
Windows tiene clasificada como Privada, y el adaptador "Radmin VPN" suele quedar como Publica. El
script siempre informa como esta clasificada esa red; con -RedPrivada la pasa a Privada. Si queda
Publica, las reglas de los 7 programas no se aplican al juego por Radmin VPN (si al juego por la LAN
de casa, que normalmente ya es Privada).

Requiere ser administrador: si no lo estas, el script se vuelve a abrir solo (UAC) y sigue ahi.

Para deshacer todo: en una consola de administrador,
  Remove-NetFirewallRule -Group 'Warlords 3'
#>
param(
    [string]$Juego = 'C:\Warlords3',
    [switch]$Simular,
    [switch]$RedPrivada
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Grupo = 'Warlords 3'

function Falla($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }
function Aviso($msg) { Write-Host "AVISO: $msg" -ForegroundColor Yellow }

# Reglas (de cualquier perfil y direccion) cuyo programa sea este .exe. En el filtro de aplicacion
# el InstanceID es el Name de la regla.
function ReglasDe($exe) {
    Get-NetFirewallApplicationFilter -PolicyStore ActiveStore |
        Where-Object { $_.Program -and $_.Program -eq $exe } |
        ForEach-Object { Get-NetFirewallRule -Name $_.InstanceID -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------- administrador
$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $esAdmin -and -not $Simular) {
    # -NoExit para que la ventana elevada quede abierta y se pueda leer el resultado
    $argumentos = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-NoExit', '-File', $PSCommandPath)
    if ($Juego -ne 'C:\Warlords3') { $argumentos += @('-Juego', $Juego) }
    if ($RedPrivada) { $argumentos += '-RedPrivada' }
    Write-Host 'Hace falta ser administrador: se vuelve a abrir pidiendo permisos...' -ForegroundColor Yellow
    try {
        Start-Process -FilePath (Get-Process -Id $PID).Path -Verb RunAs -Wait -ArgumentList $argumentos
    }
    catch { Falla 'no se pudieron obtener permisos de administrador (se cancelo el pedido de UAC?)' }
    exit 0
}

# ---------------------------------------------------------------- la lista
# Etiqueta = como se muestra la regla; Ruta = el .exe exacto que se habilita.
$Programas = @(
    @{ Etiqueta = 'Radmin VPN';       Ruta = 'C:\Program Files (x86)\Radmin VPN\RvRvpnGui.exe' }
    @{ Etiqueta = 'Darklords Rising'; Ruta = Join-Path $Juego 'DarklordAV.exe' }
    @{ Etiqueta = 'Sorteo';           Ruta = Join-Path $Juego 'HERRAMIENTAS\sorteo.exe' }
    @{ Etiqueta = 'Comparador';       Ruta = Join-Path $Juego 'HERRAMIENTAS\DarkCompare.exe' }
    @{ Etiqueta = 'Votacion';         Ruta = Join-Path $Juego 'HERRAMIENTAS\votacion.exe' }
    @{ Etiqueta = 'Editor bandos';    Ruta = Join-Path $Juego 'HERRAMIENTAS\EditorPGS.exe' }
    @{ Etiqueta = 'Validator';        Ruta = Join-Path $Juego 'HERRAMIENTAS\DarklordsValidator.exe' }
)

if ($Simular) { Write-Host 'SIMULACION: no se cambia nada.' -ForegroundColor Cyan }

$objetivo = @()
$faltan = $Programas | Where-Object { -not (Test-Path -LiteralPath $_.Ruta) }
foreach ($p in $faltan) { Aviso "no existe $($p.Ruta): se saltea" }
if ($faltan.Count -eq $Programas.Count) { Falla 'no existe ninguno de los programas de la lista' }
$objetivo = @($Programas | Where-Object { Test-Path -LiteralPath $_.Ruta })

# ---------------------------------------------------------------- borrar y crear, programa por programa
$fallos = 0
$creadas = 0
foreach ($p in $objetivo) {
    Write-Host ''
    Write-Host "=== $($p.Etiqueta): $($p.Ruta)" -ForegroundColor Cyan

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
    $descripcion = "Regla de tools\configurar-firewall.ps1: $($p.Ruta) habilitado solo en la red privada."
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
    Write-Host ''
    Write-Host 'Verificacion (leido otra vez del firewall):' -ForegroundColor Cyan
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

# ---------------------------------------------------------------- como ve Windows las redes
Write-Host ''
Write-Host 'Redes que ve Windows (alias, red, categoria):' -ForegroundColor Cyan
$perfiles = @(Get-NetConnectionProfile)
foreach ($n in $perfiles) { Write-Host ("  {0,-24} {1,-24} {2}" -f $n.InterfaceAlias, $n.Name, $n.NetworkCategory) }

$radmin = @($perfiles | Where-Object { $_.InterfaceAlias -like '*Radmin VPN*' })
if (-not $radmin) {
    Aviso 'no veo la red "Radmin VPN" (abri Radmin VPN y volve a correr el script si queres controlarla)'
}
elseif ([string]$radmin[0].NetworkCategory -eq 'Private') {
    Write-Host '  Radmin VPN esta en Privada: si se le aplican las reglas de perfil Privada.' -ForegroundColor Green
}
else {
    Aviso "Radmin VPN esta en $($radmin[0].NetworkCategory): las reglas de perfil Privada NO se aplican al juego por Radmin VPN."
    if ($RedPrivada) {
        if ($Simular) { Write-Host '  [simulado] pasar la red Radmin VPN a Privada' }
        else {
            try {
                Set-NetConnectionProfile -InterfaceAlias $radmin[0].InterfaceAlias -NetworkCategory Private -ErrorAction Stop
                Write-Host '  Red Radmin VPN pasada a Privada.' -ForegroundColor Green
            }
            catch { Aviso "no se pudo pasar Radmin VPN a Privada: $($_.Exception.Message)"; $fallos++ }
        }
    }
    else { Write-Host '  Para que si se apliquen, volve a correrlo con -RedPrivada.' }
}

# ---------------------------------------------------------------- resumen
Write-Host ''
if ($Simular) { Write-Host "Simulacion terminada: no se cambio nada ($($objetivo.Count) programas)." -ForegroundColor Cyan; exit 0 }
if ($faltan.Count -or $fallos -or $malas) {
    Write-Host "Termino con problemas: $($faltan.Count) programa(s) no encontrados, $fallos regla(s) con error, $malas programa(s) sin verificar." -ForegroundColor Red
    exit 1
}
Write-Host "Listo: $creadas programa(s) habilitados solo en la red privada (grupo `"$Grupo`")." -ForegroundColor Green
