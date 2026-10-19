# KairosWeb v2.0.18 — Release completo para GitHub

**Versión aplicación:** `2.0.18` · **Schema Google Sheets:** `5.0.0` sin cambios · **Fuente de datos operativos:** Google Sheets ORIGINAL PUBLICADO y MCP Spot; nunca ZIP, capturas ni archivos locales como balances o precios.

## Novedad desde v2.0.17 — Semáforo de peso post-compra

En **Compras → Maestro de Precios - Retrocesos Fibo**, el fondo de cada grupo de tres celdas (Precio Fib, % Peso, USDT) se activa **únicamente si ese token recibe al menos un centavo de USDT en la compra simulada del tramo**:

- **Verde:** desviación del peso cripto **post-compra** frente a su objetivo `>= 0 pp` (alcanza o supera target).
- **Ámbar:** `-1 pp <= desviación < 0 pp` (ligeramente bajo target).
- **Rojo:** `desviación < -1 pp` (aún bajo target por más de 1 punto porcentual).
- **Sin color:** asignación que se muestra como USDT `$0.00`, N/D, tramo no comprable o valoración no disponible.

La desviación se calcula en **puntos porcentuales**: `100 × (peso post-compra en fracción − target en fracción)`. La clasificación cromática **NO utiliza más** el mínimo histórico post-P2; no cambia la disponibilidad de pivotes P1/P2 ni sus semáforos de estado. Mover el slider y aplicar porcentajes C1–C4 vuelve a calcular colores, pesos y compras.

## Funciones conservadas

- Slider `0–100%` del USDT físico disponible **menos reserva QF una sola vez**; cupos máximos en O2C1→O2C4 con waterfall secuencial.
- Porcentajes C1–C4 editables y aplicables sólo cuando suman exactamente 100%; restaurar porcentajes desde el Master sin escribir sobre él.
- Compras **sólo INFRA**, máximo déficit/target por token, reevaluación por tramo; caja no asignada permanece en USDT.
- Órdenes fase 1: backlog, filtro de Nivel, importes de compra y unidades venta cuando existe base aprobada; sin ejecución remota.
- Forecast protege pivotes VALIDADO/CONFIRMADO; Ventas ordinarias no filtra por pivotes; BTC NEVER SELL y custodia HODL/Core protegida.

## Instalación y verificación

1. Descomprimir el contenido del ZIP en el repositorio GitHub, conservando las rutas. Hacer commit y desplegar en Render. No subir secretos.
2. Visitar `/health`, verificar `version: 2.0.18`, `status: UP`, `release_assets.consistent: true` y controles `buy_postweight_semaphore`, `buy_postweight_color_ui`.
3. En Compras, probar slider `0%, 50%, 100%`; verificar que las compras de `USDT $0.00` no tengan color, y que sólo las que reciben USDT se iluminen en Precio/% Peso/USDT según su desviación **post-compra** (pp).
4. Verificar que P1/P2 siguen mostrando estados, editor C1–C4 sigue respondiendo y Ventas/Forecast/Órdenes no cambian inesperadamente.
5. Para HYPE verificar conectividad independiente con Hyperliquid Spot HYPE/USDC en Render. Los tests locales no certifican endpoints de producción.

**Seguridad:** no se publican pivotes ni cambia el Master desde este ZIP; sin fills ni órdenes reales. El release tiene menos de 100 archivos e incluye manifiesto de integridad SHA-256.
