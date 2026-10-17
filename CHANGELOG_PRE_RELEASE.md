# Cambios de KairosWeb v1.0.0 — candidato actualizado antes de liberación

- Removida página/botón Modos Kairos, menú global derivado de listado de modos habilitados.
- Campana de Alertas 1H históricas no leídas desde Google Sheets, timestamp Lima, token/acción/estado, acuse persistente.
- Nueva página Configuración para unidades/costos, objetivos/Tiers, distribución de custodia, liquidez, parámetros O3/O5 y pivotes pendientes.
- Acceso editor separado + contraseña admin + comprobación origen + vista previa HMAC + publicación versionada + auditoría campo a campo.
- `O5` ahora usa fracciones aprobadas desde Google Sheets, sin constante 30/70 en el lector; la regla publicada actual continúa 30/70.
- Se mantienen las restricciones de BSI SELL, TradingBot WATCH, cero fills inferidos y ausencia de JSON locales.
