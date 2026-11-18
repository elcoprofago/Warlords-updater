# Video: basura en las casillas ocultas con placas viejas (cnc-ddraw)

## Estado (18/11/2026)

- **Síntoma.** En la notebook (Intel HD Graphics 3000, driver de 2016, Windows build 17763) y en la PC de Nico, las
  casillas ocultas o sin explorar se llenaban de tropas. En la PC principal (NVIDIA RTX 5050) no pasa.
- **Diagnóstico.** Opción 16 del Actualizador. Mismos `Darklord.exe`, `ddraw.dll` (dxcfg 1.0.0.5164), `dxcfg.ini` y
  `SCREEN.INI` en las dos PC: solo cambia la placa. El `ddraw.dll` actual dibuja con Direct3D 9 y efectos de la placa.
- **Descartado.** Pantalla completa en `dxcfg.ini`: achica la imagen y deja el cursor inutilizable (TAREAS 255).
- **Solución probada en la notebook (TAREAS 256): funciona perfecto.** Se reemplazó `ddraw.dll` por el de
  **cnc-ddraw 7.1.0.0** (https://github.com/FunkyFr3sh/cnc-ddraw, código abierto), con el renderer **GDI**, que
  dibuja con Windows y no usa la placa. El `ddraw.dll` viejo quedó renombrado `ddraw.dll.dxcfg` para volver atrás.
  `ddraw.ini`:

  ```ini
  [ddraw]
  windowed=true
  fullscreen=true
  maintas=false
  renderer=gdi
  adjmouse=false
  fixchilds=0
  hook_peekmessage=true
  ```

  Por qué cada línea:
  - `fullscreen=true` con `windowed=true`: pantalla completa sin borde.
  - `fixchilds=0`: sin esto, cnc-ddraw apaga el escalado, porque Warlords usa ventanas hijas.
  - `hook_peekmessage=true` y `adjmouse=false`: sin estas dos, el cursor queda corrido a la izquierda.
- **En el banco** (`E:\Warlords-TEST\Warlords3`, PC principal): con GDI en ventana anduvo bien (menú, mapa oculto,
  cursor). La pantalla completa no se puede juzgar ahí: el juego se abre en el segundo monitor, que es 4:3. El banco
  quedó con su `ddraw.dll` original.

## Opción 17 del Actualizador (1.0.22.0, 18/11/2026)

«RENDER DE VIDEO» (1.0.23.0; en la 1.0.22.0 se llamaba «VIDEO PARA PLACAS VIEJAS»): 1 instala (baja cnc-ddraw 7.1.0.0 de GitHub, verifica su SHA-256, renombra el
`ddraw.dll` de dxcfg a `ddraw.dll.dxcfg`, pone el de cnc-ddraw y escribe el `ddraw.ini` de arriba); 2 vuelve al
original. Mientras exista `ddraw.dll.dxcfg`, la opción 6 no pisa `ddraw.dll`. Es a elección: no se instala sola.
Probado en una carpeta de prueba: instalar, opción 6 sin pisarlo, deshacer y opción 6 normal.

## Próximo paso (anterior; el 2 quedó hecho con la opción 17)

1. El informe de Nico (TAREAS 252): si su placa también es vieja o integrada, se confirma el patrón.
2. Llevarlo a los jugadores sin tocar las PC que andan bien: una opción del Actualizador, o del parche, que instale
   cnc-ddraw con este `ddraw.ini` y que se pueda deshacer (vuelve a poner el `ddraw.dll` de dxcfg). No conviene
   ponerlo por defecto para todos: en la PC principal el actual anda bien y GDI no se probó en partidas largas.
