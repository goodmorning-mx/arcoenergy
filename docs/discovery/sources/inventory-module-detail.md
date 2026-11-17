# Referencia de inventario — alcance integral de pantallas

Fuente: nueve capturas compartidas por el usuario en el chat de Arco Energy el 17 de noviembre de 2026. Los nombres, cantidades, fechas, folios e importes que aparecen en ellas son datos de la cuenta de referencia; no deben tomarse como configuración, registros ni reglas aprobadas de Arco Energy.

La solicitud literal asociada se conserva en la tarjeta **US-45** y en `ae_history_cards`. Las capturas originales se guardan sin modificación y sus SHA-256 están incorporados a la migración `202611170159`.

## Qué muestra cada pantalla

| N.º / pantalla | Datos observables | Acciones y estados observables |
| --- | --- | --- |
| [01 Productos](inventory-module-detail/01-products.png) | Catálogo agrupado por categoría; código, imagen, nombre, subcategoría, existencia, indicador de nivel, costo, ubicación y estado. | Búsqueda por nombre/código/barras; filtros por categoría y estado; selección múltiple, exportar PDF, nuevo producto y menú contextual por producto. Estados visibles: Activo y nivel OK. El dashboard general anterior a esta iteración muestra alertas bajo mínimo. |
| [02 Entradas](inventory-module-detail/02-entries.png) | Folio, producto, cantidad positiva, proveedor, factura, responsable y fecha/hora. | Conteo de registros, búsqueda por folio/producto y nueva entrada. |
| [03 Salidas](inventory-module-detail/03-exits.png) | Folio, producto, cantidad negativa, proyecto, departamento, responsable y fecha/hora. | Conteo de registros, búsqueda y devolución por movimiento. Una devolución debe dejar el movimiento original rastreable. |
| [04 Kardex](inventory-module-detail/04-kardex.png) | La pantalla inicia con selector de producto y subtítulo “Historial de movimientos por producto”. | Seleccionar producto para consultar su historial. Las columnas y saldo progresivo no son visibles en la captura; se proponen como requisito de trazabilidad y deben confirmarse. |
| [05 Escáner](inventory-module-detail/05-scanner.png) | Producto identificado a partir de un código, implícito en el propósito de la pantalla. | Cambiar entre Cámara y Manual; solicitar permiso del dispositivo; activar cámara; detección automática; seleccionar una acción. Estados iniciales: cámara desactivada/permisos pendientes. |
| [06 Reportes](inventory-module-detail/06-reports.png) | Período, tipo/alcance del reporte, total de productos, bajo stock, agotados, valor total, distribución por categoría, top de productos por salidas y tabla de inventario general. | Cambiar período y alcance; generar reporte mensual. El formato de salida y filtros disponibles deben validarse. |
| [07 Proveedores](inventory-module-detail/07-suppliers.png) | Nombre, contacto, email, teléfono y RFC. | Conteo, búsqueda, nuevo proveedor y menú contextual por proveedor. Preservar los movimientos históricos cuando se cambie o desactive un proveedor. |
| [08 Proyectos](inventory-module-detail/08-projects.png) | Nombre/instalación, folio, cliente, estado, prioridad, avance porcentual, responsable, fecha y resumen económico con monto, gastos, materiales y utilidad. | Buscar, filtrar por estado, abrir agenda, crear proyecto, abrir detalle y registrar gasto de instalación. |
| [09 Configuración](inventory-module-detail/09-settings.png) | Categorías de producto con descripción; pestañas Categorías y Empresa. | Agregar categoría y administrar configuración empresarial. Las operaciones de edición/desactivación no se ven en la imagen. |

## Modelo funcional propuesto para la implementación

La lista siguiente traduce las pantallas a entidades y campos candidatos. No afirma que estos sean los nombres o columnas actuales de la base de datos, ni autoriza eliminar/reemplazar el modelo existente. Implementación debe mapear el alcance al esquema real y conservar compatibilidad con historial y datos actuales.

