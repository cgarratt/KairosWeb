# KairosWeb v1.1.0 RC1 — Mejoras 01 a 08

**Cambios funcionales:** alertas 1H solo pendientes con acuse masivo, edición de inversión remanente y costo medio derivado, publicación unificada, porcentajes con unidad/semántica explícita, totales de liquidez, explicaciones de parámetros, candidatos Elliott MCP editables sin certificación, tema visual azul marino oscuro.

**Seguridad:** formulario administrativo separado, `KAIROS_SESSION_SECRET` nuevo obligatorio, sesión firmada HttpOnly/Secure/SameSite, CSRF y auditoría persistente; editor de Google únicamente para el archivo Master. La edición no permite modificar órdenes históricas, fills, BSI ni pivotes certificados por inferencia.

**Sin cambios:** contrato Google Sheets `schema_version=5.0.0`; KairosGPT; saldos publicados; políticas O5 30% BTC / 70% USDT; vinculación Binance Spot y HYPE macro Hyperliquid Spot.

**Estado:** paquete candidato listo para pruebas en Render, no producción certificada.
