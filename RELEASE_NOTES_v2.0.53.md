# KairosWeb v2.0.53 — Capturas en Órdenes

- Solo acciones **Confirmar** y **Ejecutada** sobre recomendaciones O2/O4/O3/O5.
- Captura PNG/JPG/WEBP (5 MB máximo), extracción opcional con `OPENAI_API_KEY` y revisión humana obligatoria.
- Sin clave de extracción, ingreso manual disponible; no se simula reconocimiento.
- Registro de ejecución directa con tres eventos atómicos: propuesta, confirmación, ejecución.
- No envía órdenes ni modifica inventario, USDT, fills ni custodia.
- El archivo no se guarda en Sheets; se registra su SHA256 como referencia, sin almacenamiento de la imagen.
- Despliegue y prueba integral en Render pendientes.
