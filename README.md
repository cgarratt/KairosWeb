# KairosWeb v2.0.22 — RELEASE PARA GITHUB / RENDER

**Aplicación:** `2.0.22` · **Google Sheets schema:** `5.0.0` · **Motor KairosGPT compatible:** v1.3.6.

## Novedades acumuladas sobre KairosWeb v2.0.18

1. **Ventas ordinarias (2 etapas)**: primera etapa vende tokens SOBRE de forma secuencial; segunda etapa minimiza la suma de desviaciones cuadráticas entre pesos cripto finales y targets al distribuir el faltante de USDT. No confundir con Ventas O3/O5.
2. **Objetivo dinámico USDT**: `Kairos Ventas` usa 40% por defecto en el Master `ORDINARY_DEFAULT_USDT_TARGET`; `/mode/ventas?usdt_pct=55` o el deslizador permiten un porcentaje explícito de 0% a 100%, sin modificar el default. Meta no alcanzable = mostrar faltante y `CAPACITY_LIMITED`.
3. **Restricciones duras**: BTC NEVER SELL; Exchange libre y órdenes SELL reservadas; límites acumulados T1 30% / T2 70% / T3 100%; HODL/Core protegidos; QF contado una sola vez. No hay creación/cancelación de órdenes, ni fills supuestos ni transferencias.
4. **UI**: lista de ventas ordenadas con fase, unidades y USDT, y tabla de los 12 tokens con peso antes / objetivo / después. El selector de porcentaje funciona independientemente de los sliders de Compras.
5. **Portafolio**: se libera el gráfico de resultado no realizado de la anterior DEV; usa unidades y costos del Master y precios del MCP, sin mezclar pérdidas realizadas históricas ni USDT.
6. **Se preserva v2.0.18**: semáforo de peso post-compra en Precio / %Peso / USDT Fibonacci, y módulos de Compras, Forecast, Pivotes, Alertas y Órdenes fase 1.

## Fuentes y gates

- Fuente única de saldos/custodia/parámetros: Google Sheets ORIGINAL `KAIROS_V5_MASTER`, ID `1_tG5FK_u0biVZm2iXaK6fJi1enBYJYLAG6txkpTgsy8`. Sólo snapshot `PUBLICADO`, schema 5.0.0. No usar ZIP/capturas para cotizaciones o inventario.
- Mercado: MCP Binance Spot (12 tokens); macro HYPE con Hyperliquid Spot HYPE/USDC. No sustituir precios faltantes.
- Ventas requiere `SALES_STAGE_1=SELL_SOBRE_EXCHANGE_FREE_FIRST` (APROBADO), `SALES_STAGE_2=SELL_REST_MINIMIZE_SQUARED_PP_DRIFT` (APROBADO_SIMULACION), `ORDINARY_DEFAULT_USDT_TARGET` (APROBADO) y `SLIDER_MAX_SIMULATED_USDT_TARGET` (APROBADO_SIMULACION).
- No se han alterado inventarios ni configuraciones del Master durante la **creación de este ZIP**.

## Publicar en GitHub / Render

1. Extraer el ZIP **en la raíz del repositorio de KairosWeb**; el contenido se encuentra en la raíz, no en un subdirectorio adicional. Reemplazar los archivos por estos manteniendo las variables de entorno existentes. **No añadir credenciales ni subir `.env`.**
2. Revisar diferencias, hacer commit y desplegar Render. Este ZIP no ejecuta git push, no crea un GitHub Release y no redepliega por sí mismo.
3. Comprobar `/health`: `service=KairosWeb`, `version=2.0.22`, `status=UP`, `release_assets.consistent=true` y checks `sales_optimizer_engine`, `sales_optimizer_ui`, `portfolio_unrealized_chart`.
4. Abrir `/mode/ventas` y `/mode/ventas?usdt_pct=55`; comprobar el porcentaje solicitado, prioridades y el comparativo. Confirmar que no hay órdenes reales creadas.
5. Confirmar `/mode/portafolio` y el gráfico de resultado no realizado; verificar Compras, Forecast, Pivotes y Órdenes fase 1.

## Verificación local

- `python -m pytest -q` sobre el release extraído.
- `node tests/test_sales_optimizer.js` y tests JS adicionales incluidos.
- `SHA256SUMS.txt` / `RELEASE_MANIFEST_v2.0.22.json` permiten comprobar integridad de archivos del ZIP, excluyendo sus propios metadatos.

**Límite:** menos de 100 archivos; se omiten algunos tests de regresión antiguos del paquete distribuible para mantener ese límite (pero se ejecutaron en el checkout completo). Los fuentes de aplicación y assets no se han eliminado.

## Balancer 2.0.20 · Custodia

Tabla actual/ideal/factible de unidades HODL, Core y Exchange más propuestas manuales Exchange→HODL/Core. Sin transfers automáticos.


## Release 2.0.21 · Hotfix compatibilidad Balancer

Incluye el módulo de custodia 2.0.20 y corrige el renderizado de Balancer cuando clientes o pruebas entregan payloads anteriores sin `custody_comparison`. El panel de custodia solo se muestra cuando hay datos conciliados; el resto de Balancer permanece disponible. No ejecuta transferencias ni modifica el MASTER.


## Release 2.0.22 · Nuevo layout de Portafolio

- Cuatro filas tras los KPI: (1) capital histórico / allocation 13 componentes, (2) rentabilidad histórica / PnL no realizado por token, (3) categoría T1–T3 / composición 12 tokens, (4) seguimiento del portafolio.
- Gráficos actuales consumen el MASTER PUBLICADO y MCP Spot; el histórico solo utiliza observaciones completas y verificables en `21_PRI_HISTORIAL`. Hasta que existan al menos dos observaciones completas, las curvas permanecen en **Historial insuficiente**. No se crean series sintéticas.
- Comparación histórica de valor no equivale a rentabilidad real ajustada por depósitos/retiros; PnL histórico N/D sin serie de costos de cada fecha.
- Ver `RELEASE_NOTES_v2.0.22.md`, `/health` (marcadores `portfolio_layout_v2022`, `portfolio_allocation_v2022`) y `/mode/portafolio`.
