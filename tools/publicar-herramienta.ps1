<#
Publica DarklordsValidator (opcion 7), EditorPGS (opcion 8) o DarkCompare (opcion 10) en la release "Actualizador":
compila el repo hermano en Release, arma el zip plano que bajan esas opciones, lo sube y lo verifica bajandolo de
nuevo (SHA-256): se verifica lo publicado, no el codigo de salida.

  powershell -NoProfile -ExecutionPolicy Bypass -File tools\publicar-herramienta.ps1 DarklordsValidator|EditorPGS|DarkCompare

Se niega si el repo del programa tiene cambios sin commitear: lo publicado tiene que poder rearmarse.
#>
param([Parameter(Mandatory)][ValidateSet('DarklordsValidator', 'EditorPGS', 'DarkCompare')][string]$Programa)

$asset = @{ DarklordsValidator = 'DarkValidator.zip'; EditorPGS = 'PGS-VISOR.zip'; DarkCompare = 'DarkCompare.zip' }[$Programa]
$repo = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) $Programa
function Falla($texto) { Write-Host "NO PUBLICADO: $texto" -ForegroundColor Red; exit 1 }

$gh = 'C:\Program Files\GitHub CLI\gh.exe'
if (-not (Test-Path -LiteralPath $gh)) { $gh = 'gh' }

$sucio = & git.exe -C $repo status --porcelain --untracked-files=no
if ($LASTEXITCODE -ne 0) { Falla "git status en $repo" }
if ($sucio) { Falla "hay cambios sin commitear en $repo" }

& dotnet build $repo -c Release -nologo -v q
if ($LASTEXITCODE -ne 0) { Falla 'no compila' }

$bin = Get-ChildItem -Directory (Join-Path $repo 'bin\Release') | Select-Object -First 1
$archivos = Get-ChildItem -File $bin.FullName | Where-Object { $_.Name -like "$Programa.*" -and $_.Extension -in '.exe', '.dll', '.json', '.pdb', '.config' }
if (-not ($archivos | Where-Object Name -eq "$Programa.exe")) { Falla "no esta $Programa.exe en $($bin.FullName)" }

$tmp = Join-Path $env:TEMP "publicar-herramienta-$Programa"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force (Join-Path $tmp 'bajado') | Out-Null
$zip = Join-Path $tmp $asset
Compress-Archive -Path $archivos.FullName -DestinationPath $zip

& $gh release upload Actualizador $zip --clobber -R elcoprofago/Warlords-updater
if ($LASTEXITCODE -ne 0) { Falla 'gh release upload' }

$bajado = Join-Path $tmp "bajado\$asset"
& $gh release download Actualizador -p $asset -D (Split-Path $bajado) -R elcoprofago/Warlords-updater --clobber
if ($LASTEXITCODE -ne 0) { Write-Host "PUBLICADO A MEDIAS: no se pudo bajar $asset para verificarlo" -ForegroundColor Red; exit 1 }
$a = (Get-FileHash $zip).Hash; $b = (Get-FileHash $bajado).Hash
if ($a -ne $b) { Write-Host "PUBLICADO A MEDIAS: el $asset publicado no es el armado ($a / $b)" -ForegroundColor Red; exit 1 }
Write-Host "PUBLICADO: $asset ($($archivos.Count) archivos, SHA-256 $a)" -ForegroundColor Green
