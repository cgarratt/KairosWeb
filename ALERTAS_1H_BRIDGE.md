# Integración pendiente de la tarea ChatGPT Alerta 1H

La tarea de ChatGPT no transmite resultados automáticamente a servicios Render. Se mantiene la recepción autenticada `POST /api/notifications/ingest` con `X-Kairos-Token` y deduplicación por ID.

Para completar el flujo se requiere un emisor externo autorizado (por ejemplo, automatización que tenga acceso real al resultado de cada corrida) o implementar un motor horario propio en Render. Nunca generar alertas ficticias ni inferirlas del último precio.

Configurar `KAIROS_ALERTS_INGEST_TOKEN` en Render y almacenar las notificaciones en DB persistente para evitar pérdida tras reinicios.
La ruta `/api/notifications/bridge-status` devuelve `AWAITING_EXTERNAL_SENDER` hasta que exista una integración de envío.
