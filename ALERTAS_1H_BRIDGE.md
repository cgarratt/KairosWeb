# Alertas 1H · Lectura directa desde Google Sheets

KairosWeb ya no utiliza el puente POST `/api/notifications/ingest`, ni un inbox SQLite que pudiera perder datos al reiniciar Render. La campana lee `15_ALERTAS_RUNS` y `16_ALERTAS_EVENTOS` en el Master, y filtra exclusivamente corridas con `marco=1H`. Los acuses de lectura viven en `17_ALERTAS_LECTURAS`, sin borrar eventos.

Cada evento conserva `creado_utc` y muestra hora en `America/Lima`, token, estado, certificación y **acción_sugerida textual**. No se inventan órdenes ni señales READY. Para marcar leído se requiere `KAIROS_GOOGLE_WRITER_JSON` con permiso Editor en el archivo (separado de la identidad Lector). Si falta se permite consultar el histórico no leído, pero no acusar recibo.
