# Entrenamiento de la IA de los bandos — plan

Estado al 13/10/2026: spec en specs\ia-destrezas-v1.md; base de pruebas empezada (IA.INI y registro por turno).

## Objetivo (pedido del usuario)
Que la IA resuelva mejor los problemas y recuerde estrategias, no solo que reciba más recursos.
Lo que valga para single player vale para multi player (la IA es la misma).

## Hechos de partida
- La IA es código x86 dentro de Darklord.exe (1997): sin red neuronal ni pesos. Todo cambio es un parche binario
  (parches\vista-aliada\build.py: ai_move, ai_conv, ai_free...). Un modelo externo no puede decidir jugada a jugada.
- Se puede ejecutar código real del juego sobre el estado de un .SAV con unicorn (prueba_emulada.py, prueba_ia*.py).
- PC: Ryzen 5 5600G, 47 GB RAM, RTX 5050. El límite es la cantidad de partidas, no el cálculo.
- Según el usuario: no se pueden correr partidas simultáneas en la misma PC; un turno humano dura 5 a 10 minutos.
  Confirmado por el usuario (13/10/2026): Darklord.exe original juega una partida con los 8 bandos en IA; sigue
  corriendo minimizado, con turnos indefinidos; hay una interrupción ("Interrupt Game" en DATA\War3.RES) que pausa
  y permite pasar cualquier bando a humano para revisar la partida. La tecla no está confirmada: en el exe, la
  rutina de espera 0x417470 corta con Escape (evento 5, tecla 0x1b, si [0x50269c] & 1) o con un clic (eventos
  0xb/0x13/0x14, si [0x50269c] & 2), pero no se verificó que sea esa la interrupción. Prueba en TAREAS.md.
- Grabar sin intervención humana: lo resuelve el propio parche (el exe escribe su registro y, si hace falta,
  un .SAV por turno con nombre fijo). No depende del diálogo de grabar.
- Corrección (usuario, 13/10/2026): los .PGS definen el bando (regulares, aliados, orden, oro, stack, maná, héroes,
  barcos), no la personalidad. Los puntos de personalidad los reparte la propia IA al arrancar ("AI Chooses
  Personalities"); el anfitrión solo fija el límite. Cómo los elige es desconocido.

## Material del clan (aportado por el usuario)
- Puntos de personalidad (PGS), con costo: Strong/Very Strong/Herculean (fuerza +1/+2/+3: 1/3/5), Fast/Very Fast/
  Lightning (mov +3/+6/+9: 1/2/3), Informed/Farseeing (visión +2/+4: 1/2), Heroic/Legendary (héroes -40/-80%: 1/2),
  Merchant (ítems -80%: 1), Famous/Renowned (mercenarios -40/-80%: 1/2), Disciplined (producción -1: 4),
  Resolute/Immovable (hits +1/+2: 3/5), Rich/Opulent (ingreso +5/+15 por ciudad: 1/3), Engineer/Artificer
  (ingeniería +2/+6: 1/3), Ceremonial (doble chance de medallas: 2), Devout (todas las unidades benditas: 2).
- Matriz de importancia por fase (arranque/intermedia/final) para mapa visible y mapa oculto, rubros: power, vision,
  move, medal, blessed, desc. hero, desc. mercs, desc. items, engineer, income/city, producción. Lectura gruesa:
  arranque = move, producción, visión (oculto) y héroes; final = power, medal, blessed, income. Las celdas exactas
  hay que transcribirlas con el usuario en la entrevista (vienen en tonos, no en números).
- Habilidades de unidades: combate (Acid, Assassin, Morale, Lightning, Medal, Paralysis, Chaos, Curse, Disease, Fear,
  Poison, Missiles, Life Drain, Leadership, Warding, Banding, Trample, Bless, Siege, Fortify) y de radio (Mana Drain,
  Dispel, Shatter). Dudas marcadas por el clan: el efecto exacto de Chaos, Curse, Disease y Fear.
- Perfiles del clan: https://sites.google.com/view/plagacarriers/perfiles (Agresivo, Agresivo b, Defensivo,
  Económico, Equilibrado; más elegidas; calculador en Google Sheets). El contenido está en imágenes: pedir al usuario
  los puntos de cada perfil o el enlace a la planilla.

## Plan (por etapas; cada una sirve sola, en orden de eficacia)
1. Medir: partida con todos los bandos en IA; tiempo de un turno de IA; ubicar en el exe las constantes de decisión
   (cómo valora ciudades, cuándo ataca, cómo estima una batalla, qué compra).
2. Registro automático: una línea por turno y bando en LOGS\IA.csv (ciudades, ejércitos, oro, batallas, decisiones).
3. Combate exacto: ejecutar la rutina de combate real (emulada) para medir cada habilidad (resuelve las dudas de
   Chaos/Curse/Disease/Fear con datos) y comparar con cómo la IA estima una batalla. Si se equivoca, corregirle la
   estimación: es la mejora de "resolver problemas" más directa.
4. Personalidad de la IA: que cada bando IA elija su PGS según tipo de mapa (oculto/visible) y los perfiles del clan,
   y que su forma de jugar use los puntos que tiene (ej. con Rich/Opulent prioriza ciudades; con Heroic, héroes).
5. Fases: que las prioridades de la IA cambien de arranque a intermedia a final según la matriz del clan.
6. Parámetros en DATA\IA.INI leídos al arrancar. Sin archivo, comportamiento original idéntico (control).
7. Memoria entre partidas: archivo por mapa/escenario con lo aprendido (ciudades clave, pasos y puentes disputados,
   dónde perdió ejércitos). La IA lo lee al empezar y lo actualiza al terminar.
8. Tanda automática (idea del usuario): un programa auxiliar juega N partidas seguidas sin nadie delante.
   Por cada una: arranca el juego, abre una partida nueva con todos los bandos en IA (el parche la inicia sola
   leyendo un archivo de configuración: mapa, semilla, PGS de cada bando, IA.INI a usar; o, si no se puede, el
   auxiliar recorre los menús), la deja correr hasta que haya ganador o hasta un tope de turnos, cierra el juego y
   pasa a la siguiente. Los registros de cada partida van a una base (SQLite, ia\datos.db): partida, parámetros,
   resultado y la línea de cada turno y bando. Si el juego se cuelga, el auxiliar lo detecta por tiempo, lo cierra,
   anota la partida como fallida y sigue.
9. Ajuste por resultados: torneos IA contra IA en mapas chicos, misma semilla, una partida por vez; un optimizador
   propone valores de IA.INI y se queda con lo que gana más. Victoria = criterio final; ciudades/pérdidas = señales.
10. Análisis de partidas humanas (Claude, fuera del juego): patrones de los ganadores convertidos en reglas nuevas.

## Descartado
- Entrenamiento tipo AlphaZero (millones de partidas): el juego no da ese volumen.
- Modelo de lenguaje decidiendo dentro de la partida: el exe no puede consultarlo y la demora sería inaceptable.
- Copiar jugadas humanas por imitación directa: hay pocas partidas; se usan para análisis (etapa 10).
- Partidas simultáneas en la misma PC.

## Avance de la base de pruebas (13/10/2026)
Hecho (build.py, bloque "IA: base de pruebas"; prueba_iaregistro.py, TODO OK en ABN_001-FIN, Aliados01 y hide01;
prueba_emulada.py sigue OK):
- DATA\IA.INI, [IA] Color0..Color7 = original | prueba. Sin el archivo el exe no lee ni escribe nada más.
  Valor inválido = IA original con ia=2 en el registro. Se relee al empezar cada turno. Tabla ia_mode[8] para que
  las destrezas sepan qué color es de prueba (todavía ninguna destreza: "prueba" juega igual que la original).
- Al empezar el turno de cada bando (0x4223ad, antes de turn/0x442470) agrega a DATA\IA.CSV:
  turno, color, ia, vivo, control (-1 humano), oro, ciudades, ejércitos, héroes, s0..s15 (por ranura del bando).
Direcciones verificadas en el código del exe: jugador 0x536b30 + p*0x1f8 (+1 vivo, +0xe2 control, +0xe4 oro);
ciudades 0x537e2c + i*0xde (dueño +0xa5, cantidad [0x537e2a]); ejércitos 0x54fe50 + i*0x1c (vivo +0x13 & 0x40,
palabra +0xe: dueño bits 5-8, ranura bits 0-4, 0x10 héroe); jugador actual [0x537ce8].
Sin verificar en una partida real: turno = [0x503328] (0x420a80 sobre 0x5032f8, el que imprime doComputerTurn) y
que la carpeta de trabajo del juego sea C:\Warlords3 (las rutas son .\DATA\...).
Hallazgo: el exe trae un registro de depuración apagado (0x4e4b90: nivel [0x501024], archivo 0x58d0a0), pero sus
mensajes son casi todos de gráficos; no sirve para la IA.

## Próximo paso
1. Probar en vivo: partida corta con IA.INI y ver DATA\IA.CSV (turno, una línea por bando y turno).
2. Batallas en el registro (atacante, defensor, lugar, composición, resultado): ubicar la rutina de batalla.
3. Fin de partida y cartel "Game Over" (VPs, podio): ubicarlo en el exe (req. 5).
4. Auxiliar de tandas (Python): arrancar el juego, iniciar partida (menús o parche), vigilar cuelgues, pasar
   DATA\IA.CSV a ia\datos.db, rotación de colores, informe.
Frase para retomar: "Seguimos con specs\ia-destrezas-v1.md: base de pruebas".

### 13/10/2026 (2)
- Probado en vivo: el registro por turno funciona (IA.CSV, turnos 1-4). Interrumpir la partida: Tab + clic.
- Registro de batallas hecho (vista-aliada 1.0.28.0): ia_bat reemplaza la llamada 0x469f54 -> 0x465c80 y agrega a
  DATA\IA_BAT.CSV turno, atacante, defensor, x, y, ciudad, resultado, ia de cada uno, cantidades antes y vivos
  después, y ranuras s0..s16 de cada lado. Probado emulado (prueba_iaregistro.py); falta la prueba en vivo (TAREAS).
