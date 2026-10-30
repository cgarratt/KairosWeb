# KairosWeb 3.0.15 — Estados de compra y asignación de liquidez

## Flujo aprobado
- Cada compra nueva nace PROPUESTA.
- La imagen de la transacción registrada y verificada por KairosGPT confirma la orden en el MASTER compartido.
- En Órdenes de Web solamente una orden CONFIRMADA puede pasar a EJECUTADA. Las propuestas no muestran botón de cambio. El servidor vuelve a verificar el estado persistido, revisión y snapshot.
- Confirmadas, parciales y ejecutadas no reciben nueva asignación. Las propuestas solo pueden recibir liquidez cuando su objetivo Fibo es estrictamente inferior al Spot vigente y cumplen las reglas de ponderación existentes.
- Compras manuales y Balancer no se atribuyen automáticamente a niveles O2/O4.

## Alcance y publicación
Web guarda eventos en 26_ORDENES_GESTION. No envía operaciones al exchange ni acredita inventario o caja. La ejecución queda pendiente de conciliación cuando corresponde. No repetir el ajuste de balances si el comprobante ya fue conciliado por KairosGPT.
La confirmación por imagen es una instrucción de KairosGPT incluida en ADENDA_KAIROSGPT_ESTADOS_COMPRA.md; requiere que GPT pueda escribir y leer el MASTER compartido. No se agrega reconocimiento de imágenes en Web.
Se mantienen sesión administrativa, CSRF, validación de origen, evidencia, ID, revisión, duplicados y capacidad por venue. Se necesita KAIROS_GOOGLE_WRITER_JSON con permiso de edición de la hoja.
Paquete preparado localmente; despliegue remoto y escrituras reales no verificados. Sustituir los archivos del repositorio y desplegar en Render. Los cambios posteriores de datos comparten MASTER y no requieren otro deploy.

## Verificación de esta versión
11 pruebas Python: transiciones, rechazo de saltos, acceso administrativo, validación del estado persistido y plantillas.
7 casos JavaScript: objetivo inferior/igual/superior al Spot y bloqueo por estados.
Sintaxis JavaScript e integridad de assets verificadas. Sin pruebas visuales en navegador ni pruebas de escritura en producción.
