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

## Descartado
Combate ácido/relámpago, diplomacia, misiones, ingresos y vida de héroes del Code Patch: cambian el juego entre
humanos y no se probaron en multijugador.
