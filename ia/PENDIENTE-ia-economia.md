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
**Paso 4.6, partir el 10 (8/11/2026, vista-aliada 1.0.141.0; falta la tanda, TAREAS 130).** Solo anota.
me_pre, en el call de 0x40edf1 (cada pila de la IA que juega su turno, antes de ai_ord): me_mk(pila, 12) anota 11 + 1
con la ronda en ME_TAB para sus 8 ejércitos = «jugó y no eligió meta». Si 0x40c990 llega a 0x40cc3f, me_set lo pisa
con la meta. ai_ally, al decidir sin 0x40c990 (al_done: refugio, defensa, refugiada que espera), marca 12. El evento
34 ahora tiene x = 0 a 12: 10 = no jugó en esta ronda ni en la anterior (ninguna pila jugada lo tiene: lo ocioso de
verdad o fuera de las pilas del planificador), 11 = jugó sin meta (0x40c990 salió antes, p. ej. sin movimiento),
12 = lo movió ai_ally. Las órdenes del humano (ai_ord, or_go) pasan por 0x40c990 con meta 1 o 7 y quedan con esa.
Prueba emulada: prueba_mantenimiento.py ampliada (270 controles TODO OK con IA_ROTADA, Tanda_Kor_CA, roads02,
ABN_000_29, agua03: el 34 con metas 0-12 = modelo; me_pre marca 11 y la ronda, sigue a ai_ord con la pila y ebx
intactos, sin ia_on o con jugador >= 8 no marca). prueba_saldo, prueba_produccion (2.425), prueba_reserva (2.080),
prueba_oro y prueba_chatordenes OK. prueba_iaalianzas y prueba_chatordenes buscan ahora ai_ord pasando por me_pre.
prueba_iaalianzas: 2 fallas (evento 12 de la pila amenazada, al_surv), **iguales con el 1.0.140.0 instalado**: vienen
de antes, no de este cambio; sin investigar.
Uso: `python prueba_mantenimiento.py <AV> <orig> 6c9e2b 6c9e23 6c9f10 6cbf10 6d9470 6d9280 <SAV>...` (ia_on, ia_mode,
me_tab, me_set, me_pre, ai_ord).
Al volver la tanda: por IA y tramo, ahorro de 10, 11 y 12. Lo ocioso es 10 + 11 (+ 0 y 1); si pasa el 3 % del ingreso,
programar que esas pilas esperen en la ciudad propia más cercana que alcancen este turno; 12 no se toca.
**Medido (9/11/2026, tanda 147, 1.0.141.0, 10 partidas ok, 701 eventos 34).** Ahorro / ingreso por meta, tramos
1-10 / 11-20 / 21-30 (n = ejércitos-turno):
| | 10 no jugó | 11 jugó sin meta | 12 ai_ally | 2 ruina | 7 ciudad enemiga | 6 misión | resto | ocioso (0+1+10+11) |
|---|---|---|---|---|---|---|---|---|
| original | 0,8 / 3,6 / 7,5 % (n 21 / 185 / 473) | 0,04 % (n 6) | no aparece | 1,2 % | 1,0 % | 0,9 % | ≤ 0,3 % c/u | **5,0 %** |
| nueva | 1,2 / 4,7 / 13,2 % (n 37 / 298 / 1.095) | no aparece | no aparece | 1,1 % | 0,9 % | 0,7 % | ≤ 0,7 % c/u | **8,2 %** |
Casi todo el «sin decisión» es 10: **ningún ejército de esas pilas pasó por 0x40edf1 en esta ronda ni la anterior**.
Las que juegan casi siempre eligen meta (11 casi nulo) y ai_ally no movió ninguna fuera de ciudad (12 = 0; sin
comprobar que su marca funcione en partida real: la prueba emulada sí la cubre). Pasa el 3 %, pero el cambio de 4.5
no se puede aplicar dentro del turno de la pila, porque esas pilas no juegan turno. Resultados (no cambia el juego):
nueva puesto 2,73, PV 8,2, 5,9 ciudades, 6 primeros; original 3,32 / 4,65 / 3,9 / 4. Deserciones: 8 nueva, 3 original.
Próximo paso (4.7): averiguar por qué el bucle de 0x40edf1 no visita esas pilas (¿tope de pilas por turno, pilas
sin movimiento, pilas que el recorrido salta por su tipo o posición?), leyendo el bucle que lo llama y, si hace
falta, un evento con cuántas pilas recorre y cuántas salta, y por qué. Según la causa: que el recorrido las incluya
o mandarlas a la ciudad propia más cercana al final del turno.
**Paso 4.7, por qué esas pilas no juegan (9/11/2026, leído en el exe original; vista-aliada 1.0.145.0; falta la tanda,
TAREAS 135).** El bucle de 0x40eab0 no recorre pilas del mapa: recorre los **10 grupos** de la IA del jugador
(0x561f00 + 1178·p, 64 bytes cada uno; bit 0 = activo, bit 0x10 = ya jugó, +4 prioridad, +0xc..+0x1a hasta 8
ejércitos, el primero es el líder). Elige el activo sin jugar de mayor prioridad, lo junta (0x410630: quita del grupo
a los que no están en la casilla del líder y no la alcanzan) y lo hace jugar (0x40edf1). El log del propio juego lo
nombra: «Starting new stack procedures», «Hero %d aiTask %d in city», «Non Hero Stack», «Army %d has been removed
as SLOW», «Leader %d of Stack %d KIA'd so dismissAll», «Stack %d Nothing to do - we could disband».
Quién entra a un grupo: 0x40efc0 (al empezar el turno, desde 0x40ea00) crea grupos solo con **héroes que están en una
ciudad** (tipo & 0x1f = 0x10, sin tarea); 0x40f1a0 los crea (falla si los 10 están ocupados); el planificador arma
grupos sin héroe (0x40d434) y suma escoltas desde la ciudad (0x4a66a0). Quién sale: los lentos, los separados del
líder (0x410630), todo el grupo si muere el líder. **Ningún camino vuelve a meter en un grupo a un ejército que quedó
fuera de una ciudad**: queda quieto para siempre, pagando el mantenimiento entero. Eso es el 10 de la tanda 147.
En las guardadas (inicio del turno del humano) casi todos los colores tienen 0 grupos activos y ejércitos afuera sin
grupo (ABN_000_29: color 6, 24 afuera, 0 en grupo); falta medirlo en partida.
Evento 34, código nuevo: el 10 se parte en 10 = está en un grupo activo de su color y no jugó, 13 = en ningún grupo
(huérfano). Prueba emulada: prueba_mantenimiento.py 280 controles TODO OK (34 con 13 = modelo; un huérfano puesto a
mano en un grupo activo pasa a 10); prueba_saldo, prueba_produccion (1.812), prueba_reserva (1.168), prueba_oro y
prueba_chatordenes OK; prueba_iaalianzas con las 2 fallas de antes.
Al volver la tanda: ahorro / ingreso de 13 y de 10 por IA y tramo. Si el 13 es casi todo el 10 (lo esperado), el
cambio es darles destino a los huérfanos: al empezar el turno de la IA, a cada huérfano de fuera de ciudad, mandarlo
a la ciudad propia más cercana (o meterlo en un grupo libre con meta «Form», que ya lleva a una ciudad).
**Medido (9/11/2026, tandas 148 y 149, 1.0.161.0, 10 partidas ok; 2 colgadas en el turno 0, sin eventos; 731
eventos 34).** Ahorro / ingreso, tramos 1-10 / 11-20 / 21-30 (n = ejércitos-turno):
| | 13 huérfano | 10 en grupo, no jugó | toda la partida: 13 / 10 / ocioso (0+1+10+11+13) / techo |
|---|---|---|---|
| original | 0,2 / 2,6 / 8,2 % (n 7 / 152 / 480) | 0,4 / 0,3 / 0,3 % | 4,3 / 0,3 / 4,7 / 7,1 % |
| nueva | 0,9 / 5,7 / 13,9 % (n 28 / 343 / 997) | 0,1 / 0,3 / 0,5 % | 8,3 / 0,3 / 8,7 / 11,2 % |
Lo esperado: **el 10 de la tanda 147 era casi todo huérfanos**; con grupo y sin jugar queda en 0,3 %.
**Paso 4.8, los huérfanos vuelven a jugar (9/11/2026, vista-aliada 1.0.162.0; falta la tanda, TAREAS 145).** Primer
cambio de juego de esta serie (solo la IA en prueba, IA_MODE = 1). or_grp reemplaza el call 0x40efc0 de 0x40ea00
(principio del turno de un bando de la computadora): después de que el juego arme los grupos de héroes, or_run junta
a los huérfanos (vivos, no héroes, fuera de casilla de ciudad, en ningún grupo activo) por casilla, hasta 8 con el
primero de líder, y les crea un grupo con 0x40f1a0 (lo mismo que hace el juego con los que suelta 0x40d380). El
bucle de 0x40eab0 los hace jugar y el planificador les elige meta: atacar, explorar o «Form» (volver a una ciudad).
Se elige eso y no «ir a la ciudad más cercana» para no quitarles tareas útiles. Tope: arma grupos mientras haya
menos de 7 activos (OR_MAX), los otros 3 quedan para el planificador. Héroes no (su grupo pide 0x40f480).
Evento 35: x = grupos creados, y = ejércitos, n = huérfanos que quedaron sin grupo por el tope.
Leído en el exe: 0x40f1a0(líder, lista de 8 o 0) toma el primer lugar libre (0x410000, -1 si no hay), copia la
lista con el líder en +0xc, marca 0x400 en +0x1a de cada miembro, limpia el resto del grupo; usa [0x4fb0ec].
Tareas de los huérfanos en las guardadas (byte +0x15): 0 a 5, sin bits de pila; no se filtra por tarea.
Prueba emulada: `prueba_huerfanos.py` (3.516 controles TODO OK con ABN_000_29, IA_ROTADA, Tanda_Kor_CA, roads02,
agua03): grupos creados = modelo (lugar, líder, lista, bit 0x400), los demás grupos y colores iguales, evento 35 =
modelo, registros intactos; sin ia_on, IA_MODE 0, jugador 8 o bando humano no cambia nada; con 6 grupos ocupados
arma uno solo. ABN_000_29 color 6: 7 grupos con 22 ejércitos, queda 1. prueba_saldo, prueba_produccion (2.425),
prueba_reserva (2.080), prueba_oro, prueba_mantenimiento (280) y prueba_chatordenes OK; prueba_iaalianzas con las 2
fallas de antes (evento 12).
Uso: `python prueba_huerfanos.py <AV> <ia_on> <ia_mode> <or_run> <SAV>...` (1.0.162.0: 6cf41b 6cf413 6d1800).
Al volver la tanda: (a) evento 35 por IA y tramo: cuántos grupos y ejércitos, cuántos quedan por el tope;
(b) 13 del evento 34 en la nueva (tiene que bajar mucho: los huérfanos de un turno juegan al siguiente);
(c) a qué metas pasan (34 de la nueva: más Form, ruina, ciudad enemiga); (d) resultados contra la original
(puesto, PV, ciudades) y deserciones. Si los grupos de huérfanos le quitan lugar al planificador (menos grupos
de ataque), bajar OR_MAX.
**Paso 4.9, medido (10/11/2026, tandas 150 y 151, 1.0.169.0 y 1.0.170.0, 19 partidas ok; 1 colgada en el turno 0).**
Ahorro / ingreso (evento 29 x), tramos 1-10 / 11-20 / 21-30 y toda la partida:
| | 13 huérfano | 1 Form | 3 neutral | 7 ciudad enemiga | ocioso (0+1+10+11+13) / techo |
|---|---|---|---|---|---|
| original | 0,4 / 3,7 / 11,6 % (n 1.985) | 0,03 % | 0,5 % | 0,6 % | 7,2 / 10,4 % |
| nueva | 0,3 / 2,0 / 5,0 % (n 797) | 1,1 % (2,5 % en 21-30) | 2,1 % | 1,9 % | 4,8 / 11,2 % |
(a) Evento 35: 263 grupos con 931 ejércitos en 1.795 turnos de la nueva (38 / 86 / 139 grupos por tramo); el tope
OR_MAX se tocó en 9 turnos, todos en 21-30, y dejó 72 huérfanos sin grupo. (b) El 13 bajó de 8,3 % (tandas 148-149)
a 2,8 %, menos de la mitad que la original. (c) Los huérfanos pasan a neutral, ciudad enemiga y Form: hacen lo
esperado. (d) **Pero la nueva ahora pierde**: puesto 3,07 contra 2,64, PV 5,58 / 6,32, ciudades 4,09 / 5,01,
primeros 8 / 12 (76 resultados por IA). Antes ganaba: tanda 147 2,73 / 3,32; tandas 148-149 2,50 / 3,21. Las dos
tandas van en el mismo sentido (150: 3,21 / 2,48; 151: 2,96 / 2,81). Deserciones (evento 28, todas con oro 0):
nueva 38 en 4 color-partida, original 16 en 2 (antes 17 / 3). Ejércitos vivos por tramo casi iguales (2,4 / 14 / 28
contra 2,0 / 13 / 28,9); la nueva tiene más oro (262 / 281 / 226 contra 197 / 217 / 169) y menos ciudades al final
(6,56 contra 7,53). Lectura: mover a los huérfanos no le da ciudades; o le quita lugares de grupo al planificador
(que arma los de ataque) o los manda a pelear sueltos y los pierde. Los cambios de 1.0.163 a 1.0.170 son de obras y
dibujo y valen para los dos bandos.
Próximo paso (4.10): separar las dos lecturas. (1) Evento nuevo con los grupos que arma el planificador por turno
(0x40d434 y escoltas de 0x4a66a0) y los que muere/disuelve, para ver si bajaron contra la tanda 148-149. (2) Bajar
OR_MAX de 7 a 4 y, si el puesto no vuelve a ganar, limitar los huérfanos a la meta Form (volver a una ciudad, que es
el ahorro buscado) en vez de dejar que el planificador los mande a atacar. Tanda 10 partidas, Scarpart y Kor.
**Paso 4.10 (10/11/2026, vista-aliada 1.0.173.0; falta la tanda, TAREAS 153).** Las dos lecturas en una tanda.
(1) Evento 36, grupos del planificador. Leído en el exe: 0x40f1a0 tiene dos llamadores, 0x40f12b (grupos de héroes,
dentro de 0x40efc0) y 0x40d434 (dentro de 0x40d380, el planificador arma un grupo sin héroe si junta 2 o más);
0x4a66a0 (escoltas desde una ciudad) se llama desde 0x40cfd5 y 0x40f144 (este, en los de héroes). pl_mk reemplaza
el call de 0x40d434 y cuenta los grupos creados (ax != -1); pl_es reemplaza el de 0x40cfd5 y cuenta las llamadas.
pl_run, primero en or_grp (antes de 0x40efc0), anota el 36: x = grupos del planificador en el turno anterior de
ese color, y = llamadas de escolta, n = grupos activos al empezar el turno; y pone los contadores en 0. Vale para
las dos IA. Perdidos (muertos o disueltos) por turno = n(t-1) + creados(t-1) + héroes y huérfanos de t-1 - n(t);
los de héroes no se cuentan aparte (el 35 da los de huérfanos). Las tandas 148-149 no tienen este evento: la
comparación es nueva contra original dentro de la tanda.
(2) OR_MAX de 7 a 4 (quedan 6 lugares para el planificador).
Prueba emulada: `prueba_planificador.py` (413 controles TODO OK con ABN_000_29, IA_ROTADA, Tanda_Kor_CA, roads02,
agua03: evento 36 = contadores y grupos activos, contadores del color en 0 y los demás iguales, grupos y registros
intactos; sin ia_on no anota; jugador 8 nada; pl_mk deja grupos y ejércitos igual que 0x40f1a0 y cuenta solo si
creó (con los 10 lugares llenos no); pl_es pasa los 3 argumentos y el eax). prueba_huerfanos (con OR_MAX 4 y el
control de tope con 3 grupos ocupados) 3.505 TODO OK; prueba_mantenimiento 280 TODO OK.
Uso: `python prueba_planificador.py <AV> <ia_on> <ia_mode> <pl_n> <pl_e> <pl_mk> <pl_es> <pl_run> <SAV>...`
(1.0.173.0: 6cf84b 6cf843 6d1d53 6d1d73 6d1da0 6d1dd0 6d1e00); prueba_huerfanos: or_run 6d1c30.
Al volver la tanda: (a) 36 por IA y tramo: grupos del planificador por turno y grupos activos, nueva contra
original; (b) 35: tope tocado y huérfanos que quedan; 13 del 34; (c) resultados (puesto, PV, ciudades, primeros)
y deserciones. Si la nueva vuelve a ganar y su planificador arma tantos grupos como la original, queda OR_MAX 4.
Si no gana: limitar los huérfanos a la meta Form (volver a una ciudad) en vez de dejar que el planificador los
mande a atacar.
**Paso 4.10, medido (11/11/2026, tandas 152 y 153, 1.0.192.0, 18 partidas ok; 2 colgadas en el turno 0).**
(a) Evento 36: el planificador casi no arma grupos, en ninguna de las dos IA: 0,03 / 0,04 / 0,04 por turno
(original) y 0,03 / 0,05 / 0,02 (nueva) por tramo; escoltas (y) 0 en todas. Grupos activos al empezar el turno:
original 1,0 / 1,0 / 0,8, nueva 1,1 / 1,5 / 1,7. Con 10 lugares y menos de 2 ocupados, los huérfanos no le quitan
lugar al planificador: la lectura (1) queda descartada. Los grupos los arma casi todos el juego con héroes.
(b) Evento 35: 257 grupos con 914 ejércitos (31 / 92 / 134 por tramo); el tope de 4 se tocó en 80 turnos (2 / 15 /
63) y dejó 528 huérfanos sin grupo (461 en 21-30). Evento 34, meta 13 sobre todas las pilas anotadas: nueva 32,7 %
(24,5 % en 150-151), original 64,7 %.
(c) Resultados (72 por IA): la nueva vuelve a estar arriba, por poco: puesto 2,84 contra 2,92, PV 6,49 / 5,29,
ciudades 4,58 / 4,24, primeros 11 / 10 (en 150-151 perdía 3,07 / 2,64). Deserciones: nueva 18 en 2 color-partida,
original 14 en 1. Ejércitos vivos por tramo iguales (2,4 / 13,9 / 27,4 contra 2,3 / 13,8 / 27,7); la nueva junta
más oro (264 / 311 / 271 contra 201 / 206 / 167).
Decisión (la prevista en el paso): queda OR_MAX 4. La diferencia de puesto es chica y cabe en el azar de 18
partidas; como el planificador no usa los lugares, lo que cambió de 7 a 4 es cuántos huérfanos se mueven por
turno: con 7 los mandaba a pelear de a muchos y los perdía. No se limita a Form por ahora.
Sin verificar: que escoltas = 0 sea real y no un fallo de pl_es en el juego (la prueba emulada solo comprobó que
cuenta cuando se lo llama).

