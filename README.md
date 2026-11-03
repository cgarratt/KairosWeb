# KairosWeb v4.2.0 · Indicadores BTC/USDT

Balancer: RSI y Stoch RSI diarios (1D). Compras y Ventas: los mismos indicadores semanales (1W). Dos velocímetros por página; RSI/RSI-MA y K/D. TOTAL2 retirado del código activo, botón, endpoint y dependencias Web.

Descomprimir este ZIP y sustituir el contenido del repositorio Web existente. Conservar variables y secretos. Desplegar el último commit en el servicio Render Web. No se requiere actualizar los MCP ni configurar TradingView. Compatible con Binance MCP 5.4.1/5.5.0 y KuCoin MCP 1.1.0 para los históricos existentes.

En Configuración → Estado de conexiones MCP, Actualizar históricos (preferiblemente 999 días para el cálculo semanal). Actualizar Spot no descarga históricos. Verificar /health: version 4.2.0 y release_assets.consistent=true. Abrir Balancer (1D), Compras y Ventas (1W).

Si ya activaste las alertas TOTAL2 de la versión anterior, puedes desactivarlas en TradingView y retirar las variables TOTAL2 que añadiste. La Web ya no las utiliza; este paquete no modifica servicios ni alertas remotas. Mantener BINANCE_MCP_URL, KUCOIN_MCP_URL y los secretos existentes.

El paquete contiene código y pruebas; no acredita despliegue remoto ni datos reales actuales. Ver RELEASE_NOTES_v4.2.0.md y VALIDACION_RELEASE_v4_2.json.
