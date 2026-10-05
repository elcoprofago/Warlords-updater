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

Para publicar un parche no hace falta recompilar el actualizador. Cada script explica al principio
qué controla y por qué puede negarse.

Una sola vez por clon: `git config core.hooksPath hooks`.