**Paso 4.11 (11/11/2026; TAREAS 171, hecha).** Confirmar el 4.10 con una tanda más, sin tocar el parche
(10 partidas, Scarpart y Kor). Se juntan 152, 153 y la nueva: si con unas 27 partidas la nueva sigue arriba
(puesto, PV, ciudades), el hilo de los ejércitos ociosos se da por cerrado con OR_MAX 4. Si queda abajo, se
limitan los huérfanos a la meta Form. Los cambios de muros y Life Ward que vengan en el medio valen para las dos IA.
Después, y en otra sesión: el oro que la nueva ya junta (271 contra 167 de la original en los turnos 21-30) no
tiene destino. Ese es el objetivo de origen, un ahorro con destino (puentes, trampas, caminos, ayuda a aliados).
Depende de que la IA sepa hacer esas obras: paso 5 de PENDIENTE-ia-innovaciones.
**Paso 4.11, medido (11/11/2026, tandas 154 y 155, 1.0.202.0, 20 partidas ok).** La nueva gana en las dos:
puesto 2,61 contra 3,32, PV 6,81 / 5,74, ciudades 4,92 / 4,40, primeros 13 / 9 (80 resultados por IA; tanda 154
2,68 / 3,64, tanda 155 2,52 / 2,95). Juntas las cuatro tandas 152-155 (38 partidas, 152 resultados por IA): puesto
2,72 / 3,14, PV 6,66 / 5,53, ciudades 4,76 / 4,32, primeros 24 / 19. Ejércitos vivos por tramo parejos (2,3 / 13,0 /
28,2 contra 1,9 / 12,6 / 25,8); oro de la nueva 251 / 261 / 255 contra 203 / 209 / 163. Evento 36 igual que en el
4.10 (el planificador casi no arma grupos; escoltas 0). Lo que sigue en contra: deserciones (evento 28) nueva 43 en
4 color-partida, original 16 en 2; en las cuatro tandas 61 en 6 contra 30 en 3. Son pocos colores y no le cuestan
el puesto, pero se miran si vuelven a crecer.
**Decisión: el hilo de los ejércitos ociosos queda cerrado con OR_MAX 4.** No se limitan los huérfanos a Form.
Próximo tema (en otra sesión): darle destino al oro que la nueva junta (255 contra 163 en 21-30): puentes, trampas,
caminos, ayuda a aliados. Depende del paso 5 de PENDIENTE-ia-innovaciones (que la IA sepa hacer esas obras).
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-economia.md, el oro con destino, después del paso 5 de
innovaciones".

