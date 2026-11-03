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

- **Paso 2, primera parte** (28/10/2026): tandas 97 a 99 sobre Tanda_hex_pozos_control (1.0.91.0, exe ddd41a96,
  todos con la IA original, sin alianzas): 20 partidas, 13 completas (30 turnos), 6 colgadas y 1 cortada. La guardada
  trae 9 pozos (ningún remolino ni trampa) y ninguno visible al empezar (máscara +6 = 0 en los 9). Caídas: 2, ambas
  en pozos ocultos (t97: verde en 55,87 con 5 muertos; negro en 81,57 con 1). Vistas: 0. Lectura: con pozos que nadie
  ve, el riesgo evitable no aparece y la línea base no mide nada; 2 caídas en 13 partidas es poco riesgo en Hexagon.
  Las 6 colgadas (30 %) son muchas para esta serie; no se investigaron.
- ia\pozos_vistos.py arma SAVES\<guardada>_PV[_control].SAV con todos los pozos descubiertos por los 8 colores (solo
  cambia la máscara +6; verificado: 9 bytes distintos). Ya armada: Tanda_hex_pozos_PV_control.

## Próximo paso
Paso 2, segunda parte: tanda de 10 sobre Tanda_hex_pozos_PV_control (TAREAS 70) y contar con informe.py las caídas
vistas. Si siguen en 0, la IA ya los esquiva o no pasa por ahí: revisar las casillas de los 9 pozos contra los caminos
antes de programar el paso 3. Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 2".

## Resultado del paso 2, segunda parte (tanda 105 = TAREAS 70, revisado 30/10/2026)
Tanda_hex_pozos_PV_control: los 9 pozos descubiertos por los 8 colores. 10 partidas ok, 30 turnos, ninguna colgada.
Caídas vistas: color 1, 2 caídas (7 muertos); color 3, 1 caída (8 muertos). Ocultas: 0. Como el pozo ya estaba
explorado por el bando que cayó, son **errores evitables**: falla confirmada (criterio del usuario: caer en un pozo no
explorado está bien; en uno explorado, es falla). Lo observado por el usuario: los héroes van por el ítem que dejó
un caído y caen en el mismo pozo.
Colgadas de tandas anteriores (30 % en 97-99): hipótesis del usuario, no medida: él sigue usando la PC durante la
tanda y el mouse y el teclado llegan igual al juego en el otro monitor. No investigarlas por ahora.
Próximo paso: paso 3, que la IA no entre en un pozo que su bando ya descubrió (ni para levantar un ítem).
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 3".

## Paso 3, hecho el código (30/10/2026, vista-aliada 1.0.97.0)
po_pf (build.py, en 0x4a5d34 del buscador de caminos 0x4a5c40, por cada casilla vecina): un pozo, remolino o trampa
activa que el jugador del camino ve (bit suyo en +6; en la trampa, también ser su dueño o aliado con vista aliada) es
intransitable. Tumbas y trampas gastadas no cuentan. Excepción, solo para el humano: si esa casilla es el destino que
eligió, llega y cae (decisión del 19/10/2026). La computadora no tiene excepción: tampoco entra por el ítem de un caído.
Vale para el mapa de distancias de la IA y para sus caminos, porque usan el mismo buscador. Los voladores van por otra
rama del buscador y no se tocan (no caen).
Prueba emulada: parchesista-aliada\prueba_iapozos.py, 17 casos OK (incluye controles: pozo que ve otro, trampa
gastada, tumba, fuera del mapa, destino del humano en otra casilla, y el exe original que deja pasar siempre).
Sin verificar en partida: que la IA, sin camino al ítem, no se quede trabada intentándolo todos los turnos.
Próximo paso: tanda A/B = TAREAS 78 (misma guardada que la tanda 105). Comparar con informe.py: caídas vistas
(tienen que ser 0; en la 105 fueron 3) y PV (no tiene que bajar contra la 105).
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 3, resultado de la tarea 78".

## Resultado del paso 3 (tanda 114 = TAREAS 78, revisado 1/11/2026)
Tanda_hex_pozos_PV_control con 1.0.98.0 (exe d1bdbf67, lleva po_pf): 9 partidas válidas, 1 colgada en el turno 10.
Caídas en pozos vistos: **0** (la tanda 105, sin po_pf, tuvo 5 con 17 muertos: colores 1 (2), 3, 4 y 7; arriba se
anotaron 3, mal contadas). El registro funcionó: la tanda anotó sus eventos 11 y 12 como la 105. PV medio 11.5 contra
11.8 de la 105: -0.3 ± 0.4 por partida, dentro del azar; no retrocede. Paso 3 cerrado.
Próximo paso: paso 4 (puentes): medir ai_brraze con el registro (evento 1). Ojo: en las tandas 105 y 114 no hubo
ningún derribo de puente; hace falta una guardada con puentes. Frase para retomar:
"Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 4".

