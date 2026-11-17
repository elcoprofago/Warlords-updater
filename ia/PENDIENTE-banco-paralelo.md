# Banco de pruebas en paralelo: varias partidas a la vez

Pedido del usuario (16/11/2026). Corrige lo anotado en `PENDIENTE-entrenamiento-ia.md` («no se pueden correr
partidas simultáneas»): eso venía de una suposición, no de una medición.

## Medido (16/11/2026, sobre una partida de tanda en curso)
- DarklordAV usa un solo núcleo al 100 %; la PC tiene 12. Hoy el banco usa 1/12 de la máquina.
- 52 MB de memoria por partida, 18 GB libres: la memoria no limita.
- El juego corre en ventana: pueden convivir varias.
- Estimación: 6 a 10 partidas a la vez.

## Qué lo impide hoy (`ia\tanda.py`)
1. Una sola carpeta, `C:\Warlords3` (`JUEGO`): ahí se escribe qué partida cargar (IA.INI, guardada rotada) y el
   juego deja sus registros (IA.CSV, eventos, IA_FIN.CSV). Dos partidas ahí se pisan.
   Hecho (16/11/2026, autorizado por el usuario, que pidió E: y no C:): `E:\Warlords-TEST\Warlords3-1` a `-6`,
   copias de trabajo de `C:\Warlords3` (robocopy /E /XJ; verificadas: 6056 archivos y 583,8 MB cada una, igual
   que el origen). Se copiaron con la tanda 222 en curso: antes de usarlas, refrescarlas con vista-aliada al día.
2. `cerrar_juego()` cierra el juego por nombre: mataría todas. Cerrar cada una por su PID.
3. Reparto de partidas (`plan`/`correr`), grabación en `datos.db` y el Monitor de IA suponen una partida por vez:
   repartir entre carpetas y grabar sin chocar (una sola escritura a la base por vez).

## Prueba de varias copias (16/11/2026): el juego las admite
Sin tanda corriendo, `Tanda_Scarpart` con IA original en todos los colores, 4 minutos cada medición, desde las
carpetas de `E:\Warlords-TEST` (mismo DarklordAV.exe que `C:\Warlords3`, md5 comparado):
- 1 sola (Warlords3-1): 21 turnos.
- 6 a la vez (Warlords3-1 a -6): 16, 25, 23, 19, 17, 18 turnos = 118 en total, **5,6 veces lo de una sola**.
  Cada partida va en promedio al 94 % de la velocidad de una sola.
- Las 6 abrieron, el botón «Single Player» se apretó en todas por su PID, y ninguna se frenó por no tener la
  ventana al frente.
- No se probó con más de 6 (hay 6 carpetas). Hoy no hace falta: 6 ya multiplica por 5,6.

## Hecho: el banco juega en paralelo (16/11/2026, Monitor de IA 1.0.24)
`ia\tanda.py` resuelve los puntos 1 a 3:
- Las partidas se reparten entre las carpetas de `[Carpetas] paralelas` de `tanda.ini` (separadas por coma); sin esa
  línea, las `E:\Warlords-TEST\Warlords3-1` a `-6` que existan; sin ninguna, se juega en `JUEGO` como antes.
  `[Carpetas] juego` cambia `JUEGO` (por defecto la de `juego_pruebas.py`).
- `JUEGO` sigue siendo el origen: ahí instala `build.py` y ahí están las guardadas. Antes de cada tanda (y al
  retomar), `sincronizar` copia a cada carpeta lo que cambió (`robocopy /MIR /XJ`, sin tocar IA.INI, los CSV ni
  IA_ROTADA.SAV) y verifica que el exe quedó igual; si no, la tanda no arranca.
- Un hilo por carpeta, que toma la siguiente partida pendiente; se abren de a una cada 3 s. Cada juego se cierra por
  su PID. Las escrituras a `datos.db` van de a una (`DBLOCK`). La tabla `partida` suma la columna `carpeta`.
- Al retomar se juegan las partidas que falten, no solo las del final; antes se cierran los juegos que hayan quedado
  abiertos en carpetas del banco (por ruta del exe: nunca uno de `C:\Warlords`).
- Monitor de IA: lee los registros de la carpeta de la partida; con varias, dice «jugando N a la vez» y muestra la
  tabla de la primera; el fin estimado divide por las que corren a la vez.

Probado en caliente con una base aparte (no `datos.db`):
- 7 partidas con tope de 3 turnos en 6 carpetas: la carpeta 2 jugó dos, todas grabadas con su carpeta, tanda
  terminada, ningún juego abierto al final.
