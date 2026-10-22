# KairosWeb v2.0.34 — Objetivos de Liquidez y ReservaTrading

**Aplicación:** `2.0.34` · **Google Sheets schema:** `5.0.0` · **Motor KairosGPT compatible:** v1.3.6.

## Novedades acumuladas sobre KairosWeb v2.0.18

1. **Ventas ordinarias (2 etapas)**: primera etapa vende tokens SOBRE de forma secuencial; segunda etapa minimiza la suma de desviaciones cuadráticas entre pesos cripto finales y targets al distribuir el faltante de USDT. No confundir con Ventas O3/O5.
2. **Objetivo dinámico USDT**: `Kairos Ventas` usa 40% por defecto en el Master `ORDINARY_DEFAULT_USDT_TARGET`; `/mode/ventas?usdt_pct=55` o el deslizador permiten un porcentaje explícito de 0% a 100%, sin modificar el default. Meta no alcanzable = mostrar faltante y `CAPACITY_LIMITED`.
3. **Restricciones duras**: BTC NEVER SELL; Exchange libre y órdenes SELL reservadas; límites acumulados T1 30% / T2 70% / T3 100%; HODL/Core protegidos; QF contado una sola vez. No hay creación/cancelación de órdenes, ni fills supuestos ni transferencias.
4. **UI**: lista de ventas ordenadas con fase, unidades y USDT, y detalles de cada orden con pesos antes/objetivo/después; se elimina la tabla de 12 tokens redundante. El selector de porcentaje funciona independientemente de los sliders de Compras.
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
3. Comprobar `/health`: `service=KairosWeb`, `version=2.0.34`, `status=UP`, `release_assets.consistent=true` y checks `sales_optimizer_engine`, `sales_optimizer_ui`, `portfolio_unrealized_chart`.
4. Abrir `/mode/ventas` y `/mode/ventas?usdt_pct=55`; comprobar el porcentaje solicitado, prioridades y el comparativo. Confirmar que no hay órdenes reales creadas.
5. Confirmar `/mode/portafolio` y el gráfico de resultado no realizado; verificar Compras, Forecast, Pivotes y Órdenes fase 1.

## Verificación local

- `python -m pytest -q` sobre el release extraído.
- `node tests/test_sales_optimizer.js` y tests JS adicionales incluidos.
- `SHA256SUMS.txt` / `RELEASE_MANIFEST_v2.0.33.json` permiten comprobar integridad de archivos del ZIP, excluyendo sus propios metadatos.

**Límite:** menos de 100 archivos; se omiten algunos tests de regresión antiguos del paquete distribuible para mantener ese límite (pero se ejecutaron en el checkout completo). Los fuentes de aplicación y assets no se han eliminado.

## Balancer 2.0.20 · Custodia

Tabla actual/ideal/factible de unidades HODL, Core y Exchange más propuestas manuales Exchange→HODL/Core. Sin transfers automáticos.


## Release 2.0.21 · Hotfix compatibilidad Balancer

Incluye el módulo de custodia 2.0.20 y corrige el renderizado de Balancer cuando clientes o pruebas entregan payloads anteriores sin `custody_comparison`. El panel de custodia solo se muestra cuando hay datos conciliados; el resto de Balancer permanece disponible. No ejecuta transferencias ni modifica el MASTER.


## Release 2.0.22 · Nuevo layout de Portafolio

- Cuatro filas tras los KPI: (1) capital histórico / allocation 13 componentes, (2) rentabilidad histórica / PnL no realizado por token, (3) categoría T1–T3 / composición 12 tokens, (4) seguimiento del portafolio.
- Gráficos actuales consumen el MASTER PUBLICADO y MCP Spot. El panel BSI usa solo una muestra 4H archivada en `09_BSI` como referencia; no representa señales de venta certificadas.
- Comparación histórica de valor no equivale a rentabilidad real ajustada por depósitos/retiros; PnL histórico N/D sin serie de costos de cada fecha.
- Ver `RELEASE_NOTES_v2.0.22.md`, `/health` (marcadores `portfolio_layout_v2022`, `portfolio_allocation_v2022`) y `/mode/portafolio`.


## Hotfix 2.0.23 · MODE_RENDER Balancer
- Corrige incompatibilidad entre el formato real de `04_CUSTODIA` validado por `google_sheets_master` (lista `[HODL, Core, Exchange]`) y el comparador que antes requería un diccionario.
- Nueva regresión usa la forma real retornada por `parse_master`; acepta también mapeos con nombres; datos malformados siguen bloqueados.
- Los gráficos históricos de Portafolio siguen mostrando **Historial insuficiente** cuando el MASTER no incluye 2+ observaciones completas; no hay seguimiento de rentabilidad certificada en el MASTER actual. Se requiere captura periódica verificable y registro de flujos; no se fabrican puntos.
- El hotfix no modifica Google Sheets ni ejecuta operaciones.

