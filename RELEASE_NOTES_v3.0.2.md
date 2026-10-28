# Kairos v3.0.2 · Homologación con KairosGPT 1.3.12

- Validador común de cronología estricta CL < O1 < O2 < O3 < O4 < O5. Las filas heredadas incoherentes siguen disponibles en Configuración para reparación, pero no aportan anclas ni precios operativos.
- Configuración marca los errores de fechas, rechaza publicación inválida y permite retirar explícitamente O1–O5 PROPUESTOS del borrador, conservando CL. Confirmados inmutables. No cambia fechas por inferencia ni modifica MASTER al instalar.
- Forecast y Compras excluyen las anclas incoherentes. Forecast identifica el motivo de exclusión. BSI, TradingBot y certificación remota conservan sus controles.
- O3 del ciclo sin freno por porcentaje USDT; límite Exchange libre/Tier, descontando SELL reservadas. Ventas ordinarias al X% conserva su objetivo de caja independiente.
- Motor Forecast JavaScript puro comparado con Python por unidades y caja. Ambos recalculan déficits después del presupuesto por tramo, protegen QF/compromisos BUY/SELL y separan conversión virtual BTC.
- O5 lee reparto aprobado dinámico. Core en O5 requiere casilla explícita; no habilitada por defecto. Post-O5 sigue siendo una hipótesis terminal separada.
- Pesos O3 no publicados: escenario solicitado 20/20/30/30, identificado como simulación pendiente de publicación; no escribe parámetros por instalar.
- Contador de ejecuciones conciliadas y estado visible requieren CONCILIADA_EN_05. El diario devuelve balances_updated=false; no se confunde evidencia con inventario acreditado. No incluye un reconciliador financiero automático.
- Custodia solo movimientos >5% del total por token, preservando SELL reservadas. Nuevo análisis requiere Spot de hasta180s y tolerancia futuro30s. Las solicitudes financieras releen MASTER con force=True, sin redeploy por cambios de datos.
- Confirmación técnica con pivote semanal posterior HL/LH, además de validación base 5PI/5PD+BoS y autorización explícita para publicar. La revisión firmada no publica por sí sola.

Instalación: subir el contenido descomprimido al repositorio existente y desplegar en Render. /health debe indicar 3.0.2 y assets consistentes. Conservar credenciales existentes. Esta entrega es código preparado, no evidencia de despliegue remoto.