| Entidad | Campos candidatos necesarios | Estados / reglas a validar |
| --- | --- | --- |
| Producto | id; código interno único; código de barras opcional; nombre; imagen; categoría; subcategoría; unidad; ubicación; costo unitario; stock mínimo; stock actual derivado; activo; fechas y autoría. | Activo/inactivo; existencia OK/baja/agotada derivada de reglas aprobadas. No editar stock sin movimiento trazable. Confirmar costo, unidades y umbral. |
| Categoría | id; nombre; descripción; activa; orden opcional. | Categorías como agrupación de catálogo/reportes; evitar borrado si hay productos dependientes. |
| Movimiento de inventario | id; folio único; tipo; producto; cantidad con signo o dirección explícita; unidad; costo aplicado; fecha efectiva; usuario responsable; motivo/nota; origen y documento; estado; vínculo opcional a movimiento corregido/devolución. | Entrada, salida, devolución, ajuste/merma y reversa son candidatos. Registro contabilizado inmutable: rectificar mediante movimiento compensatorio con actor, fecha y motivo. Permitir borrador/anulado sólo según política. |
| Entrada / recepción | movimiento; proveedor; referencia de factura; fecha de factura; cantidad recibida; responsable; adjunto opcional. | Entrada aumenta inventario; si es a crédito se vincula a cuenta por pagar/proveedor; al contado a caja/banco según reglas contables. |
| Salida / entrega | movimiento; proyecto/orden de trabajo; departamento; responsable que entrega y recibe si aplica; cantidad; nota/adjunto. | Salida consume existencia y se vincula al proyecto/orden de trabajo; devolución o merma crea movimientos vinculados, no borrado. |
| Proveedor | id; nombre/razón social; persona de contacto; email; teléfono; RFC; datos de pago opcionales sólo si se autorizan; activo; fechas/autoría. | Activo/inactivo. No eliminar si tiene compras, facturas o pagos; las correcciones conservan historial. |
| Proyecto / instalación | id; folio; nombre; cliente; ubicación; contacto opcional; estado; prioridad; porcentaje de avance; responsable; fecha; monto/ingreso; gastos; costo de materiales; utilidad calculada; vínculo a orden de trabajo. | Captura visible: activo, pendiente, en proceso; prioridad baja/media. Confirmar flujo completo, fórmula del avance y cierre. |
| Gasto de proyecto | id; proyecto; concepto/categoría; importe; moneda; fecha; autor; comprobante opcional; estado y nota. | El gasto se refleja en el resumen del proyecto; distinguir viáticos, gasto operativo y costo directo conforme a contabilidad. |
| Cuenta/empresa | razón social, datos fiscales, contacto, moneda y preferencias de operación que se acuerden. | La captura sólo confirma una pestaña “Empresa”; no muestra campos ni permite deducir valores. |
| Reporte | período; alcance/tipo; filtros; fecha de generación; usuario; formato/archivo. | Mostrar métricas conciliables con movimientos; define reporte mensual y alcance general. No guardar agregados como fuente de verdad si pueden calcularse de registros. |

## Flujo y relaciones entre módulos

1. El producto pertenece a una categoría y tiene uno o varios códigos de búsqueda; la existencia resulta de su saldo inicial y sus movimientos confirmados.
2. Una recepción genera una entrada y conserva proveedor/factura. El evento se relaciona con la compra y con su contrapartida financiera cuando contabilidad determine el flujo.
3. Una venta/proyecto aprobado produce una orden de trabajo. La entrega de materiales se registra como salida vinculada a esa orden y al proyecto, con responsable y fecha.
4. Devoluciones, mermas, daños y correcciones dejan trazabilidad con el movimiento original; reportes y kardex incorporan el efecto según fecha/regla aprobada.
5. El kardex, dashboard, alertas y reportes leen las mismas fuentes de movimiento y muestran saldos conciliables. El usuario puede abrir desde métricas/filas hacia el detalle con permisos adecuados.
6. El escáner resuelve un producto y propone la acción; la persona confirma producto, cantidad y destino antes de crear el movimiento. Cámara, permisos y modo offline requieren pruebas en dispositivos reales.

## Preguntas para definición con stakeholders

