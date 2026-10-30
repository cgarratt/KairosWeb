# KairosWeb v3.0.22 — Indicador junto al objetivo

Se mueve únicamente el indicador desde USD al precio objetivo Fibo. USD queda solo como importe. Se conservan title/aria-label, leyenda inferior y claves numéricas de ordenación para precio, peso, USD y total. Sin cambio de cálculos, estados o MASTER.

Verificación: sintaxis del JavaScript de la plantilla y ubicación del indicador/claves numéricas. Sin prueba visual ni despliegue remoto.

## Antecedente UI v3.0.21 (ubicación del indicador sustituida por v3.0.22)

# KairosWeb v3.0.21 — Tabla Fibo e importes ordenables

USD por escalón muestra solo importe e indicador; se retira el texto visible PROPUESTA/EJECUTADA/NO APLICA. Se mantiene el estado/motivo en title y aria-label. Debajo se añade leyenda compacta de indicadores, distinta del fondo de celda por peso post-compra.

Ordenación de USD, Total USD, precios y pesos usa data-sort-value con el valor numérico original. No analiza símbolos, comas, porcentajes ni texto del estado. Conserva precisión interna, compara números en ambos sentidos, mantiene0 como importe válido y N/D como vacío. No cambia la asignación, clasificación, umbral, ventas condicionadas ni pivotes5L/5R.

Verificado:11 comprobaciones de valores/orden ascendente/descendente; sintaxis del sorter y del JavaScript embebido de la plantilla. No se repitió la suite completa ni prueba visual en navegador. No se modificó MASTER. Pendiente de desplegar. Compatible con GPT1.3.13 y el parche de liquidez de v3.0.20.
