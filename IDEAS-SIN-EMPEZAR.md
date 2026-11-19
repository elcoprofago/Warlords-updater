# Ideas sin empezar (recuento del 18/11/2026)

Ideas surgidas en algún momento (del usuario o propuestas por Claude) sobre este repo y sus complementarios
(Puente, Votación, DarkCompare, DarkValidator, EditorPGS) que nunca se empezaron. No incluye lo que está en curso
o esperando una prueba en `TAREAS.md`.

Límite: sale solo de lo anotado en los `PENDIENTE-*.md`. Lo hablado en conversaciones sin anotar no aparece; las
del 27/8 al 16/10/2026 se borraron.

Cuando una idea se empiece, se quita de acá y pasa a su `PENDIENTE-*.md`.

## Juego (parche vista-aliada)
1. **Día/noche: lo no explorado más oscuro sin Hidden Map.** Primero, que el juego lleve aparte el registro de lo
   explorado (`PENDIENTE-dia-noche.md`, paso 7).
2. **Life Ward dado por una magia, un poder de héroe o un ítem.** «No pedido todavía» (`PENDIENTE-life-ward.md`).
3. **Construir en el agua** (minas o trampas navales). «No pedido todavía»
   (`parches/vista-aliada/PENDIENTE-pozos-y-trampas.md`, pedidos del 22/10).
4. **Construcciones, etapa 2:** que la IA convierta ciudades, y una miniatura propia. Solo si se pide
   (`PENDIENTE-construcciones.md`).
5. **Mociones de votación nuevas** («6. Otras, a incorporar», `PENDIENTE-pedidos-15nov.md`).
6. **Textos en inglés que faltan:** las órdenes por chat, los textos del Visor de historia y revisar si los PCX
   tienen texto en castellano.

## IA
7. **La IA le pide cosas al humano aliado** («mandame oro», usando Bribe). Es la segunda etapa de los mensajes
   entre aliados (`ia/PENDIENTE-entrenamiento-ia.md`, 19/10).
8. **Regla de cantidad/calidad de los grupos por tercios de la partida** («para después», 19/10).
9. **Averiguar si el mapa oculto es oculto también para la IA.** Es condición previa para tocar la exploración.
10. **Que la IA use la magia.** Casi no lanza hechizos (9 en 30 partidas); ver 0x49b8b0
    (`ia/PENDIENTE-ideas-moddb.md`).
11. **Héroes del 25th Anniversary:** si se retoma, antes sumar el registro de habilidades compradas (+0x3fc).

## Banco de pruebas / Monitor de IA
12. **Comparativa de bandos (.PGS) en el PDF.** Pide una etapa propia y anotar qué .PGS juega cada color
    (`ia/PENDIENTE-monitor-ia.md`).
13. **Publicar los PDF de estadísticas** en una sección de la página del Clan.
14. **En el Monitor:** que muestre la duración de todas las partidas terminadas (hoy solo las últimas 5) y un
    informe después de cada partida (hoy sale al final de la tanda).
15. **Probar 10 juegos a la vez** (Warlords3-9 y -10) contra 8 (`ia/PENDIENTE-banco-paralelo.md`).

## Visor de historia
16. **Distribuirlo como opción del Actualizador.** Además, dos detalles menores: el tamaño del escudo chico y los
    colores del minimapa por terreno (`PENDIENTE-visor-historia.md`).

## Instalación / Actualizador
17. **Instalación completa en una PC limpia:** comparar contra el instalador de GOG. Quedó frenado esperando
    permiso para usar innoextract (`PENDIENTE-instalacion-completa.md`).

## Puente Warlords (repo `puente-warlords`)
18. **Que el Puente avise si falta DirectPlay** antes de abrir el juego (`PENDIENTE-estabilidad.md`).
19. **Pasar el tráfico UDP del juego por UDP propio** en vez de dentro del TCP. Solo se retoma si aparecen picos
    de lag sin cortes.
20. **Plan B de «inyectar como GameRanger»** si DirectPlay anuncia la dirección equivocada (`PENDIENTE-spec.md`).

## Descartadas (no son pendientes)
- Botón de pausa en el Monitor.
- Usar en el ranking el arreglo de hechizos y los héroes del 25th: no mejoraron.
- Las demás ideas del Code Patch de ModDB.
- Crear el DirectDraw en el segundo monitor: es un cambio riesgoso.
