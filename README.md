# KairosWeb 4.8.2 · PWA v1

El icono del iPhone abre el Portafolio en `/pwa/`.

- **Balancer** muestra las unidades sugeridas y el ingreso condicional por token.
- **Órdenes** muestra los últimos dos pivotes semanales confirmados cuando se elige un token. Si el Spot vigente rompe el rango, el tramo usa el pivote opuesto y el Spot como extremo provisional. HYPE utiliza exclusivamente HYPE/USDC de Hyperliquid para evaluar la ruptura.
- **Forecast** permite seleccionar cualquier token activo y muestra la trayectoria cuando hay anclas. La tabla proyecta precio, unidades publicadas y monto en O1–O5, con los saldos mantenidos constantes. Los niveles ausentes figuran como N/D. HYPE se expresa en USDC.
- **Llave de acceso** activa el registro y el acceso WebAuthn de la PWA con verificación de usuario. Kairos admite una llave activa para la cuenta del portafolio en este dominio. Se requiere la contraseña para activarla, reemplazarla o retirarla.

## Publicar en Render

1. Copia el contenido del ZIP a la raíz del repositorio conectado al servicio existente KairosWeb y publica la versión. Render instala las dependencias desde `requirements.txt`. Comprueba que `/health` muestra 4.8.2.
2. Para habilitar la llave, abre **Environment** del mismo servicio. Agrega `KAIROS_PASSKEY_DATABASE_URL` con la URL de PostgreSQL persistente. Si la base PostgreSQL y el servicio están en el mismo workspace y región de Render, usa la URL interna. Kairos crea las dos tablas de acceso al primer uso. Usará el hostname de Render o, si utilizas un dominio personalizado, `KAIROS_PUBLIC_ORIGIN` debe contener la dirección HTTPS exacta.
3. Abre el icono de Kairos en el iPhone e inicia sesión con la contraseña. Al final de Portafolio, abre **Llave de acceso · Face ID**, confirma la contraseña y registra la llave.
4. Cierra sesión desde la PWA. Usa **Entrar con llave de acceso** y comprueba que iOS pide la verificación del dispositivo.

La prueba local de WebAuthn utilizó PostgreSQL y un autenticador de prueba. Quedan pendientes el despliegue y la validación en iPhone.
