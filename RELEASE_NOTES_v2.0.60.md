# KairosWeb v2.0.60 · Custodia con umbral de materialidad

Basado en v2.0.59. Mantiene donut de liquidez, edición única de topes desde Objetivos de gestión, consulta dinámica en Parámetros y navegación Órdenes antes de Forecast.

- Balancer: cada transferencia Exchange→HODL o Exchange→Core solo se propone si las unidades a mover son estrictamente mayores al5% del TOTAL de unidades del token (HODL+Core+Exchange). Se aplica por movimiento, no sobre el saldo Exchange ni sobre valor USDT.
- Movimientos menores o exactamente iguales al5% se consideran aceptables y se omiten. Sus unidades no se transfieren virtualmente: la distribución posterior únicamente incluye los movimientos visibles.
- La vista identifica variaciones menores aceptadas y distingue brechas residuales superiores al umbral. Conserva custodia protegida, BTC NEVER SELL, reservas SELL y conservación de unidades.
- Ninguna propuesta altera saldos, órdenes ni custodia real. El MASTER no se modifica por generar el reporte.

Validación:71 pruebas dirigidas aprobadas, integración del reporte Balancer y render Jinja verificados, sintaxis JavaScript válida. Se mantienen los siete fallos generales documentados del release anterior (contratos antiguos de autenticación de Alertas, aserciones de versión y botones retirados de Órdenes); no se certifica inspección visual mediante navegador en este entorno.

Instalación:descomprimir y subir todo el contenido a la raíz del repositorio, incluidas static y templates. Paquete de carga con menos de100archivos; excluye pruebas y cachés. Desplegar en Render y comprobar /health versión2.0.60 y release_assets.consistent=true. Este paquete no ejecuta el despliegue remoto. KairosGPT se mantiene en1.3.11.