## Release 2.0.25 · Cartera retrospectiva y diagnóstico de Órdenes

- La curva de rentabilidad retrospectiva y su endpoint `/api/portfolio-repricing` fueron **retirados** de Portafolio por petición del usuario; no se disparan consultas 1D para esa vista.
- `/mode/portafolio` ya no genera curvas históricas. La segunda fila muestra BSI 4H archivado y resultado no realizado por token.
- `/mode/ordenes` mantiene independiente el Balancer ordinario del filtro 1W de Compras. Si falla solo la estructura semanal, los niveles de compra quedan N/D y los cálculos de Balance pueden continuar como **propuestas no ejecutables**. Si faltan Sheets válidos, 12 precios Spot o la valoración Balancer, muestra `DATA ERROR` y la etapa/ID diagnóstico; no usa inventarios del ZIP.
- `/health`: version `2.0.30`, chequeos de integridad para el nuevo motor e interfaz.
- No se ejecutan, cancelan, envían o simulan fills de órdenes. No se actualiza el MASTER.

### Validación de esta entrega
- Regresión completa Python: **172 aprobadas, 2 omitidas**.
- 9 archivos de suites JS: **OK**.
- `py_compile` y validación sintáctica de plantillas Jinja: **OK**.
- **Regresión Flask completa / HTTP real / Render:** pendiente. Este entorno no dispone de Flask/FastMCP instalados ni permite su instalación remota. No confundir con release desplegado.


## Dashboard + Portafolio consolidados (2.0.25)

Una sola vista `/mode/portafolio` accesible desde `/` (redirección). Valor total en USDT y equivalente BTC Spot `total_usdt/BTCUSDT`, sin agregar la reserva QF dos veces. La segunda fila muestra gráfico BSI archivado y P&L por token. La tabla ejecutiva muestra los 12 tokens, custodias, valoraciones BTC y estado INFRA/NEUTRAL/SOBRE. BSI sigue siendo solo una referencia histórica NO SELL; el presupuesto O2C2 sigue correspondiendo al modo Compras. Sin órdenes, fills ni cambios al Master.


## Release 2.0.26 (heredado) · Cálculos y controles consistentes

- **Balancer BUY:** asignación INFRA únicamente, recalculando el denominador de la manga cripto. Límite final del déficit por token, con USDT sobrante sin gastar. El escenario con ventas también se recalcula desde un inventario post-venta **hipotético**, sin acreditar fills ni caja real.
- **Balancer SELL + Órdenes:** cálculo compartido de unidades máximas: `min(Exchange − reserva SELL, unidades_totales × fracción Tier − reserva SELL)`, T1=30%, T2=70%, T3=100%. BTC nunca se vende. Se prioriza SOBRE y se reevalúan pesos después de cada venta hipotética.
- **Reserva SELL:** el MASTER actualmente declara cero órdenes abiertas y su lector falla cerrado si aparecen órdenes operativas no reconciliadas. No implica que el exchange remoto esté verificado; no se crean reservas ficticias de propuestas.
- **Semáforos:** clasificación centralizada ±`DRIFT_BAND_PP` del MASTER (hoy 0.5 pp), límites inclusivos NEUTRAL.
- **TradingBot:** solo los 5 tokens T1 del parámetro `TRADINGBOT.UNIVERSE` APROBADO. Si falta o difiere, DATA ERROR; Quantfury continúa WATCH.
- **Regresión:** tests de borde, reservas SELL, conciliación BUY por déficit, y paridad numérica JavaScript/Python para la etapa SOBRE. Ninguna operación real.
- El registro de histórico, la arquitectura de servicios y diagnósticos de dependencias en vivo permanecen en backlog v2.0.27–29.


## Release 2.0.27 · Presentación Portafolio

- Fila 2 izquierda: BSI histórico 4H archivado en 09_BSI, solo informativo; jamás se presenta como señal SELL activa.
- Fila 4: nueva columna INFRA / NEUTRAL / SOBRE basada en la desviación frente al objetivo y la banda dinámica `DRIFT_BAND_PP` del MASTER.
- Identificadores visuales al lado de tokens en tabla, allocation, P&L, BSI y comparación; imagen externa opcional con fallback local permanente.
- Retiradas las dos secciones colapsables inferiores BSI y composición histórica por segmentos. El donut histórico de primera fila se mantiene.
- Conserva valorización total en USDT y BTC, simulaciones de trading y protección de custodia.
- No cambia posiciones, parámetros ni órdenes del MASTER.


