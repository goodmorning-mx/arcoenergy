# Arco Energy — Registro de history user story cards

- **Propósito:** conservar los hallazgos por stakeholder, fuente e iteración para poder revisar cómo evolucionan sin borrar lo que se dijo antes.
- **Estado:** registro documental de descubrimiento; todavía no es una base de datos funcional ni un backlog aprobado.
- **Cuidado con la reconstrucción:** US-1 a US-34 se reconstituyen aquí a partir de mensajes, fuentes y los resúmenes disponibles en la conversación. Los IDs US-15 a US-32 se asignan a capacidades explícitas del Word del contador para recuperar el rango histórico, pero no se cuenta con una exportación de las tarjetas originales que confirme su título/texto exactos. Deben validarse en una próxima iteración.
- **Regla de evolución:** agregar nuevas versiones/iteraciones relacionadas; no reemplazar la fuente original. Las reglas contables pendientes no se deben tratar como comportamiento aprobado.

## Iteración 1 — Requerimientos de Goito Profugo

**Stakeholder:** Goito Profugo. **Fuente:** mensajes de WhatsApp compartidos en esta conversación. Las tarjetas reflejan su solicitud; sus criterios no implican que la funcionalidad exista.

### US-1 — Cotizar paquetes solares manualmente

Como vendedor, quiero cotizar desde celular o computadora eligiendo un paquete de paneles, para generar una propuesta con los datos vigentes del negocio.

- La administración puede actualizar periódicamente paquetes de 4 a 20 paneles, precio, marca y potencia.
- La estructura se mantiene predefinida.
- El vendedor captura cliente, lugar de instalación, cantidad de paneles, inversor y forma de pago predefinida.
- La relación entre cantidad de paneles e inversor se configura/valida según las reglas del negocio.
- **Pendiente:** catálogo y fórmula de precio exactos; especificación de inversores por tamaño.

### US-2 — Cotizar automáticamente desde el recibo de electricidad

Como vendedor, quiero subir el recibo en PDF para que el sistema calcule una propuesta automáticamente.

- La carga del recibo inicia un cálculo y presenta el resultado para revisión.
- **Prioridad indicada:** modo avanzado para más adelante.
- **Pendiente:** datos a extraer, fórmula técnica, validación humana y tratamiento de recibos ilegibles.

### US-3 — Foliar, guardar y compartir la cotización

Como vendedor, quiero generar una cotización PDF con folio, guardarla en Drive y compartirla por WhatsApp con el cliente con quien ya tengo una conversación abierta.

- Disponible desde app o computadora.
- El PDF se genera automáticamente al terminar la cotización.
- Se ofrece una acción para compartirlo por WhatsApp.
- **Pendiente:** formato del folio, estructura de Drive y si WhatsApp será enlace compartido o integración API.

### US-4 — Programar seguimiento de prospectos/clientes

Como vendedor, quiero programar cuándo volver a contactar a una persona después de sus comentarios sobre una propuesta y registrar notas de bitácora.

- Opciones mencionadas: 3, 7, 15, 30 días o fecha/comentario abierto.
- Registrar comentarios e historial de seguimiento.
- **Pendiente:** alertas, asignación de responsable y canales.

### US-5 — Preparar contratos y pagarés con datos de identificaciones

Como administrador, quiero generar contrato y pagaré usando fotos del INE del titular y, para financiamiento, del responsable solidario.

- La generación debe distinguir contado/financiamiento y titular/responsable solidario.
- **Pendiente:** plantillas, campos extraídos, revisión de identidad, privacidad y retención documental.

### US-6 — Firma electrónica con alternativa física

Como cliente, quiero firmar en pantalla y realizar una verificación facial para poder formalizar el documento digitalmente; si no se completa, se conserva el proceso físico.

- Firma táctil y verificación propuesta por el stakeholder.
- Alternativa de firma física.
- **Pendiente:** proveedor, validez y consentimiento aplicables, controles antifraude y flujo de excepción. No se asume que el escaneo facial esté aprobado o implementado.

### US-7 — Asignar instalaciones a los instaladores

Como coordinador/administrador, quiero asignar una instalación y notificar al equipo de campo con la ubicación y datos necesarios del cliente.

- La asignación incluye lugar, nombre, teléfono y correo del cliente, según lo solicitado.
- El instalador recibe notificación de que tiene una instalación.
- **Pendiente:** calendario, aceptación, estados y límites de acceso a datos del cliente.

### US-8 — Consultar existencias antes de instalar

Como instalador, quiero consultar el stock desde la app para saber si los materiales requeridos para una instalación están disponibles.

