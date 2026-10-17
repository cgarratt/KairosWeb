# KairosWeb v1.8.0 — Forecast balanceado y vista privada

Fecha de preparación: 17/10/2026 (America/Lima). Release completo basado en v1.7.0. Fuente de datos: Google Sheets nativo KAIROS_V5_MASTER con schema 5.0.0, Binance MCP y Hyperliquid MCP conforme al contrato existente.

## Cambios acumulados

1. **Motor Forecast O2→O5**: O3 prioriza tokens sobreponderados con disponibilidad Exchange; O4 recalcula infraponderaciones tras ventas O3 y compras BTC hipotéticas, y usa el presupuesto y caja elegibles por tramo. O5 mantiene liquidación de cierre y no fuerza balance al target de una cartera en acumulación. Mostrar pesos, target y desviaciones pp por onda. Sin órdenes/fills/transfers reales; no se modifica el Master.
2. **O3/O5**: los repartos BTC / USDT se consultan **por separado** de los parámetros APROBADOS del Master. Se valida suma igual a 100%. No existe conversión automática; las dos etapas de SELL ALT y BUY BTC se simulan por separado. Si falta lectura o aprobación, no inventar porcentajes.
3. **Mejora 36 — precisión**: precio Spot, costo medio y precios Fibonacci con hasta cinco decimales sin cambiar precisión de cálculos. Precios entre cero y US$0.00001 se presentan como `<0.00001`; importes USDT se presentan con dos decimales. Valor BTC conserva ocho.
4. **Mejora 37 — Pivotes**: formularios de Configuración muestran solo Cycle Low, O1, O2, O3, O4, O5. Las antiguas referencias O2C2/O2C3 siguen en 07_PIVOTES como evidencia histórica y no se borran ni certifican.
5. **Mejora 38 — Tabla ejecutiva**: `Token | Estado | Unidades | Peso | Target | Precio Spot | Valor USDT | Valor BTC | Precio Medio | Rentabilidad`. P&L porcentual no realizado contra costo medio del Master; N/D si falta costo. BTC NEVER SELL sin cambios.
6. **Mejora 39 — privacidad**: botón de ojo en encabezado de todas las pantallas; arranca oculto, oculta importes y unidades como `*****` también tras actualizaciones dinámicas, conserva porcentajes y precio Spot público. Preferencia visible solo durante la pestaña del navegador vía sessionStorage; en una nueva pestaña inicia oculto. Es una protección de **presentación** y **no** oculta datos de API, DOM o red a usuarios con acceso técnico. No sustituye autenticación.
7. **Mejora 40 — Compras**: solo cuatro tarjetas de importe O2C1–O2C4, manteniendo el algoritmo de balanceo y distribución proporcional internamente.
8. **Mejora 41 — Ventas**: Candidatos SELL se coloca inmediatamente después de los gráficos de distribución y liquidez post-escenario, sin modificar los importes simulados.

## Restricciones mantenidas

- BTC NEVER SELL, HODL protegido, ventas O3 sujetas a Exchange libre, Core elegible solo bajo políticas aprobadas; reserva QF contada una vez.
- No se certifican pivotes históricos, BSI SELL bloqueado hasta homologación, TradingBot en WATCH sin verificación Quantfury.
- Forecast exclusivamente local, no guarda cambios en Master; ediciones en Configuración siguen siendo operaciones administrativas separadas con validación y auditoría.
- Esta distribución de archivos no cambia nada en GitHub, Render ni Google Sheets por sí sola.

## Regresión en entorno local (offline)

- 124 pruebas Python y 3 subtests; pruebas JavaScript puras (Forecast balances, niveles, segmentos, Settings format).
- Chromium: privacidad y actualizaciones dinámicas, tabla ejecutiva, Pivotes, Settings, Forecast O2→O5 y splits independientes.
- El precio Spot en vivo, permisos de Google service account y funcionamiento real de Render/MCP se validan **después de desplegar**; las pruebas sintéticas no los certifican.

## Despliegue sugerido

1. Sustituir contenido del repositorio `cgarratt/KairosWeb` por el contenido del ZIP (excepto secretos locales y configuraciones de Render de entorno).
2. Commit/push y Deploy latest commit en Render; verificar `/health` devuelve versión `1.8.0`.
3. Comprobar `/api/sheets-status` y las conexiones MCP; revisar errores o cambios de contrato sin sustituir datos con snapshots antiguos.
4. Probar el icono del ojo en todas las vistas y el comportamiento de cada pestaña de Forecast con datos reales solo en lectura.
