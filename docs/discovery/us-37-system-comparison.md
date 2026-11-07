# Comparación del sistema de César con la solicitud del contador

## Fuentes y alcance

La solicitud se revisó en el Word “COMENTARIOS Y MEJORAS PARA EL SISTEMA DE ARCO ENERGY” y en su versión PDF “MEJORAS AL SISTEMA ARCO ENERGY”. Ambos contienen la misma estructura de diez apartados y una captura del menú de ARCO ENERGY Inventario en Base44. Esta comparación describe el alcance presente en el CRM/PWA de ArcoEnergy en DEV, commit `b8ef038`; no agrega reglas contables que el contador todavía debe definir.

## Matriz de cobertura

| Solicitud del contador | Interfaz o función existente | Estado frente a la solicitud | Diferencias que siguen abiertas |
| --- | --- | --- | --- |
| Ventas con fecha, cliente, código de proyecto, domicilio, subtotal/impuestos y pago contado/crédito/Plan 24 | CRM: Ventas / OT; propuestas aprobadas crean venta, orden y reserva de materiales; contado crea entrada de caja/banco; crédito crea cuenta por cobrar | Parcial | No hay tipo de venta Plan 24/tanda ni plan de cuotas. El folio de venta y el folio de orden no son una entidad de proyecto independiente. La fecha comercial se deriva del registro; impuestos, subtotal fiscal y pagos mixtos no están definidos. |
| Clientes, deuda y captura de cobranza con fecha, importe y cuenta | CRM: Clientes y Cobranza; los abonos se enlazan a la cuenta y actualizan el saldo pendiente | Funcional básico | Las cuotas pueden registrarse manualmente; todavía no se generan desde reglas de financiamiento ni se distribuye automáticamente un pago entre cuotas. No se modela Plan 24. |
| Gastos no relacionados con mercancía, con fecha, categoría, cuenta y proyecto | CRM: Gastos; importe, fecha, categoría, cuenta y orden/proyecto opcional; el gasto genera salida de caja/banco si se paga desde una cuenta | Funcional básico | Las categorías se capturan de forma abierta; el contador debe validar tratamiento contable, autorización, impuestos y clasificación de gastos. |
| Saldos de efectivo y débito con reporte por cuenta | CRM: Caja / bancos; cuentas, movimientos y detalle por cuenta | Funcional básico | La conciliación bancaria y el corte formal de efectivo no están implementados. |
| Dashboard con stock, pagos próximos, estados de cuenta, gráficas y oportunidades | CRM: Resumen y reportes operativos muestran alertas de stock bajo, cobranza vencida/próxima y saldos | Parcial funcional | Falta validar indicadores/umbrales con administración y contador, gráficas acordadas y flujo de efectivo por periodo. |
| Inventario con clave, QR/barras, descripción, categoría/subcategoría, marca, modelo, proveedor y unidad | CRM: Catálogo de materiales; PWA: inventario, disponibilidad por orden y búsqueda QR/barras con cámara o captura | Parcial funcional | El QR/barcode se captura, no se genera una etiqueta automáticamente. Falta subcategoría, conversiones de unidad y crear artículos desde el formulario de compra. |
| Entradas de mercancía con proveedor, factura, varios artículos, costo y forma de pago | CRM: Compras / CxP; compras de múltiples líneas, contado/crédito, pago inicial y saldo a proveedor; lectura revisable de CFDI XML | Funcional básico | La factura en imagen/PDF no se interpreta; el XML no se conserva. Los impuestos, fletes, descuentos y facturas relacionadas requieren política contable. |
| Salidas por orden de servicio, devolución de sobrantes y alerta de bajo inventario | CRM: Ventas / OT; PWA: materiales solicitados, consumos, devoluciones y mermas ligados a la orden; CRM: alertas de stock mínimo | Parcial funcional | No se carga/escanea el formato externo de orden de servicio; el flujo requiere crear la venta/orden en el sistema. La alerta actual es visible en CRM, no una notificación de reabasto. |
| Kardex por producto y rango de fechas | CRM: Kardex con filtro por artículo/fechas y exportación CSV | Funcional básico | La consulta se limita a 500 movimientos; falta paginación y valoración histórica completa. |
| Reportes de stock, entradas, salidas, clientes, proveedores, proyectos y gastos | CRM: Reportes operativos y de rentabilidad por periodo y orden | Parcial funcional | No todos los reportes son vistas independientes; faltan paginación, reportes de proyectos con entidad/código propio y fórmulas validadas para estados de resultados. |
| Proveedores con contado/crédito, plazo, deuda y pago | CRM: Proveedores y Compras / CxP; condiciones y pagos quedan relacionados con compra, proveedor y cuenta de caja/banco | Funcional básico | Faltan conciliación y validación del contador sobre saldos y tratamiento de correcciones de compra completas. |
| Proyectos con código único para relacionar gastos y salidas | CRM: ventas y órdenes de trabajo folian la operación y relacionan materiales/gastos | Parcial | No existe aún una entidad Proyecto separada de venta/cotización/orden. El formato de código de proyecto debe acordarse con el stakeholder. |

## Decisiones pendientes del stakeholder

- Definir qué significa Plan 24/tanda: anticipo, calendario de pagos, titularidad y tratamiento de incumplimientos.
- Aprobar el formato y ciclo de vida del código de proyecto, incluyendo su relación con cotización, venta y orden.
- Definir impuestos, pagos mixtos, valuación/costeo, clasificación de gastos y reportes contables oficiales.
- Entregar el formato vigente de orden de servicio y confirmar qué campos deben capturarse al escanearlo.
- Definir umbrales, destinatarios y canal para las notificaciones de reabasto.

## Validación visual de las fuentes

El PDF fuente tiene cuatro páginas y se inspeccionaron todas. La conversión visual del Word no pudo ejecutarse en este entorno porque falta la dependencia `pdf2image`; el texto extraído del Word coincide con el contenido del PDF. Esta limitación de render del archivo fuente no afecta la matriz funcional.
