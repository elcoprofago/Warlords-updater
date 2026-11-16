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
