# Actualizador de Warlords 3: Darklords Rising

Programa que mantiene al día la carpeta del juego (`C:\Warlords3`): baja los paquetes del juego
(ejércitos, hechizos, héroes, escenarios, ítems o el juego completo) y los parches.

## Para jugar

Bajar el último `Actualizador-v.<versión>.exe` de la release
[Ejecutable](https://github.com/elcoprofago/Warlords-updater/releases/tag/Ejecutable), abrirlo y
elegir en el menú qué actualizar.

## Para mantenerlo

**Cambiar el actualizador**

Es un programa C# (.NET Framework 4.8, WinForms, con aspecto de terminal) en `source/Actualizador/`. Las
direcciones de los paquetes del juego están en `source/*_url.txt` (línea 1 principal, línea 2 alternativa) y van
embebidas en el exe, igual que la fuente JetBrains Mono (licencia OFL).

1. Editar `source/` y subir la versión en `source/Actualizador/Actualizador.csproj` (`Version`, `FileVersion` y
   `AssemblyVersion`, las tres iguales).
2. Commitear y `git push`.
3. `.\tools\compilar-actualizador.ps1 -Publicar`: compila el exe (`dotnet build`, SDK del Windows 10), lo prueba y
   lo sube a la release Ejecutable.

Para probarlo sin tocar `C:\Warlords3` ni el escritorio: `W3_JUEGO` (carpeta del juego), `W3_ESCRITORIO` (dónde
crea los accesos directos), `W3_PARCHES_URL` (otro `PARCHES.txt`, puede ser un archivo local), `W3_ENTRADA`
(respuestas separadas por `|`; al acabarse cierra), `W3_TRANSCRIPCION` (guarda el texto de la pantalla) y
`W3_CAPTURA` (una captura PNG cada vez que espera una respuesta).

Cada programa de `C:\Warlords3\HERRAMIENTAS` se baja con su propia opción y se publica por un solo canal (no hay
un zip con todos, que quedaba con versiones viejas):

| Opción | Programa | Asset de la release Actualizador | Lo publica |
|---|---|---|---|
| 7 | DarklordsValidator | `DarkValidator.zip` | `toolspublicar-herramienta.ps1 DarklordsValidator` |
| 8 | EditorPGS (PGS-VISOR) | `PGS-VISOR.zip` | `toolspublicar-herramienta.ps1 EditorPGS` |
| 10 | DarkCompare | `DarkCompare.zip` | `toolspublicar-herramienta.ps1 DarkCompare` |
| 11 | Votación | parche `herramientas` | `tools\publicar-parche.ps1 herramientas` |
| 12 | Sorteo | parche `herramientas` | `tools\publicar-parche.ps1 herramientas` |
| 13 | Puente Warlords | `PuenteWarlords.zip` + `.txt` | `tools\publicar.ps1` de puente-warlords |

7, 8 y 10 descomprimen su zip (los archivos sueltos, sin carpeta) en `HERRAMIENTAS` y no pisan los `.ini` que ya
estén (la configuración de cada PC). 11 y 12 bajan el zip del parche `herramientas`, lo verifican como la opción 9 y
extraen solo su programa. La opción 6 no trae nada de `HERRAMIENTAS` (ni lo publica `publicar-full.ps1` ni lo pisa
el actualizador). `COMPLEMENTOS.zip` (todas juntas) se borró de la release: la
opción 10 de los actualizadores 1.0.8.0 y anteriores da "no está publicado".

La opción 13 (JUGAR EN RED) deja Puente Warlords en `C:\Warlords3\HERRAMIENTAS\PuenteWarlords` y lo abre. Baja
`PuenteWarlords.txt` (la versión publicada) y, si es más nueva que la del exe instalado o no hay exe, baja
`PuenteWarlords.zip`; los dos assets de la release Actualizador los publica `tools\publicar.ps1` del repo
puente-warlords. Tampoco pisa los `.ini`.

La opción 14 (TAILSCALE) es la conexión de respaldo del Puente: si falta, baja e instala Tailscale
(`https://pkgs.tailscale.com/stable/tailscale-setup-latest.exe`), corre `tailscale up` y abre en el navegador el
enlace de inicio de sesión, pide el enlace con que el dueño del servidor comparte su PC y espera a que el servidor
conteste en el puerto 47800 de alguna dirección 100.64.0.0/10 del `servidor.txt` del Puente instalado. La 15 crea
los accesos directos y la 16 sale.

**Publicar un parche**

1. Cambiar `parches/<ID>/build.py`, correrlo (`python parches\<ID>\build.py`) y probar el juego.
2. Subir la versión del parche en `parches/parches.txt`.
3. Commitear y `git push`.
4. `.\tools\publicar-parche.ps1 <ID>`: lo empaqueta y lo sube a la release Actualizador.

**Publicar Votación o Sorteo** (parche `herramientas`: `C:\Warlords3\Herramientas\`, de donde los abren los
botones de vista-aliada)

1. En el repo del programa (`..\Votacion` o `..\Sorteo`): subir su VERSION, commitear y correr `compilar.ps1`.
2. Poner esa versión en `PROGRAMAS` de `parches/herramientas/build.py` y subir la versión de `herramientas` en
   `parches/parches.txt`.
3. Commitear, `git push` y `.\tools\publicar-parche.ps1 herramientas`.

`build.py` no compila: copia los exe y se niega si la versión no coincide, si el repo del programa tiene cambios sin
commitear o si el exe es anterior a su último commit. `votacion.ini` no se publica (la pantalla de cada PC no se
pisa).

Para publicar un parche no hace falta recompilar el actualizador. Cada script explica al principio
qué controla y por qué puede negarse.

Una sola vez por clon: `git config core.hooksPath hooks`.
