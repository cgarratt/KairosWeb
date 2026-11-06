# KairosWeb v4.6.6 · Guardado de tolerancia

Corrige Campo duplicado al guardar por primera vez DRIFT_BAND_RELATIVE_PCT. La inicialización del parámetro encolaba valor y evidencia, y la fase final los encolaba otra vez. Ahora cada celda se escribe una sola vez, con el porcentaje solicitado y la justificación administrativa.

Se conserva el rechazo de entradas duplicadas, la validación 0–100%, lectura del snapshot, conciliación y publicación auditada existentes. Incluye la corrección /health de v4.6.5. No modifica MASTER durante estas pruebas ni requiere cambios de GPT/MCP.

Validación local: 43 pruebas aprobadas, incluidas creación, edición, duplicados, valores fuera de rango y salud del release. Las pruebas de guardado usan datos sintéticos y sustituyen validaciones externas; no acreditan una escritura remota.

## Despliegue

Descomprimir, reemplazar archivos del repositorio KairosWeb y desplegar en Render. Mantener /health. Confirmar versión 4.6.6, recargar Configuración y volver a guardar la tolerancia deseada con su justificación. Verificar el valor publicado tras guardar. Despliegue y escritura remotos pendientes.
