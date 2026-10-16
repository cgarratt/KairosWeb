# Kairos Web v4.0.2 — estabilidad de conexión MCP

Parche sobre v4.0.1. Sin cambios de política de portafolio ni de interfaz.

- Registra en Render `http_status` HTTP real para errores httpx.HTTPStatusError, incluso anidados en ExceptionGroup.
- Los logs contienen solo ID, proveedor, tipo y código HTTP; nunca URL/token/cabeceras/trazas con secretos.
- `/api/mcp-diagnostics` devuelve `diagnostic.http_status` cuando está disponible.
- Una sola petición de mercado en vuelo por proceso. Caché de 30 segundos con `observed_at` original; no ofrece cotizaciones caducadas como LIVE.
- Gunicorn pasa a 1 worker y 8 threads para compartir caché en el plan Free.

## Instalación
Copiar contenido de esta carpeta a la raíz del repo KairosWeb; commit/push a main. Mantener variables de entorno de Render. Después probar `/api/mcp-diagnostics`, `/api/portfolio`, `/mode/balancer`, `/mode/compras` y `/mode/ventas`.

## Nota
Un 502/503/504 de Render o del MCP necesita revisión operativa del servicio remoto; el parche registra el HTTP exacto y no promete resolver errores upstream.

## Ajuste v4.0.3 — Reserva Balancer

- Reserva Balancer actual = max(0, USDT físico consolidado − 25% P − Reserva Trading QF).
- No se aplica mínimo de liquidez 40% ni techo 5% P al cálculo de esa reserva.
- Reserva con ventas sugeridas = reserva actual + ventas brutas sugeridas (escenario hipotético).
- El piso 40% permanece como indicador aparte, sin restringir este cálculo.
- Los montos siguen siendo referenciales hasta reconciliar LIMIT, reservas y comisiones.


## v4.0.4 Compras a dos etapas

- El slider mantiene máximo = (USDT consolidado − QF) / patrimonio.
- Etapa 1: aporte para corregir infraponderaciones; si alcanza, se diluyen sobrepesos SIN vender.
- Etapa 2: resto del presupuesto asignado proporcionalmente a los targets entre TODOS los tokens.
- Columna diferenciada por etapa y presupuestos C1/C2 estimados.
- No equivale a orden ejecutable; el límite de 40% sigue como aviso, no como techo del simulador.
- C1/C2 todavía sin anclas verificadas.

## v4.0.5 Ventas
- Slider inicia en porcentaje de USDT actual y termina en 40%; si ya supera 40%, inicia en 40% para mantener rango válido.
- Eliminada la tabla de inventario Tier/Custodia.
- Candidatos SELL incluyen peso actual, objetivo y peso post-venta sobre manga cripto tras descontar ventas del denominador.
- Sin ejecución automática, BTC NEVER SELL y unidades Exchange limitan ventas hipotéticas.


## v4.0.6 — Slider de Ventas

- Mínimo: porcentaje USDT actual del portafolio.
- Máximo: 70% USDT (o liquidez actual si supera 70%, para no invertir el rango).
- Valor inicial: 40% cuando el porcentaje actual sea menor, de lo contrario el actual.
- Recalcula propuestas SELL, unidades y pesos post-venta; BTC NEVER SELL, Exchange disponible y simulación sin ejecución.

## v4.0.7
- Totales C1, C2 y USDT al pie de Compras; total USDT al pie de Ventas.
- Ventas: slider liquidez actual–70%, inicia 40% si el saldo actual es inferior; 40% NO limita el cálculo.
- Ventas en dos etapas: primero sobreponderados; después restantes activos proporcionalmente al target, hasta el límite del inventario Exchange; BTC no se vende.
- C1/C2 siguen PENDIENTES porque las anclas aprobadas no están integradas al backend; NO se inventan precios.
- Sólo simulación: reservas SELL, comisiones y fills requieren reconciliación.

## v4.0.8
Balancer: eliminación exclusiva de la columna USDT ref. en candidatos de compra. Permanecen Reserva actual y Con ventas, sin alteraciones de cálculo.


## v4.0.9 — Filas de totales
- Se agrega un pie TOTAL USDT a las dos tablas de Balancer: compras (reserva actual y con ventas) y ventas.
- Compras C1/C2 y Ventas ya incluyen total USDT dinámico; se conservan.
- La tabla ejecutiva del Dashboard conserva su fila de patrimonio consolidado.
- No sumar porcentajes ni cantidades de tokens heterogéneos como si fueran USDT.


## v4.1.0 — Referencias O2 C1/C2
Se cargan niveles O2 de la tabla Kairos fechada 16/10/2026 en `data/o2_reference_levels.json` (10 tokens). PEPE y VIRTUAL N/D. Los niveles NO se recalculan en vivo ni se consideran órdenes ejecutables o pivotes nuevos. Revisar vigencia de anclas y reconciliación de órdenes antes de operar.


## v4.1.1 — Forecast centralizado (escenarios)
- Tabla de candidatos O2 trasladada desde Compras a `/mode/forecast`: precios 38.2%, C1 50%, C2 61.8%, 78.2%; ambos niveles de referencia llevan USDT $0.
- Tabla Cycle Low (S0) → O1 → O2 → O3 → O4 → O5 simulados desde las referencias de O2, con selectores de extensiones/retracciones. Los pivotes S0/O1 invertidos algebraicamente NO tienen certificación Elliott.
- Compras conserva sus sliders y totales, con enlace a la tabla de Forecast.

