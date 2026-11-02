# KairosWeb 3.0.34 · Release activo

Ver RELEASE_NOTES_v3.0.34.md para el comportamiento vigente. Spot e históricos se actualizan por separado. Notas anteriores se conservan como historia; las de 3.0.1 y 3.0.33 se integraron en HISTORIAL_RELEASES_v2.md.

# KairosWeb v3.0.34 · Suite2026.11.02.1

Compatible con GPT1.3.17, Binance5.4.1, KuCoin1.0.1 e Hyperliquid1.0.1. Conservar los tres endpoints independientes. La versión incluye los modos de Portafolio, Balancer, Compras, Ventas, Órdenes y Forecast, con sus restricciones vigentes. Leer RELEASE_NOTES_v3.0.34.md e INSTALACION_SUITE.md del paquete completo. Pendiente de despliegue.

# KairosWeb v3.0.32

KuCoin Spot como respaldo explícito de Binance. Desplegar MCP KuCoin1.0.0 y configurar KUCOIN_MCP_URL en Render Web. Conservar Binance5.4.0. Leer RELEASE_NOTES_v3.0.32.md. Preparado localmente, no desplegado.

# KairosWeb v3.0.31

Una carga manual de Binance compartida por las pantallas. Instalar primero MCP v5.4.0 y luego Web. Pulsar Actualizar Spot para cargar datos; no se consulta Binance por navegar. Ver RELEASE_NOTES_v3.0.31.md. Preparado y validado localmente; pendiente de despliegue.

# KairosWeb v3.0.30

Bloqueo Binance visible, botón en pausa con horario Lima e históricos cerrados conservados al actualizar Spot. Ver RELEASE_NOTES_v3.0.30.md para instalación de MCP y Web. Compatible con KairosGPT v1.3.15. Preparado localmente, no desplegado.

# KairosWeb v3.0.29

Corrige el cálculo de Órdenes para usar el precio y estado de cada token. Conserva O2C2/O2C3, filtro de importe $0, combos y guardado global. Compatible con KairosGPT v1.3.15. Ver RELEASE_NOTES_v3.0.29.md.

Descomprimir y reemplazar el contenido del repositorio existente. Desplegar en Render y verificar /health: 3.0.29. No se modificó MASTER.

# KairosWeb v3.0.28

Corrige el listado O2C2/O2C3 y oculta órdenes con importe $0.00. Conserva combos y guardado global. Compatible con KairosGPT v1.3.15. Ver RELEASE_NOTES_v3.0.28.md.

Instalación: descomprimir y subir los archivos al repositorio existente; desplegar en Render. /health debe informar 3.0.28. MASTER no fue modificado.

# KairosWeb v3.0.22

Indicador junto al precio objetivo Fibo; USD sin indicador. Leyenda y ordenación numérica conservadas. Pendiente de desplegar.

# KairosWeb v3.0.21

Tabla Fibo: solo indicadores y leyenda; ordenación monetaria numérica. Ver RELEASE_NOTES_v3.0.21.md. Pendiente de desplegar.

# KairosWeb v3.0.20

Corregido Compras (con ventas) cuando la reserva Balancer es0. Ver RELEASE_NOTES_v3.0.20.md. Incluye parche del módulo de liquidez para KairosGPT v1.3.13. Pendiente de desplegar/instalar.

# KairosWeb v3.0.19

Corrección BTC semanal: pivotes 5L/5R. Ver RELEASE_NOTES_v3.0.19.md. Pendiente de desplegar. Compatible con GPT v1.3.13.

# KairosWeb v3.0.18 · KairosGPT v1.3.13

Ver RELEASE_NOTES_v3.0.18.md y HOMOLOGACION_ORDENES.md. Pendiente de instalar y desplegar.

# KairosWeb v3.0.17

Ver RELEASE_NOTES_v3.0.17.md. Umbral Balancer configurable, predeterminado 10%. Pendiente de desplegar y guardar el parámetro en MASTER desde Configuración.

# KairosWeb v3.0.16

Ver RELEASE_NOTES_v3.0.16.md. Paquete preparado; pendiente de despliegue.

Release v3.0.14: Tendencia BTC 1W con flecha y minigráfico de rangos semanales cerrados, cierres y tres pivotes 2L/2R. Sin datos verificables muestra N/D. No modifica pivotes Elliott ni órdenes.
# KairosWeb v3.0.8 — Objetivos por token y límites Tier

Base: KairosWeb v3.0.6. Configuración > Objetivos de gestión incorpora los 12 pesos editables y valida 100% cripto y sumas exactas T1/T2/T3. La publicación auditada escribe los porcentajes aprobados en 02_POSICIONES sin redistribuirlos proporcionalmente. No cambia unidades ni caja.

Release v3.0.11: PRI v1 y tendencia BTC semanal con datos verificados.

Release v3.0.12: Panel ejecutivo visual PRI (velocímetro y 3 métricas), tendencia BTC 1W (ícono/estado/último cierre) y precarga asíncrona de 210 velas 1D cerradas Binance Spot. El panel muestra N/D hasta contar con 21 semanas UTC completas. Los cálculos son informativos; no autorizan órdenes. La actualización del indicador consulta el estado del caché sin recargar Portafolio.
