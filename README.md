# KairosWeb v2.0.58

Entrega para GitHub por navegador: menos de100archivos. Ver RELEASE_NOTES_v2.0.58.md.

# KairosWeb v2.0.57 · Topes de reservas

Ver RELEASE_NOTES_v2.0.57.md. Los topes de Balancer y Trading se editan en Configuración → Parámetros. Se recalculan con cada valoración Spot; cambiar porcentajes no necesita otro deploy una vez instalado este release.

# KairosWeb v2.0.56 — Spot snapshot on first use; manual refresh in header.
# KairosWeb v2.0.37 — Logout seguro corregido

**Cambio focalizado:** el cierre de sesión HTML valida el CSRF del formulario y redirige a invitado con HTTP 303. Se mantiene CSRF administrativo y la lectura privada protegida. Consultar `RELEASE_NOTES_v2.0.37.md`.

# KairosWeb v2.0.35 — Distribución actual del capital

**Aplicación:** `2.0.35` · **Google Sheets schema:** `5.0.0` · **Motor KairosGPT compatible:** v1.3.6.

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
3. Comprobar `/health`: `service=KairosWeb`, `version=2.0.35`, `status=UP`, `release_assets.consistent=true` y checks `sales_optimizer_engine`, `sales_optimizer_ui`, `portfolio_unrealized_chart`.
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


## Release v2.0.35 · Donut de capital actual (Spot)

- **Portafolio, primer donut:** reemplaza “Composición del capital histórico” por **“Distribución actual del capital”**, calculada exclusivamente de `02_POSICIONES` y `03_LIQUIDEZ` del último snapshot `PUBLICADO` con cotizaciones Binance Spot MCP vigentes.
- **Cuatro componentes sin solapamiento:** (1) HODL + Core (unidades × Spot), (2) Exchange (unidades × Spot), (3) Liquidez operativa (USDT físico menos Quantfury), (4) ReservaTrading QF real. Pérdidas realizadas y objetivos de `08_INTEGRAL` no se suman ni sustituyen saldos presentes.
- El donut utiliza **el mismo patrimonio total** que “Allocation por token (incluye USDT)”. Una prueba explícita rechaza discrepancias de totales, unidades por custodia, precios incompletos o QF fuera del USDT físico. Con DATA ERROR la vista indica N/D en vez de mostrar histórico obsoleto.
- La leyenda incluye USDT y porcentajes actuales; se conserva el segundo donut de 13 componentes, P&L, BSI archivado, Ventas y el resto de módulos. Sin movimientos reales ni edición del MASTER.
- Nueva verificación `/health`: `current_capital_donut_v2035`. La comprobación HTTP real de Render requiere desplegar el ZIP.


## v2.0.36 · Acceso con privacidad por servidor
- `KAIROS_WEB_USER` y `KAIROS_WEB_PASSWORD` autentican sesión de portafolio; `KAIROS_SESSION_SECRET` firma cookie HttpOnly/Secure/SameSite=Strict.
- Sin sesión: navegación de invitado con marcadores ocultos; `/api/portfolio`, alertas, MCP y demás endpoints de datos se bloquean con 401 (no basta privacidad JS).
- Configuración mantiene una SEGUNDA clave (`KAIROS_SETTINGS_ADMIN_KEY`), sesión administrativa y CSRF.
- Portafolio usa título único “Portafolio”.
- Error `UPSTREAM_HTTP`: se origina en el proveedor remoto; revisar logs Render con ID y diagnóstico MCP autenticado. No se reutilizan cotizaciones antiguas.

## Release v2.0.38 · Sesión recordada (Portafolio)

- En `/login`, la casilla **Mantener sesión iniciada en este dispositivo (30 días de inactividad)** aparece marcada inicialmente; puede desmarcarse en equipos compartidos. Con la casilla activa se crea una cookie de sesión firmada, `Secure`, `HttpOnly`, `SameSite=Strict`, con vencimiento renovable de 30 días por inactividad. Las visitas regulares renuevan la cookie sin solicitar usuario y contraseña. Con la casilla desmarcada la cookie es de sesión del navegador y, por política del servidor, caduca tras 12 horas sin actividad.
- El cierre de sesión por POST `/logout` elimina los permisos de usuario y de administrador, incluso si se había elegido recordar el acceso. Un cambio de credenciales de usuario o administrador invalida el nivel correspondiente de las sesiones anteriores.
- Configuración mantiene una **segunda autenticación administrativa de 30 minutos**, que no se prolonga por navegar Portafolio. La autorización administrativa no vuelve persistente una sesión de usuario marcada como temporal.
- **Requisito de Render:** conservar `KAIROS_SESSION_SECRET` sin cambios entre despliegues y réplicas; regenerarlo cierra todas las sesiones existentes. Configurar `KAIROS_WEB_USER`, `KAIROS_WEB_PASSWORD` y `KAIROS_SETTINGS_ADMIN_KEY` solo como variables secretas de entorno, nunca en GitHub o el ZIP. En navegación privada, navegadores que eliminan cookies o al cambiar de dispositivo se necesitará iniciar sesión de nuevo.
- Las sesiones del navegador son cookies firmadas, no contraseñas guardadas. **No registra ni modifica información del MASTER**, no altera permisos de invitado ni autorización de escritura.
- Tests locales: pruebas de caducidad por inactividad, renovación, login temporal, autorización administrativa independiente, rotación de contraseña, CSRF y logout; ver `RELEASE_NOTES_v2.0.38.md`. La prueba HTTP en Render se realiza después del despliegue.

