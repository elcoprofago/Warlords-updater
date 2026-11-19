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
| Raft (1.0.250.0) | Sí, sola: el buscador agrega los pasos costa↔agua y quita lo lejos de tierra; ai_move parte el grupo al tope de 3 | Solo pruebas emuladas (prueba_balsa.py); falta un barco con Raft en un mapa del banco |
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
partidas, así que el juego toma los bonos de la guardada. Evento 2 (convoy ordenado por ai_conv): 0. Corrección:
el evento 2 no cuenta los convoyes que crlink forma solo cuando cualquier movimiento choca con un barco propio lleno;
el usuario vio al amarillo usar convoyes varias veces en una partida. Se agregó el evento 25 (1.0.108.0). No hay control de la misma versión
(las Scarpart/Kor de datos.db son de 1.0.32.0), así que el PV no se compara todavía.
Diagnóstico agregado en 1.0.107.0 (sigue en 1.0.108.0): evento 24 en ai_conv, una vez por movimiento de un grupo embarcado con "Carrier"
que no armó convoy; n = 1 ya en convoy, 2 ya enlazado, 3 con "Landing" y sin puerto a 2 casillas del destino,
4 sin barco propio vecino que vaya cerca del mismo destino, 5 lo hubo pero la suma entraba en un stack.
Lectura previa del código: el convoy exige dos grupos ya embarcados, en casillas de agua vecinas, yendo a menos de 2
casillas del mismo destino y que no quepan en un stack; como ai_move parte el grupo antes de embarcar, lo que sobra
queda en tierra y casi nunca hay un segundo barco al lado. Si domina el motivo 4, el arreglo es que el resto soltado
por ai_move embarque en otro barco y se sume (convoy desde el muelle), en vez de esperar a que coincidan.
Evento 25 (1.0.108.0): crlink formó un enlace nuevo (x, y = casilla a la que se sumó), por cualquier vía.
Tanda pedida: TAREAS 90 (serie de 2 x 10 con Scarpart, Kor, Scarpart_CR y Kor_CR: las dos primeras son el control).

Resultado de la tarea 90 (tandas 129-130, vista-aliada 1.0.120.0, 20 partidas ok, 8 en _CR):
- Evento 25 (convoy formado por cualquier vía): 0. Evento 2: 0. Evento 3 (grupo partido): 22.
- Evento 24 (ai_conv no armó): 187 = motivo 3 (con "Landing", sin puerto a 2 casillas del destino) 164, motivo 4
  (sin barco propio vecino) 23; motivos 1, 2 y 5: 0. El diagnóstico funciona (escribe), así que el 0 del 25 es real
  salvo falla propia de crlink->ia_evt (puntero verificado en el exe compilado, no en partida).
- PV medio: Scarpart 7,66 / Scarpart_CR 7,56; Kor 4,97 / Kor_CR 5,19. Sin diferencia con muestras tan chicas.
Corrección del usuario (4/11/2026): la prueba estaba mal armada. Juntar Landing y Carrier en el mismo barco no
representa el juego: el usuario nunca los pone juntos (sería demasiada ventaja en una unidad; la idea es repartir
cualidades para obligar a elegir al armar el bando), y con Landing siempre conviene la playa, para la IA y para un
humano. Atracar solo en puertos es la razón de ser del Carrier, lo que lo diferencia del Landing: no se toca.
El amarillo de las tandas 127-128 (1.0.106.0): el usuario lo vio en directo y eran barcos enlazados. Como el evento 2
fue 0 en esas partidas, el enlace no lo ordenó ai_conv: salió de crlink al chocar un movimiento común con un barco
propio lleno (accidental). La 1.0.106.0 no tenía el evento 25 para contarlo.
Paso 5.1 reabierto: guardadas Tanda_Scarpart_CA y Tanda_Kor_CA (ia\convoy.py, ahora solo "Carrier" en el barco;
verificado releyendo: 7 bytes por bando). Sin "Landing", ai_conv no exige puerto (va directo a cv_need) y el tope
es el stack del bando. Tanda pedida: TAREAS 100 (serie de 2 x 10 con Scarpart, Kor, Scarpart_CA, Kor_CA).
Al volver: eventos 2, 24 (por motivo) y 25 en _CA, y PV contra el control de las mismas tandas.
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 5.1: terminó la tarea 100".

## Paso 5.2: por qué nunca se reconstruye un puente (4/11/2026, vista-aliada 1.0.121.0)
Datos: 90 puentes derribados (evento 1) en las tandas 124-130, con unos 1.080 turnos restantes de partida en total, y
0 eventos 4. ai_brrebev se ejecuta (desde él sale el evento 22, 245 veces), así que el evaluador corre: lo frena
algún filtro o la competencia con las otras metas.
Hipótesis principal, sin confirmar: cuando el puente queda como el mejor candidato, se anota en la tabla de la meta 9
con valor 1 (igual que el original con una ciudad muerta, 0x41e510), y el selector 0x41f2c5 le suma a lo sumo +6 por
cercanía; la defensa entra con 100 y sí se ejecuta (51 derribos). Si el valor 1 pierde siempre, nunca se elige.
Antes de tocar el valor, enumerar (regla 3): 1.0.121.0 agrega en ai_brrebev
- evento 26, una vez por puente derribado, color y turno (en la primera pila evaluada; rbe_last guarda turno*16 +
  jugador), n = filtro que lo descartó: 1 ejército encima, 2 falta oro, 3 cabecera sin camino, 4 enemigo visible más
  cerca que el límite, 5 lo volvería a derribar (ai_brs >= 5), 6 nada que ganar al cruzar, 7 pasó todo;
- evento 27, cada vez que un puente queda como candidato de la meta 9 en la tabla (n = costo).
Prueba emulada: prueba_iareconstruye.py compara los eventos 26/27 con el modelo en todos los casos nombrados y en los
600 al azar (motivos 1, 2, 4-7 y el 27 más de 5 veces cada uno; el 3 en «sin camino a ninguna cabecera»); las
decisiones, iguales que antes. prueba_iarazea y prueba_iapuente, TODO OK.
Medición: la serie de la tarea 100 (Scarpart, Kor y sus _CA), ahora con 1.0.121.0 o posterior.
Lectura al volver: si dominan 27 sin eventos 4, el valor 1 pierde con otras metas: subirlo (como la defensa, pero
menor que 100) y medir PV. Si domina un motivo de 26, ajustar ese filtro (el 4, enemigo a menos de 30, es el
sospechoso: el puente se derribó justamente porque había enemigos cerca). Contar con
`select n, count(*) from evento where tipo = 26 group by n` y `tipo in (4, 27)`.
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-innovaciones.md, resultado del paso 5.2".

