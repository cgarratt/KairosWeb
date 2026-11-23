# KairosWeb 4.8.4 · PWA v1

El icono del iPhone abre el Portafolio en `/pwa/`.

- **Balancer** muestra las unidades sugeridas y el ingreso condicional por token.
- **Órdenes** muestra los últimos dos pivotes semanales confirmados cuando se elige un token. Si el Spot vigente rompe el rango, el tramo usa el pivote opuesto y el Spot como extremo provisional. HYPE utiliza exclusivamente HYPE/USDC de Hyperliquid para evaluar la ruptura.
- **Forecast** permite seleccionar cualquier token activo y muestra la trayectoria cuando hay anclas. La tabla proyecta precio, unidades publicadas y monto en O1–O5, con los saldos mantenidos constantes. Los niveles ausentes figuran como N/D. HYPE se expresa en USDC.

El acceso a la PWA usa el usuario y la contraseña de KairosWeb.

Usa A− y A+ en la barra superior para ajustar el texto del 90 % al 130 %. Kairos guarda la preferencia en el navegador.

## Publicar en Render

1. Copia el contenido del ZIP a la raíz del repositorio conectado a KairosWeb.
2. Publica la versión. Render instala las dependencias desde `requirements.txt`.
3. Comprueba que `/health` muestra 4.8.4 y que puedes iniciar sesión en `/pwa/`.
