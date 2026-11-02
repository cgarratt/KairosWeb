# KairosWeb 3.0.39 · KuCoin primario

Instalar primero MCP KuCoin 1.1.0 y conservar KUCOIN_MCP_URL en el servicio Web. Después reemplazar el contenido del repositorio Web por este ZIP descomprimido, mantener variables/secretos, desplegar y recargar. /health debe indicar version 3.0.39 y release_assets.consistent=true. 99 archivos. GPT 1.3.18, Binance 5.4.1 e Hyperliquid 1.0.1 compatibles.

## Mercado

KuCoin es primario para Spot y velas 1D. Binance sólo se intenta como respaldo ante timeout/conexión, HTTP418/429 o5xx transitorios; nunca durante una pausa vigente. Falta de configuración/autenticación o datos inválidos no genera fallback automático. Una respuesta inválida conserva el error y los snapshots anteriores, sin promoverlos a vigentes.

Actualizar Spot: una consulta conjunta KuCoin para 12 pares, reutilizada 60s desde la observación original. Antigüedad de valoración máxima 180s. No descarga históricos. Si Binance es usado, aparece Binance Spot (respaldo), sin atribuirlo a KuCoin.

Actualizar históricos: en Configuración → Estado de conexiones MCP. Pide el snapshot KuCoin de 12 series 1D cerradas e indicadores diarios; Binance es respaldo completo ante fallo transitorio. Cada actualización conserva proveedor, par y cierre. No combina velas de exchanges; history_by_source conserva las cargas de cada proveedor. Indicadores RSI/StochRSI/EMA mantienen su fuente. Una carga con huecos/malformada se rechaza sin publicar un conjunto parcial. La historia puede ser más corta desde el listado; sus consumidores exigen la ventana que necesitan.

La Web reutiliza históricos hasta el próximo cierre UTC. El MCP KuCoin guarda SQLite y descarga días faltantes, pero un cambio a una ventana mayor puede requerir una descarga completa. Los archivos locales son temporales en Render Free salvo disco persistente ya provisionado. No se contrata ni instala almacenamiento externo.

Tendencia BTC1W, Compras, Forecast y revisión de candidatos diarios admiten la serie completa activa KuCoin/Binance, con procedencia real y semanas lunes-domingo UTC. HYPE macro sigue exclusivamente en Hyperliquid HYPE/USDC. BSI conserva su contrato Binance4H y sigue bloqueado sin certificación: no se sustituye con KuCoin. TradingBot conserva sus restricciones WATCH. No se publican ni cambian pivotes VALIDADO/CONFIRMADO por conmutar mercado.

Abrir Portafolio, navegar o abrir Configuración no realiza llamadas de mercado Binance. Las tarjetas y el diagnóstico integral requieren un clic explícito; su verificación es por proveedor, sin fallback encubierto. Spot e históricos permanecen acciones separadas.

## Comprobación en Render

1. Verificar MCP KuCoin 1.1.0 y sus cuatro herramientas antes de actualizar Web.
2. Actualizar Spot: debería indicar KuCoin Spot (primario) con 12 cotizaciones vigentes.
3. Actualizar históricos: debe informar KuCoin Spot y el último cierre UTC. Luego revisar la tendenciaBTC. Si faltan datos, se muestra N/D con causa; no se inventan velas.
4. No pulsar continuamente diagnósticos Binance durante pausas. Con KuCoin disponible no se necesita verificar Binance para valorar.

Variables Spot: KAIROS_PRIMARY_SPOT_TIMEOUT_SECONDS ahora corresponde a KuCoin(default 45s, rango 3–90); KAIROS_BACKUP_SPOT_TIMEOUT_SECONDS corresponde a Binance(default 10s, rango 3–45). Si existen valores de releases anteriores, revisarlos tras cambiar los roles. Mantener KUCOIN_MCP_URL, BINANCE_MCP_URL, HYPERLIQUID_MCP_URL y todos los secretos existentes.

239 pruebas Web aprobadas; health, consistencia de assets y plantillas Jinja verificados. Sin prueba visual de navegador ni validación de despliegue remoto. Desde este entorno la pruebaREST pública de velas KuCoin no devolvió JSON válido; cobertura histórica real pendiente de verificar en Render. Sin cambios en MASTER, saldos, fills, órdenes, custodia o automatizaciones.
