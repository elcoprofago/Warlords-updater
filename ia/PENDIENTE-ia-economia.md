# La economía de la IA: aprender a ahorrar — plan (desde el 4/11/2026)

## Objetivo (usuario, 4/11/2026)
Que la computadora aprenda a ahorrar oro, para la estrategia en general y no solo para los puentes:
- reservas para gastos importantes: reconstruir puentes (800 = fundar una ciudad; paso 5.2 de
  PENDIENTE-ia-innovaciones), poner trampas, construir caminos, enviar dádivas o ayudas a aliados;
- evitar el desbande automático de fuerzas que el usuario vio en partidas cuando la IA maneja mal su economía;
- no malgastar: más de tres héroes es casi un derroche, salvo que vengan con descuento.
Texto del usuario: «Seria bueno, no solo para los puentes, sino para la estrategia en general, que la maquina
aprenda a ahorrar oro ... Sospecho que tenemos un largo camino por recorrer con el banco de pruebas.»

## Lo que ya se sabe (datos.db, 4/11/2026, 51.980 turnos-color de la IA viva, todas las tandas)
- Oro: mediana unas 150 por turno en las tandas 131-132; solo el 3,9 % de los turnos llega a 800. Oro = 0 en 32
  turnos; < 50 en 6.920 (13 %).
- Héroes: 0 en 7.530 turnos, 1 en 40.322, 2 en 3.356, 3 en 582, 4 en 166, 5 en 24. Más de tres: 190 (0,4 %).
  **En las tandas la IA casi nunca junta más de tres héroes.** Lo que vio el usuario puede venir de partidas
  reales (con humanos, otros mapas u otra duración) o de partidas más largas que los 30 turnos de las tandas: averiguarlo
  antes de tocar la compra de héroes.
- Caídas de ejércitos de un turno al siguiente sin ninguna batalla de ese color: 2.015, de ellas 116 con oro < 20.
  No es todavía una medida del desbande: pueden ser pozos, trampas, embarques o batallas no registradas.

## Plan
1. **Medir el desbande de verdad.** Ubicar en el exe dónde el juego disuelve ejércitos por falta de oro (el
   mantenimiento por turno) y anotar un evento nuevo (color, ejércitos disueltos, oro antes). Probarlo en emulación.
   Correr una tanda y contar cuántos hay, en qué turno y con qué oro.
   **Hecho en el código (4/11/2026, vista-aliada 1.0.129.0); falta la tanda (TAREAS 108).** Cómo lo hace el juego:
   al empezar el turno (0x42244b), si oro [0x536c14 + p·0x1f8] − mantenimiento [0x5643d8 + 2p] + ingreso
   [0x5643f0 + 2p] < 0, pone la bandera de quiebra [0x536c1c + p·0x1f8] (0x415a00) y aplica el saldo (0x4b9390).
   Después 0x4159d0 → 0x415910(p): cada ejército vivo de p que no sea héroe y tenga algún bit 0xf0 en +0x10 deserta
   con 20 % (0x4deb20(1, 100) ≤ 20 → 0x4b9e20); cuenta en [0x4f9894] y, al humano, «%d troops desert your cause»
   (Sagetext 0x90, 0x4158a0). Es aparte del desbande por **maná** (0x490xxx, «banished creatures», grupo 0x1e7),
   que todavía no se anota. Evento 28 (ds_evt, gancho en 0x415995): x, y del ejército, n = oro en ese momento.
   Prueba emulada: `parches\vista-aliada\prueba_desbande.py` (3 guardadas, 8 colores: 438 deserciones anotadas
   = conteo propio; controles: azar 21 → ninguna; sin ia_on → desertan sin anotarse).
   **Medido (5/11/2026, tandas 133 y 134, 1.0.129.0, 17 partidas completas, 136 bandos-partida):** 52
   deserciones en 7 episodios (5 %): todas con oro 0, todas en un bando que ya se derrumbaba (perdía ciudades ese
   turno o el anterior; p. ej. tanda 134 partida 6, color 3: 3→1 ciudades y 22→11 ejércitos en 2 turnos). 5 de 7
   episodios en la IA nueva, 2 en la original; 6 de 7 en los turnos 24-30. Conclusión: en 30 turnos el desbande es
   raro y es consecuencia de perder ciudades (se cae el ingreso), no de gastar de más con la economía sana. Una
   reserva no lo evitaría; lo que pesa es no perder ciudades. Queda por ver en partidas más largas (paso 3).
   Aparte: 3 partidas de la 134 quedaron «colgadas» en el turno 0 (la 133, mismo exe, ninguna): sin causa vista.
   Pendiente sin comprobar: qué marca el bit 0xf0 de +0x10 (¿ejércitos con mantenimiento?).
