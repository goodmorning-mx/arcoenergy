# Modelo financiero de Arco Energy

## Estados financieros

- **Balance general / estado de situación financiera:** muestra activos, pasivos y patrimonio en una fecha de corte. La ecuación que debe cuadrar es activos = pasivos + patrimonio, incluyendo el resultado acumulado del mayor.
- **Estado de resultados:** muestra ingresos y gastos durante un periodo. En Arco Energy separa ingresos, costo de venta, gastos operativos, gastos financieros y gastos personales/otros, de acuerdo con la separación solicitada por Mario Groso.
- **Estado de flujo de efectivo:** muestra los cambios en efectivo y bancos durante un periodo clasificados como operación, inversión y financiamiento. El flujo neto debe reconciliar el efectivo inicial y final. Una póliza puede dividir el tratamiento; por ejemplo, pago de deuda y pago de intereses.

La referencia de estructura es [IAS 1 de IFRS](https://www.ifrs.org/issued-standards/list-of-standards/ias-1-presentation-of-financial-statements/) y la clasificación de flujo es [IAS 7 de IFRS](https://www.ifrs.org/issued-standards/list-of-standards/ias-7-statement-of-cash-flows.html). La política contable particular de Arco Energy se irá confirmando con su contador.

## Libro financiero de la iteración

- `AccountingAccount` guarda secciones, cuentas y subcuentas. Cada subcuenta puede enlazarse a un cliente o a una cuenta de caja/banco existente.
- `AccountingEntry` y `AccountingLine` guardan pólizas append-only con fecha, folio, descripción, referencia, proyecto opcional y cargos/abonos. Una póliza se acepta únicamente si tiene al menos dos renglones y el total de cargos coincide con el total de abonos.
- Los reportes se calculan desde pólizas publicadas. Corregir una operación financiera agrega una póliza inversa y conserva la original.
- Los saldos existentes de caja/banco, cuentas por cobrar e inventario se copian una vez como saldos de apertura. Ese proceso no cambia caja operativa, cartera ni existencias.
- Las ventas nuevas se contabilizan como efectivo/banco contra ingresos o como cuentas por cobrar del cliente contra ingresos. La cobranza nueva reduce la cuenta del cliente y aumenta caja/banco. Las reversiones crean pólizas opuestas.
- El calendario de cobranza presenta vencimientos y pagos del módulo operativo; al elegir un cliente muestra cargos, abonos y saldo acumulado.
- Un asiento vinculado a proyecto se incluye en el filtro por proyecto de resultados y flujo. El balance general conserva el saldo consolidado de la empresa al corte.

## Alcance contable pendiente de confirmación

La póliza de apertura no reconstruye resultados históricos ni movimientos antiguos del kardex. El consumo de materiales, compras, pagos a proveedores y gastos existentes aún no generan pólizas automáticas en esta iteración. Antes de automatizarlos, el contador debe confirmar las cuentas, fecha de reconocimiento, costo de venta, tratamiento de impuestos y clasificación de cada categoría. Los gastos financieros y personales/otros pueden registrarse en sus cuentas separadas y se presentan después del resultado operativo.

La acción **Registrar movimiento** actualiza únicamente el libro financiero. No muta las operaciones comerciales, órdenes, caja operativa ni existencias.
