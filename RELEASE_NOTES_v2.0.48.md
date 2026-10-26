# KairosWeb v2.0.48 — Spot bajo demanda

- Primera consulta de precios Spot Binance MCP por proceso del servidor, al abrir una vista que requiere precios. Reutilización de la misma observación en las siguientes páginas; no caduca automáticamente a los 30 segundos.
- Botón «Actualizar Spot» en encabezado para usuarios autenticados: consulta Spot nuevamente y, si se valida, actualiza la observación compartida y recarga la vista. No requiere contraseña administrativa adicional, pero sí sesión y token CSRF.
- Se muestra la fecha/hora original de observación y se etiqueta la caché como `SNAPSHOT`, no `FRESH`/tiempo real. En caso de error, no se sustituye el snapshot previo ni se le asigna una fecha nueva.
- El caché reside en la memoria del proceso (un worker en render.yaml). Se reinicia con el servidor. No es almacenamiento persistente ni coordinación entre réplicas.
- Google Sheets sigue siendo fuente única y se consulta/valida de manera independiente; las órdenes y fills no se guardan en caché Spot.
- Datos históricos de Forecast, TradingBot, pivotes y alertas pueden requerir MCP por separado: este cambio optimiza la consulta común de precios Spot, no garantiza cero llamadas MCP en todos los módulos.
- Sin escrituras al MASTER ni órdenes enviadas. Es responsabilidad del usuario refrescar antes de tomar decisiones sensibles a precio.