2. **Medir el gasto.** Por turno y color: ingreso, mantenimiento, producción, héroes comprados (con y sin
   descuento), y lo que sobra. Ver si la tabla turno alcanza o hace falta otro evento.
   **Hecho en el código (5/11/2026, vista-aliada 1.0.130.0); falta la tanda (TAREAS 110).** La tabla turno no
   alcanza: anota el oro en 0x4223ad, antes de que el juego calcule el ingreso (0x43ff80) y el mantenimiento
   (0x4406b0) y aplique el saldo en 0x42248d → 0x4b9390. Evento 29 (ec_evt, en 0x422482): x = ingreso, y =
   mantenimiento, n = oro en ese momento. Cuentas por color y turno t: turno.oro(t) − n = lo cobrado al empezar el
   turno antes del saldo (producción); n + x − y − turno.oro(t+1) = lo gastado durante el turno (héroes, puentes;
   negativo si ganó oro, p. ej. ruinas o saqueo); heroes(t+1) − heroes(t) = héroes comprados (sin distinguir
   descuento todavía). Prueba emulada: `parches\vista-aliada\prueba_saldo.py` (3 guardadas, 8 colores, 4 casos con y
   sin quiebra: 96 líneas correctas, quiebra y saldo iguales al original; control sin ia_on: nada anotado).
   **Medido (6/11/2026, tandas 135 y 136, 1.0.132.0, 19 partidas completas, 3.526 turnos-color con t y t+1):**
   | | IA original | IA nueva |
   |---|---|---|
   | ingreso total | 182.892 | 144.188 |
   | mantenimiento | 60.412 (33 %) | 42.912 (30 %) |
   | gastado en el turno | 111.931 (61 %) | 93.251 (65 %) |
   | ahorrado | 10.549 (6 %) | 8.025 (6 %) |
   Oro al empezar el turno: mediana 150 en los turnos 1-10, 11-20 y 21-30, en las dos IA, aunque el ingreso se
   triplica (50 → 165). O sea: **la IA gasta todo lo que le sobra y no ahorra**; el mantenimiento crece con el
   ejército (5 → 72 por turno) y se come cada vez más. Turnos con 800 o más: 4 % (IA nueva 1 de 434 en los turnos
   21-30). Mantenimiento mayor que el ingreso: 44 de 3.526 turnos. Terminan el turno con menos de 50: 12 %.
   Hallazgos de la medición: (a) «producción» = turno.oro − n dio 0 siempre: la tabla turno anota el oro en el
   mismo momento que el evento 29, así que no se cobra nada antes; la producción se paga durante el turno y queda
   dentro de «gastado». (b) Los 54 héroes nuevos aparecen en turnos con gasto 0 (mediana): su pago no cae en esta
   ventana o vienen gratis (sin comprobar). Para separar producción de héroes y puentes haría falta otro evento
   en el cobro de la producción; por ahora no hace falta: el diagnóstico ya es claro (gasta todo, en tropas).
3. **Contrastar con partidas reales.** Usar el Visor de historia o las guardadas del ranking del clan para ver si
   más de tres héroes y el desbande aparecen ahí y no en las tandas.
   **Hecho (6/11/2026).** Guardadas de partidas en red reales que quedan en la PC: C:\Warlords\NETSAVES,
   C:\Warlords3\NETSAVES, C:\Warlords\HISTORY y la papelera (NA_*, NAB_002, NA-004, xMapaPozos, xSORTEO, xvotacion,
   xx; 34 archivos, unas 14 partidas, rondas 1 a 30; las abn_009 y BAN_001 ya no están). Leídas con
   historia.Partida: héroes vivos (ranura 0x10 de los ejércitos de 0x54fe50), oro (+0xe4), humano (+0xe2 = -1) y el
   historial (0xe surge un héroe, 0xf muere, 0x10 «is disbanded»). Script de la sesión, sin versionar (lectura única).
   - **Héroes:** la IA nunca tiene más de 3 vivos a la vez (3 en NA_003 color 1 y xvotacion color 7); en toda la
     partida le surgen como mucho 5, casi todos para reponer muertos (p. ej. NA_006 color 4: 5 surgidos, 4 muertos).
     Los humanos, igual (máximo 3). **Más de tres héroes no aparece ni en las tandas ni en las partidas reales que
     hay.** No se toca la compra de héroes por ahora; queda la sospecha para partidas de más de 30 rondas, de las
     que no hay ninguna guardada.
   - **Desbande:** el juego no lo anota en el historial ni en la guardada, y el evento 28 solo se anota en tandas
     (con ia_on): en partidas reales no se puede contar. Lo que sí se ve coincide con el paso 1: la IA con oro 0 o
     casi es siempre un bando que se derrumba (NAB_002 color 0: oro 0 y 17→15 ejércitos; NA-004 color 7: oro 3→0 y
     30→18 ejércitos; NA_2 color 0: oro 18 y 10 ejércitos). Los bandos sanos de la IA cierran con 100 a 900.
   - **Hallazgo aparte:** en xMapaPozos la IA **despide** héroes: colores 1 y 4, rondas 10 y 11, «is disbanded!»
     poco después de tener un segundo héroe, con oro 400-900 (no por quiebra). Sin averiguar por qué (¿tope de la IA
     original, o el héroe sin ejército?): mirarlo en el paso 4 antes de poner un tope propio.
   Conclusión para el paso 4: lo medible es que la IA gasta todo (paso 2), no los héroes ni el desbande de bandos
   sanos. La reserva se diseña para el gasto y los usos con destino; el tope de héroes queda en segundo plano.