Resultado del paso 5.2 (tandas 131-132, vista-aliada 1.0.128.0, 20 partidas ok, Scarpart/Kor y sus _CA):
- Evento 26: 818 sobre 20 puentes distintos. n = 2 (falta oro) 770 (94 %), 3 (sin camino) 32, 4 (enemigo cerca) 16;
  1, 5, 6: 0. Igual en IA original y de prueba.
- Oro de la computadora en esos turnos: mediana 148, p90 305; reconstruir cuesta lo de fundar una ciudad
  ([0x56950e], 800 en estas partidas). Solo el 3,9 % de los turnos-color vivos de la IA tiene >= 800.
- Evento 27: 2 (los dos únicos que pasaron todo); uno terminó en evento 4 (tanda 131, partida 8, turno 9, costo 800):
  la primera reconstrucción registrada. La hipótesis del valor 1 queda sin apoyo: con oro, se elige y se ejecuta.
- Lo que el usuario vio (héroe blanco derribando un puente, tanda 132, partida n = 8, Kor): color 0, evento 1 n = 101
  en los turnos 18 y 21, precedidos de eventos 22: el criterio de defensa del paso 4 D.
Lectura: la IA no reconstruye porque gasta el oro en producción cada turno y nunca junta 800. No es una falla del
código. Cambiarlo es una decisión de juego (abaratar reconstruir, o que la IA ahorre para un puente que le abre
camino); se le planteó al usuario. Mientras no decida, paso 5.2 cerrado.

Decisión del 5.2 (11/11/2026): la IA ahorra para el puente que le abre camino, en vez de abaratar reconstruir (era
el objetivo del usuario del 4/11 en PENDIENTE-ia-economia). Hecho en vista-aliada 1.0.203.0: ver «Oro con destino,
primer destino: el puente» en PENDIENTE-ia-economia.md (tanda: TAREAS 174). Siguen sin hacer el 5.3 (trampas) y 5.4. (5.3 hecho: ver abajo.)

## Paso 5.3, hecho el código: la IA siembra trampas (13/11/2026, vista-aliada 1.0.219.0)

`tr_ai` (build.py) corre antes de cada meta de pila de la IA (0x40cc3f -> tr_me -> me_set). Una pila con un ejército
no héroe con el bono «Trap» siembra en su propia casilla si, en este orden: 1) no es una ciudad; 2) hay una ciudad
propia viva a 3 o menos; 3) hay un enemigo visible a 12 o menos; 4) la casilla está libre en po_map y hay lugar en la
tabla; 5) tiene oro >= costo de la trampa + 2 × mantenimiento. Una por bando y turno. Manda el mismo paquete que el
humano (TR_PKT), así la trampa queda igual en todas las PC; tr_recv ahora acepta el paquete de un bando de la
computadora sin mirar la máquina. Su propio buscador ya trata sus trampas como intransitables (paso 3).

Eventos: 41 = sembró (n = costo); 42 = pila con «Trap» que no sembró (n = el filtro que falló, 1 a 5).
Solo con DATA\IA.INI y para los colores en prueba, hasta que una tanda lo confirme (regla del repo).
Pruebas: prueba_iatrampas.py (siembra, motivos 1 a 5 y controles), prueba_trampas.py (recepción), regresiones de
pozos, misión trampa e IA de pozos: todas sin fallas.

Próximo paso: tanda TAREAS 212 con Tanda_hex_alianzas (Zapadores y Blade Runners tienen «trap» en los 6 colores; la IA
de prueba va por equipo). La tanda 166 (14/11/2026) se corrió con Tanda_hex_control y no mide nada: una guardada
«_control» pone la IA original en todos los colores (tanda.plan), y tr_ai solo actúa en colores de prueba. Cero
eventos 41/42, como corresponde. Leer cuántos eventos 41 y 42 hay y con qué motivos; si casi todo es 42, revisar el
filtro que más falla. Si siembra, comparar posiciones y bajas enemigas en trampas entre prueba y original.
Frase para retomar: «Seguimos con ia\PENDIENTE-ia-innovaciones.md, resultado del paso 5.3 (tarea 212)».

## Resultado del paso 5.3 (tanda 167 = TAREAS 212, Tanda_hex_alianzas, revisado 14/11/2026)

10 partidas completas, la IA de prueba por equipo (013 o 457). Sembró **11 trampas** en 7 de las 10 partidas
(turnos 14 a 29). No sembró (evento 42): 3690 veces por estar en una ciudad (motivo 1, lo normal: las pilas pasan el
turno ahí), 849 lejos de una ciudad propia (2), 49 sin enemigo cerca (3), 15 sin oro (5); ninguna por casilla
ocupada (4).
**Caídas**: las únicas 2 de la tanda son en esas trampas, de bandos de la IA original, sin verlas: partida 3, turno 22,
(94,64), sembrada ese turno por el color 0, 1 muerto; partida 6, turno 20, (65,148), sembrada el turno 19 por el color
4, 8 muertos. 2 de 11 trampas mataron 9 ejércitos enemigos. Ningún bando de prueba cayó en una propia.
Resultado general: prueba 3,64 de puesto medio y 6,7 ciudades, original 2,79 y 13,9; la misma diferencia que en esta
guardada sin trampas (tanda 40: 3,56 contra 2,77; viene de las reglas de alianzas que solo juega el equipo de
prueba), así que no se le atribuye a las trampas, que cuestan poco y tienen la reserva de oro.
**Decisión** (regla del repo, IA al ranking): avance genuino. Desde **vista-aliada 1.0.220.0** tr_ai juega también sin
IA.INI (las partidas del ranking); con IA.INI, solo en colores de prueba. Paso 5.3 cerrado.
Queda el 5.4 (cerrado: ver abajo).

## Paso 5.4: atacar de noche con monster/demon/undead (14/11/2026)

Primer vistazo, de paso, con datos ya juntados (no es la medición del 5.4): en las guardadas hex la única unidad de
noche es la ranura 11 («undead_b»); en hex_pozos_control y hex_pozos_PV_control (con día/noche) atacó en 87 batallas de
noche y 65 de día, de unas 25.000, y ganó el 94-95 % de día o de noche. Con tan pocas unidades no se puede concluir
nada: hace falta una guardada armada para medir la noche, como se hizo con Carrier (convoy.py) y Trap.