## v4.1.2 — Forecast por tramos
- Cuatro secciones independientes: O1→O2, O2→O3, O3→O4, O4→O5.
- Cada una: tabla para los 12 tokens con unidades, precios de ambos extremos, valorización USD de cada extremo, delta, y fila TOTAL CRIPTO / LIQUIDEZ USDT / TOTAL PATRIMONIO.
- Cada tabla acompañada por un gráfico SVG con tres líneas: cripto valorizado, USDT físico constante y patrimonio combinado, con interpolación lineal ilustrativa (sin fechas).
- Al modificar los controles Fibonacci se recalculan los cuatro tramos; los presupuestos Fib en la tabla O2 son simulaciones *independientes* y no alteran las tenencias usadas en la proyección.
- Supuesto explícito HOLD: unidades del snapshot inmóviles, USDT físico intacto, Reserva QF contada una vez, sin órdenes, fills, comisiones ni monetización O3/O5. No es Forecast oficial de acumulación de BTC.
- PEPE y VIRTUAL sin anclas muestran precios O1–O5 N/D; su contribución al portafolio se mantiene al Spot actual y se indica como hipótesis neutra, no como objetivo.
- Las fases se sincronizan artificialmente para comparabilidad: no son fechas reales ni eventos simultáneos de mercado. Los niveles O1/O2/O3/O4/O5 siguen siendo escenarios, sin confirmación semanal 5L/5R y BOS.
- Test unitario `node tests/test_forecast_segments.js` y prueba visual local del HTML pre-renderizado superados.


## v4.1.3 — Dashboard ejecutivo + limpieza Balancer
- Dashboard reorganizado: fila superior con Patrimonio, Cripto Valuado y Composición General.
- Liquidez USDT y Reserva Trading se movieron a la sección Gestión de liquidez, junto a Liquidez por Venue.
- Balancer: se retiró el bloque 'Cómo se forma la capacidad del Balancer' y la fila duplicada de KPIs marcada para eliminar.


## v4.1.4 — Modos activos
La página /modes y /api/modes solo muestran Balancer, Compras, Ventas, TradingBot y Forecast. Se ocultaron Alertas, Benchmark, Rotation y MonteCarlo del menú y se inhabilitó su acceso directo; su código no se borra para una fase futura.

## v4.1.5
- Dashboard con gráfico vertical por token, logos, KPI superiores y liquidez reagrupada.
- Balancer incluye barra de distribución USDT C1/C2/Balancer/Trading sin piso 40% como restricción.
- BSI sigue histórico informativo; no inventa series temporales.


## v4.1.6 — Dashboard compacto
- Los KPIs Patrimonio total, Cripto valuado, Liquidez USDT y Reserva Trading forman una cuadrícula 2 × 2.
- El pie de composición consolida T1, T2, T3 y USDT contra patrimonio total; no cuenta Reserva Trading dos veces.
- Se retiran los gráficos de Distribución por Tiers y Liquidez por Venue. BSI y la tabla ejecutiva permanecen.
- Se conserva el backend y los modos sin cambios de reglas.


## v4.1.7 — Top 5 Rentabilidad
- Panel junto a BSI, ranking por porcentaje P&L no realizado contra costo promedio verificado.
- Configurar costos en data/cost_basis_verified.json, clave prices, por token (p.ej. {"BTC": 50000.0}). No insertar estimaciones.
- La rentabilidad en USD se calcula sobre unidades actuales, NO P&L realizado histórico.
- Sin datos suficientes se muestra estado incompleto, nunca resultados inventados.


## v4.1.8 — Portafolio integral
- Nuevo modo Portafolio en `/modes` y `/mode/portafolio`.
- Referencia histórica separada de los saldos en vivo en `data/integral_portfolio_reference.json`.
- KPIs capital base/vivo, Lost realizado y recuperación; gráfico objetivo vs actual, composición y tabla con desviaciones.
- No altera datos MCP, snapshot operativo ni modos de trading.


## v4.1.9 — MCP Resilience
- Reintentos con nueva sesión MCP únicamente para HTTP 502/503/504 y timeouts; esperas 2, 5, 10 segundos, sin reintentos para 401/403/404.
- Tiempo por intento 35 segundos; consultar `/api/market-status` para saber la edad de la última lectura validada.
- Cache 30s compartida entre hilos en un único proceso Gunicorn; datos vencidos no se reutilizan para análisis ni se muestran como LIVE.
- `/mode/portafolio` continúa independiente del MCP, mostrando exclusivamente cifras históricas confirmadas.
- Se conservan las reglas de inversión y las demás páginas sin cambios.
- Para mayor disponibilidad, Render Free puede requerir un plan sin suspensión o una fuente de mercado siempre activa.

## v4.2.0 — Top 5 rentabilidad
Se incorporan 12 costos promedio declarados en captura del 16/10/2026, sin modificar saldos de unidades del snapshot ni las fuentes MCP. El indicador es P&L no realizado estimado y no incluye pérdidas realizadas del portafolio integral.


## v4.2.1 — Cambios consolidados
- Portafolio: capital inicial, capital vivo registrado, Spot opcional por custodia; montos sobre barras.
- Forecast: trayectoria al inicio, elimina cuatro tramos, tabla de dos filas por token (precio y unidades/valor).
- Selectores O2–O5 compartidos por tabla y gráfico, con cambios dinámicos.
- Menú global consistente para ocho destinos (dashboard, modos y seis modos activos).
- Sin ejecución de órdenes. Spot ausente -> N/D en Portafolio, conserva ledger histórico.