- La consulta se relaciona con la instalación/orden y muestra disponibilidad de materiales.
- **Pendiente:** reserva de materiales y tratamiento de faltantes.

### US-9 — Registrar materiales utilizados en campo

Como instalador, quiero registrar desde la app el material gastado y al final del día confirmar las cantidades de manera intuitiva, para mantener el inventario actualizado.

- Captura manual sencilla de materiales y cantidades.
- Relación con instalación/proyecto.
- **Pendiente:** confirmar si el descuento se hace al entregar, consumir o aprobar el reporte.

### US-10 — Registrar viáticos y gastos de instalación

Como instalador, quiero registrar viáticos y otros gastos en la app y asociarlos al proyecto.

- Capturar importe, tipo y proyecto.
- **Pendiente:** comprobantes, categorías y flujo de aprobación.

### US-11 — Administrar pagos financiados y enviar recordatorios

Como encargado de cuentas, quiero consultar quién debe, cuánto, bajo qué forma paga y enviar mensajes predefinidos sobre pagos próximos, del día o atrasados.

- Acceso rápido a mensajes de recordatorio.
- Control de saldos y modalidad de pago.
- **Pendiente:** calendario, mora, plantillas y canal de envío.

### US-12 — Controlar materiales y costos directos

Como administrador, quiero llevar el control de materiales y costos directos para conocer el costo de cada operación/proyecto.

- **Pendiente:** método de costeo y relación con inventario/órdenes.

### US-13 — Guardar la información del sistema en Drive

Como equipo, queremos que la información/documentación del sistema se almacene en Drive.

- **Pendiente:** distinguir archivos/documentos de datos operacionales; definir permisos, estructura, sincronización, respaldo y fuente autoritativa.

### US-14 — Restringir información según privilegios

Como administrador, quiero que cada usuario tenga privilegios para que vea y ejecute solamente las funciones autorizadas.

- **Pendiente:** matriz de permisos por rol y alcance por proyecto/organización.

## Iteración 2 — Solicitud del contador en Word/PDF

**Stakeholder:** contador (Mario Groso identificado posteriormente en la conversación). **Fuentes:** `COMENTARIOS Y MEJORAS PARA EL SISTEMA DE ARCO ENERGY.docx` y `MEJORAS AL SISTEMA ARCO ENERGY.pdf`, documento de comentarios sobre el borrador Base44. El PDF se revisó como contenido equivalente del Word.

### US-15 — Registrar ventas

Como contador/administrador, quiero registrar las ventas con sus datos principales, para llevar control de ingresos y proyectos vendidos.

- Capturar fecha del proyecto, cliente, código y domicilio del proyecto.
- Capturar subtotal, impuestos y valor de venta.
- Registrar si es contado, crédito o parte del plan 24 (tanda de paneles).
- **Pendiente:** reglas de impuestos, pagos mixtos y efecto exacto en inventario/cuentas.

### US-16 — Consultar saldo y registrar cobranza de clientes

Como encargado de cobranza, quiero consultar cada cliente y su deuda actual y capturar pagos/abonos.

- Capturar monto, fecha y si el pago fue efectivo o entró a una cuenta de débito.
- Relacionar el pago con cliente/deuda.
- El movimiento debe reflejarse en flujo de efectivo y reporte de cuenta correspondiente.
- **Pendiente:** aplicación de pagos a varias deudas, pagos parciales, mora y cancelaciones.

### US-17 — Registrar gastos operativos

Como contador, quiero registrar gastos que no correspondan a adquisición de mercancías, para analizar costos y salidas de dinero.

- Capturar fecha, monto, descripción y categoría (por ejemplo nómina, combustible, impuestos, intereses, préstamos, mantenimiento o servicios).
- Asociar la cuenta o efectivo usado.
- Asociar código de proyecto cuando sea gasto directo.
- **Pendiente:** catálogo final de categorías y aprobaciones.

### US-18 — Consultar cuentas de débito y efectivo

Como administrador/contador, quiero ver los saldos de cuentas de débito y efectivo y abrir el reporte de cada cuenta, para tomar decisiones de caja.

- Mostrar cuentas y montos disponibles.
- Permitir navegar al reporte de movimientos de cada cuenta.
- **Pendiente:** conciliación, saldos iniciales y permisos.

### US-19 — Ver alertas y resumen en el dashboard

Como administrador/contador, quiero ver en el dashboard la información y alertas más relevantes del negocio.