## Paso 4, medición (1/11/2026)
Derribos por criterio propio (evento 1) en toda la base: **0**, en todas las guardadas con registro de eventos
(~600 partidas desde la tanda 19). Puentes por guardada (casillas de puente entero, misma regla que br_kind, leídas
de la grilla del .SAV con ia\puentes.py):
- Tanda_hex_* (Hexagon): 1 casilla (17,103). Por eso 105 y 114 no podían medir nada.
- Tanda_Border_Alianzas / Tanda_Borderlands: 13 casillas. Border_Alianzas: 69 partidas con registro y 0 derribos.
- Tanda_Scarpart: 33; Tanda_Kor: 14 (sus tandas son de antes del registro de eventos).
Por qué no se activa (cuenta de ai_brs aplicada a cada puente y color en la guardada inicial):
- el temperamento c es 0 en los 8 colores, así que s arranca en -1 y solo sigue si el grupo de IA del líder (flag) no
  es 0;
- con Diplomacy todos empiezan en paz: la ciudad dueña no es hostil y el puente se descarta (11 de 13 en Border); los
  2 de dueño neutral dan entre -7 y -1, lejos de 5;
- en Scarpart, los 31 de dueño neutral dan -1 a -3 para todos los colores;
- además exige que el puente quede atrás de la pila (no en su camino), lo que excluye justo los puentes que importan.
Para llegar a 5 hacen falta guerra declarada y unas 3 ciudades hostiles más que propias a menos de 15 casillas.
Conclusión: el criterio actual es inalcanzable en la práctica; afinarlo no alcanza, hay que cambiarlo.

## Próximo paso (paso 4, parte B): criterio nuevo para derribar
Idea del plan: derribar un puente que esté en el camino de un enemigo hacia una ciudad propia (defensa), sin
depender del temperamento. Esbozo a diseñar contra el código: al terminar el movimiento de una pila de la IA junto a
un puente entero sin ejércitos encima, mirar si (a) del lado de la pila hay una ciudad propia a pocas casillas y
(b) del otro lado hay una pila de un jugador en guerra que, con el puente cortado, queda más lejos de esa ciudad
(comparar distancias del buscador con y sin el puente). Nunca derribar uno que la propia IA necesita (el destino de
la pila está del otro lado). Prueba emulada con controles, después tanda A/B sobre una guardada con puentes y
registro: Borderlands sin alianzas, 1.0.98.0 o posterior (la base ya medida es 0 derribos). Medir derribos y PV.
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 4, parte B".

## Paso 4, parte B, hecho el código (1/11/2026, vista-aliada 1.0.99.0)
ai_brdef (build.py, llamado desde ai_brraze antes de la cuenta vieja): derriba el puente junto al que terminó la pila si
- hay una ciudad viva propia a 8 casillas o menos del puente (BRD_CITY) y el líder le queda más cerca que el puente
  (está del lado de la pila);
- hay un ejército vivo de un jugador en guerra (0x49c1c0; neutrales no) a 6 o menos del puente (BRD_ARMY), del otro
  lado: el puente le queda más cerca que el líder, y la ciudad más lejos que al puente.
Siguen valiendo los descartes de antes: líder junto al puente y no encima, nadie sobre el puente, y el puente no está en
el camino de la pila (así nunca corta uno que la propia IA necesita). Sin temperamento, sin azar, sin mirar la ciudad
dueña (puede cortar el propio). Evento 1 con n = 100 (la cuenta vieja anota c + s, siempre < 100); informe.py lo
cuenta en la columna «defensa».
Simplificación: «del otro lado» es geométrico (distancias de rey), no con el buscador de caminos con y sin el puente;
la tanda dirá si alcanza. Ojo: la reconstrucción (ai_brrebev) no conoce el criterio nuevo, pero no repone un puente
con un ejército hostil a menos de 15/30, así que mientras dure la amenaza no lo vuelve a poner.
Para medir en una sola tanda: con DATA\IA.INI (tanda) solo lo usan los colores en «prueba»; sin IA.INI (partidas
normales) vale siempre.
Prueba emulada: prueba_iarazea.py, 89 casos OK (29 nuevos de defensa con controles: sin enemigo, sin ciudad, en paz,
aliado, mismo lado, ciudad del otro lado, límites 6/7 y 8/9, destino del otro lado, IA original en tanda, el exe
original; y 3000 al azar contra el modelo). Sin probar en partida.
Próximo paso: tanda A/B = TAREAS 81 (Borderlands sin alianzas, 1.0.99.0). Comparar con informe.py: derribos por
defensa (columna «defensa», tiene que haber), PV de prueba contra original (no tiene que bajar).
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 4, resultado de la tarea 81".

