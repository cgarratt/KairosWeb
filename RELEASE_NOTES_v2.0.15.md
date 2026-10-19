# Release Notes — KairosWeb v2.0.15

Base publicada: KairosWeb v2.0.14. Esta versión **no** actualiza KairosGPT.

## Compras
- Matriz: «Maestro de Precios - Retrocesos Fibo».
- El mismo color histórico posterior a P2 se aplica a Precio, % Peso y USDT.
- Máximo disponible = USDT físico menos QF contado una vez.
- Slider de despliegue teórico desacoplado de la elegibilidad por token: el 100% del importe escogido se reparte en cuatro escalones según el Master APROBADO. La compra simulada efectiva continúa limitada por INFRA y déficit contra targets y puede ser menor; remanente en USDT.

## Órdenes
- Resumen: «Próximas órdenes por Token», Nivel después de Origen, glosa Fib para códigos genéricos C1..4 y EXT1W1..4.
- Tabla principal: «Backlog de Ordenes Compra / Venta».
- Cuatro combos: Exchange, Tier, Operación y Token. Removidos Vista rápida, Origen, Grupo y Proximidad; botón Limpiar filtros.
- Sin cambios en fases de ejecución: no se envían órdenes ni se marcan fills.

## Regresiones estructurales VIRTUAL / HYPE
- VIRTUAL: comprobar en simulación P1 O2 `0.4977` (2026-06-25) y P2 máximo semanal posterior. CL anómalo de 2025 no se reintroduce desde el archivo MCP si la estructura actual está publicada.
- HYPE: comprobar P1 O2 VALIDADO `51.11` (2026-08-02) y máximo posterior `97.885` (2026-09-23) con fuentes Hyperliquid Spot HYPE/USDC y semanas UTC cerradas.
- Pruebas locales con velas de prueba representativas; **no** se verificó la conexión remota en Render ni se modificó el Master.

## Validación del paquete
- Python: 162 aprobadas, 2 omitidas.
- JavaScript: suite sin fallos (ver comprobación de release).
- Python compila, 13 plantillas Jinja verificadas, controles `/health` y manifest de integridad comprobados.
- 99 archivos totales, con SHA-256 y release manifest.

## Instalación
Descomprimir en el repositorio GitHub, hacer commit/push y verificar `/health` con versión `2.0.15`. Queda pendiente validación HTTP de Render y de la instancia privada MCP Hyperliquid.
