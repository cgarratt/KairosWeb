# KairosWeb v2.0.49 — Historial semanal compartido

- Compras y Forecast reutilizan en memoria las series MCP de velas diarias cerradas durante el mismo día UTC, compartidas entre vistas y usuarios del proceso. No se inventan ni sustituyen precios Spot.
- El caché distingue Binance Spot de Hyperliquid HYPE/USDC, símbolo, intervalo y parámetros de consulta.
- Actualizar Spot invalida además las series diarias, que se vuelven a consultar cuando se visite Compras/Forecast. No afecta saldos ni órdenes.
- Respuestas MCP fallidas no se almacenan; los intervalos 1h/4h no se cachean.
- Si Render reinicia o ejecuta múltiples workers, cada proceso mantiene su propio caché. La primera visita a Compras/Forecast seguirá necesitando histórico MCP.
- Validación local de código: 262 pruebas aprobadas, 2 omitidas, 4 subtests. No se ha verificado Render.