## Resultado del paso 4 B (tarea 81, tandas 117 a 119, revisado 2/11/2026)
Borderlands sin alianzas, vista-aliada 1.0.100.0 (exe d53fc857; ai_brdef ya estaba, 1.0.100.0 y 1.0.101.0 solo
agregan el historial de partidas y no tocan la IA): 25 partidas válidas (la 119 se cortó en la 7.ª porque otra sesión
instaló la 1.0.101.0 a mitad de tanda y tanda.py se niega a retomar con otro exe). Derribos: **0**, tampoco de la IA de
prueba. No es por falta de guerra: hubo guerra declarada en las 25 (primera entre los turnos 5 y 14; 21 % de los pares
color-color en guerra a lo largo de las partidas). El registro funcionó (eventos 11 y 12). PV prueba 7.2 contra
original 6.2: como el criterio nunca se activó, esa diferencia es puro azar entre colores de la misma IA (sirve de
calibración: ±1 PV con 25 partidas no significa nada).
Corrección (usuario, 2/11/2026): la 119 la cortó él (pruebas en red del Visor), y con varias sesiones a la vez
instalar parches va a seguir pasando. La guarda que se había puesto en build.py (no compilar en C:\Warlords3 con
una tanda sin terminar) se quitó: frenaba instalaciones legítimas. Una tanda cortada se reemplaza por una nueva.
Hueco encontrado: tanda.py anota como versión la de parches.txt del repo, no la instalada (el exe no la lleva), así
que las tandas 121 y 122 quedaron como 1.0.102.0 con el exe c1d0822c de la 1.0.101.0 (se subió parches.txt antes de
instalar). Corregidas a mano en datos.db; el hash del exe sigue siendo el dato confiable.

## Paso 4 C: diagnóstico (vista-aliada 1.0.103.0; la 1.0.102.0 no se publicó, 2/11/2026; enumerar antes de cambiar el criterio)
Evento 21, solo en tandas (ia_on): una pila de la IA terminó junto a un puente entero y no lo derribó; x, y = puente,
n = por qué: 1 ejército encima, 2 el puente está en el camino de la pila, 3 color con la IA original, 4 (prueba) sin
ciudad propia a <= 8 del lado de la pila, 5 (prueba) con ciudad pero sin ejército en guerra a <= 6 del otro lado.
ai_brdef devuelve en edx si encontró la ciudad. informe.py lo cuenta («Puentes junto a una pila de la IA que no se
derribaron»). Prueba emulada: prueba_iarazea.py, el evento 21 igual al modelo en los 3000 casos al azar, con cada n
más de 10 veces y sin evento fuera de tandas; las decisiones de derribo, iguales que antes.
Estado: commiteado; **sin instalar ni publicar** (la tanda 122 corría con la 1.0.101.0; no suma: cortarla).
Próximo paso, con el juego cerrado: python parches\vista-aliada\build.py (en C:\Warlords3), prueba_iarazea.py
contra lo instalado, tools\publicar-parche.ps1 vista-aliada, y avisar al usuario para la tarea 86. Con su resultado:
si el motivo dominante es 1 o 2, una pila casi nunca para junto a un puente sin cruzarlo, y el criterio tiene que mirar
desde otro lugar (por ejemplo, desde una ciudad propia amenazada, mandar una pila al puente); si es 4 o 5, ajustar
las distancias 8/6. Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 4 C".

Resultado (tanda 123, 1.0.103.0, 10 partidas Borderlands, 2/11/2026): 0 derribos. Evento 21: 12 en total, todos
n = 2 (el puente era el camino de la pila: 7 original, 5 prueba); ningún 1, 4 ni 5. Conclusión: las pilas de la IA
casi nunca quedan junto a un puente salvo para cruzarlo, así que un criterio que parte de "pila junto a puente" no
puede disparar. Próximo paso (4 D): partir de la ciudad propia amenazada (enemigo en guerra del otro lado de un
puente a <= 6, ciudad a <= 8) y mandar una pila a ese puente para derribarlo. Frase para retomar:
"Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 4 D".