## Oro con destino, primer destino: el puente (11/11/2026, vista-aliada 1.0.203.0; medido en las tandas 156-157, TAREAS 174 hecha)
Estado del paso 5 de PENDIENTE-ia-innovaciones al empezar: 5.1 (convoy) y 5.2 (puentes) medidos; 5.3 (trampas) y 5.4
(noche) sin hacer. De las obras, la única que la IA ya sabe hacer es reconstruir un puente, y el 5.2 dejó la causa:
el 94 % de las veces le falta el oro (800). Ese es el primer destino; trampas, caminos y ayuda a aliados se suman
cuando la IA sepa hacerlos, con la misma anotación (RS_GOAL).
Qué cambió (build.py):
- ai_brrebev: la falta de oro ya no corta los filtros. Si el puente pasa todo lo demás (vacío, cabecera alcanzable,
  sin enemigo cerca, no lo volvería a derribar, algo que ganar), anota RS_GOAL[p] = costo y RS_GOALT[p] = turno + 1;
  si además falta oro, evento 26 n = 2. **Desde 1.0.203.0 el 26 n = 2 significa «todo lo demás pasa, falta oro»**;
  antes cortaba sin mirar el resto, así que los 770 del 5.2 no se comparan con los nuevos.
- rs_ok: si la anotación es de este turno o del anterior, el piso suma ese costo; el evento 31 lleva x = tipo + 10
  (11 = tipo de unidad, 12 = agrandar) cuando el freno incluye el ahorro. Solo IA en prueba (IA_MODE 1), como antes.
