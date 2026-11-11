# PENDIENTE: ventana de victoria, simulador con edificios y manual (pedido del 11/11/2026)

Viene de PENDIENTE-life-ward.md (Life Ward de edificios hecho en vista-aliada 1.0.198.0; TAREAS 169).
Confirmado por el usuario: **Life Ward solo para edificios**; héroes, items y magias se ven más adelante.

## Parte A: ventana de victoria solo para el atacante — HECHA (vista-aliada 1.0.199.0, TAREAS 170)
- Causa: no era el original sino el parche propio cv_chk (combate visto por el atacado, 5/11/2026). Abre la ventana
  de combate (0x405a10) en la PC del atacado, y esta termina en 0x406d10, que abre la de victoria (0x4d52d0) si ganó
  el atacante, hay ciudad y [0x537ce8] es humano; en la PC del atacado [0x537ce8] es el atacado.
- Arreglo: marca cv_def = 1 mientras cv_chk muestra el combate; cv_vic (en 0x406da9) sale entonces sin abrirla.
- Prueba de juguete en prueba_combatevisto.py (atacado no la ve; controles: el atacante la ve, sin humano igual que el
  original): todo OK. Falta la prueba en red (TAREAS 170).

## Parte B: Simulador de combate (simcombate\) con murallas, torre y faro — HECHA (simulador 1.0.21.0, vista-aliada 1.0.200.0, TAREAS 172)
- Hecho: desplegable «Edificio del defensor» en TERRENO; el motor busca OB_TAB/ob_map en el exe por el código de ob_at
  y pone la obra en la casilla del defensor; el exe emulado aplica los bonos solo. prueba_escenario.py 7: todo OK
  (3 contra 3 gnollcav: 50,70 % sin obra, 38,99 % faro o torre, 18,93 % muralla).
- Hallado al probar: bridgeab (vista-aliada) leía la x con basura en la parte alta de ebx y el +1 de fuerza de torre
  y faro nunca se aplicaba en combate. Corregido (movsx) en 1.0.200.0.
- Se entiende por «visor de combates» el Simulador de combate (simcombate\, PENDIENTE-simulador-combate.md,
  repo elcoprofago/Simulador-Combate). Confirmado por el usuario el 11/11/2026.
- En el menú del escenario, agregar los edificios nuevos: **faro, torre de vigía y muralla**, con su Life Ward
  (+1, +2, +3) y, para la muralla, los bonos del muro (Missiles +3, Acid +3, Fortify +3, Life Drain +1).
- Datos exactos en build.py: LW_MURO/LW_TORRE/LW_FARO, WB_MIS/WB_ACID/WB_FORT/WB_LD, wb_grp, wb_unit; ciudad: Life
  Ward = tamaño (1-3). Torre y faro dan además +1 de fuerza a los no héroes (bridgeab).
- El simulador emula el exe (motor.py): ver si alcanza con poner la obra en OB_TAB/ob_map del DarklordAV.exe
  emulado o si hay que cargarlo a mano. Versión nueva visible (regla 19) y publicar con simcombate\publicar.py.

## Parte C: Manual del juego — HECHA (vista-aliada 1.0.201.0, TAREAS 173)
- Hecho: capítulo XVII «Obras y defensas» al final de manual\manual.html (al final para no renumerar las
  referencias «cap. N»), más filas en índice, novedades, referencia rápida y estado (apéndice C).

## Para retomar
Frase: «Seguimos con PENDIENTE-victoria-simulador-manual.md, parte C».
