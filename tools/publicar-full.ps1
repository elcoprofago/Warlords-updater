<#
Arma Warlords3_FULL.zip desde C:\Warlords3 y lo publica en la release "Actualizador" de GitHub, de
donde lo baja la opcion 6 (ACTUALIZAR TODO EL JUEGO) del actualizador.

  .\tools\publicar-full.ps1           # arma, compara, pregunta y publica
  .\tools\publicar-full.ps1 -Prueba   # arma y compara; no sube nada (resultado en dist\)

Pasos:
  1. Lee la lista del zip publicado (solo su indice, por HTTP con rangos: no baja los 450 MB).
  2. Junta los archivos de C:\Warlords3 dejando afuera lo propio de quien lo arma (ver Incluir):
     lo mismo que la opcion 6 no pisa (NoPisar en source\Actualizador\Actualizador.cs), mas Saves.
     De PGS y SCENARIO van solo los archivos que ya trae el zip publicado (los de fabrica).
     Suma los de iniciales\ (originales de GOG que una PC limpia necesita), tomados de ahi y no de la PC.
  3. Muestra lo que el zip publicado trae y el nuevo no: ese zip es el criterio de que es esencial,
     asi que publicar exige confirmarlo. Muestra tambien lo que se agrega.
  4. Arma dist\Warlords3_FULL.zip y comprueba que tenga exactamente los archivos elegidos.
  5. Arma dist\FULL.txt: el SHA-256 del zip y la version de cada parche cuyos archivos van en el zip
     (la anotada en <Juego>\PARCHES\<ID>.txt, que tiene que ser la de parches\parches.txt). Con eso la
     opcion 9 sabe si esta PC corrio la opcion 6 y si el zip quedo atras de algun parche.
  6. Sube el zip y despues FULL.txt (reemplaza los anteriores), los vuelve a bajar y compara el SHA-256.