## v2.0.39 · Objetivos de gestión unificados

Abrir Configuración → **Objetivos de gestión**. El editor concentra objetivos globales Cripto/Liquidez, por Tier, por subreserva y por custodia, sin mostrar tres formularios separados. Seis validaciones al 100%, objetivo derivado para los 12 tokens y previsualización contable antes de publicar. Dos confirmaciones administrativas obligatorias; publicación multihoja con auditoría, snapshot y homologación. Unidades, USDT físico y QF no se modifican.

**Diferencias de origen importantes:** `STRUCTURAL_USDT_TARGET` / `BALANCER_RESERVE_FORMULA` mantienen su régimen operativo hasta una revisión explícita; los nuevos porcentajes de reservas son de planificación. Si no se ha publicado la mezcla de liquidez, 70/20/10 es un borrador de la imagen, no una lectura del MASTER. La custodia inicial de cada Tier viene del MASTER publicado, aunque difiera de la imagen ilustrativa.

El botón de publicación requiere administración vigente, CSRF, preview, confirmación y snapshot sin conflictos. Ver `RELEASE_NOTES_v2.0.39.md`. No hay cambios de credenciales ni despliegue automático.

## v2.0.40 · Gestión USDT: Compras vs Balancer

- `liquidity_reserves.py` concentra los presupuestos de los dos modos y la exclusión QF. **Compras O2/O4** dispone de todo USDT operativo no comprometido, gastando primero la bolsa semanal y después, si hace falta, la asignación Balancer. **Balancer** solo consume su asignación explícitamente publicada y el ingreso *condicional* de sus propias ventas simuladas; los proceeds no se cuentan como efectivo real antes del fill. Nunca se suma QF por segunda vez.
- La nueva asignación `BALANCER_RESERVE_ASSIGNED_USDT` es un monto en USDT, NO un porcentaje y NO una transferencia; se publica mediante Configuración → Objetivos de gestión, con autorización administrativa y límite igual al USDT operativo físico. Si el campo falta o figura PENDIENTE, el presupuesto BUY actual de Balancer es USDT 0, no se infiere del mix objetivo, ni se transfiere caja semanal. El motor antiguo (25% P) deja de dimensionar Balancer en esta versión.
- Las ventas del Balancer solo aumentan presupuesto ejecutable tras registro de fills reales y conciliación del efectivo en el MASTER; los escenarios de ventas simuladas siguen identificados como *condicionales*. La aplicación no registra fills ni mueve dinero automáticamente.
- Los porcentajes de liquidez de Configuración permanecen **objetivos de planificación**; la asignación en USDT es el gate operativo de Balancer. No modificar balances físicos para intentar alcanzar objetivos.
- Antes de habilitar el flujo en producción, el MASTER debe publicar la política actualizada. Ningún lanzamiento de código modifica automáticamente su 01_CONTROL o los parámetros de Google Sheets.


## v2.0.41 · Reserva Balancer automática (20% de USDT físico) + modo oscuro

- Los porcentajes APROBADOS en `12_PARAMETROS_KAIROS` (`PORTFOLIO_LIQ_USDT_FRACTION`, `PORTFOLIO_LIQ_BALANCER_FRACTION`, `PORTFOLIO_LIQ_TRADING_FRACTION`) suman 100% y gobiernan las reservas virtuales. `BALANCER_RESERVE_ASSIGNED_USDT` es una fórmula de lectura que recalcula **USDT físico × participación Balancer**, no una entrada manual.
- El saldo total incluye QF exactamente una vez. La asignación se rechaza si invade los USDT de QF; Balancer no consume USDT semanal; Compras O2/O4 puede extenderse hasta la reserva disponible de Balancer. Los proceeds no acreditados siguen solo en escenarios condicionales.
- En Configuración → Objetivos de gestión se muestra el importe derivado, sin un segundo campo manual, con validación en vivo. Los fondos se recalculan al variar la liquidez publicada o la mezcla aprobada.
- Estilos `data-theme=dark` dedicados a tarjetas de objetivos, textos y formularios; en modo claro se conserva la presentación anterior.
- Validar despliegue de Render y saldos del MASTER después de instalar. No se ejecutan órdenes, fills ni transferencias.

