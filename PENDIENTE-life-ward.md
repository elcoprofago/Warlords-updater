# PENDIENTE: habilidad Life Ward (contra del Life Drain)

Pedido del usuario (11/11/2026): una habilidad nueva, **Life Ward**. Tope +3. Cada punto anula un punto del
Life Drain enemigo: devuelve solo lo que el drenaje quita, nunca suma golpes por encima de los propios.

## Diseño decidido por el usuario (11/11/2026, segunda indicación)

- **Las unidades comunes no la llevan.** No hace falta agregarla al editor de unidades ni a las armas regulares.
- La llevan **por defecto los edificios**, para el grupo que defiende: **muro +3** (en cada casilla del muro; se usa
  la misma zona que los otros bonos del muro: sobre el bloque o a 1 casilla), **torre +2**, **faro +1**, **ciudad
  +1, +2 o +3** según cómo están armadas sus defensas (el tamaño, +0xa4 del registro de ciudad: 1, 2 o 3).
- Más adelante, quizás: alguna magia, poder de héroe o item que la dé. No pedido todavía.

## Hecho (vista-aliada 1.0.198.0, 11/11/2026)

- `wb_grp` (0x464df2, habilidades de grupo del defensor) carga el Life Ward en grp[+6] con `lw_max` (vale el mayor):
  ciudad de la casilla (0x440be0, tamaño con tope 3; también para defensores neutrales), obra de la casilla
  (torre LW_TORRE = 2, faro LW_FARO = 1) y muro propio cerca (LW_MURO = 3, junto con los bonos del muro).
- `lw_hit_a` (0x469913) y `lw_hit_d` (0x4699fe): `hits += out[2|3] - drenaje` pasa a
  `hits -= max(0, drenaje - ward)`. grp[+6] no lo cargaba nada antes, así que sin edificios todo queda igual.
- Prueba: prueba_muroataque.py, secciones «Life Ward de los edificios» y «Life Ward en los golpes» (con controles).
  Se corrigieron de paso 2 expectativas viejas de la sección del muro (Life Drain +1 desde la 1.0.197.0).
- Prueba en el juego: TAREAS 169.

## Lo averiguado (en Darklord.exe)

- Una unidad tiene **una sola habilidad**: código en +0xe6 y valor en +0xe8 del tipo de unidad. Los códigos
  válidos en 0x469083 van de 1 a 54. **Ojo:** el Simulador de combate (simcombate\datos.py) nombra 55 Questing,
  56 Mana Drain y 57 None, así que 55 y 56 **no** están libres como decía la versión anterior de esta nota.
  Hoy no importa (no se usa un código nuevo); si algún día un héroe o item la da, habrá que elegir otro código.
- Habilidades de grupo: 0x468440 (tabla de saltos 0x469634). Life Drain = código 54 → grp[0x16], tope 3.
- 0x4696c0: out[2] = grp_atacante[6], out[3] = grp_defensor[6], out[0xe] = drenaje del defensor,
  out[0xd] = drenaje del atacante.

## Falta

1. TAREAS 169 (prueba en el juego).
2. Si el usuario lo pide: Life Ward por magia, poder de héroe o item (para el atacante, grp[+6] del atacante
   ya lo respeta lw_hit_a).
