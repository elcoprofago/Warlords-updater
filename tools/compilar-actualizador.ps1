<#
Compila source\Actualizador (C#, .NET Framework 4.8, WinForms) a Actualizador-v.<VERSION>.exe (+ .exe.zip)
en la raiz del repo, y opcionalmente lo sube a la release "Ejecutable".

  .\tools\compilar-actualizador.ps1              # compila y prueba
  .\tools\compilar-actualizador.ps1 -Publicar    # ademas sube exe y zip a la release Ejecutable

VERSION sale de <Version> de source\Actualizador\Actualizador.csproj (tambien tienen que decir lo mismo
<FileVersion> y <AssemblyVersion>). Compila con el SDK de .NET (dotnet build), que esta en el Windows 10.
Las fuentes y los *_url.txt van embebidos: sale un solo exe que no deja nada junto a si.

Prueba: corre el exe con W3_ENTRADA=13 (elige SALIR) y W3_TRANSCRIPCION, y exige que termine solo, con
codigo 0, y que la pantalla muestre v<VERSION> y el menu de 13 opciones.
-Publicar exige main limpio y subido, que el exe no este ya en la release, y verifica bajando de nuevo.
#>
param([switch]$Publicar)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Repo = 'elcoprofago/Warlords-updater'
$Release = 'Ejecutable'
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Falla($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }
function Sha256($path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash }

$csproj = 'source\Actualizador\Actualizador.csproj'
[xml]$x = Get-Content -Raw -Encoding UTF8 $csproj
$pg = $x.Project.PropertyGroup | Where-Object { $_.Version } | Select-Object -First 1
if (-not $pg) { Falla "no encuentro <Version> en $csproj" }
$version = $pg.Version
if ($version -notmatch '^\d+\.\d+\.\d+\.\d+$') { Falla "<Version> '$version' no es x.x.x.x" }
if ($pg.FileVersion -ne $version -or $pg.AssemblyVersion -ne $version) {
    Falla "en $csproj Version ($version), FileVersion ($($pg.FileVersion)) y AssemblyVersion ($($pg.AssemblyVersion)) tienen que ser iguales"
}
$nombre = "Actualizador-v.$version.exe"
$exe = Join-Path $raiz $nombre
$zip = "$exe.zip"

# ---------------------------------------------------------------- compilar
$salida = Join-Path $raiz 'dist\compilado'
if (Test-Path -LiteralPath $salida) { Remove-Item -Recurse -Force -LiteralPath $salida }
dotnet build $csproj -c Release -o $salida --nologo -v q
if ($LASTEXITCODE) { Falla "dotnet build termino con codigo $LASTEXITCODE" }
$compilado = Join-Path $salida 'Actualizador.exe'
if (-not (Test-Path -LiteralPath $compilado)) { Falla "dotnet build no genero $compilado" }
if (Test-Path -LiteralPath $exe) { Remove-Item -Force -LiteralPath $exe }
Copy-Item -LiteralPath $compilado $exe
$fv = (Get-Item -LiteralPath $exe).VersionInfo.FileVersion
if ($fv -ne $version) { Falla "FileVersion del exe es '$fv', se esperaba $version" }
Write-Host "Compilado $nombre (FileVersion $fv)"

# ---------------------------------------------------------------- probar
$prueba = Join-Path ([IO.Path]::GetTempPath()) ("w3upd-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $prueba | Out-Null
Copy-Item -LiteralPath $exe "$prueba\A.exe"
$transcripcion = "$prueba\pantalla.txt"
$env:W3_ENTRADA = '13'
$env:W3_TRANSCRIPCION = $transcripcion
try {
    $p = Start-Process "$prueba\A.exe" -WorkingDirectory $prueba -PassThru
    if (-not $p.WaitForExit(30000)) { Stop-Process -Id $p.Id -Force; Falla "el exe no se cerro solo en 30 s (probado en $prueba)" }
} finally { Remove-Item Env:W3_ENTRADA, Env:W3_TRANSCRIPCION -ErrorAction SilentlyContinue }
if ($p.ExitCode) { Falla "el exe termino con codigo $($p.ExitCode) (probado en $prueba)" }
if (-not (Test-Path -LiteralPath $transcripcion)) { Falla "el exe no dejo la transcripcion (probado en $prueba)" }
$texto = Get-Content -Raw -Encoding UTF8 $transcripcion
if ($texto -notmatch [regex]::Escape("v$version")) { Falla "la pantalla no muestra v$version (ver $transcripcion)" }
foreach ($op in 'ACTUALIZAR TODO EL JUEGO', 'CREAR ACCESOS DIRECTOS AL ESCRITORIO', 'CONFIGURAR RADMIN-VPN', 'SALIR') {
    if ($texto -notmatch [regex]::Escape($op)) { Falla "el menu no muestra '$op' (ver $transcripcion)" }
}
$sobrantes = @(Get-ChildItem -LiteralPath $prueba | Where-Object { $_.Name -notin 'A.exe', 'pantalla.txt' })
if ($sobrantes) { Falla "el exe dejo archivos junto a si: $($sobrantes.Name -join ', ')" }
Write-Host "  probado: abre, muestra v$version y el menu de 13 opciones, cierra con 13 y no deja nada"
Remove-Item -Recurse -Force -LiteralPath $prueba -ErrorAction SilentlyContinue

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
if ($subidos -contains $nombre) { Falla "$nombre ya esta en la release ${Release}: subi la version en $csproj" }

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
