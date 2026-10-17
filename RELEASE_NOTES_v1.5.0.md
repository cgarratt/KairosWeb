# KairosWeb v1.5.0 — Notas de liberación

**Ámbito:** KairosWeb (Render/GitHub). No modifica KairosGPT ni crea/ejecuta órdenes. **Fuente:** `KAIROS_V5_MASTER` nativo Google Sheets, esquema `5.0.0`, y MCP Binance/Hyperliquid.

## Cambios incluidos (mejoras 23–25)

### 23. Configuración de parámetros ordenada e individual

- La opción del menú lateral se llama **Parámetros** y presenta estos grupos: Portafolio, Liquidez y Balancer, Compras O2, Ventas O3, Compras O4, Ventas O5, Trading QF, Indicadores y BSI, Alertas. El diagnóstico MCP sigue separado.
- Las distribuciones Fibonacci de **Forecast O2/O3/O4/O5** ahora tienen **16 claves numéricas independientes** en el contrato (`4 × 4`), con etiquetas en porcentaje; se evita guardar los cuatro valores en un solo texto.
- Los valores iniciales son O2 **0/60/40/0**, O3 **40/30/20/10**, O4 **0/60/40/0** y O5 **20/20/30/30**. Las compras de O2/O4 siguen limitadas a **25% de P por onda**, no al 25% del USDT disponible.
- **Una edición aprobada** materializa los cuatro campos completos de esa onda en `12_PARAMETROS_KAIROS`, de modo atómico con historial y auditoría. Hasta entonces son defaults virtuales; **el despliegue no escribe en Sheets**.
- Si existen claves antiguas `FORECAST_O*_FIB_ALLOCATION`, se leen únicamente como referencia de compatibilidad cuando no existan claves individuales; nunca se suman como un segundo presupuesto. `O5_STAGED_TRANCHES` queda como referencia histórica no editable; no se confunde con los cuatro tramos simulados de O5.
- Validación por onda: cuatro tramos numéricos **0–100%**, suma exactamente **100%**. No se publican estados incompletos ni parciales. Se mantiene el flujo administrativo validado y registrado.

Claves individuales exactas (formato `FORECAST_<ONDA>_FIB_<NIVEL>_PCT`):

| Onda | Sufijos de los cuatro niveles |
|---|---|
| O2 / O4 (compras) | `382`, `500`, `618`, `786` |
| O3 / O5 (ventas) | `1618`, `2618`, `3618`, `4618` |

**Distinción esencial:** los presupuestos operativos `C1_BAG_FRACTION_P=15%P` y `C2_BAG_FRACTION_P=10%P` siguen independientes y NO se agregan otra vez al presupuesto de Forecast. Las reglas O3 y O5 operativas, la protección de HODL/Core, BTC NEVER SELL y el reparto O5 30/70 no se modifican en este release.

### 24. O1 candidato con máximo semanal posterior a CL

- En **Configuración → Pivotes preliminares**, tras mostrar el archivo MCP existente, las O1 faltantes se consultan automáticamente con una ruta simplificada **`/api/settings/pivots/preliminary?o1_only=1&token=BTC`**.
- La consulta utiliza **Binance Spot 1D cerrado** y el Cycle Low candidato archivado; reconstruye solo **semanas UTC completas (lunes–domingo)** y muestra el mayor HIGH posterior a la semana del CL. Evita depender para O1 del escáner H4 5L/5R, que devuelve vacíos cuando no existe certificación estructural.
- Ejemplo MCP verificado el 17/10/2026: BTC CL candidato `57,800.19` (01/07/2026), O1 observada **`87,395.67 USDT`** en la semana del 21/09/2026 (**PRELIMINAR**, sin 5L/5R/BOS ni Elliott certificados).
- Para HYPE se respetan exclusivamente datos históricos **Hyperliquid Spot HYPE/USDC**. Para SUI/PUMP no se inventa la fecha de sus CL seleccionados ni se rescata el mínimo flash-crash excluido; si falta esa fecha, O1 permanece pendiente y se muestra la causa.
- Las ediciones manuales y O1 preliminares previamente visualizadas se preservan ante respuestas parciales. No se publican ni certifican automáticamente.

### 25. Menú Configuración

La opción **«Reglas y ventas O3/O5»** pasa a llamarse **«Parámetros»**, situada inmediatamente **encima de «Estado de conexiones MCP»**. Se conserva el resto del menú.

## Controles y pruebas

- Google Sheets `PUBLICADO` obligatorio; sin snapshot válido → `DATA ERROR`, nunca fallback a JSON, ZIP o capturas históricas.
- BSI SELL **BLOQUEADO**, TradingBot **WATCH** hasta homologaciones obligatorias.
- Compras/ventas/O3/O5 y Forecast siguen siendo simulaciones o propuestas sin órdenes automáticas.
- Pruebas realizadas localmente: **105 tests Python**, **3 suites JS**, **navegador Chromium de Settings, Forecast y Pivotes**. Verificar los resultados en Render tras despliegue.
- **Limitación:** el entorno de construcción no dispone de Flask/FastMCP/Google Auth instalados para un ensayo completo de la aplicación servida; las pruebas locales de funciones y UI pasaron, pero la consulta real de Render aún debe validarse.

## Pasos de despliegue

1. Descomprimir el ZIP y subir **su contenido** a la **raíz** del repositorio KairosWeb; commit en la rama usada por Render.
2. Conservar las variables de entorno actuales, incluidos `KAIROS_GOOGLE_SHEET_ID`, las credenciales Google, las URLs MCP y las claves de sesión administrativa. **No se requieren nuevas variables**.
3. Esperar a Render y comprobar `/health` → `version: 1.5.0`, `/api/sheets-status` → `status: OK`.
4. Abrir `/settings?tab=parameters` y verificar 16 campos individuales, distribución 100% por onda y menú.
5. Abrir `/settings?tab=pivots`: BTC debe calcular O1 preliminar con fecha posterior al CL, con latencia sujeta al MCP. Si falla, se conserva el archivo y se muestra aviso. **No guardar los pivotes oficiales hasta revisión humana**.
6. Abrir `/mode/forecast` y modificar controles solo como simulación; verificar continuidad de las tablas O2–O5.
7. Para una prueba de guardado real de parámetros, utilizar autenticación administrativa y una distribución que pase las validaciones; confirmación explícita requerida, auditoría en `18_SETTINGS_AUDITORIA` y nueva revisión en `10_HISTORIAL`. No utilizar inventario real para pruebas arbitrarias.

**Estado:** paquete v1.5.0 preparado; no desplegado ni verificado en producción en esta conversación.
