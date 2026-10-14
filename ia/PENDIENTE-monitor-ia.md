# Monitor de IA: panel de control de las tandas (pedido 14/10/2026)

## Qué quiere el usuario
Reemplazar `ia\tanda.bat` por un programa .exe con ventana propia, el "Monitor de IA", que sirva de panel de
control de las tandas de prueba de la IA, que corren en segundo plano en el monitor secundario.

## Dónde va
En este repo, en `ia\monitor-ia\`. No en un repo aparte: el panel usa `ia\tanda.py`, lee `ia\datos.db` y
`ia\tanda.ini`, y depende del formato de IA.CSV / IA_BAT.CSV que escribe DarklordAV.exe. Separarlo crearía un
contrato entre repos (regla 9) sin ninguna ventaja.

## Qué debe mostrar
Pedido por el usuario:
- cuántas partidas tiene programadas la tanda y cuál está corriendo;
- desde qué fecha y hora corre;
- botón "desactivar sonido del juego" (hoy `tanda.silenciar(pid)`, con pycaw);
- botón "activar alarma" de fin de tanda (hoy `ia\aviso.py`, Alarm01.wav tres veces).

Propuesto por Claude y aceptado en general (falta elegir qué entra en la primera versión):
- partida en curso: mapa, turno actual de cuántos, qué colores juegan con la IA de prueba;
- tabla en vivo por color: puntos de victoria, ciudades, oro, ejércitos (de IA.CSV);
- batallas hasta ahora, ganadas y perdidas por IA (de IA_BAT.CSV);
- tiempo desde el último turno, con aviso de posible cuelgue;
- partidas terminadas con resultado (ok, colgada, cerrada) y duración, y hora estimada de fin;
- el informe comparativo de `ia\informe.py`, actualizado tras cada partida;
- controles: elegir monitor (hoy `ia\monitor.bat`), programar partidas y mapas, pausar, cortar y retomar
  (`tanda.py seguir`), y mantener la PC despierta (si Windows suspende o reinicia, la tanda se corta).

## Estado de lo que ya existe (todo probado en vivo el 14/10/2026)
- `ia\tanda.py nueva --partidas N` corre la tanda; `seguir` la retoma. Mueve el juego al monitor de `tanda.ini`
  cada 5 s, aprieta "Single Player" y silencia el juego. Registra todo en `ia\datos.db` (tablas tanda, partida,
  batalla, etc.).
- DarklordAV.exe 1.0.32.0 (build en `parches\vista-aliada\build.py`) no se pausa en segundo plano, carga sola la
  partida "Tanda_*" y pasa a Computadora el bando guardado como Humano.
- Partidas guardadas: Tanda_Scarpart y Tanda_Borderlands (Hexagon y TomeLand no tienen 8 casillas).
- Una partida de Scarpart dura unos 22–27 minutos.
- Límites conocidos: el juego toma el foco un instante al arrancar cada partida; el mouse no funciona en el
  monitor secundario (no hace falta).

## Primera versión (14/10/2026)
`ia\Monitor-IA.exe` (fuente `ia\monitor-ia\monitor_ia.py`, se compila con `python ia\monitor-iauild.py`; el exe
no se versiona). Reemplazó a tanda.bat, monitor.bat y aviso.py (borrados). Probado abriéndolo sobre la tanda 4 a
medias: muestra tanda, partida en curso, tabla por color y batallas. Falta la prueba con una tanda real (TAREAS.md).
- Tanda: partidas, guardadas, Nueva tanda / Retomar / Cortar; fecha de inicio, cuántas van y fin estimado.
- Controles: sonido del juego (tanda.CONTROL), alarma al terminar (con botón de prueba), monitor del juego.
- Partida en curso: mapa, turno, colores con IA de prueba, batallas ganadas/perdidas por IA atacante, aviso de
  posible cuelgue a los 5 min sin turnos, tabla por color (PV calculados con pv_calc).
- Bitácora con lo que imprime tanda.py y el informe al final. Mantiene la PC despierta mientras corre.
- tanda.py: una partida cortada (o que quedó "jugando" al cerrar la ventana) se guarda como "cortada" y se vuelve
  a jugar al retomar.

## Próximo paso
Según lo que diga la prueba del usuario. Quedan de la lista propuesta: pausar, partidas terminadas con duración en
pantalla (hoy solo las últimas 5 cuando no hay partida en curso), informe tras cada partida (hoy al final).

## Cambios posteriores (14/10/2026)
Ventana angosta, círculos de CPU y RAM (imágenes de USBagent), ruedita de configuración con fondo liso o textura
(sección [Fondo] de tanda.ini), Retomar solo la última tanda, el panel muestra la tanda que se juega. Se borraron
de datos.db las tandas 2 y 3 (pruebas abandonadas) con sus partidas.

## Parche de cada tanda (14/10/2026)
El panel Tanda muestra con qué parche juega la tanda mostrada (vista-aliada y huella del exe) y con cuál jugaron
todas, agrupadas de corrido. tanda.py lo registra al crear la tanda y se niega a retomar con otro exe.
Falta recompilar Monitor-IA.exe: estaba abierto jugando la tanda 5. Se recompila solo cuando se cierre.
