# Comparación del sistema de César con la solicitud del contador

## Fuentes y alcance

La solicitud se revisó en el Word “COMENTARIOS Y MEJORAS PARA EL SISTEMA DE ARCO ENERGY” y en su versión PDF “MEJORAS AL SISTEMA ARCO ENERGY”. Ambos contienen la misma estructura de diez apartados; el PDF incluye la captura del menú y dashboard de ARCO ENERGY Inventario en Base44. La comparación vigente describe CRM/PWA/API de ArcoEnergy en DEV, aplicación `4de38c56278b194373f9775ef866c20e8073e887`, esquema `202611100082`. La UI de origen de César no se pudo consultar; la imagen del PDF sirve como referencia visual parcial. No se agregan reglas contables que el contador todavía deba definir.

## Matriz de cobertura

| Solicitud del contador | Interfaz o función existente | Estado frente a la solicitud | Diferencias que siguen abiertas |
| --- | --- | --- | --- |
| Ventas con fecha, cliente, código de proyecto, domicilio, subtotal/impuestos y pago contado/crédito/Plan 24 | CRM: Ventas / OT; propuesta aprobada, venta, proyecto, orden, reserva, caja en contado o cartera en crédito | Parcial | No existe Plan 24/tanda. Subtotal e impuestos fiscales, pagos mixtos y fecha comercial distinta del registro requieren definición. |
| Clientes, deuda y captura de cobranza con fecha, importe y cuenta | CRM: Clientes, Cobranza y cuenta afectada; calendario por cuota, pagos, recordatorios manuales y reversas enlazadas | Parcial funcional | No se generan calendarios desde fórmulas de financiamiento aprobadas; no existe Plan 24 ni aplicación automática de un pago entre cuotas. |
| Gastos no relacionados con mercancía, con fecha, categoría, cuenta y proyecto | CRM/PWA: fecha, importe, concepto, categoría, tipo fijo/variable/sin clasificar, cuenta, proyecto y comprobante cuando Drive esté disponible | Parcial funcional | Contabilidad debe validar categorías, casos mixtos, autorización y tratamiento fiscal; no es contabilidad de partida doble. |
| Saldos de efectivo y débito con reporte por cuenta | CRM: Caja / bancos, saldo derivado, detalle por cuenta, transferencias y correcciones enlazadas | Funcional básico | No hay conciliación contra estados bancarios ni corte formal de efectivo aprobado. |
| Dashboard con stock, pagos próximos, estados de cuenta, gráficas y oportunidades | CRM: Resumen con métricas por permisos, alertas de stock/cobranza/cuentas y, desde Iteración 70, gráficas de movimientos de almacén por siete días y disponibilidad de stock; destaca vencidos y paquetes pendientes de aprobación | Parcial funcional | Las gráficas cuentan movimientos, no cantidades ni costo. Falta validar métricas/umbrales con administración y contador y acordar oportunidades adicionales. |
| Inventario con clave, QR/barras, descripción, categoría/subcategoría, marca, modelo, proveedor y unidad | CRM: catálogo con ficha, código capturable y etiqueta QR imprimible; PWA: existencias, reservas por orden y lectura por cámara/captura; alta rápida desde compras | Parcial funcional | La etiqueta usa el código del artículo o su ID técnico; no hay folio corto de artículo ni conversión entre unidades. Falta probar lectores/impresoras físicos y validar taxonomía con almacén. |
| Entradas de mercancía con proveedor, factura, varios artículos, costo y forma de pago | CRM: Compras/CxP, líneas múltiples, alta rápida de material, contado/crédito, pago y factura; propuesta revisable desde XML CFDI; archivo guardado/descargado si Drive está conectado | Parcial funcional | PDF/fotografía no se interpreta; distribución de impuestos, fletes y descuentos globales requiere reglas contables. Verificar conexión real y retención de Drive en DEV. |
| Salidas por orden de servicio, devolución de sobrantes y alerta de bajo inventario | CRM: salida ligada a solicitud/orden y stock reservado; PWA: consumo, devolución/merma ligada a salida; alertas push opcionales al responsable | Parcial funcional | No se importa el formato externo manuscrito/escaneado de orden; push requiere suscripción en el dispositivo y validar operación física. |
| Kardex por producto y rango de fechas | CRM: artículo, intervalo, paginación y descarga CSV completa | Funcional básico | Costos históricos faltantes se señalan, pero requieren movimientos reales y revisión del método de costeo. |
| Reportes de stock, entradas, salidas, clientes, proveedores, proyectos y gastos | CRM: stock físico/reservado/disponible y bajo mínimo, kardex, reportes operativos y resultado preliminar por mes/proyecto con gastos fijos/variables, devoluciones/bonificaciones | Parcial funcional | El reporte de resultados no es estado financiero oficial; falta validación contable y confirmar si hacen falta reportes o filtros separados. |
| Proveedores con contado/crédito, plazo, deuda y pago | CRM: proveedores, términos y plazo, compras, CxP y pagos ligados a cuenta y movimientos; corrección conserva historial | Funcional básico | Falta conciliación bancaria y aprobación de políticas de factura, fletes/descuentos y correcciones complejas. |
| Proyectos con código único para relacionar gastos y salidas | CRM: entidad Proyecto separada con código único; órdenes y gastos pueden relacionarse y el reporte agrupa varias órdenes | Parcial funcional | Administración debe confirmar formato comercial del código y si una instalación real puede tener varias órdenes. |

