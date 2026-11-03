# KairosWeb v4.4.0 · Cuatro tarjetas BTC

RSI, Stoch RSI, ADX y Spot/STH/EMA20/EMA50. Minivelocímetros compactos y distancias respecto del Spot. Cuatro tarjetas en una línea en escritorio. Balancer diario; Compras/Ventas semanal. STH conserva corte diario independiente.

Instalación: descomprimir ZIP, subir todo el contenido a raíz del repositorio Web existente y desplegar en Render. Conservar variables/secretos. No actualizar MCP de mercado. /health: version 4.4.0 y assets consistentes. Actualizar Spot e históricos (preferiblemente 999 días); pulsar «Actualizar STH · Glassnode» para cargar STH y conversión USDT/USD desde el MCP público oficial. Primera carga vacía: STH N/D hasta pulsar ese botón.

No se presume USDT=USD; sin FX válido, distancia a STH N/D. Fuentes/cortes en los desplegables. La conexión Glassnode se probó desde el adaptador local, no desde tu servicio Render. Si el proveedor no responde o no concede acceso, la interfaz conserva N/D con causa.

No requiere API key en acceso público probado. Caché local temporal; tras reinicio sin persistencia, actualizar STH de nuevo. Opciones avanzadas y metodología: RELEASE_NOTES_v4.4.0.md. El paquete no despliega automáticamente ni modifica MASTER o reglas financieras.