4. **Diseñar la reserva**, con lo medido: un piso de oro para el mantenimiento de los próximos turnos (contra el
   desbande), un tope de héroes salvo descuento, y un ahorro con destino (puente que abre camino, trampa, camino,
   ayuda a un aliado) cuando haya un uso concreto con valor.
   **4.1 Primero, en qué se va el 61-65 % «gastado» (6/11/2026, vista-aliada 1.0.133.0; falta la tanda, TAREAS 121).**
   Sin eso la reserva se diseña a ciegas: no se sabe si frenar producción, compras de unidades, héroes u otra cosa.
   En el exe original, 0x4b9390 no toca el oro: arma el paquete 0x151 (0x4dd3b0). El oro de un color lo cambian
   0x43fd60(jugador, cantidad) —suma, topes 0 y 32000 (0x7d00), libro 0x41bee0 en 0x503170 con 2 = gasto y 4 =
   ingreso— y tres escrituras directas (0x433a00 add, 0x470016 y 0x4701ad mov). Llaman a 0x43fd60 16 lugares:
   0x4054e9, 0x438111, 0x43aec5, 0x455303 (+10000: ¿truco?), 0x4663ad y 0x4663cd (cobra a uno y le da la mitad a
   otro: ¿saqueo?), 0x4756ad y 0x4ac4e9 (dueño sacado del ejército, +0xe), 0x48bae5 (cantidad × porcentaje / -10),
   0x48f1c8, 0x4afa9f, 0x4b6625, 0x4b7ec8, 0x4d2ac6, 0x4d6176 y 0x4d6418 (con mensaje 0x15/0x16 de 0x572ab0), más
   los del parche (puentes 0x6cb9xx, caminos y trampas). Cuál es cuál está **sin comprobar**: se lee de la tanda
   (qué dirección aparece al comprar un héroe o al terminar una unidad) y se confirma en el exe.
   Evento 30 (gl_evt, en la entrada de 0x43fd60): x = dirección de retorno de quien llamó, y = cantidad (negativa
   si gasta), n = oro antes. Las escrituras directas no se anotan todavía: si en la tanda la suma de eventos 30 no
   cierra con «gastado» del paso 2, se agregan. Prueba emulada: `parches\vista-aliada\prueba_oro.py` (3 guardadas,
   8 colores, 5 casos con topes: 144 controles; oro final, libro y registros iguales al original; sin ia_on nada).
   Al volver la tanda: sumar por dirección y por IA (original/nueva), ponerle nombre a cada dirección y recién ahí
   decidir dónde va el freno de la reserva.
   **Medido (6/11/2026, tanda 137, 1.0.133.0, 10 partidas completas, eventos 30; IA original / nueva):**
   | quién | qué es | IA original | IA nueva |
   |---|---|---|---|
   | 0x48bae5 | comprar un tipo de unidad para una ciudad (costo de +0xe2 del registro de unidad 0x53c410 con su % ; 300, 350, 520, 1000) | −98.630 | −79.450 |
   | 0x4054e9 | pago fijo en una ciudad, mensaje 0x1b (100, 300, 400) — **sin comprobar qué es** | −40.080 | −33.770 |
   | 0x43aec5 | comprar héroe (el color tiene un héroe más al turno siguiente: +0,97) | −13.847 | −6.504 |
   | 0x4663ad / 0x4663cd | al perder una ciudad se le cobra al dueño y el que la toma recibe la mitad | −6.876 / +3.266 | −5.217 / +2.704 |
   | 0x4756ad | dueño de un ejército, 166-900 — sin comprobar | −2.758 | −2.611 |
   | 0x4b7ec8 | saldo del turno (ingreso − mantenimiento) aplicado por el paquete 0x151 | +84.928 | +71.204 |
   | 0x4d6176 | oro al tomar ciudad, mensaje 0x15 (26-583) | +36.724 | +32.091 |
   | 0x4ac4e9 / 0x438111 | premios grandes (311-3.041): ruinas o tesoros, sin comprobar | +22.071 / +17.157 | +13.074 / +11.158 |
   Del gasto (~290.000 en total): **61 % comprar tipos de unidad**, 25 % el pago fijo en ciudad, 7 % héroes, 4 % lo
   que se pierde con las ciudades. Las unidades en sí no cuestan al salir (no hay evento por unidad terminada): el
   costo es la compra del tipo y después el mantenimiento. No aparecieron 0x455303, 0x48f1c8, 0x4afa9f, 0x4b6625,
   0x4d2ac6, 0x4d6418 ni los del parche (puentes, caminos, trampas).
   Para la reserva: el freno va en 0x48bae5 (no comprar un tipo nuevo si deja el oro por debajo del piso) y quizás
   en 0x4054e9, que antes hay que identificar (leer 0x572ab0 mensaje 0x1b y quién llama a la función de 0x4054e9).
