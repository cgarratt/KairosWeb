# KairosWeb v2.0.59 · Donut de liquidez y editor único de reservas

- Gestión de liquidez: donut con liquidez total en el centro. Categorías excluyentes Compras O2/O4, Reserva Balancer y Reserva Trading real, con importe USDT y porcentaje. Sin topes, metas o déficits en esta sección. QFreal se conserva íntegro; sin duplicar Balancer ni QF.
- Configuración → Objetivos de gestión → Reservas y topes del portafolio es el único lugar donde se editan los topes de ambas reservas. Publicación conjunta con las demás metas y auditoría existente.
- Configuración → Parámetros conserva ambos topes como consulta de los valores publicados en MASTER. No aparecen inputs editables. El servidor rechaza intentos de actualizar esos topes a través de la sección Parámetros.
- Las descripciones de consulta muestran el porcentaje actual de MASTER, sin texto fijo6%/3%. No se modifican valores publicados a partir de capturas de borradores.
- Se conservan topes independientes0..100%, presencia de ambos, sumas al100% de los repartos, partición física de caja y protección de QF. Se conserva el cálculo financiero de v2.0.58.
- Conserva navegación Portafolio → Balancer → Compras → Ventas → Órdenes → Forecast y el historial de órdenes.

Comprobaciones:52 pruebas dirigidas y8subpruebas aprobadas, incluyendo render del donut, caso caja cero, integridad y bloqueo de la vía duplicada de edición. Sintaxis JavaScript válida. Suite general conserva siete fallos heredados sin relación con estos cambios; no se certificó inspección visual con navegador en este entorno.

Instalación:descomprimir y subir todo el contenido a la raíz del repositorio, incluidas static y templates. Este paquete de carga excluye únicamente pruebas y cachés y tiene menos de100archivos. Desplegar en Render y verificar /health versión2.0.59 y assets consistentes. Esta entrega no realiza despliegues remotos ni cambios de saldos, custodia u órdenes.

KairosGPT permanece en v1.3.11; no necesita actualizarse por estos cambios de interfaz. Los valores financieros se leen del MASTER PUBLICADO y las cotizaciones vigentes al ejecutar el motor.