- ai_brreb: al reconstruir (evento 4) borra la anotación.
No frena la producción de los tipos ya comprados (eso es pr_ok), ni los héroes.
Sin cubrir: una anotación de una partida anterior en el mismo proceso, si coincide el turno, vale un turno de más.
Prueba emulada: prueba_reserva.py ampliada (ahorro vigente, del turno anterior, vencido, sin anotar, costo 0, y
humano / IA original / sin ia_on con ahorro anotado): 2.148 controles TODO OK (ABN_000_29, agua03, IA_ROTADA).
Uso nuevo: `python prueba_reserva.py <AV> <orig> <ia_on> <ia_mode> <rs_goal> <rs_goalt> <SAV>...` (en 1.0.203.0:
6d035b 6d0353 6d2a0b 6d2a2b). prueba_iareconstruye.py con el modelo nuevo (oro al final): 109 OK; prueba_iarazea,
prueba_iapuente y prueba_oro OK. No probado en emulación: que ai_brrebev escriba RS_GOAL (solo sus eventos).
Al volver la tanda: eventos 4 (reconstrucciones; antes 1 en 20 partidas), 26 por motivo, 31 con x = 11/12 (cuántas
veces y en qué turnos frena por el ahorro), y puesto, PV, ciudades y deserciones (28) de la nueva contra la original.
Si reconstruye y no pierde puesto, queda. Si pierde puesto por frenar de más, limitar el ahorro (p. ej., solo si el
oro ya pasa la mitad del costo, o un tope de turnos esperando).
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-economia.md, oro con destino, resultado de la tarea 174".
**Medido (12/11/2026, tandas 156 y 157, 1.0.204.0, 20 partidas ok; la 1.0.204.0 solo quita el Life Drain del muro,
vale para las dos IA).**
- Reconstrucciones (evento 4): 3 de la nueva (turnos 7, 10 y 21; 640, 800 y 800 de oro), contra 1 en 20 partidas
  antes. La original, ninguna.