5. **Banco de pruebas:** tandas IA de prueba contra original, con PV y desbandes, como en los pasos anteriores.
   Trampas, caminos y dádivas de la IA todavía no existen (paso 5 de PENDIENTE-ia-innovaciones): la reserva se
   diseña para poder sumarlos después.

   **0x4054e9 identificado (6/11/2026, exe original): es agrandar una ciudad.** Está en 0x405310(ciudad, tamaño
   nuevo, costo): pone el tamaño en +0xa4 del registro de ciudad (0 = arrasada, máximo 3) y en los bits 0x300 de la
   casilla del mapa (0x503e58), vacía las 4 ranuras de unidades de la ciudad («EMPTY», +0xaa, 9 bytes cada una),
   avisa con el mensaje 0x1b y cobra con 0x43fd60. El costo lo calcula la función de 0x405200-0x405307 según
   tamaño actual y nuevo: 1→2 = [0x569512], 2→3 = [0x569514], 1→3 = las dos sumadas; a la mitad si el jugador
   tiene [0x536c12 + p·0x1f8] ≠ −1, y con un ajuste de porcentaje (0x4057a0, ÷ −10) como el de 0x48bae5. Los
   100/300/400 de la tanda calzan con 1→2, 2→3 y 1→3. Llamadores: 0x4b7e2f (paquete de red: así lo pide la IA o el
   humano) y 0x455afc (todas las ciudades de un color a tamaño 3 gratis; ¿escenario o truco?). Sin comprobar:
   cuánto ingreso o producción da cada tamaño, y si vaciar las ranuras obliga a volver a comprar tipos de unidad
   (eso sumaría a 0x48bae5).
   **Diseño de la reserva (con lo medido):**
   - Piso = mantenimiento de los próximos 2 turnos (y del evento 29; hoy 5-72 por turno), nunca menos de 50.
   - Freno en 0x48bae5 (comprar un tipo de unidad) y en 0x405310 (agrandar ciudad): la IA no gasta si el oro
     quedaría por debajo del piso + lo apartado con destino. No se toca 0x43aec5 (héroes, 7 %, nunca más de 3).
   - Ahorro con destino: cuando la IA marca un puente a reconstruir (paso 5.2 de PENDIENTE-ia-innovaciones),
     aparta 800 y los frenos de arriba lo respetan hasta gastarlo o descartar el destino.
   - Solo en la IA nueva (ia_on), para comparar contra la original en el paso 5.

   Datos del usuario (6/11/2026): el costo a la mitad es cuando el bando tiene «engineering» o «artificer»
   ([0x536c12] es entonces esa habilidad, sin comprobar en el exe); poner todas las ciudades en tamaño 3 gratis
   (0x455afc) sería alguna modalidad de escenario al azar («crusade», para uno solo, o «battle of Titans»; no seguro).
   **Agrandar no da ingreso (6/11/2026):** el ingreso del turno (0x43ff80) suma +0xa7 de las ciudades con
   tamaño > 0, y la función que agranda no toca +0xa7; en ABN_000_29.SAV la mediana de +0xa7 es 23 en tamaño 1
   (27 ciudades), 2 (24) y 3 (18). Agrandar compra defensa, no renta: se puede frenar igual que la compra de tipos.

   **Camino del pedido de agrandar (6/11/2026, exe original):** el paquete es el 0x1c8 (tabla de 0x4b6a30: índice
   0x1c8 + 8 → caso 0x97 → 0x4b7e1e → 0x405310(ciudad, tamaño, costo)). Lo arma 0x4b9ca0(ciudad, tamaño, costo),
   cuyo único llamador es 0x4b7451, dentro del mismo despachador (reenvío del anfitrión). El costo lo calcula
   0x4051a0, que llaman 0x4041a0 (¿ventana de ciudad del humano?, llamada desde 0x401b54, 0x4040fa, 0x40e92f y
   0x49acd4) y 0x404f30. **Sin ubicar todavía dónde decide la IA agrandar.** No hace falta para el freno: se
   pone en la entrada de 0x405310, que corre en el anfitrión para todos los pedidos; con ia_on y dueño de la IA,
   si el oro menos el costo queda bajo el piso, no agranda ni cobra (la IA lo puede volver a pedir otro turno).

   **Piso y frenos programados (6/11/2026, vista-aliada 1.0.134.0; falta publicar y la tanda, TAREAS 123).**
   rs_ok(p, costo, tipo): con ia_on, IA_MODE[p] = 1 (en prueba) y bando de la computadora ([0x536c12] ≠ −1), piso =
   2 × mantenimiento del turno [0x5643d8 + 2p], nunca menos de 50; si oro − costo < piso, no gasta. Frenos en la
   entrada de 0x48ba50 (rs_unit; costo calculado como el original: [0x53c4f2 + (16p + tipo)·0xfc] con el ajuste del
   5.º argumento ÷ −10) y de 0x405310 (rs_grow; costo = 3.er argumento, dueño = +0xa5 de la ciudad). Único
   llamador de 0x48ba50: 0x4b72f9, el mismo despachador de red que 0x405310. Evento 31 cada vez que frena (x = 1 tipo
   de unidad, 2 agrandar; y = costo; n = oro). Ahorro con destino (800 para un puente) todavía no: va cuando el
   paso 5.2 de PENDIENTE-ia-innovaciones marque el puente a reconstruir.
   Prueba emulada: `parches\vista-aliada\prueba_reserva.py` (3 guardadas, 8 colores, 848 controles): frena justo
   bajo el piso y sigue justo en el piso, con el mismo costo que cobra el original; controles humano, IA original,
   sin ia_on, ciudad ajena y agrandar gratis: igual que el original y sin evento 31. prueba_oro.py sigue OK.
   Corrección: la mitad de costo de agrandar (0x405235) es para los bandos de la computadora ([0x536c12] ≠ −1,
   que es «no humano» en todo el parche), no «engineering/artificer»; esos atributos irían en el ajuste de 0x4057a0
   (sin comprobar).
   Al volver la tanda: comparar IA nueva contra original en PV, ciudades, desbandes (evento 28), oro al empezar el
   turno y cuántas veces frena (evento 31) y en qué.

   **Medido (6/11/2026, tanda 138, 1.0.134.0, 10 partidas completas; mismo plan que 135-137):**
   | | original 138 | nueva 138 | nueva 137 (sin freno) |
   |---|---|---|---|
   | PV medio | 6,3 | 6,7 | 6,6 |
   | puesto medio | 3,19 | 2,65 | 3,20 |
   | ciudades al final | 5,1 | 4,5 | 5,1 |
   | oro al empezar el turno (mediana) | 148 | 208 | 147 |
   | turnos con < 50 / con ≥ 800 | 12,0 % / 3,8 % | 1,1 % / 6,2 % | 12,4 % / 2,5 % |
   | compra de tipos / agrandar / héroes | −92.740 / −44.920 / −12.288 | −74.290 / −26.020 / −10.990 | −79.450 / −33.770 / −6.504 |
   | deserciones (evento 28) | 6 en 2 episodios | 31 en 5 | 26 en 3 |
   Frenos (evento 31): 348 compras de tipo (costo medio 375) y 127 agrandamientos (294). La reserva funciona: casi
   desaparecen los turnos con la caja vacía y la IA nueva termina mejor ubicada (puesto 2,65 contra 3,19), con
   menos ciudades. Parte de lo ahorrado se va en héroes (−6.504 → −10.990).
   **Lo que el freno no cubre:** 26 de las 31 deserciones son de un solo bando (partida 964, color 2, IA nueva):
   con 7 ciudades y sin comprar casi nada (frenado en los turnos 15-21), su mantenimiento subió de 65 a 306 por
   turno mientras el ingreso quedaba en 163-212: el ejército crece con los tipos **ya comprados**, la producción no
   cuesta al salir y el mantenimiento termina pasando al ingreso (turno 22). Mantenimiento mayor que el ingreso en
   la 138: 22 turnos-color en la IA nueva, 16 en la original. Un piso de oro no lo evita: hace falta frenar la
   **producción** cuando el mantenimiento se acerca al ingreso.

