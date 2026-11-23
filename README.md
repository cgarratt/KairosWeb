# KairosWeb 4.8.9 · PWA v1

El icono del iPhone abre el Portafolio en `/pwa/`. La PWA incluye Portafolio, Balancer y Órdenes. Forecast se consulta desde la versión web.

- **Balancer** muestra las unidades sugeridas y el ingreso condicional por token.
- **Órdenes** muestra retrocesos y extensiones Fibonacci entre dos referencias semanales fechadas. Las extensiones 1.272, 1.618 y 2.618 se proyectan desde el primer punto en la dirección del tramo. Si solo existe el CL vigente, usa el O1 guardado en 27_PIVOTES_ANTES_20261121 cuando es compatible. BTC se selecciona al abrir. Si se verifica una ruptura, el extremo del tramo se actualiza de forma provisional.

El acceso a la PWA usa el usuario y la contraseña de KairosWeb.

Pulsa A± en la barra superior para recorrer los tamaños de texto. Tras el 130 %, el botón vuelve al 90 %. Kairos guarda la preferencia en el navegador.

En Seguimiento del portafolio, Precio Spot aparece justo después de Token.

## Publicar en Render

1. Copia el contenido del ZIP a la raíz del repositorio conectado a KairosWeb.
2. Publica la versión. Render instala las dependencias desde `requirements.txt`.
3. Comprueba que `/health` muestra 4.8.9 y que puedes iniciar sesión en `/pwa/`.
