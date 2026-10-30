# KairosWeb 3.0.23 — Pivotes MASTER prioritarios

Los pares publicados CL/O1, O2/O3 y O4/O5 se usan como P1/P2 para simular compras. Se conserva precio, fecha y estado del MASTER sin exigir coincidencia con MCP y sin mostrar discrepancias. Un par completo no requiere consultar históricos MCP. Si falta P2, MCP puede proponerlo conservando P1 publicado. No se modifican pivotes ni se ejecutan órdenes. Continúan las validaciones de cronología, precios positivos, P2>P1 y elegibilidad de órdenes/Spot/liquidez. No se elevan estados de pivotes.

SUI publicado: P1=0.6359 / P2=1.2938. Regla general para todos los tokens, sin excepciones por token.

Instalar reemplazando el código de GitHub y desplegar en Render. No cambia MASTER. Pendiente despliegue externo.

## Historial anterior

# KairosWeb v3.0.22 — Indicador junto al objetivo

Se mueve únicamente el indicador desde USD al precio objetivo Fibo. USD queda solo como importe. Se conservan title/aria-label, leyenda inferior y claves numéricas de ordenación para precio, peso, USD y total. Sin cambio de cálculos, estados o MASTER.

Verificación: sintaxis del JavaScript de la plantilla y ubicación del indicador/claves numéricas. Sin prueba visual ni despliegue remoto.

## Antecedente UI v3.0.21 (ubicación del indicador sustituida por v3.0.22)

# KairosWeb v3.0.21 — Tabla Fibo e importes ordenables

USD por escalón muestra solo importe e indicador; se retira el texto visible PROPUESTA/EJECUTADA/NO APLICA. Se mantiene el estado/motivo en title y aria-label. Debajo se añade leyenda compacta de indicadores, distinta del fondo de celda por peso post-compra.

Ordenación de USD, Total USD, precios y pesos usa data-sort-value con el valor numérico original. No analiza símbolos, comas, porcentajes ni texto del estado. Conserva precisión interna, compara números en ambos sentidos, mantiene0 como importe válido y N/D como vacío. No cambia la asignación, clasificación, umbral, ventas condicionadas ni pivotes5L/5R.

Verificado:11 comprobaciones de valores/orden ascendente/descendente; sintaxis del sorter y del JavaScript embebido de la plantilla. No se repitió la suite completa ni prueba visual en navegador. No se modificó MASTER. Pendiente de desplegar. Compatible con GPT1.3.13 y el parche de liquidez de v3.0.20.

## Homologación KairosGPT
Copiar compat/kairos_gpt/buy_weekly_policy.py sobre buy_weekly_policy.py del paquete KairosGPT 1.3.13 para aplicar la misma prioridad MASTER. El archivo es idéntico al selector Web. Esta entrega no instala el parche automáticamente.

Validación: 9 pruebas de prioridad MASTER, 9 de reciclaje de ventas y 8 de pivotes BTC; compilación Python. No se probó navegador ni despliegue.

# KairosWeb v3.0.19 — Pivotes BTC semanales 5L/5R

Corrige el gráfico Portafolio: antes usaba 2 semanas a cada lado; ahora exige extremos estrictos con 5 semanas completas a la izquierda y 5 a la derecha. Se excluye la semana UTC en curso. Las ventanas con semanas faltantes no cuentan como confirmación. Empates no son extremos estrictos.

Se calculan sobre toda la historia disponible (incluidas semanas previas al CL) y se muestran desde la semana del CL publicado hasta la última semana cerrada. Se seleccionan los últimos tres extremos confirmados en orden temporal, sin sustituirlos por candidatos ni colapsar artificialmente extremos consecutivos del mismo tipo. Cada pivote informa confirmed_at_utc: apertura UTC del lunes posterior al cierre de la quinta semana derecha. Si hay menos de tres, se muestran solo los disponibles y el contador n/3.

No cambia el régimen SMA20 de tendencia ni publica pivotes Elliott/CL/O1–O5 en MASTER. Conserva reglas de órdenes y reservas de v3.0.18; compatible con KairosGPT v1.3.13.

Validación actual: 8 pruebas aisladas ejecutan la función de producción (no una copia de su algoritmo), cubren 2R/5R, quinto vecino, empate, últimos tres, historia pre-CL, huecos y semana actual. Compilación Python verificada. La suite completa de Flask no fue repetida en este entorno; falta prueba visual y despliegue remoto. No se cambiaron saldos ni órdenes.

# KairosWeb v3.0.20 — Compras Balancer con ventas

Corrige la condición de reserva Balancer 0 por umbral O2/O4: solo desactiva la reserva/capacidad inicial financiada con liquidez existente. No anula el reciclaje condicionado de ingresos por ventas simuladas.

Compras con ventas = reserva Balancer libre permitida + ingresos de ventas simuladas, una sola vez. El tope porcentual del portafolio limita la reserva inicial, no esos ingresos reciclados. La asignación sigue recalculando pesos después de las ventas, comprando únicamente INFRA y respetando déficit/caja. Si no hay INFRA o se cubre todo el déficit, el sobrante queda sin asignar.

Los USD3694 de la captura son referencia bruta, no ingreso neto certificado. Descontar comisiones y diferencias de ejecución al conciliar. Antes del fill, el monto solo existe en el escenario Con ventas; no cambia liquidez física, QF, inventario, snapshot ni compromisos. No se envían órdenes.

Conserva pivotes BTC semanales5L/5R de v3.0.19 y clasificación de órdenes v3.0.18. Compatible con KairosGPT v1.3.13 aplicando el módulo idéntico incluido en compat/kairos_gpt/liquidity_reserves.py; copiar sobre ese archivo del paquete GPT, sin sustituir el resto. La actualización del módulo requiere instalación, no ocurre por generar este ZIP.

Validación actual:9 pruebas de reserva/asignación condicionada y8 de pivotes5L/5R, ejecutadas sin Flask; compilaciónPython verificada. Suitecompleta y prueba visual no repetidas. Los resúmenes de versiones2.x se consolidan en HISTORIAL_RELEASES_v2.md para mantener menos de100archivos. Pendiente de desplegar en Render; ningún MASTER modificado.