## Release 2.0.28 · Custodia compacta Opción B

La sección 7 de Balancer presenta una fila por token con transferencias desde Exchange a HODL/Core, cantidades exactas por destino y una barra de porcentajes **post-movimiento**. Los tokens sin transferencias están en un desplegable secundario; se retira la tabla anterior de 36 filas. La simulación es de solo lectura y no altera posiciones ni reglas. Ver `RELEASE_NOTES_v2.0.28.md`.


## Release 2.0.29 · Ventas y línea Spot en trayectoria

- **Ventas:** retirar exclusivamente la segunda tabla “Pesos antes / objetivo / después (12 tokens)”. La tabla priorizada de SELL, el cálculo del optimizador, los estados y los importes siguen intactos.
- **Forecast:** dibujar una línea horizontal punteada con el Spot MCP vigente del token seleccionado y su precio. Incluir Spot en la escala vertical; actualizar al cambiar token y al ajustar etapas. Si falta Spot, mostrar N/D y omitir la línea, sin inventar cotización.
- La línea es referencia informativa sobre un eje de etapas hipotéticas; **no es una onda, pivote ni señal**.
- `/health` incorpora el marcador `forecast_spot_overlay_v2029` y deja de exigir la tabla eliminada.
- Paquete local pendiente de despliegue. Master, órdenes y custodia sin cambios. Ver `RELEASE_NOTES_v2.0.31.md`.


## Release v2.0.30 · Diagnóstico y procedencia B05–B08

- `/health`: servidor y hashes locales sin consulta remota; último diagnóstico de dependencias en caché, con marca de hora y estado explícito `NOT_CHECKED` si aún no se ha ejecutado.
- `Configuración → Estado de conexiones MCP → Ejecutar diagnóstico integral`: visualiza servidor, proveedores y estado de dependencia de los módulos. La consulta requiere autenticación HTTP Basic existente.
- `/api/health/diagnostics`: **autenticado**. Comprobación read-only de Sheets, Binance y Hyperliquid y mapa de módulos por dependencias. No es homologación de orden real ni prueba funcional end-to-end.
- Portafolio muestra error estructurado y no reutiliza datos parciales cuando falla el MCP o el cálculo.
- `13_CONTROL_HOMOLOGACION` se contrasta con `01_CONTROL` y `03_LIQUIDEZ` para detectar referencias históricas stale, sin alterar el MASTER.
- Capital histórico `08_INTEGRAL` muestra procedencia y referencia de corte; no se confunde con patrimonio Spot.
- El release empaquetado es candidato listo para GitHub; la verificación HTTP en Render sigue pendiente. Ver `RELEASE_NOTES_v2.0.31.md`.


## Release v2.0.31 · Homologación contable automática

- Nueva hoja `25_HOMOLOGACION_HISTORIAL` (creación automática en primera publicación/autorización administrativa). No sobrescribe `13_CONTROL_HOMOLOGACION`.
- Las publicaciones desde Configuración registran en un único batch el nuevo snapshot y su homologación base validada.
- Para el snapshot vigente previo al despliegue, Configuración → Estado de conexiones MCP → **Homologar snapshot actual**. Se requiere sesión admin, CSRF y editor Google.
- Sólo se certifican inventario (12 tokens), targets, custodias y QF/USDT; pivotes, BSI SELL y órdenes remotas siguen pendientes.
- Los nuevos snapshots publicados por otro cliente de Google Sheets quedan STALE hasta una revalidación explícita.
- `RELEASE_NOTES_v2.0.31.md` detalla pruebas, seguridad y procedimiento de actualización.


## Release v2.0.32 · Presentación allocation y Ventas Balancer

