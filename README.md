# Kairos Web v3

Kairos Web v3 añade:

- dashboard ejecutivo mejorado
- menú visual de modos
- una página preliminar por cada modo Kairos
- vistas read-only con tarjetas, tablas y gráficos simples
- conexión a MCP de Binance para valoración actual
- conexión a Hyperliquid para HYPE macro vía endpoint dedicado

## Despliegue en Render

1. Reemplaza el contenido del repositorio con esta versión.
2. Mantén `render.yaml`, `requirements.txt` y `data/`.
3. Conserva las variables ya creadas:
   - `KAIROS_WEB_USER`
   - `KAIROS_WEB_PASSWORD`
   - `BINANCE_MCP_URL`
   - `HYPERLIQUID_MCP_URL`
   - `BINANCE_MCP_TOKEN` si aplica
   - `HYPERLIQUID_MCP_TOKEN` si aplica
4. Haz push a `main` y espera el redeploy automático.

## Rutas nuevas

- `/mode/resumen`
- `/mode/balancer`
- `/mode/compras`
- `/mode/ventas`
- `/mode/tradingbot`
- `/mode/alertas`
- `/mode/forecast`
- `/mode/benchmark`
- `/mode/rotation`
- `/mode/montecarlo`

## Nota

Estas páginas son preliminares. Buscan reflejar visualmente el tipo de salida que Kairos entrega en ChatGPT, pero todavía no integran todos los motores formales ni las reglas completas de ejecución.
