# Anexo del manual: cómo funciona la IA del juego (pedido del 25/10/2026)

## Qué pidió el usuario
Un PDF **separado** del manual del parche (`manual\Manual-Era-de-Alianzas.pdf`), como anexo complementario,
que explique a fondo cómo juega la IA de los colores de la computadora en toda situación: defenderse, atacar,
aliarse con otras IA, aliarse con humanos, alianzas desactivadas, romper alianzas, enviar oro, cumplir misiones,
perfiles de personalidad, etc. Es para que el usuario pueda verificar que entiendo cómo funciona la IA.
Estudio profundo: recorrer cada función, orden y rutina del exe que interviene. Sin apuro.

## Fuentes a repasar (todas)
- Transcripciones de sesiones: `C:\Users\Rodolfo\.claude\projects\f--source-repos-actualizador-warlords\*.jsonl`
  (56 al 25/10/2026). Hay que filtrar las del banco de pruebas, la IA, las alianzas y las personalidades.
- `ia\PENDIENTE-entrenamiento-ia.md`, `ia\PENDIENTE-monitor-ia.md`, `ia\puntos-de-victoria.md`,
  `specs\ia-alianzas-v1.md`, `specs\ia-destrezas-v1.md`, `TAREAS.md` (resultados de las tandas en «Hecho»),
  `parches\vista-aliada\build.py` (los comentarios documentan direcciones del exe) y `git log`.
- «ROADMAP.md»: **no existe en este repo**. Buscarlo en los otros repos (DarkCompare, DarklordsValidator, EditorPGS)
  y en la memoria; si no aparece, decirlo.
- `ia\datos.db`: 63 tandas (1 a 65), 372 partidas ok/tope. Reanalizar con `ia\informe.py` y con consultas propias.
  Las partidas en estado 'invalida' no cuentan (las tandas 53 a 64 son pruebas o se anularon).
- El exe `C:\Warlords3\DarklordAV.exe`: desensamblar las rutinas de la IA para cubrir lo que falte.

## Lo ya sabido que hay que incluir (ejemplos)
- Diplomacia: tabla 0x55ee4c + a*56 + b (0 aliados, 1 paz, 2 guerra; +9 propuestas; +18/+36 palabras); opción 0x53c393 & 8.
- Con la diplomacia apagada, 0x49fec0 (llamada desde 0x4476d9) alía a toda computadora contra el humano;
  las propuestas se aplican en 0x4395c0. vista-aliada 1.0.71.0 la saltea en modo tanda.
- Personalidades: bits en +0xc0 del jugador (Merchant = descuento de mercenarios, Famous = descuento de ítems).
- Con la diplomacia encendida, la IA cambia de relación muy a menudo (5549 cambios en 281 partidas).
- Criterios del usuario en la memoria: juzgar las alianzas por bloque y no las pérdidas aisladas, y tandas por bando.

## Cómo entregarlo
- Fuente en `manual\anexo-ia\` (HTML más un build propio, como `manual\build_manual.py`), y el PDF en `manual\`.
- En español, para un jugador que no es programador. Las direcciones del exe van en un apéndice técnico.
- Separar lo **verificado** (desensamblado o medido en tandas, con el número de tanda o la dirección) de lo **inferido**.
- Commitear, y anotar en TAREAS.md la tarea de leerlo.

## Estado
Hecho (25/10/2026): `manual\anexo-ia\anexo.html` + `build.py` → `manual\Anexo-IA.pdf` (22 páginas). Lectura en TAREAS 42.
Quedó sin ubicar (capítulo 16 del anexo): cómo reparte puntos «AI Chooses Personalities», qué es «Loot» (0x56219e),
los umbrales de «media/completa» pila al atacar, la estimación de batalla y las condiciones completas del modo rendición.
No se halló rutina de la computadora que envíe oro o soborne. Próximo paso: según lo que marque el usuario.
