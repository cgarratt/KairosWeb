# KairosWeb v4.6.0 · Niveles Fibo de ventas

Configuración muestra O3V1–O3V4 y O5V1–O5V4 sin niveles Fibonacci fijos. Las claves históricas de los porcentajes se conservan para compatibilidad; no se migran ni escriben datos de MASTER.

Forecast incorpora ocho desplegables en Trayectoria del ciclo por token: uno por tramo de venta. Opciones: 38.2%, 50%, 61.8%, 78.6%, 100%, 127.2% y 161.8%. Inicio del escenario local: 38.2%, 50%, 61.8%, 78.6% en cada onda. Los controles O3/O5 del punto final de trayectoria también admiten los siete valores.

La distribución independiente muestra los niveles elegidos arriba y calcula sus precios con esos mismos valores: O3 desde O2 usando O1−CL; O5 desde O4 usando O3−O2. Solo participan los niveles alcanzados por el punto final del escenario. V1–V4 deben estar ordenados de menor a mayor (se admiten iguales); una selección descendente bloquea el cálculo con una indicación visible. Los porcentajes conservan su validación de suma 100%.

Los valores son de simulación local y se reinician al recargar la página. No se publican en Sheets ni modifican pivotes VALIDADO/CONFIRMADO, órdenes o saldos. Las reglas operativas de órdenes quedan conservadas. Este cambio no resuelve ni certifica el incidente de conexión mostrado previamente en Órdenes.

## Instalación

Descomprimir y reemplazar el contenido del repositorio Web sobre v4.5.0; desplegar con el procedimiento habitual de Render. Sin cambios de MCP ni variables de entorno. Si se actualiza desde v4.4 o anterior, retirar además los siete archivos obsoletos descritos en el release v4.5.

Validación local: 243 pruebas aprobadas, incluyendo precios personalizados O3/O5, pivote confirmado protegido, compilación de plantilla y sintaxis JavaScript. Despliegue remoto pendiente.
