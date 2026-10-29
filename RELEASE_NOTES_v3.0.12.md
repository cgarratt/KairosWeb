# KairosWeb v3.0.12 — PRI visual y tendencia autónoma

Base: KairosWeb v3.0.11.

- PRI: velocímetro semicircular, clasificación y tres métricas. Metodología en desplegable.
- Tendencia BTC 1W: icono/estado visual; descarga de velas Binance Spot 1D en segundo plano, reutilizando caché histórico por día UTC. Agregación exclusivamente de semanas completas UTC, SMA20 y pendiente. N/D si faltan datos.
- El navegador consulta únicamente el estado de la tendencia por una ruta de solo lectura mientras se completa la carga; no dispara múltiples consultas MCP.
- No modifica la política PRI, los pivotes, saldos, órdenes ni MASTER.
- Se requiere verificación funcional en Render; los datos del proveedor no se simulan.
