# Actualizador de Warlords 3: Darklords Rising

Programa que mantiene al día la carpeta del juego (`C:\Warlords3`): baja los paquetes del juego
(ejércitos, hechizos, héroes, escenarios, ítems o el juego completo) y los parches.

## Para jugar

Bajar el último `Actualizador-v.<versión>.exe` de la release
[Ejecutable](https://github.com/elcoprofago/Warlords-updater/releases/tag/Ejecutable), abrirlo y
elegir en el menú qué actualizar.

## Para mantenerlo

**Cambiar el actualizador**

1. Editar `source/Actualizador.bat` y subir la versión en `source/banner.txt`.
2. Commitear y `git push`.
3. `.\tools\compilar-actualizador.ps1 -Publicar`: compila el exe, lo prueba y lo sube a la release Ejecutable.

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
