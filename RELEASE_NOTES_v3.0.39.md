# KairosWeb3.0.39 · KuCoin primario e históricos

Ver README.md para instalación y política vigente. Los roles actuales prevalecen sobre estas notas históricas.

# KairosWeb 3.0.38 · Gráfico de tendencia BTC

Ver README.md para instalación, requisitos, cambios y validación vigente.

## Notas históricas

# KairosWeb 3.0.37 · Diagnóstico sin dependencia del MASTER

Ver README.md para instalación, causa corregida y validación vigente.

## Notas históricas

# KairosWeb 3.0.36 · Configuración y diagnóstico de tres MCP

Ver README.md para instalación, cambios y validación vigente.

## Notas históricas de 3.0.35 y 3.0.34

# KairosWeb 3.0.35 · Forecast independiente de históricos

Ver README.md para instalación, correcciones, límites y validación.

## Comportamiento heredado de 3.0.34

# KairosWeb 3.0.34 · Spot rápido e históricos separados

- Actualizar Spot llama a get_kairos_spot_prices, no a la carga de históricos. Conserva 12 cotizaciones completas, fuente y hora. Binance requiere dos peticiones REST internas; KuCoin requiere una. Ninguna cotización se inventa o mezcla.
- Reutiliza Spot durante 60 segundos desde la hora original, incluso con clics simultáneos. Más de 180 segundos bloquea valoración actual. La navegación no solicita mercado Binance.
- Plazo completo de conexión + negociación MCP + herramienta: Binance Spot 10 s, KuCoin 45 s. Configurables con KAIROS_PRIMARY_SPOT_TIMEOUT_SECONDS (3–45) y KAIROS_BACKUP_SPOT_TIMEOUT_SECONDS (3–90). No hay reintentos en esta ruta. Una pausa primaria conocida permite ir directo a KuCoin.
- Nuevo control Actualizar históricos. Llama al snapshot existente del MCP Binance una vez y reutiliza las 12 series hasta el próximo cierre diario UTC. Verifica fuente, identidad y último cierre; conserva Spot sin cambiar su fecha. El endpoint de carga también obtiene cotizaciones internamente porque ese es el contrato del MCP existente; esas cotizaciones no reemplazan el Spot Web.
- Cambiar a KuCoin conserva históricos Binance por separado. Un histórico vencido permanece guardado pero no se sirve como serie vigente. Si falla su actualización se mantiene la valoración Spot válida.
- Las vistas GET reutilizan el MASTER validado durante KAIROS_SHEETS_CACHE_SECONDS (60 s por defecto). POST y publicaciones releen el MASTER. Las mutaciones conservan sus verificaciones, CSRF y revisión de snapshot.
- Snapshot atómico en KAIROS_MARKET_SNAPSHOT_FILE; la ruta predeterminada /tmp es efímera. Se puede apuntar a un volumen persistente ya provisionado. Un solo worker, conforme al render.yaml. No es caché distribuida.
- No cambia reglas financieras, saldos, custodia, órdenes o automatizaciones.

## Alcance pendiente

No se instala gateway común para GPT/Web/Alertas, almacenamiento externo ni un planificador. La descarga incremental solo de velas nuevas requiere ampliar el contrato del MCP; este release reutiliza series completas por día. La sesión y pausas Web siguen siendo locales al proceso. Los 3 MCP actuales son compatibles y no se modifican.

## Instalar

Reemplazar el contenido del repositorio por este ZIP descomprimido en la raíz, mantener secretos y desplegar. Mantener KUCOIN_MCP_URL=https://kairos-kucoin.onrender.com/mcp. /health debe reportar 3.0.34 y release_assets.consistent=true.

Tras desplegar: pulsar Actualizar Spot; comprobar las 12 valoraciones y fuente/hora. Para análisis técnico, pulsar Actualizar históricos cuando Binance esté disponible. Confirmar que cambiar de pestaña no solicita nuevas cotizaciones. Si falla por despertar de Render Free, revisar logs y ajustar plazos; no esperar la misma latencia que con servicios siempre activos.

Rollback: restaurar Web3.0.33 y las instrucciones GPT1.3.16; la forma del snapshot sigue usando policy=MANUAL_SNAPSHOT. Tras la reversión, cargar datos explícitamente. Nunca borrar MASTER.

Validación local: consultar VALIDACION_RELEASE.json en el paquete conjunto. No hay verificación de despliegue, prueba visual en navegador ni escritura live del MASTER.
