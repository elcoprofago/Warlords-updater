# Partidas terminadas a una carpeta aparte

Pedido del usuario (1/11/2026): que el juego parcheado (DarklordAV.exe, parche vista-aliada) pase las partidas
**terminadas** a una carpeta nueva, distinta de NETSAVES, donde se guardan normalmente. Solo en el parche, no en
el Darklord.exe original.

Para qué (contexto): el Visor de historia (`PENDIENTE-visor-historia.md`) sirve sobre todo para consultar
partidas reales del ranking; tenerlas terminadas y separadas facilita encontrarlas.

## Plan

1. Ubicar en DarklordAV.exe el momento en que la partida termina (pantalla de victoria / fin por límite de
   turnos o condición) y la rutina que guarda en NETSAVES (y la de SAVES, si aplica).
2. En ese momento, pasar la partida a la carpeta `HISTORY` dentro de la carpeta del juego (se crea si no
   existe; convive sin problema con el archivo HISTORY.DAT, que es otro nombre).
   **Decidido por el usuario (1/11/2026):** solo pasan las partidas en que el juego detecta cumplida la
   condición de victoria. Las que los jugadores abandonan o dan por terminadas a mano no: el programa no tiene
   forma de saberlo, y quedan en NETSAVES como siempre.
3. Partidas en red: verificar qué PC lo hace (anfitrión, cada una) sin desincronizar.
4. Construir con `parches/vista-aliada/build.py`, probar en C:\Warlords3, anotar la prueba en TAREAS.md y
   publicar con `tools\publicar-parche.ps1`.

## Por decidir al investigar

- Mover o copiar: «pasar» sugiere mover; si la partida terminada queda solo en TERMINADAS, NETSAVES queda
  limpia. Confirmar que el .SAV al terminar contiene el estado final (para el Visor).

- NETSAVES guarda varios archivos por partida, uno por turno (NA_2_29.SAV, NA_2_30.SAV…). Decidir si se pasan
  todos los de esa partida o solo el último (el último ya trae el historial completo).

## Punto 1, resuelto (1/11/2026, por lectura del Darklord.exe original; nada probado en el juego todavía)

Fin de partida (ya documentado para las tandas, `build.py` ia_fin / ia_vic):
- **Game Over** con podio: rutina 0x482d77; en 0x482fd6 ya están orden y puestos (ahí engancha ia_fin).
- **Victoria aliada sin Game Over** (quedan solo aliados vivos): cartel «Victory! / An allied victory!», apertura
  en 0x482790 (call 0x482c10, ahí engancha ia_vic). Victoria = [0x571760] ≠ 0, Game Over = [0x57175c].
  La partida sigue después de Aceptar, así que el «terminó» de este caso es el cartel.

Guardado:
- 0x439880(nombre, x) guarda; el modo [0x503de8] elige la carpeta: 0 → `SAVES\%s.SAV`, 2 → `NETSAVES\%s.SAV`.
  El nombre base de la partida queda en [0x503da0].
- Autoguardado en red **0x4397f0**: arma `%s_%d` (nombre base, turno de 0x420a80) y guarda con 0x439880; después,
  si [0x503df4] ≥ 0, borra `NETSAVES\%s_%d.SAV` del turno (actual − [0x503df4] − 1) con 0x4ddbb0. O sea, NETSAVES
  conserva solo los últimos [0x503df4]+1 turnos de cada partida.
- Lo llama una sola vez, 0x4aa0a6, y solo cuando [0x4ff010] = 0 (a confirmar en el punto 3: parece ser el anfitrión;
  0x4ff010 = 2 se trata igual en el bucle previo).

Consecuencia para el punto 2: al detectar el fin, alcanza con mover los `NETSAVES\<nombre>_*.SAV` de esa partida
(nombre en [0x503da0]) a `HISTORY\`; no hace falta un guardado propio si el último autoguardado ya es del turno final
(a verificar: si el fin se detecta antes o después del autoguardado de ese turno).

## Próximo paso

Punto 2: ver el orden autoguardado ↔ detección de fin en el turno final, y escribir el parche.
