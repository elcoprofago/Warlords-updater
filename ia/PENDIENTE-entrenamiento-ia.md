# Entrenamiento de la IA de los bandos — estudio y plan

Estado al 13/10/2026: estudio hecho, nada implementado. Respuesta completa en el chat de esa fecha; acá lo necesario
para retomar.

## Hechos de partida
- La IA es código x86 compilado dentro de Darklord.exe (1997). No hay red neuronal ni archivo de pesos: cada cambio
  hasta hoy fue un parche binario en cuevas de código (parches\vista-aliada\build.py: ai_move, ai_conv, ai_free...).
- Ya se puede ejecutar código real del juego sobre el estado de un .SAV con unicorn (prueba_emulada.py, prueba_ia*.py).
- PC: Ryzen 5 5600G (6 núcleos/12 hilos), 47 GB RAM, RTX 5050. Alcanza de sobra para el análisis y el ajuste;
  el cuello de botella es cuántas partidas se pueden jugar, no la potencia de cálculo.

## Plan (por etapas; cada una sirve sola)
1. Medir antes de diseñar (regla 3): ¿el juego permite partidas con todos los bandos en IA y sin pausas?
   ¿cuánto tarda un turno de IA nativo y emulado? ¿dónde están las constantes de decisión de la IA
   (umbrales de ataque, valor de ciudades, reservas de oro)?
2. Registro: gancho en el exe que agregue una línea por turno y bando a LOGS\IA.csv (ciudades, ejércitos,
   oro, batallas ganadas/perdidas, decisiones clave). Más un .SAV automático por turno si hace falta detalle.
3. Parámetros: llevar esas constantes a un archivo de texto (DATA\IA.INI) que el exe lea al arrancar.
   Sin archivo, valores originales (control que tiene que sobrevivir: el comportamiento original idéntico).
4. Ajuste: torneos IA contra IA en mapas chicos con semilla fija; un optimizador (evolutivo, tipo CMA-ES)
   propone juegos de parámetros, se juegan N partidas, gana el que más gana contra la IA de referencia.
5. Revisión externa: análisis de las partidas humanas grabadas acá (Claude), para encontrar patrones
   que la IA no tiene y convertirlos en reglas o parámetros nuevos.

## Próximo paso
Etapa 1. Frase para retomar: "Seguimos con ia\PENDIENTE-entrenamiento-ia.md, etapa 1".
