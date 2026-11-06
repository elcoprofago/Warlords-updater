<#
Arma el zip de una carpeta del juego desde C:\Warlords3 y lo publica en la release "Actualizador" de GitHub,
de donde lo bajan las opciones 1 a 5 del actualizador (Paquete en source\Actualizador\Actualizador.cs, que lo
descomprime encima de la carpeta del juego sin borrar nada).

  .\tools\publicar-paquete.ps1 ARMY             # opcion 1   (tambien SPELL = 2, HERO = 3, ESCEN = 4, ITEMS = 5)
  .\tools\publicar-paquete.ps1 ARMY -Prueba     # arma y compara; no sube nada (resultado en dist\)
  .\tools\publicar-paquete.ps1 ITEMS -Quitar 'ITEMS\Nuevos'   # acepta dejar afuera lo que el publicado trae

Pasos:
  1. Baja el zip publicado (el mas grande, ARMY, pesa unos 36 MB) y le saca el SHA-256 a cada archivo.
  2. Junta los archivos de C:\Warlords3\<CARPETA>, dejando afuera lo que publicar-full.ps1 tambien deja afuera:
     carpetas back (experimentos de quien arma el zip) y los .TMP/.lnk.
  3. Compara con lo publicado: que cambia, que se agrega y que dejaria de repartirse. Esto ultimo corta la
     publicacion salvo que se acepte con -Quitar (por carpeta o archivo) o este en una carpeta back: una PC
     que ya lo tiene lo conserva, pero una instalacion nueva no lo recibiria.
  4. Si no cambia nada, no publica.
  5. Arma dist\<ZIP>.zip, comprueba que tenga exactamente lo elegido, lo sube (reemplaza el anterior), lo
     vuelve a bajar y compara el SHA-256.