- Próximo: fin de partida (PV y podio, empates), después el programa de tandas.

## Para investigar (pedido del usuario, 13/10/2026)
- **Héroe vivo de nivel más alto**: registrarlo por bando (en IA.CSV y en el resultado final) y usarlo como
  puntaje adicional del podio en una mejora del parche. Falta averiguar dónde guarda el juego el nivel del héroe
  (registro del ejército 0x54fe50 + i*0x1c o una tabla de héroes aparte).

### 13/10/2026 (3): tandas (vista-aliada 1.0.29.0)
- Hecho:
  - PV y podio documentados en ia/puntos-de-victoria.md.
  - Partida en vivo: IA_BAT.CSV registró 60 batallas.
- Parche:
  - ia_menu: en 0x452c3b, el menú del arranque. Con [Tanda] Partida=<nombre> en IA.INI, carga SAVES\<nombre>.SAV
    con 0x4b9c10, la misma rutina que usa el diálogo Load.
  - ia_fin: en 0x482fd6, dentro del cartel Game Over. Escribe el podio en DATA\IA_FIN.CSV con estas columnas:
    turno, orden, puesto (-1 = empate), color, ia, PV, ciudades, oro.
  - Probado emulado con prueba_iaregistro.py, todo OK.
  - Sin probar en vivo: que la carga desde el menú funcione, y si ia_fin se repite al redibujar. tanda.py se queda
    con el primer bloque.
- ia/tanda.py:
  - plan con pares de asignaciones complementarias;
  - vigila el cuelgue (sin turnos nuevos) y el tope de turnos;
  - pasa los registros a ia/datos.db y borra los CSV;
  - si quedaron registros de una partida jugada a mano, los guarda como partida "suelta".
- ia/informe.py: informe de la tanda. Probados los dos con los registros reales de la partida del 13/10.
- Falta: las 3 partidas guardadas y la primera tanda en vivo (TAREAS.md).
- Después de eso vienen las destrezas.
- Frase para retomar: "Seguimos con specs\ia-destrezas-v1.md: base de pruebas (resultado de la primera tanda)".
- 1.0.30.0, ia_compu en 0x42237a. Según el usuario, con todos los bandos en Computadora la interrupción no deja guardar,
  así que las partidas de la tanda se guardan con un bando en Humano. Si la partida se cargó por [Tanda], al elegir
  cada turno los bandos con +0xe2 = -1 pasan a 2, igual que el diálogo en 0x40a5df. Probado emulado; falta en vivo.

### 14/10/2026: primera tanda (tanda 1 en ia/datos.db)
- Partidas: Scarpart OPOPOPOP, Scarpart POPOPOPO y Borderlands OPOPOPOP. Las 3 terminaron ok, 30 turnos cada una,
  de 23 a 27 minutos.
- Las partidas guardadas son Tanda_Scarpart, Tanda_Borderlands y Tanda_Kor. Hexagon y TomeLand no admiten 8 bandos.
- Funcionó en vivo:
  - carga por [Tanda];
  - bandos guardados en Humano pasados a Computadora;
  - podio en IA_FIN.CSV;
  - importación e informe.
- Problema: cada partida esperaba al botón Single Player. La carga la atiende la pantalla de un jugador. Corregido
  en 1.0.31.0: ia_menu llama a 0x443980, lo mismo que hace el botón, antes de pedir la carga. Falta probarlo en vivo
  (TAREAS.md).
- La IA de prueba todavía es igual a la original. Las diferencias del informe (PV 9,8 contra 7,9) son ruido de
  colores y mapas: sirven de medida de cuánto varía el resultado sin ningún cambio. Con 3 partidas no dicen nada
  todavía.
- Pedido del usuario: antes de tandas largas (20 partidas), elegir el monitor donde se abre el juego, con la misma
  lógica de "Votacion". Va en una sesión aparte.
  - Frase para retomar: "Seguimos con ia/PENDIENTE-entrenamiento-ia.md: elegir monitor para el juego".
  - Después de eso: "Seguimos con specs\ia-destrezas-v1.md: base de pruebas (resultado de la tanda sin tocar nada)".

### 14/10/2026: monitor del juego (hecho)
- `python ia\tanda.py monitor` (o `ia\monitor.bat`) lista los monitores y guarda el elegido por nombre en
  `ia\tanda.ini` (no versionado), como Votación. Si ya no está conectado, se usa el principal. Si no hay ninguno
  guardado y hay más de un monitor, `nueva`/`seguir` lo preguntan al empezar.
- El juego corre en ventana (dxcfg): tanda.py la lleva al monitor elegido y le da su tamaño. Lo comprueba cada 5 s
  porque el juego cambia de ventana (lanzador 600x400, después la de juego del tamaño del monitor donde arrancó).
  Probado en vivo en los monitores de 1024x768 y 1366x768: la partida se ve completa, escalada.
  **Pero el mouse no funciona ahí** (lo vio el usuario; medido 14/10/2026 con SetCursorPos y captura): el juego toma
  la posición del mouse relativa al monitor PRINCIPAL, sin importar dónde esté la ventana (con o sin cambiarle el
  tamaño). En un monitor a la izquierda el cursor queda pegado al borde izquierdo. Es del ddraw.dll de GOG; mover la
  ventana no sirve. Vías: que el monitor elegido pase a ser el principal mientras dura la tanda, o cambiar el ddraw.
- Tanda_Kor no juega sola: carga en el turno de un bando Humano y queda esperando (3 min sin turnos, medido sin
  tocar la PC). Scarpart sí (turnos desde el primer minuto). Kor no se usó en la tanda 1.
- Hallado al probar: la entrada sola a "Single Player" de vista-aliada 1.0.31.0 (ia_menu -> 0x443980) NO funciona
  en vivo: con [Tanda] el lanzador quedó 90 s quieto, con la ventana movida o sin mover. tanda.py ahora aprieta el
  botón (WM_COMMAND id 1001 al lanzador) y así entra y carga la partida (probado con Tanda_Kor). El llamado de
  ia_menu queda sin efecto; revisarlo o quitarlo cuando se toque el parche. (Después se vio que la ventana blanca y
  el lanzador quieto podían venir del aviso de poco espacio en disco, ver abajo.)
- Siguiente: "Seguimos con specs\ia-destrezas-v1.md: base de pruebas (resultado de la tanda sin tocar nada)".

### 14/10/2026: tanda en segundo plano y en el monitor secundario (vista-aliada 1.0.32.0)
Pedido del usuario: que las partidas corran solas en un monitor secundario, en segundo plano, mientras usa la PC.
Probado en vivo con Tanda_Scarpart: la ventana estaba en DISPLAY6 y el Bloc de notas tenía el foco. IA.CSV creció
durante 60 s seguidos y la captura mostró la partida en el turno 5.
- Ventana blanca al arrancar: la causaba el WM_COMMAND al botón Single Player. tanda.py ahora le manda
  WM_LBUTTONDOWN/UP al botón (PostMessage), sin foco ni mouse.
- "You are low on disk space": el juego calcula el espacio libre en 32 bits (0x4e0770) y con decenas de GB libres se
  desborda. Según lo que haya libre, avisaba al arrancar y esperaba un clic: el juego no se veía y la tanda no
  cargaba nada. El parche lo deja en 2 GB si GetDiskFreeSpaceA respondió.
- Turno del bando Humano al cargar (Scarpart y Kor): ia_compu solo actúa al elegir el bando siguiente. ia_tload, en
  OnIdle (0x4ecf10), una sola vez con [Tanda]: si el bando del turno está en Humano, llama a 0x4c0ca0, el fin de
  turno del jugador (0x485c00 + 0x4c0690). Ese bando pierde su jugada del turno 1; los demás turnos los juega la IA.
  No sirvió 0x4221a0(0): vuelve a empezar el mismo turno y queda en modo humano. 0x4212b0 es el que pasa al bando
  siguiente.
- Sin foco: ia_bg (0x4ed415) saltea la pausa de WA_INACTIVE con [Tanda].
- Queda: al arrancar cada partida, el juego toma el foco un instante, hasta que tanda.py lo lleva al monitor. El
  mouse en el monitor secundario sigue sin andar (ddraw), pero para la tanda no hace falta.


### 14/10/2026: observaciones del usuario (partidas en Scarpart)
- Rojo, con su bando personalizado (barco landcraft.arm), usa bien el bono `landing`: el héroe desembarcó en
  costas sueltas en los primeros turnos, posiblemente por una misión.
