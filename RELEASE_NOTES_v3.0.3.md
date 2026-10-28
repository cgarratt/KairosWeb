# Kairos v3.0.3 · Corrección Balancer MODE_RENDER

Se normalizan las claves PUMP/PUMPFUN de las reservas SELL igual que las posiciones de custodia. La versión3.0.2 construía posiciones con PUMPFUN y reservas con PUMP, provocando CustodyError incluso con reserva0. No se elimina la protección de unidades comprometidas.

Regresión: reporte real Balancer y plantilla Jinja con los12tokens y reservas PUMP de0 y1 unidades. La prueba reproduce el error antes de corregir y pasa después. Suite completa:289 pruebasPython+8subtests aprobados.

Compatible con KairosGPT1.3.12; conserva las correcciones de homologación y cronología CL→O5. MASTER no se modifica. No requiere actualizar GPT ni variables de entorno.

Descomprimir el ZIP y subir el contenido completo al repositorio existente. Desplegar en Render; /health debe indicar3.0.3 y consistencia de assets. Verificar /mode/balancer. El despliegue remoto y sus logs no se han consultado desde esta sesión.
