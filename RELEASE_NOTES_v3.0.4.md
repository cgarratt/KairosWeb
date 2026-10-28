# KairosWeb 3.0.4 · Renovación automática de Spot

Cuando el Spot en memoria supera 180 segundos (o tiene una fecha futura fuera de tolerancia), se consulta el MCP nuevamente antes de calcular el reporte. Una falla de consulta nunca habilita cotizaciones vencidas como respaldo. Se conserva el botón Actualizar Spot.

El mensaje heredado «Spot vencido» se identifica como STALE_DATA en lugar de MCP_ERROR. Este defecto local es reproducible; no se han consultado los logs de Render para certificar la causa del incidente 2b45b140b4 de la captura.

Incluye la corrección Balancer PUMP/PUMPFUN de 3.0.3. Compatible con KairosGPT 1.3.12; sin cambios en MASTER.

Validación: 292 pruebas Python y 8 subpruebas. Cubre renovación de caché vencida/futura, falla sin respaldo vencido y rechazo de respuesta MCP antigua. Datos sintéticos; despliegue remoto no verificado.

Descomprimir y subir el contenido al repositorio existente. Desplegar en Render y comprobar versión 3.0.4 en /health. Abrir Compras después de más de 3 minutos. Si falla, consultar Diagnóstico MCP y logs mediante el ID mostrado.
