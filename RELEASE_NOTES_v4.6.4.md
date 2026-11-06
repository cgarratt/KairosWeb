# KairosWeb 4.6.4


## Tolerancia relativa y despliegue de caja · revisión aprobada 05/11/2026
- Sustituye DRIFT_BAND_PP para clasificar composición por DRIFT_BAND_RELATIVE_PCT (número 0..100; ingresar 10 = 10%). Si todavía no existe, este release utiliza 10 por instrucción explícita del usuario y muestra su origen; no convierte ni reinterpreta el pp legado. Configuración Guardar crea/publica la nueva fila con auditoría y snapshot; GET no escribe.
- Desviación relativa = 100 × (peso actual/peso objetivo − 1). INFRA < −10%, SOBRE > +10%, límites inclusivos NEUTRAL. Para objetivo cero, posición positiva SOBRE; sin posición NEUTRAL. Mantener pp para medir exposición e informar ambas métricas.
- Compras conserva elegibilidad, estados, QF y caja por venue. Distribuye simultáneamente entre INFRA, proporcional a sus déficits proyectados y con techo en peso objetivo después de incorporar TODAS las compras del tramo. No priorizar por mayor drift.
- El 100% del presupuesto seleccionado es el objetivo de despliegue; cuota no usada se arrastra hacia tramos posteriores con peso aprobado positivo, nunca a una orden confirmada ni a otra moneda/venue sin fondos. Mantener sin asignar cualquier importe incompatible con déficits, estructura, estados o liquidez real; no forzar sobreponderación.
- UI Compras omite la tabla de caja inicial/final por venue. Conserva resumen global de presupuesto, asignado y sin asignar con causa. Auditoría interna conserva los saldos por venue.
- Propuestas/simulaciones únicamente. Este ZIP no despliega Render ni publica el MASTER por sí mismo.
