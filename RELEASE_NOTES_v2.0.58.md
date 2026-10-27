# KairosWeb v2.0.58 · Liquidez simplificada y configuración integrada

Cambios aprobados:
- Gestión de liquidez: total USDT, barra seccionada y tres categorías excluyentes: Compras O2/O4, Reserva Balancer y Reserva Trading real. Importes con dos decimales y porcentajes sobre liquidez física. Se retiran de esta sección patrimonio, metas, topes y déficits. Los límites financieros del motor se conservan.
- Objetivos de gestión: campos editables para Tope Balancer y Tope Trading, leídos de los parámetros aprobados de MASTER (inicialmente6%/3%). Se publican atómicamente junto con los demás objetivos, con autorización administrativa, vista previa y auditoría existentes. También se conservan en Parámetros.
- Integridad: topes independientes0..100%, ambos presentes, sumas de Cripto/Liquidez, Tiers, reparto base de liquidez y custodias igual100%. Las categorías reales deben sumar liquidez física y no tener saldos negativos. QFreal no se reduce automáticamente por cambiar un tope.
- Navegación: Portafolio → Balancer → Compras → Ventas → Órdenes → Forecast.

Comprobaciones:49 pruebas dirigidas y8subpruebas aprobadas, render Jinja del reporte Balancer y sintaxis JavaScript válidos. Se conservan siete fallos generales heredados del release anterior: dos contratos de autenticación de Alertas, tres verificaciones de versión antigua y dos botones de órdenes retirados. No se certificó inspección visual mediante navegador en este entorno.

Paquete para GitHub: excluye únicamente pruebas y cachés; conserva todos los archivos de ejecución. Descomprimir y cargar TODO el contenido en la raíz del repositorio, incluidas static y templates. Se requiere desplegar este release en Render; después, los parámetros pueden cambiarse sin nuevo deploy. Comprobar /health versión2.0.58 e integridad de assets. No incluye credenciales ni datos del portafolio.

KairosGPT permanece en1.3.11; este release solo cambia KairosWeb y la validación de publicación desde su menú Configuración. No envía órdenes, transfiere custodia ni modifica saldos por sí mismo.
