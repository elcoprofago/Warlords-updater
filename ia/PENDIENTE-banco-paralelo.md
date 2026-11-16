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

## Próximo paso
Adaptar `ia\tanda.py` (puntos 2 y 3 de arriba) para repartir una tanda entre las 6 carpetas, junto con el cambio a
una sola ruta configurable del punto «Orden de carpetas».

## Orden de carpetas (pedido del usuario, 16/11/2026)
Cuando se confirme que el juego admite varias copias: en C: queda solo `C:\Warlords` (ranking). Todas las carpetas
de prueba, incluida la que hoy es `C:\Warlords3`, pasan a `E:\Warlords-TEST`. Hoy 75 archivos del repo (.py, .ps1,
.cs, .ini) nombran `C:\Warlords3` (tanda.py, build.py de los parches, pruebas, publicar-parche.ps1, Visor, opción 9
del Actualizador): cambiarlos todos a una sola ruta configurable en el mismo commit, y recién después retirar
`C:\Warlords3` (borrarla es decisión del usuario, regla global 1).
