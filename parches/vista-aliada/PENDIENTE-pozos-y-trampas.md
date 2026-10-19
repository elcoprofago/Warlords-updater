# Pozos y remolinos ocultos, y el bono "trap" (idea del usuario, 19/10/2026)

No es una destreza de la IA, pero la IA tiene que conocerlo (no meterse a sabiendas en un pozo descubierto, y
usar el bono "trap" en una etapa posterior).

## Lo que pidió el usuario
1. Sumar al mapa, con la misma lógica de las ruinas ocultas, **pozos** ocultos (accidentes del terreno, en tierra)
   y **remolinos** ocultos (en el agua).
2. Se descubren igual que las ruinas ocultas, con el mismo rango de casillas (el usuario no sabe cuál es: hay que
   averiguarlo en el exe).
3. Efecto: el grupo que pasa sobre un pozo o remolino oculto muere de inmediato, **salvo los voladores**.
4. Cantidad: un porcentaje parecido al de las ruinas ocultas.
5. Al caer (terrestres al pozo, barcos al remolino) suena, al azar, el sonido de muerte de héroe o de heroína.
6. Dibujos nuevos: el pozo, y el remolino **animado**. Una vez descubiertos quedan visibles el resto de la
   partida, como las ruinas ocultas.
7. Bono **"trap"**: solo algunas armas (por ejemplo los actuales "zappers") pueden construir en el mapa, donde el
   jugador elija, un pozo-trampa oculto con el mismo efecto. Cuesta lo mismo que una ciudad. Siempre visible para
   su creador, con la misma lógica interna que las unidades con bono de invisibilidad.

## A averiguar en el exe (antes de diseñar)
- Cómo se generan y guardan las ruinas ocultas (opción de partida, porcentaje, estructura de la ruina, bandera de
  "oculta") y en qué rutina y con qué rango se descubren.
- Dónde se valida cada paso de un grupo (para el efecto de caer) y cómo se mata un grupo entero (sin batalla).
- Los sonidos de muerte de héroe y heroína (archivos y la rutina que los dispara).
- Cómo se dibujan las ruinas en el mapa y si hay casillas animadas que sirvan de modelo para el remolino (agua).
- Cómo funciona el bono de invisibilidad (visible para el dueño, oculto para los demás) y la lista de bonos de las
  armas (dónde sumar "trap", como ya se sumaron landing, carrier y cabotaje).
- "Costo de una ciudad": qué valor del juego es (¿construir una ciudad? averiguar si existe y cuánto vale).
- Qué viaja por red y qué se guarda con la partida: pozos y trampas tienen que estar en el SAV y ser iguales en
  todas las PC.

## Preguntas de juego para el usuario (no técnicas)
- ¿La trampa del bono "trap" afecta también a los aliados del creador, o solo a los enemigos?
- ¿Un héroe cae como cualquier otro, o tiene alguna chance de salvarse?
- ¿Los pozos y remolinos son una opción de la partida (como Hidden Ruins) o van siempre?
- ¿Una trampa construida se puede descubrir por los demás con el mismo rango, y una vez descubierta deja de ser
  peligrosa (se la esquiva) o sigue matando a quien la pise?

## Estado
Nada averiguado ni programado. Para retomar: "Seguimos con PENDIENTE-pozos-y-trampas.md".