- Ninguna IA derribó un puente todavía, ni por misión ni para perjudicar. ai_brraze (build.py, "la IA derriba un
  puente por criterio propio") exige c + s >= 5 y puentes de ciudades hostiles sin ejércitos encima; puede que casi
  nunca se cumpla. Nada lo registra hoy: sumar un contador de derribos (por misión y por criterio propio) al
  registro por turno antes de evaluarlo.
- Scarpart: naranja muere siempre y celeste suele ganar, con cualquier IA. Esos colores casi no informan en las
  comparaciones; medir por color y mapa qué colores tienen resultado fijo y darles menos peso.

### 14/10/2026: bandos uniformes desde la próxima tanda
Decisión del usuario: en las pruebas, los 8 colores juegan con el mismo .PGS, para que las diferencias vengan de
las decisiones de la IA y no del armado. Las partidas Tanda_* se rehacen con los mismos nombres (TAREAS.md).
- Las tandas 1 a 5 de ia\datos.db se jugaron con bandos distintos por color. Se conservan, pero no se mezclan con
  las nuevas en un mismo informe: el nombre de la guardada es igual en ambas, lo que las separa es el número de
  tanda (o la fecha de inicio).
- Cada tanda registra su parche en datos.db (tanda.parche = número de vista-aliada de parches\parches.txt,
  tanda.exe = huella sha256 de DarklordAV.exe, 8 caracteres). Retomar una tanda con otro exe se niega. Una etapa
  del cronograma se juega entera con el mismo exe; un cambio a la IA abre etapa nueva.
- Cargado a mano: tandas 4 y 5 = 1.0.32.0, exe 9d706a67 (el exe instalado es del 14/10 11:27, antes de la tanda 4).
  Tanda 1 = 1.0.30.0, deducido de las fechas de los commits (1.0.30.0 a las 23:53 del 13/10, 1.0.31.0 a las 01:54
  del 14/10, tanda a las 00:22); su huella no se puede saber.
- Cronograma acordado con el usuario (14/10/2026): tandas 6 a 20, todos contra todos, mismo bando en los 8
  colores, 3 mapas. Tandas 21 a 40: un solo mapa (las 20 tandas en el mismo, decidido por el usuario) y un solo bando, para estudiar las posiciones (Scarpart, hecho por
  el usuario, tiene posiciones muy malas y muy buenas). Después, modalidades (Crusade, norte contra sur), cada una
  en su tanda y con todo lo demás igual.
  Etapa "medir bandos PGS" (después de la 40): objetivo propio, saber qué .PGS ganan más y cuáles menos, valga o no
  para mejorar la IA. Varios .PGS distintos rotando por todas las posiciones de un mismo mapa, la misma IA en todos
  los colores. Antes hay que registrar en datos.db qué .PGS jugó cada color (ia\PENDIENTE-monitor-ia.md).
- Bandos verificados dentro de los .SAV (14/10/2026, 16:25-16:28, rehechas por el usuario): Tanda_Scarpart,
  Tanda_Borderlands y Tanda_Kor tienen las mismas 16 unidades en los 8 colores. Control: ABN_000_29.SAV da
  "distintos". tanda.py lo anota solo en tanda.bandos desde la versión que sigue a Monitor-IA.exe de las 16:15; si la
  tanda 6 se larga con ese exe, su columna bandos se carga a mano con lo verificado acá.

### 16/10/2026: cierre de la etapa 1 (tandas 6 a 16)
- 96 partidas válidas (32 por mapa), todas vista-aliada 1.0.32.0 exe 9d706a67, bando común verificado. Las tandas 9
  y 16 tuvieron 18 y 24 partidas; la 14 tuvo una cortada y repetida.
- La IA de prueba todavía es igual a la original, así que la etapa fue una prueba de control (las dos IA iguales):
  ganadores 47 prueba, 45 original, 4 empates; diferencia de PV medio por partida 0,0 ± 1,2 (IC 95 %), 47 partidas
  mejor y 47 peor. El banco no favorece a ningún lado. Ruido medido: con 96 partidas se detecta una diferencia de
  ~1,2 PV (el 20 % de la spec, sobre PV medio ~6); para diferencias menores hacen falta más partidas.
- Efecto de la posición muy fuerte (color = posición de arranque). Gana: Scarpart color 7 47 %, color 5 28 %;
  Borderlands color 6 47 %, color 0 25 %; Kor color 0 50 %, color 2 25 %. Hay posiciones con 0 a 3 % de victorias.
  Con las dos IA iguales, estas partidas ya valen para las chances por posición de los 3 mapas.
- La tanda 17 (16/10, 12:20) se largó con la misma condición: cuenta como etapa 1 (control).
- Cronograma corrido: la etapa 2 (posiciones, Scarpart, 20 tandas) empieza en la tanda que siga a la 17.
- Choque a cuidar: programar la IA de prueba recompila DarklordAV.exe en C:\Warlords3 y cambiaría el exe a mitad
  de la etapa 2. Mientras corra la etapa 2, build.py va a otra carpeta (python build.py <carpeta>) y se instala
  recién entre etapas. Con la IA ya cambiada, se repite la etapa 1 (mismas 3 partidas) y se compara con este control.
- Frase para retomar la IA: "Seguimos con specs\ia-destrezas-v1.md: programar la IA de prueba".
- Numeración de colores (verificada 16/10/2026): el "color" de IA.CSV y datos.db es el índice del registro de jugador
  (0x536b30 + p*0x1f8). En el .SAV esos registros traen el estandarte de cada uno: 0 Bwhite, 1 Byellow, 2 Borange,
  3 Bred, 4 Bgreen, 5 Bblue, 6 Bcyan, 7 Bblack (Tanda_Scarpart.SAV, desde 0x32bb9). Mismo orden que "Scenario Sides"
  de War3Ed.RES: 0 blanco, 1 amarillo, 2 naranja, 3 rojo, 4 verde, 5 azul, 6 celeste, 7 negro.
- Scarpart, negro (7): con su bando propio murió en las 6 partidas de las tandas 1, 4 y 5; con el bando común gana
  el 47 %. Según el usuario, su bando propio tiene voladores y el común no, y en Scarpart eso decide.

### 16/10/2026: cambio de plan del usuario, rating de posiciones por mapa
- Scarpart queda medido con las 32 partidas de la etapa 1: no se hacen las 20 tandas de la etapa 2.
- En adelante, un grupo de tandas por mapa (editados por el usuario y originales del juego), bando común, unas 30
  partidas por mapa. Objetivo: rating de mejores y peores posiciones, para ganar y para sobrevivir. Los cuadros se
  publican en la página del Clan, uno por mapa.
- Mientras dure el rating, DarklordAV.exe no cambia (la IA de prueba sigue igual a la original): si cambiara, los
  mapas medidos antes y después no serían comparables. Programar la IA se hace compilando en otra carpeta.
- Un mapa con menos de 8 lugares: tanda.bandos() da "?" (espera 8 colores); revisar a mano o ajustar si aparece.

### 16/10/2026: etapas 1 y 2, y plan de la etapa 3 (alianzas)
- Etapa 1 cerrada (tandas 6 a 17). Etapa 2 probada en 3 mapas (Scarpart 32, Borderlands 34, Kor 33 partidas) y el
  PDF sale completo; sigue abierta para el resto de los mapas. Faltan las posiciones de arranque de Borderlands y Kor
  en posiciones.json.
- Corrección del usuario (16/10/2026): la etapa 3 no es de modalidades sino de alianzas: medir si la IA nueva arma
  mejor las alianzas que la original, en concreto si refugia ejércitos en las ciudades compartidas de un aliado y si
  defiende en común una ciudad sitiada. Crusade y demás modalidades pasan a segundo plano.
- Hecho comprobado: la IA de prueba todavía no tiene ninguna destreza (build.py, comentario de IA.INI: "con prueba
  juega igual que la original"). Las ciudades compartidas son una regla del parche que ambas IA pueden usar al mover,
  pero ninguna la busca a propósito. Hoy una tanda original contra nueva daría empate por construcción.
- Plan de la etapa 3:
  1. Registro: matriz diplomática por turno (DIPLO = 0x55ee4c) y eventos de refugio: pila de un color que entra o
     termina el turno en una ciudad compartida de otro, y batallas en ciudad compartida con defensores de más de un
     color (IA_BAT ya trae atacante/defensor; falta el color de cada defensor). Cambia el exe: entre etapas.
  2. Control: tandas con alianzas fijas (dos equipos de 4, ciudades compartidas y diplomacia activadas), las dos IA
     iguales. Mide cuánto refugio usa hoy la IA original sin proponérselo.
  3. Programar la destreza en la IA de prueba (spec nuevo): refugiarse en la ciudad aliada cuando la pila está
     amenazada, y reforzar una ciudad compartida sitiada. Solo para colores con ia_mode = prueba.
  4. Tandas A/B: un equipo de 4 con la IA de prueba contra uno de 4 con la original, alternando qué equipo tiene
     cada IA en pares complementarios (como la etapa 1). Mide refugios, defensas en común, ciudades compartidas
     perdidas, aliados vivos y equipo ganador, contra el control del paso 2.

### 16/10/2026: verificar que la IA usa las mejoras del juego (puentes, convoy, Landing)
- Pedido del usuario: comprobar en las tandas si la IA derriba puentes y forma convoyes. Visualmente no vio
  ningún derribo ni convoy; sí un héroe desembarcando con landcraft.arm en Scarpart (rojo con bando x-12).
- Las tres cosas están en el parche para TODA la computadora, original y de prueba (no dependen de ia_mode):
  ai_brraze (derribo, build.py ~4998), ai_move/ai_conv (convoy y partir el grupo al embarcar, 1.0.25.0, ~5286).
- Hoy no se pueden verificar desde datos.db: IA.CSV, IA_BAT.CSV e IA_FIN.CSV no anotan derribos ni convoyes.
- Por qué pueden ser raros aunque anden: el derribo exige c + s >= 5 (temperamento + ciudades hostiles cercanas) y
  un puente sin nadie encima que no esté en su camino; ai_conv solo cuando el grupo no entra en un barco y hay otro
  barco propio con "Carrier" en la casilla vecina yendo al mismo destino.
- Plan: DATA\IA_EVT.CSV (turno, color, ia, tipo, x, y), tipos: puente derribado (ai_brraze), convoy ordenado
  (ai_conv), grupo partido al embarcar (ai_move), puente reconstruido (ai_brrebev). Tabla `evento` en datos.db y
  conteo por tanda en el Monitor. Solo anota, no cambia decisiones; probarlo en unicorn igual que prueba_iarazea.py.
- Cambia el exe: va en el mismo exe que el registro de alianzas (etapa 3), instalado entre etapas, cuando el
  usuario cierre el grupo de mapas en curso. Así la etapa 2 sigue con un solo exe.

### 16/10/2026: etapa 3, paso 1 hecho: registro de alianzas, refugios, puentes y convoyes (vista-aliada 1.0.33.0)
- Instalado en C:\Warlords3 y publicado (16/10/2026): el usuario deja la etapa 2 para otro momento y sigue con la 3.
  Solo anota (con DATA\IA.INI); no cambia decisiones.
- DATA\IA_DIP.CSV (tabla `diplo`): por color y turno, `turno,color,opciones,d0..d7`. opciones: 1 ciudades
  compartidas, 2 diplomacia, 4 Hidden Map, 8 vista aliada. dN: 0 aliados, 1 paz, 2 guerra con el color N.
- DATA\IA_EVT.CSV (tabla `evento`): `turno,color,ia,tipo,x,y,n`. Tipos: 1 puente derribado por criterio propio
  (ai_brraze, n = c+s), 2 convoy (ai_conv, x,y destino, n = ejército), 3 grupo partido al embarcar (ai_move, x,y
  del líder, n = cuántos), 4 puente reconstruido (ai_brreb, n = costo), 5 refugio (pila en ciudad compartida de
  otro color, n = ejércitos), 6 puente derribado por misión (ai_brq).
- Refugio: se mide al empezar el turno del dueño de la pila (donde terminó el turno anterior). Entrar y salir de la
  ciudad en el mismo turno no se anota.
- IA_BAT.CSV: columna nueva al final `colores_d` (máscara de bits de los colores defensores). tanda.py acepta filas
  viejas (sin la columna, queda NULL) y agrega la columna a datos.db si falta. El Monitor cuenta eventos por tipo.
- Probado emulado (prueba_iaregistro.py, unicorn) con ABN_001-FIN, Aliados01, hide01 y Tanda_Scarpart: TODO OK.
  Falta la prueba en vivo (TAREAS.md).
- Próximo paso: etapa 3, paso 2 (tandas de control con alianzas fijas). Para retomar:
  "Seguimos con PENDIENTE-entrenamiento-ia.md, etapa 3 paso 2: tandas de control con alianzas fijas".

### 16/10/2026: etapa 3, paso 2 preparado (tandas de control con alianzas fijas)
- Ninguna guardada existente sirve: todas sin alianzas, o de 2 bandos (Aliados01-03, hide01), o crusade01 (1 contra 7).
  Las partidas las arma el usuario (TAREAS.md): Tanda_Scarpart_Alianzas y Tanda_Borderlands_Alianzas, bando común,
  compartidas + diplomacia, dos equipos de 4.
- Equipos elegidos con las partidas de la etapa 1 (tandas 6-17): el reparto con la misma suma de PV medio por color.
  Scarpart 0,1,3,5 | 2,4,6,7 (diferencia 0,1); Borderlands 0,2,4,7 | 1,3,5,6 (diferencia 0,2). Kor no tiene
  reparto parejo (color 0 con 13,9 de PV medio): queda afuera.
- tanda.alianzas(guardada) lee del .SAV la matriz DIPLO y las opciones y lo anota en tanda.alianzas (columna nueva),
  p. ej. "equipos 0135|2467; compartidas, diplomacia". Comprobado con crusade01 (equipos 123567), Aliados03 (23) y
  Tanda_Scarpart (sin alianzas; diplomacia).
- Monitor-IA 1.0.3: las guardadas con equipos se muestran "(alianzas)" y no vienen marcadas por defecto, para no
  mezclarlas en un rating.
- Tamaño: 32 partidas (16 por mapa). La primera tanda de 6 hace además de prueba en vivo de 1.0.33.0.
- Para el paso 4 (A/B) los PATRONES de tanda.py tendrán que repartir la IA por equipo, no por color suelto; en el
  control da igual (las dos IA son iguales).
- Medir en el control: eventos tipo 5 por color y turno, batallas en ciudad con colores_d de más de un bit, cambios de
  la matriz diplo durante la partida (si la IA rompe la alianza), equipo ganador.
- Para retomar: "Seguimos con PENDIENTE-entrenamiento-ia.md, etapa 3 paso 2: resultado de las tandas de control".
- 16/10/2026: el usuario armó Tanda_Scar_Alianzas y Tanda_Border_Alianzas (nombres cortos por límite del diálogo),
  las dos con equipos 0,1,3,5 | 2,4,6,7. El juego no tiene equipos al armar la partida: quedaron como PROPUESTAS
  mutuas. Cada fila de DIPLO (56 bytes por color) tiene la tabla vigente en +0..7 y otra en +9..16 (en crusade01 y
  Aliados03 son iguales; aquí la segunda trae 0 con los compañeros). tanda.alianzas lee la vigente, así que dice
  "sin alianzas". El usuario decidió no tocar los archivos: prueba de 1 partida (Scar_Alianzas) para ver en
  IA_DIP si el juego las vuelve vigentes. Si no, la vía es copiar +9..16 a +0..7 en el .SAV (pedirle permiso).

### 16/10/2026: prueba de 1 partida con alianzas (tanda 18, partida 118, Tanda_Scar_Alianzas, 1.0.33.0 exe 3351b46a)
- Las propuestas mutuas se vuelven vigentes solas: IA_DIP turno 2 a medias (cada color al jugar su turno), turno 3
  completas. Los equipos siguieron aliados hasta el turno 30 (entre equipos, guerras a partir de la mitad). No hace
  falta tocar los .SAV.
- Equipo 0,1,3,5: 55 PV, ninguno eliminado; equipo 2,4,6,7: 17 PV, naranja (t20) y verde (t12) eliminados.
- Eventos: 0 refugios, 0 convoyes, 1 puente derribado por misión. 76 batallas, ninguna con defensores de 2 colores.
- CAUSA de cero refugios y de que el usuario no viera banderas dobles: partners() (build.py, "Ciudades compartidas
  por la alianza") exige la opción Hidden Map, y las dos guardadas de alianzas tienen opciones 11 = compartidas +
  diplomacia + vista aliada, SIN Hidden Map. Con el mapa visible no hay ciudad compartida nunca. El usuario pidió
  bajar la exigencia de 4 casillas exploradas a 3; eso no habría cambiado esta partida. Decisión pendiente del
  usuario (regla de juego): partidas con Hidden Map, o que con mapa visible las ciudades aliadas se compartan sin
  exigir exploración; y si igual baja a 3 casillas.
- Observaciones del usuario: (1) Scarpart tiene las ciudades en grupos muy alejados; para alianzas sirve más
  Borderlands (más apretado) o más turnos. (3) En Tanda_Scar_Alianzas los colores arrancan en otras ciudades que en
  Tanda_Scarpart (verificado en los .SAV: Scarpart sortea la ciudad inicial de cada color en cada partida nueva;
  Borderlands no, las capitales son las mismas). El rating de posiciones de Scarpart vale solo para Tanda_Scarpart.
  (4) El X-12 ahora trae la lancha rápida (cabotaje) y la IA parece usarla bien respetando la limitación.
- La partida 117 "(a mano)" son 2 turnos que quedaron de armar las guardadas.

### Estado al 16/10/2026 (fin de sesión)
- vista-aliada 1.0.34.0 publicado e instalado: ciudades compartidas también con mapa visible (prueba_compartidas.py TODO OK).
- La tanda 18 (partida 118) fue solo prueba; no entra en el control.
- `tanda.alianzas()` ahora distingue vigentes de propuestas ("equipos ... (propuestas)").
- Próximo paso: tanda de 6 con Tanda_Border_Alianzas (TAREAS 1, paso 5); revisar refugios y defensores de varios colores.

### 17/10/2026: tanda 19 de control (6 partidas, Tanda_Border_Alianzas, vista-aliada 1.0.34.0, exe 6e1cc74e)
- El usuario confirmó en vivo las banderas dobles en ciudades aliadas y la suspensión al terminar (TAREAS 2).
- Alianzas 0135|2467 vigentes desde el arranque y nunca rotas en las 6; entre equipos, de paz pasan a guerra (t8-24).
- Refugios (evento 5): 0. Batallas con defensores de más de un color: 0 de 533. Ningún otro evento (puentes, convoyes).
  => la IA original no usa las ciudades aliadas. Límite: el refugio con member real nunca dio positivo en vivo; la
  prueba emulada lo simula, y partners/member están probados por separado (prueba_compartidas.py).
- PV por equipo (0135 vs 2467): 38-13, 2-54, 15-31, 6-50, 4-53, 46-13 -> el equipo 2467 gana 4 de 6. En Borderlands el
  reparto parejo calculado era 0247|1356; el usuario armó 0135|2467 en los dos mapas. Para el control vale igual
  (la prueba A/B usará los mismos equipos), pero la ventaja de 2467 es del mapa, no de la IA.
- Decidido: Scarpart afuera (ciudades muy separadas). Control = 16 partidas en Borderlands: faltan 10 (TAREAS 1, paso 6).
- Para retomar: "Seguimos con PENDIENTE-entrenamiento-ia.md, etapa 3: cierre del control".

### 17/10/2026: tanda 20 de control (6 partidas, Tanda_Border_Alianzas, vista-aliada 1.0.34.0, exe 6e1cc74e)
- Mismo comportamiento que la 19: alianzas 0135|2467 vigentes hasta el final; refugios (evento 5): 0; ningún otro
  evento; batallas con defensores de más de un color: 0 de 522 (colores_d es máscara: más de un bit = varios colores).
- Partida 126 (n=0) colgada en el turno 25: el equipo 2467 ya estaba eliminado (4 en t11, 7 en t16, 2 en t24; 6 sin
  fila en t25) y el juego dejó de registrar turnos tras jugar el color 3. Hipótesis sin verificar: con solo aliados
  vivos el juego no muestra el "Game Over" que espera ia_fin. El informe la descarta; de hecho la ganó 0135 (38-0).
- PV por equipo (0135 vs 2467) de las 5 válidas: 46-19, 26-33, 12-41, 40-14, 13-53 -> 0135 gana 2 de 5.
  Acumulado del control (tandas 19 y 20): 11 partidas válidas, 2467 gana 7 de 11.
- Faltan 5 válidas para las 16: se pide una tanda de 6 (de a pares) en vez de la de 4 (TAREAS 1, paso 7).

### 17/10/2026: tanda del paso 7 en curso (lo que vio el usuario)
- Partida 2: el juego mostró un cartel de «victoria aliada» con un botón Aceptar y se quedó ahí. El usuario lo
  aceptó, pasó al menú del disquete y salió a mano. Confirma la hipótesis de la partida 126: cuando solo quedan
  aliados vivos, el juego muestra ese cartel en vez del «Game Over» que espera ia_fin. Pendiente: que la tanda (o
  ia_fin) apriete Aceptar en ese cartel y cierre sola, para no perder partidas como colgadas. No se tocó el código
  con la tanda corriendo.
- Al arrancar cada partida se oye un momento el juego antes de que el Monitor lo silencie: silenciar() corre cada
  5 s en el bucle de jugar(). Es esperable; si molesta, se puede silenciar apenas aparece la sesión de audio.

### 18/10/2026: tanda 21 de control (6 partidas, Tanda_Border_Alianzas): control cerrado
- Partidas 133 (cortada, t20) y 134 (colgada, t28, solo vivos 0 y 1: otra «victoria aliada» sin atender) perdidas.
  135 la cerró el usuario en el turno 30 tras el cartel: se cuenta con los PV del último turno (22-0, gana 0135).
- PV (0135 vs 2467) de las 5 válidas: 22-0, 17-42, 48-13, 22-52, 47-9 -> 0135 gana 3 de 5.
- Acumulado del control (tandas 19, 20 y 21): 16 partidas válidas, 2467 gana 9 y 0135 gana 7. Refugios (evento 5):
  0; ningún otro evento; batallas con defensores de más de un color: 0 en las tres tandas.
- Conclusión del paso 2: la IA original no se refugia ni defiende en común. Sigue el paso 3 (spec de la destreza en
  la IA de prueba) y, antes de las tandas A/B, que la tanda apriete Aceptar en el cartel «victoria aliada».
- Sonido: después de la tanda el juego abre sin silencio (medido con medir_mute leer). Monitor-IA 1.0.5 anda.

### 18/10/2026: cartel «victoria aliada» atendido (vista-aliada 1.0.35.0, exe b392b261)
- Causa, leída del exe: la rutina de fin 0x482570 abre el mismo cuadro (diálogo 0x2b, init 0x482c10) con la bandera
  de victoria [0x571760] (aliada si [0x571758]) y sin Game Over ([0x57175c] = 0): textos 0xd3 de Sagetext ("Victory!
  / An allied victory!"), sin podio. ia_fin está dentro del podio (0x482d70), así que nunca corría; después de
  Aceptar la partida sigue.
- Parche ia_vic (call 0x482c10 en 0x482790): con IA.INI, victoria y sin Game Over, calcula los PV con 0x440840 y
  agrega a DATA\IA_VIC.CSV una línea por bando en juego: turno, color, ia, PV, ciudades, oro.
- tanda.py: IA_VIC.CSV con datos = fin "ok" (cierra el juego, no espera el cuelgue); orden y puestos con la regla del
  podio por PV (empate = mismo puesto, guardado como -1 igual que ia_fin); vale el primer cartel.
- Probado: prueba_iaregistro.py (nuevo caso "victoria aliada", PV recalculados con la fórmula; con Game Over, sin
  victoria y sin IA.INI no escribe) TODO OK en Tanda_Border_Alianzas, ABN_001-FIN, Aliados01, hide01 y
  Tanda_Scarpart, contra el exe instalado. importar() probado en juguete (empate en el 2.º puesto, eliminado, CSV
  borrados). Falta verlo en vivo: la primera tanda de alianzas que termine con solo aliados vivos.
- Límite: el podio del juego ordena por la condición de victoria del escenario ([0x560e52]); ia_vic/tanda ordenan
  siempre por PV. Las tandas usan PV (condición 0), así que coincide.

### 18/10/2026: etapa 3, paso 3: spec escrito (specs/ia-alianzas-v1.md)
- Entrevista con el usuario: motivos de refugio (enemigo más fuerte a un turno, pila débil tras batalla, héroe con
  misión de cazarla), salidas, quedarse hasta el final, refuerzo de ciudad aliada (a tiempo, o importante y aguanta;
  5 criterios de importancia). La IA usa todo lo que sabe (sin limitar visión por ahora).
- Medición: táctica, batalla por batalla; qué alianza gana se registra como dato secundario "con pinzas".
- Próximo paso: construir según el spec, empezando por las preguntas abiertas (misión del héroe, fuerza de una pila).
  Para retomar: "Seguimos con specs/ia-alianzas-v1.md: construir la destreza de alianzas".

### 18/10/2026: etapa 3, paso 3: destreza de alianzas construida (vista-aliada 1.0.36.0)
- ai_ally (gancho en 0x40edf1, la decisión de cada pila de la IA): refugio (1a/1b/1c, salidas 3a/3b, req. 4 y 5) y
  refuerzo de ciudad aliada (6a/6b con el criterio 7a). Detalle, umbrales y aproximaciones en specs/ia-alianzas-v1.md,
  sección «Construcción». Eventos nuevos 7-13 en IA_EVT.CSV; 11/12 (pila amenazada y si sobrevivió) para las dos IA.
- Probado emulado: parches/vista-aliada/prueba_iaalianzas.py (Tanda_Border_Alianzas, equipos y guerra armados en la
  prueba) TODO OK; las demás pruebas del parche siguen OK. Bug encontrado por la prueba: la tabla usaba turno 0 como
  «sin dato» y la tanda arranca en el turno 0 (se guarda turno + 1).
- Hallazgos para la emulación: 0x497240 (formar grupo) llama a rutinas de pantalla (0x486ab0, 0x4868d0) y 0x4974a0
  termina en _ftol; en la prueba van con stubs. En el SAV de turno 0 solo viven los héroes y 55 neutrales (las listas
  de pilas traen ejércitos viejos, más allá de la cantidad [0x54fe50]).
- tanda.py: con equipos en la guardada, la IA se reparte por equipo en pares complementarios (req. 13), probado en
  juguete; Monitor de IA 1.0.6. informe.py: sección «Alianzas» (req. 12 a-f), probada sobre las tandas 19-21 (sin
  eventos: en blanco; batallas con defensores de más de un color: 0).
- No construido: criterios 7b-7e (no ubicados en el exe); la tabla de refugios no se guarda con la partida.
- Próximo paso: tanda A/B en vivo (TAREAS 21) y su informe contra el control.
  Para retomar: "Seguimos con specs/ia-alianzas-v1.md: informe de la tanda A/B".


### 19/10/2026: refuerzo quitado (vista-aliada 1.0.38.0) y clasificación táctica / estratégica
- El usuario quitó el refuerzo de ciudades aliadas (spec de alianzas, req. 6 y 7): es estratégico, no táctico.
- Criterio del usuario: **táctica** = ganar cada batalla individual; **estratégica** = los fines últimos de la
  contienda, en función del criterio de victoria.
- Propuesta de clasificación (pendiente de que el usuario la revise):

| Instrucción | Origen | Clase propuesta |
|---|---|---|
| Refugiarse ante una pila enemiga más fuerte que la alcanza | alianzas 1a | táctica |
| Refugiarse tras quedar débil en una batalla | alianzas 1b | táctica |
| Refugiarse ante un héroe enemigo que viene a cazarla | alianzas 1c | táctica |
| Elegir el refugio alcanzable este turno, lejos de la amenaza | alianzas 2 | táctica |
| Salir del refugio al pasar el peligro o reforzarse | alianzas 3 | táctica |
| Quedarse hasta el final porque un héroe vivo suma PV | alianzas 4 | **estratégica** |
| Quedarse a defender la ciudad aliada atacada donde está | alianzas 5 | táctica |
| Atacar un blanco débil que tiene en el camino | destrezas 8 | táctica |
| No atacar con baja probabilidad de victoria (salvo un sondeo) | destrezas 10 | táctica |
| Tras 2 derrotas, juntar fuerzas y atacar con un grupo superior y distinto | destrezas 11 | táctica |
| … o cambiar de objetivo si el blanco no es vital | destrezas 11 | **estratégica** |
| Ordenar el grupo antes de la batalla según el rival | destrezas 13 | táctica |
| Corregir la estimación de batalla de la IA con el combate real | plan, etapa 3 | táctica |
| Derribar un puente o puerto solo para frenar un ataque inminente | idea del usuario, 18/10 | táctica |
| Un objetivo por grupo (tomar ciudad, reforzar sector, reagrupar) | destrezas 7 | **estratégica** |
| Exploración con fin (una ruina o zona concreta) | destrezas 9 | **estratégica** |
| Armar grupos por cantidad al principio, por calidad al final | destrezas 12 | **estratégica** |
| Destrezas 4-7: economía, cuidado del héroe, reportes y terreno/retirada, salir del aislamiento | destrezas, fuera de alcance | economía y aislamiento estratégicas; héroe y retirada tácticas |
| Elegir el bando (PGS) según el mapa; prioridades por fases; memoria entre partidas | plan, etapas 4, 5, 7 | **estratégicas** |
- Revisión del usuario (19/10/2026): la clasificación es correcta, con estos cambios:
  - Exploración con fin: no tocarla sin cuidado. La IA original ya explora bien, y no se sabe si para la IA el
    mapa oculto es oculto de verdad (verificarlo en el exe antes de cualquier cambio).
  - Cantidad / calidad de los grupos: pasa a **táctica**, redefinida como regla simple: en el primer tercio de la
    partida (por turnos o por tiempo) asegurar cantidad; después, cuidar también la calidad del grupo.
  - Táctica incluye «evitar perder»: sostener una ciudad es siempre buena decisión táctica. Abandonar una ciudad
    defendible es estratégico (excepción), y no se le pide a la IA.
  - Regla nueva propuesta por el usuario: «Siempre defender una ciudad aliada en riesgo inminente de ataque de un
    enemigo común, salvo que eso descuide una ciudad propia también en riesgo.» Respuesta y forma lógica en el
    chat del 19/10. Confirmada por el usuario y programada en vista-aliada 1.0.39.0.
  - Héroe (alianzas 4) redefinido por el usuario como táctico: «un héroe débil se refugia en una ciudad aliada
    mientras a) la ciudad ya esté bien defendida con armas aliadas, b) un héroe enemigo lo persiga para asesinarlo
    y cumplir una misión, y c) el perseguidor esté cerca». Programado en 1.0.39.0; reemplaza al req. 4 y al 1c
    aproximado. Detalle en specs/ia-alianzas-v1.md, «Regla del héroe y defensa de ciudades aliadas».
  - Quedan para después: la regla de cantidad / calidad por tercios, y derribar puentes o puertos solo para frenar
    un ataque inminente. La exploración no se toca hasta verificar si el mapa oculto es oculto para la IA.

### 19/10/2026: idea del usuario, mensajes entre aliados (averiguado el chat nativo)
- El humano le ordena a un aliado de la computadora por chat («atacá la ciudad XX», «atacá al verde», «mandame
  refuerzos»), sin que lo vean los enemigos; y la IA le pide al humano lo que le falta («mandame oro»), sabiendo
  qué le sobra al aliado (fuerzas, oro). Dos partes: a) mandar pedidos; b) recibirlos, interpretarlos y decidir.
