# KairosWeb v2.0.5 RELEASE — consolidado v2.0.4 + notificaciones unificadas

## Cambios acumulativos
- Compras O2: tabla al final después de distribución/liquidez; columna Spot; simulación secuencial O2C1–O2C4 con los fills **simulados** previos; estado del peso previo a cada compra mediante círculo rojo SOBRE, verde INFRA, ámbar NEUTRAL (banda DRIFT_BAND_PP publicada).
- Fondos de Precio/USDT: mínimo de velas cerradas 1D posteriores a un O1 **candidato** reconstruido por referencia histórica; alcanzado=verde, hasta 1% por encima=ámbar, sin evidencia=N/D sin color. No dependen del presupuesto del token ni del Spot actual. No certifican pivotes, órdenes ni fills.
- Slider Compras: valor inicial igual a (USDT físico - ReservaTrading QF) / P, expresado en porcentaje, con tope disponible y sin techo nominal 25% del patrimonio. Editarlo no modifica el Master.
- Campana de alertas única 1H/4H/1D: `/api/alerts/unread` acepta timeframe opcional; `/api/alerts/read` permite acuse individual; `/api/alerts/read-all` permite acuse global o filtrado por timeframe. `tipo_alerta` 1H (NIVEL_PROXIMO, NIVEL_TOCADO, FILL_*, REQUIERE_REVISION...), 4H (BREAK_BAJISTA, BREAK_ALCISTA, NUEVA_ESTRUCTURA...), 1D (NUEVA_ONDA, RECALCULO_MACRO, BALANCER_ACCION, BSI_ACCION, LIQUIDEZ_CRITICA...). Eventos sin certificación se rotulan INFORMATIVA y no habilitan ejecución.
- Autodiagnóstico de despliegue: `GET /health` devuelve `release_assets` con presencia, SHA-256 corto y marcadores de la plantilla `trade_sim.html`, JS secuencial y JS de campana. Si una pieza crítica falta o está obsoleta, retorna DEGRADED (HTTP 503) para detectar cargas parciales. La versión del backend por sí sola nunca prueba actualización visual.
- Cache-busting explícito de scripts de Compras por `?v=<versión>`; marca verificable `data-o2-ui-version` en la plantilla. La página es no-cache.

## Alcance
No hay escrituras en Google Sheets ni trading/custodia, no se alteran MCP ni KairosGPT. Los precios/indicadores en producción dependen de Google Sheets PUBLICADO y Binance/Hyperliquid MCP; sin evidencia requerida la interfaz falla cerrada.

## Despliegue GitHub → Render
1. Hacer copia o commit de la rama vigente y crear commit para la v2.0.5.
2. **Extraer el ZIP y copiar TODOS los archivos y las carpetas `templates/` y `static/` directamente a la RAÍZ del repositorio**, sobrescribiendo versiones anteriores (NO subir solo `app.py` ni subir una carpeta contenedora).
3. No subir claves ni .env; conservar las variables existentes en Render. Publicar commit y esperar finalización de Deploy en Render.
4. Abrir `/health`: exigir `version=2.0.5`, `status=UP`, `release_assets.consistent=true`; registrar los `sha256_12` de `compras_template`, `o2_simulator` y `alerts_bell`.
5. Abrir `/mode/compras` tras Ctrl+Shift+R; verificar en código fuente `o2-drift-dot` y `data-o2-ui-version="2.0.5"`; slider al máximo elegible; círculos y colores solo si la evidencia histórica lo permite.
6. Verificar `/api/alerts/unread` (con Basic auth) sin filtro y con filtros `?timeframe=1H`, `4H`, `1D`; probar lectura en entorno con identidad Google editora, sin modificar posiciones.
7. Confirmar seguridad, lectura del Master y MCP; no declarar producción certificada hasta pasar pruebas HTTP reales y navegador.

## Limitaciones
- La fecha O1 solo es provisional: si no se halla candidato en velas diarias disponibles, no se colorean niveles.
- La suite histórica contiene pruebas de versiones previas que exigen textos y ubicaciones eliminadas en v2.0; no representan criterios actuales. Se preservan para trazabilidad; las pruebas actuales están separadas.
- Sin acceso a Render/GitHub autenticado, el despliegue efectivo queda a cargo del usuario.

## Validación local de este paquete
- Chromium headless: PASS (slider al máximo de caja elegible, ocho círculos visibles para dos activos, Precio/USDT verde aun con $0 y rebalanceo simulado).
- Suite Python completa: 134 PASS, 10 FAIL por aserciones heredadas 1.9/2.0.0, 2 SKIP por dependencia Flask ausente en este entorno (no prueba HTTP real).
- Pruebas dirigidas de v2.0.5 y alertas: 15 PASS, 2 SKIP.
- Pruebas JS, sintaxis Python/JS: PASS.