- Freno por el ahorro (evento 31): x = 11 (tipo de unidad) 46 veces en 8 color-partida, turnos 6-21; x = 12
  (agrandar) 15 veces en 7, turnos 9-30. Frena poco: 12 color-partida de 80.
- Evento 26 n = 2 («todo pasa, falta oro»): 19 de la nueva (el 94 % del 5.2 era el filtro viejo, que cortaba antes).
- Los colores que frenaron: puesto 2,0, PV 9,6, ciudades 7,1; los 3 que reconstruyeron, primeros (PV 23); el resto
  de la nueva, puesto 3,26, PV 5,2. El ahorro no le cuesta a quien lo hace (hay sesgo: el que tiene más ciudades
  tiene más oro y más puentes a mano, así que tampoco prueba que ayude).
- En conjunto la nueva quedó pareja con la original: puesto 3,00 / 3,02, PV 5,83 / 6,34, ciudades 4,31 / 4,89,
  primeros 10 / 12. En 152-155 ganaba (2,72 / 3,14). La baja no viene de los que ahorraron; puede ser azar de 20
  partidas o el muro sin Life Drain. Oro de la nueva 249 / 289 / 248 por tramo contra 202 / 204 / 150. Deserciones
  (28): nueva 47, original 8 (sigue creciendo, ver el 4.11).