- Mostrar estado de inventario y artículos con stock bajo.
- Mostrar pagos/cobranzas próximos a vencer.
- Mostrar estatus de cuentas de débito.
- Incluir gráficas, resumen de reportes y áreas de oportunidad.
- **Pendiente:** definición de indicadores, fórmulas y umbrales.

### US-20 — Mantener catálogo de inventario identificable

Como responsable de almacén, quiero registrar y consultar artículos con clave y datos descriptivos, para controlar existencias e identificarlos.

- Capturar nombre, descripción, categoría/subcategoría, marca, modelo, proveedor y unidad de medida.
- Asignar clave y código QR o de barras para identificación.
- Permitir alta de un artículo desde el flujo de entrada si todavía no existe.
- **Pendiente:** unidades, conversiones, almacenes y política para códigos.

### US-21 — Registrar entradas de compra con varios artículos

Como responsable de almacén/contador, quiero registrar una entrada con proveedor, artículos y condiciones de pago para actualizar almacén y saldos relacionados.

- Capturar proveedor, artículo/código, factura si existe, costo unitario, cantidad y medio/cuenta o crédito.
- Agregar varios artículos en una misma orden de entrada.
- Ofrecer alta de artículo desde el formulario.
- **Pendiente:** impuestos, fletes, descuentos y efecto contable detallado.

### US-22 — Capturar datos de entrada desde factura

Como responsable de almacén/contador, quiero cargar una factura (archivo/XML o fotografía) para facilitar el registro de los artículos recibidos.

- La captura asistida presenta datos para revisión antes de confirmar la entrada.
- **Alcance avanzado solicitado:** lectura automática; no se considera necesaria para el primer corte.
- **Pendiente:** formatos, OCR, CFDI/XML y validación de cantidades/precios.

### US-23 — Devolver sobrantes al almacén

Como instalador/responsable de almacén, quiero registrar artículos sobrantes devueltos después de una instalación para que regresen a existencias y no carguen indebidamente al costo del proyecto.

- Asociar devolución con proyecto/orden y artículo/cantidad.
- Conservar trazabilidad de la salida original y su devolución.
- **Pendiente:** condiciones del material y cálculo de costo.

### US-24 — Registrar salidas de materiales por orden/proyecto

Como responsable de almacén, quiero registrar materiales que salen conforme a órdenes de servicio y asociarlos al proyecto para costearlo.

- Capturar artículo, cantidad y costo asociado.
- Relacionar la salida con orden de servicio/proyecto.
- Permitir registrar devolución asociada.
- **Pendiente:** momento del descuento de stock y distinción entre material solicitado, entregado y consumido.

### US-25 — Facilitar salida desde la orden de servicio

Como responsable de almacén, quiero cargar o escanear la orden de servicio (fotografía o PDF) para iniciar el registro de materiales que salen y sus devoluciones.

- La orden debe permitir revisar artículos y cantidades antes de confirmar.
- **Pendiente:** calidad de reconocimiento y aprobación del responsable.

### US-26 — Recibir alertas de stock bajo

Como responsable de almacén, quiero recibir notificaciones cuando un artículo esté agotándose o tenga existencia baja para solicitar reposición.

- Configurar/ver nivel de stock bajo.
- Relacionar alerta con artículo y existencia.
- **Pendiente:** umbrales y destinatarios.

### US-27 — Consultar kardex por intervalo de fechas

Como responsable de almacén/contador, quiero revisar los movimientos históricos por producto y filtrar desde/hasta una fecha.

- Mostrar movimientos del producto dentro del rango seleccionado.
- **Pendiente:** valoración y filtros adicionales.

### US-28 — Identificar artículos con cámara

Como usuario de almacén/campo, quiero escanear QR o código de barras con la cámara del teléfono para identificar un artículo.

- El código se asigna o registra al dar de alta el artículo.
- La lectura lleva al artículo correspondiente.
- **Pendiente:** lectores soportados y funcionamiento sin conexión.

### US-29 — Consultar reportes de operación

Como administrador/contador, quiero consultar reportes de stock y actividad para revisar el estado del negocio.

- Stock disponible en gráfica y tabla detallada.
- Reportes de entradas, salidas, clientes, proveedores, proyectos/estatus y gastos varios.
- **Pendiente:** filtros, exportación y fórmulas de cada reporte.

### US-30 — Administrar proveedores y sus condiciones

Como contador, quiero ver proveedores, estatus, condiciones de contado/crédito, días de crédito y saldos pendientes.

- Listar y dar de alta proveedores.
- **Pendiente:** campos obligatorios y reglas de vencimiento.

### US-31 — Relacionar compras, proveedores y pagos

