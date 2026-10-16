# Kairos Web v3.2 · Horizon

Actualización visual sobre v3.1: identidad **Kairos Horizon**, isotipo vectorial, versión horizontal y favicon SVG, nuevo estilo azul marino/celeste. Se conserva el soporte de logos para 12 tokens + USDT y todas las páginas por modo.

## Despliegue

Reemplaza los archivos del repositorio en GitHub por **el contenido** de esta carpeta (sin crear una carpeta anidada), confirma los cambios en `main` y espera el deploy automático de Render. No cambies las variables de entorno o claves existentes.

## Archivos de marca

- `static/kairos-horizon.svg` — isotipo, favicon y header
- `static/kairos-horizon-horizontal.svg` — logo horizontal

## Importante

- Versión de solo lectura. No envía órdenes.
- Continúa con autenticación Basic del navegador: **no** existe una pantalla de login personalizable todavía.
- Conexiones MCP e inventario heredados de v3.1. La caché/reintentos ayudan con cold starts pero no garantizan disponibilidad; para un DATA ERROR persistente revisar logs.
- Los precios dinámicos no actualizan por sí solos el snapshot estático de unidades, USDT o fills.
- Los logos de monedas se solicitan a un proveedor externo; para no depender de él convendría empaquetar iconos con licencias apropiadas más adelante.

## v3.3
- Kairos sin texto Horizon; conserva el símbolo geométrico seleccionado.
- Iconografía patrimonial y logos de exchanges (CDN, con fallback).
- `/api/mcp-diagnostics` comprueba llamadas reales a ambos MCP e informa códigos y error_id, sin URL ni secretos.
- Buscar `ID=...` en Render Logs para causa específica.
- Se mantiene autenticación Basic y read-only.


## v3.4
- Menú de modos movido fuera del dashboard a `/modes`, con botón superior.
- Panel de comparación por Tier contra target (peso sobre la manga cripto; USDT excluido).
- Columna Valor BTC en la tabla ejecutiva: `valor_USDT / BTCUSDT` del mismo lote Binance MCP.
- Conserva tratamiento DATA ERROR y políticas de solo lectura de v3.3.