## Paso 4 D, hecho el código (vista-aliada 1.0.105.0; la 1.0.104.0, igual, no se publicó; 2/11/2026)
- ai_brdefev (desde ai_brrebev, evaluador de metas de cada pila; solo IA de prueba en tandas): recorre los puentes
  enteros sin ejércitos encima; para cada uno toma la cabecera más barata (br_head) y prueba ai_brdef con el líder
  parado ahí. Elige el más barato que cumpla y lo pone como candidato a meta 9 con valor 100 (gana a cualquier
  ciudad muerta). Evento 22 (n = costo).
- ai_brreb (ejecutor de meta 9): si el puente está entero, va a la cabecera; al llegar vuelve a mirar: si sigue
  entero, sin ejércitos y con la amenaza, lo derriba (0x4b9550; evento 1 con n = 101). Si no, evento 23 (n = 1 ejército
  encima, 2 sin amenaza) y la pila queda libre ese turno (no se le da el turno por terminado).
- informe.py: tabla «Ir a derribar un puente que amenaza una ciudad propia»; la columna «defensa» suma n = 100 y 101.
- Prueba emulada: prueba_iareconstruye.py (casos 4 D, 600 al azar contra el modelo, con más de 12 de defensa);
  prueba_iarazea y prueba_iapuente siguen igual. Las tres, TODO OK contra lo instalado.
Próximo paso: tarea 87 (tanda Borderlands de 10). Mirar: eventos 22 (¿se elige?), 1 n = 101 (¿se derriba?), 23
(¿por qué no?) y los PV de prueba contra original. Si se elige mucho y no se llega, revisar la cabecera; si se derriba
y el PV baja, el valor 100 es demasiado alto. Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md,
resultado del paso 4 D".

## Resultado del paso 4 D (tandas 124 a 126 = TAREAS 87 y dos más, revisado 3/11/2026)
Borderlands sin alianzas, exe 13fcb17c (1.0.105.0) en las tres; la 125 y la 126 figuran como 1.0.106.0 por el hueco
ya conocido de tanda.py (anota parches.txt del repo, no lo instalado), pero el exe es el mismo. 30 partidas válidas,
todas de 30 turnos.
- Derribos por defensa: **51** (14 + 21 + 16), todos de la IA de prueba y en 7 de los 8 colores. Antes del 4 D: 0.
- Evento 22 (elige ir): 133 veces sobre 78 puentes-color distintos; de esos, 51 terminaron derribados, en general en
  1 a 3 turnos desde la primera elección. Los 27 restantes no llegaron, pero ninguno por fallar al llegar (evento 23:
  0 con ejército encima, 0 sin amenaza): la pila cambió de meta, murió o se acabó la partida (varios eligen en el
  turno 28-30). La cabecera funciona; no hace falta revisarla.
- PV prueba 6.8 contra original 6.0 (+0.8 por color; por tanda +1.4, +0.2, +0.9). Dentro de la calibración de ±1
  de la tarea 81, así que no se lee como mejora, pero **no retrocede**: el valor 100 no es demasiado alto.
- Sin medir: si cada derribo frenó al enemigo (hueco del paso 1, sigue abierto).
Conclusión: paso 4 cerrado. En partidas normales (sin IA.INI) ai_brdefev ya vale para toda computadora, así que no hay
nada que pasar de «prueba» a todos.
Próximo paso: paso 5 del plan (relevar los bonos de movimiento y habilidades nuevos que la IA usa o ignora).
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 5".

## Paso 5: relevamiento (3/11/2026)
Fuentes: los bloques de build.py de cada bono, la tabla evento de datos.db (648 partidas) y los registros de unidad
de los bandos de las 15 guardadas Tanda_*.SAV (0x383f5, 8 x 16 x 0xfc: bonos de movimiento +0xb2, combate +0xd6,
habilidad +0xe6) y su byte de opciones (0x53c3a5, & 2 = día/noche).

