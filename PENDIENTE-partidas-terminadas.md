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

## Punto 2, hecho (2/11/2026, vista-aliada 1.0.100.0; probado emulado con prueba_historia.py, falta la prueba real)

- hi_govic (en 0x482790, si [0x571760] ≠ 0) y hi_gofin (en 0x482fd6, Game Over) llaman a hi_fin antes de los
  registros de las tandas (ia_vic / ia_fin, que siguen igual).
- hi_fin recuerda el nombre de la partida (hi_name) y llama a hi_mover: crea `HISTORY\` y, para los turnos 0 a
  [0x503328] + 1, copia `NETSAVES\<nombre>_<t>.SAV` a `HISTORY\` (pisando) y borra el original solo si la copia salió.
- Orden autoguardado ↔ detección: no hizo falta averiguarlo. hi_auto envuelve el autoguardado (0x4aa0a6): después de
  guardar, si la partida es la de hi_name (sin distinguir mayúsculas), vuelve a llamar a hi_mover. Cubre los dos
  órdenes y además los turnos que se jueguen después de una victoria aliada.
- Se decidió **mover** (copiar y borrar) y **todos** los turnos que haya en NETSAVES (son pocos: el juego ya borra
  los viejos según [0x503df4]).
- Solo partidas en red (NETSAVES): en una partida de un jugador no hay autoguardados; el .SAV lo guarda el usuario
  con el nombre que quiere, y queda en SAVES.

## Punto 3, resuelto por la prueba real (2/11/2026, TAREAS 83)

Partida en red a 4 turnos, «victoria por más puntos»: HISTORY se creó en **las dos** PC y la partida salió de NETSAVES
en ambas. O sea, la otra PC también autoguarda, y la victoria se detecta en todas.

## Parte B (pedido del 2/11/2026): ver cómo terminó la partida

**B1. Visor:** en el panel superior, un botón o enlace que abra el cuadro de victoria tal como lo muestra el juego al
terminar (podio de Game Over o cartel de victoria aliada). Si la partida se cerró de común acuerdo, en su lugar
un pergamino con el texto del acuerdo, como cuadro de mensaje o ventana.

**B2. Juego (DarklordAV.exe), no el Visor:** un mecanismo para que el anfitrión deje constancia de que la partida
se cerró de común acuerdo (texto libre y/o opciones). El Visor solo lo lee, no lo edita.

Por resolver al empezar:
- Dónde queda el dato. Propuesta: el juego escribe, al pasar la partida a HISTORY, un archivo de texto
  `HISTORY\<nombre>.FIN` con el tipo de cierre (podio / victoria aliada / acuerdo), el turno y, en el podio, lo que
  ia_fin ya tiene a mano (orden, puesto, color, PV, ciudades, oro por bando); en el acuerdo, el texto. El Visor lo
  busca al lado del .SAV. Alternativa: averiguar si el .SAV final ya trae todo lo del podio (los PV los calcula
  0x440840) y que el Visor lo recalcule; descartarla si no es exacta.
- Cómo lo dispara el anfitrión en B2: ver si alcanza con una orden en el chat (ya existe el mecanismo de órdenes,
  ch_order / ch_pfx, p. ej. «acuerdo: <texto>») o si hace falta un cuadro propio. Al consignarlo, la partida
  también pasa a HISTORY (hi_fin), aunque el juego no haya detectado victoria: así se amplía lo decidido en el punto 2
  por pedido del usuario.
- Dibujo del cuadro en el Visor: tomar el arte del juego (como ya hace con DLG_BIG y el minimapa).

## B2, hecho (2/11/2026, vista-aliada 1.0.101.0; probado emulado con prueba_historia.py, falta la prueba real)

- Dónde queda el dato: `HISTORY\<nombre>.FIN`, texto, al lado de los .SAV. Se descartó recalcular desde el .SAV.
  Formato:
  ```
  cierre=podio | aliada | acuerdo
  turno=<turno>
  bando=<puesto>,<color>,<PV>,<ciudades>,<oro>   (uno por bando; podio en su orden, puesto -1 = empatado con el
                                                  anterior; aliada: puesto 0, en orden de color)
  texto=<lo escrito>                             (solo acuerdo)
  ```
- Podio: hi_wpod (mismos datos que ia_fin). Victoria aliada: hi_wali (como ia_vic, PV de 0x440840; no si hay Game
  Over). Lo escribe cada PC que detecta el fin (todas, según el punto 3).
- Acuerdo: en el chat, «acuerdo: <texto>» (sin distinguir mayúsculas). ch_pfx lo detecta en la PC que lo escribe,
  llama a hi_acu (hi_fin + .FIN) y el mensaje sigue al chat normal, así los demás lo leen. Lo puede escribir cualquier
  jugador, no solo el anfitrión (no hay forma confirmada de saber quién es el anfitrión: [0x4ff010] sin verificar).
  **Límite:** la partida pasa a HISTORY solo en la PC que lo escribió; en las otras sigue en NETSAVES. Si la prueba
  real muestra que hace falta en todas, enganchar la recepción del chat.

## B1, hecho (2/11/2026, Visor de historia 1.0.6.0; probado con .FIN de prueba, falta la prueba real: TAREAS 85)

- `leer_fin` busca `<nombre>.FIN` al lado del .SAV: el nombre es el del archivo sin el `_<turno>` final
  (NA_2_29.SAV → NA_2.FIN), y si no, el nombre entero.
- Botón «Cómo terminó…» en el panel superior (gris si no hay .FIN). Abre un cuadro con DLG_MED.PCX del set (recortado
  a 520x376, el resto del PCX es blanco): «Game Over» con puestos (los -1 repiten el anterior), «Victory!» sin puestos,
  ambos con pvictory.pcx, escudo, nombre, PV, ciudades y oro; «Peace Agreement» con un pergamino y el texto.
- No es copia exacta de la pantalla del juego: no se averiguó cómo la arma 0x482d77; se usó el mismo arte.

## B1, ajustes tras la primera prueba (2/11/2026, Visor 1.0.7.0)

- El cartel se rehízo según la captura del juego: «Game Over!» en la barra, «<límite> turns have passed!», columnas
  SIDE / VPs / CITIES / GOLD, escudo chico, nombre en el color del bando (negro en gris), botón Done. Sin pvictory.pcx.
- Actualización del Visor y del Monitor de IA: el .exe relanzado heredaba las variables de PyInstaller del viejo (misma
  ruta) y usaba su carpeta _MEI, que el viejo borraba al cerrar. Ahora se lanza con esas variables quitadas y
  PYINSTALLER_RESET_ENVIRONMENT=1, y el .bat espera al proceso padre (el cargador). Probado con un .exe de juguete.
- Prueba real: la partida de la anfitriona («eventos2») se jugó en C:\Warlords con un parche anterior a 1.0.101.0:
  pasó a HISTORY sin .FIN. Falta probar con 1.0.101.0 (TAREAS 84 y 85).

## B1, más ajustes (2/11/2026, Visor 1.0.9.0)

- Botón y ventana: «Resultado» (el acuerdo sigue en la ventana «Final por acuerdo»). Done solo en el acuerdo.
- cierre=aliada: el juego lo usa también cuando queda un solo bando (prueba «eventos03»: Rojo eliminó a Blanco), y muestra
  «Victory!» / «Total victory!» con pvictory.pcx enmarcada, sin tabla. El Visor hace lo mismo: «Total victory!» con un
  solo bando= en el .FIN, «An allied victory!» con varios (este último texto no se vio en el juego todavía).
- Subtítulo del acuerdo: Arial 10 (la de los sucesos), bermellón.

## Próximo paso

Publicar el Monitor de IA 1.0.21 (`python ia\monitor-ia\publicar.py`) y el Visor de historia 1.0.8.0
(`python iaisor-historia\publicar.py`): ya commiteados; el 2/11 no se pudo porque los dos .exe (ia\Monitor-IA.exe,
ia\Visor-Historia.exe) estaban abiertos y la compilación no puede reemplazarlos.


Nada de código pendiente en este plan: quedan las pruebas reales (TAREAS 84 y 85). Si la 84 muestra que el acuerdo
tiene que pasar la partida a HISTORY en todas las PC, enganchar la recepción del chat (ver B2, «Límite»).