Guardada: `ia
oche.py Tanda_Borderlands _control` escribe Tanda_Borderlands_NO_control.SAV: Day/Night encendido
(SHOPT & 2; offset verificado: 2 en las dos hex_pozos, 0 en las demás) y clase «Undead» (segunda clase, +0xa9) en las
ranuras 1, 3, 5, 7 y 9 de los 8 bandos; con la 11 (Demon) quedan 6 de noche y 6 de día. Se controla sola.
Línea base con la IA original (TAREAS 214): anulada sin correr. La original no tiene código que lea el día/noche
(invento del parche) ni su estimación de ataque pasa por el armado de batalla 0x467240 (no hay llamada desde la IA):
no puede preferir la noche, el resultado se sabía. Objeción del usuario, 14/11/2026.
Próximo paso: programar en la IA de prueba que use la noche (las pilas con mayoría de unidades de noche esperan la
vuelta par para atacar un blanco parejo, y evitan pelear de día contra pilas así) y medirla contra la original con
`noche.py Tanda_Borderlands` (sin _control: la IA de prueba en la mitad de los colores).
Frase para retomar: «Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 5.4: programar la noche en la IA de prueba».

### Paso 5.4, hecho el código: la pila de noche espera la noche (14/11/2026, vista-aliada 1.0.221.0)

`nt_wait` (build.py) corre al final de ai_ally, en al_orig (cuando ni el refugio ni la defensa de ciudades aliadas
decidieron), solo para ia_mode = prueba y solo con IA.INI (ai_ally entero depende de ia_on). La pila no juega ese
turno (al_done, como la refugiada que espera) si: Day/Night puesto y vuelta impar (día); más de la mitad de sus
ejércitos vivos son de noche (no héroes, clase monster/demon/undead en +0xa0 o +0xa9; el héroe cuenta en el total);
y la amenaza al alcance (al_thr, la misma del refugio) es > 0 y al menos la mitad de la fuerza de la pila (blanco
parejo). Contra uno más débil sigue la original, de día. Espera a lo sumo una vuelta: la siguiente es noche.
Evento 43: esperó (x, y = líder, n = amenaza × 1000 + fuerza, topes 999).
Prueba: prueba_ianoche.py (14 casos: espera, segunda clase en mayúscula, monster, borde de la mitad, y controles sin
Day/Night, de noche, sin amenaza, blanco débil, mitad justa de unidades, muertos, héroe, «undeadx»): TODO OK.
Regresiones sin cambios: prueba_iatrampas, prueba_iarazea, prueba_iapuente, prueba_iareconstruye, prueba_noche_razas,
prueba_dianoche; prueba_iaalianzas da las mismas 2 fallas del evento 12 (al_surv) que la 1.0.220.0, ajenas a esto.
No hecho: la contraparte (que una pila sin unidades de noche evite pelear de noche contra una pila de noche): al_thr
suma la fuerza de todos los enemigos sin separar los de noche; queda para después de medir esta.
Guardada: `noche.py Tanda_Borderlands` → Tanda_Borderlands_NO.SAV (sin _control: IA de prueba en la mitad de los
colores). Tanda: TAREAS 215. Al volver: contar eventos 43 por partida y comparar, entre prueba y original, las
batallas de noche y de día de las unidades de noche (ranuras 1, 3, 5, 7, 9, 11), su porcentaje de victorias, puestos
y PV. Si espera mucho y no gana más, la espera cuesta tiempo: revisar el umbral de la mitad.
Frase para retomar: «Seguimos con ia\PENDIENTE-ia-innovaciones.md, resultado del paso 5.4 (tarea 215)».

## Resultado del paso 5.4 (tandas 168 y 169 = TAREAS 215, Tanda_Borderlands_NO, revisado 15/11/2026)

20 partidas completas (30 turnos), 1.0.221.0 (exe d8d8a053), IA de prueba en 4 de los 8 colores, rotando.
**Espera (evento 43): 55 veces**, solo en colores de prueba, en 12 de las 20 partidas (0 a 9 por partida).
Ataques de pilas con mayoría de unidades de noche (ranuras 1, 3, 5, 7, 9, 11), noche = vuelta par:

| IA | de noche | ganados | de día | ganados |
|---|---|---|---|---|
| original | 46 | 96 % | 47 | 87 % |
| prueba | 78 | 92 % | 47 | 94 % |

La prueba corre sus ataques de noche (62 % contra 49 % de la original), pero no gana más: 92 % de noche, menos que de
día. Las pilas sin unidades de noche ganan 85-86 % sea de día o de noche, en las dos IA: el efecto noche del juego
casi no cambia el resultado de batallas que ya se ganan en más de 85 %.
Resultado general (80 colores por IA): prueba puesto 3,33, 7,1 PV y 5,2 ciudades; original 3,26, 6,5 PV y 5,2.
Diferencias del tamaño del ruido (tanda 168 favorece a prueba en PV, la 169 a la original).
**Decisión**: no es avance genuino; nt_wait queda solo en los colores de prueba (con IA.INI), no pasa al ranking.
Tampoco se programa la contraparte (evitar pelear de noche contra pilas de noche): si atacar de noche no ayuda,
esquivarlo tampoco. Paso 5.4 cerrado.
Con esto el orden del paso 5 queda completo (5.1 a 5.4). De la tabla del relevamiento solo queda sin IA «build»
(construir caminos), que es tema de PENDIENTE-construcciones.md.

## Paso 6: medir con el banco rápido y cortar los ataques perdidos (plan acordado con el usuario, 17/11/2026)

Contexto: con el banco en paralelo (8 partidas a la vez, Monitor de IA 1.0.31) 16 partidas tardan ~34 min (tanda
180). Los pasos 5.4 (noche) y los hechizos se descartaron con 20-30 partidas por quedar «dentro del ruido»; ahora se
pueden juntar ~64 partidas en 2,5 h. Toda la IA de prueba ya juega en el ranking (sin IA.INI, desde 1.0.218.0),
salvo nt_wait y hs_w; C:\Warlords tiene el mismo exe que las pruebas (1.0.241.0, verificado 17/11/2026).

**6.1 Medir el ruido.** Con las tandas 176, 177 y 180 (Borderlands_NO, 1.0.236-1.0.241, misma IA) más una serie de
4 tandas de 16: cuánto varía entre tandas la diferencia de PV y de puesto medio prueba − original sin cambiar nada.
Sumar a `ia\informe.py` (o a un informe de serie) el intervalo de esa diferencia, para que cada destreza se juzgue
contra ese número. Sumar 2-3 guardadas Tanda_* de otros mapas a la serie (todas las recientes son Borderlands_NO).

