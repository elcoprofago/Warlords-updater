@echo off
rem Diagnostico de video para Warlords 3. Junta datos de la PC en un .txt en el Escritorio.
rem Uso: doble clic. No cambia nada en la PC: solo lee.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f='%~f0'; $c=(Get-Content -LiteralPath $f -Raw) -split '#PS#'; Invoke-Expression $c[2]"
pause
exit /b
#PS#
$VERSION = '1.0.0.0'
$sal = New-Object System.Collections.Generic.List[string]
function L($t) { $sal.Add([string]$t) }
L "DIAGNOSTICO DE VIDEO WARLORDS - VERSION $VERSION"
L ("Fecha: " + (Get-Date -Format 'yyyy-MM-dd HH:mm'))
L ("Equipo: " + $env:COMPUTERNAME)
L ""
$cv = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
L ("Windows: build " + $cv.CurrentBuildNumber + " (" + $cv.DisplayVersion + ")")
$ram = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
L ("RAM: {0:N1} GB" -f ($ram/1GB))
L ""
L "== PLACAS DE VIDEO =="
foreach ($g in Get-CimInstance Win32_VideoController) {
  L ("- " + $g.Name)
  L ("  Driver: " + $g.DriverVersion + "  fecha " + $g.DriverDate)
  L ("  Modo actual: " + $g.CurrentHorizontalResolution + "x" + $g.CurrentVerticalResolution + ", " + $g.CurrentBitsPerPixel + " bits, " + $g.CurrentRefreshRate + " Hz")
}
L ""
L "== PANTALLAS Y ESCALA =="
Add-Type -AssemblyName System.Windows.Forms
foreach ($s in [System.Windows.Forms.Screen]::AllScreens) { L ("- " + $s.DeviceName + " " + $s.Bounds.Width + "x" + $s.Bounds.Height + $(if ($s.Primary) {' (principal)'} else {''})) }
$dpi = (Get-ItemProperty 'HKCU:\Control Panel\Desktop\WindowMetrics' -ErrorAction SilentlyContinue).AppliedDPI
if ($dpi) { L ("Escala de Windows: " + [math]::Round($dpi/96*100) + " %  (AppliedDPI " + $dpi + ")") } else { L "Escala de Windows: no se pudo leer" }
L ""
L "== CARPETAS DEL JUEGO =="
$carpetas = @()
foreach ($u in Get-PSDrive -PSProvider FileSystem) {
  foreach ($n in 'Warlords','Warlords3','Warlords 3') {
    $p = Join-Path $u.Root $n
    if (Test-Path (Join-Path $p 'Darklord.exe')) { $carpetas += $p }
  }
}
if (-not $carpetas) { L "No se encontro Darklord.exe en X:\Warlords ni X:\Warlords3" }
foreach ($p in $carpetas) {
  L ("--- " + $p)
  foreach ($a in 'Darklord.exe','DarklordAV.exe','ddraw.dll','winmm.dll','dxcfg.exe') {
    $r = Join-Path $p $a
    if (Test-Path $r) {
      $i = Get-Item $r
      $h = (Get-FileHash $r -Algorithm MD5).Hash.Substring(0,12)
      L ("  " + $a + "  " + $i.Length + " bytes  " + $i.LastWriteTime.ToString('yyyy-MM-dd') + "  md5 " + $h + "  ver " + $i.VersionInfo.FileVersion)
    } else { L ("  " + $a + "  NO ESTA") }
  }
  foreach ($a in 'SCREEN.INI','VIDEO.INI','dxcfg.ini','ddraw.ini') {
    $r = Join-Path $p $a
    if (Test-Path $r) { L ("  [" + $a + "]"); foreach ($x in Get-Content $r) { L ("    " + $x) } }
  }
}
L ""
L "== MODOS DE COMPATIBILIDAD DEL JUEGO =="
$hay = $false
foreach ($k in 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers','HKLM:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers') {
  $it = Get-ItemProperty $k -ErrorAction SilentlyContinue
  if ($it) { foreach ($pr in $it.PSObject.Properties) { if ($pr.Name -match 'warlord|darklord|war3') { L ("- " + $pr.Name + " = " + $pr.Value); $hay = $true } } }
}
if (-not $hay) { L "Ninguno" }
$dest = Join-Path ([Environment]::GetFolderPath('Desktop')) ("diagnostico-video-" + $env:COMPUTERNAME + ".txt")
$sal | Set-Content -LiteralPath $dest -Encoding UTF8
$sal | ForEach-Object { Write-Host $_ }
Write-Host ""
Write-Host ("Listo. El informe quedo en: " + $dest) -ForegroundColor Green
Write-Host "Manda ese archivo a quien te pidio el diagnostico."
