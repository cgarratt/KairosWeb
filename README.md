# KairosWeb 4.8.7 · PWA v1

El icono del iPhone abre el Portafolio en `/pwa/`. La PWA incluye Portafolio, Balancer y Órdenes. Forecast se consulta desde la versión web.

- **Balancer** muestra las unidades sugeridas y el ingreso condicional por token.
- **Órdenes** muestra retrocesos y extensiones de simulación entre dos referencias semanales fechadas, incluso propuestas. Si solo está publicado el CL, puede usar un O1 anterior fechado del archivo de 07_PIVOTES. Para actualizar el extremo del escenario usa máximos o mínimos de velas diarias cerradas del mismo mercado y la cotización Spot vigente. Si falta cobertura, indica que el extremo está por verificar.

El acceso a la PWA usa el usuario y la contraseña de KairosWeb.

Pulsa A± en la barra superior para recorrer los tamaños de texto. Tras el 130 %, el botón vuelve al 90 %. Kairos guarda la preferencia en el navegador.

En Seguimiento del portafolio, Precio Spot aparece justo después de Token.

## Publicar en Render

1. Copia el contenido del ZIP a la raíz del repositorio conectado a KairosWeb.
2. Publica la versión. Render instala las dependencias desde `requirements.txt`.
3. Comprueba que `/health` muestra 4.8.7 y que puedes iniciar sesión en `/pwa/`.
