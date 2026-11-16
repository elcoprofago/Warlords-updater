# Ideas tomadas de los parches públicos de ModDB (15/11/2026)

Parches analizados en `F:\source\repos\Mods` (ver `F:\source\repos\negocio-warlords\ESTRATEGIA-negociacion.md`). Regla del usuario: de
ellos se incorpora solo lo que se demuestre que mejora el nuestro, con código y datos propios.

## Paso 1 — Héroes: movimiento más caro (a cargo del usuario, TAREAS 220)
Idea del 25th Anniversary Project 0.7: la IA gasta puntos de habilidad en movimiento aunque sus héroes ya sean más
rápidos que sus tropas. Él subió un poco el movimiento base de los héroes y encareció comprar movimiento
(+16 por 4 puntos). **No está medido**: su autor casi no lo probó.

## Paso 2 — Medirlo en el banco (Claude)
Tanda con los héroes nuevos en el mismo mapa y criterio de bandos que las últimas tandas, comparada con ellas.
Mirar: niveles y habilidades que compran los héroes de la IA, misiones cumplidas, victorias. Si mejora, el
paquete HERO se publica (`tools\publicar-paquete.ps1 HERO`) y llega al ranking.

**Preparado el 15/11/2026 (TAREAS 222).** El usuario puso los 15 `.HER` del 25th en `C:\Warlords3\HERO` (originales en
`HERO\back`). Medido: esos héroes piden 42 hechizos propios del 25th (`25mason`, `25pets`...) que nuestro SPELL no
tiene; ninguno pisa uno nuestro y las 11 tropas que invocan ya existen. El resto del mod (ARMY, ITEMS, 25th.rul) no
hace falta para los héroes y no se instala: cambiaría más que lo que se quiere medir. `ia\heroes25.py 25th|original|
estado` cambia entre los dos juegos y verifica byte a byte lo que quedó (probado en carpeta de juguete con controles).
- Diseño: el cambio de héroes les toca a todos los colores, así que no se mide prueba contra original dentro de una
  tanda. Se comparan dos tandas iguales y con la misma versión: la 221 (héroes originales, `C:\Warlords3` ya quedó así)
  y la 222 (héroes del 25th). Ojo: la 221 cambia los hechizos de los colores en prueba; se compara color a color.
- Límite: el banco no registra niveles ni habilidades compradas, solo héroes vivos por turno. Se juzga por héroes vivos
  al final, ciudades, puestos y largo de partida; si eso no alcanza, sumar el registro de las habilidades (+0x3fc).
- Si mejora, para el ranking hay que publicar también los 42 hechizos (paquete SPELL), no solo HERO.
- **Resultado (16/11/2026), tanda 173 (10 partidas completas, 1.0.232.0, héroes del 25th) contra 171-172 (18 partidas,
  misma versión, héroes originales), todos los colores juntos:** PV por color 7,0 contra 7,0; ciudades 5,2 contra 5,2;
  ejércitos 21,5 contra 20,6; héroes vivos al final 0,45 contra 0,42 por color; todas las partidas al tope de 30 turnos.
  **Sin mejora medible: no se publica HERO ni SPELL.** `C:\Warlords3` volvió a los héroes originales
  (`ia\heroes25.py original` → OK). Si se retoma, sumar antes el registro de habilidades compradas (+0x3fc).

## Paso 3 — Error de la IA al elegir hechizos (Claude)
Descripción pública del Code Patch 1.q10: al pesar un hechizo, la IA suma también las casillas de efecto vacías,
que le dan un valor al azar. Arreglo: que las vacías pesen cero. Reprogramarlo con código propio en
`parches\vista-aliada\build.py`, primero solo para los colores en prueba; tanda; si mejora, pasa al ranking.
No copiar nada del plugin. Ojo: el Code Patch también toca 0x45EC40 (misiones), que nosotros usamos.

**Hecho en vista-aliada 1.0.223.0 (15/11/2026); tandas 170-172 hechas, resultado abajo.** Lo medido en Darklord.exe:
- 0x492c40(unidad, efecto, costo) pesa una habilidad o efecto (tabla de saltos por id 1..52). Un id fuera de la tabla
  (el 0, casilla vacía) cae al caso por defecto: azar(1,6) × azar(1,6). Después todo se multiplica por azar(40,80)/100
  y se divide por costo + 3.
- La llaman dos lugares: 0x49b4a6, subir de nivel (los 10 casilleros del héroe, +0x3fc; no tiene vacíos) y 0x49b7ed,
  elegir hechizo: suma los 4 efectos del hechizo con costo 1. Ahí está el error: un hechizo de 1 efecto suma 3 azares.
- Arreglo: `hs_w` en `build.py` reemplaza el call de 0x49b7ed; con efecto id 0 devuelve 0, solo con IA.INI y si el
  dueño de la unidad (+0xe, bits 5-8) está en prueba. Sin IA.INI juega como el original: no llega al ranking hasta
  que una tanda lo confirme. `parches\vista-aliada\prueba_iahechizos.py` → TODO OK (vacío vale 0 solo en prueba con
  IA.INI; efecto lleno, color original y sin IA.INI dan lo mismo que el original).
- Límite: la tanda no registra qué hechizos se lanzan; se juzga por victorias y puestos. Si no se ve nada, sumar un
  evento de hechizo lanzado antes de descartarlo.
- **Resultado (16/11/2026), tandas 170, 171 y 172 (28 partidas completas; en la 172 dos partidas no arrancaron,
  0 turnos, «colgada»):** puesto medio prueba 3,25 contra original 3,41; primeros puestos 16 contra 15; PV iguales
  (6,9); ciudades 4,9 contra 5,4. Referencia sin el arreglo (tandas 168-169, 1.0.221.0): prueba 3,33 contra 3,26.
  Mejora de unas 0,2 posiciones, dentro de lo que varía una tanda a otra (la 171 y la 172 dieron resultados opuestos
  entre sí) y con menos ciudades: **no es un avance confirmado, queda solo en la IA de prueba** y no pasa al
  ranking. Para decidir hace falta el evento de hechizo lanzado (ver si cambia qué se lanza) antes de más tandas.

- **Evento de hechizo lanzado (vista-aliada 1.0.233.0, 16/11/2026; TAREAS 232).** `hs_ev` reemplaza en 0x49b883 el
  call 0x4ba210(unidad, hechizo elegido, 0) y anota el evento 44 (solo con IA.INI): x = efecto 1 * 100 + efecto 2,
  y = costo, n = puntaje con que lo eligió (el del elegido está en [esp + 0x88 + 2 si] del llamador). El juego no
  cambia. `parchesista-aliada\prueba_hechizolanzado.py` → TODO OK (con IA.INI anota (44, 5, 712, 3, 437) y deja
  pila y registros intactos; control sin IA.INI no anota). `ia\informe.py` suma la sección «Hechizos lanzados» por
  IA: cuántos, puntaje medio, % de un solo efecto y los más lanzados. **Próximo paso:** con la tanda, ver si la IA de
  prueba lanza otros hechizos que la original (menos de un solo efecto inflados). Si no cambia nada, el arreglo no
  tiene efecto real y se descarta; si cambia y no empeora puestos, pasa al ranking.

## Descartado
Combate ácido/relámpago, diplomacia, misiones, ingresos y vida de héroes del Code Patch: cambian el juego entre
humanos y no se probaron en multijugador.