**6.2 Ataques perdidos.** La IA de prueba gana más (180: 8 contra 6 partidas, PV 7,3 contra 6,4) pero pierde más
ejércitos, y en 2 de 3 tandas también más por ataque:

| Tanda | perdidos prueba / original | por 100 ataques prueba / original |
|---|---|---|
| 176 | 62 / 49 | 12,7 / 10,4 |
| 177 | 90 / 74 | 12,0 / 12,3 |
| 180 | 112 / 70 | 13,9 / 10,1 |

Pasos: (a) registrar cada batalla atacando con la fuerza de ambas pilas (ver qué guarda hoy IA_BAT / leer_batallas;
si falta la fuerza, evento nuevo solo con IA.INI); (b) con una serie, la curva desventaja → % ganado; (c) en la IA
de prueba, no atacar por debajo del umbral donde casi siempre pierde; (d) serie de ~64 partidas; si gana igual o
más y no baja el PV, pasa al ranking (regla del repo).

**Menor, para mirar de paso:** en la 180 la prueba dejó sin derribar 25 puentes «en el camino de la pila» (evento
21) contra 10 de la original: ver si es descuido o que los usa más.

### Paso 6.1 y 6.2, hecho (17/11/2026, vista-aliada 1.0.242.0)

**6.1.** `ia\informe.py` imprime ahora «Prueba - original, partida por partida» con el intervalo del 95 %
(1,96·sd/√n) de PV y puesto medio y el veredicto (dentro del ruido / prueba mejor / original mejor). El desvío por
partida es ~5,5 PV y ~1,65 puestos: ±2,7 PV con 16 partidas, ±1,35 con 64. Resultados: 180 sola (16): PV +0,86
(-1,59 a +3,31), dentro del ruido. 176-180 (41): PV +1,33 (-0,36 a +3,02); puesto -0,47 (-0,92 a -0,02), prueba
mejor. 170-180 (99): todo dentro del ruido. Las guardadas de otros mapas siguen pendientes.

**6.2 (a, b).** No hizo falta evento nuevo: la tabla batalla ya tiene los ejércitos por ranura y la fuerza×vida de
cada ranura sale de la guardada. Curva en campo abierto (tandas 170-180, ambas IA): ataque/defensa < 0,5 → gana 3-4 %;
0,5-0,8 → 24-29 %; 0,8-1,2 → 59 %; 1,2-2 → 82-83 %; ≥ 2 → 94-100 %. La prueba dio 119 ataques en campo abierto por
debajo de 0,5 contra 70 de la original: de ahí salen las pérdidas de más. En ciudades la curva no sirve (los
neutrales no están en esa tabla): quedan fuera.

**6.2 (c).** `ap_gate` en build.py, en el call de 0x4c4de7 (la orden de atacar del movimiento de grupo): solo con
IA.INI y color en prueba de la computadora, fuera de ciudad, si la fuerza del grupo (suma de fuerza×vida de sus
vivos) es menos de la mitad de la de los enemigos vivos de la casilla, no ataca y registra el evento 45
(n = grupo·1000 + defensores). Prueba unicorn `parchesista-aliada\prueba_iaataque.py`: 13 casos, TODO OK.
Regresiones iaxxx: sin cambios.

**6.2 (d), próximo:** serie de 64 partidas Tanda_Borderlands_NO con 1.0.242.0 (TAREAS 245). Mirar: cuántos eventos
45, perdidos por 100 ataques, y el intervalo de PV y puesto. Si gana igual o más y no baja el PV, ap_gate pasa al
ranking (sin IA.INI) y se anota en TAREAS actualizar C:\Warlords.

### Paso 6.2 (d), hecho (17/11/2026): ap_gate pasa al ranking (vista-aliada 1.0.243.0)

Tanda 181: 64 partidas Tanda_Borderlands_NO con 1.0.242.0, todas «ok», ninguna cortada.

| | original | prueba |
|---|---|---|
| PV medio por color | 6,1 | 7,8 |
| partidas ganadas | 22 | 37 |
| ataques / perdidos | 2773 / 311 | 3215 / 338 |
| perdidos por 100 ataques | 11,2 | 10,5 (en la 180: 13,9 contra 10,1) |
| ataques evitados (evento 45) | — | 154 |

Prueba − original por partida: PV +1,77 (+0,33 a +3,22), **prueba mejor**; puesto medio −0,48 (−1,02 a +0,05),
dentro del ruido. Gana más y no baja el PV: según la regla del repo, ap_gate queda activo sin IA.INI desde 1.0.243.0
(en bando de la computadora; con IA.INI sigue solo en los colores en prueba). Prueba `prueba_iaataque.py`: 16 casos
OK, incluidos «sin IA.INI corta» y los controles sin IA.INI (humano, ciudad). TAREAS 246: actualizar C:\Warlords.

`ia\informe.py`: un color eliminado tiene puesto vacío. El cálculo del paso 6.1 lo ignoraba (sesgo a favor de la IA
que pierde colores) y se caía cuando una IA perdía todos los suyos en una partida (pasó en la 181). Ahora el eliminado
cuenta como último puesto. Las cifras de puesto de 6.1 (176-180) se calcularon con el sesgo viejo.

**Próximo:** 6.1 pendiente (guardadas Tanda_* de otros mapas) y el punto menor de los puentes del evento 21.

### Paso 6.1, otros mapas (17/11/2026, hecho: tanda 182)

Guardadas: Tanda_Scarpart y Tanda_Kor (sin alianzas, sin Day/Night; las mismas de las tandas 1-165). No se arman
versiones _NO: noche.py cambia clases de unidades para medir la noche y eso no es lo que se mide acá. Tanda: TAREAS 247,
64 partidas con 1.0.243.0 (ap_gate ya activo en los colores en prueba).
Al volver: `python ia\informe.py <tanda>` y por guardada (Scarpart / Kor por separado): intervalo de PV y puesto,
eventos 45, perdidos por 100 ataques. Sirve para dos cosas: (1) ver si ap_gate también gana fuera de Borderlands
(ya está en el ranking; si en estos mapas sale «original mejor», se revisa AP_K); (2) comparar el desvío por partida
con el de Borderlands (~5,5 PV): si es parecido, el ±1,35 PV con 64 partidas vale como vara general.

**Resultado, tanda 182** (64 partidas «ok», 32 por mapa, 1.0.243.0):