- Nada averiguado todavía. Primero: si el chat nativo existe durante la partida en multijugador (teclas, a quién
  llega, si se puede dirigir a un solo color) y dónde lo maneja el exe; si no, ver otra vía (por ejemplo un
  diálogo propio del parche, como los botones de Votación y Sorteo).
- Clasificación (borrador para revisar con el usuario): obedecer una orden concreta del humano es táctico (la
  decisión ya la tomó el humano); decidir qué pedir y si conceder un pedido es estratégico.

**Chat nativo en partida (averiguado en el exe original el 19/10/2026):**
- Ojo: el número que el exe le pasa a 0x4d7980 (abrir diálogo) no es el número de diálogo del RES; se traduce por
  la tabla tipo 6 del RES (entradas de 32 bytes; el 3er campo es el diálogo). Ej.: exe 0x67 -> RES 108, exe 0x6c ->
  RES 74 (Kills Report).
- Diálogo "Multiplayer Chat" (RES 108, exe 0x67, se abre en 0x408a00, manejador 0x408ae0): 9 renglones de historial
  (0x501788, 64 bytes c/u), casilla Mute ([0x4f91b4]), campo Message (control 4) y 7 botones Send (19-25), uno por
  cada bando humano de otra máquina. Cada fila guarda la **máquina** del bando ([0x5019d0+fila], de 0x536b33); el
  botón alterna el byte [0x5019c8+máquina]. **Los bandos de la computadora no aparecen** (solo los que tienen
  0x536c12 == -1, humanos).
