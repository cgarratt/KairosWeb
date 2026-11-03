# KairosWeb v4.4.0 · Cuatro tarjetas BTC

Base v4.3.0. Layout aprobado: cuatro tarjetas en una fila de escritorio, dos columnas en pantallas menores de 850px y una en móvil estrecho. RSI, Stoch RSI y ADX: minivelocímetro a la izquierda y valores a la derecha. Cuarta tarjeta «Spot y referencias»: Spot BTC/USDT, STH onchain USD, EMA20 y EMA50 con distancia porcentual y barras centradas.

## Datos y temporalidad

- Balancer: RSI/Stoch/ADX y EMA20/EMA50 en 1D.
- Compras/Ventas: los mismos indicadores y EMA en semanas completas 1W lunes–domingo UTC. EMA calculada desde cierres, inicialización SMA del período; no desde promedios de EMA diaria. Los históricos usan el proveedor activo KuCoin o Binance, sin mezclar ni rellenar huecos. Faltan históricos válidos: EMA N/D, nunca Spot como reemplazo.
- Spot: cotización BTCUSDT del dashboard ya validado, antigüedad máxima 180s y futuro máximo 30s. Se conserva hora original y fuente.
- STH: métrica Glassnode `/v1/metrics/market/price_realized_less_155_usd`, BTC, resolución 24h; costo realizado de UTXOs menores de 155 días. Consulta independiente del timeframe técnico. No se transforma STH en una EMA semanal. Solo puntos diarios cerrados; se muestra fecha nativa UTC, conservando su corte propio. Máximo aceptado: 72h desde fecha nativa del punto.
- Monedas: Spot y EMA están en USDT. STH está en USD. Distancia a EMA = 100*(SpotUSDT−EMAUSDT)/EMAUSDT. Distancia a STH = 100*(SpotUSDT*USDTUSD−STHUSD)/STHUSD. USDT/USD procede de Glassnode `/v1/metrics/market/price_usd_close`, activo USDT, cierre diario independiente (no FX en tiempo real). Sin conversión reciente válida: precio STH visible si válido, distancia STH N/D. No se supone USDT=USD.
- Barras: escala ±6.25%; se limitan al borde para distancias mayores. El texto porcentual conserva su valor completo. No son probabilidades ni señales de trading.

## Glassnode desde la Web

«Actualizar STH · Glassnode» realiza una acción explícita de lectura: dos métricas públicas, sin enviar cartera, saldos ni direcciones privadas. Consulta por defecto `https://mcp.glassnode.com`, herramienta `fetch_metric`, usando una sesión FastMCP. No se requiere actualizar los conectores Binance/KuCoin/Hyperliquid. La conexión de Glassnode en GPT no comparte caché con Web.

Consulta siete días, dentro del acceso público documentado (máximo 30 días). No necesita API key para el acceso público probado. Opcional `GLASSNODE_API_KEY` en entorno, solo si el operador decide usar acceso autenticado; se envía como cabecera X-Api-Key, nunca en archivo o URL y puede consumir créditos del proveedor. No se configuró ninguna clave.

Caché local Web `KAIROS_GLASSNODE_CACHE_FILE` opcional, default `/tmp/kairos-glassnode-refs.json`. Mínimo 60s entre consultas explícitas y reutilización del mismo día UTC cuando ambas métricas siguen vigentes. Fechas originales no se rejuvenecen. Sin cron, tareas o consultas automáticas al navegar. Un reinicio sin disco persistente puede eliminar la caché: pulsar de nuevo el botón. La fuente STH o FX puede fallar sin bloquear Spot, EMA o los otros indicadores. Permisos/errores del proveedor producen N/D, no valores supuestos.

## Instalación y validación

Descomprimir el ZIP y subir su contenido a la raíz del repositorio Web existente. Conservar variables y secretos. Desplegar en el servicio Render Web y verificar `/health`: 4.4.0 y `release_assets.consistent=true`. Actualizar Spot e históricos en sus acciones existentes (preferiblemente 999 días para el cálculo semanal); después pulsar Actualizar STH. Revisar fuentes y fechas desplegables. No ejecutar scripts de ejemplo como sustitutos de datos reales.

261 tests aprobados, plantillas Jinja y JavaScript inline de Compras/Ventas comprobados; runtime de minivelocímetros y manejo N/D comprobados. El adaptador incluido obtuvo STH y FX de Glassnode en prueba real local con fecha nativa 2026-11-02 UTC. Esto no certifica el despliegue Render ni su conectividad. No se incluye el dato real como fixture/cache de producción. Sin QA visual de navegador.

STH y EMA son contexto visual; no se incorporan como nuevos filtros financieros. Continúan las reglas RSI/Stoch con confirmación ADX >23, BTC NEVER SELL y protecciones QF/Core/HODL/compromisos. No cambia MASTER, PRI, órdenes, pivotes ni la planificación de tareas.

Fuentes oficiales: https://docs.glassnode.com/integrations-and-tools/glassnode-mcp-server y https://studio.glassnode.com/charts/market.PriceRealizedLess155Usd