| Mapa | PV prueba - original (95 %) | Puesto (95 %) | Ganadas P / O | Eventos 45 | Desvío PV por partida |
|---|---|---|---|---|---|
| Kor (32) | +1,65 (-0,60 a +3,90) | -0,23 (-0,98 a +0,53) | 20 / 11 | 99 | 6,50 |
| Scarpart (32) | -0,39 (-2,56 a +1,78) | +0,04 (-0,68 a +0,76) | 17 / 13 | 13 | 6,27 |
| Los dos (64) | +0,63 (-0,94 a +2,20) | -0,09 (-0,61 a +0,43) | 37 / 24 | 112 | — |
| Borderlands_NO, tanda 181 (64) | +1,77 (+0,33 a +3,22) | -0,48 (-1,02 a +0,05) | 37 / 22 | 154 | 5,89 |

Perdidos por 100 ataques (182): original 10,4, prueba 9,4.

(1) **ap_gate se queda en el ranking.** En ningún mapa sale «original mejor». En Kor va en la misma dirección que
Borderlands (y gana 20 a 11); en Scarpart la regla casi no se dispara (13 eventos 45 en 32 partidas) y el resultado
es neutro, como corresponde a una regla que actúa poco. No se toca AP_K.
(2) **El desvío por partida es parecido** (6,3-6,5 contra 5,9): la vara vale como general, un poco más ancha fuera de
Borderlands: con 64 partidas, ±1,5 a ±1,6 PV (no ±1,35). Una destreza que gane menos de ~1,5 PV por partida
necesita más de 64 partidas para distinguirse del ruido.

### Punto menor de los puentes del evento 21, hecho (17/11/2026, Monitor de IA 1.0.34)

No es descuido: es un artefacto del registro. La pila de la prueba que va a derribar un puente (paso 4 D) deja el
evento 21 n = 2 al llegar a la cabecera y lo derriba **en el mismo turno** (evento 1 n = 101, mismo color y puente).
Sacando esos, los puentes que de verdad quedan en pie son parecidos o menos en la prueba:

| Tanda | Original | Prueba, total | Prueba, derribado ese turno | Prueba, quedó en pie |
|---|---|---|---|---|
| 180 | 10 | 25 | 17 | 8 |
| 181 | 44 | 101 | 71 | 30 |
| 182 | 3 | 26 | 21 | 5 |

`ia\informe.py` (y el Monitor de IA 1.0.34, que lo lleva adentro; desde la 1.0.35 con el botón «Ver el informe de una tanda…») muestra ahora esos casos en una fila aparte,
«en el camino de la pila (lo derribó ese turno)». El parche no cambia.

**Próximo:** no queda nada abierto de este pendiente. Lo que siga en la IA sale de una idea nueva.

## Paso 5.5: qué hace la IA frente a un muro enemigo (propuesta del usuario, 17/11/2026)

Pregunta: ante una muralla, ¿la IA la ataca, la rodea o se congela? Va antes de que la IA construya muros (y mucho
antes de que los repare por iniciativa propia). Hoy se miden solo lo que ya hace la IA original, sin tocarla.

Lo que dice el código (sin verificar en partida):
- `po_pf`: un bloque de muro enemigo en pie no se atraviesa; solo puede ser **destino** del camino (wl_war, en
  guerra). Las metas de la IA son ciudades, pilas, ruinas: nunca un bloque de muro. Hipótesis: la IA rodea el muro
  si hay paso, y si una ciudad queda encerrada no le encuentra camino y la descarta (ni ataca ni se congela: la
  ignora). Si alguna batalla contra un muro aparece, sería de una pila con meta en otra cosa.
- `wv_post` ya llama `ia_bat`, así que una batalla contra un muro queda en IA.CSV, pero sin marca de «muro».
- La IA no construye muros: ninguna guardada de tanda tiene. Las guardadas terminan en bloques opcionales
  (VOTA, POZO, OBRA de 528 bytes: 'OBRA', cantidad, 64 x 8 bytes, 8 de pausas); las Tanda_hex_* terminan en POZO,
  las de Borderlands/Kor/Scarpart en VOTA. Registro de un bloque: x, y (palabras), +4 tipo 7, +6 dueño, +7 muertos.

Plan:
1. **Guardada** `ia\muros.py <guardada>` → `<guardada>_MU.SAV`: anillo de 12 bloques de muro de piedra alrededor de
   la capital de 4 de los 8 colores (48 de 64 registros); los otros 4 son el control dentro de la misma partida.
   Solo casillas de tierra libres (sin agua, puente, ruina, sitio ni otra ciudad); si falta alguna, el anillo queda
   abierto y se anota. Verificar releyendo el archivo y cargándola una vez en el juego (los muros a la vista).
2. **Registro** (vista-aliada, como los eventos 21-27): evento nuevo en `wv_post` cuando ataca la computadora
   (x, y = bloque, n = arqueros muertos en esa batalla + 100 si el bloque cayó); y uno por turno y color cuando una
   pila de la IA termina a 1 casilla de un muro enemigo sin atacarlo (para distinguir «rodea» de «se queda ahí»).
   informe.py: tabla «Muros» por color y por IA.
3. **Tanda** sobre la guardada _MU con la IA original en todos los colores (_control): ataques a muros, bloques
   caídos, pilas quietas junto a un muro, y capitales con muro contra sin muro (cuándo cayeron, cuántas veces se las
   atacó). Con eso se decide si hace falta enseñarle algo a la IA (atacar un bloque como meta, o abrir brecha) antes
   de pensar en que construya.
Hecho (17/11/2026, vista-aliada 1.0.244.0):
- Paso 1: `python ia\muros.py Tanda_hex_control` escribió `Tanda_hex_MU_control.SAV` (en `E:\Warlords-TEST\Warlords3\SAVES`):
  30 bloques en las capitales de 3 de los 6 colores activos (0, 3 y 5; los 1, 4 y 7 son el control). White Main
  (122,79) 8 de 12, Red Main (33,21) 11, Blue Main (93,21) 11: lo que falta es costa, así que por tierra las tres
  quedan cerradas. Verificado releyendo el archivo; falta verlo cargado en el juego (tarea 249).
- Paso 2: eventos **46** (wv_post: la computadora atacó un bloque; n = arqueros muertos, + 100 si cayó) y **47**
  (ai_wobs al empezar el turno: pilas de la IA en las 8 casillas vecinas de un muro enemigo en pie; n = cuántas
  casillas). El 45 ya era «ataque no dado» (1.0.242.0). Solo con IA.INI y bandos de la computadora. Probado en
  `prueba_muroataque.py` (3 casos y 3 controles del 46; 2 casos y 9 controles del 47). informe.py: tabla «Muros».
