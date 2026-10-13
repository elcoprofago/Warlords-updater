# Entrenamiento de la IA de los bandos — plan

Estado al 13/10/2026: plan cerrado en líneas generales, nada implementado. Falta la entrevista del spec.

## Objetivo (pedido del usuario)
Que la IA resuelva mejor los problemas y recuerde estrategias, no solo que reciba más recursos.
Lo que valga para single player vale para multi player (la IA es la misma).

## Hechos de partida
- La IA es código x86 dentro de Darklord.exe (1997): sin red neuronal ni pesos. Todo cambio es un parche binario
  (parches\vista-aliada\build.py: ai_move, ai_conv, ai_free...). Un modelo externo no puede decidir jugada a jugada.
- Se puede ejecutar código real del juego sobre el estado de un .SAV con unicorn (prueba_emulada.py, prueba_ia*.py).
- PC: Ryzen 5 5600G, 47 GB RAM, RTX 5050. El límite es la cantidad de partidas, no el cálculo.
- Según el usuario: no se pueden correr partidas simultáneas en la misma PC; un turno humano dura 5 a 10 minutos.
  Está averiguando si se puede jugar una partida con todos los bandos en IA (pendiente en TAREAS.md si hace falta).
- Grabar sin intervención humana: lo resuelve el propio parche (el exe escribe su registro y, si hace falta,
  un .SAV por turno con nombre fijo). No depende del diálogo de grabar.
- El exe ya lee la personalidad de cada jugador de PGS\<nombre>.PGS (build.py, ~línea 1566).

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
8. Ajuste por resultados: torneos IA contra IA en mapas chicos, misma semilla, una partida por vez; un optimizador
   propone valores de IA.INI y se queda con lo que gana más. Victoria = criterio final; ciudades/pérdidas = señales.
9. Análisis de partidas humanas (Claude, fuera del juego): patrones de los ganadores convertidos en reglas nuevas.

## Descartado
- Entrenamiento tipo AlphaZero (millones de partidas): el juego no da ese volumen.
- Modelo de lenguaje decidiendo dentro de la partida: el exe no puede consultarlo y la demora sería inaceptable.
- Copiar jugadas humanas por imitación directa: hay pocas partidas; se usan para análisis (etapa 9).
- Partidas simultáneas en la misma PC.

## Próximo paso
Entrevista del spec (transcribir matriz de fases y perfiles; fijar alcance de la primera versión), luego etapa 1.
Frase para retomar: "Seguimos con ia\PENDIENTE-entrenamiento-ia.md: entrevista del spec".
