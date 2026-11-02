# KairosWeb 3.0.38 · Tendencia BTC con históricos explícitos

## Instalación

Extraer el ZIP y reemplazar el contenido del repositorio Web existente. Mantener variables y secretos, desplegar en Render y recargar. /health debe indicar version=3.0.38, component_versions.KairosWeb=3.0.38 y release_assets.consistent=true. Contiene 99 archivos. Compatible con GPT1.3.17 y MCP Binance5.4.1, KuCoin1.0.1 e Hyperliquid1.0.1; no reinstalarlos.

## Problema y corrección

Tendencia BTC todavía dependía de una precarga antigua de 210 velas y de una caché distinta del snapshot histórico explícito. Esa ventana podía no cubrir el CL publicado. Cuando la API devolvía N/D o fallaba, la interfaz ignoraba la respuesta y mantenía Consultando BTC semanal / Esperando pivotes.

Ahora el régimen y las velas usan el historial completo BTCUSDT:1d del snapshot cargado mediante Actualizar históricos. No se consulta mercado al navegar ni en un hilo de precarga. Se utilizan sólo semanas lunes-domingo UTC cerradas y al menos 21 consecutivas, incluido el último cierre semanal. La gráfica sigue iniciando en la semana del CL publicado y conserva los pivotes estrictos 5L/5R; no se generan pivotes por falta de datos.

La interfaz realiza una lectura de estado, con timeout 15s y sin sondeo repetitivo. Ante N/D, error HTTP o red, muestra el motivo y ofrece Gestionar históricos hacia Configuración → Estado de conexiones MCP. Si hay régimen calculable pero falta CL, muestra el régimen y explica por qué no puede dibujar la gráfica.

## Requisito operativo

Actualizar Spot no descarga velas. El gráfico requiere una carga histórica Binance válida al último cierre diario UTC. Si Binance sigue bloqueado y no hay esa carga, no se dibujará: se mostrará la causa. KuCoin todavía respalda únicamente Spot; esta entrega no cambia la fuente histórica ni implementa históricos KuCoin. No reintentar repetidamente durante RATE_LIMIT.

## Validación

234 pruebas Web aprobadas. Incluyen serie desde CL anterior a 210 días, falta de carga, datos vencidos, fuente incorrecta, semanas con huecos, ausencia deCL, respuesta N/D y fallos HTTP/red del navegador simulado. Conserva las pruebas de pivotes BTC 5L/5R y diagnóstico MCP independiente del MASTER. /health y todas las plantillas Jinja verificados localmente. Sin prueba visual en navegador ni validación del despliegue remoto. No se consultó mercado para estas pruebas.

No modifica MASTER, saldos, órdenes, custodia ni automatizaciones. Conserva todas las correcciones de 3.0.37 y anteriores.

## Comprobación después de desplegar

1. Confirmar /health 3.0.38 y consistencia de archivos.
2. Si falta histórico vigente: esperar a que Binance permita consultas y usar Configuración → Estado de conexiones MCP → Actualizar históricos.
3. Volver a Portafolio. Con CL e históricos suficientes, se muestran velas desde CL, régimen y los pivotes 5L/5R disponibles. Menos de tres pivotes no impide dibujar las velas.
4. Sin histórico vigente debe aparecer una explicación y Gestionar históricos, sin quedarse Consultando indefinidamente.