La opcion 6 (Warlords3_FULL.zip) va aparte, con tools\publicar-full.ps1.
Requiere: gh autenticado.
#>
param(
    [Parameter(Mandatory = $true)][ValidateSet('ARMY', 'SPELL', 'HERO', 'ESCEN', 'ITEMS')][string]$Carpeta,
    [switch]$Prueba,
    [string[]]$Quitar = @(),
    [string]$Juego = 'C:\Warlords3'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Repo = 'elcoprofago/Warlords-updater'
$Release = 'Actualizador'
$Nombre = "$Carpeta.zip"
$Url = "https://github.com/$Repo/releases/download/$Release/$Nombre"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Falla($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }
function Sha256($path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash }
function Fresca($u) { "${u}?t=$([guid]::NewGuid().ToString('N'))" }   # esquiva la cache de GitHub (ver publicar-parche.ps1)
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$sha256 = [Security.Cryptography.SHA256]::Create()

# ---------------------------------------------------------------- 1. lo publicado
$dist = Join-Path $raiz 'dist'
$verif = Join-Path $dist 'verificacion'
New-Item -ItemType Directory -Force $verif | Out-Null
$pubZip = Join-Path $verif "publicado-$Nombre"
Invoke-WebRequest -UseBasicParsing -Uri (Fresca $Url) -OutFile $pubZip
$publicado = New-Object 'Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
$z = [IO.Compression.ZipFile]::OpenRead($pubZip)
try {
    foreach ($e in ($z.Entries | Where-Object { $_.Name })) {
        $s = $e.Open()
        try { $publicado[($e.FullName -replace '/', '\')] = [BitConverter]::ToString($sha256.ComputeHash($s)) -replace '-' }
        finally { $s.Dispose() }
    }
}
finally { $z.Dispose(); Remove-Item -Force $pubZip }
Write-Host "Publicado: $Nombre, $($publicado.Count) archivos"

# ---------------------------------------------------------------- 2. que va en el zip
function EsBack($rel) { ('\' + $rel) -match '\\_*back\\' }
function Incluir($rel) {
    if (EsBack $rel) { return $false }
    $ext = [IO.Path]::GetExtension($rel)
    -not ($ext -eq '.tmp' -or $ext -eq '.lnk')
}
$dir = Join-Path $Juego $Carpeta
if (-not (Test-Path -LiteralPath $dir)) { Falla "no existe $dir" }
$base = (Resolve-Path -LiteralPath $Juego).Path.TrimEnd('\')
$elegidos = @(Get-ChildItem -LiteralPath $dir -Recurse -File -Force |
    ForEach-Object { $_.FullName.Substring($base.Length + 1) } | Where-Object { Incluir $_ } | Sort-Object)
$nuevo = New-Object 'Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($e in $elegidos) { $nuevo[$e] = Sha256 (Join-Path $base $e) }
Write-Host "Nuevo: $($nuevo.Count) archivos de $dir"

# ---------------------------------------------------------------- 3. comparar
function Resumen($titulo, $lista, $color) {
    if (-not $lista.Count) { return }
    Write-Host "${titulo}: $($lista.Count)" -ForegroundColor $color
    $lista | Group-Object { Split-Path -Parent $_ } | Sort-Object Name | ForEach-Object {
        Write-Host ("  {0} ({1})" -f $_.Name, $_.Count) -ForegroundColor $color
        $_.Group | Select-Object -First 30 | ForEach-Object { Write-Host "      $(Split-Path -Leaf $_)" }
        if ($_.Count -gt 30) { Write-Host "      ... y $($_.Count - 30) mas" }
    }
}
function Aceptado($rel) {
    foreach ($q in $Quitar) {
        $q = $q.TrimEnd('\')
        if ($rel -ieq $q -or $rel.StartsWith("$q\", [StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    $false
}
$cambiados = @($nuevo.Keys | Where-Object { $publicado.ContainsKey($_) -and $publicado[$_] -ne $nuevo[$_] } | Sort-Object)
$agregados = @($nuevo.Keys | Where-Object { -not $publicado.ContainsKey($_) } | Sort-Object)
$quitados = @($publicado.Keys | Where-Object { -not $nuevo.ContainsKey($_) } | Sort-Object)
Resumen 'Cambian' $cambiados Cyan
Resumen 'Se agregan' $agregados Cyan
Resumen 'Trae el publicado y el nuevo NO' $quitados Yellow
$sinAceptar = @($quitados | Where-Object { -not (EsBack $_) -and -not (Aceptado $_) -and [IO.Path]::GetExtension($_) -ne '.tmp' })
if ($sinAceptar.Count) {
    $carpetas = @($sinAceptar | ForEach-Object { Split-Path -Parent $_ } | Sort-Object -Unique)
    Falla ("el zip nuevo dejaria de repartir $($sinAceptar.Count) archivo(s) que no estan en $dir (en $($carpetas -join ', ')). " +
        "Ponelos en $dir, o acepta quitarlos con -Quitar '<carpeta o archivo>'.")
}
if (-not $cambiados.Count -and -not $agregados.Count -and -not $quitados.Count) {
    Write-Host "Sin cambios: $Nombre publicado ya es igual a $dir. No se publica nada." -ForegroundColor Green
    exit 0
}

# ---------------------------------------------------------------- 4. armar
$zip = Join-Path $dist $Nombre
if (Test-Path $zip) { Remove-Item -Force $zip }
$z = [IO.Compression.ZipFile]::Open($zip, 'Create')
try {
    foreach ($e in $elegidos) {
        [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($z, (Join-Path $base $e), ($e -replace '\\', '/'),
            [IO.Compression.CompressionLevel]::Optimal)
    }
}
finally { $z.Dispose() }
$z = [IO.Compression.ZipFile]::OpenRead($zip)
try { $dentro = @($z.Entries | ForEach-Object { $_.FullName -replace '/', '\' }) }
finally { $z.Dispose() }
if ($dentro.Count -ne $elegidos.Count -or @(Compare-Object $dentro $elegidos).Count) { Falla "el zip armado no tiene exactamente los $($elegidos.Count) archivos elegidos" }
Write-Host ("Armado {0}: {1} archivos, {2:N1} MB, SHA-256 {3}" -f $zip, $dentro.Count, ((Get-Item $zip).Length / 1MB), (Sha256 $zip))
if ($Prueba) { Write-Host "-Prueba: no se sube nada. Resultado en dist\$Nombre" -ForegroundColor Cyan; exit 0 }

# ---------------------------------------------------------------- 5. subir y verificar
gh release upload $Release $zip --clobber -R $Repo
if ($LASTEXITCODE) { Falla "no se pudo subir $Nombre" }
$bajado = Join-Path $verif $Nombre
$ok = $false
for ($i = 1; $i -le 3 -and -not $ok; $i++) {
    try { Invoke-WebRequest -UseBasicParsing -Uri (Fresca $Url) -OutFile $bajado; $ok = (Sha256 $bajado) -eq (Sha256 $zip) }
    catch { Write-Host "  intento ${i}: $($_.Exception.Message)" }
    if (-not $ok) { Start-Sleep -Seconds 10 }
}
Remove-Item -Force -ErrorAction SilentlyContinue $bajado
if (-not $ok) { Falla "lo que se baja de $Url no coincide con lo subido" }
Write-Host "Publicado y verificado: $Nombre ($($dentro.Count) archivos)" -ForegroundColor Green