Sin verificar: la columna puesto viene vacía en 70 de 160 resultados; los promedios usan solo los que la tienen.
**Decisión: el ahorro para el puente queda, sin límite.** Próximo: (a) si en la próxima tanda la nueva sigue sin
ganar, mirar las deserciones (evento 28), que ya son 6 veces las de la original; (b) sumar destinos al oro cuando la
IA sepa hacerlos (trampas, caminos, ayuda a aliados: pasos 5.3 y siguientes de PENDIENTE-ia-innovaciones).
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-economia.md, deserciones de la nueva".

## Deserciones de la nueva: diagnóstico (12/11/2026, datos.db, tandas 148-157, sin tocar el parche)
Cada episodio (color-partida con evento 28) cruzado con el 29 (ingreso, mantenimiento), el 33 (fuera de ciudad), el
31/32 (frenos), el 35 (huérfanos), ciudades y batallas de los 4 turnos previos. Scripts de la sesión, sin versionar.
- Tandas 152-157: nueva 108 deserciones en 10 color-partida, original 38 en 6. Turnos con mantenimiento > ingreso:
  nueva 143 de 5.410, original 88 de 5.264; colores con 3 o más turnos seguidos así: nueva 13, original 7.
- **Dos clases de episodio.** Derrumbe (pierde ciudades y pelea; ya conocido, igual en las dos IA): nueva 3 de 10,
  original 4 de 6. **Estructural** (sin batallas y con las ciudades quietas, el mantenimiento pasa al ingreso y el
  oro baja hasta 0 en 4-8 turnos): **nueva 7 de 10**, original 1 (1093 color 6).
- Cómo es el estructural (ejemplos): 1135 color 5, 11 ciudades, ingreso 258: en el turno 17 pasan de 0 a 17
  ejércitos fuera de ciudad y el mantenimiento salta de 76 a 221; turno 21, 35 fuera y 368. 1124 color 3: turno 25,
  de 0 a 20 fuera, mantenimiento 43 → 175 con ingreso 106. 1145, 1114, 1107, 1086 color 3 (la misma posición: 4
  ciudades, ingreso 82): 10 a 16 ejércitos fuera, quietos turno tras turno, mantenimiento 94-134 contra 82.
- **La causa es el mantenimiento entero de los que están fuera, no la producción.** El freno de producción (32) ya
  frena en todos esos turnos (4 por turno) y no alcanza: los ejércitos ya existen. Lo que fuera paga entero, en una
  ciudad pagaría un tercio: en esos casos volver a una ciudad deja el mantenimiento bajo el ingreso (1145: 94 → unos
  41 contra 82; 1135 color 5: 368 → unos 170 contra 258).
- El 35 arma grupos de huérfanos esos mismos turnos (p. ej. 1135 color 5, turno 17: 3 grupos con 17), pero or_ok solo
  toma ejércitos que **ya** estaban fuera: el salto lo hace quien los saca (planificador o grupos de héroes), no
  or_run. Sin verificar quién los saca y por qué quedan quietos fuera (1145 color 3: 10 fuera 6 turnos seguidos).