Como contador, quiero que las entradas por compra se relacionen con el proveedor y registren si la compra fue a crédito o contado; también quiero registrar pagos a proveedores.

- Entrada a crédito actualiza el saldo del proveedor correspondiente.
- Pago registra fecha, monto y cuenta/medio (tarjeta, efectivo o transferencia).
- **Pendiente:** pagos parciales, aplicación a facturas, correcciones y conciliación.

### US-32 — Administrar proyectos y su folio

Como administrador/contador, quiero registrar proyectos con código único para relacionar gastos y salidas de almacén y mejorar el costeo.

- Alta de proyecto genera código/folio.
- Gastos y materiales se vinculan al proyecto.
- **Pendiente:** formato del código, estados, cliente, orden e integración con ventas.

## Iteración 3 — Audio del contador

**Stakeholder:** contador, identificado en el hilo como remitente de los audios de WhatsApp. **Fuentes:** tres OGG de WhatsApp enviados el 2 de noviembre de 2026. Transcripción local guardada fuera del repositorio; se registran aquí los hallazgos, no el audio ni la transcripción literal completa.

### US-33 — Reflejar efectos relacionados de una operación

Como contador, quiero que al registrar una operación sus efectos relacionados se reflejen en las áreas correspondientes, para que el costeo y los saldos sean coherentes.

- Una entrada de inventario debe relacionarse con el proveedor correspondiente.
- Un pago en efectivo o transferencia afecta efectivo o cuenta bancaria, según el medio.
- **Fuente/certeza:** audio `WhatsApp Ptt 2026-11-02 at 4.16.19 PM.ogg`; se oyó “entradas alimentarios”, posiblemente “inventario”, por validar con el contador.

### US-34 — Registrar movimientos de efectivo y cuentas

Como contador, quiero registrar movimientos de efectivo y cuentas para llevar control y costeo más preciso.

- Registrar movimientos y cuenta afectada con detalle suficiente para consulta.
- **Fuente/certeza:** audio `WhatsApp Ptt 2026-11-02 at 4.16.19 PM.ogg`.
- **Nota:** audio `4.15.39 PM` termina con una frase incompleta/ruidosa sobre relacionar opciones; no se reconstruye el contenido ausente.
- **Nota de descubrimiento (no historia):** audio `4.15.14 PM` pide revisar sección por sección el sistema Base44/César y tomar notas antes de aplicar las mejoras escritas.

## Iteración 4 — Definición contable y de operación con Mario Groso

Las tarjetas US-35 a US-38 están descritas con mayor detalle en [la iteración de plan de producto](iteration-2026-11-06-product-design-plan.md), donde también constan su procedencia, reglas provisionales y criterios abiertos. Se resumen aquí para tener un índice completo.

| ID | Historia | Fuente |
|---|---|---|
| US-35 | Registrar operaciones relacionadas y sus efectos (ventas, ventas a crédito, compras; impactos en caja/banco, clientes/proveedores e inventario; salida ligada a orden de trabajo) | Mario, WhatsApp 5 nov. 2026, 12:54–12:58 p. m. |
| US-36 | Corregir movimientos relacionados conservando historial y visibilidad de efectos paralelos; orden de trabajo enlazada con solicitud de materiales | Mario, WhatsApp 5 nov. 2026, 1:00–1:01 p. m. y foto de formato |
| US-37 | Revisar pestañas/secciones del sistema actual según el Word, documentar función y diferencias antes de implementar mejoras | Mario, WhatsApp 5 nov. 2026, 1:04–1:06 p. m. y Word |
| US-38 | Consultar efectivo, clientes/cobranza, valor de almacén y gastos día con día; costeo/estado de resultados mensual y por proyecto | Mario, WhatsApp 5 nov. 2026, 1:16 p. m. |

## Registro de fuentes y límites

- Word/PDF: fuente de las tarjetas US-15 a US-32; el usuario indicó que ambos documentos se compartieron como materiales del contador.
- Mensajes de Goito: fuente de las tarjetas US-1 a US-14.
- Audios del contador: fuente de US-33 y US-34; audio y WAV procesados permanecen fuera del repositorio por privacidad.
- Mensajes de Mario y fotografía de orden/solicitud de materiales: fuente de US-35 a US-38.
- La forma exacta de las tarjetas US-1 a US-34 se recuperó de requisitos y resúmenes disponibles, no de una exportación histórica de tarjetas. Revisar en futuras iteraciones cualquier diferencia con lo dicho originalmente.
- No se persisten nombres, teléfonos, direcciones, INE ni archivos de clientes reales dentro de este registro.
