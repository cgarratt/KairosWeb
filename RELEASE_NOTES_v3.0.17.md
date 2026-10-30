# KairosWeb 3.0.17 — Umbral de liquidez para Balancer

Configuración > Objetivos de gestión > Reservas: nuevo Umbral mínimo O2/O4 (% del portafolio), valor predeterminado autorizado 10%. Clave compartida BALANCER_MIN_O2_O4_PORTFOLIO_FRACTION; se almacena como fracción 0–1 en 12_PARAMETROS_KAIROS. El guardado crea la fila si falta, conserva las validaciones de las demás sumas y usa el flujo auditado existente. El umbral es independiente: no se suma a los porcentajes de composición.

Primero se calcula la reserva Balancer normal con su porcentaje de liquidez y tope del portafolio. Se compara (liquidez sin QF − compromisos BUY − reserva Balancer libre normal) / valor total Spot del portafolio con el umbral. El denominador incluye todo el portafolio, incluida su liquidez. Si la relación es estrictamente menor, la reserva Balancer nueva y su capacidad de nuevas compras quedan en 0. La reserva libre se reasigna a O2/O4. Con igualdad se mantiene la fórmula normal. Umbral 0 desactiva esta condición.

La comparación usa siempre la reserva normal antes de liberarla, para evitar oscilación. No cancela compromisos ni envía órdenes; QF físico no cambia. Se bloquea también la capacidad hipotética de nuevas compras Balancer con ventas mientras opere la condición. Configuración rechaza porcentajes negativos, >100%, no finitos o filas presentes no aprobadas. Si la nueva clave aún no existe, se usa el 10% explícitamente aprobado por el usuario; se persiste al guardar Objetivos.

compat/kairos_gpt/liquidity_reserves.py es una actualización del módulo compartido para el paquete KairosGPT existente. Copiar en kairos_gpt/liquidity_reserves.py; no reemplazar todo KairosGPT por una versión anterior. La instrucción complementaria está en ADENDA_KAIROSGPT_ESTADOS_COMPRA.md.

Validación: 33 pruebas Python (incluye creación/actualización del parámetro, límites y preservación de fondos), 7 casos JavaScript de compras y sintaxis de Configuración. Assets consistentes; sin prueba visual en navegador. Paquete preparado localmente: no desplegado, ni parámetro publicado en MASTER, ni modificación de saldos reales.