**Próximo paso (4.12), repliegue por quiebra:** cuando el oro + ingreso − mantenimiento del turno no alcance para
el turno siguiente (oro + ingreso < 2 × mantenimiento) y el mantenimiento pase al ingreso, mandar los grupos de la
nueva que no atacan a «Form» (meta 1, 0x40db40, volver a una ciudad) hasta que el mantenimiento proyectado (fuera
pasando a un tercio) quede bajo el ingreso. Primero leer en el exe cómo se fija la meta de un grupo (0x40ca70,
tabla 0x40d02c) y anotar con un evento la meta de los grupos fuera en esos turnos, para saber cuáles atacan.

### 4.12 hecho: repliegue por quiebra (vista-aliada 1.0.208.0, 12/11/2026)

- Lo que mostró el evento 34: en los casos estructurales del color 3 (1107, 1114, 1145, 1086) las pilas fuera tienen
  **meta 3 (neutral)** y quedan quietas 6 turnos o más; en 1135 color 5 son huérfanos (meta 13).
- Cambio en me_set (build.py, `RP_EVT = 37`, `RP_TURNS = 8`): con IA_MODE 1, color de la computadora, mant > ing y
  oro < 8 × (mant − ing), si la meta elegida es 2 (ruina), 3 (neutral), 4 (ítem) o 6 (misión) y el líder no es héroe,
  la meta pasa a 1 (Form) con destino la ciudad propia viva más cercana al líder (0x4974a0; en empate, la primera).
  Evento 37 = (meta original, ciudad, oro). ME_TAB anota la meta nueva. Ataques (7, 8), héroes (5) y reconstrucción
  (9) no se tocan. Los huérfanos (meta 13) no pasan por me_set: quedan para otro paso si siguen pesando.
- Pruebas: `prueba_repliegue.py` 198 controles TODO OK (ABN_000_29, IA_ROTADA, Tanda_Kor_CA, roads02, agua03);
  `prueba_mantenimiento.py` 280 TODO OK.
- Sin verificar: que la ruta Form llegue a la ciudad en juego real y que no vuelva a salir al turno siguiente.
- A medir con la tanda de la TAREAS 179: eventos 37 por color y su relación con los 28 (deserciones de la nueva
  contra 108 en 10 color-partidas de 152-157); turnos con mant > ing; puesto, PV y ciudades de la nueva contra la
  original. Si se repliega y vuelve a salir (37 repetidos en la misma pila), hace falta memoria del repliegue.
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-economia.md, resultado del repliegue (TAREAS 179)".

### Resultado del repliegue (tandas 158 y 159, vista-aliada 1.0.213.0, 12/11/2026)
- **Donde se activa, funciona y no vuelve a salir.** 1160 color 3 (turno 22) y 1166 color 3 (turnos 22 y 28), siempre
  meta 3 (neutral). En 1166: mantenimiento 113 → 55 y 119 → 29 al turno siguiente, contra un ingreso de 82; en el
  turno 23 quedan 2 ejércitos fuera (antes, 25). No desertó. Los 37 salen repetidos en el mismo turno (3 o 4 con la
  misma meta, ciudad y oro): son varias pilas o varias llamadas a me_set, no una pila que vuelve a salir.
- **Deserciones de la nueva:** 30 en 2 color-partidas (1156 color 3: 16; 1170 color 3: 14), sin batallas ni ciudades
  perdidas: las dos estructurales. En las dos el repliegue **no se activó**: según el evento 34, las pilas fuera
  eran huérfanos (meta 13), atacantes (7) y pilas que ya iban a Form (1) y no llegaban. 1170 color 3: de los turnos
  19 a 28, entre 13 y 20 ejércitos fuera con mantenimiento 124-162 contra 106; en el turno 25, 17 con meta 1 y
  siguen fuera los turnos siguientes. Original: 29 deserciones en 3 color-partidas.
- Turnos con mantenimiento > ingreso: nueva 58 de 1.942 (3,0 %; antes 2,6 %), original 40 de 1.899 (2,1 %; antes
  1,7 %). No bajó.
- Resultado de las partidas: nueva puesto 2,65 / 2,92, PV 8,5 / 7,0, ciudades 6,1 / 5,05; original puesto 3,27 /
  3,19, PV 5,1 / 5,4, ciudades 3,8 / 4,3. El repliegue no le costó partidas.
- Conclusión: el cambio queda. Lo que sigue desertando son huérfanos y pilas con meta Form que no entran a la ciudad.
**Próximo paso (4.13):** en quiebra (misma condición que 4.12), (a) que or_run arme los grupos de huérfanos con
destino la ciudad propia más cercana en vez de una meta de ataque o captura; (b) averiguar por qué las pilas con meta
1 de 1170 color 3 (turnos 25-28) no entran a la ciudad: anotar con un evento el destino y la distancia de cada pila
Form que termina fuera. Los atacantes (7) no se tocan.
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-economia.md, paso 4.13 (huérfanos y Form en quiebra)".

