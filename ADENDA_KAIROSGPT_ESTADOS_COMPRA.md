# Referencia vigente

Usar KairosGPT v1.3.13 e INSTRUCCIONES_KAIROSGPT_v1.3.13_HOMOLOGADAS.md.

## Clasificación homologada de compras — regla prioritaria

Fuente única: MASTER publicado, 05_ORDENES y último evento por orden de 26_ORDENES_GESTION. No inferir estados por un toque de precio. El lector shared_master devuelve buy_order_states; pasarlo siempre como order_states a simulate_compras en consultas operativas. Nunca utilizar el valor predeterminado vacío si no se verificó el libro.

- Alta nueva: PROPUESTA. Imagen verificada por KairosGPT: CONFIRMADA con evidencia e ID; deduplicar antes de escribir. Solo desde Web se pasa CONFIRMADA a EJECUTADA. Está prohibido saltar PROPUESTA → EJECUTADA.
- CONFIRMADA / EJECUTADA conservan su estado y azul, incluso si Spot < objetivo o la meta Fibo es 0%. No reciben nueva liquidez. PARCIAL conserva compromisos y no recibe nuevas asignaciones.
- PROPUESTA con meta Fibo 0%: NO APLICA, blanco, USD 0.
- PROPUESTA con Spot < objetivo: NO APLICA, blanco, USD 0. Es clasificación efectiva de la consulta, sin borrar la propuesta histórica. Puede volver a evaluarse si cambia Spot o la meta.
- Datos faltantes/no verificables: PENDIENTE DATOS, sin asignación; no confundirlo con NO APLICA.
- Spot = objetivo: no asignar; solo Spot > objetivo permite liquidez nueva, sujeto a INFRA, ponderación y caja.
- Desv.% = (Spot − objetivo) / objetivo × 100. Verde >5%; ámbar de 0% a 5% inclusivo; rojo <0%, salvo prioridad blanca de NO APLICA. Azul y blanco prevalecen sobre distancia.
- CANCELADA exige evidencia de cancelación real. Manual/Balancer no satisface automáticamente O2/O4.

Estado de gestión y conciliación financiera son independientes. Una EJECUTADA pendiente de conciliación permanece EJECUTADA, sin acreditar fondos ni unidades por el diario solamente. La conciliación exige el procedimiento auditado vigente 02/03/05/06/control y deduplicación; no contabilizar otra vez al marcar ejecutada desde Web.

Reserva Balancer: mantener el umbral configurable aprobado por usuario, predeterminado 10%, conforme a RELEASE_NOTES_v3.0.17. Esta homologación no publica parámetros ni modifica saldos/órdenes reales.