- Tanda de 8 cortada matando el proceso a los 35 s: quedaron 5 juegos abiertos; «seguir» los cerró, marcó las 6 a
  medias como «cortada», las volvió a jugar y conservó la ya terminada.
- Monitor leyendo una tanda de 6 en curso: «jugando 4 a la vez», luego 6, luego 5 de 6 terminadas, y «terminada».
- El silencio del juego fallaba en los hilos (COM sin iniciar): corregido con `CoInitialize` en cada hilo.

Prueba con una tanda real: `TAREAS.md` 231.

## Hecho: orden de carpetas (16/11/2026)
- `C:\Warlords3` se copió a `E:\Warlords-TEST\Warlords3` (robocopy /E /XJ, código 1; 6010 archivos y 583,7 MB en
  los dos lados).
- La ruta del juego de pruebas vive solo en `juego_pruebas.py` (raíz del repo, `W3`). La importan `ia\tanda.py`
  (origen del banco), los `build.py` de los parches, las pruebas, `heroes25.py`, `creditos\extraer.py`,
  `manual\build_manual.py`; los `tools\publicar-*.ps1` la leen de ese archivo. 72 archivos cambiados; el Monitor
  de IA se compila con la raíz del repo en `--paths`.
- No cambian (son de la PC de cada jugador, no del banco): el `C:\Warlords3` por defecto del Actualizador
  (`juego.txt` lo cambia) y `JUEGO0` del Simulador de combate.
- Configuración local (fuera de git) del Visor de historia y del Simulador: pasada a E:.
- Pruebas `prueba_*.py` (60) corridas antes y después del cambio: mismos resultados. La copia tenía el `WAR3AV.RES` de la 1.0.232.0 (`prueba_puerto` lo detectó); se reinstaló vista-aliada 1.0.233.0 con `build.py`, que ya instala en E:, y volvió a dar bien.
- Monitor de IA 1.0.25: el mismo banco, con el origen en E:.
- Retirar `C:\Warlords3`: decisión del usuario, `TAREAS.md` 233.

## Orden de carpetas (pedido del usuario, 16/11/2026)
Cuando se confirme que el juego admite varias copias: en C: queda solo `C:\Warlords` (ranking). Todas las carpetas
de prueba, incluida la que hoy es `C:\Warlords3`, pasan a `E:\Warlords-TEST`. Hoy 75 archivos del repo (.py, .ps1,
.cs, .ini) nombran `C:\Warlords3` (tanda.py, build.py de los parches, pruebas, publicar-parche.ps1, Visor, opción 9
del Actualizador): cambiarlos todos a una sola ruta configurable en el mismo commit, y recién después retirar
`C:\Warlords3` (borrarla es decisión del usuario, regla global 1).

## Medición de CPU y tope de partidas (16/11/2026)
Con 6 partidas a la vez (PC de 6 núcleos / 12 hilos, 47 GB): CPU 70-80 % según el Administrador de tareas, 52 MB por
partida. El semáforo del Monitor usaba psutil.cpu_percent (tiempo ocupado de los hilos: 54-62 %) y no llegaba al
rojo; desde el Monitor 1.0.26 lee «% Processor Utility» (PdhAddEnglishCounterW, el mismo número del Administrador de
tareas; psutil queda de respaldo). Probado en caliente: 66-71 % contra 65 % del contador de Windows por WMI.
**Próximo paso:** después de la serie de la TAREAS 232, crear `Warlords3-7` y `-8` y correr una tanda con 8. Se
compara minutos por partida contra 6: si baja, quedan 8; si no, 6. Con 10 el procesador ya estaría saturado.

