Warlords 3 Darklords Rising v. 1.02 (actualizador de carpetas del juego).

## Qué hay acá

| Ruta | Qué es |
|---|---|
| `source/Actualizador.bat` | El actualizador. Se compila a exe con **Bat To Exe Converter**, embebiendo los `.txt` de `source/`. |
| `source/*_url.txt`, `source/banner.txt` | URL de cada paquete (primaria y alternativa) y el banner con la versión. |
| `parches/parches.txt` | Lista de parches: ID, versión, archivos y descripción. |
| `parches/<ID>/build.py` | Genera los archivos del parche a partir de los originales de `C:\Warlords3`. |
| `tools/publicar-parche.ps1` | Compila, empaqueta y publica un parche. |
| `tools/compilar-actualizador.ps1` | Compila el exe del actualizador, lo prueba y opcionalmente lo publica. |
| `hooks/pre-commit` | Controles de commit (activar una vez por clon: `git config core.hooksPath hooks`). |

Lo que baja el actualizador está en las releases de GitHub:
- **Actualizador**: `ARMY.zip`, `SPELL.zip`, `HERO.zip`, `ESCEN.zip`, `ITEMS.zip`, `Warlords3_FULL.zip`,
  `DarkValidator.zip`, y para los parches `PARCHES.txt` + `PARCHE-<ID>-v<VERSION>.zip`.
- **Ejecutable**: el exe del actualizador.

## Parches (opción 8 del menú)

El actualizador baja `PARCHES.txt` de la release, muestra cada parche con su estado (no instalado,
instalado, hay versión nueva), y al elegir uno baja su zip, **verifica el SHA-256** contra
`PARCHES.txt` y recién ahí lo descomprime en `C:\Warlords3`. La versión instalada queda en
`C:\Warlords3\PARCHES\<ID>.txt`.

Publicar un parche, o una versión nueva, no requiere recompilar el exe del actualizador.

### Sacar una versión nueva de un parche

1. Cambiar `parches/<ID>/build.py` y generarlo en el juego: `python parches\<ID>\build.py`
   (escribe en `C:\Warlords3`, nunca sobre los originales).
2. Probarlo jugando.
3. Subir la VERSION de `<ID>` en `parches/parches.txt` y commitear todo junto (el hook bloquea
   el commit si cambia el parche y no la versión). `git push`.
4. `.\tools\publicar-parche.ps1 <ID> -Prueba` para ver qué se publicaría, y después sin `-Prueba`.

El script se niega si: no estás en `main`, hay cambios sin commitear, el commit no está en GitHub,
la versión ya se publicó (existe la etiqueta `parche-<ID>-v<VERSION>`) o es menor que la publicada,
o lo que compila no es idéntico, byte a byte, a lo que está en `C:\Warlords3` (lo que se probó).
Después de subir, vuelve a bajar el zip y `PARCHES.txt` y compara los SHA-256. El zip de la versión
anterior queda en la release; se puede borrar a mano.

GitHub cachea por un rato lo que sirvió en cada URL de una release, aun después de reemplazar el
archivo, y ignora `Cache-Control: no-cache`. Por eso cada versión del zip tiene su propio nombre, y
el `.bat` y la verificación agregan `?t=<aleatorio>` a la URL.

`build.py` requiere `pip install keystone-engine capstone`; `prueba_emulada.py`, `pefile unicorn`.

### Agregar un parche nuevo

Crear `parches/<ID>/build.py` que acepte la carpeta de salida como primer argumento (por defecto
`C:\Warlords3`), agregar su línea a `parches/parches.txt` y seguir los pasos de arriba.

## Cambiar el actualizador mismo

1. Editar `source/`, subir la versión en `source/banner.txt`. Commitear y `git push`.
2. `.\tools\compilar-actualizador.ps1`: compila con Bat To Exe Converter 4.2 por línea de comandos
   (embebe los `.txt` de `source/` y `tools/actualizador.ico`), prueba el exe en una carpeta con
   `.txt` viejos (tiene que mostrar su versión, leer los suyos y no tocar esos), y arma `Actualizador-v.<versión>.exe` + `.exe.zip` en la raíz.
3. `.\tools\compilar-actualizador.ps1 -Publicar`: además los sube a la release **Ejecutable** y los
   verifica bajándolos de nuevo. Se niega si esa versión ya está subida.

La línea de comandos del conversor ignora la cabecera `::[Bat To Exe Converter]` del `.bat`: el
ícono, la versión, los `.txt` y la carpeta de extracción los pone el script. Con `/extractdir 1` el
exe extrae los `.txt` en una carpeta temporal nueva en cada ejecución y el `.bat` los lee de ahí
(`%b2eincfilepath%`). Hasta el 1.0.0.8 se extraían junto al exe (`/extractdir 0`), que no pisa
archivos existentes: el 1.0.0.8, donde había corrido el 1.0.0.7, mostraba "V. 1.0.0.7" y usaba sus URLs.

Para probar el `.bat` sin tocar el juego ni lo publicado: `W3_JUEGO` cambia la carpeta del juego
y `W3_PARCHES_URL` la URL de `PARCHES.txt` (acepta `file:///`).
