# KairosWeb v1.6.0 · Renombramiento explícito de Fibonacci

## Nomenclatura canónica en KairosWeb

| Nivel de compras | O2 | O4 |
| --- | --- | --- |
| Fib 38.2% | O2C1 | O4C1 |
| Fib 50% | O2C2 | O4C2 |
| Fib 61.8% | O2C3 | O4C3 |
| Fib 78.6% | O2C4 | O4C4 |

| Nivel de ventas | O3 | O5 |
| --- | --- | --- |
| Fib 1.618 | O3V1 | O5V1 |
| Fib 2.618 | O3V2 | O5V2 |
| Fib 3.618 | O3V3 | O5V3 |
| Fib 4.618 | O3V4 | O5V4 |

## Compatibilidad sin recálculo ni cambio de precios

| Columna histórica en `07_PIVOTES` | Equivalencia canónica **solo para la onda O2** |
| --- | --- |
| C1 Fib 50% (columna L) | O2C2 Fib 50% |
| C2 Fib 61.8% (columna M) | O2C3 Fib 61.8% |
| Fib 38.2% (columna K) | O2C1 Fib 38.2% |
| Fib 78.2% (columna N), referencia histórica | O2C4 Fib **78.6%** para cálculos nuevos, **recalcular**, nunca reetiquetar como el mismo precio |

- El código `google_sheets_master.py` **lee el mismo valor en las columnas históricas L/M** y lo presenta como `O2C2` / `O2C3`. Las cifras no se intercambian ni alteran. Los IDs originales de órdenes/fills históricos no se renombran.
- En el release, `C1_BAG_FRACTION_P`, `C2_BAG_FRACTION_P` y `ORDINARY_DEFAULT_USDT_TARGET` pasan a ser **claves históricas/no activas para KairosWeb**; no se presentan en Settings ni gobiernan montos. Se conservan sin borrar en el Google Sheets original para trazabilidad y por compatibilidad KairosGPT hasta migración transversal posterior.
- **Única fuente activa de la meta USDT para KairosWeb:** `STRUCTURAL_USDT_TARGET`. La tolerancia Balancer se obtiene de `DRIFT_BAND_PP`.
- **Presupuesto máximo de compras O2 y O4:** 25% del patrimonio P por onda, NO sumado nuevamente a bolsillos históricos C1/C2. Los 4 porcentajes de cada onda se guardan individualmente en `12_PARAMETROS_KAIROS` al autorizar Guardar.
- La modificación física de las cabeceras históricas de Sheets, la homologación de los registros KairosGPT y la actualización del esquema de órdenes remotas **no forman parte del despliegue automático del ZIP**, ni se debe hacer sin revisión y autorización separadas.
- En `07_PIVOTES` las referencias O2C2/O2C3 conservan estado histórico; nada se transforma en órdenes ejecutables o pivotes certificados.