- Paso 3: tarea 249.

Resultado de la tanda 183 (17/11/2026, 16 partidas sobre Tanda_hex_MU_control, IA original, todas «ok», 30 turnos):
- **La IA casi no ataca el muro**: 1 solo ataque a un bloque en 16 partidas (verde, turno 30, 1 arquero muerto; el
  bloque no cayó). Ningún bloque cayó.
- **No se congela ni lo rodea: se queda pegada al muro y asalta la ciudad.** 190 turnos con pilas junto a un muro
  enemigo (negro 106, amarillo 39, blanco 23, azul 22), casi todo alrededor de Red Main, desde el turno 17-27 hasta
  el final. El anillo deja abierta la casilla de costa, así que la ciudad sigue siendo alcanzable y la IA la ataca.
- **El muro protege mucho**: las capitales amuralladas perdieron 8 de 37 asaltos (Red 6 de 27, Blue 2 de 9, White
  0 de 1); las sin muro, 55 de 76 (Black 27 de 33, Green 22 de 25, Yellow 6 de 18). (Corregido: el «primer asalto en los
  turnos 20-23 contra 13-17» que se dijo al principio era el más temprano de todas las partidas, no el típico. La
  mediana por partida da Red 24 y Blue 27 con muro, contra 21,5 y 24,5 en las tandas de control sin muro 79, 80
  y 166; pero Yellow, sin muro, también se atrasó, de 20,5 a 24,5. La demora no es propia del muro. Lo que sí cambia
  es cuántas veces se las ataca: White, amurallada y casi sin costa, fue atacada en 1 de 16 partidas, contra 16 de 17
  en el control.)
- **Ataques desangrantes contra el muro**: negro asaltó Red Main 8 contra 1 y perdió una y otra vez (partida
  1546: 3 veces; 1547: 4; 1558: 3). Es el mismo error de los ataques perdidos (eventos 45), pero contra una ciudad
  amurallada, donde la regla de 1.0.242.0 no actúa porque solo mira campo abierto.
- Rojo y azul igual terminaron últimos (PV 2,9 y 6,1): el muro les da tiempo, no les cambia la partida (el muro
  está solo en la capital; perdieron el resto de las ciudades).

Conclusión: la hipótesis («la ignora») no se cumple porque el anillo no cierra la ciudad: queda la costa. Lo que
hace la IA es insistir contra la ciudad amurallada sin abrir brecha. Próximo paso posible: (a) que la IA no repita
un asalto perdido contra una ciudad amurallada (como los ataques en campo abierto), o (b) que ataque un bloque de
muro como meta para abrir brecha. Antes de elegir, una tanda con el anillo cerrado del todo (un mapa donde la
capital no tenga costa) mostraría qué hace cuando no hay ningún camino.

Análisis del usuario y plan (17/11/2026):
1. ¿La IA «ve» el muro y junta más fuerza antes de atacar? Los datos no lo muestran. La demora del primer asalto
   también aparece en una capital sin muro, y la fuerza media de los asaltos cambia poco (Red 6,6 contra 5,7; Blue
   6,7 contra 5,2). En el código, la IA original no conoce los muros. Lo único que los muros cambian para ella es el
   camino (po_pf no los atraviesa): una ciudad con menos accesos queda más lejos o sin camino, y por eso se la ataca
   menos (White).
2. **Regla de relación de fuerzas también ante ciudades y muros** (pedido del usuario): antes de asaltar una ciudad,
   o un bloque de muro, comparar la fuerza propia con la defensa contando el bonus del muro, y desistir si no
   alcanza. Excepción, el **ataque de sondeo**: cuando la guarnición no está a la vista y el Combat Advisor está
   apagado. Antes de programarla, averiguar si la IA original ve de verdad las pilas ocultas (si las ve, nunca le
   falta información y la excepción no se usaría). Y como mínimo, no repetir un asalto perdido con el mismo
   atacante, la misma ciudad y la misma composición (negro, 8 contra 1, perdió 3 y 4 veces seguidas).
3. **Abrir brecha por el bloque más débil** (pedido del usuario): cada bloque guarda sus arqueros muertos (+7 del
   registro OBRA, 24 = caído), así que la IA puede elegir el bloque vecino con menos defensores vivos e insistir en
   ese mismo hasta derribarlo.
4. Atacar por la costa: no parece que la IA haya buscado la zona más débil. El buscador de caminos solo encontró la
   única casilla abierta. El efecto es bueno, pero es del camino, no de una evaluación.
Orden propuesto: primero la 2 (evita las pérdidas que ya se ven en la tanda 183), después la 3. Las dos se prueban
con la IA de prueba en una tanda sobre Tanda_hex_MU_control.

### Paso 5.5, punto 2, hecho el código (17/11/2026, vista-aliada 1.0.245.0)

- En ap_gate (0x4c4de7, build.py), cuando la meta del ataque es una ciudad (0x440be0 ≥ 0): la IA original ya
  calcula su probabilidad de victoria (0x497390: 4 × 10 batallas simuladas con la ficha real, que suma el bonus del
  muro y de la ciudad) y solo la escribía en su registro. Ahora la IA **de prueba** no asalta si ese número es menor
  que **AP_PCT = 30 %**. Con eso no hace falta calcular nada nuevo ni consumir azar extra.
- Evento **48** (con IA.INI, todos los bandos de la computadora): asalto evaluado, n = % de victoria, + 1000 si no se
  dio. Tabla nueva del informe, «Asaltos a ciudades»: asaltos por IA y tramo de 10 %, cuántos no se dieron, cuántos
  terminaron en batalla y cuántos ganó el atacante. Sirve para calibrar AP_PCT: si en el tramo 30–39 % la original
  pierde casi siempre, se sube.
- Sin IA.INI (ranking) no cambia nada hasta que una tanda lo confirme.
- **Excepción del sondeo: no implementada.** No encontré el bit del Combat Advisor en las opciones (el candidato,
  [0x53c390] & 2, está apagado en todas las guardadas del banco y del ranking, así que no se puede confirmar). Además,
  la IA calcula con los datos verdaderos de la guarnición, oculta o no: hoy nunca le falta la información. Si se quiere
  el sondeo, primero hay que identificar ese bit (una guardada con el Combat Advisor encendido y otra apagado).