- Barra de chat (0x409170, llamada desde 0x473319/0x473335): «#3 texto» va solo al bando 3 (si es humano);
  «#nombre texto» a los bandos humanos cuyo nombre empieza así; sin «#», a los destinatarios marcados con Send.
- Envío 0x4ba990(bando, destinos[8 por máquina], texto): paquete **0x1ac** de 0x4a bytes = bando (word) + 8 bytes de
  destino + texto (hasta 63 caracteres), por 0x4dd3b0 (la misma difusión que usan TL_OPEN/TL_STATE). Llega a todas
  las máquinas; el receptor 0x409040 lo muestra solo si su máquina (0x4dd3a0) está marcada y no tiene Mute: un
  enemigo con el exe original no lo ve. El remitente siempre se incluye (eco).
- Consecuencia: **el chat nativo no puede dirigirse a un aliado de la computadora**, y como esos bandos corren en la
  máquina de algún humano (0x536b33), marcar esa máquina se lo mostraría a ese humano, que puede ser enemigo.

**Diseño propuesto (a programar en vista-aliada):**
- Humano -> IA: ampliar la barra de chat para que «#n texto» con n = bando de la computadora no use 0x1ac sino un
  paquete propio (0x2a2, que un Warlords sin parche descarta, como 0x2a0/0x2a1) con bando de origen, bando destino
  y texto. Lo procesa solo la máquina que corre ese bando; no se muestra a nadie. Ahí se interpreta la orden (lista
  cerrada de órdenes, ver abajo) y se le confirma al humano.
