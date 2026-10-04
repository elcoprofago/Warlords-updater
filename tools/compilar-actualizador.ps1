<#
Compila source\Actualizador.bat a Actualizador-v.<VERSION>.exe (+ .exe.zip) en la raiz del repo, con
Bat To Exe Converter 4.2 por linea de comandos, y opcionalmente lo sube a la release "Ejecutable".

  .\tools\compilar-actualizador.ps1              # compila y prueba
  .\tools\compilar-actualizador.ps1 -Publicar    # ademas sube exe y zip a la release Ejecutable

VERSION sale de la linea "V. x.x.x.x" de source\banner.txt.

La linea de comandos del conversor IGNORA la cabecera ::[Bat To Exe Converter] del .bat: todo va
por parametros. /extractdir 0 extrae los .txt embebidos junto al exe (como el 1.0.0.7, que el .bat
necesita: lee banner.txt y los *_url.txt de la carpeta actual); con 2 (u otros) no aparecen ahi.

Prueba: corre el exe en una carpeta temporal y exige que los 7 .txt extraidos sean identicos a source\.
-Publicar exige main limpio y subido, que el exe no este ya en la release, y verifica bajando de nuevo.
#>
param(
    [switch]$Publicar,
    [string]$Convertidor = 'F:\PARA GRABAR\Programas\Programacion\bat-to-exe-converter-x64-4.2-installer.exe'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Repo = 'elcoprofago/Warlords-updater'
$Release = 'Ejecutable'
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Falla($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }
function Sha256($path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash }

$m = Select-String -Path 'source\banner.txt' -Pattern 'V\. (\d+\.\d+\.\d+\.\d+)'
if (-not $m) { Falla 'no encuentro "V. x.x.x.x" en source\banner.txt' }
$version = $m.Matches[0].Groups[1].Value
$nombre = "Actualizador-v.$version.exe"
$exe = Join-Path $raiz $nombre
$zip = "$exe.zip"
if (-not (Test-Path -LiteralPath $Convertidor)) { Falla "no esta el conversor en $Convertidor (usar -Convertidor)" }
$txts = @(Get-ChildItem 'source\*.txt')

# ---------------------------------------------------------------- compilar
if (Test-Path -LiteralPath $exe) { Remove-Item -Force -LiteralPath $exe }
$a = @('/bat', "`"$raiz\source\Actualizador.bat`"", '/exe', "`"$exe`"",
    '/icon', "`"$raiz\tools\actualizador.ico`"", '/fileversion', $version, '/extractdir', '0')
foreach ($t in $txts) { $a += '/include'; $a += "`"$($t.FullName)`"" }
$p = Start-Process $Convertidor -ArgumentList $a -PassThru
if (-not $p.WaitForExit(60000)) { Falla 'el conversor no termino en 60 s' }
if ($p.ExitCode) { Falla "el conversor termino con codigo $($p.ExitCode)" }
if (-not (Test-Path -LiteralPath $exe)) { Falla "el conversor no genero $nombre" }
$fv = (Get-Item -LiteralPath $exe).VersionInfo.FileVersion
if ($fv -ne $version) { Falla "FileVersion del exe es '$fv', se esperaba $version" }
Write-Host "Compilado $nombre (FileVersion $fv)"

# ---------------------------------------------------------------- probar la extraccion
$prueba = Join-Path ([IO.Path]::GetTempPath()) ("w3upd-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $prueba | Out-Null
Copy-Item -LiteralPath $exe "$prueba\A.exe"
$vacio = "$prueba.in"; [IO.File]::WriteAllText($vacio, '')
$p = Start-Process "$prueba\A.exe" -WorkingDirectory $prueba -RedirectStandardInput $vacio `
    -RedirectStandardOutput "$prueba.out" -NoNewWindow -PassThru
Start-Sleep -Seconds 4
Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $p.Id } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
foreach ($t in $txts) {
    $e = Join-Path $prueba $t.Name
    if (-not (Test-Path -LiteralPath $e)) { Falla "el exe no extrajo $($t.Name) junto a si mismo (probado en $prueba)" }
    if ((Sha256 $e) -ne (Sha256 $t.FullName)) { Falla "$($t.Name) extraido difiere de source\ (probado en $prueba)" }
}
if (-not (Select-String -Path "$prueba.out" -SimpleMatch "V. $version" -Quiet)) { Falla "el exe no mostro el banner V. $version" }
Write-Host "  probado: extrae los $($txts.Count) .txt identicos a source\ y muestra V. $version"
Start-Sleep -Seconds 1
Remove-Item -Recurse -Force -LiteralPath $prueba, $vacio, "$prueba.out" -ErrorAction SilentlyContinue

# ---------------------------------------------------------------- zip (solo el exe, como los anteriores)
if (Test-Path -LiteralPath $zip) { Remove-Item -Force -LiteralPath $zip }
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$z = [IO.Compression.ZipFile]::Open($zip, 'Create')
try { [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($z, $exe, $nombre) | Out-Null }
finally { $z.Dispose() }
Write-Host "  $nombre        SHA-256 $(Sha256 $exe)"
Write-Host "  $nombre.zip    SHA-256 $(Sha256 $zip)"

if (-not $Publicar) { Write-Host 'Sin -Publicar: no se sube nada.' -ForegroundColor Cyan; exit 0 }

# ---------------------------------------------------------------- publicar
if ((git rev-parse --abbrev-ref HEAD) -ne 'main') { Falla 'no estas en main' }
if (git status --porcelain) { Falla 'hay cambios sin commitear' }
git fetch -q origin
if ([int](git rev-list --count origin/main..HEAD)) { Falla 'el commit actual no esta subido a GitHub (git push)' }
$subidos = @(gh release view $Release -R $Repo --json assets --jq '.assets[].name')
if ($LASTEXITCODE) { Falla "no se pudo leer la release $Release" }
if ($subidos -contains $nombre) { Falla "$nombre ya esta en la release ${Release}: subi la version en source\banner.txt" }

gh release upload $Release $exe $zip -R $Repo
if ($LASTEXITCODE) { Falla 'no se pudo subir' }
$tmp = Join-Path $raiz 'dist\verificacion'
New-Item -ItemType Directory -Force $tmp | Out-Null
foreach ($f in @($exe, $zip)) {
    $n = Split-Path -Leaf $f
    $bajado = Join-Path $tmp $n
    Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/$Repo/releases/download/$Release/$n" -OutFile $bajado
    if ((Sha256 $bajado) -ne (Sha256 $f)) { Falla "lo que se baja de la release ($n) no coincide con lo subido" }
    Write-Host "  verificado: $n"
}
Write-Host "Publicado $nombre en la release $Release" -ForegroundColor Green
