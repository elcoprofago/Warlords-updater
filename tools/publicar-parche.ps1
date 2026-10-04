<#
Publica un parche en la release "Actualizador" de GitHub, de donde lo baja la opcion 8 (PARCHES)
del actualizador.

  .\tools\publicar-parche.ps1 vista-aliada           # publica
  .\tools\publicar-parche.ps1 vista-aliada -Prueba   # hace todo menos subir y etiquetar

Pasos:
  1. Lee ID, VERSION, ARCHIVOS y DESCRIPCION de parches\parches.txt.
  2. Exige rama main, sin cambios sin commitear, el commit ya subido a GitHub y que no exista
     la etiqueta parche-<ID>-v<VERSION> (lo publicado tiene que corresponder a un commit).
  3. Recompila con parches\<ID>\build.py en dist\<ID> y exige que el resultado sea identico,
     archivo por archivo, a lo instalado en C:\Warlords3: se publica lo que se probo jugando.
  4. Arma dist\PARCHE-<ID>.zip y su SHA-256.
  5. Baja el PARCHES.txt publicado, exige que la VERSION sea mayor que la publicada y reescribe
     solo la linea de <ID> (las de los demas parches quedan como estaban).
  6. Sube el zip y despues PARCHES.txt, los vuelve a bajar y compara el SHA-256 con lo local.
  7. Etiqueta el commit como parche-<ID>-v<VERSION> y sube la etiqueta.

