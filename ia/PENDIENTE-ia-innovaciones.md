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

## Próximo paso
Paso 1: ubicar en po_step (caída) cómo saber si el pozo era visible para el que cae (bit del jugador en +6 de la
tabla po_*), y agregar el evento. Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 1".