- Bloques de muro sueltos (no ciudades): siguen con la regla de fuerza de campo abierto; el punto 3 los trata aparte.
- Pruebas emuladas: prueba_iaataque (8 casos nuevos: 29 % corta, 0 % corta, 30 y 80 % asaltan, original y ranking
  sin cambio, humano sin cambio, campo abierto igual que antes), prueba_muroataque, prueba_obras, prueba_iatrampas,
  prueba_iarazea: todo OK.
- Medición: TAREAS 250, tanda sobre **Tanda_hex_MU** (copia de Tanda_hex_MU_control sin «_control», para que el
  banco reparta la IA de prueba en la mitad de los colores).

### Resultado de la tanda 184 (TAREAS 250, Tanda_hex_MU, revisado 17/11/2026) y corrección (vista-aliada 1.0.246.0)

- 16 partidas «ok». **Ningún evento 48** en 1401 batallas, 1389 de ellas en casillas de ciudad: la regla de la
  1.0.245.0 no actuó nunca. Los asaltos a ciudades no pasan por 0x4c4de7, sino por la llamada gemela 0x4c50c8 (otro
  paso de 0x4c4a10, que calcula el % en 0x4c50a1 y lo guarda en la pila). La prueba emulada no lo vio porque llamaba
  directo al gancho. Corregido en 1.0.246.0 con ac_gate2 en 0x4c50c8, probado ahora desde el sitio real de la llamada
  (0x4c50c5 a 0x4c50cd), con la posición del % tomada del código del juego.
- Lo que sí mide la 184: con muros y mitad de colores en prueba (regla de campo abierto de 1.0.242.0 activa), PV
  prueba − original −1,08 (−4,82 a +2,66), dentro del ruido. Pilas junto a un muro enemigo: original 160 turnos,
  prueba 16.
- Próximo: TAREAS 251, la misma tanda con la 1.0.246.0.

### Resultado de la tanda 185 (TAREAS 251, Tanda_hex_MU, 64 partidas, revisado 18/11/2026)

- 64 partidas «ok». La regla de 1.0.246.0 **actúa**: la IA de prueba dejó de dar 284 asaltos con menos de 30 %
  (238 en 0–9 %, 29 en 10–19 %, 17 en 20–29 %); de 30 % para arriba asaltó siempre.
- Perdidos por partida, prueba: 6,1 en la 184 → 5,4 (−11 %); ataques casi iguales (37,6 → 36,6). Desangrantes: 5
  contra 25 de la original. Original sin cambio (10,2 → 9,6 perdidos por partida).
- PV prueba − original −0,83 (−2,31 a +0,65), puesto +0,20 (−0,10 a +0,50): dentro del ruido, con un
  intervalo 2,5 veces más angosto que el de la 184. Las diferencias de ciudades (10,6 contra 13,1), ejércitos (41,6
  contra 69,6) y oro (376 contra 184) ya estaban iguales en la 184: no las causa esta regla.
- **Calibración del %** (asaltos de la original, que no corta, ganados sobre batallas): 0–9 % → 5 %; 10–19 % → 16 %;
  **20–29 % → 43 %**; 30–39 % → 50 %; 50–59 % → 63 %; 90–99 % → 92 %. El cálculo del juego subestima en la franja
  media: con AP_PCT = 30 la IA de prueba se priva de asaltos de 20–29 % que la original gana casi la mitad de las
  veces. Por debajo de 20 % sí son pérdidas casi seguras.
- Conclusión: la regla es correcta pero el corte está alto. Próximo paso: AP_PCT = 20 y repetir esta tanda; si los
  perdidos siguen abajo y el PV no empeora, pasa al ranking (sin IA.INI). Hasta entonces queda solo en la IA de
  prueba.

### AP_PCT a 20 (18/11/2026, vista-aliada 1.0.247.0)

- build.py: AP_PCT = 20 (antes 30). prueba_iaataque con los bordes nuevos (19 % corta, 20 % asalta, en 0x4c4de7 y
  0x4c50c8); prueba_muroataque, prueba_obras, prueba_iatrampas, prueba_iarazea: todo OK.
- Medición: TAREAS 258, la misma tanda que la 185 (Tanda_hex_MU, 64 partidas). Comparar con la 185: perdidos por
  partida de la IA de prueba (5,4), asaltos no dados (ahora solo 0–19 %), PV prueba − original (−0,83). Si los
  perdidos no suben y el PV no empeora, la regla pasa al ranking (sin IA.INI).

### Resultado de la tanda 186 (TAREAS 258, AP_PCT = 20, 64 partidas, revisado 18/11/2026)

- 63 «ok» y 1 colgada (n.º 23, turno 1, sin datos). La regla cortó 179 asaltos (0–19 %) y dejó pasar los de 20–29 %:
  la prueba ganó 5 de 17 (29 %); la original, 17 de 43 (40 %, como en la 185).
- Comparada con la 185 (corte 30 %), por partida, IA de prueba: ataques 36,6 → 37,5; perdidos 5,4 → 5,6;
  desangrantes 5 → 9 (en total). PV prueba − original −0,83 → **−0,80** (−2,32 a +0,73); puesto +0,20 → +0,13.
  Todo dentro del ruido: entre 20 y 30 no hay diferencia medible.
- Balance de la regla (184 sin efecto → 185/186): perdidos de la prueba 6,1 → 5,4–5,6 por partida (−10 %), sin
  cambio en PV. Es un ahorro de pérdidas, no una mejora de resultado; no se pasa al ranking por sí sola. Queda
  AP_PCT = 20 en la IA de prueba.
- Próximo: punto 3 (abrir brecha por el bloque de muro más débil). Si con ese punto el PV de la prueba sube, las dos
  pasan juntas al ranking.

### Paso 5.5, punto 3: abrir brecha por el bloque más débil (18/11/2026, vista-aliada 1.0.252.0)

- build.py, ab_brk y ab_cut: cuando la IA de prueba desiste de un asalto a una ciudad (% < AP_PCT, en ap_gate o
  ac_gate2), si el grupo que se mueve (posición del primer ejército del grupo) tiene en sus 8 vecinas un bloque de muro
  en pie de un bando en guerra con ella (wl_war), da la orden de atacar ese bloque (0x4648d0) en vez de quedarse
  quieta. Elige el de más arqueros muertos (+7): así insiste en el mismo hasta que cae (24) y abre paso.
