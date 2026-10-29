# Pendiente: el Actualizador tiene que dejar el juego completo en una PC limpia (29/10/2026)

Pedido del usuario: el Actualizador debe ser **autosuficiente**. Hoy, con la opción 6 (sola o con la 9), la
instalación queda incompleta. Instalar con el instalador de GOG resolvería lo que falta, pero agrega archivos
de GOG que el juego no necesita: se prefiere que lo resuelva el Actualizador.

## Lo que se vio
- **DirectPlay:** en la notebook del usuario faltaba (es una característica de Windows que viene desactivada).
  Sin DirectPlay el juego no juega en red. El usuario lo instaló a mano el 29/10/2026. El Actualizador no lo
  revisa ni lo instala.
- **Archivos que faltaban** en la PC del usuario cuando el juego pasó a otra carpeta: los puso a mano; la
  opción 6 no los cubrió. **No se sabe todavía cuáles eran.**
- Relacionado (puente-warlords, `PENDIENTE-estabilidad.md`): los OBSOLETOS de vista-aliada recién se borran al
  abrir `DarklordAV.exe`; el Puente compara antes y avisa diferencias.

## Próximos pasos
1. Enumerar de una vez qué necesita el juego para correr: comparar una instalación de GOG limpia (o su
   instalador, extraído aparte con innoextract, sin instalarlo) contra lo que trae `Warlords3_FULL.zip` (su
   índice, ver `PENDIENTE-opcion6.md`). Lo que el juego usa y el zip no trae es lo que falta.
2. Separar lo que es de GOG y el juego no usa (`GOG`, `__support`, `unins000.*`, etc.), para no traerlo.
3. DirectPlay: que el Actualizador lo detecte y lo active
   (`dism /online /enable-feature /featurename:DirectPlay /all`, con permiso de administrador).
4. Probar en una carpeta vacía que la opción 6 sola deje el juego abriendo y jugando en red.
