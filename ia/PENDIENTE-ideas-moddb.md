# Ideas tomadas de los parches públicos de ModDB (15/11/2026)

Parches analizados en `F:\source\repos\Mods` (ver `propuesta\ESTRATEGIA-negociacion.md`). Regla del usuario: de
ellos se incorpora solo lo que se demuestre que mejora el nuestro, con código y datos propios.

## Paso 1 — Héroes: movimiento más caro (a cargo del usuario, TAREAS 220)
Idea del 25th Anniversary Project 0.7: la IA gasta puntos de habilidad en movimiento aunque sus héroes ya sean más
rápidos que sus tropas. Él subió un poco el movimiento base de los héroes y encareció comprar movimiento
(+16 por 4 puntos). **No está medido**: su autor casi no lo probó.

## Paso 2 — Medirlo en el banco (Claude)
Tanda con los héroes nuevos en el mismo mapa y criterio de bandos que las últimas tandas, comparada con ellas.
Mirar: niveles y habilidades que compran los héroes de la IA, misiones cumplidas, victorias. Si mejora, el
paquete HERO se publica (`tools\publicar-paquete.ps1 HERO`) y llega al ranking.

## Paso 3 — Error de la IA al elegir hechizos (Claude)
Descripción pública del Code Patch 1.q10: al pesar un hechizo, la IA suma también las casillas de efecto vacías,
que le dan un valor al azar. Arreglo: que las vacías pesen cero. Reprogramarlo con código propio en
`parches\vista-aliada\build.py`, primero solo para los colores en prueba; tanda; si mejora, pasa al ranking.
No copiar nada del plugin. Ojo: el Code Patch también toca 0x45EC40 (misiones), que nosotros usamos.

**Hecho en vista-aliada 1.0.223.0 (15/11/2026), falta la tanda (TAREAS 221).** Lo medido en Darklord.exe:
- 0x492c40(unidad, efecto, costo) pesa una habilidad o efecto (tabla de saltos por id 1..52). Un id fuera de la tabla
  (el 0, casilla vacía) cae al caso por defecto: azar(1,6) × azar(1,6). Después todo se multiplica por azar(40,80)/100
  y se divide por costo + 3.
- La llaman dos lugares: 0x49b4a6, subir de nivel (los 10 casilleros del héroe, +0x3fc; no tiene vacíos) y 0x49b7ed,
  elegir hechizo: suma los 4 efectos del hechizo con costo 1. Ahí está el error: un hechizo de 1 efecto suma 3 azares.
- Arreglo: `hs_w` en `build.py` reemplaza el call de 0x49b7ed; con efecto id 0 devuelve 0, solo con IA.INI y si el
  dueño de la unidad (+0xe, bits 5-8) está en prueba. Sin IA.INI juega como el original: no llega al ranking hasta
  que una tanda lo confirme. `parchesista-aliada\prueba_iahechizos.py` → TODO OK (vacío vale 0 solo en prueba con
  IA.INI; efecto lleno, color original y sin IA.INI dan lo mismo que el original).
- Límite: la tanda no registra qué hechizos se lanzan; se juzga por victorias y puestos. Si no se ve nada, sumar un
  evento de hechizo lanzado antes de descartarlo.

## Descartado
Combate ácido/relámpago, diplomacia, misiones, ingresos y vida de héroes del Code Patch: cambian el juego entre
humanos y no se probaron en multijugador.