- Evento **49**: x, y = bloque, n = arqueros muertos antes del ataque. La batalla misma sigue en el evento 46.
  informe.py: columna «brechas» en la tabla «Muros».
- Sin IA.INI (ranking) no actúa, porque el corte de ciudades tampoco. Bloques que no son vecinos del grupo: no se
  buscan (no cambia el camino; la IA solo abre brecha donde ya llegó).
- Pruebas emuladas: prueba_muroataque desde el sitio real 0x4c50c5 (3 casos: un bloque, dos bloques eligiendo el más
  dañado, primer lugar del grupo vacío; 6 controles: bloque a 2 casillas, propio, caído, en paz, 50 %, IA original);
  prueba_iaataque, prueba_obras, prueba_iatrampas, prueba_iarazea: todo OK.
- Medición: TAREAS 262, la misma tanda que la 185 y la 186 (Tanda_hex_MU, 64 partidas). Comparar: eventos 49 y
  bloques caídos de la prueba, asaltos ganados a capitales amuralladas, perdidos por partida (5,6 en la 186) y PV
  prueba − original (−0,80). Si el PV sube, la regla de asaltos y la brecha pasan juntas al ranking.

### Resultado de la tanda 187 (TAREAS 262, brecha, 64 partidas, revisado 18/11/2026) y brecha apagada (1.0.254.0)

- 64 «ok». De 266 asaltos cortados, solo 16 terminaron en brecha (evento 49): todas del negro (7), contra el mismo
  bloque (33,20) de Red Main. **Las 16 perdidas**: 9 con un grupo de 1 ejército (murió sin matar ningún arquero) y 7
  con grupos de 8 (murieron los 8, mataron 0 a 3 arqueros cada vez). En total, 65 ejércitos muertos por 8 arqueros
  de 24, y ningún bloque cayó.
- PV prueba − original −0,80 (186) → **−1,46** (−2,99 a +0,08): dentro del ruido, pero hacia abajo. Perdidos por
  partida de la prueba 5,6 → 5,3.
- Conclusión: un bloque entero (24 Longbows virtuales) es demasiado fuerte para un grupo de la IA; abrir brecha solo
  sirve con una fuerza que la IA hoy no junta. **1.0.254.0: AB_ON = False**, ab_cut vuelve al corte simple (código y
  evento 49 quedan para otra vez). prueba_muroataque: los casos de brecha ahora esperan «corta».
- Lo que queda del paso 5.5: la regla de asaltos (AP_PCT = 20) en la IA de prueba, que ahorra pérdidas sin cambiar el
  PV. Si se retoma la brecha, tendría que exigir juntar varias pilas contra el mismo bloque (un objetivo de grupo, no
  de una pila suelta), o atacar solo bloques ya muy dañados.

### Regla de asaltos al ranking (18/11/2026, vista-aliada 1.0.255.0)

- Corrección del criterio (usuario, 18/11/2026: «el ahorro de pérdidas ya es un buen resultado en general, para
  cualquier partida»): una regla que ahorra pérdidas sin empeorar el PV es un avance genuino, aunque no suba el PV. En
  las tandas 185-186, −10 % de ataques perdidos y PV sin cambio medible; la diferencia de PV entre las dos IA ya estaba
  antes de la regla (ciudades, ejércitos y oro iguales desde la 184).
- ap_gate y ac_gate2: sin IA.INI, todo bando de la computadora no asalta una ciudad con % < AP_PCT (20), sin evento.
  Con IA.INI sigue igual (solo la prueba corta; evento 48 en todas). prueba_iaataque: ranking 5 % corta, 20 % asalta,
  humano sin cambio, en los dos sitios.
- TAREAS 263: actualizar C:\Warlords.

### Paso 5.5, punto 4: ¿hay un lado más débil por donde atacar? (18/11/2026, sin cambio de código)

- El bono del muro (wb_near, build.py) lo recibe el defensor de una casilla que es un bloque o que está a 1 casilla
  de un bloque de su bando. Se midió en Tanda_hex_MU_control: las 12 casillas de las tres capitales amuralladas
  tocan de 2 a 5 bloques cada una (White Main, con 8 de 12 bloques: 5, 5, 2 y 2; Red y Blue: 4 o 5). **No hay
  ninguna casilla de la ciudad sin bono**: se la ataque por donde se la ataque, el muro defiende igual.
- La costa abierta solo sirve para llegar, y eso ya lo resuelve el buscador de caminos (po_pf). Elegir un lado no
  cambia la batalla, y el % de victoria que corta los asaltos (punto 2, 0x497390) ya incluye el bono. No hay nada
  que enseñarle a la IA en este punto.
- Lo único que haría variar el lado es un anillo dañado (bloques caídos). Eso depende de la brecha (punto 3,
  apagada), y si se retoma se mira junto con ella.
- **Paso 5.5 cerrado.** Lo que queda abierto: la brecha con varias pilas juntas (punto 3) y que la IA construya
  muros (paso aparte).


## Paso 5.6: la balsa (Raft) en el banco (18/11/2026)

Lo único del relevamiento del paso 5 que nunca se midió en partida: la balsa (1.0.250.0) solo tiene pruebas emuladas
(prueba_balsa.py). La IA no necesita código propio: el buscador de caminos ya agrega los pasos costa-agua y ai_move
parte el grupo al tope de 3 (evento 3).
- `iaalsa.py <guardada>` escribe `<guardada>_RF.SAV` con solo «Raft» en los bonos de movimiento del barco
  (ranura 15) de los 8 bandos (reusa convoy.py). Hechas y verificadas releyendo el archivo: Tanda_Scarpart_RF y
  Tanda_Kor_RF (32 bytes cambiados cada una; antes decían «None»).
- Tanda: TAREAS 264, 64 partidas, las _RF y sus originales en la misma tanda (mismo exe, así el control vale).
- Al volver, por guardada _RF contra su original: eventos 3 (grupo partido al embarcar: si la balsa se usa, tiene
  que aparecer mucho más que en el control), PV y puesto por color, y si hay partidas colgadas que no aparecen en
  el control (caminos nuevos por la costa). Si los eventos 3 salen en 0, primero confirmar que el juego tomó el bono
  (la balsa a la vista en una partida cargada) antes de concluir nada.
- Límite: no hay un evento propio de «zarpó desde una costa sin puerto»; el evento 3 solo cuenta grupos de más de 3.
  Si la lectura no alcanza, se agrega ese evento.

Frase para retomar: «Seguimos con ia\PENDIENTE-ia-innovaciones.md, paso 5.6: terminó la tarea 264».
