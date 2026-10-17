# Alertas Kairos (1H) — lectura desde Sheets

15_ALERTAS_RUNS determina si una corrida es 1H; 16_ALERTAS_EVENTOS contiene fecha UTC, token, acción literal, tipo y certificación; 17_ALERTAS_LECTURAS es append-only. El botón «Marcar todas como leídas» escribe únicamente las IDs 1H pendientes en un solo lote idempotente; no borra eventos, no crea órdenes ni notificaciones push, no interpreta WATCH como entrada ejecutable. Fecha visual: America/Lima.
