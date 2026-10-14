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

## Próximo paso
Elegir la tecnología (Python con interfaz y empaquetado a .exe es lo natural, porque reutiliza tanda.py) y
armar una primera versión con lo pedido por el usuario más la partida en curso y la tabla en vivo.
