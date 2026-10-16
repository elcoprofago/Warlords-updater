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
