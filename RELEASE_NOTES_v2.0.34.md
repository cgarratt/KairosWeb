# KairosWeb v2.0.34 — Objetivos de Liquidez y ReservaTrading

## Alcance

Se añade una nueva pestaña de Configuración llamada **Objetivos de liquidez y ReservaTrading (%)**, que permite editar la distribución objetivo del capital histórico registrada en `08_INTEGRAL` sin usar Google Sheets manualmente.

Se muestran cuatro entradas: Liquidez, Trading · ReservaTrading, HODL + Core y Exchange. Se muestra el valor objetivo USDT equivalente al porcentaje seleccionado sobre el capital histórico original y se exige que el total sea **100%** antes de publicar. Si se aumenta Liquidez o Trading se debe compensar en otros objetivos; KairosWeb no decide esa compensación unilateralmente.

## Separación de conceptos

- `08_INTEGRAL` almacena **objetivos de capital histórico**, no liquidez Spot vigente.
- `12_PARAMETROS_KAIROS.STRUCTURAL_USDT_TARGET` conserva el **objetivo estructural de liquidez** de la política. Sigue editable en `Configuración → Parámetros → Portafolio` y no se cambia por editar `08_INTEGRAL`.
- `03_LIQUIDEZ` contiene saldos **reales** por venue; Quantfury es la ReservaTrading física y ya forma parte de USDT físico total. Un porcentaje de objetivo NO cambia esos saldos.
- El backend modifica solo `08_INTEGRAL!B11:B14` según las filas editadas: se mantienen intactas las fórmulas `D11:D14` que calculan el objetivo %, las fórmulas de total, datos históricos, pérdidas realizadas, costos, custodia y unidades.

## Garantías

Requiere sesión administrativa, protección CSRF, justificación, validación de snapshot y suma 100%. Publica nuevo snapshot, historial y auditoría, con homologación de base contable conforme al motor ya existente. No opera en exchanges ni registra fills.

## Validación local

- 215 pruebas Python aprobadas, 2 omitidas.
- 9 suites JavaScript aprobadas.
- 12 plantillas Jinja analizadas.
- Contrato probado: edición 25% Liquidez / 15% Trading y no alteración de QF físico, rechazo de sumas distintas de 100% y de filas fuera de la lista permitida.
- Flask/Render y permisos reales de escritura no verificados en producción; paquete GitHub pendiente de despliegue.