## v2.0.42 · Hotfix conciliación de fills agregados en Google Sheets

- Mantiene la publicación del MASTER y la exigencia de 12 tokens/100% targets/QF una sola vez.
- El lector `google_sheets_master.py` admite evidencia **agregada por orden** de una compra ya completada, cuando el exchange no ha proporcionado Trade IDs individuales o la captura no permite certificar zona horaria UTC. Requiere orden `FILLED/COMPLETED` explícitamente conciliada con una fila `06_FILLS`, clave única de procedencia `VENUE|ORDER_ID|ORDER_AGGREGATE_NO_TRADE_IDS`, fuente verificable en ambas hojas, coincidencia de token/lado/cantidad y neteo de fee en token.
- Es evidencia de recepción agregada, **no un Trade ID ni un timestamp inventado**, y **no suma de nuevo las unidades o USDT al snapshot**. Duplicados, fondos sin evidencia, mezcla agregados+trades, órdenes abiertas o reservas sin conciliar siguen bloqueadas.
- Si persiste `DATA ERROR`, Portafolio mostrará la categoría segura (`ORDERS_FILLS_RECONCILIATION_REQUIRED`, `GOOGLE_SHEETS_HTTP_403`, etc.) y el ID de incidente. La causa detallada queda en logs de Render, sin divulgar secretos.
- Instalación: desplegar el ZIP descomprimido, comprobar `/health` versión `2.0.42` y después consultar Portafolio/Balancer con el MASTER vigente. Ninguna operación real se ha realizado desde este hotfix.

## v2.0.43 · Órdenes — seguimiento de estados con evidencia

- Gestión administrativa **Propuesta → Confirmada → Parcial / Ejecutada** en `/mode/ordenes`.
- Primera escritura autorizada crea `26_ORDENES_GESTION` en el MASTER, sin modificar el inventario. Se preserva historial append-only y cada transición requiere revisión de versión para evitar sobrescrituras silenciosas.
- Se registran **unidades previstas y ejecutadas**, importe de USDT/USDC, comisiones, ID del exchange y evidencia. Los fills históricos de `05_ORDENES` / `06_FILLS` se preservan; no deben registrarse de nuevo.
- Confirmada = declarada como colocada, pero sin fill acreditado; Ejecutada = evidencia declarada **pendiente de conciliación contable**, sin crédito automático de saldo. La validación del MASTER reserva capacidad para evitar reutilizar los presupuestos pendientes y mantiene QF protegida.
- Requiere identidad lectora y editora Google; solo administradores pueden registrar cambios de estado; el resto de usuarios autenticados pueden revisar.
- `/health` debe informar `2.0.43` y consistencia del paquete. No ofrece ni presume envío, cancelación ni sincronización real con exchanges.


## v2.0.44 · Hotfix órdenes abiertas
Permite órdenes pendientes documentadas en 05_ORDENES con reserva de USDT/unidades, conteo conciliado y referencias locales cuando no se dispone de Exchange Order ID. No acredita fills ni altera saldos.


## v2.0.45 · Hotfix HYPE pending quote-only
See RELEASE_NOTES_v2.0.45.md.

## v2.0.46 · Conciliación USDC por venue y gráfico Forecast ampliado
Ver RELEASE_NOTES_v2.0.46.md.


## Rendimiento de Compras y Forecast (v2.0.51)
Las series diarias MCP se cachean en memoria por día UTC y parámetros; el botón Actualizar Spot invalida la caché histórica. La primera consulta histórica sigue siendo necesaria.

## v2.0.51
TradingBot retirado de navegación y API deshabilitada; Compras presenta disponibilidad libre separada de techo bruto no QF. Las órdenes declaradas canceladas deben conciliarse en MASTER, nunca borrarse.

## Capturas de órdenes
Para extracción opcional, configurar `OPENAI_API_KEY` en Render (no incluir en GitHub). Sin clave, el registro manual permanece disponible. La captura se envía al servicio de visión solo tras pulsar «Extraer». Se guarda referencia SHA256, no la imagen.