- **Portafolio:** la leyenda de allocation contiene USDT en fila independiente y los otros 12 tokens en dos grupos de **seis por columna** en escritorio, sin barra de desplazamiento vertical. En móvil estrecho, se apilan los dos grupos para mantener legibilidad. Todos los 13 componentes permanecen presentes en el donut y suman el patrimonio total sin duplicar QF.
- **Balancer → 4. Candidatos de venta:** nueva columna `Unidades estimadas`; presenta las unidades ya calculadas por el motor compartido `overweight_sell_plan` (USDT venta / Spot MCP), limitadas a Exchange libre, reservas SELL y cupos Tier. No calcula ventas adicionales ni cambia balances.
- **Precisión:** hasta 8 decimales referenciales; sin ajuste a LOT_SIZE, comisiones o pasos de cantidad de cada venue. **Propuesta, no orden**.
- Ver `RELEASE_NOTES_v2.0.32.md`. `GET /health` debe indicar `2.0.32` y `release_assets.consistent=true`; controles de versión mixtos `allocation_legend_v2032` y `balancer_sell_units_v2032`.
- No se despliega automáticamente ni se modifican saldos, configuración MASTER, órdenes o custodias.


## Release v2.0.33 · Homologación fiable y UI de unidades

- **Balancer (candidatos de venta):** cabecera `Unidades`, siempre dos decimales en visualización (`17,857.39`). Los valores exactos del motor (`r.units`) siguen intactos; no cambia volumen sugerido ni cálculo USDT, Exchange, Tier o QF.
- **Configuración → Estado de conexiones MCP:** botón de solo lectura `Consultar estado de homologación` para ver si existe `25_HOMOLOGACION_HISTORIAL` y si su última evidencia corresponde al snapshot actual. `Homologar snapshot actual` crea la pestaña y anexa la primera fila en un único batch Google Sheets, **únicamente después de confirmación administrativa**. No escribe desde GET ni al abrir Portafolio.
- **Diagnósticos por fase:** `HOM_WRITER_MISSING`, `HOM_WRITER_FORBIDDEN`, `HOM_MASTER_NOT_FOUND`, `HOM_WRITE_REQUEST_INVALID`, `HOM_VALIDATION_FAILED`, `HOM_WRITE_UNVERIFIED`, `HOM_PUBLICATION_UNVERIFIED`, entre otros. `phase` identifica READ / METADATA / VALIDATION / WRITE / POST_WRITE_READ / POST_WRITE_CHECK; nunca se expone la clave de servicio.
- **Publicación protegida:** una nueva publicación desde Configuración sigue anexando homologación contable en la misma transacción. La API distingue errores de escritura de certificación no visible. Si el servidor **pudo escribir pero no verificar**, **no reintentar ciegamente**: comprobar `01_CONTROL` y hoja `25` para no duplicar registros.
- **Certificación solo contable:** 12 tokens, targets 100%, custodia, QF y USDT; no acredita pivotes, BSI SELL, órdenes, fills ni saldos remotos.
- Si el aviso STALE continúa, el Administrador deberá inspeccionar el código de fallo y realizar la primera homologación verificada; desplegar el código **no altera** el MASTER por sí mismo.
- `/health` debe declarar `version=2.0.34` y `release_assets.consistent=true`; los nuevos marcadores son `balancer_sell_units_v2033` y `homologation_diagnostics_v2033`.
- Ver `RELEASE_NOTES_v2.0.33.md` para límites de prueba, instalación y validación.

## Release v2.0.34 · Editar objetivos de Liquidez y ReservaTrading

- Configuración incorpora la pestaña **Objetivos de liquidez y ReservaTrading (%)**. Edita los cuatro segmentos objetivo de `08_INTEGRAL`: Liquidez, Trading (ReservaTrading), HODL + Core, Exchange. El conjunto debe sumar **100% del capital histórico de referencia**. Ningún porcentaje se ajusta automáticamente.
- `08_INTEGRAL` tiene `Objetivo %` como **fórmula** `=Bxx/$B$5`. Para conservarla, el backend escribe **solo la columna B (Objetivo USDT)** para los segmentos modificados; preserva C/E (registrado histórico), D/F (fórmulas y notas), el segmento Lost y el total con fórmula.
- El formulario calcula una previsualización monetaria de cada porcentaje. **No cambia USDT físico ni ReservaTrading Quantfury**; estos se editan como USDT en `Liquidez por venue` solo ante balances reales conciliados.
- La política operativa `STRUCTURAL_USDT_TARGET` (por defecto publicado 40%) **es un parámetro independiente**, ya editable en Configuración → Parámetros → Portafolio. Cambiar porcentajes históricos de `08_INTEGRAL` no modifica Balancer ni Ventas.
- Cada cambio requiere sesión admin, evidencia/justificación, `expected_snapshot_id`, una nueva publicación Google Sheets atómica, entrada de auditoría y certificado contable del snapshot. No se generan órdenes ni transferencias.
- No se modificó el MASTER real durante la creación del ZIP. Los nuevos porcentajes deben ser indicados y publicados por el administrador.