- IA -> humano: la máquina que corre el bando de la IA manda un 0x1ac normal con remitente = bando de la IA y
  destino = máquina del humano aliado; se ve con el sistema nativo, con el color de la IA, sin cambios en el receptor.
- Primeras órdenes (cada una es táctica: la decisión ya la tomó el humano): «atacá CIUDAD», «atacá a COLOR»,
  «mandame refuerzos». Respuestas de la IA: «ok», «no puedo: MOTIVO». Los pedidos de la IA («mandame oro») van
  en una segunda etapa, porque decidir qué pedir es estratégico.
- Respuestas del usuario (19/10/2026): empezar con esas tres órdenes; la clasificación (obedecer = táctico; qué
  pedir y si conceder = estratégico) es correcta. El oro ya se puede pasar a cualquier bando en partida: cuadro de
  Diplomacia, botón «Bribe», que abre un diálogo con barra deslizante para el monto según las reservas (sirve para
  la segunda etapa: la IA concede oro por ese mismo camino).
- Próximo paso: averiguar por dónde meter una orden en el plan de la IA para un turno (los ganchos de alianzas de
  1.0.39.0 son el punto de partida), y luego programar el paquete 0x2a2 y la barra «#n».

**Por dónde meter una orden en el plan de la IA (averiguado en el exe original el 19/10/2026):**
- La decisión de cada pila es 0x40c990(pila, arg), que llama a 0x40ca70(pila, arg). Con arg = 0 (el único llamador,
  0x40edf1, que hoy es ai_ally) la meta la elige el planificador 0x41eda0 (tras puntuar con 0x41cb10). **Con arg != 0
  se saltea el planificador: meta = arg / 1000, objetivo = arg % 1000.** Es una entrada que el exe ya tiene y no usa.
- Metas (tabla 0x40d02c, textos del registro de la IA): 1 ir a una ciudad («Form to City», 0x40db40: va al centro de
  la ciudad, sin mirar el dueño, y al llegar llama a 0x48c510(ciudad, 0), sin averiguar qué hace), 2 ruina, 3 ciudad
  neutral (0x40d9f0(c, 3)), 4 ítem, 5 héroe (0x40dd00), 6 misión, **7 ciudad enemiga** (0x40d9f0(c, 7): anota la meta
  en el registro de la pila, +6 = 7 y +8 = ciudad, se acerca con 0x497830/0x40d2b0 y entrar ataca), 8 sitio
  (0x40d450), 9 reconstruir (0x40dbf0).
- El planificador vuelve a puntuar todo en cada llamada (la meta anotada en +6/+8 no lo ata): una orden que dure
  varios turnos hay que volver a pasarla en cada turno.
- Consecuencia para el diseño: ai_ally ya intercepta cada pila; con una orden vigente para el bando, en vez de
  0x40c990(pila, 0) llama a 0x40c990(pila, meta * 1000 + objetivo). Sin tocar el resto de la IA:
  - «atacá CIUDAD» -> 7000 + ciudad;
  - «atacá a COLOR» -> 7000 + la ciudad de ese color más cercana a la pila (elección del parche);
  - «mandame refuerzos» -> 1000 + una ciudad del humano (la más cercana a la pila, o la amenazada).
  La orden se guarda por bando (tipo, objetivo, turno en que vence) en una tabla del parche, la llena el receptor del
  paquete 0x2a2 y ai_ally la consulta.
- A decidir con el usuario (es comportamiento del juego, no técnica): ¿la orden va antes o después del refugio y de la
  defensa de ciudades aliadas? ¿la cumplen todas las pilas o solo las que llegan en N turnos / parte de la fuerza?
  ¿cuántos turnos dura? Propuesta: refugio primero (supervivencia de la pila), luego la orden; la cumplen las pilas
  que llegan en 3 turnos o menos; dura hasta cumplirse o 5 turnos.
- Próximo paso: con esas respuestas, programar la tabla de órdenes y su uso en ai_ally (probado emulado como
  prueba_iaalianzas.py, con 0x40c990 en stub para ver el arg), y después el paquete 0x2a2 y la barra «#n».
- Respuestas del usuario (19/10/2026): la orden va **primero** (antes del refugio y de la defensa: manda el humano,
  a su costo y riesgo); la cumplen las pilas que llegan en **2 turnos** o menos; **caduca a los 2 turnos**.
- Hecho (vista-aliada 1.0.40.0, sin publicar): tabla de órdenes OR_TAB y ai_ord antes de ai_ally; detalle en
  specs/ia-alianzas-v1.md, «Órdenes del humano». prueba_iaalianzas.py TODO OK.
- Próximo paso: el paquete 0x2a2 (humano -> máquina que corre la IA; llena OR_TAB con 3 turnos) y la barra «#n»
  que interpreta «atacá CIUDAD / atacá a COLOR / mandame refuerzos» y confirma con un 0x1ac de la IA; después
  publicar. (Hecho, abajo.)
- Hecho (vista-aliada 1.0.41.0, 19/10/2026, sin instalar ni publicar): barra «#n» y paquete 0x2a2; detalle en
  specs/ia-alianzas-v1.md, «Dar la orden desde el juego». prueba_chatordenes.py TODO OK. No se instaló en
  C:\Warlords3 porque la tanda de la tarea 21 estaba corriendo con 1.0.39.0 (la 1.0.41.0 no cambia la IA sin
  órdenes, pero pisar el exe en plena tanda la corta).