## Decisiones pendientes del stakeholder

- Definir qué significa Plan 24/tanda: anticipo, calendario de pagos, titularidad y tratamiento de incumplimientos.
- Aprobar el formato y ciclo de vida del código de proyecto, incluyendo su relación con cotización, venta y orden.
- Definir impuestos, pagos mixtos, valuación/costeo, clasificación de gastos y reportes contables oficiales.
- Entregar el formato vigente de orden de servicio y confirmar qué campos deben capturarse al escanearlo.
- Definir umbrales, destinatarios y canal para las notificaciones de reabasto.
- Aprobar si el código técnico de artículo basta para las etiquetas QR o si almacén requiere una clave corta adicional.

## Validación visual de las fuentes

El PDF fuente tiene cuatro páginas; se revisaron visualmente sus páginas, incluido el menú/dashboard de referencia en la primera página, y se cotejó el texto con la transcripción del Word. La imagen muestra Dashboard, Inventario, Entradas, Salidas, Kardex, Escáner, Reportes, Proveedores, Proyectos, Usuarios y Configuración. La solicitud escrita detalla diez apartados funcionales; no especifica comportamiento de Usuarios ni Configuración.

## Revisión actual de DEV — 2026-11-11

La API DEV informa commit `b5740b6232445af2d066e5e4a5e54b12a3251049` y esquema `202611110124`. Web, PWA, CRM y `/health` responden HTTP 200. El menú del CRM en el código de esa release expone Inicio, Clientes, Cotizaciones, Seguimientos, Ventas, Instalaciones, Inventario, Compras, Proveedores, Gastos, Cuentas, Reportes, Proyectos, Catálogo, Historial y Equipo. Esta evidencia confirma rutas/recursos publicados; no sustituye una revisión visual de navegador ni una comparación con la instancia viva de César.

| Sección visible en la referencia Base44 | Sección actual en CRM/PWA | Comparación y brecha concreta |
| --- | --- | --- |
| Dashboard | CRM: Inicio y Reportes | Tarjetas y alertas de operación, más métricas por permiso. Los indicadores/umbrales requieren validación administrativa y contable. |
| Inventario | CRM: Inventario; PWA: Inventario | Catálogo descriptivo, disponibilidad/reservas, mínimos, responsable de reabasto y etiqueta QR imprimible. Confirmar unidades, etiquetas y existencias con almacén. |
| Entradas | CRM: Compras | Compra multirrenglón, proveedor, factura/XML revisable, pago/crédito y actualización de existencias/cuentas. Faltan reglas de impuestos/fletes/descuentos y Drive autorizado. |
| Salidas | CRM: Instalaciones; PWA: Material/gasto | Orden de trabajo con solicitud, reserva/salida física, consumo y devolución enlazados. Falta validar el circuito físico y aprobar excepciones contables. |
| Kardex | CRM: Inventario → Historial de almacén | Filtro por artículo/fecha, paginación y CSV completo; costos según permiso. El rendimiento y costos históricos requieren datos reales. |
| Escáner | PWA: Inventario; CRM: etiqueta/código | Cámara, captura manual y lector tipo teclado tienen fallback. Falta probar cámara, etiqueta y modo avión en teléfonos reales. |
| Reportes | CRM: Reportes y Cuentas | Reporte operativo, caja/cartera, almacén, gastos y resultado preliminar por periodo/proyecto. No equivale a estados financieros aprobados. |
| Proveedores | CRM: Proveedores y Compras | Proveedor, términos, plazo, saldos por pagar y pagos trazables. Aún faltan conciliación y políticas contables de documentos/costos. |
| Proyectos | CRM: Proyectos e Instalaciones | Entidad de proyecto con código y órdenes/gastos asociados. Falta que administración confirme el formato y cardinalidad comercial. |
| Usuarios | CRM: Equipo | Roles y permisos por endpoint operativos; faltan cuentas autorizadas de todo el personal y validación del alcance con cada rol. |
| Configuración | Catálogo, Equipo, Cuentas y configuración organizacional | Funciones repartidas por área; no hay una sección única de configuración como la referencia. Confirmar si hace falta para el cliente. |

La comparación se limita al menú y las secciones visibles en la captura del PDF y a las funciones expresadas en el Word. No afirma paridad con pantallas que no aparecen en la referencia ni con la instancia privada de César. Para completar la comparación visual y de comportamiento se necesita acceso al sistema actual o capturas navegables de sus secciones.