| Innovación | ¿La IA la usa? | ¿Está en las tandas? |
|---|---|---|
| Landing (desembarco) | Sí, sola: su mapa de distancias y sus caminos usan el mismo buscador. ai_move parte el grupo que no entra (evento 3) | Ningún bando |
| Cabotage | Sí, solo: el buscador quita las casillas lejos de la costa | Barcos de los 8 bandos en Border_Alianzas y Scar_Alianzas |
| Carrier (convoy) | Código hecho (ai_conv, evento 2), pero **0 eventos 2 y 0 eventos 3 en 648 partidas** | **Ningún bando**: nunca se midió. El usuario vio el 19/10 que la IA lo maneja mal |
| Bridge +N | Pasivo (suma si la batalla cae en un puente); la IA no busca pelear ahí | Ningún bando |
| Trap (construir trampa) | No («La IA no la usa», build.py) | 12 unidades en las guardadas hex |
| build (construir camino) | No (etapa 1 de PENDIENTE-construcciones: solo humanos); usa los caminos que haya | Ningún bando |
| camouflg | Sin efecto entre computadoras: solo cambia el dibujo y el Army Report; la IA lee los ejércitos de la memoria | 6 unidades en hex_pozos (nombre viejo «camo»), con día/noche |
| Efecto noche (monster, demon, undead) | Pasivo: suma +2 en la batalla; la IA no elige atacar de noche | Día/noche solo en hex_pozos y hex_pozos_PV |
| Reconstruir puentes (meta 9) | Código hecho (ai_brrebev) | **0 eventos 4 en 648 partidas** |

Lectura: lo pasivo (Landing, Cabotage, Bridge +N, noche) la IA lo aprovecha sin decidir nada. Las tres cosas con
código de IA que nunca se vieron funcionar son el convoy (Carrier), partir el grupo al embarcar y reconstruir
puentes; las dos primeras porque ninguna tanda las ofrece. Trap y build: la IA no las tiene.
Orden propuesto (por riesgo observado y porque el código ya existe):
1. **Carrier**: armar una guardada de tanda en un mapa con mar (Scarpart o Kor) con barco Landing + Carrier en los 8
   bandos (como pozos_vistos.py, solo los bonos del registro 15) y medir eventos 2 y 3 y PV contra la base.
2. Reconstruir puentes: por qué el evento 4 nunca sale (enumerar con un diagnóstico, como el 21 del paso 4 C).
3. Trap: programar que la IA la use (oportunidad nueva).
4. Noche: atacar de noche con monster/demon/undead (oportunidad; poco peso).
Próximo paso: 5.1, la guardada con Carrier. Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md,
paso 5.1".

## Paso 5.1: guardadas con convoy (3/11/2026)
`ia\convoy.py <guardada>` escribe `<guardada>_CR.SAV` con "Landing" y "Carrier" en los bonos de movimiento del barco
(registro 15) de los 8 bandos; verificado releyendo el archivo (104 bytes cambiados, 13 por bando). Hechas:
Tanda_Scarpart_CR y Tanda_Kor_CR; el control son las partidas de Tanda_Scarpart y Tanda_Kor de datos.db.
Tanda pedida al usuario: TAREAS 89 (serie de 2 tandas de 10). Al volver: contar eventos 2 y 3 por partida y comparar PV y
puestos contra el control. Si salen 0 eventos, primero confirmar que el juego tomó los bonos de la guardada (el
barco en una partida cargada tiene que mostrar Landing/Carrier) antes de concluir nada sobre ai_conv.

Resultado de la tarea 89 (tandas 127-128, 1.0.106.0, 20 partidas ok): evento 3 (grupo partido) 62 veces en 17
partidas, así que el juego toma los bonos de la guardada. Evento 2 (convoy): 0. No hay control de la misma versión
(las Scarpart/Kor de datos.db son de 1.0.32.0), así que el PV no se compara todavía.
Diagnóstico agregado en 1.0.107.0: evento 24 en ai_conv, una vez por movimiento de un grupo embarcado con "Carrier"
que no armó convoy; n = 1 ya en convoy, 2 ya enlazado, 3 con "Landing" y sin puerto a 2 casillas del destino,
4 sin barco propio vecino que vaya cerca del mismo destino, 5 lo hubo pero la suma entraba en un stack.
Lectura previa del código: el convoy exige dos grupos ya embarcados, en casillas de agua vecinas, yendo a menos de 2
casillas del mismo destino y que no quepan en un stack; como ai_move parte el grupo antes de embarcar, lo que sobra
queda en tierra y casi nunca hay un segundo barco al lado. Si domina el motivo 4, el arreglo es que el resto soltado
por ai_move embarque en otro barco y se sume (convoy desde el muelle), en vez de esperar a que coincidan.
Tanda pedida: TAREAS 90 (serie de 2 x 10 con Scarpart, Kor, Scarpart_CR y Kor_CR: las dos primeras son el control).
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 5.1: terminó la tarea 90".