- ¿El código interno y el código de barras son uno o varios? ¿Qué campos de producto son obligatorios y quién mantiene el catálogo?
- ¿Qué unidades, ubicaciones, subcategorías y categorías se usan? ¿Stock mínimo por producto, almacén o ambos?
- ¿Qué método de valuación se usa para costo de almacén y costo de venta: promedio, PEPS u otro? ¿Cómo tratar ajustes de costo y redondeo?
- ¿Se permite stock negativo? ¿Quién autoriza entradas, salidas, ajustes, devoluciones, mermas, cancelaciones y reversiones?
- ¿Qué tipos de entrada/salida existen, cómo se generan folios y qué adjuntos son obligatorios? ¿Una devolución admite parcialidades?
- ¿Cómo se enlazan compras a proveedores/caja/banco/proveedores por pagar, y las salidas a venta/orden de trabajo/proyecto/costo directo?
- ¿Cuáles son estados, roles, permisos y transiciones de producto, movimiento, proyecto y gasto? ¿Quién puede ver costos y utilidad?
- ¿Cómo se calcula monto, costo de materiales, gastos, utilidad, avance y alertas? ¿Qué fecha/período se usa para los reportes diarios/mensuales?
- ¿Qué debe producir “Exportar PDF” y “Reporte mensual”? ¿Se almacenarán archivos en Drive? Definir carpeta, permisos y retención.
- ¿Qué acciones ofrece cada menú contextual? ¿Hay almacenes múltiples, existencias reservadas o transferencias entre almacenes?
- ¿El escáner debe funcionar sin conexión? ¿Qué comportamiento se espera si no existe el código o hay varias coincidencias?
- ¿Quién es el autor solicitante de esta tarjeta? El nombre visible de la sesión/screenshot no se utiliza para inferirlo.

## Implementación v1 — iteración 160

La captura se conserva como referencia visual; la app no copia números, productos ni usuarios de las imágenes. En el CRM, `/crm/` abre un módulo con navegación interna oscura, barra superior y secciones propias:

- **Dashboard:** métricas conectadas a movimientos/artículos reales, gráfica de siete días, stock bajo o agotado y actividad reciente.
- **Inventario:** catálogo por categoría, búsqueda por nombre/código/barcode, estado, filtros, ficha editable, imagen URL, unidad, ubicación, mínimo, costo sujeto a permiso y exportación mediante impresión.
- **Entradas:** historial con folio, artículo, cantidad, proveedor/fuente, factura, responsable y fecha. Las compras se capturan desde Compras/CxP para conservar sus enlaces de factura, proveedor y pagos; la recepción manual bajo permiso de inventario también conserva proveedor/factura en el movimiento.
- **Salidas:** historial con folio, artículo, cantidad, proyecto/orden, departamento, autor y fecha. La devolución se registra contra la salida original e identifica si el material es reutilizable o dañado.
- **Kardex:** selector de producto y búsqueda histórica de movimientos.
- **Escáner:** cámara trasera con detección compatible cuando el navegador ofrece `BarcodeDetector`, y fallback por código/barcode escrito.
- **Reportes:** período mensual, artículos totales, stock bajo/agotado, valor protegido por permiso, distribución por categoría, productos con más salidas y tabla general. La acción de reporte abre el diálogo de impresión del navegador.
- **Configuración:** categorías persistentes con descripción, contador de artículos y estado activo/inactivo. La edición/desactivación conserva productos e historial. La pestaña Empresa se muestra informativa mientras se acuerdan campos y fuente de datos.
- **Relaciones:** proveedor y costos se enlazan con el catálogo/compras existentes; movimientos enlazan artículo, instalación/orden, línea de compra y material de la orden. Actor se mantiene como identidad/email en el mismo patrón de auditoría existente; cada movimiento recibe folio único.

Las reglas financieras de compras, pagos, saldos, proyectos y gastos continúan perteneciendo a sus módulos existentes. Se protege consulta de costos y artículos inactivos con permisos del servidor; la UI refleja estos permisos. No se eliminan movimientos ni proveedores con dependencias.

**Verificación local:** `crm npm run build`; pruebas de backend en `backend/tests/test_inventory_module_foundation.py`, `test_inventory_catalog.py`, `test_inventory_kardex.py`, `test_inventory_work_order_issue.py` y `test_inventory_returns.py`. Capturas visuales con el browser integrado están pendientes porque no hay browser conectado en este entorno.

**Pendiente de stakeholders:** confirmar valuación/método de costo, límites y permisos definitivos, reglas de stock negativo, períodos/umbrales, campos de Empresa, política de exportación/Drive, múltiples almacenes y ciclo real de recepción/entrega. Esta entrega no marca US-44/US-45 como `Finished`; queda para revisión del usuario en History Cards.

## Alcance y cautelas

Las capturas sirven para descubrir pantallas/campos y flujos; no contienen autorización para copiar datos del sistema de referencia como registros productivos. US-44 sigue siendo el detalle del dashboard y alertas. Las reglas contables/operativas previas de US-19, US-20, US-26–US-30, US-32, US-36 y US-38 se mantienen como dependencias, no se redefinen por inferencia visual.
