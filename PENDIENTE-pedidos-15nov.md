# Pedidos y bugs del 15/11/2026 (partidas con Nico)

Recibidos mientras corría la tanda 170. Cada parte es independiente; se trabaja una por sesión.

## A. Bugs

1. **Cuelgue al mover aliados de una ruina (NA_159, turno 17).** Héroe del usuario explora una ruina, obtiene
   Red Knights (4, 3 y 2 en tres intentos con las mismas jugadas); al moverlos, el juego de Nico (otra PC) se cuelga,
   las tres veces. En el turno 29, con Dushdana, los mismos 2 aliados se movieron sin cuelgue.
   Material: `C:\Warlords\HISTORY\NA_159_30.SAV`, `NA_159_31.SAV`, `NA_159.FIN`.
   Primer paso: reproducir con el .SAV más cercano al turno 17 (si no hay, partir del 30/31 y comparar qué cambia
   entre el héroe del turno 17 y Dushdana: tipo de héroe, pila llena, casilla de destino, orden de red del movimiento
   de aliados nuevos). Bisecar contra Darklord.exe sin parche (regla 4) para saber si el cuelgue es nuestro.
2. **Íconos de armas en la zona oculta del mapa (NA_160, turno 21, PC de Nico: 4 GB RAM, W11).** La niebla muestra
   mosaicos de ejércitos repetidos (captura del usuario). Hipótesis a descartar: superficie de dibujo perdida
   por falta de memoria vs. un índice de imagen fuera de rango en nuestro código de vista aliada. Mirar primero si
   pasa en otra PC con el mismo .SAV.
3. **Bosque tapa la cúpula del faro (NA_159).** La cúpula debe dibujarse siempre encima del bosque.
   Ver `PENDIENTE-faros-muros.md` (orden de dibujo del faro).

## B. Guardado al pausar
La pausa manual (PZ_MANUAL, `parches/vista-aliada/build.py` ~línea 10950) no guarda. Al entrar en pausa, guardar la
partida como hace el guardado automático del turno.

## C. Cuenta regresiva sonora al fin del turno
Que la cuenta regresiva sonora de los informes suene también en los últimos 5 s del turno (vencimiento en
[0x4ff7a8], ver build.py ~10936), y que los números se vean junto al cursor.

## D. Visor de historia: bloquear partidas en curso
- Una partida que no terminó (ni por final normal ni por decreto) no se puede ver en el Visor.
- Excepción: partidas marcadas "de prueba". La marca la pone el clan escribiendo `prueba` en el chat (con acuerdo,
  definir: ¿todos los jugadores humanos deben escribirla?) y viaja dentro del .SAV.
- Con la marca, el mapa principal muestra una **P** mayúscula, Arial Bold, verde claro con borde rojo, en el ángulo
  superior izquierdo.
- El Visor (`ia\visor-historia`) lee la marca y el estado de terminada (ver `PENDIENTE-partidas-terminadas.md`) y
  solo abre una partida en curso si está marcada.