**Freno de producción (6/11/2026, vista-aliada 1.0.135.0; falta la tanda, TAREAS 124).**
Dónde produce una ciudad (exe original): 0x43b930(p), paquete de red (llamado desde 0x4b7c1b), recorre las ciudades
de p; +0xd8 = turnos que faltan, +0xd7 = tipo. Con +0xd8 = 1, en 0x43bdf2 crea la unidad (0x43b120, o 0x43b390 si va
dirigida a otra ciudad, +0xd9/+0xda) y 0x4ae250 reinicia la cuenta con el tipo +0x9d. Ejércitos: 0x46c330 toma un
registro libre. Mantenimiento de un ejército: bits 0xf0 de +0xe (= tipo +0x9e con ajustes de objetos, 0x43b6d0
salida[4]); 0x4406b0 lo suma por color: mínimo 4 con el bit 8 de +0x12, y un tercio (mínimo 1) si está en una casilla
de ciudad no arrasada, salvo con el bit 0 de +0xb (la producción no lo pone). O sea: se paga por dónde termina el
turno, no por moverse; esperar en una ciudad ahorra dos tercios (sin comprobar en partida).
Freno (pr_ok, pr_unit en 0x43bdf2): con ia_on, IA_MODE[p] = 1 y bando de la computadora, si 10 × (mantenimiento
[0x5643d8 + 2p] + lo producido por p en este turno + mantenimiento entero de la unidad nueva) > 9 × ingreso
[0x5643f0 + 2p], no crea ni reinicia: la cuenta queda en 1 y lo vuelve a intentar el turno siguiente. Evento 32
(x = tipo, y = ese total, n = ingreso). La unidad nueva se cuenta entera (lo que paga al salir de la ciudad): puede
frenar de más; la tanda lo dirá.
Prueba emulada: `parches\vista-aliada\prueba_produccion.py` (corre 0x43b930 real; 3 guardadas, 1.956 controles,
TODO OK): sale justo en el límite y frena uno por debajo, acumula dentro del turno y se reinicia al siguiente;
controles humano, IA original y sin ia_on igual que el original y sin evento 32.
Idea para después: que la IA deje en una ciudad los ejércitos sin tarea (pagan un tercio).
Al volver la tanda: comparar con la 138 (PV, puesto, ciudades, desbandes del evento 28, mantenimiento > ingreso,
cuántas veces frena el evento 32).
**Medido (7/11/2026, tandas 140 y 141, 1.0.135.0, 20 partidas completas; la 139 se cortó con 2 partidas sin terminar):**
| | original 140-141 | nueva 140-141 | nueva 138 (sin freno de producción) |
|---|---|---|---|
| PV medio | 7,14 | 6,60 | 6,70 |
| puesto medio | 3,13 | 3,10 | 2,65 |
| ciudades al final | 5,3 | 4,7 | 4,5 |
| oro al empezar el turno (mediana) | 150 | 203 | 208 |
| turnos con < 50 / con ≥ 800 | 12,9 % / 3,7 % | 0,9 % / 3,8 % | 1,1 % / 6,2 % |
| mantenimiento > ingreso (turnos-color) | 28 de 1.987 | 25 de 1.956 | 22 de 930 |
| deserciones (evento 28) | 17 en 2 bandos | **0** | 31 en 1 bando |
Frenos: evento 31 (reserva) 1.024 veces; evento 32 (producción) 200 veces en 33 bandos-partida, 146 de ellas en los
turnos 20-29. Gasto (20 partidas, original / nueva): tipos de unidad −184.070 / −170.950, agrandar −87.160 /
−64.620, héroes −18.923 en la nueva.
Lectura: **el freno de producción elimina el desbande** (0 deserciones en 20 partidas), y la reserva sigue
evitando la caja vacía. Pero **se pierde la ventaja de la 138**: el puesto queda igual que la original (3,10 contra
3,13), con menos PV y menos ciudades. Los 25 casos de mantenimiento mayor que el ingreso que quedan son casi todos
(18) de bandos que perdieron ciudades en los 2 turnos anteriores: se cae el ingreso, no es producción de más.
Sospecha: el freno corta tropas justo en los turnos 20-29, cuando se decide la partida, y frena de más porque
cuenta la unidad nueva con su mantenimiento entero aunque se quede en la ciudad (paga un tercio).
**Paso 4.3: freno aflojado (7/11/2026, vista-aliada 1.0.136.0; medido en las tandas 142-143, TAREAS 125).**
pr_ok cuenta la unidad nueva como la cobra 0x4406b0 en una casilla de ciudad (comprobado en el exe original,
0x440797: `idiv 3`, truncado, mínimo 1; 0 si el mantenimiento es 0) y frena solo si mantenimiento + lo producido en
el turno + ese tercio > ingreso (antes 10 × … > 9 × ingreso, con la unidad entera). Lo acumulado en el turno también
suma el tercio. prueba_produccion.py ajustada a la regla nueva: 1.812 controles TODO OK (ABN_000_29, agua03 e
IA_ROTADA de C:\Warlords3\Saves; ia_on 0x6c9dfb, ia_mode 0x6c9df3); prueba_reserva.py sigue OK (1.168).
Uso: `python prueba_produccion.py C:\Warlords3\DarklordAV.exe C:\Warlords3\Darklord.exe 6c9dfb 6c9df3 <SAV>...`.
Al volver la tanda: comparar con 138 (sin freno de producción) y 140-141 (freno al 90 % con la unidad entera) en
puesto, PV, ciudades, deserciones (evento 28), mantenimiento > ingreso y veces que frena (evento 32, y en qué turnos).
Si vuelven las deserciones, el punto medio es el 100 % con la unidad entera, o el tercio con 90 %.
**Medido (8/11/2026, tandas 142 y 143, 1.0.136.0, 20 partidas completas):**
| | original 142-143 | nueva 142-143 | nueva 140-141 (freno al 90 %, unidad entera) | nueva 138 (sin freno) |
|---|---|---|---|---|
| PV medio | 6,40 | 6,42 | 6,60 | 6,70 |
| puesto medio | 3,08 | 2,95 | 3,10 | 2,65 |
| ciudades al final | 5,1 | 4,6 | 4,7 | 4,5 |
| primeros puestos | 11 | 9 | 10 (orig. 13) | 6 (orig. 4) |
| oro al empezar el turno (mediana) | 148 | 204 | 203 | 208 |
| turnos con < 50 / con ≥ 800 | 13,4 % / 4,8 % | 0,9 % / 3,8 % | 0,9 % / 3,8 % | 1,1 % / 6,2 % |
| mantenimiento > ingreso | 40 de 1.884 | 42 de 1.916 | 25 de 1.956 | 22 de 930 |
| deserciones (evento 28) | 16 en 3 bandos | 17 en 3 bandos | 0 | 31 en 1 bando |
Frenos: evento 32 132 veces en 19 bandos-partida (98 en los turnos 20-29; antes 200 en 33); evento 31 913.
Lectura: aflojar el freno recupera algo de puesto (2,95 contra 3,08 de la original en las mismas partidas; en la
140-141 estaban iguales), sin volver a la ventaja de la 138. **Las 17 deserciones no son producción de más**: los 3
bandos venían perdiendo ciudades (6→4→2, 3→2→1, 6→6→2 en los 2 turnos previos) y el freno ya estaba frenando
(2 a 23 eventos 32 en los 3 turnos anteriores). Se cae el ingreso de golpe y el ejército ya existente no se paga;
la original tiene lo mismo (16 en 3 bandos, también tras perder ciudades). De los 42 mantenimiento > ingreso, 26
siguen a una pérdida de ciudades. **Se queda la 1.0.136.0** (freno al 100 % con el tercio): cumple el objetivo
del freno, que es no fabricar lo que no se puede pagar.
Lo que queda del desbande es del colapso, no del gasto. Próximo paso (4.4): la idea de arriba, que la IA deje en
una ciudad los ejércitos sin tarea (pagan un tercio): baja el mantenimiento en todo momento y deja margen para
cuando se pierden ciudades. Primero ubicar en el exe dónde la IA decide el destino de un ejército sin tarea.
**Paso 4.4, primero medir (8/11/2026, vista-aliada 1.0.137.0; falta la tanda, TAREAS 126).**
Lo que ya hace el juego: una pila sin otra meta va a «Form» (meta 1, juntarse en una ciudad, 0x40db40); o sea, la IA
ya lleva a las ciudades a las pilas sin nada que hacer. No hay guardadas de mitad de tanda (solo la inicial y los
resultados), así que no se sabe cuánto paga la IA por ejércitos que terminan el turno afuera.
Evento 33 (mt_evt, llamado desde ec_evt después del 29, solo anota): por color, el mismo recorrido que 0x4406b0;
x = mantenimiento entero de los ejércitos fuera de una casilla de ciudad, y = lo que pagarían en una ciudad (tercio
truncado, mínimo 1), n = cuántos son. x − y = el techo de lo que ahorraría llevarlos a todos a una ciudad (de más:
muchos están afuera porque van a atacar o explorar).
Prueba emulada: `parches\vista-aliada\prueba_mantenimiento.py` (120 controles TODO OK con IA_ROTADA, Tanda_Kor_CA,
roads02, ABN_000_29 y agua03): un modelo en Python da el mismo mantenimiento que el 0x4406b0 original en cada color,
el evento 33 coincide con el modelo, un ejército movido a mano a una ciudad o afuera cambia lo esperado, sin ia_on no
anota. prueba_saldo.py ajustada (después del 29 viene el 33): OK; prueba_produccion (3.272) y prueba_reserva (1.664) OK.
Referencia, partida real ABN_000_29 (turno 29): los de fuera de ciudad pagan del 15 % al 65 % del mantenimiento de
cada color (p. ej. color 6: 22 ejércitos, 67 de 147; en una ciudad pagarían 29).
Al volver la tanda: por IA y por tramo de turnos, x / mantenimiento (evento 29, y) y (x − y) / ingreso. Si el techo
del ahorro es chico (menos del 5 % del ingreso), la idea no vale y se descarta; si es grande, ver qué metas tienen
esas pilas (hace falta otro evento en 0x40ca70 con la meta elegida) antes de cambiar nada.
**Medido (8/11/2026, tanda 144, 1.0.137.0, 10 partidas completas):** evento 33 cruzado con el 29 por color y turno.
| | tramo | fuera / mantenimiento | techo (x − y) / ingreso | pilas fuera (media) | turnos-color con techo > 5 % |
|---|---|---|---|---|---|
| original | 1-10 / 11-20 / 21-30 | 21 % / 26 % / 30 % | 1,2 % / 5,5 % / 9,6 % | 0,1 / 0,9 / 2,0 | 7 % / 27 % / 36 % |
| nueva | 1-10 / 11-20 / 21-30 | 31 % / 32 % / 44 % | 2,4 % / 7,7 % / 15,3 % | 0,2 / 1,5 / 4,1 | 10 % / 35 % / 48 % |
Total: 35 % del mantenimiento lo pagan ejércitos fuera de ciudad; el techo del ahorro es el 8,5 % del ingreso (en la
nueva, 15 % en los turnos 21-30). **Supera el 5 %: la idea sigue.** Es un techo: muchas de esas pilas atacan o exploran.
Resultados (no cambia el juego): nueva puesto 2,89, PV 7,67, 5,4 ciudades, 9 primeros; original 3,46 / 4,92 / 3,5 / 3.
Deserciones (evento 28): 14 en 4 bandos (10 de la original).
Próximo paso (4.5): evento 34 en 0x40ca70 con la meta elegida para cada pila de la IA que termina fuera de ciudad, para
saber cuánto del techo es de pilas sin tarea (meta «Form» o ninguna) y cuánto de pilas que atacan o exploran.
**Paso 4.5, medir la meta de los de fuera (8/11/2026, vista-aliada 1.0.138.0; falta la tanda, TAREAS 127).**
me_set, en 0x40cc3f de 0x40ca70 (justo antes del salto por la tabla de metas 0x40d02c, con la meta ya elegida por el
planificador o por arg): anota en ME_TAB[ejército] meta + 1 y el byte bajo de la ronda [0x503328] para los 8
ejércitos de la pila [0x5020d4] + 0xc. mt_evt, para cada ejército de fuera de ciudad, toma esa meta si es de esta
ronda o de la anterior (si no, 10 = sin decisión) y anota el evento 34 por meta: x = meta (0 ninguna, 1 Form, 2 ruina,
3 neutral, 4 ítem, 5 héroe, 6 misión, 7 ciudad enemiga, 8 sitio, 9 reconstruir, 10 sin decisión), y = ahorro
(entero − tercio), n = cuántos. La suma de los 34 de un color es x − y y n del 33. Solo anota.
Sin comprobar: si las pilas que ai_ally/ai_ord resuelven sin pasar por 0x40c990 (refugio, defensa de aliadas)
quedan con la meta de la ronda anterior o como 10; la tanda lo dirá por el tamaño del 10.
Prueba emulada: prueba_mantenimiento.py ampliada (208 controles TODO OK: 34 = modelo por meta y suma igual al 33;
me_set anota meta + 1 y la ronda, se salta índices ≤ 0 o fuera de tabla, deja eax y [esp+0x10] como el original;
sin ia_on no anota). prueba_saldo.py ajustada (después del 33 vienen los 34): OK; prueba_produccion (1.812),
prueba_reserva (1.168) y prueba_oro OK.
Uso: `python prueba_mantenimiento.py <AV> <orig> 6c9dfb 6c9df3 6c9ee0 6cbee0 <SAV>...` (me_tab, me_set).
Al volver la tanda: por IA y tramo, reparto del ahorro (y del 34) por meta. Lo de metas 0, 1 y 10 es el ahorro
alcanzable sin quitarle tareas; si pasa el 3 % del ingreso, programar que esas pilas esperen en la ciudad propia
más cercana que alcancen este turno.
**Medido (8/11/2026, tanda 145, 1.0.138.0, 9 partidas; la n.º 7 colgada en el turno 0, sin eventos).** Los 34 de
cada color suman igual que el 33 en los 466 turnos-color con ejércitos afuera. Ahorro (x − y) / ingreso por meta:
| | tramo | techo | sin decisión (10) | ruina | ciudad enemiga | misión | héroe | Form | resto |
|---|---|---|---|---|---|---|---|---|---|
| original | 1-10 / 11-20 / 21-30 | 1,1 / 7,5 / 9,2 % | 0,5 / 4,0 / 6,0 % (36 / 51 / 63 % de los ej.) | 0,3 / 1,1 / 0,9 % | 0 / 0,3 / 0,7 % | 0,1 / 0,8 / 0,5 % | 0,1 / 0,3 / 0,4 % | ≤ 0,1 % | ≤ 0,5 % |
| nueva | 1-10 / 11-20 / 21-30 | 2,2 / 12,4 / 15,2 % | 1,2 / 7,4 / 10,9 % (51 / 60 / 72 % de los ej.) | 0,5 / 2,2 / 1,3 % | 0 / 0,6 / 1,0 % | 0,3 / 0,8 / 0,2 % | 0,1 / 0,5 / 0,7 % | ≤ 0,1 % | ≤ 0,8 % |
Toda la partida: original techo 7,1 %, metas 0 + 1 + 10 = 4,3 %; nueva 11,5 %, metas 0 + 1 + 10 = 7,7 %. Pasa el 3 %,
pero casi todo es la meta 10 (ninguna decisión de 0x40ca70 esta ronda ni la anterior), y la meta 0 no aparece:
**no se sabe todavía si el 10 son pilas ociosas o pilas que mueve otro camino** (ai_ally/ai_ord: refugio, defensa
de aliadas, guarnición; o pilas que el planificador no visita). Programar que esperen en una ciudad sin saberlo
podría quitarles tareas reales. Resultados (no cambia el juego): nueva puesto 2,86, PV 6,03, 4,2 ciudades,
4 primeros; original 3,13 / 6,89 / 5,4 / 5. Deserciones (evento 28): 4, todas de un color.
Próximo paso (4.6): partir el 10. En mt_evt, para los ejércitos sin meta reciente, anotar quién los movió por última
vez (marca en los caminos de ai_ally/ai_ord que mueven pilas sin pasar por 0x40c990) y si se movieron este turno;
el resto del 10 (sin marca y quietos) es lo ocioso de verdad. Con eso, si lo ocioso pasa el 3 % del ingreso, el
cambio de 4.5 (esperar en la ciudad propia más cercana alcanzable este turno) solo para esas pilas.
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-economia.md, paso 4.6".