Con -Prueba, los controles del paso 2 y 3 avisan en vez de cortar, y nada sale de dist\.
Requiere: python con keystone y capstone (build.py), gh autenticado.
#>
param(
    [Parameter(Mandatory = $true)][string]$Id,
    [switch]$Prueba,
    [string]$Juego = 'C:\Warlords3'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Repo = 'elcoprofago/Warlords-updater'
$Release = 'Actualizador'
$BaseUrl = "https://github.com/$Repo/releases/download/$Release"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Falla($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }
function Control($msg) {
    if ($Prueba) { Write-Host "AVISO (-Prueba, publicando cortaria aca): $msg" -ForegroundColor Yellow }
    else { Falla $msg }
}
function Sha256($path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash }

# ---------------------------------------------------------------- 1. manifiesto del repo
$linea = Get-Content 'parches\parches.txt' | Where-Object { $_ -notmatch '^\s*(#|$)' } |
    Where-Object { ($_ -split '\|')[0] -eq $Id }
if (-not $linea) { Falla "'$Id' no esta en parches\parches.txt" }
if (@($linea).Count -gt 1) { Falla "'$Id' aparece mas de una vez en parches\parches.txt" }
$campos = $linea -split '\|'
if ($campos.Count -ne 4) { Falla "la linea de '$Id' no tiene 4 campos: $linea" }
$version, $archivos, $descripcion = $campos[1], ($campos[2] -split ';'), $campos[3]
if ($version -notmatch '^\d+\.\d+\.\d+\.\d+$') { Falla "VERSION '$version' no son cuatro numeros" }
if ($descripcion -match '!') { Falla "la DESCRIPCION no puede llevar ! (el .bat la pierde)" }
$etiqueta = "parche-$Id-v$version"
Write-Host "Parche $Id v$version : $($archivos -join ', ')"

# ---------------------------------------------------------------- 2. estado de git
$rama = git rev-parse --abbrev-ref HEAD
if ($rama -ne 'main') { Control "no estas en main (estas en $rama)" }
if (git status --porcelain) { Control 'hay cambios sin commitear' }
git fetch -q origin
if ($LASTEXITCODE) { Falla 'git fetch fallo' }
if ([int](git rev-list --count origin/main..HEAD)) { Control 'el commit actual no esta subido a GitHub (git push)' }
git rev-parse -q --verify "refs/tags/$etiqueta" | Out-Null
$etiquetaLocal = -not $LASTEXITCODE
$etiquetaRemota = [bool](git ls-remote --tags origin "refs/tags/$etiqueta")
if ($etiquetaLocal -or $etiquetaRemota) { Falla "la etiqueta $etiqueta ya existe: esta version ya se publico. Subi la VERSION." }

# ---------------------------------------------------------------- 3. compilar y comparar con lo probado
$build = Join-Path $raiz "dist\$Id"
if (Test-Path $build) { Remove-Item -Recurse -Force $build }
New-Item -ItemType Directory -Force $build | Out-Null
python "parches\$Id\build.py" $build
if ($LASTEXITCODE) { Falla "build.py termino con codigo $LASTEXITCODE" }

$generados = Get-ChildItem -Recurse -File $build | ForEach-Object { $_.FullName.Substring($build.Length + 1) }
foreach ($g in $generados) {
    if ($archivos -notcontains $g) { Falla "build.py genero $g, que no esta en ARCHIVOS de parches\parches.txt" }
}
foreach ($a in $archivos) {
    $nuevo = Join-Path $build $a
    $probado = Join-Path $Juego $a
    if (-not (Test-Path -LiteralPath $nuevo)) { Falla "build.py no genero $a" }
    if (-not (Test-Path -LiteralPath $probado)) { Control "no existe ${probado}: no hay version probada contra la cual comparar" }
    elseif ((Sha256 $nuevo) -ne (Sha256 $probado)) {
        Control "$a recompilado difiere de ${probado}: publicarias algo distinto de lo que probaste"
    }
    else { Write-Host "  $a identico a lo probado" }
}

# ---------------------------------------------------------------- 4. zip
$zip = Join-Path $raiz "dist\PARCHE-$Id.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$z = [IO.Compression.ZipFile]::Open($zip, 'Create')
try {
    foreach ($a in $archivos) {
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($z, (Join-Path $build $a), ($a -replace '\\', '/')) | Out-Null
    }
}
finally { $z.Dispose() }
$shaZip = Sha256 $zip
Write-Host "  $zip  SHA-256 $shaZip"

# ---------------------------------------------------------------- 5. PARCHES.txt publicado
# Por la API (gh), no por la URL publica: pedir la URL publica de un archivo que todavia no existe
# deja un 404 en la cache de GitHub que siguio sirviendose despues de subirlo (4/10/2026).
$publicado = @()
$subidos = @(gh release view $Release -R $Repo --json assets --jq '.assets[].name')
if ($LASTEXITCODE) { Falla "no se pudo leer la release $Release" }
if ($subidos -contains 'PARCHES.txt') {
    $previo = Join-Path $raiz 'dist\PARCHES.publicado.txt'
    gh release download $Release -p PARCHES.txt -O $previo --clobber -R $Repo
    if ($LASTEXITCODE) { Falla 'no se pudo bajar el PARCHES.txt publicado' }
    $publicado = @(Get-Content $previo | Where-Object { $_ -notmatch '^\s*(#|$)' })
}
else { Write-Host '  todavia no hay PARCHES.txt publicado: se crea' }
$anterior = $publicado | Where-Object { ($_ -split '\|')[0] -eq $Id }
if ($anterior) {
    $verPublicada = [version](($anterior -split '\|')[1])
    if ([version]$version -lt $verPublicada) { Falla "VERSION $version es menor que la publicada ($verPublicada)" }
    if ([version]$version -eq $verPublicada) {
        Write-Host "  la v$version ya figura publicada pero sin etiqueta: se completa esa publicacion" -ForegroundColor Yellow
    }
    else { Write-Host "  publicada: v$verPublicada" }
}
$nueva = "$Id|$version|$shaZip|$BaseUrl/PARCHE-$Id.zip|$descripcion"
$lineas = @($publicado | Where-Object { ($_ -split '\|')[0] -ne $Id }) + $nueva
$manifiesto = Join-Path $raiz 'dist\PARCHES.txt'
$cabecera = '# ID|VERSION|SHA256 del zip|URL del zip|DESCRIPCION  (generado por tools\publicar-parche.ps1)'
# ASCII sin BOM: el for /f del .bat leeria el BOM como parte del primer ID
[IO.File]::WriteAllText($manifiesto, (@($cabecera) + $lineas -join "`r`n") + "`r`n", [Text.Encoding]::ASCII)
Write-Host "  PARCHES.txt:"; Get-Content $manifiesto | ForEach-Object { Write-Host "    $_" }

if ($Prueba) { Write-Host "-Prueba: no se sube nada. Resultado en dist\" -ForegroundColor Cyan; exit 0 }

# ---------------------------------------------------------------- 6. subir y verificar
# Primero el zip: si se corta antes de subir PARCHES.txt, el .bat ve un SHA viejo y se niega a instalar.
gh release upload $Release $zip --clobber -R $Repo
if ($LASTEXITCODE) { Falla 'no se pudo subir el zip' }
gh release upload $Release $manifiesto --clobber -R $Repo
if ($LASTEXITCODE) { Falla 'no se pudo subir PARCHES.txt' }

$tmp = Join-Path $raiz 'dist\verificacion'
New-Item -ItemType Directory -Force $tmp | Out-Null
foreach ($par in @(@("PARCHE-$Id.zip", $zip), @('PARCHES.txt', $manifiesto))) {
    $bajado = Join-Path $tmp $par[0]
    $ok = $false
    # igual que lo pide el .bat (no-cache), para verificar lo que va a recibir el jugador
    for ($i = 1; $i -le 3 -and -not $ok; $i++) {
        try {
            Invoke-WebRequest -UseBasicParsing -Headers @{ 'Cache-Control' = 'no-cache' } -Uri "$BaseUrl/$($par[0])" -OutFile $bajado
            $ok = (Sha256 $bajado) -eq (Sha256 $par[1])
        }
        catch { Write-Host "  intento ${i}: $($_.Exception.Message)" }
        if (-not $ok) { Start-Sleep -Seconds 10 }
    }
    if (-not $ok) { Falla "lo que se baja de $BaseUrl/$($par[0]) no coincide con lo subido" }
    Write-Host "  verificado: $($par[0])"
}

# ---------------------------------------------------------------- 7. etiqueta
git tag -a $etiqueta -m "Parche $Id v$version publicado (zip SHA-256 $shaZip)"
if ($LASTEXITCODE) { Falla 'no se pudo crear la etiqueta' }
git push -q origin $etiqueta
if ($LASTEXITCODE) { Falla "no se pudo subir la etiqueta $etiqueta (crearla a mano: git push origin $etiqueta)" }
Write-Host "Publicado: $Id v$version" -ForegroundColor Green
