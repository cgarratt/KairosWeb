# KairosWeb v1.2.0 — Release consolidado

**Alcance:** release completo basado en v1.1.0 RC2.1, incluyendo el hotfix de autenticación administrativa y las mejoras pendientes de presentación (RC3), además de la corrección de carga de pivotes históricos MCP.

## Cambios

1. **Precarga al abrir Pivotes preliminares:** consulta directa, de solo lectura, de `07_PIVOTES!A21:Q33` del `KAIROS_V5_MASTER`, que contiene los 12 candidatos archivados provenientes de Binance MCP y Hyperliquid MCP. El archivo se identifica **HISTORICO_MCP_EN_GOOGLE_SHEETS**, nunca como cotización en tiempo real.
2. **Actualización MCP por token:** botón **Actualizar candidatos desde MCP**. KairosWeb consulta por separado Binance Spot `get_kairos_cycle_phase` (11 tokens) y Hyperliquid Spot HYPE/USDC `get_hype_spot_ohlcv` (HYPE). Sólo 2 consultas simultáneas; muestra progreso, éxitos y errores por token. Una respuesta lenta o fallida no bloquea las otras ni elimina los candidatos históricos disponibles.
3. **Pivotes no certificados:** se distinguen Cycle High, Cycle Low, O1/O2/O3 y ausencias de O4/O5. Se conserva el mínimo SUI seleccionado 0.6359 en lugar de 0.5597, y el candidato PUMP 0.001151 en lugar del mínimo bruto 0.000411. Para HYPE, O3 observado 97.885 USDC todavía carece de 5R: es **candidato**, no onda confirmada. No se crean órdenes; **Guardar cambios** conserva `PENDIENTE_CERTIFICACION`.
4. **No sobrescribir correcciones del usuario:** al precargar/actualizar se preservan los campos oficiales ya presentes en Google Sheets y cualquier campo editado manualmente durante la sesión.
5. **Contraste oscuro transversal:** textos de gráficos, importes a la derecha de barras, encabezados, celdas fijas, tablas de Forecast, subfilas de ondas, totales y tablas anidadas reciben colores de alto contraste.
6. **Inversión remanente (USDT):** interfaz de Maestro de unidades con 2 decimales. El monto **original de Google Sheets mantiene todos sus decimales si no fue editado explícitamente**, aunque se modifiquen otras columnas; al editar la inversión se admiten hasta 2 decimales. Se conserva el costo medio calculado = inversión remanente / unidades totales.
7. **Conservado del hotfix RC2.1:** acceso administrativo con CSRF y verificación de origen, sin desactivar la protección de escrituras.
8. **Conservadas funcionalidades previas:** campana de Alertas Kairos, lectura masiva, Guardar cambios auditado, modo Claro/Oscuro, Settings, Forecast y menú global.

## Seguridad / datos

- **Sin modificar ni escribir en Google Sheets en esta entrega.** Sólo se leyó `07_PIVOTES` para cotejar el contrato.
- Todas las propuestas de pivotes son `EXPLORATORY_ONLY`, requieren confirmación humana estructural (5L/5R y BOS), y no habilitan órdenes LIMIT.
- No hay snapshots JSON antiguos de respaldo. Si falla la lectura de posiciones/parameters `PUBLICADO`, el sitio debe seguir mostrando `DATA ERROR`.
- Ninguna operación ni transferencia se ejecuta desde este desarrollo.
- El permiso de escritura de Settings sigue sujeto a sesión administrativa y auditoría.

## Despliegue

Sube el **contenido descomprimido** del ZIP a la raíz del repositorio de GitHub y haz commit. Verifica en Render que el último deploy esté activo. No subas el ZIP sin descomprimir y no introduzcas credenciales en GitHub.

1. `/health`: `version: "1.2.0"`.
2. `/api/sheets-status`: `status: OK`; último snapshot `PUBLICADO`.
3. `/settings` → **Pivotes preliminares**: 12 filas precargadas desde el histórico MCP en Sheets, con información de procedencia y advertencias.
4. Botón **Actualizar candidatos desde MCP**: progreso hasta `12/12`; errores identificados por token, sin perder los valores archivados.
5. `/api/settings/pivots/preliminary`: archivo histórico, sin ejecución MCP remota de gran volumen.
6. `/api/settings/pivots/preliminary?token=BTC`: exploración fresca de BTC solamente, `certified: false`.
7. En la web, tema oscuro: revisar **Dashboard / Forecast / Compras / Ventas** y filas de totales.
8. Maestro de unidades: inversión con 2 decimales y costo medio automático.

### Limitaciones conocidas

- El scanner Binance del MCP sólo ofrece candidatos exploratorios; su resultado no equivale a certificación Elliott. HYPE exige BOS semanal adicional y revisión humana.
- La navegación avanzada y motores financieros se mantienen con las restricciones KairosGPT actuales: BSI SELL bloqueado, TradingBot WATCH.
- Pruebas automatizadas locales y simulación Chromium **no sustituyen pruebas con Render, credenciales y MCP reales**. No se ha desplegado esta versión.
