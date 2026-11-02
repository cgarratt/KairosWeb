# KairosWeb 3.0.36 · Configuración y diagnóstico MCP

## Instalación

Extraer el ZIP y reemplazar el contenido descomprimido del repositorio Web existente. Mantener las variables y secretos actuales. Desplegar en Render y recargar el navegador. /health debe informar version=3.0.36, component_versions.KairosWeb=3.0.36 y release_assets.consistent=true. Contiene 99 archivos.

Compatible con GPT1.3.17, Binance5.4.1, KuCoin1.0.1 e Hyperliquid1.0.1. No reinstalar GPT ni MCP para este cambio. Mantener KUCOIN_MCP_URL configurada en la Web.

## Cambios

- Actualizar históricos se encuentra en Configuración → Estado de conexiones MCP → Históricos de mercado. Muestra la fuente y fecha del cierre cargado, con horario de Lima. Ya no aparece en la cabecera global; Actualizar Spot permanece en la cabecera.
- La carga histórica sigue siendo una acción manual e independiente de Spot: velas 1D cerradas Binance, reutilizadas durante el mismo día UTC. Frecuencia sugerida: una vez al día después de las 19:00 de Lima. No actualiza pivotes publicados ni saldos u órdenes.
- La tarjeta KuCoin muestra su configuración, cobertura de 12 tokens, fuente, observación de mercado y última comprobación exitosa. Su MCP actual sólo ofrece Spot: esta entrega no incorpora históricos KuCoin.
- Cada tarjeta consulta exclusivamente su MCP y respeta las pausas. Binance no puede aparecer conectado por reutilizar un snapshot KuCoin. Las respuestas Spot requieren identidad de fuente, cobertura completa y frescura válida.
- Refrescar conexión sólo comprueba al proveedor indicado; no inicia una valoración ni cambia el snapshot del portafolio.
- El diagnóstico integral incluye Google Sheets, Binance, KuCoin e Hyperliquid. Para Portafolio, Balancer y Ventas acepta Binance o KuCoin como dependencia Spot. No sustituye Binance por KuCoin para indicadores, BSI o análisis histórico. Es evaluación de dependencias, no certificación funcional de cada módulo.
- Conserva Forecast3.0.35 con anclas CL/O1 publicadas y pivotes protegidos, Spot rápido e históricos separados.

## Validación y límites

219 pruebas Web aprobadas, incluyendo diagnóstico KuCoin, cobertura/frescura, rechazo de fuente incorrecta, pausa Binance con respaldo disponible, rutas GET/POST, independencia del snapshot y ubicación del botón. Sintaxis JavaScript, plantillas Jinja y /health verificados localmente. No se completó prueba visual en navegador porque el entorno no tiene un ejecutable Chromium instalado. Despliegue y consultas reales a los proveedores no verificados en esta entrega. MASTER y automatizaciones sin cambios; sin órdenes enviadas.

## Comprobación tras desplegar

1. Confirmar /health3.0.36 y consistencia de assets.
2. Abrir Configuración → Estado de conexiones MCP; deben aparecer las tres tarjetas y la sección Históricos de mercado.
3. Verificar KuCoin: debe mostrar su propia fuente y 12/12 precios vigentes. Una pausa de Binance debe aparecer en Binance aunque KuCoin funcione.
4. Usar Actualizar históricos sólo cuando se necesite el nuevo cierre UTC. El botón no mueve el Spot ni publica pivotes. Ante RATE_LIMIT, respetar la pausa del proveedor; no repetir intentos continuos.
5. La barra global debe conservar Actualizar Spot sin Actualizar históricos.
