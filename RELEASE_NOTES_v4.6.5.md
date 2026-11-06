# KairosWeb v4.6.5 · Corrección health Render

Se reprodujo /health HTTP 503 con el paquete v4.6.4 completo: tres marcadores obsoletos en _deployed_asset_status no coincidían con la lógica vigente. Afectaban venue_buy_orders, buy_postweight_color_ui y sales_optimizer_engine.

Se actualizan los marcadores a las firmas actuales de asignación por venue, semáforo con tolerancia relativa y optimizador de ventas. Se conserva la verificación estricta de archivos presentes y marcadores. No se cambia la lógica financiera, MCP, MASTER ni órdenes. Metadatos de compatibilidad GPT: 1.3.22.

Validación local: 38 pruebas aprobadas (36 heredadas y 2 de regresión health). /health 200 con paquete completo; 503 ante archivo faltante o contenido obsoleto. No acredita diagnóstico de proveedores externos ni despliegue remoto.

## Despliegue

Descomprimir el ZIP y reemplazar los archivos del repositorio KairosWeb. Confirmar el commit y desplegar en Render. Conservar Health Check Path /health. No requiere cambios de variables de entorno, MCP ni KairosGPT. Tras el despliegue, abrir /health: version 4.6.5, status UP, release_assets.consistent true.

Si continúa el 503, compartir el JSON de /health para identificar qué archivo difiere del paquete.
