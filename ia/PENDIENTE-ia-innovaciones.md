# La IA ante las innovaciones del parche — plan (desde el 27/10/2026)

## Objetivo (usuario, 27/10/2026)
El fin último de las tandas y del Monitor es que la IA juegue cada vez mejor, sobre todo ante lo que el juego
original no tenía: puentes que se derriban, pozos, remolinos, trampas, bonos nuevos de movimiento y de habilidades.
Las tandas nuevas miden cuánto progresa la IA en dos frentes:
- **a) Oportunidades** (visión «oportunista»): detectar jugadas tácticas o estratégicas que dan las innovaciones.
  Ejemplo: derribar un puente fuera de una misión, para defenderse o solo para complicar al adversario.
- **b) Riesgos**: evitarlos. Ejemplo observado por el usuario: ante un pozo la IA no sabe esquivarlo y pierde
  pilas turno a turno.

Antecedente: las reglas de alianzas (tandas 29-52) no dieron ventaja ni desventaja (-0.5 ± 0.4 PV contra la base de
cada lugar). Lectura del usuario: no es un mal dato, porque muestra que las reglas condicionadas no desordenan a la
IA. No retroceder importa tanto como avanzar: toda regla nueva se mide también contra eso (que no baje el PV).

## Lo que hay hoy (revisado en el código, 27/10/2026)
- **Pozos, remolinos y trampas** (parches\vista-aliada\PENDIENTE-pozos-y-trampas.md): datos, generación, caer,
  descubrir, dibujo y trampas están hechos. **La parte «IA» nunca se programó**: el diseño decía que en la búsqueda
  de camino un pozo visto es intransitable para ese jugador (decisión del usuario del 19/10/2026), pero en build.py
  no hay nada que lo haga. Por eso la IA entra a pozos ya descubiertos: es la causa probable de lo que vio el
  usuario, sin verificar en una partida (falta registrar las caídas, ver abajo).
- **Puentes**: la IA ya derriba puentes por criterio propio (ai_brraze, build.py ~5175: la misma cuenta con que
  arrasa una ciudad, al terminar el movimiento de una pila junto a un puente enemigo o neutral). Nunca se midió
  cuántas veces lo hace ni si le sirve.
- Bonos nuevos de movimiento y habilidades: falta relevar cuáles usa la IA y cuáles ignora.

## Plan
1. **Registro** (vista-aliada, como ia_bat): eventos nuevos en IA_EV.CSV / tabla evento:
   - caída en pozo/remolino/trampa: color, casilla, ejércitos perdidos, y si el pozo **ya era visible** para ese
     color (error evitable) o estaba oculto (mala suerte);
   - puente derribado por la IA: color, casilla, dueño de la ciudad dueña, y si en los turnos siguientes un enemigo
     quedó frenado (no cruzó / atacó menos esa zona).
   El informe y el Monitor los cuentan por partida y por color.
2. **Línea base**: una tanda con la IA actual y pozos encendidos (Hidden Ruins) mide cuántas pilas se pierden en
   pozos vistos. Esa es la cifra a bajar.
3. **Riesgo, pozos**: programar la parte IA pendiente (pozo/remolino/trampa visto = intransitable en el buscador de
   caminos para ese jugador). Prueba emulada, después tanda A/B contra la base de cada lugar: caídas en pozos vistos
   (tiene que llegar a 0) y PV (no tiene que bajar).
4. **Oportunidad, puentes**: con el registro, medir ai_brraze; si casi no se activa o no frena a nadie, afinar el
   criterio (puente en el camino de un enemigo hacia una ciudad propia).
5. Después, uno por uno, los demás bonos y habilidades nuevos, con el mismo esquema: registrar, base, cambio, A/B.

## Hecho
- **Paso 1** (27/10/2026, vista-aliada 1.0.91.0, Monitor 1.0.20): po_step guarda si el registro ya era visible para
  el que pisa (po_pvis, antes de «descubrir al pasar»); po_fall anota ia_evt 18 pozo, 19 remolino, 20 trampa, con
  x, y = casilla y n = muertos + 100 si ya lo veía (los paralizados de la trampa no cuentan). Los derribos de puentes
  ya estaban (evento 1, ai_brraze). informe.py tiene la sección «Innovaciones» (por IA y color: caídas vistas y
  ocultas con sus muertos, puentes derribados); el Monitor separa «visto» y «oculto». Probado en prueba_pozos.py.
  Sin hacer: si un puente derribado frenó a alguien (necesita seguir las pilas enemigas; se ve en el paso 4).
  No probado en emulación: un pozo oculto que se descubre en el mismo paso en que se cae (por diseño cuenta como
  oculto, porque po_pvis se toma antes de descubrir).

## Próximo paso
Paso 2: ninguna guardada de tanda tiene pozos (revisado 27/10/2026: las de Hexagon tienen Hidden Ruins apagada, tabla
POZO con 0; Borderlands, Kor y Scarpart son anteriores a los pozos y no traen el bloque POZO, cargan la tabla vacía).
Los pozos se generan solo en partida nueva (po_gen), así que el usuario arma Tanda_hex_pozos_control (TAREAS 69).
Al recibirla: verificar el bit 0x10 de [0x53c393] y la tabla tras 'POZO' (cantidad y tipos); después la tanda de 10
y contar con informe.py las caídas vistas por color. Frase para retomar: "Seguimos con
ia\PENDIENTE-ia-innovaciones.md, paso 2".
