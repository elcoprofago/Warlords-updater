# PENDIENTE: habilidad Life Ward (contra del Life Drain)

Pedido del usuario (11/11/2026): una habilidad nueva, **Life Ward**, en dos versiones:
**Life Ward** (de la unidad) y **Life Ward (grp)** (de todo el grupo). Tope +3.
Cada punto anula un punto del Life Drain enemigo: devuelve solo lo que el drenaje quita,
nunca suma golpes por encima de los propios.

## Lo averiguado (en Darklord.exe)

- Una unidad tiene **una sola habilidad**: código en +0xe6 y valor en +0xe8 del tipo de unidad
  (registros de 0xfc bytes en 0x53c410, o en 0x568448 para héroes). Los códigos válidos van de 1 a 54:
  `0x469083 dec edx; cmp edx,0x35; ja` → 55 y 56 están libres para Life Ward y Life Ward (grp).
- Las habilidades de grupo se suman en 0x468440 (tabla de saltos 0x469634, índices 0x469684).
  Life Drain = código 54 → grp[0x16], **tope del juego 3** (0x4694b0). Por eso un arma con
  Life Drain +4 o +5 pelea con +3. Solo el bono del muro (que se suma después del tope) lo pasa.
- grp[+6] es un bonus de golpes de grupo que nada usa hoy (solo se pone en cero, 0x46858f).
  0x4696c0 lo copia a out[2] (atacante) / out[3] (defensor), y 0x4698b0 hace
  `hits += out[2] - out[0xe]` (atacante, 0x469913) y `hits += out[3] - out[0xd]` (defensor, 0x4699fe),
  con tope 1..4. **Es el lugar natural del Life Ward (grp)**: el código 56 carga grp[+6] (tope 3) y en
  0x469913/0x4699fe se cambia por `hits -= max(0, drenaje - ward)`.
- Life Ward de la unidad: la ficha de la unidad (0x467240, esi=[esp+0xb4], 0x24 bytes) usa sus 36 bytes;
  no queda uno libre. Hay que guardar el valor en una tabla aparte por casilla de combate, o leer la
  habilidad del tipo de unidad en el momento del cálculo (en 0x4698b0, buscando el tipo desde la entrada
  de combate: falta averiguar dónde guarda la entrada el tipo/ejército).

## Falta

1. Combate: grupo (grp[+6]) y unidad, con pruebas de juguete con control (prueba_muroataque.py como modelo).
2. Nombres y descripción visibles: las habilidades se muestran con cadenas en Sagetext.tex / edtext.tex
   ("Life Drain +%d|lf drn +%d|Life Drain|..."); averiguar cómo se indexan por código y agregar
   "Life Ward +%d|lf wrd +%d|Life Ward|..." y la versión (grp), en el juego y en el editor (war3ed_av.exe).
3. Que el editor de unidades deje elegir los códigos 55 y 56.
4. Decidir con el usuario qué unidades/héroes/objetos la llevan (paquete ARMY).
5. TAREAS con la prueba en el juego; versión nueva de vista-aliada.