### 4.13 hecho: memoria del repliegue (vista-aliada 1.0.214.0, 12/11/2026)
- Lo que mostraron los datos antes de tocar nada: los huérfanos **sí** se agrupan (evento 35, n = 0 en 1156 y 1170
  color 3), así que el (a) tal como estaba escrito no hacía falta. El problema es una **oscilación**: en 1170 color 3
  las mismas 13-20 pilas tienen meta 7 (ciudad enemiga) y meta 1 (Form) en turnos alternados (20: 7, 21: 1, 22: 7,
  23: 1, 24: 7, 25: 1...) y **no hubo ninguna batalla** de ese color en los turnos 17-30; en 1156 color 3 igual
  (26: 7, 27: 1, 28: 7, 29: 1). Los huérfanos recién agrupados entran en la misma oscilación (1170 turno 19: 16
  huérfanos → meta 7). Esas pilas «atacantes» no atacan: se cambia la decisión del 4.12 de no tocar las metas 7 y 8.
- Cambio (build.py): or_run anota en ME_TAB, con la ronda, el código RP_HU = 15 para cada ejército que agrupa.
  me_set, con la misma condición de quiebra del 4.12 y líder no héroe: si la meta es 7 u 8 y el líder tiene en
  ME_TAB, de esta ronda o la anterior, meta 1 (código 2) o RP_HU, la pasa a Form hacia la ciudad propia viva más
  cercana. **Evento 38** = (meta original, ciudad, distancia a ella): sirve también para el (b), saber a qué
  distancia queda la ciudad de las pilas que no llegan. El 37 sigue igual para las metas 2, 3, 4 y 6. Fuera de
  quiebra no cambia nada; una pila que ya llegó y está en quiebra queda en la ciudad (distancia 0).
- Pruebas: `prueba_repliegue.py` 450 controles TODO OK (los casos nuevos: 7 y 8 con Form de esta ronda y de la
  anterior y con RP_HU; controles con Form de hace dos rondas, códigos 4, 8 y 13, sin quiebra, IA_MODE 0, líder
  héroe, metas 0, 5 y 9 con Form previa); `prueba_huerfanos.py` 3.705 TODO OK (ahora controla la marca en ME_TAB;
  uso nuevo: `<AV> <ia_on> <ia_mode> <or_run> <me_tab> <SAV>...`, en 1.0.214.0 6d035b 6d0353 6d2910 6d0440);
  `prueba_mantenimiento.py` 280 TODO OK. Las cinco partidas de siempre.
- Sin verificar: que con la meta sostenida las pilas lleguen a la ciudad en juego real (en 1166 la ruta Form sí
  llegó); que una pila no quede trabada en Form si la ciudad más cercana es inalcanzable (el 38 con la distancia
  repetida turno tras turno lo mostraría).
- A medir con la tanda de la TAREAS 185: eventos 37 y 38 por color y si se repiten con la misma distancia; ejércitos
  fuera (33) y mantenimiento contra ingreso en los turnos siguientes; deserciones (28) de la nueva contra la
  original; puesto, PV y ciudades.
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-economia.md, resultado de la memoria del repliegue (TAREAS 185)".

### Resultado de la memoria del repliegue (tanda 160, vista-aliada 1.0.214.0, 12/11/2026)
- **El cambio no llegó a actuar: evento 38 = 0.** En esta tanda no se dio la oscilación meta 7 / meta 1 en quiebra
  que lo motivó (1156 y 1170 color 3 en las tandas 158-159). El 37 salió 4 veces (1176 color 3 turno 30, 1179 color
  5 turno 20, siempre meta 3).
- **Deserciones (28):** nueva 1 (1174 color 5); original 30 (todas 1176 color 2, turnos 23-27). No se le puede
  atribuir al cambio: no hubo quiebra con oscilación que corregir.
- Turnos con mantenimiento > ingreso: nueva 23 de 952 (2,4 %; 3,0 % en 159), original 18 de 989 (1,8 %).
- Caso que el 4.12 deja pasar a propósito: 1176 color 3, turnos 19-29, una pila con meta 3 (neutral) quieta fuera
  con 10 ejércitos (mantenimiento 88 contra ingreso 82, oro 100-134): el déficit (6 por turno) no llega a la
  condición oro < 8 × déficit, y no desertó. No se toca.
- Resultado de las partidas: nueva puesto 2,96, PV 5,55, ciudades 3,8; original 2,84 / 6,95 / 5,55. Primera tanda
  de esta serie en que la original queda arriba; como el 37 y el 38 casi no actuaron, es variación entre tandas
  y no efecto del cambio (158: nueva 2,65 contra 3,27; 159: 2,92 contra 3,19).
- Conclusión: sin datos para juzgar la memoria del repliegue. El cambio queda (fuera de quiebra con oscilación no
  hace nada) y se repite la tanda con la misma versión (TAREAS 186).
**Próximo paso:** con la tanda de la TAREAS 186, buscar eventos 38: cuántos, si se repiten con la misma distancia
en la misma pila (pila trabada) y si los colores con 38 desertan menos que 1156/1170 color 3. Comparar de nuevo
puesto, PV y ciudades sumando las tandas 158-160 y la nueva.
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-economia.md, memoria del repliegue (TAREAS 186)".
