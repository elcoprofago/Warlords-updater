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