Requiere: gh autenticado.
#>
param(
    [switch]$Prueba,
    [string[]]$QuitarIgual = @(),   # lo que el zip nuevo deja afuera a sabiendas: no se pregunta (sesiones sin teclado)
    [string]$Juego = 'C:\Warlords3'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Repo = 'elcoprofago/Warlords-updater'
$Release = 'Actualizador'
$Nombre = 'Warlords3_FULL.zip'
$Url = "https://github.com/$Repo/releases/download/$Release/$Nombre"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Falla($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }
function Sha256($path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash }

# ---------------------------------------------------------------- 1. indice del zip publicado
function Rango($desde, $hasta) {
    $r = [Net.HttpWebRequest]::Create("${Url}?t=$([guid]::NewGuid().ToString('N'))")
    $r.AddRange([long]$desde, [long]$hasta)
    $resp = $r.GetResponse()
    try {
        if ($resp.StatusCode -ne 'PartialContent') { Falla "el servidor no respeto el rango pedido ($($resp.StatusCode))" }
        $ms = New-Object IO.MemoryStream
        $resp.GetResponseStream().CopyTo($ms)
        , $ms.ToArray()
    }
    finally { $resp.Close() }
}
function IndicePublicado {
    $h = [Net.HttpWebRequest]::Create("${Url}?t=$([guid]::NewGuid().ToString('N'))")
    $h.Method = 'HEAD'
    $rh = $h.GetResponse(); $largo = $rh.ContentLength; $rh.Close()
    # Fin del directorio central: en los ultimos 22 bytes + hasta 64 KB de comentario
    $desde = [Math]::Max(0, $largo - 65557)
    $cola = Rango $desde ($largo - 1)
    $i = $cola.Length - 22
    while ($i -ge 0 -and [BitConverter]::ToUInt32($cola, $i) -ne 0x06054b50) { $i-- }
    if ($i -lt 0) { Falla "no se encontro el indice del zip publicado" }
    $total = [BitConverter]::ToUInt16($cola, $i + 10)
    $tam = [BitConverter]::ToUInt32($cola, $i + 12)
    $off = [BitConverter]::ToUInt32($cola, $i + 16)
    if ($total -eq 0xFFFF -or $off -eq 0xFFFFFFFF) { Falla 'el zip publicado es ZIP64: este script no lo lee' }
    $cd = Rango $off ($off + $tam - 1)
    $nombres = New-Object Collections.Generic.List[string]
    $p = 0
    for ($k = 0; $k -lt $total; $k++) {
        if ([BitConverter]::ToUInt32($cd, $p) -ne 0x02014b50) { Falla "indice del zip publicado ilegible en la entrada $k" }
        $utf8 = ([BitConverter]::ToUInt16($cd, $p + 8) -band 0x800) -ne 0
        $ln = [BitConverter]::ToUInt16($cd, $p + 28)
        $le = [BitConverter]::ToUInt16($cd, $p + 30)
        $lc = [BitConverter]::ToUInt16($cd, $p + 32)
        $cod = if ($utf8) { [Text.Encoding]::UTF8 } else { [Text.Encoding]::GetEncoding(437) }
        $n = $cod.GetString($cd, $p + 46, $ln)
        if (-not $n.EndsWith('/')) { $nombres.Add(($n -replace '/', '\')) }
        $p += 46 + $ln + $le + $lc
    }
    , $nombres
}
$publicado = New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($n in (IndicePublicado)) { [void]$publicado.Add($n) }
Write-Host "Zip publicado: $($publicado.Count) archivos"

# ---------------------------------------------------------------- 2. que va en el zip
# Tiene que coincidir con NoPisar (source\Actualizador\Actualizador.cs): lo que la opcion 6 no pisa en
# ninguna PC tampoco sale de la PC de quien arma el zip (hooks\pre-commit exige cambiarlos juntos).
$raizPropia = 'HISTORY.DAT', 'AREA.DAT', 'STRAT_L.BMP', 'STRAT_S.BMP', 'keys.w3', 'update_log.txt', 'DarklordAV.exe'
$dataPropia = 'PREF.DAT', 'COMBAT.DAT', 'OPTIONS.DAT', 'OPT101.DAT', 'OPTIONS.NET', 'OPT101.NET', 'NETSTAT.TXT', 'VECTOR.TXT', 'VMOVEALL.TXT'
function EnCarpeta($rel, [string[]]$carpetas) {
    foreach ($c in $carpetas) { if ($rel.StartsWith("$c\", [StringComparison]::OrdinalIgnoreCase)) { return $true } }
    $false
}
function Incluir($rel) {
    # PGS y SCENARIO mezclan lo de fabrica con lo propio: va solo lo que ya trae el zip publicado.
    # SCENARIO\_BACK son respaldos de quien armo el zip actual.
    if (EnCarpeta $rel 'PGS', 'SCENARIO') { return $publicado.Contains($rel) -and -not (EnCarpeta $rel 'SCENARIO\_BACK') }
    # Carpetas back (ITEMS\back, HERO\back, ...): experimentos de quien arma el zip, el juego no las usa
    if (('\' + $rel) -match '\\_*back\\') { return $false }
    if (EnCarpeta $rel 'Saves', 'Randscen', 'Netsaves', 'Email', 'HERRAMIENTAS', 'GOG', '__support', 'PARCHES') { return $false }
    $nombre = Split-Path -Leaf $rel
    $ext = [IO.Path]::GetExtension($rel)
    if ($rel.IndexOf('\') -lt 0) {
        if ($raizPropia -contains $nombre -or $nombre -like 'unins000.*') { return $false }
        # COMPLEMENTOS.zip y demas zips de la raiz: descargas de herramientas, no son el juego
        if ($ext -eq '.zip') { return $false }
    }
    if ((Split-Path -Parent $rel) -eq 'DATA' -and $dataPropia -contains $nombre) { return $false }
    # Registros de las pruebas de IA (ia\): DarklordAV.exe los escribe solo si existe DATA\IA.INI, que ya queda
    # afuera por ser .ini. En las PC de los jugadores no existen, asi que NoPisar no necesita nombrarlos.
    if ((Split-Path -Parent $rel) -eq 'DATA' -and $nombre -like 'IA*.CSV') { return $false }
    if ($ext -eq '.lnk' -or $ext -eq '.tmp') { return $false }
    # Video: sin dxcfg.ini, SCREEN.INI y VIDEO.INI una instalacion nueva arranca con otra resolucion (ddraw.dll sin
    # su configuracion). Van como valores iniciales: la opcion 6 no los pisa si ya existen (NoPisar, por ser .ini).
    if ($rel -in 'dxcfg.ini', 'SCREEN.INI', 'VIDEO.INI') { return $true }
    if ($ext -eq '.ini' -and -not (EnCarpeta $rel 'CAMPAIGN', 'Ereg', 'edpicts')) { return $false }
    $true
}
if (-not (Test-Path -LiteralPath $Juego)) { Falla "no existe $Juego" }
$base = (Resolve-Path -LiteralPath $Juego).Path.TrimEnd('\')
# iniciales\ (del repo): originales del instalador de GOG que Incluir deja afuera de la PC de quien arma el zip
# (sus opciones, sus bandos) pero que una PC limpia necesita. Van tomados de iniciales\, nunca de la PC: en las PC
# que ya los tienen la opcion 6 no los pisa (NoPisar), en una limpia quedan (PENDIENTE-instalacion-completa.md).
$iniBase = Join-Path $raiz 'iniciales'
$origen = New-Object 'Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($f in (Get-ChildItem -LiteralPath $iniBase -Recurse -File | Where-Object { $_.Extension -ne '.md' })) { $origen[$f.FullName.Substring($iniBase.Length + 1)] = $f.FullName }
$elegidos = @(@(Get-ChildItem -LiteralPath $base -Recurse -File -Force |
    ForEach-Object { $_.FullName.Substring($base.Length + 1) } | Where-Object { -not $origen.ContainsKey($_) -and (Incluir $_) }) +
    @($origen.Keys) | Sort-Object)
foreach ($e in $elegidos) { if (-not $origen.ContainsKey($e)) { $origen[$e] = Join-Path $base $e } }
$nuevo = New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($e in $elegidos) { [void]$nuevo.Add($e) }
Write-Host "Zip nuevo: $($nuevo.Count) archivos de $base"

# OBSOLETOS de parches\<id>\build.py: archivos que instalo una version anterior y ya no van
function Obsoletos($buildPy) {
    if (-not (Test-Path -LiteralPath $buildPy)) { return @() }
    $l = Select-String -LiteralPath $buildPy -Pattern '^OBSOLETOS = ' | Select-Object -First 1
    if (-not $l) { return @() }
    @([regex]::Matches($l.Line, "r?'([^']+)'") | ForEach-Object { $_.Groups[1].Value })
}
# Un resto de version anterior en C:\Warlords3 viajaria a todas las PC con la opcion 6.
$restos = @(Get-ChildItem parches -Directory | ForEach-Object { Obsoletos (Join-Path $_.FullName 'build.py') } |
    Where-Object { $nuevo.Contains($_) })
if ($restos) { Falla "quedan archivos obsoletos en ${base}: $($restos -join ', '). Borralos (o abri DarklordAV.exe una vez) y volve a publicar." }

# ---------------------------------------------------------------- 3. comparar
function Resumen($titulo, $lista, $color) {
    if (-not $lista.Count) { return }
    Write-Host "${titulo}: $($lista.Count)" -ForegroundColor $color
    $lista | Group-Object { if ($_.Contains('\')) { $_.Substring(0, $_.IndexOf('\')) } else { '(raiz)' } } |
        Sort-Object Name | ForEach-Object {
            Write-Host ("  {0} ({1})" -f $_.Name, $_.Count) -ForegroundColor $color
            $_.Group | Select-Object -First 15 | ForEach-Object { Write-Host "      $_" }
            if ($_.Count -gt 15) { Write-Host "      ... y $($_.Count - 15) mas" }
        }
}
$quitados = @($publicado | Where-Object { -not $nuevo.Contains($_) } | Sort-Object)
$agregados = @($nuevo | Where-Object { -not $publicado.Contains($_) } | Sort-Object)
Resumen 'Trae el zip publicado y el nuevo NO' $quitados Yellow
Resumen 'Se agregan' $agregados Cyan
if (-not $quitados.Count -and -not $agregados.Count) { Write-Host 'Misma lista de archivos que el zip publicado.' }

# ---------------------------------------------------------------- 4. armar
New-Item -ItemType Directory -Force (Join-Path $raiz 'dist') | Out-Null
$zip = Join-Path $raiz "dist\$Nombre"
if (Test-Path $zip) { Remove-Item -Force $zip }
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
Write-Host "Armando $zip ..."
$z = [IO.Compression.ZipFile]::Open($zip, 'Create')
try {
    foreach ($e in $elegidos) {
        [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($z, $origen[$e], ($e -replace '\\', '/'),
            [IO.Compression.CompressionLevel]::Optimal)
    }
}
finally { $z.Dispose() }
$z = [IO.Compression.ZipFile]::OpenRead($zip)
try { $dentro = @($z.Entries | ForEach-Object { $_.FullName -replace '/', '\' }) }
finally { $z.Dispose() }
if ($dentro.Count -ne $elegidos.Count -or @(Compare-Object $dentro $elegidos).Count) { Falla "el zip armado no tiene exactamente los $($elegidos.Count) archivos elegidos" }
$sha = Sha256 $zip
Write-Host ("  {0} archivos, {1:N0} MB, SHA-256 {2}" -f $dentro.Count, ((Get-Item $zip).Length / 1MB), $sha)

# ---------------------------------------------------------------- 5. FULL.txt
# Formato que lee LeerCompleto (source\Actualizador\Actualizador.cs): SHA-256 del zip y despues ID|VERSION
# La version de cada parche se comprueba por contenido, no por <Juego>\PARCHES\<ID>.txt: publicar-parche.ps1
# instala en C:\Warlords3 sin escribir esa anotacion. Cada archivo del parche que va en el zip tiene que ser
# igual al del zip del parche publicado (lista y SHA de PARCHES.txt de la release).
$lineasFull = @("# Warlords3_FULL.zip: SHA-256 y version de cada parche que trae (tools\publicar-full.ps1)", $sha)
$verif = Join-Path $raiz 'dist\verificacion'
New-Item -ItemType Directory -Force $verif | Out-Null
$listaPub = Join-Path $verif 'PARCHES.txt'
Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/$Repo/releases/download/$Release/PARCHES.txt?t=$([guid]::NewGuid().ToString('N'))" -OutFile $listaPub
$sha256 = [Security.Cryptography.SHA256]::Create()
foreach ($l in (Get-Content -Encoding UTF8 $listaPub | Where-Object { $_.Trim() -and -not $_.StartsWith('#') })) {
    $c = $l.Split('|')
    $id = $c[0].Trim(); $version = $c[1].Trim()
    $zp = Join-Path $verif "PARCHE-$id.zip"
    Invoke-WebRequest -UseBasicParsing -Uri "$($c[3].Trim())?t=$([guid]::NewGuid().ToString('N'))" -OutFile $zp
    if ((Sha256 $zp) -ne $c[2].Trim()) { Falla "el zip publicado del parche $id no coincide con su SHA de PARCHES.txt" }
    $distintos = @(); $van = 0
    $zz = [IO.Compression.ZipFile]::OpenRead($zp)
    try {
        foreach ($e in ($zz.Entries | Where-Object { $_.Name })) {
            $rel = $e.FullName -replace '/', '\'
            if (-not $nuevo.Contains($rel)) { continue }
            $van++
            $s = $e.Open()
            try { $h = [BitConverter]::ToString($sha256.ComputeHash($s)) -replace '-' } finally { $s.Dispose() }
            if ($h -ne (Sha256 $origen[$rel])) { $distintos += $rel }
        }
    }
    finally { $zz.Dispose(); Remove-Item -Force $zp }
    if (-not $van) { continue }
    if ($distintos.Count) {
        $msg = "el zip trae archivos del parche $id distintos de los de la v$version publicada: $($distintos -join ', '). Instalalo en $base antes de armar el zip."
        if ($Prueba) { Write-Host "AVISO (-Prueba, publicando cortaria aca): $msg" -ForegroundColor Yellow } else { Falla $msg }
    }
    $lineasFull += "$id|$version"
}
Remove-Item -Force $listaPub
$full = Join-Path $raiz 'dist\FULL.txt'
[IO.File]::WriteAllText($full, ($lineasFull -join "`r`n") + "`r`n")
Write-Host "FULL.txt:"; $lineasFull | Select-Object -Skip 1 | ForEach-Object { Write-Host "  $_" }

if ($Prueba) { Write-Host "-Prueba: no se sube nada. Resultado en dist\$Nombre y dist\FULL.txt" -ForegroundColor Cyan; exit 0 }

# lo que sale porque esta en OBSOLETOS de algun parche es lo esperado: no se pregunta
$obsTodos = @(Get-ChildItem parches -Directory | ForEach-Object { Obsoletos (Join-Path $_.FullName 'build.py') })
if (@($quitados | Where-Object { $obsTodos -notcontains $_ -and $QuitarIgual -notcontains $_ }).Count) {
    $r = Read-Host "El zip nuevo deja afuera $($quitados.Count) archivo(s) que hoy se reparten (lista de arriba). Publicar igual? (S/N)"
    if ($r -notmatch '^\s*s') { Write-Host 'No se publico nada.'; exit 0 }
}

# ---------------------------------------------------------------- 6. subir y verificar
# Primero el zip y despues FULL.txt: mientras tanto, la opcion 6 rechaza el zip nuevo por SHA (no instala
# nada) en vez de instalarlo y anotarle los datos del anterior.
function SubirYVerificar($local, $url) {
    gh release upload $Release $local --clobber -R $Repo
    if ($LASTEXITCODE) { Falla "no se pudo subir $(Split-Path -Leaf $local)" }
    $bajado = Join-Path $raiz "dist\verificacion\$(Split-Path -Leaf $local)"
    New-Item -ItemType Directory -Force (Split-Path $bajado) | Out-Null
    $ok = $false
    # ?t=<aleatorio> esquiva la cache de GitHub (Cache-Control: no-cache no la esquiva; ver publicar-parche.ps1)
    for ($i = 1; $i -le 3 -and -not $ok; $i++) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri "${url}?t=$([guid]::NewGuid().ToString('N'))" -OutFile $bajado
            $ok = (Sha256 $bajado) -eq (Sha256 $local)
        }
        catch { Write-Host "  intento ${i}: $($_.Exception.Message)" }
        if (-not $ok) { Start-Sleep -Seconds 10 }
    }
    Remove-Item -Force -ErrorAction SilentlyContinue $bajado
    if (-not $ok) { Falla "lo que se baja de $url no coincide con lo subido" }
}
SubirYVerificar $zip $Url
SubirYVerificar $full "https://github.com/$Repo/releases/download/$Release/FULL.txt"
Write-Host "Publicado y verificado: $Nombre ($($dentro.Count) archivos) y FULL.txt" -ForegroundColor Green