- Próximo paso: cuando termine la tanda 21, `python parches\vista-aliada\build.py` (instala en C:\Warlords3) y
  `.\tools\publicar-parche.ps1 vista-aliada`; después el usuario prueba en red (TAREAS 22). Pendiente de diseño:
  la respuesta «no puedo: MOTIVO» y la segunda etapa (pedidos de la IA, oro por Bribe). Para retomar: "Seguimos
  con PENDIENTE-entrenamiento-ia.md: instalar y publicar 1.0.41.0".

### 19/10/2026: observación del usuario sobre barcos
- La IA maneja bien los barcos con bono `landing` y con cabotaje; **no así con el bono `carrier`**. Sin averiguar
  todavía qué hace mal (ai_conv solo ordena convoy cuando el grupo no entra en un barco y hay otro barco propio con
  Carrier en la casilla vecina yendo al mismo destino; ver «verificar que la IA usa las mejoras del juego»).

### 19/10/2026: tanda 25, primera A/B válida (8 partidas, Tanda_Border_Alianzas, vista-aliada 1.0.39.0, exe a2927257)
- 8/8 ok, 30 turnos. Equipos alternados 0135|2467 entre IA de prueba (P) y original (O). La serie de 2 (tandas 26
  y 27) no corrió: no hay tandas después de la 25. Desde las 14:17 C:\Warlords3 tiene 1.0.43.0: las órdenes por chat
  no actúan sin humano y los pozos se generan al armar partida (la guardada no trae bloque POZO), así que no cambia
  la prueba; igual el exe queda anotado en la tabla tanda y se compara por esa columna.
- Por color (32 cada IA): P 8.1 PV, 6.2 ciudades, 24.0 ejércitos; O 6.9 PV, 5.0 ciudades, 19.1 ejércitos.
- Por equipo (PV promedio): 0135 con P 26.5 (32, 2, 47, 25) contra 19.3 con O (8, 9, 48, 12); 2467 con P 38.0
  contra 36.3 con O. Victorias: 2467 gana 6 de 8 (cada IA ganó una vez con 0135); en el control 19-21, 2467 ganó 5
  de 9: la ventaja del mapa sigue. Dispersión enorme (2 a 47 PV): con 8 partidas la diferencia no es concluyente.
- Alianzas (tácticas): P registró 18 refugios, 1 salida, 3 defensas desde refugio, 2 defensas de ciudad aliada y 2
  batallas con defensores de varios colores; O, 0 en todo (la IA original no lo hace). Héroes vivos: P 14, O 17;
  amenazados que sobreviven: P 118/157 (75 %), O 136/169 (80 %). Resistencias en compartidas: P 21, O 32.
- Lectura: las reglas nuevas se ejecutan en vivo (antes, en el control, todo en cero). El resultado tiende a
  favor de P en PV y ciudades, pero sin significancia; el refugio no mejoró todavía la supervivencia de amenazados
  ni de héroes. Falta juntar las tandas 26-27 (24 partidas) antes de concluir.

### 20/10/2026: tandas A/B 27 y 28 y cierre de la serie (25, 27, 28: 24 partidas, Tanda_Border_Alianzas)
- La 26 no es de esta prueba (Borderlands/Kor/Scarpart sin alianzas, cortada en la partida 1): se excluye.
  27 y 28: 16/16 ok, exe 832708c1 en las dos (vista-aliada 1.0.43.0/1.0.44.0); la 25 fue con 1.0.39.0 (a2927257).
- PV por color: P 9.1 / O 6.5 (t27), P 6.6 / O 9.0 (t28); con la 25, P 7.9 y O 7.5 en promedio.
- PV por equipo en las 24 (promedio ± desvío): 0135 P 29.8±19.5, O 27.5±18.5; 2467 P 33.5±16.5, O 32.2±21.6.
  Victorias: P 12, O 12. La ventaja del mapa de 2467 se achicó (ganó 4 de 8 en la 27 y en la 28).
- Alianzas sumadas: P 56 refugios, 4 salidas, 8 defensas desde refugio, 9 defensas de ciudad aliada, 4 batallas
  con defensores de varios colores; O 0 en todo. Pero amenazados que sobreviven: P 280/404 (69 %), O 400/505 (79 %);
  héroes vivos al final: P 13.3, O 16.7 por partida.
- Conclusión: las reglas de alianzas se ejecutan; a nivel de bloque, el resultado es neutro (empate en victorias,
  +1.8 PV por equipo, muy por debajo del desvío): ni ganan ni cuestan.
- Corrección del usuario (20/10/2026): la menor supervivencia de amenazados y héroes no se le puede atribuir, aislada,
  a un defecto. Un héroe puede quedarse a defender una ciudad clave, y su caída o la de esa ciudad puede ganar tiempo
  para la alianza en otro sector. Aunque las pruebas sean de reglas tácticas, el balance es siempre estratégico: el
  objetivo es que gane el bloque, no cada color. Esas pérdidas serían un problema solo si vinieran con menos victorias
  del equipo, y no es el caso (12 a 12).
- Próximo paso: no hay defecto que corregir en las reglas de alianzas. Para ver si dan ventaja hace falta más
  muestra o un mapa sin ventaja de un equipo; decisión pendiente de qué sigue.
- Decidido (20/10/2026): repetir la A/B en Hexagon (posiciones y recursos casi iguales; los mapas al azar no igualan
  condiciones). TAREAS 23: el usuario arma Tanda_Hex_Alianzas (dos equipos iguales, menos de 8 bandos). Al recibir
  la primera tanda, verificar que tanda.plan e informe.py se porten bien con colores ausentes (hoy asumen 8).

### 20/10/2026: tandas A/B 29 a 34 en Hexagon (48 partidas, Tanda_hex_alianzas, equipos 013|457, exe df2d19b0)
- 48/48 ok. Colores 2 y 6 no juegan; los datos no tienen filas de ellos (el plan los nombraba: arreglado en Monitor 1.0.9).
- Victorias por equipo: P 20, O 27, 1 empate. PV por equipo: 013 con P 44.8±11.1, con O 47.8±9.6; 457 con P
  31.5±8.5, con O 34.9±10.6.
- Hexagon no quedó parejo con estos equipos: 013 ganó 37 de 48 (margen de 10 a 16 PV). Controlando por equipo
  (margen 013-457 con 013 en P contra 013 en O), el efecto de la IA de prueba es -3.2 ± 2.8 PV por equipo: en contra,
  pero dentro de lo que da el azar.
- Las reglas casi no se disparan en Hexagon: 16 refugios, 4 defensas desde refugio, 2 defensas de ciudad aliada y 1
  batalla con defensores de varios colores en 48 partidas (en Borderlands: 56, 8, 9 y 4 en 24).
- Conclusión, sumada a Borderlands (+1.8 PV, 12 a 12): las reglas de alianzas no muestran ventaja para el bloque;
  en Hexagon tienden levemente en contra sin significancia, y se activan tan poco que no pueden explicar mucho de la
  diferencia. Decisión pendiente del usuario: seguir con otra destreza o revisar por qué casi no se activan acá.
- Decisión del usuario (20/10/2026): reducir el azar. Bando simple (sin maná, mismo héroe y regulares en todos los
  colores), Hexagon, sin ruinas (TAREAS 24). Las ruinas de Hexagon tienen contenido, guardián y «oculta» distintos
  entre sí (47 ruinas), así que desbalancean aun con el mapa simétrico.
- Las ruinas las quita el usuario desde las opciones de la partida (ia\sin_ruinas.py se descartó).
  **Corrección del usuario (21/10/2026):** el juego no tiene opción «sin ruinas», solo «sin ruinas ocultas» (Hidden
  Ruins apagada). La tanda en curso corre **con las 47 ruinas de Hexagon, todas visibles**: el azar de su contenido
  y guardián sigue ahí. (Con Hidden Ruins apagada tampoco hay pozos ni remolinos.) Si hace falta quitarlo, la vía
  es la descartada: sacar las ruinas del mapa o igualarlas.
  **Retomado (21/10/2026):** ia\sin_ruinas.py vuelve (del commit e7aff43): de la guardada arma
  SAVES\<guardada>_SR.SAV con las 47 ruinas exploradas, vacías y sin guardián, sin tocar el mapa ni la original.
  Ya armada: Tanda_hex_alianzas_SR.SAV (verificado: 47 de 47). Se usa en la próxima tanda.
- Ojo, dos límites que el bando simple no resuelve: (1) los equipos 013|457 no quedaron parejos en Hexagon (013
  ganó 37 de 48); el A/B lo compensa alternando, pero suma varianza. (2) las reglas de alianzas se activaron muy poco
  en Hexagon (16 refugios en 48 partidas): con menos azar se mide mejor, pero si casi no se activan el efecto
  seguirá siendo chico.
- (21/10/2026) El usuario armó la partida con el bando simple, pero la guardó sobre **Tanda_hex_alianzas** (no como
  Tanda_hex_simple): bando nuevo sin maná, casi el mismo héroe, mismos bandos, sin ruinas ocultas (no «sin ruinas»: ver la corrección de arriba), dos grupos de aliados
  intercalados en ubicación (el usuario confirmó que quedaron intercalados igual que antes: 013|457).
  Próximo: revisar el SAV y armar la tanda nueva (TAREAS 25).
- (21/10/2026) Revisión del SAV con tanda.bandos/alianzas:
  - Alianzas: 013 vigente, 457 solo propuesta (se guardó antes de que jugaran). tanda.alianzas leía solo la vigente
    y daba «equipos 013»: el plan habría caído en los PATRONES de 8 colores. Arreglado (cuenta vigentes y
    propuestas) en Monitor 1.0.10; ahora da «equipos 013|457; compartidas, diplomacia».
  - Bandos: tanda.bandos daba «?» porque exigía datos en los 8 colores (2 y 6 no juegan). Arreglado: solo cuenta
    los colores que juegan. Resultado: **distintos**. Los colores 1, 3, 4, 5 y 7 son idénticos; el blanco (0)
    tiene además 3 unidades en los lugares 13 a 15 (Peasants, Clay Golems, Moonguard) que los otros tienen vacíos.
    Pedido al usuario en TAREAS 25 que lo iguale; la tanda espera a eso.
  - (21/10) El usuario igualó el blanco: bandos «común», equipos 013|457 (SAV de 01:23).
  - Próximo: el usuario corre la tanda (TAREAS 25, paso 4: el usuario la lanzó con 10 partidas x 6 = 60, Monitor 1.0.10); después, analizarla
    como las 29 a 34.