- **Prueba de 8 a la vez preparada** (16/11/2026, TAREAS 240): creadas `Warlords3-7` y `-8`; `[Carpetas] paralelas` de tanda.ini (local) lista las 8, porque el valor por defecto del código sigue en 1 a 6. Si 8 rinde más, pasar el valor por defecto a 8 en tanda.py (exige publicar el Monitor).
- **Ventanas fuera de la pantalla principal** (16/11/2026, vista-aliada 1.0.238.0 + Monitor 1.0.27, TAREAS 241): el lanzador se crea en `[Tanda] VentanaX/VentanaY` de IA.INI (ia_ventana en 0x478f82). La ventana de juego no se puede crear fuera: DirectDraw (SetCooperativeLevel 0x11, 0x4ed961) la estira sobre la pantalla principal; tanda.py la mira cada 20 ms, la mueve (medido: 0,3 s en la principal, antes 5 s) y devuelve el foco a lo que estaba en uso. Para que no asome nada habría que crear DirectDraw sobre el otro monitor (DirectDrawEnumerateEx), cambio grande y riesgoso: no se hizo.
- **Resultado de 8 a la vez** (tanda 177, 16/11/2026): 16 partidas en 33,3 min = **2,1 min por partida**, contra 3,1-3,4 con 6 (tandas 174-176). Cada partida tarda lo mismo que con 6 (15,6 min contra 16), así que la CPU (84-85 %) todavía no frena: 8 queda como valor por defecto (tanda.py, Monitor 1.0.27) y tanda.ini ya no lo fija. Conviene pedir múltiplos de 8 partidas. Una partida colgada (n.º 9, Warlords3-6, 0 turnos, 20:32-20:42), en el mismo rato en que yo abría el juego de prueba en Warlords3: no se verificó si fue por eso. Próximo paso posible: probar 10 (Warlords3-9 y -10) y mirar si cada partida se alarga.

## Para retomar (16/11/2026)
- En curso: TAREAS 241, tanda de 16 en Borderlands_NO con Monitor 1.0.27 y vista-aliada 1.0.238.0, para probar que las ventanas no tapen la pantalla principal ni quiten el foco. Al terminar: revisar el informe (minutos por partida, colgadas) y lo que el usuario anote en la 241.
- No queda ningún experimento de IA preparado. Próximo paso: elegir el siguiente de ia\PENDIENTE-ia-innovaciones.md (objetivo: oportunidades y riesgos de las innovaciones, memoria objetivo-ia-innovaciones) y correrlo en una sola tanda de 24 o 32 partidas (múltiplos de 8).
- Opcional: probar 10 carpetas (crear Warlords3-9 y -10, [Carpetas] paralelas en tanda.ini) y ver si cada partida se alarga.

## Tanda 178 fallida (16/11/2026, investigada el 17/11)
- 32 registros, todos 0 turnos y «cortada»: son las mismas 8 partidas (n 0-7), arrancadas 4 veces (21:16, 22:54,
  23:25, 23:36) y cortadas a mano a los 98, 31 y 11 min. La última ronda quedó «jugando» (se cerró a la fuerza).
  Ningún IA.CSV en 98 min, y aun así nunca saltó «colgada» (10 min): el hilo de cada partida quedó trabado antes
  de su vuelta de control, no solo el juego.
- Es la primera tanda con vista-aliada 1.0.238.0 + Monitor 1.0.27 (commit d8e83c7); la 177 (1.0.237.0, misma
  guardada, 8 a la vez) anduvo. Cambios de d8e83c7 que pueden explicarlo (sin verificar todavía):
  1. La ventana de juego se mueve a los 20 ms de aparecer (antes a los 5 s), mientras DirectDraw todavía inicia
     el modo exclusivo/pantalla completa (SetCooperativeLevel 0x11): si el juego se traba ahí, el SetWindowPos de
     tanda.py (sincrónico entre procesos) espera para siempre y la detección de cuelgue no corre.
  2. El juego nunca tiene el foco (se devuelve enseguida): si la carga de la guardada lo necesita, no arranca.
  3. El lanzador nace en VentanaX/Y (ia_ventana): el código del parche se revisó y está bien armado.
- **Causa (17/11/2026, reproducida con 1 partida en Warlords3-1):** la 2. Mover la ventana a los 20 ms no afecta
  (con foco, IA.CSV crece igual). Sin foco nunca, el juego no pasa por la activación (0x4ed480: [0x501280] = 1 y
  despausa con 0x4de090(0)) y queda pausado desde el arranque: la ventana responde (IsHungAppWindow 0) pero IA.CSV
  se queda en el encabezado (52 bytes). Por qué no saltó «colgada»: queda sin explicar del todo; de paso,
  `llevar_al_monitor` usa SWP_ASYNCWINDOWPOS para que una ventana trabada no frene al hilo de la partida.
- **Arreglo:** vista-aliada 1.0.239.0, `ia_tload`: con [Tanda], si [0x501280] = 0 hace la activación una vez
  (marca el foco y despausa). Probado igual que la 178 (mover a los 20 ms y devolver foco): IA.CSV 364 → 2161 bytes
  en 60 s. Monitor de IA 1.0.28 con el tanda.py nuevo. Prueba real: TAREAS 242.
