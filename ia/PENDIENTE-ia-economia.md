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
3. **Contrastar con partidas reales.** Usar el Visor de historia o las guardadas del ranking del clan para ver si
   más de tres héroes y el desbande aparecen ahí y no en las tandas.
4. **Diseñar la reserva**, con lo medido: un piso de oro para el mantenimiento de los próximos turnos (contra el
   desbande), un tope de héroes salvo descuento, y un ahorro con destino (puente que abre camino, trampa, camino,
   ayuda a un aliado) cuando haya un uso concreto con valor.
5. **Banco de pruebas:** tandas IA de prueba contra original, con PV y desbandes, como en los pasos anteriores.
   Trampas, caminos y dádivas de la IA todavía no existen (paso 5 de PENDIENTE-ia-innovaciones): la reserva se
   diseña para poder sumarlos después.

Próximo paso: analizar la tanda de TAREAS 110 con los eventos 29 (cerrar el paso 2) y seguir con el 3.
Frase para retomar: "Seguimos con ia\PENDIENTE-ia-economia.md, paso 2: la tanda de la 110 terminó".