- (22/10) Corrección: esa serie ya terminó (tandas 35 a 40, 60 partidas, 1.0.50.0) y corrió sobre
  Tanda_hex_alianzas, **con ruinas**: el _SR se armó a las 23:37 del 21/10, después. La serie sin ruinas, con los
  mismos bandos, es TAREAS 30; comparar 35-40 (con ruinas) contra esa mide cuánto pesan las ruinas.

### 23/10/2026: serie A/B sin ruinas, tandas 41 a 46 (60 partidas, Tanda_hex_alianzas_SR, 1.0.65.0, exe 1a40e8b8)
Comparada con la 35-40 (mismo bando simple y mismos equipos 013|457, con ruinas, 1.0.50.0), que no se había
analizado, y con la 29-34 (bando viejo, con ruinas). Script: margen de PV 013-457 por partida, separado según qué
equipo tenía la IA de prueba (P); efecto = (margen con 013 en P - margen con 013 en O) / 2, ± error estándar.
| serie | válidas | 013 gana | victorias P / O / empate | efecto P (PV por equipo) | refugios P |
|---|---|---|---|---|---|
| 29-34 (bando viejo, ruinas) | 48 | 37 | 20 / 27 / 1 | -3.2 ± 2.8 | 16 |
| 35-40 (bando simple, ruinas) | 59 (1 colgada) | 17 | 26 / 30 / 3 | -5.0 ± 4.4 | 59 |
| 41-46 (bando simple, sin ruinas) | 58 (2 colgadas) | 28 | 35 / 23 / 0 | +7.1 ± 3.7 | 18 |
- Las ruinas deciden quién tiene ventaja en el mapa: con ruinas, el equipo favorecido cambia según el bando (013
  ganó 37/48 con el viejo; 457 ganó 42/59 con el simple). Sin ruinas, Hexagon queda parejo: 28 a 30. Quitarlas sí
  sirvió.
- Sin ruinas, P gana 35 a 23 y +7.1 PV por equipo: es la primera vez que sale a favor, pero apenas pasa 1,9 veces
  su error (no llega a ser concluyente) y las reglas de alianzas se activaron poco (18 refugios, 8 defensas desde
  refugio, 2 de ciudad aliada en 58 partidas): no alcanzan para explicar 7 PV.
- Las tres series juntas (promedio ponderado): -0.6 ± 2.0 PV. Sigue sin haber ventaja demostrada.
- Próximo paso propuesto: repetir la 41-46 tal cual (otras 60 partidas sin ruinas, Monitor 1.0.13). Si vuelve a dar
  a favor de P, el efecto es real; si da cerca de cero, fue azar. Es TAREAS 33.

### 24/10/2026: repetición sin ruinas, tandas 47 a 52 (36 partidas, Tanda_hex_alianzas_SR, 1.0.68.0, exe 59a13aea)
TAREAS 33. Corrió con 6 partidas por tanda (no 10). Los cambios 1.0.66 a 1.0.68 (chat, ítems de mapas al azar) no
tocan la IA ni esta guardada. Mismo script que la 41-46 (reproduce su +7.1).
| serie | válidas | 013 gana | victorias P / O / empate | efecto P (PV por equipo) | refugios P |
|---|---|---|---|---|---|
| 41-46 (sin ruinas) | 58 | 28 | 35 / 23 / 0 | +7.1 ± 3.8 | 18 |
| 47-52 (sin ruinas) | 36 | 13 | 11 / 24 / 1 | -6.3 ± 4.8 | 9 |
| 41-52 juntas | 94 | 41 | 46 / 47 / 1 | +2.0 ± 3.0 | 27 |
- La repetición da en contra: el +7.1 de la 41-46 fue azar. Sin ruinas el mapa sigue parejo (013 gana 41 de 94).
- Las reglas de alianzas casi no se activan (9 refugios, 1 defensa desde refugio en 36 partidas).
- Las cuatro series (29-34, 35-40, 41-46, 47-52), promedio ponderado: -1.4 ± 1.9 PV. **No hay ventaja de la IA de
  prueba**, ni a favor ni en contra: con tan pocas activaciones, las reglas actuales no mueven el resultado.
- Próximo paso: más partidas no lo van a cambiar. Lo que falta es que las reglas se activen más seguido (o probarlas
  en un mapa donde los aliados estén en contacto), antes de volver a medir.

### 24/10/2026: línea de alianzas CERRADA (decisión del usuario)
No se corren más series A/B de alianzas hasta que la IA tenga instrucciones nuevas para reconocer situaciones (por
ejemplo, un aliado que necesita ayuda para defender una ciudad en riesgo) y actuar, sin atentar contra su propio
objetivo de sobrevivir con el mayor puntaje u otra condición de victoria de la partida. Recién con eso se vuelve a medir.

## Ronda nueva: personalidades (desde el 24/10/2026)
Objetivo: qué perfil de personalidad gana más partidas. Todo igual salvo la personalidad: mismo bando (.PGS) en los
8 colores, mismas armas, Hexagon, sin ruinas (sin_ruinas.py), sin alianzas, la misma IA (original) en todos los
colores. Cada color recibe 4 puntos de personalidad que elige el usuario (ejemplos que dio: blanco = máximo poder
de ataque, amarillo = mucho movimiento, naranja = héroes y mercenarios más baratos).
- Problema de método: en Hexagon cada color arranca en un lugar fijo, y la ubicación pesa (con alianzas, un equipo
  ganó 37 de 48). Si la personalidad no cambia de color, «el blanco gana más» no distingue perfil de ubicación.
  Solución: rotar los perfiles entre colores de una partida a otra (como la rotación P/O), para que cada perfil
  pase por cada ubicación la misma cantidad de veces. Para eso hay que ubicar dónde guarda el .SAV los puntos de
  personalidad de cada color (estructura de jugador: 0x536b30 + color*0x1f8, todavía sin mapear) y escribirlos
  antes de cada partida, como hace sin_ruinas.py con las ruinas.
- Para ubicarlos: una guardada del usuario con perfiles distintos y conocidos por color (TAREAS 38); se buscan
  esos valores en los 8 bloques de jugador. Si no aparecen, comparar con una segunda guardada que cambie uno solo.
- La IA no tiene que repartir sus propios puntos («AI Chooses Personalities» apagado), o pisaría los del usuario.
- Mapeados (25/10/2026, Tanda_hex_perfiles, TAREAS 38: 6 colores, 5 puntos, sin naranja ni celeste): son 22 bits en
  los bytes +0xc0..0xc2 del registro de jugador (little endian), uno por personalidad, en el orden de la lista del
  clan: 0 Strong, 1 Very Strong, 2 Herculean, 3 Fast, 4 Very Fast, 5 Lightning, 6 Informed, 7 Farseeing, 8 Heroic,
  9 Legendary, 10 Merchant, 11 Famous, 12 Renowned, 13 Disciplined, 14 Resolute, 15 Immovable, 16 Rich, 17 Opulent,
  18 Engineer, 19 Artificer, 20 Ceremonial, 21 Devout. Los 6 colores coinciden bit a bit con lo que asignó el
  usuario (blanco 0x12, amarillo 0x8000, rojo 0x10e00, verde 0x51100, azul 0x2001, negro 0x280000). 10 y 11 (Merchant/
  Famous) confirmados en Darklord.exe: el bit 10 solo divide un precio por 5 (80%, 0x74990), y el 11 va de a par con
  el 12: 12 divide por 5 y 11 multiplica por 3/5 (40%), igual que los descuentos de mercenarios Famous/Renowned
  (0xb08fe, 0xb0a58). Los héroes, 8/9, mismo esquema (0x4fb2d). Coincide con Sagetext.tex y la tabla del clan. Sin verificar:
  si el juego deriva otros campos de estos bits al arrancar (+0xe2..0xe4 también cambian entre colores); la primera
  partida con perfiles rotados tiene que mostrar en el juego el perfil escrito.
- Hecho (25/10/2026, Monitor 1.0.14): con una sola guardada de perfiles distintos, tanda.plan juega todos con la
  IA original y en la partida i le da a cada color el perfil del color i lugares después (6 partidas = una vuelta
  completa); jugar escribe SAVES\IA_ROTADA.SAV (solo cambian los bytes +0xc0..0xc2) y la carga; partida.perfiles
  guarda {color: color de origen del perfil}; informe.py suma ganadas y PV por perfil. Guardada:
  Tanda_hex_perfiles_SR (sin_ruinas.py: tenía 47 ruinas aunque la opción estuviera apagada). El oro del turno 1
  difiere por color (blanco y amarillo 64, rojo 119, verde, azul y negro 244): queda con la ubicación, la rotación
  lo reparte. Sin verificar: si alguna personalidad ya se aplicó a las unidades iniciales al armar la partida
  (Immovable/Strong guardados en el ejército); si fuera así, esas unidades conservan el bono del perfil original.
- Tanda 53 (1.0.14) anulada (partidas en estado «invalida»): Tanda_hex_perfiles trae 01457 aliados en la tabla de
  diplomacia aunque la diplomacia esté apagada, y cada partida terminó al turno 3 con victoria aliada. Desde 1.0.15
  escribir_rotada pone guerra (1) entre todos los colores, vigentes y propuestas.
- Próximo paso: TAREAS 41 (5 tandas de 6) y analizar por perfil.

