# KairosWeb v3.0.19 — Pivotes BTC semanales 5L/5R

Corrige el gráfico Portafolio: antes usaba 2 semanas a cada lado; ahora exige extremos estrictos con 5 semanas completas a la izquierda y 5 a la derecha. Se excluye la semana UTC en curso. Las ventanas con semanas faltantes no cuentan como confirmación. Empates no son extremos estrictos.

Se calculan sobre toda la historia disponible (incluidas semanas previas al CL) y se muestran desde la semana del CL publicado hasta la última semana cerrada. Se seleccionan los últimos tres extremos confirmados en orden temporal, sin sustituirlos por candidatos ni colapsar artificialmente extremos consecutivos del mismo tipo. Cada pivote informa confirmed_at_utc: apertura UTC del lunes posterior al cierre de la quinta semana derecha. Si hay menos de tres, se muestran solo los disponibles y el contador n/3.

No cambia el régimen SMA20 de tendencia ni publica pivotes Elliott/CL/O1–O5 en MASTER. Conserva reglas de órdenes y reservas de v3.0.18; compatible con KairosGPT v1.3.13.

Validación actual: 8 pruebas aisladas ejecutan la función de producción (no una copia de su algoritmo), cubren 2R/5R, quinto vecino, empate, últimos tres, historia pre-CL, huecos y semana actual. Compilación Python verificada. La suite completa de Flask no fue repetida en este entorno; falta prueba visual y despliegue remoto. No se cambiaron saldos ni órdenes.
