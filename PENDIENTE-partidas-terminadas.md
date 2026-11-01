# Partidas terminadas a una carpeta aparte

Pedido del usuario (1/11/2026): que el juego parcheado (DarklordAV.exe, parche vista-aliada) pase las partidas
**terminadas** a una carpeta nueva, distinta de NETSAVES, donde se guardan normalmente. Solo en el parche, no en
el Darklord.exe original.

Para qué (contexto): el Visor de historia (`PENDIENTE-visor-historia.md`) sirve sobre todo para consultar
partidas reales del ranking; tenerlas terminadas y separadas facilita encontrarlas.

## Plan

1. Ubicar en DarklordAV.exe el momento en que la partida termina (pantalla de victoria / fin por límite de
   turnos o condición) y la rutina que guarda en NETSAVES (y la de SAVES, si aplica).
2. En ese momento, guardar (o mover) el .SAV de la partida a la carpeta nueva. Nombre propuesto:
   `TERMINADAS` dentro de la carpeta del juego; se crea si no existe.
3. Partidas en red: verificar qué PC lo hace (anfitrión, cada una) sin desincronizar.
4. Construir con `parches/vista-aliada/build.py`, probar en C:\Warlords3, anotar la prueba en TAREAS.md y
   publicar con `tools\publicar-parche.ps1`.

## Por decidir al investigar

- Mover o copiar: «pasar» sugiere mover; si la partida terminada queda solo en TERMINADAS, NETSAVES queda
  limpia. Confirmar que el .SAV al terminar contiene el estado final (para el Visor).

## Próximo paso

Punto 1.
