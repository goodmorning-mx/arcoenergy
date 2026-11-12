# Arco Energy — Registro de history user story cards

- **Propósito:** conservar los hallazgos por stakeholder, fuente e iteración para poder revisar cómo evolucionan sin borrar lo que se dijo antes.
- **Estado:** registro de discovery con fuentes preservadas en documentación y carga inicial versionada a la base de datos de ArcoEnergy; los relatos reconstruidos siguen marcados como tales y no equivalen a backlog aprobado.
- **MUST — preservación literal:** todo hallazgo debe guardar el relato original literal del stakeholder (o una referencia durable al artefacto original cuando no sea texto), separado de la user story normalizada. Nunca reemplazar, corregir ni parafrasear el original al actualizar una tarjeta.
- **Cuidado con la reconstrucción:** US-1 a US-34 se reconstituyen aquí a partir de mensajes, fuentes y los resúmenes disponibles en la conversación. Los IDs US-15 a US-32 se asignan a capacidades explícitas del Word del contador para recuperar el rango histórico, pero no se cuenta con una exportación de las tarjetas originales que confirme su título/texto exactos. Deben validarse en una próxima iteración.
- **Regla de evolución:** agregar nuevas versiones/iteraciones relacionadas; no reemplazar la fuente original. Las reglas contables pendientes no se deben tratar como comportamiento aprobado.

## MUST — conservar la voz original del stakeholder

Este es un requisito obligatorio para el proceso de discovery y para el futuro modelo de datos:

1. Guardar el **contenido literal** aportado por el stakeholder, sin normalizar su redacción. Para texto/audio transcrito, preservar el mensaje o transcripción fuente; para documentos, conservar el archivo original y registrar páginas/secciones o extractos literales con ubicación; para imágenes, conservar el artefacto y su referencia.
2. Mantenerlo separado de la **interpretación**: user story, criterios de aceptación, reglas inferidas, preguntas y decisiones del equipo son datos derivados y deben enlazar al relato fuente que los sustenta.
3. Registrar procedencia mínima: stakeholder/autor tal como se conoce, fecha/hora original si está disponible, canal o tipo de artefacto, identificador/ruta de fuente, iteración y versión de transcripción cuando aplique.
4. No sobrescribir fuentes ni versiones previas. Las correcciones, aclaraciones y nuevas interpretaciones se agregan como eventos/versiones nuevas, enlazadas con la tarjeta anterior y su fuente.
5. Marcar explícitamente lo incierto: transcripción dudosa, texto ilegible, fecha aproximada, atribución no confirmada o paráfrasis reconstruida. Nunca presentar una reconstrucción como cita literal.
6. Aplicar permisos y retención adecuados a datos personales y documentos sensibles. Las referencias a archivos pueden apuntar a almacenamiento privado autorizado; no se deben publicar INE, teléfonos, direcciones ni audios sensibles en repositorios abiertos.

### Campos mínimos que deberá soportar la base de datos

- `source_artifact`: tipo, referencia durable, hash opcional, canal y ubicación exacta (página/minuto/mensaje) cuando corresponda.
- `source_literal`: texto literal o transcripción original, con idioma, autor/atribución, fecha y estado de confianza.
- `story_card`: necesidad normalizada, actor, valor, criterios, preguntas abiertas y estado.
- `source_links`: relación entre una o más fuentes y cada tarjeta/versión, indicando si el vínculo es cita, paráfrasis, inferencia o validación explícita.
- `iteration` y `revision`: fecha, stakeholder que validó, cambios introducidos y vínculo a la revisión anterior; historial append-only.

La restricción del repositorio sobre datos sensibles no elimina este MUST: los originales deben quedar en un almacenamiento privado con control de acceso y la tarjeta debe conservar una referencia durable y verificable. En Markdown/Git se documentan las fuentes no sensibles o las ubicaciones autorizadas, no se publican datos personales.

## Iteración 1 — Requerimientos de Goito Profugo

**Stakeholder:** Goito Profugo. **Fuente:** mensajes de WhatsApp compartidos en esta conversación. Las tarjetas reflejan su solicitud; sus criterios no implican que la funcionalidad exista.

Fuente literal recuperada: [mensajes de WhatsApp de Goito](sources/goito-profugo-whatsapp-2026-10-26.md).

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
- La cola offline conserva consumos y devoluciones con identificador idempotente; tras un rechazo mantiene el detalle entre recargas, pausa operaciones posteriores y permite corregir cantidad o retirar individualmente la acción tras revisión.
- Respuestas HTTP temporales por sesión vencida, timeout, disponibilidad temprana o límite de solicitudes conservan la acción sin fijarla como conflicto permanente y permiten reintentar.
- **Pendiente:** confirmar si el descuento se hace al entregar, consumir o aprobar el reporte y validar sincronización con instaladores en teléfonos reales.

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

Fuentes literales recuperadas: [Word original](sources/contador-comentarios-mejoras-original.docx), [PDF original](sources/contador-mejoras-original.pdf) y [transcripción textual del Word](sources/contador-comentarios-mejoras-transcripcion.md).

### US-15 — Registrar ventas

Como contador/administrador, quiero registrar las ventas con sus datos principales, para llevar control de ingresos y proyectos vendidos.

- Capturar fecha del proyecto, cliente, código y domicilio del proyecto.
- Capturar subtotal, impuestos y valor de venta.
- Registrar si es contado, crédito o parte del plan 24 (tanda de paneles).
- **Pendiente:** reglas de impuestos, pagos mixtos y efecto exacto en inventario/cuentas. Plan 24/tanda puede quedar en la propuesta, pero no se registra como venta ni crédito estándar hasta que contabilidad defina el anticipo y calendario.

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

**Stakeholder:** contador, identificado en el hilo como remitente de los audios de WhatsApp. **Fuentes:** tres OGG de WhatsApp enviados el 2 de noviembre de 2026.

Fuente/transcripción automática versionada: [transcripciones de los audios](sources/contador-whatsapp-audio-transcripts-2026-11-02.md). Los OGG originales permanecen en el equipo del solicitante y sus hashes están registrados allí.

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

## Iteración 5 — Límites de portales, agente y evolución de discovery

**Stakeholder:** dueño del producto Arco Energy (nombre no registrado). **Fuente:** conversación del proyecto del 6 de noviembre de 2026. Los relatos literales están en [requerimientos del dueño](sources/owner-product-brief-2026-11-06.md). Esta iteración define responsabilidades por portal y la conservación del aprendizaje; no reemplaza las tarjetas de Goito o Mario.

### US-39 — Administrar el negocio desde un CRM de escritorio

- **Relato literal:** “el CRM es el sistema de administracion es un panel dashboard para las computadoras y es el panel admin de todo.”
- **Necesidad derivada:** como administrador del negocio, quiero un CRM pensado para computadora que concentre la administración del sistema.
- **Criterios iniciales:** navegación propia de escritorio; administración por permisos; clientes, cotizaciones y seguimiento en la primera iteración. Los demás módulos administrativos se agregan cuando se validen con los stakeholders.
- **Estado:** base de clientes, cotizaciones, seguimiento, catálogo y usuarios está implementada; reportes contables, inventario financiero, compras y costos permanecen pendientes de definición.

### US-40 — Ejecutar trabajo operativo desde la PWA

- **Relato literal:** “el PWA es una aplicacion mobile para las personas de campo y ademas un cliente para los empleados. donde se van a ejecutar ciertas mas que nada acciones porque es operativa.”
- **Necesidad derivada:** como empleado de campo o usuario operativo, quiero una app móvil con acciones breves adecuadas a mi rol.
- **Criterios iniciales:** aplicación PWA separada del CRM; autenticación y privilegios por rol; la información del cliente debe limitarse según permisos y asignaciones.
- **Estado:** la experiencia móvil y el acceso autenticado se conservan; el cotizador manual toma el catálogo y los trabajos consultan instalaciones asignadas. Asignación, notificaciones, consumos por proyecto, viáticos y modo offline siguen pendientes.

### US-41 — Orientar una cotización desde la web con un agente

- **Relato literal:** “la web es una web donde vamos a cotizar por IA agentica; donde hablamos con una IA para que nos cotice paneles solares. a su vez este proyecto va a usar el MCP server y otros modulos de goodmorning-factry por lo que tambien ve a leerlos en nuestro github.”
- **Necesidad derivada:** como visitante, quiero conversar con una IA desde el sitio público para entender opciones y solicitar una cotización solar.
- **Criterios iniciales:** integrar los módulos `gm-agent` y `gm-mcp`; cotizar solo con un paquete aprobado; limitar las herramientas a información pública; no inventar precios ni crear registros; capturar contacto con consentimiento.
- **Estado:** asistente consulta tamaños y devuelve total/inversor únicamente desde paquetes aprobados; la consulta directa del catálogo del CRM exige permiso. La clave administrada de OpenAI funciona en DEV y el chat responde en español. Una solicitud de 8 paneles no devolvió precio porque el catálogo no ofreció un paquete activo aprobado; el asistente comunicó esa limitación sin inventar datos. El formulario de prospecto pide consentimiento. Falta cargar/validar el catálogo comercial real y verificar la captura con consentimiento; Drive, WhatsApp Business y carga de recibos no se declaran integrados.

### US-42 — Conservar cada tarjeta como dato versionado por iteración

- **Relato literal:** “lo vamos a hacer por iteraciones; asi que todo eso que tenemos ahora asi esta bien y las actualizaciones van a ser iteraciones historycards me entiendes” y “tienes que poner eso es un MUST”.
- **Necesidad derivada:** como equipo que aprende con los usuarios, quiero conservar cada history user story card vinculada a su fuente y a su iteración para que el aprendizaje no se pierda.
- **Criterios iniciales:** guardar voz original y fuente separadas de la historia normalizada; nuevas revisiones se agregan sin sobrescribir; registrar stakeholder, momento, canal, versión, incertidumbres y vínculos entre tarjetas.
- **Estado:** MUST y campos mínimos documentados al inicio de este archivo. El repositorio conserva las tarjetas/fuentes en Markdown; un modelo de datos y una interfaz append-only para registrar iteraciones quedan para una iteración futura.

## Registro de fuentes y límites

- Word/PDF: fuente de las tarjetas US-15 a US-32; el usuario indicó que ambos documentos se compartieron como materiales del contador.
- Mensajes de Goito: fuente de las tarjetas US-1 a US-14.
- Audios del contador: fuente de US-33 y US-34; audio y WAV procesados permanecen fuera del repositorio por privacidad.
- Mensajes de Mario y fotografía de orden/solicitud de materiales: fuente de US-35 a US-38.
- Requerimientos literales del dueño del producto del 6 de noviembre de 2026 en [owner-product-brief-2026-11-06.md](sources/owner-product-brief-2026-11-06.md).
- La forma exacta de las tarjetas US-1 a US-34 se recuperó de requisitos y resúmenes disponibles, no de una exportación histórica de tarjetas. Revisar en futuras iteraciones cualquier diferencia con lo dicho originalmente.
- Los relatos textuales de Goito y del Word del contador ya están recuperados. Para US-1 a US-32 falta cotejar la asignación exacta de cada fragmento a los IDs históricos; el texto de las cards es una síntesis derivada, no una cita.
- Para US-33 y US-34 hay transcripciones ASR de los audios, no transcripción humana validada. Los OGG originales se identifican por hash y ruta local, sin subir audio de voz al repositorio.
- No se persisten nombres, teléfonos, direcciones, INE ni archivos de clientes reales dentro de este registro.

## Iteración 2 — producto autenticado y operación de campo (2026-11-06)

### Cambios incorporados a DEV en esta iteración

- CRM y PWA pasan a login separado y protegen el acceso; dejan de renderizar personas, cotizaciones, instalaciones y saldos ficticios. No se persisten acciones localmente como si fueran reales.
- El backend deja de insertar paquetes e inventario de ejemplo al iniciar. Una migración elimina solo los 17 paquetes `is_demo` identificados y artículos de semilla con costo/existencia/mínimo cero y sin movimientos.
- CRM puede crear clientes, configurar paquetes comerciales, asignar órdenes a cuentas activas con rol de instalador y registrar artículos/entradas de almacén.
- PWA consulta catálogo, órdenes e inventario del API; permite registrar consumo y gasto enlazados a una orden asignada.
- Se crea el modelo append-only `ae_history_cards`, una migración que carga las 42 tarjetas recuperadas/reconstruidas con sus fuentes y una pantalla administrativa para añadir versiones sin sobrescribir las anteriores.

### Estado por user story card al cierre de esta iteración

| Tarjetas | Estado | Alcance pendiente principal |
| --- | --- | --- |
| US-1 | Parcial funcional | Configurar paquetes reales y validar PDF con el cliente. |
| US-2 | Pendiente | Recibo PDF, OCR, fórmula y aprobación humana. |
| US-3 | Parcial | PDF foliado se descarga y se archiva en Drive si las credenciales están configuradas; WhatsApp ofrece compartir/adjuntar desde el dispositivo. La configuración debe confirmarse en la cuenta real y no hay envío automático por API. |
| US-4 | Funcional básico | Agregar alertas/notificaciones y responsable asignado. |
| US-5–6 | Pendientes | Plantillas legales, carga segura de INE, consentimiento, firma y proveedor biométrico. |
| US-7 | Parcial | Asignación y visibilidad para instalador; falta notificación push/SMS/WhatsApp. |
| US-8 | Parcial | Consulta de existencias reales y reservas por orden; falta alerta por faltantes de materiales requeridos. |
| US-9–10 | Funcionales básicos | Consumo y gasto enlazados a orden; faltan evidencia/recibo, revisión y modo sin conexión. |
| US-11 | Parcial | API de cuentas por cobrar y pagos; faltan agenda, avisos de pago y plantillas WhatsApp listas. |
| US-12 | Parcial | Catálogo, existencia y costo unitario; falta costo real por movimiento/proyecto. |
| US-13 | Pendiente | Google Drive y políticas de carpetas/permisos. |
| US-14 | Funcional en API y portales | Completar matriz de acceso por cada entidad/campo y pruebas de aislamiento. |
| US-15–16, US-19 | Parciales | Venta aceptada alimenta reporte preliminar; historial/aplicación de cobranza y alertas financieras siguen parciales. El resumen no es estado financiero formal. |
| US-17 | Funcional básico | Administrador y contador registran gastos operativos/directos por fecha, categoría, proyecto opcional y comprobante enlazado. Falta afectar una cuenta de caja/banco, autorización y conciliación. |
| US-18 | Funcional básico | Se crean cuentas de efectivo/banco con saldo inicial y se consultan saldos/reportes; falta conciliación bancaria y vincular automáticamente los cobros, pagos y gastos. |
| US-20 | Parcial | Artículos con descripción, unidad, existencia, mínimo y costo; faltan categoría, marca, modelo, proveedor y QR. |
| US-21–22 | Pendientes/parciales | Entrada individual de almacén disponible; faltan compra multirenglón, proveedor, factura/XML y OCR. |
| US-23 | Funcional básico | El instalador devuelve contra una salida de su orden; el kardex enlaza ambos movimientos, limita el acumulado devuelto y repone existencias. Falta distinguir condición del material y aprobar costos de devolución. |
| US-24 | Parcial | La orden solicita material; la PWA confirma consumo sin doble descuento y el evento queda fechado/costeado. Falta separar entrega física y autorizar variaciones. |
| US-25 | Pendiente | Lectura asistida de orden/solicitud escaneada. |
| US-26 | Funcional básico | CRM y PWA señalan existencias por debajo del mínimo configurado; faltan notificaciones push y asignación de responsable de reabasto. |
| US-27 | Funcional básico | Kardex distingue salida física, consumo confirmado y corrección del consumo; conserva fecha y costo histórico. Acceso de instalador limitado a sus órdenes. Faltan filtros expuestos en UI y exportación. |
| US-28–29 | Pendientes | Cámara QR/código de barras e informes de operación. |
| US-30 | Funcional básico | Proveedores y condiciones contado/crédito con días; el saldo queda pendiente hasta enlazar entradas de compra y pagos. |
| US-31 | Pendiente | Compras multirenglón, saldos por proveedor y pagos vinculados. |
| US-32 | Parcial | Orden enlazada con cliente y cotización; falta entidad proyecto y folio comercial acordado. |
| US-33, US-35 | Parciales | Hay un reporte operativo preliminar de ventas menos material consumido y gastos. Libro de doble partida y efectos contables completos requieren validar reglas con el contador. |
| US-34 | Funcional básico | Entradas/salidas manuales de efectivo o banco, saldo derivado e historial; las operaciones comerciales aún no se enlazan automáticamente. |
| US-36 | Parcial | Las entradas/salidas manuales se corrigen con reversa append-only; falta extender la corrección relacionada a compras, ventas, cobranza e inventario. |
| US-37 | Pendiente | Comparación con cada pantalla del sistema legado; falta acceso al entorno de César. |
| US-38 | Parcial | Reporte mensual y por proyecto con ventas, consumos, gastos y resultado preliminar. No incluye devoluciones de venta/bonificaciones ni impuestos y no sustituye cierre contable. |
| US-39 | Parcial funcional | CRM de escritorio autenticado y flujos comerciales iniciales; falta el resto administrativo y financiero. |
| US-40 | Parcial funcional | PWA autenticada con consulta de órdenes/inventario y captura de consumos/gastos; faltan flujos de cierre y trabajo offline. |
| US-41 | Parcial funcional | Web pública y agente con catálogo aprobado; faltan credenciales y validación de experiencia de venta completa. |
| US-42 | Funcional para registro/versiones | 42 tarjetas iniciales persistidas con fuente, vista administrativa e inserción append-only; cotejar reconstrucciones e incorporar futuras iteraciones. |

## Iteración 3 — Compras y proveedores (2026-11-06)

Cada tarjeta conserva las versiones previas; el relato fuente y su procedencia no se modifican.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-18 | Funcional básico | Saldos de caja/banco reflejan pagos de compra ligados al proveedor. Pendiente: ventas, cobranza y conciliación bancaria. |
| US-21 | Funcional básico | Compra multirenglón con proveedor, referencia/factura, folio, costo por línea y entrada de existencias. Pendiente: XML/OCR, impuestos/fletes y valoración acordada. |
| US-30 | Funcional básico | El saldo por pagar se deriva de compras y pagos vinculados al proveedor. |
| US-31 | Funcional básico | Anticipos y pagos parciales/totales reducen la cuenta por pagar y descuentan caja/banco. Pendiente: conciliación y reversa enlazada a la compra. |
| US-34 | Funcional básico | Pagos de compra ligados al proveedor se reflejan en las cuentas y conservan historial. Pendiente: ventas, cobranza y gastos. |

## Iteración 4 — Gastos vinculados a cuentas (2026-11-06)

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-17 | Funcional básico | Los gastos administrativos/contables requieren cuenta activa y generan salida de caja/banco; gastos de campo siguen registrándose por orden en PWA. Pendiente: autorización, conciliación y anticipos/reembolsos de campo. |
| US-18 | Funcional básico | Gastos administrativos y pagos a proveedores afectan la cuenta elegida. Pendiente: ventas, cobranza y conciliación bancaria. |
| US-34 | Funcional básico | Movimientos ligados a compras y gastos administrativos se reflejan en cuentas con historial. Pendiente: enlazar ventas/cobros y conciliación. |

## Iteración 5 — Cobranza de clientes (2026-11-06)

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-11 | Parcial funcional | CRM registra cuotas, abonos parciales y recordatorios WhatsApp iniciados por el encargado; los pagos aumentan la cuenta elegida. Pendiente: agenda/avisos automáticos y conexión con planes de venta. |
| US-16 | Funcional básico | Cuotas manuales por cliente, forma de pago, pagos parciales con fecha/referencia e historial enlazado a caja/banco. Pendiente: generar cuotas desde ventas/crédito y distribuir un pago entre deudas. |
| US-18 | Funcional básico | La cobranza aumenta caja/banco y los pagos ligados a compras/gastos reducen saldos. Pendiente: enlazar ventas y conciliar. |
| US-34 | Funcional básico | Movimientos ligados a compras, gastos administrativos y abonos de clientes se reflejan en cuentas con historial. Pendiente: enlazar ventas y conciliación. |

## Iteración 6 — Ventas y órdenes de trabajo (2026-11-06)

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-7 | Parcial | La venta crea orden foliada, la asigna a un instalador activo y se muestra en su PWA. Pendiente notificación push/mensajería y confirmación de cuadrilla. |
| US-15 | Funcional básico | Cotización aceptada se registra como venta contado o crédito; ingreso o saldo por cobrar, materiales descargados por orden y folios se actualizan juntos. Pendientes: impuestos, pagos mixtos, calendario de crédito y reversa integral. |
| US-18 | Funcional básico | La venta de contado aumenta caja/banco; abonos a crédito, compras y gastos enlazan su movimiento. Pendiente conciliación bancaria y libros contables. |
| US-24 | Parcial | Material solicitado en la orden se valida, descuenta almacén y conserva costo por movimiento ligado al proyecto. Falta diferenciar solicitado, entregado, consumido y autorizado. |
| US-32 | Parcial | Venta y orden tienen folios únicos y se relacionan con cotización y cliente. Falta la entidad de proyecto independiente y aprobar formato de folio. |
| US-34 | Funcional básico | Ingresos de ventas de contado y abonos de crédito, así como salidas por compra/gastos y material en kardex, quedan enlazados a su operación. Faltan conciliación y correcciones relacionadas. |
| US-35 | Parcial | Venta aceptada actualiza ingreso o cartera, salida de inventario por orden y folios relacionados en transacción. No hay todavía doble partida ni todas las reglas fiscales/contables. |

Las funciones marcadas como pendientes se mantienen visibles en el backlog. Los bloqueos de esta iteración no autorizan inventar precios, documentos legales, tratamiento biométrico, reglas contables ni credenciales de servicios externos.

## Iteración 7 — Reserva y consumo de materiales (2026-11-06)

La Iteración 6 está desplegada en DEV. La corrección de la Iteración 7 quedó mergeada en `dev` y espera una operación manual de Factory para despliegue. Crear una venta/orden solicita y reserva cantidades, mientras la confirmación en la PWA descuenta físicamente solo el consumo nuevo. La migración enlaza las líneas y movimientos previos y revierte el solapamiento de descuentos históricos que puede identificar. Las tarjetas fuente permanecen sin alteraciones; esta implementación es una versión añadida por el equipo, pendiente de validación del stakeholder.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-7 | Parcial | La PWA muestra folio y estado de material solicitado/consumido en órdenes asignadas. Pendiente notificación push/mensajería y confirmación de cuadrilla. |
| US-8 | Parcial | Existencia física, reservado y disponible se distinguen. Pendiente alerta de faltantes por orden y notificación. |
| US-9 | Parcial | Consumo confirmado queda ligado a la orden y la existencia solo se descuenta una vez; se limita a cantidades de la solicitud. Pendientes evidencia, revisión, modo sin conexión y reglas para variaciones. |
| US-12 | Parcial | El inventario presenta reservas abiertas junto a disponibilidad física. Falta costeo final por proyecto. |
| US-15 | Funcional básico | La venta reserva materiales sin volver a descontarlos; contado/crédito, folios y orden se conservan. Pendientes reglas contables/fiscales y reversa integral. |
| US-20 | Parcial | CRM y PWA muestran existencia física, reserva y disponibilidad; faltan campos de marca/modelo/categoría y escáner. |
| US-24 | Parcial | Solicitud, reserva, consumo confirmado, devolución y salida física quedan diferenciados en la orden/kardex. Pendiente entrega/autorización y ajustes por material dañado. |
| US-26 | Funcional básico | No se permite confirmar un material no solicitado ni exceder la cantidad restante de la orden. Pendientes alertas de reabasto. |
| US-27 | Funcional básico | El kardex separa salida física de confirmación de consumo sin nueva salida; reserva no cambia el saldo físico. Pendientes filtros en UI/exportación. |
| US-29 | Parcial | La cantidad disponible considera reservas activas. Pendiente reporte gráfico y filtros/exportación. |
| US-32 | Parcial | La orden foliada expone líneas solicitadas, consumidas y pendientes. Falta proyecto independiente y formato acordado. |
| US-35 | Parcial | Reservas, consumos físicos, devoluciones y corrección de doble descuento conservan trazabilidad. Pendiente doble partida, costos finales y revisión con contador. |

## Iteración 8 — Costeo preliminar por proyecto y mes (2026-11-06)

La captura de cada consumo crea un evento fechado de costo sin producir otro descuento físico. Devoluciones de sobrantes ligadas a esa salida generan una corrección de costo. Un backfill idempotente conserva fecha y costo conocidos en el historial anterior. El reporte administra `ventas registradas − costo de materiales consumidos − gastos capturados`; señala faltantes de costo y declara fuera del cálculo las devoluciones de venta y bonificaciones. No se presenta como estado contable cerrado. Cada revisión conserva el relato fuente literal.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-15 | Funcional básico | Las ventas registradas se consultan en reporte mensual y por orden; se separan de los cobros de caja. Pendientes impuestos, pagos mixtos y reversas integrales. |
| US-17 | Funcional básico | Reporte agrega gastos por fecha, orden y categoría. Pendientes autorización y conciliación. |
| US-24 | Parcial | El consumo confirmado tiene evento de costo y fecha, desacoplado de la salida física; devoluciones ligadas corrigen el evento. Pendientes autorización y variaciones de materiales. |
| US-27 | Funcional básico | Kardex diferencia cantidad física movida de material consumido para costeo; la corrección de consumo no duplica entrada/salida física. Pendientes filtros visibles y exportación. |
| US-32 | Parcial | Reporte agrupa por folio de orden/proyecto y periodo mensual. Falta identidad de proyecto independiente y clave aprobada. |
| US-35 | Parcial | Reporte enlaza ventas, consumo material fechado y gastos por proyecto. Doble partida, devoluciones/bonificaciones de venta, impuestos y conciliación siguen pendientes. |
| US-38 | Parcial | CRM muestra ventas − costo consumido − gastos por mes o proyecto, con faltantes de costo visibles. Falta añadir devoluciones/bonificaciones, validar reglas contables y entregar estado formal. |

## Iteración 9 — acceso de producto y avance de órdenes (2026-11-06)

CRM y PWA conservan accesos separados en `/crm/login` y `/app/login`; `/login` lleva al CRM. Las cuentas cliente se dirigen al portal PWA. Los portales privados exigen autenticación y no crean ni muestran usuarios/clientes/cotizaciones/inventario ficticios. Las rutas se sirven con fallback de aplicación para abrir enlaces directos. La PWA ahora permite actualizar checklist persistido de cada orden y registra cada cambio en la bitácora. El instalador solo puede cambiar órdenes asignadas a su correo. Los avisos locales se reciben mientras la PWA está abierta; notificaciones de fondo requieren configurar un proveedor push. El catálogo solo permite generar cotizaciones después de cargar y aprobar precios reales.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-7 | Parcial | La asignación y checklist de órdenes se muestran y actualizan desde PWA; el cambio deja bitácora. Pendiente push cuando la app está cerrada y confirmación de cuadrilla. |
| US-14 | Parcial funcional | Login CRM/PWA separado y acceso de cliente redirigido a PWA; completar revisión de permisos por entidad/campo. |
| US-39 | Parcial funcional | CRM y PWA sin datos de muestra y rutas privadas tras login; hace falta completar el resto administrativo/financiero y configurar catálogo aprobado. |
| US-40 | Parcial funcional | PWA consulta órdenes asignadas, actualiza checklist con autorización de API y activa avisos locales con permiso del navegador. Offline para escritura y push de fondo siguen pendientes. |

## Iteración 10 — exportación del kardex (2026-11-06)

El CRM ya permitía filtrar el kardex por artículo y rango de fechas, pero no descargarlo. Se agrega exportación CSV de los movimientos actualmente consultados. La exportación respeta el permiso de costos y escapa celdas de texto que podrían interpretarse como fórmulas. La fuente literal de la historia no se modifica.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-27 | Funcional básico | CRM expone filtro por artículo/fecha y descarga CSV del conjunto cargado (hasta 500 movimientos de API). Costos se exportan solo con permiso. Pendientes paginación/volúmenes mayores y valoración histórica completa. |

## Iteración 11 — existencias por orden para campo (2026-11-06)

En la PWA, cada instalación ahora muestra el material solicitado, consumido y pendiente, junto con existencia física y reservas globales activas. La interfaz advierte cuando el total reservado supera la existencia física, de modo que el instalador pueda detectar una posible falta antes del trabajo. La señal es global al artículo porque el sistema aún no tiene una regla aprobada para repartir un faltante entre órdenes concurrentes.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-8 | Parcial funcional | PWA relaciona material solicitado por orden con existencia, reservas y disponibilidad; alerta de déficit de reservas globales. Pendiente asignar/priorizar faltantes por orden y notificar reabasto. |

## Iteración 12 — alertas operativas del dashboard (2026-11-06)

El CRM muestra artículos bajo el mínimo configurado, cuentas por cobrar vencidas o próximas a vencer en los siguientes 7 días y saldos de caja/bancos. Cada grupo de información aparece únicamente para identidades con el permiso correspondiente. El cálculo no añade reglas financieras nuevas. El dashboard continúa parcial: falta que administración y contador validen métricas, umbrales, gráficas y periodo formal del flujo de efectivo.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-19 | Parcial funcional | Dashboard presenta alertas de inventario/cobranza y saldos por permiso. Pendientes indicadores y umbrales acordados, gráficas y flujo de efectivo por periodo validado. |

## Iteración 13 — catálogo de materiales identificable (2026-11-06)

El alta de inventario ahora conserva descripción, categoría, marca, modelo, proveedor habitual y un código QR/barras opcional único. El CRM permite capturar estos datos y consultarlos en el catálogo; el proveedor se selecciona del registro de proveedores. Esto prepara identificación futura desde cámara, pero no genera una etiqueta ni escanea códigos todavía.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-20 | Parcial funcional | Catálogo guarda y muestra categoría, marca, modelo, proveedor y barcode opcional; descripción separada del nombre. Pendientes ediciones completas, conversiones/unidades y generar/leer etiquetas QR o barras. |
| US-28 | Pendiente | Se puede guardar un identificador escaneable por artículo, pero falta escáner de cámara e identificación del código. |

## Iteración 14 — identificación de materiales desde PWA (2026-11-06)

La pantalla móvil de inventario permite escanear QR y códigos de barras en navegadores que exponen `BarcodeDetector`, usando la cámara trasera cuando está disponible. La lectura busca el identificador único del catálogo y lleva visualmente al artículo con su disponibilidad actual. También permite introducir el código desde un lector conectado como teclado o capturarlo manualmente en navegadores incompatibles. La lectura necesita conexión para consultar el inventario; el modo sin conexión y la matriz de dispositivos/formatos probados siguen pendientes.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-20 | Parcial funcional | Código QR/barras opcional se conserva en el catálogo y se muestra en la vista de almacén móvil. Pendientes generación de etiquetas y confirmación de formatos/dispositivos. |
| US-28 | Parcial funcional | PWA reconoce códigos asignados a artículos y localiza el registro; incluye búsqueda manual como alternativa. Pendientes modo sin conexión y validación en teléfonos y lectores usados por ArcoEnergy. |

## Iteración 15 — reportes operativos de inventario y actividad (2026-11-06)

El CRM incorpora un resumen filtrable por periodo con existencia y disponibilidad actuales, alerta de artículos bajo mínimo, movimientos del kardex, estado de clientes, proveedores y órdenes, y gastos agrupados por categoría. Los movimientos se pueden descargar en CSV (límite visible de 500 registros). El valor de existencias y los costos aparecen solo con permiso de lectura de costos. El reporte describe registros operativos y no asigna tratamiento contable nuevo; fórmulas oficiales y periodos de corte requieren validación del contador.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-19 | Parcial funcional | Dashboard previo más resumen de movimientos por periodo, estado de clientes/proveedores/órdenes y gastos por categoría. Falta validar umbrales y flujo de efectivo con contador. |
| US-27 | Parcial funcional | Kardex con filtro de fecha y descarga CSV desde reportes; se limita a 500 movimientos por consulta. Falta paginación y mayor volumen. |
| US-29 | Parcial funcional | CRM ofrece stock disponible, movimientos, estatus operativos y gastos agrupados con filtros de fecha y CSV. Faltan reportes dedicados por todas las entidades y validación de fórmulas del contador. |

## Iteración 16 — precarga asistida de compras con CFDI y rutas de acceso (2026-11-06)

Se agrega lectura asistida de CFDI XML 3.3/4.0 en MXN como propuesta revisable para capturar una compra. La lectura no registra la compra, no conserva el XML y no distribuye impuestos, descuentos globales ni fletes. El usuario debe relacionar proveedor y artículos, validar cantidades e importes y confirmar la operación. Esta entrega no procesa imágenes ni OCR. Se verifica la separación de acceso en `/crm/login` para administración y `/app/login` para equipo de campo y clientes; `/login` es alias del acceso CRM. El portal CRM permite a administradores crear y asignar los cinco roles definidos. No se generan cuentas de muestra: la primera cuenta administradora depende de credenciales de arranque configuradas como secretos en Factory. El código fuente ya no presenta modo de prueba; el despliegue DEV sigue pendiente de actualización/verificación de su commit.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Accesos CRM/PWA y cinco roles en API/gestión de equipo. Falta completar la matriz de permisos y verificar cuentas reales en el entorno DEV. |
| US-21 | Funcional básico | Compra multirrenglón y CFDI XML pueden precargar una propuesta revisable. Faltan impuestos/fletes según política del contador, XML variantes y manejo de facturas relacionadas. |
| US-22 | Parcial funcional | CFDI 3.3/4.0 en MXN precarga proveedor/referencia/fecha y conceptos en CRM; revisión humana obligatoria. Imagen, OCR y otros formatos quedan pendientes. |
| US-39 | Parcial funcional | CRM de escritorio autenticado con catálogo, clientes, ventas/órdenes, compras, finanzas, equipo y reportes ya existentes. El estado del despliegue es anterior a estos cambios; falta integrar y verificar DEV. |
| US-40 | Parcial funcional | PWA autenticada con rutas de acceso y operaciones móviles. Falta completar flujos de campo y comprobar sesión/roles sobre el despliegue actualizado. |

### Alineación de la cuenta administradora de DEV

La base de DEV tiene una cuenta que coincide con el correo de arranque guardado como secreto en Factory. La membresía conservaba `admin` y permisos previos; el inicio del backend ahora reconcilia ese usuario configurado a `administrador` con el mapa vigente, sin imprimir ni cambiar su contraseña. Pendiente desplegar esta revisión y verificar el rol a través del acceso autenticado.

## Iteración 17 — correcciones enlazadas de pagos (2026-11-07)

El contador indicó que corregir un pago debe conservar historial y actualizar en paralelo la operación afectada. Ahora un pago a proveedor o un abono de cliente se corrige mediante un nuevo registro con motivo, ligado al original y al movimiento inverso de caja/banco. El saldo por pagar o cobrar se recalcula dentro de la misma transacción. El endpoint genérico ya no permite revertir por separado un movimiento de caja originado por estos pagos. El CRM expone el historial y una acción de corrección para contador/administrador. No se editan ni eliminan los registros originales.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-16 | Funcional básico | Abonos de clientes pueden revertirse con motivo, reabren el saldo y generan el movimiento inverso en la misma cuenta. Pendiente: distribuir pagos entre cuotas, generación automática del plan y conciliación. |
| US-18 | Funcional básico | Reversas de pagos enlazados corrigen el saldo de caja/banco y la cuenta por cobrar o pagar en la misma operación. Pendiente: conciliación bancaria y otras fuentes externas. |
| US-31 | Funcional básico | Pagos a proveedores conservan su original; la corrección aumenta cuenta por pagar y repone el saldo de la cuenta. Pendiente: reversa integral de compra e inventario. |
| US-34 | Parcial funcional | Reversa de pago de proveedor/cliente actualiza movimiento de caja y saldo relacionado con trazabilidad. Quedan otros tipos de operación y conciliación. |
| US-36 | Parcial funcional | Se corrigen pagos de clientes y proveedores con eventos enlazados y motivo; no se permite revertir por separado el movimiento de caja enlazado. Pendiente extender a compras completas, ventas e inventario. |

## Iteración 18 — checklist de campo sin conexión (2026-11-07)

La PWA guarda en IndexedDB las órdenes consultadas previamente por una cuenta instaladora y permite marcar pasos del checklist sin conexión. Cada cambio queda asociado a la cuenta y la orden; al reconectar, la PWA vuelve a consultar las órdenes autorizadas y aplica el cambio a la versión actual del checklist antes de enviarlo. Los cambios confirmados se eliminan de la cola. Al cerrar sesión se borra la caché de órdenes de esa cuenta. Consumos, devoluciones de inventario y gastos continúan requiriendo conexión al API y sus validaciones. El almacenamiento local necesita validación en los teléfonos de ArcoEnergy y no sustituye una política de borrado remoto del dispositivo.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-40 | Parcial funcional | Checklist de órdenes con cola offline persistente y sincronización tras reconexión; caché de órdenes por cuenta instaladora. Consumos, devoluciones, gastos, otras escrituras offline, notificaciones de fondo, validación en dispositivos y borrado remoto siguen pendientes. |

## Auditoría de accesos y despliegue DEV (2026-11-07)

La rama `dev` quedó en `bf70b0c`. Las rutas `/app/login` y `/crm/login` y sus portales responden HTTP 200; `/api/version` informa el commit desplegado `470708e`, que incluye la Iteración 17. La ruta CRM/PWA usa autenticación y se verificó la cuenta real existente con rol `administrador`; no se crearon cuentas de muestra ni están verificadas cuentas reales para los demás roles. La limpieza de selectores CSS obsoletos del PR #39 no cambia el comportamiento servido. Estos datos acreditan accesos y un usuario administrador, no la cobertura completa de las 42 user story cards.

## Iteración 19 — devolución reutilizable y merma de obra (2026-11-07)

La devolución de una salida ahora distingue sobrante reutilizable y material dañado. El material dañado queda relacionado con la salida original, no incrementa el stock y se registra como costo de la orden si todavía no se había confirmado como consumo; si ya estaba consumido, no duplica el costo. El kardex muestra la merma con cambio físico cero. Se conserva el registro original y la cuenta de piezas devueltas o dañadas no puede exceder la salida. La política de inspección y autorización de materiales reparables necesita validación del responsable de almacén.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-23 | Funcional básico | Distingue devolución reutilizable y pieza dañada ligada a la salida. Solo lo reutilizable vuelve a existencias. Pendientes inspección/aprobación y tratamiento reparable. |
| US-24 | Parcial funcional | Merma preemitida genera costo de consumo por proyecto sin reponer stock; material ya consumido conserva su costo sin duplicarlo. Pendientes aprobación de consumo y variaciones. |
| US-27 | Parcial funcional | El kardex marca merma ligada a salida con cambio físico cero. Pendientes filtros y exportación específicos. |
| US-35 | Parcial funcional | La merma actualiza costo preliminar por proyecto en los casos no consumidos. Doble partida, validación contable y reglas fiscales siguen pendientes. |

## Iteración 20 — operaciones de campo resilientes sin conexión (2026-11-07)

La PWA amplía su cola local por cuenta instaladora a consumos, devoluciones/mermas y gastos, además del checklist. También conserva inventario y movimientos consultados para que el operador pueda preparar acciones cuando no tiene señal. Al reconectar, cada acción se reenvía con el mismo identificador único; el servidor guarda un recibo transaccional junto al movimiento y devuelve el resultado original en reintentos. Si se reutiliza el identificador con datos distintos, la operación se rechaza. Los registros con errores de validación permanecen pendientes hasta corregirse o descartarse explícitamente. La persistencia en dispositivos reales requiere validar almacenamiento, uso compartido y políticas de retención con ArcoEnergy.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-9 | Parcial funcional | PWA puede encolar consumos, devoluciones y mermas sin conexión con sincronización posterior; prueba en teléfonos, actualización de cachés y conflictos de cantidades pendientes. |
| US-10 | Parcial funcional | Recibos idempotentes impiden repetir decrementos, devoluciones/mermas y movimientos por reintentos. Falta validación de conflictos operativos con almacén. |
| US-28 | Parcial funcional | La PWA busca códigos con cámara, lector o entrada manual usando el inventario cacheado tras una consulta autenticada; falta validar formatos y dispositivos reales. |
| US-40 | Parcial funcional | Checklist, gastos y operaciones de material quedan en colas locales separadas, por usuario y con confirmación del servidor; notificaciones de fondo y validación de campo siguen pendientes. |

## Verificación actual de DEV (2026-11-07)

La Iteración 20 está integrada en `dev` en `bdfc6cd7aecbcc0047d956ecc8bbe331d37842b6`. Factory terminó el despliegue y su paso de verificación de esquema; `/api/health/ready`, `/app/login`, `/crm/login` y `/login` respondieron HTTP 200, y API, PWA y CRM publican ese mismo SHA. La pantalla Equipo permite al administrador crear cuentas con correo y contraseña temporal y asignar los cinco roles definidos; se confirmó una cuenta real de administrador, pero no hay evidencia de cuentas reales creadas para contador, marketing, instalador ni cliente. No se crean usuarios ficticios para hacer pasar esa validación. Se necesitan los datos reales de las personas y la validación de acceso por sus responsables.

El código vigente no incorpora credenciales, clientes ni inventario de muestra. Las referencias históricas a las semillas demo documentan su retirada y sus resguardos, no un modo de prueba disponible para el usuario.

## Iteración 21 — comparación del sistema actual con el Word del contador (2026-11-07)

Se cotejaron el Word “COMENTARIOS Y MEJORAS PARA EL SISTEMA DE ARCO ENERGY” y el PDF “MEJORAS AL SISTEMA ARCO ENERGY” con las pantallas y endpoints actuales de CRM/PWA. Los documentos coinciden en diez apartados. La comparación detallada queda en `docs/discovery/us-37-system-comparison.md` y se conserva como una nueva versión de US-37 en la base de history cards, sin modificar su relato literal.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-37 | Funcional para la revisión | Matriz fuente-a-sistema de las diez secciones; identifica lo que existe, brechas y preguntas abiertas. No representa aprobación del contador ni declara terminadas las funciones parciales. |
| US-15 | Funcional básico | La comparación confirma venta contado/crédito y orden ligada; Plan 24, impuestos, subtotal fiscal, pagos mixtos y fecha de proyecto quedan pendientes de definición. |
| US-25 | Pendiente | La orden externa todavía no se carga ni escanea en CRM/PWA; se solicita el formato vigente para definir la extracción y revisión manual. |
| US-32 | Parcial | Ventas y órdenes tienen folios relacionados; no existe una entidad de proyecto independiente ni formato de código aprobado. |
| US-33 | Parcial | La comparación confirma enlaces entre ventas/caja/cartera/inventario y compras/proveedor/caja o CxP; las reglas contables, impuestos y tratamiento de Plan 24 esperan validación del contador. |

## Iteración 22 — gráfico y detalle de disponibilidad (2026-11-07)

El reporte de existencias ahora incluye un gráfico circular de artículos disponibles, con stock bajo y agotados, además de una tabla detallada de existencia física, reservado, disponible, mínimo y categoría. El gráfico cuenta artículos por estado y no suma unidades incompatibles, por ejemplo paneles y metros de cable. La tabla mantiene las cantidades y unidades de cada artículo. No se incorpora valuación al gráfico para roles sin permiso de costos.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-19 | Parcial funcional | Reportes muestra disponibilidad y alertas de artículos bajo mínimo; faltan indicadores/gráficas y periodo de flujo de efectivo validados por administración y contador. |
| US-29 | Parcial funcional | Reporte ofrece gráfico circular por estado y tabla detallada de stock; faltan reportes dedicados restantes, paginación y validación de fórmulas contables. |

## Iteración 23 — salida de prueba y accesos reales (2026-11-07)

Se verificó en DEV que ArcoEnergy no presenta modo de prueba, contador de trial, credenciales demo ni registros empresariales de muestra. Las semillas demo anteriores están retiradas; las menciones restantes son fixtures de pruebas y documentación histórica. El sitio raíz conserva su función pública de marketing y captura de prospectos. Las rutas privadas `/crm/` y `/app/` requieren sesión y muestran el acceso de CRM o PWA respectivamente; `/crm/login`, `/app/login` y el alias `/login` entregan la pantalla de inicio de sesión. API, CRM y PWA reportan `d9fe896ade6e5a463d2ecfd4a62d7fc9c5029821`. Se confirma una cuenta de administración existente, pero no hay datos proporcionados para crear o verificar las cuentas reales del resto del equipo.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Accesos separados y protegidos, cinco roles disponibles; sin contactos reales no se pueden provisionar las cuentas faltantes. La matriz por entidad/campo y pruebas con usuarios de cada rol siguen pendientes. |
| US-39 | Parcial funcional | Sin modo trial ni datos demo; servicios productivos de DEV desplegados y versiones alineadas. Falta cargar datos reales aprobados y configurar integraciones externas pendientes. |
| US-40 | Parcial funcional | PWA requiere autenticación para operaciones; falta probar acceso y tareas con los instaladores reales del cliente. |

## Iteración 24 — paginación del kardex (2026-11-07)

El kardex de almacén ahora puede consultarse en páginas consecutivas de hasta 500 movimientos, con orden estable por fecha e identificador. CRM mantiene los filtros por artículo y fecha al cargar más; la descarga CSV incluye todas las páginas cargadas. El límite de la vista de reportes operativos y la PWA permanece en 500 por consulta. No se cambia el saldo ni se modifica ningún movimiento.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-27 | Parcial funcional | El kardex del CRM filtra artículo/fecha, pagina conjuntos mayores a 500 y exporta las filas cargadas, respetando el permiso de costo. Falta exportación completa en un solo archivo y probar volumen real superior al disponible en DEV. |

## Iteración 25 — etiquetas QR para almacén (2026-11-07)

En el catálogo CRM, administración puede abrir e imprimir una etiqueta QR de cada artículo. El código usa el barcode del catálogo o, si no hay uno, un identificador interno basado en el ID del artículo. El escáner PWA ahora reconoce ambos. No se envía información del negocio a servicios externos para generar el QR. Queda probar impresión y lectura con el papel, cámara y lectores que usa ArcoEnergy.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-20 | Parcial funcional | El CRM genera e imprime etiqueta QR con identificador de catálogo y ya conserva marca/modelo/categoría/barcode. Falta validar tamaño/medio de impresión con almacén. |
| US-28 | Parcial funcional | El escáner PWA resuelve barcode capturado y el identificador generado de etiqueta; falta validar cámaras, lectores y formatos en dispositivos reales. |

## Iteración 26 — exportación completa del kardex (2026-11-07)

La descarga CSV del CRM ahora vuelve a consultar todas las páginas de 500 movimientos hasta completar el conjunto filtrado por artículo y fecha. Esto evita que la exportación dependa de cuántas páginas haya cargado visualmente la tabla. Se conserva la protección contra fórmulas de hoja de cálculo y el costo solo aparece para usuarios autorizados. Falta medir exportaciones con el volumen histórico real.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-27 | Parcial funcional | CRM filtra por artículo/fecha, pagina resultados y exporta el conjunto filtrado completo. Falta validar rendimiento con históricos de producción. |

## Iteración 27 — asignación y confirmación de cuadrilla

Una orden de trabajo puede asignarse a varias cuentas activas con rol instalador. Cada integrante ve la orden en la PWA y puede confirmar su propia asignación; la bitácora conserva la confirmación. La autorización de checklist, consumo, devolución y gasto acepta cualquier integrante asignado, no solamente a la persona responsable. Las órdenes existentes conservan su instalador líder al migrar. La actualización de la PWA requiere conexión para confirmar; notificaciones push cuando la app está cerrada todavía requieren configurar un proveedor externo.

La Iteración 27 se integró con el PR [#50](https://github.com/goodmorning-mx/arcoenergy/pull/50), commit `25a34b9d8acffb17cb83ea32af2e26fa49906efc`, y Factory terminó su despliegue DEV en el run [#42330777914](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42330777914). `/api/health/ready`, `/app/login`, `/crm/login`, `/login`, `/app/` y `/crm/` respondieron HTTP 200; API, PWA y CRM reportaron el mismo SHA. La verificación local de navegador no tuvo navegador conectado; el CI integrado de Chrome pasó.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-7 | Parcial funcional | CRM permite asignar una cuadrilla y la PWA confirma individualmente; falta validar el flujo con instaladores reales y configurar push de fondo. |
| US-40 | Parcial funcional | Las órdenes se filtran por asignación y cada instalador confirma desde su cuenta; falta validar en dispositivos y con cuentas reales del cliente. |

## Iteración 28 — vista previa de impactos operativos (2026-11-06)

Antes de registrar una compra, venta, pago a proveedor o cobro de cliente, CRM resume las afectaciones actuales a existencias, caja/banco y saldos relacionados. La compra aumenta existencias; su anticipo sale de la cuenta seleccionada y el remanente queda con el proveedor. Una venta de contado recibe el total en la cuenta seleccionada; una venta a crédito abre el saldo por cobrar. Ambas reservan los materiales en la orden y la existencia física baja cuando se registra su salida. Los pagos reducen o aumentan caja/banco y el saldo de la cuenta correspondiente. No se presentan estos resúmenes como pólizas contables; impuestos, pagos mixtos y Plan 24 requieren validación del contador.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-33 | Parcial funcional | CRM anticipa los efectos vinculados para cuatro acciones operativas. Falta validar reglas contables, impuestos, pagos mixtos y Plan 24 con el contador. |
| US-35 | Parcial funcional | Vista previa de saldo bancario/caja, inventario reservado y cuentas por cobrar/pagar según las reglas actuales. Falta aprobación del flujo contable y de valuación. |

## Iteración 29 — responsabilidad de seguimientos (2026-11-06)

Todo seguimiento comercial se asigna al usuario que lo programa si no se selecciona otro. Administración puede delegarlo a una persona activa del equipo que tenga permiso para gestionar clientes; marketing mantiene la responsabilidad de sus propios registros. El tablero de seguimientos muestra el responsable junto con fecha, cliente y nota, y mantiene las alertas de vencimiento dentro del CRM. Los avisos automáticos por correo, push o WhatsApp requieren seleccionar y configurar un proveedor.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-4 | Parcial funcional | Seguimientos con fecha, bitácora, alertas dentro del CRM y responsable asignado/visible; faltan avisos automáticos y validar el flujo con vendedores reales. |
| US-14 | Parcial funcional | La asignación valida que el responsable pertenezca a la organización, esté activo y tenga permiso comercial; falta completar la matriz de acceso de todas las entidades. |

## Iteración 30 — agenda de cobranza y recordatorios contextuales (2026-11-06)

La cartera puede filtrarse por pagos vencidos, con vencimiento hoy, próximos siete días o ya pagados. El acceso WhatsApp genera un mensaje con el número de cuota, saldo, fecha o días de atraso y forma acordada; el encargado revisa el texto y lo envía en la conversación. La agenda muestra las fechas capturadas, pero las cuotas de un plan se crean manualmente y no hay envío automático.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-11 | Parcial funcional | Agenda filtrable y mensajes contextuales desde WhatsApp; faltan generación del calendario de financiamiento y automatización de envíos, sujetas a reglas y canales aprobados. |

## Iteración 31 — matriz visible de permisos por rol (2026-11-06)

Administración ahora puede consultar en CRM una tarjeta por cada rol disponible y los permisos concretos que el API le asigna. Las etiquetas se traducen para el equipo y los permisos siguen siendo presets del producto, aplicados y validados por el API. Esto hace transparente la configuración existente; no crea permisos individuales ni sustituye la validación de acceso con cuentas reales de cada puesto.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | CRM presenta desde el catálogo autenticado del API los permisos efectivos de los cinco roles. Pendientes pruebas integrales de aislamiento con cuentas reales y validar el alcance de cada permiso con sus responsables. |

## Iteración 32 — vigencia de autorización por membresía

Se comprueba que los endpoints vuelven a leer el estado activo y los permisos actuales de la membresía al autorizar cada solicitud. Las pruebas verifican que un permiso que aparece en un token antiguo deja de dar acceso al cambiar de rol y que una membresía inactiva no se considera válida. También se prueba que los datos de costos del catálogo de inventario se devuelven a contabilidad y se ocultan al instalador.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Pruebas de autorización por membresía activa, cambio de rol y permisos vigentes; costos de inventario ocultos para instaladores y visibles para contabilidad. Pendiente una matriz endpoint/campo revisada con cuentas reales de cada rol y los responsables del negocio. |

## Iteración 33 — revisión y salida física desde solicitud de materiales (2026-11-07)

CRM permite seleccionar una orden, adjuntar temporalmente una foto o PDF de la solicitud y capturar las cantidades revisadas por almacén antes de confirmar. La salida se limita a los materiales y cantidades solicitados, reserva la existencia para órdenes activas y queda vinculada a la orden, renglón y kardex. Desde el mismo flujo se pueden registrar devoluciones o piezas dañadas relacionadas con una salida. La captura es manual: no hay OCR ni extracción automática. El archivo se previsualiza localmente y no se conserva ni sincroniza a Drive; se debe acordar e integrar almacenamiento documental.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-25 | Parcial funcional | CRM acepta foto/PDF como referencia temporal y permite revisar cantidades antes de emitir material y registrar devoluciones ligadas. Pendientes OCR, conservación en Drive y validación del formato operativo con almacén. |
| US-14 | Parcial funcional | Administrador y contador pueden confirmar salidas físicas mediante permiso explícito; instalador, marketing y cliente no reciben ese permiso. Pendiente validar la matriz completa con usuarios reales. |

## Iteración 34 — mantenimiento de ficha de materiales (2026-11-07)

Administración puede corregir la ficha del material desde CRM: nombre, descripción, categoría, marca, modelo, proveedor, código identificador, unidad, mínimo y costo unitario. Las existencias actuales no se editan desde el formulario; deben cambiar mediante movimientos de almacén para conservar su rastro. El código QR/barcode no puede duplicarse y las entradas de kardex históricas conservan su costo registrado aunque se actualice el costo actual del catálogo.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-20 | Parcial funcional | CRM permite corregir los metadatos del catálogo con permiso de administración, valida proveedor y código único y protege el saldo físico. Pendiente acordar unidades de medida válidas y validar impresión/lectura con almacén. |

## Iteración 35 — procedencia estructurada para history cards (2026-11-07)

Las nuevas versiones de tarjeta pueden registrar uno o más artefactos fuente con tipo, referencia durable, canal, ubicación exacta y hash SHA-256 opcional. Se conserva el literal por separado de idioma, atribución, fecha/hora original cuando se conoce y nivel de fidelidad. Cada relación indica si el vínculo representa cita literal, transcripción, paráfrasis, inferencia, validación o reconstrucción. La migración conserva las versiones existentes y las marca `needs_validation` porque no se inventan fechas ni grados de certeza para evidencia previa.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-42 | Parcial funcional | La base de datos y el CRM guardan procedencia estructurada y distinguen literal/transcripción/paráfrasis/inferencia/reconstrucción. Los artefactos sensibles aún requieren almacenamiento privado con retención y permisos definidos; las fuentes históricas necesitan cotejo de stakeholders. |

## Iteración 36 — flujo de caja por periodo y cuenta (2026-11-07)

En Reportes, contador y administración pueden filtrar el flujo de las cuentas activas por fecha. Para el periodo seleccionado se muestran los saldos al inicio y al cierre, saldos de apertura de cuentas iniciadas dentro del periodo y entradas/salidas capturadas. Cada cuenta queda desglosada; las fechas usan `occurred_on`. El reporte explica que resume movimientos guardados y no representa pronóstico ni conciliación bancaria. Las cuentas inactivas quedan fuera; el tratamiento de transferencias internas debe validarse con contabilidad.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-19 | Parcial funcional | Reportes incorpora flujo por periodo y cuenta activa a partir de movimientos y saldos iniciales. Pendientes transferencias entre cuentas, conciliación bancaria y validación de métricas con el contador. |
| US-18 | Parcial funcional | El reporte añade saldo de apertura, entradas, salidas y saldo calculado al cierre por cuenta activa. Pendiente conciliar con estados bancarios y decidir visibilidad de cuentas inactivas. |

## Iteración 37 — limpieza de caché privada al cerrar sesión (2026-11-07)

Al cerrar sesión desde la PWA se borran de IndexedDB las instantáneas locales de órdenes, inventario y movimientos asociadas a la cuenta. Las colas de checklist y de operaciones pendientes permanecen guardadas con el correo propietario para no perder trabajo sin sincronizar; al reiniciar sesión solo la misma identidad puede reanudar la sincronización. Esta entrega reduce la exposición de vistas en equipos compartidos, pero no sustituye borrado remoto, cifrado del dispositivo ni gestión MDM. Falta validar retención y uso compartido en los teléfonos reales.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Al salir se eliminan instantáneas operativas privadas del usuario desde PWA; queda pendiente matriz integral de permisos y política de dispositivos. |
| US-40 | Parcial funcional | Órdenes, inventario y movimientos en caché se limpian al salir sin borrar las acciones locales pendientes; falta validación con usuarios/dispositivos reales y política de borrado remoto. |

## Iteración 38 — estado veraz de las integraciones (2026-11-07)

El endpoint de integraciones ya no confunde configuración parcial con una conexión funcional. Un ID de carpeta de Drive no acredita que se puedan subir o leer documentos; WhatsApp está limitado al flujo click-to-chat, no envío automático. No se modificó la capacidad de almacenamiento. Para cumplir US-13 se necesita implementar el cliente de Drive y configurar credenciales/permisos privados autorizados.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-13 | Pendiente funcional; estado ahora veraz | API informa que Drive no está integrado incluso si existe un ID de carpeta. Faltan carga/lectura, permisos de servicio, retención y sincronización de archivos. |
| US-3 | Parcial | CRM conserva descarga PDF y vínculo click-to-chat; todavía no archiva PDFs en Drive ni envía adjuntos automáticamente. |

### Corrección necesaria para desplegar Iteración 16

El despliegue automático de DEV del commit `4d68416` se revirtió porque PostgreSQL rechaza el nombre de una llave foránea de más de 63 caracteres en la migración de reservas de materiales. Se acorta y se alinea el nombre en el modelo y en la migración. Hasta que se integre y despliegue esta corrección, DEV sigue sirviendo el commit API anterior `7d201b9`; no se considera desplegada la Iteración 16.

## Iteración 39 — archivo privado de cotizaciones en Drive (2026-11-07)

La API puede guardar el PDF foliado de una cotización aprobada en una carpeta privada de Drive usando credenciales de cuenta de servicio configuradas fuera del repositorio. Conserva el ID para reemplazar el documento si se vuelve a generar. El endpoint de integraciones valida acceso real a la carpeta y no confunde un ID configurado con conexión. El CRM descarga el PDF e informa si quedó almacenado, si falta configuración o si falló la carga. WhatsApp sigue siendo click-to-chat y el vendedor adjunta manualmente el PDF.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-3 | Parcial funcional | PDF foliado descargable y archivado en Drive cuando la integración tiene acceso; estado visible en CRM. Falta envío directo del adjunto por WhatsApp y captura/validación de credenciales reales en DEV. |
| US-13 | Parcial funcional | Almacenamiento privado implementado para PDFs de cotización. Faltan documentos contractuales, identificaciones, recibos y sincronización del resto de datos; definir retención, restauración y auditoría. |

## Iteración 40 — compartir cotización como archivo desde CRM y PWA (2026-11-07)

CRM y PWA ofrecen el PDF al diálogo nativo de compartir del dispositivo. En móviles compatibles, el vendedor puede seleccionar WhatsApp y la conversación existente para adjuntar la propuesta. Cuando el navegador no puede compartir archivos, el PDF se descarga y se abre WhatsApp con texto preparado para que el vendedor lo adjunte manualmente. Ninguno de los caminos envía el mensaje automáticamente ni verifica su entrega.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-3 | Parcial funcional | El PDF foliado se puede compartir como archivo desde las interfaces nativas compatibles, con descarga y WhatsApp como fallback. Pendiente validación en dispositivos reales; envío/confirmación automáticos requieren integración y aprobación separadas. |

## Iteración 41 — archivo privado de solicitudes y auditoría de acceso real (2026-11-07)

El CRM permite archivar en Drive una foto o PDF de la solicitud de materiales ligada a la orden. La carga valida tipo de contenido, firma de archivo y tamaño; la consulta del documento pasa por un endpoint autenticado. Si Drive no está configurado o falla, la interfaz lo indica expresamente y registra el movimiento sin afirmar que el documento quedó respaldado. No se agregó OCR manuscrito.

La revisión de DEV confirma que `/login` y `/crm/login` sirven el acceso de escritorio y `/app/login` sirve el acceso móvil; los recursos activos de CRM/PWA no muestran etiqueta ni contador de trial/demo. Las vistas privadas redirigen a su acceso correspondiente. En la organización de DEV hay una cuenta con rol administrador y ninguna cuenta de los roles restantes; la existencia de la ruta de acceso no implica que el equipo ya esté provisionado.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-25 | Parcial funcional | El archivo de solicitud se puede guardar y recuperar en Drive privado desde la orden. Pendientes OCR, cuenta/carpeta de Drive autorizada en DEV y validación del formato de almacén. |
| US-13 | Parcial funcional | Drive admite documentos de cotización y solicitud de materiales al estar conectado. Contratos, INE, recibos, datos operativos, retención y respaldo siguen pendientes. |
| US-14 | Parcial funcional | Las rutas de acceso están separadas y las vistas requieren sesión; DEV contiene solo una cuenta administradora. Falta cargar y validar las cuentas reales y cerrar la matriz completa de privilegios. |
| US-39 | Parcial funcional | No hay UI activa de trial/demo y el acceso al CRM está protegido. Faltan completar las capacidades administrativas descritas en las demás historias y cargar datos aprobados del negocio. |
| US-40 | Parcial funcional | PWA protegida disponible en `/app/login`; no se encontraron usuarios instalador/cliente en DEV. Falta el alta real del equipo y validar tareas/campo en dispositivos. |

## Iteración 42 — acceso visible desde el sitio público (2026-11-07)

La cabecera del sitio público ahora incluye una entrada “Ingresar” hacia `/login`, que dirige al acceso CRM. El acceso móvil continúa disponible en el pie del sitio (`/app/login`) y desde el vínculo “Acceso móvil” de la pantalla de CRM. Los espacios internos siguen protegidos con autenticación; hacer más visible la ruta no crea usuarios ni amplía permisos.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | El usuario puede llegar al login desde la web pública y cada portal conserva su acceso. Falta validar la navegación con cuentas reales de todos los roles y completar la matriz de permisos. |
| US-39 | Parcial funcional | La cabecera del sitio facilita el acceso al CRM desde escritorio; el área interna mantiene login y privilegios. Faltan datos reales y capacidades aún abiertas en las demás tarjetas. |
| US-40 | Parcial funcional | El portal PWA sigue en `/app/login` y enlazado desde el acceso CRM y el pie público. Falta probar con instaladores/clientes provisionados. |

## Iteración 43 — fuente de factura ligada a compra (2026-11-07)

La captura de compra permite adjuntar el CFDI XML ya validado, o una foto/PDF como fuente que se transcribe manualmente. Los datos sugeridos desde XML continúan en revisión humana y no confirman la compra por sí solos. Tras registrar la compra, CRM intenta archivar la fuente en Drive privado y la relaciona con el folio; si Drive no está conectado, avisa que el archivo no quedó respaldado y la operación comercial conserva su estado. Los archivos archivados pueden descargarse desde la cuenta autorizada. No se agregó OCR para PDF/fotografías.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-13 | Parcial funcional | El archivo privado de Drive cubre cotizaciones, solicitudes de materiales y fuente de facturas de compra cuando la integración está activa. Faltan conexión real, documentos legales/INE, sincronización general, retención y respaldo. |
| US-21 | Parcial funcional | Compra multirrenglón conserva la factura asociada en Drive cuando está conectado; el CRM ofrece descarga protegida. Impuestos, fletes y descuentos globales siguen sin distribuirse automáticamente. |
| US-22 | Parcial funcional | El CFDI XML valida y precarga información para revisión; PDF/foto quedan ligados a la compra y requieren captura manual. Pendientes OCR, Drive conectado en DEV y validación de formatos usados por contabilidad. |

## Iteración 44 — acceso a seguimientos por responsable (2026-11-07)

El API ahora devuelve a cada integrante únicamente los seguimientos pendientes asignados a su propia cuenta. Administración conserva la vista global; los vendedores no pueden reasignar seguimientos a otras personas ni completar los que pertenecen a otro responsable. La visibilidad y edición se aplican del lado del servidor además de los controles de interfaz. Las notificaciones push y recordatorios fuera de CRM aún requieren acordar y configurar el canal.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-4 | Parcial funcional | El API filtra seguimientos por responsable, registra su historial y permite a administración la gestión global. Pendientes avisos automáticos y validación con vendedores reales. |
| US-14 | Parcial funcional | El API impide consultar o completar seguimientos de otra persona y limita la reasignación a administración. Falta revisión completa de permisos por entidad/campo con stakeholders y cuentas reales. |

## Iteración 45 — transferencias entre cuentas de efectivo y banco (2026-11-07)

El CRM puede registrar una transferencia desde la cuenta seleccionada hacia otra cuenta activa. El API escribe en una sola transacción una salida y una entrada por el mismo importe, con identificador y descripción compartidos. La operación no aumenta los ingresos ni los gastos consolidados; su reversa genera los dos movimientos compensatorios y conserva los originales. Se rechazan cuentas iguales y fechas anteriores a los saldos iniciales de cualquiera de las cuentas. No se registran comisiones ni se afirma conciliación bancaria.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-18 | Funcional básico | Caja/bancos ahora admite transferencias internas pareadas y reversa auditable. Sigue pendiente conciliar movimientos con estados de cuenta y contabilizar comisiones externas. |
| US-19 | Parcial funcional | Flujo por periodo y cuenta puede reflejar ambos lados de una transferencia sin clasificarla como ingreso o gasto. Quedan conciliación y validación final del flujo con contabilidad. |
| US-35 | Parcial funcional | Cada transferencia vincula sus dos movimientos y se revierte de forma atómica. No sustituye doble partida contable ni conciliación bancaria. |

## Iteración 46 — calendario de cuotas de venta financiada (2026-11-07)

Al registrar una venta a crédito, CRM permite indicar primer vencimiento, entre una y 60 cuotas y frecuencia semanal, quincenal o mensual. El total de la cotización aprobada se divide en centavos y el residuo queda en la última cuota; en frecuencias mensuales se conserva el día del primer vencimiento y se ajusta al último día de los meses más cortos. Cada cuota queda como una cuenta por cobrar individual y aparece en cartera. El cambio no calcula intereses, no agrega comisiones y no activa notificaciones automáticas. Las reglas de Plan 24 y el tratamiento financiero siguen sujetos a validación contable.

La iteración quedó integrada mediante el PR [#70](https://github.com/goodmorning-mx/arcoenergy/pull/70), merge commit `6ccb42b827350e604ee01f580a0750a5f47cfbbf`. Factory completó el despliegue DEV en el run [#42399926877](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42399926877), verificó la revisión de esquema y un respaldo de la base. `/api/health` respondió HTTP 200; API, CRM y PWA reportan el mismo SHA. Backend: 137 pruebas aprobadas; builds de CRM y validación Docker/Chrome pasaron en CI.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-11 | Parcial funcional | La venta financiada genera calendario configurable y cartera por cuota. Falta validar fórmulas e intereses de cada plan con el contador y automatizar recordatorios tras aprobar canal y mensajes. |
| US-16 | Parcial funcional | Cuotas individuales con monto, número y vencimiento pueden cobrarse y consultarse en cartera. Falta aprobación de reglas financieras y envío automático de avisos. |

## Iteración 47 — respuesta mínima para el portal de cliente (2026-11-07)

El endpoint autenticado del portal de cliente deja de serializar directamente los modelos internos de cotización e instalación. La respuesta conserva los datos que la PWA presenta: folio, paneles, inversor, total y estado de la propuesta; folio/fecha/estado/checklist de instalación; y cuotas. Omite costos internos, IDs de Drive, notas privadas de coordinación y correos de instaladores. El filtro por correo autenticado del cliente se mantiene y se añaden pruebas de campos devueltos. Falta validar el portal con cuentas reales y completar la matriz de permisos con los responsables.

La iteración quedó integrada mediante el PR [#71](https://github.com/goodmorning-mx/arcoenergy/pull/71), merge commit `9a83ca8c747475d65e40b6ae702f3bc681ac2f58`. Factory completó el despliegue DEV en el run [#42400874022](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42400874022), verificó esquema y respaldo. API, CRM y PWA reportan el mismo SHA. Backend: 137 pruebas aprobadas; build PWA y validación Docker/Chrome pasaron.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | El portal limita los campos a la vista del cliente además de filtrar registros por correo. Faltan pruebas con cuentas reales de cada rol y validación integral de permisos por entidad/campo. |
| US-40 | Parcial funcional | La PWA cliente recibe solo datos para propuestas, órdenes y pagos. Falta validar la experiencia con cuentas reales de cliente. |

## Iteración 48 — correcciones de caja con motivo y origen protegido (2026-11-07)

Las reversas de movimientos manuales ahora requieren un motivo que se conserva en la descripción de la reversa y el enlace al movimiento original. Las transferencias conservan la reversa pareada en ambas cuentas y comparten el motivo. La reversa genérica rechaza movimientos ligados a ventas, gastos, pagos u operaciones derivadas; esos registros deben corregirse desde su operación de origen para no dejar caja y el registro relacionado con saldos distintos. No se permite borrar ni revertir una reversa.

La iteración quedó integrada mediante el PR [#72](https://github.com/goodmorning-mx/arcoenergy/pull/72), merge commit `f0a051e8448c58ea3783110fb9f75bd27ab2e49c`. Factory completó el despliegue DEV en el run [#42401833891](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42401833891), verificó el esquema y el respaldo. `/api/health` respondió HTTP 200; API, CRM y PWA reportan el mismo SHA. Backend: 139 pruebas aprobadas; build CRM y Docker/Chrome pasaron.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-36 | Parcial funcional | Reversa manual con motivo, enlace al original y corrección pareada de transferencias; pagos de proveedores/clientes ya usan origen. Pendientes reversas integrales de ventas, gastos e inventario. |
| US-18 | Funcional básico | Las correcciones directas de caja se limitan a movimientos manuales y transferencias; operaciones comerciales se corrigen desde su origen. Pendientes conciliación y comisiones. |
| US-35 | Parcial funcional | Se evita desincronizar caja de gastos, ventas y pagos por una reversa genérica. Falta el ciclo de corrección de origen para todas las operaciones relacionadas. |

## Iteración 49 — corrección de gastos desde su origen (2026-11-07)

La corrección de un gasto es append-only: conserva el registro original y agrega un gasto compensatorio enlazado con el motivo y la fecha de corrección. Si el gasto salió de una cuenta de caja o banco, la misma operación registra la entrada compensatoria enlazada al egreso original. Una restricción única impide corregir dos veces el mismo gasto. El endpoint rechaza a instaladores y bloquea inconsistencias entre el gasto y su movimiento de cuenta. El costeo suma ambos registros; reporta el importe neto, conservando sus fechas e historial. El gasto original de campo sin cuenta puede compensarse sin inventar un movimiento bancario.

La implementación se integró mediante el PR [#73](https://github.com/goodmorning-mx/arcoenergy/pull/73), merge commit `a9e4d44d68cdfd070f186de6e30157f7b8714ad3`. Factory completó el despliegue DEV en el run [#42403422316](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42403422316), con migración de esquema y respaldo confirmados. `/api/health` y las tres rutas de acceso respondieron HTTP 200; API, CRM y PWA reportan el mismo SHA. Backend: 141 pruebas aprobadas; builds de CRM/Next, Docker/Chrome y PWA pasaron en CI. El chequeo de reporte de evento externo de CI falló por una dependencia ajena a esta funcionalidad, como en iteraciones anteriores.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-17 | Funcional básico | Gastos administrativos corregibles desde su origen con motivo; los registros originales permanecen. Pendientes anticipos/reembolsos y autorización de gastos de campo. |
| US-18 | Funcional básico | La corrección del gasto restaura caja/banco en pareja y conserva trazabilidad. Pendiente conciliación bancaria. |
| US-35 | Parcial funcional | Gastos y saldos de cuenta se compensan desde una sola operación; reversas de venta, compra e inventario siguen pendientes. |
| US-36 | Parcial funcional | Corrección append-only y enlazada para gastos, además de caja manual, transferencias y pagos. Pendientes los demás ciclos de corrección. |
| US-38 | Parcial funcional | La corrección de gasto compensa el resultado del proyecto/periodo con su fecha de registro. El informe sigue siendo preliminar. |

## Iteración 50 — corrección de venta de contado preinstalación (2026-11-07)

La venta de contado puede corregirse con un motivo obligatorio solo si la orden sigue asignada, ningún instalador la ha confirmado y todavía no hay actividad física de materiales, checklist de instalación ni cobros derivados. La operación append-only conserva venta y folio, crea la reversa enlazada al ingreso, registra una tarjeta de corrección única, cancela la orden y libera la reserva de inventario dentro de la misma transacción. La cancelación también se conserva en la bitácora del cliente. La PWA impide después confirmar la orden, emitir/consumir material o registrar gastos en ella. Las ventas a crédito y las órdenes que ya comenzaron quedan protegidas y requieren sus propios ciclos de corrección antes de habilitarlas.

La implementación se integró mediante el PR [#75](https://github.com/goodmorning-mx/arcoenergy/pull/75), merge commit `3310c4f978cf498505616b7acad4982cd8f9d853`. Factory completó el despliegue DEV en el run [#42405193148](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42405193148), verificó el esquema y el respaldo. `/api/health` y `/login`, `/crm/login`, `/app/login` respondieron HTTP 200; API, CRM y PWA reportan el mismo SHA. Backend: 143 pruebas aprobadas; builds de CRM/Next, Docker/Chrome y PWA pasaron en CI. El chequeo externo de reporte de evento volvió a fallar por la dependencia ajena a la funcionalidad.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-15 | Parcial funcional | Se puede corregir una venta de contado preinstalación; Iteración 51 añade ventas a crédito sin cobranza neta. Ventas con pagos activos o avance/material emitido requieren flujos adicionales. |
| US-18 | Funcional básico | La reversa enlazada de venta restaura la misma cuenta de caja/banco. Conciliación sigue pendiente. |
| US-32 | Parcial funcional | Folio y orden originales se conservan y se marcan cancelados; sigue pendiente la entidad de proyecto independiente. |
| US-35 | Parcial funcional | Caja, orden y reserva se actualizan en conjunto al corregir una venta elegible. Crédito sin cobros netos se añade en Iteración 51; inventario emitido, reglas fiscales y doble partida siguen pendientes. |
| US-36 | Parcial funcional | Reversa integral disponible para gastos y ventas elegibles, además de correcciones de caja/transferencias/pagos existentes. Falta venta a crédito con pagos activos, compras y movimientos físicos de inventario. |
| US-38 | Parcial funcional | El reporte incorpora la corrección de venta en el periodo de registro. El resultado todavía es operativo y preliminar. |

## Iteración 51 — corrección de venta financiada sin cobranza neta (2026-11-08)

La corrección de una venta financiada requiere que la orden siga sin actividad de campo y que no haya saldo pagado neto ni cobros sin reversa. Si hubo cobros, primero se corrigen desde el historial de cada cuota. La operación conserva venta, cuotas, orden y folio originales; agrega una corrección enlazada sin movimiento de caja, cancela la orden y libera la reserva. Las cuotas corregidas dejan de aparecer en cartera, panel, y portal de cliente, y se rechazan intentos de cobro tardíos. El reporte de rentabilidad ya resta la corrección en su fecha. Los datos originales permanecen disponibles para auditoría.

Implementación integrada mediante PR [#77](https://github.com/goodmorning-mx/arcoenergy/pull/77), merge SHA `783a03ea5de3e09b8952da3064ebcefafb3eb0e6`. Factory desplegó DEV en el run [#42436672678](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42436672678), con revisión de esquema y respaldo confirmados. `/api/health`, `/api/version`, `/login`, `/crm/login`, `/app/login` y `/` respondieron HTTP 200; API, CRM y PWA reportan el mismo SHA. Backend: 144 pruebas; CI de Backend, CRM, Frontend, Next.js y Docker/Chrome aprobadas. El reporte de evento externo de CI falló por su notificador ajeno a la funcionalidad.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-11 | Parcial funcional | Se ofrece corrección de financiamiento sin cobranza neta y desaparecen cuotas anuladas de cartera; fórmulas/intereses y avisos automáticos siguen pendientes. |
| US-15 | Parcial funcional | Ventas de contado y crédito pueden corregirse antes de actividad de campo; ventas con pagos netos activos requieren reversas previas y órdenes iniciadas siguen bloqueadas. |
| US-16 | Parcial funcional | Cuotas corregidas dejan de presentarse y no admiten nuevos cobros; pagos distribuidos, reglas definitivas del financiamiento y notificaciones siguen pendientes. |
| US-35 | Parcial funcional | La corrección enlaza venta, cartera, orden y reserva de inventario antes de campo; siguen pendientes otras operaciones relacionadas, doble partida y reglas fiscales. |
| US-36 | Parcial funcional | Se agrega reversa de crédito sin cobro neto; falta cerrar corrección de ventas con actividad, compras y movimientos físicos de inventario. |
| US-38 | Parcial funcional | Rentabilidad compensa la venta en la fecha de corrección; estados financieros formales, impuestos, intereses y validación del contador siguen pendientes. |

## Iteración 52 — avisos locales de inventario bajo en la PWA (2026-11-08)

La PWA permite al usuario autorizar avisos del dispositivo desde Inventario. Con permiso concedido, la aplicación revisa el stock disponible contra el mínimo configurado por artículo y agrupa los artículos nuevos bajo mínimo en un solo aviso. La lista de artículos ya avisados se conserva por sesión para evitar repetir notificaciones; se vuelve a avisar si el artículo recupera stock y luego vuelve a caer. Mientras la PWA está abierta y conectada, consulta el inventario cada minuto. El aviso local no es una notificación push: para detectar cambios con la aplicación cerrada hace falta definir un servicio push y los destinatarios centrales.

Implementación integrada mediante PR [#79](https://github.com/goodmorning-mx/arcoenergy/pull/79), merge SHA `252eff7fbe9b54f972bdde68070759a7924c1414`. Factory desplegó DEV en el run [#42438040513](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42438040513); la ejecución verificó revisión de esquema y respaldo. `/api/health`, `/api/version`, las rutas de login y las páginas CRM/PWA respondieron HTTP 200; API, CRM y PWA reportan el mismo SHA. Backend: 145 pruebas aprobadas; CI de Frontend, CRM, Next.js y Docker/Chrome aprobado. El reporte externo `report` falló por el notificador de eventos ajeno al producto.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-26 | Parcial funcional | Aviso local agrupado según el mínimo por artículo con permiso explícito; falta push en segundo plano y acordar destinatarios. |

## Iteración 53 — corregir compras desde su origen (2026-11-08)

Administración o contabilidad puede corregir una compra solo cuando no tiene pagos activos y ninguno de sus materiales presenta movimientos de almacén posteriores. Primero se revierten los pagos desde su historial; sus movimientos compensatorios se conservan. La corrección agrega una fila enlazada y movimientos de salida de almacén relacionados con las entradas originales, repone al proveedor su saldo previo a la compra, conserva factura y renglones, y restaura el costo unitario previo que quedó guardado al registrar la compra. Compras antiguas sin el costo previo registrado requieren conciliación manual; movimientos de inventario posteriores requieren un flujo aparte de devolución. No se borran registros.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-21 | Parcial funcional | La compra conserva sus renglones/factura y ahora se puede compensar antes de uso posterior; impuestos, fletes y descuentos siguen sin regla contable aprobada. |
| US-31 | Parcial funcional | Reversa de compra y pagos enlazados actualiza saldo proveedor, caja y almacén; conciliación sigue pendiente. |
| US-35 | Parcial funcional | Compras previas a movimientos posteriores pueden corregirse con enlaces entre cuenta por pagar e inventario; falta cierre contable de doble partida. |
| US-36 | Parcial funcional | Gastos, ventas elegibles y compras elegibles tienen corrección append-only desde origen. Faltan devoluciones/mermas comerciales con actividad de campo y ajustes complejos de inventario. |
| US-38 | Parcial funcional | El inventario disponible y su costo unitario se restauran en la corrección; estados de resultados formales y validación contable siguen pendientes. |

La primera aplicación de Iteración 53 en DEV falló al detectar que la tabla nueva no existía en una base ya inicializada y Coolify revirtió el contenedor. El PR correctivo [#82](https://github.com/goodmorning-mx/arcoenergy/pull/82) agregó la creación explícita e idempotente de esa tabla; el despliegue final terminó correctamente en Factory run [#42439887917](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42439887917), con la revisión de esquema 064 y el respaldo verificados. API, CRM y PWA reportan el mismo commit `292446d530187f4ec08770a16dd74c238ea48dfd`. `/`, `/api/health`, `/api/version`, `/login`, `/crm/login` y `/app/login` respondieron HTTP 200; Chrome headless renderizó el texto «Iniciar sesión» en las tres rutas de acceso. Backend: 148 pruebas aprobadas; CI de Backend, CRM, Frontend, Next.js y Docker/Chrome aprobado. El chequeo externo `report` continúa fallando por el notificador de eventos del repositorio, separado del despliegue del producto.

## Iteración 54 — verificación del agente público y catálogo comercial (2026-11-08)

Se verificó en DEV el asistente público con dos consultas reales, sin crear prospectos ni cotizaciones. La consulta sobre tamaños devolvió HTTP 200 en español. Al pedir una propuesta de 8 paneles, el agente explicó que el catálogo no ofrece un paquete activo y aprobado para esa cantidad, y no inventó un precio. La clave administrada del modelo está configurada y operativa; la falta de cotización se debe al catálogo comercial pendiente, no a un error del asistente. El resultado quedó agregado como versión nueva, sin cambiar el relato literal de US-41.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-41 | Parcial funcional | El agente web está operativo y se niega a inventar un precio ante un paquete no aprobado. Administración debe cargar/aprobar los paquetes reales; falta probar el formulario con consentimiento y cotejar el catálogo con ventas. |

El asistente se verificó mediante `POST /api/v1/public/agent/chat` (HTTP 200) con consultas de tamaños y cotización de 8 paneles. La primera respuesta fue “Manejamos sistemas que van desde un mínimo de 4 paneles hasta un máximo de 20 paneles”; la segunda indicó que no había paquete activo aprobado para 8 paneles. No se enviaron datos personales. La migración 065 conserva la fuente original y agrega la verificación como una nueva versión de US-41.

Implementación integrada mediante PR [#84](https://github.com/goodmorning-mx/arcoenergy/pull/84). Factory desplegó DEV en el run [#42441554812](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42441554812), con revisión 065 y respaldo confirmados. API, CRM y PWA reportan el mismo commit `c4d240f96773e2f0a6b97482e583e77829e5c0be`; `/`, `/api/health`, `/api/version`, `/login`, `/crm/login` y `/app/login` respondieron HTTP 200. Backend: 149 pruebas; CI de Backend, CRM, Frontend, Next.js y Docker/Chrome aprobado. El notificador externo `report` sigue fallando sin afectar este despliegue.

## Iteración 55 — trazabilidad precisa de history cards (2026-11-08)

Se agregan versiones nuevas de US-39, US-40 y US-41 para que cada interpretación identifique el fragmento literal de la fuente del dueño del producto que la sustenta. El texto completo original de cada tarjeta permanece intacto. US-42 registra el estado implementado del historial append-only en base de datos, API y CRM, y conserva como pendientes el cotejo de historias reconstruidas y la política de almacenamiento privado para artefactos sensibles. Esto mejora la procedencia; no equivale a que los stakeholders hayan validado sus interpretaciones.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-39 | Parcial funcional | Se enlaza el fragmento literal sobre el CRM. La cobertura empresarial completa y las cuentas de equipo reales siguen pendientes de los flujos y datos correspondientes. |
| US-40 | Parcial funcional | Se enlaza el fragmento literal sobre la PWA móvil operativa. Falta validar tareas, permisos y dispositivos con el personal real. |
| US-41 | Parcial funcional | Se enlaza el fragmento literal sobre cotización web mediante agente y módulos. El catálogo comercial aprobado y la validación del flujo de venta siguen pendientes. |
| US-42 | Funcional para registro/versiones | DB, API y CRM ya conservan versiones append-only. El cotejo de tarjetas reconstruidas y la política de conservación privada de fuentes sensibles siguen pendientes. |

La migración `202611080066` (revision 066) no actualiza ni elimina filas previas. La prueba de migración comprueba que el literal se conserva en las versiones anterior y nueva y que se añaden vínculos de fuente específicos.

La implementación quedó integrada en el PR [#86](https://github.com/goodmorning-mx/arcoenergy/pull/86), commit de merge `0659cc199bf5976cbbb1cc4334a6a7dfb55f47ff`. Factory terminó la reconciliación DEV en el run [#42442879877](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42442879877); la base informa revisión 066 y el respaldo externo quedó verificado. La consulta de solo lectura confirmó versiones nuevas y ubicaciones específicas para US-39 a US-42. API, CRM y PWA reportan el mismo commit; `/`, `/login`, `/crm/login`, `/app/login`, `/api/health` y `/api/health/ready` respondieron HTTP 200. CI del PR aprobó Backend, CRM, Frontend, Next.js y Docker/Chrome; backend: 150 pruebas aprobadas. El job externo `report` falló, sin afectar la integración ni el despliegue.

## Iteración 56 — paginación y exportación completa del kardex (2026-11-08)

El reporte operativo ahora pagina el kardex por bloques de hasta 500 movimientos para el intervalo solicitado. CRM muestra el total, permite cargar páginas adicionales y descarga el intervalo completo a CSV, solicitando las páginas restantes antes de generar el archivo. El API mantiene visibles los costos solo para los roles con permiso. El filtro se conserva en todas las páginas y las consultas rechazan límites inválidos o desplazamientos negativos.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-27 | Parcial funcional | Filtro por fechas y artículo, paginación y exportación CSV completa del intervalo; falta validar rendimiento con el histórico real del almacén. |
| US-29 | Parcial funcional | El kardex de reportes supera el límite de 500 mediante paginación y CSV completo. Falta acordar y validar los reportes financieros y sus fórmulas con contabilidad. |

La API responde `total`, `offset`, `limit` y `has_more` para el kardex, conservando `truncated` por compatibilidad. La migración `202611080067` agrega versiones de US-27 y US-29 sin alterar los relatos fuente ni las revisiones previas.

La implementación se integró mediante el PR [#88](https://github.com/goodmorning-mx/arcoenergy/pull/88), merge commit `26ce89aa59c0155a5086e674e98b395253ae3eda`. Factory terminó DEV en el run [#42444210651](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42444210651); PostgreSQL informa la revisión 067 y las versiones nuevas de US-27/US-29 están registradas. API, CRM y PWA reportan el mismo SHA; `/api/health`, `/api/health/ready`, `/crm/login` y `/app/login` respondieron HTTP 200. CI en PR y push aprobó Backend, CRM, Frontend, Next.js y Docker/Chrome; Backend: 152 pruebas aprobadas. El job externo `report` volvió a fallar sin afectar el despliegue.

## Iteración 57 — detalle de reportes operativos (2026-11-08)

El reporte operativo agrega listados de clientes, proveedores y órdenes, y un detalle de gastos con categoría, proyecto, cuenta, fecha y responsable. Clientes, proveedores y órdenes se presentan como fotografía actual; el gasto conserva el intervalo de fechas elegido. Se excluyen teléfono, domicilio, RFC, correo y enlaces de comprobantes de estos listados. Las correcciones de gasto permanecen identificadas y sus importes compensatorios no se ocultan.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-29 | Parcial funcional | Incluye detalles operativos para clientes, proveedores, órdenes y gastos. Falta que contabilidad valide los campos requeridos, defina fórmulas/estados financieros y confirme los criterios de fecha para sus reportes finales. |

La migración `202611080068` agrega una nueva versión de US-29 sin editar la fuente literal ni las revisiones existentes. El reporte no se presenta como cierre contable y las fórmulas financieras permanecen sujetas a validación del contador.

La implementación quedó integrada mediante el PR [#90](https://github.com/goodmorning-mx/arcoenergy/pull/90), merge commit `dea2802cd126a90e3c32ce39e673ba82ba51f054`. En DEV, `/api/version` informa ese mismo SHA; `/api/health/ready`, `/`, `/crm/login` y `/app/login` respondieron HTTP 200. El CRM desplegado incluye las tablas de detalle y PostgreSQL informa la revisión `202611080068`; la base registra US-29 versión 5 para esta iteración. Pasaron Backend (153 pruebas), CRM typecheck/build y los checks CI de Backend, CRM, Frontend, Next.js y Docker. El job auxiliar `report` del PR falló, mientras todos los checks de producto terminaron correctamente. El plan de Factory confirmó los cinco recursos de aplicación y PostgreSQL existentes; la evidencia de runtime y revisión de base confirma el despliegue efectivo en DEV.

## Iteración 58 — comprobantes privados de gastos en Drive (2026-11-08)

CRM permite adjuntar un comprobante PDF/JPG/PNG/WebP de hasta 12 MiB a un gasto y descargarlo con autenticación. El archivo se guarda en la carpeta privada de Drive mediante la integración existente; los IDs privados no se devuelven al navegador. La captura de un gasto sigue siendo exitosa aunque Drive no esté configurado, pero la interfaz declara el archivo pendiente y permite reintentar la carga. Se conserva el campo previo de enlace externo.

La carga requiere `expenses:write`, la descarga requiere `expenses:read`; los instaladores solo pueden asociar archivos a gastos de órdenes asignadas. La PWA todavía no adjunta comprobantes y el archivo no se pone en cola offline. No se amplía el alcance a INE/contratos ni a sincronización de todos los datos empresariales.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-10 | Parcial funcional | El registro de gastos de campo y la captura contable se mantienen; CRM admite comprobante privado. La PWA aún no adjunta archivos y la política de revisión de gastos sigue pendiente. |
| US-13 | Parcial funcional | Drive cubre cotizaciones, solicitudes de materiales, facturas de compra y ahora comprobantes de gastos. Faltan documentos legales/INE, política de carpetas, retención, restauración y sincronización general. |
| US-17 | Parcial funcional | CRM puede archivar y descargar el comprobante de un gasto en Drive; pendientes la política de comprobación, aprobación y el flujo móvil. |

La migración `202611080069` añade metadatos de archivo a gastos sin reemplazar sus enlaces previos; `202611080070` agrega versiones append-only de las tarjetas relacionadas.

## Iteración 59 — comprobantes de gastos desde la PWA (2026-11-08)

La PWA de campo ahora permite adjuntar al gasto un comprobante opcional PDF/JPG/PNG/WebP de hasta 12 MiB, usando la cámara trasera cuando el navegador móvil lo ofrece. Si no hay conexión, IndexedDB conserva el gasto idempotente y el archivo como `Blob`, vinculados a la identidad autenticada. Al regresar la conexión, primero se confirma el gasto y después se sube el archivo a Drive; la operación local solo se elimina tras ambas confirmaciones. Si Drive no está configurado o falla, el archivo permanece en cola y se puede reintentar sin duplicar el gasto. Descartar explícitamente operaciones pendientes advierte que también eliminará comprobantes locales.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-10 | Parcial funcional | CRM y PWA admiten comprobantes privados; la PWA los mantiene offline y reintenta el archivado sin duplicar gastos. Pendientes política de aprobación/revisión y configuración autorizada de Drive en DEV. |
| US-13 | Parcial funcional | Los comprobantes de campo ahora llegan a Drive desde móvil incluso tras captura sin conexión. Sigue pendiente sincronización general de datos, documentos legales, permisos/carpetas y retención/restauración. |
| US-17 | Parcial funcional | El gasto de campo acepta archivo en la PWA y conserva el archivo pendiente hasta confirmación de Drive. La política contable de comprobación y aprobación requiere validación. |

La migración `202611080071` registra nuevas versiones append-only para US-10, US-13 y US-17; conserva intactos los relatos originales.

La implementación se integró mediante el PR [#93](https://github.com/goodmorning-mx/arcoenergy/pull/93), merge commit `6c8712c3d8b943b856232b1013e014b56675e912`. Factory completó el despliegue DEV y la verificación de esquema/respaldo en el run [#42447576484](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42447576484). API, CRM y PWA reportan el mismo SHA; PostgreSQL informa `202611080071` y las versiones activas de US-10, US-13 y US-17 corresponden a Iteración 59. Chrome headless renderizó el acceso en `/login`, `/crm/login` y `/app/login`; la PWA desplegada incluye el control de comprobante. `/`, las rutas de acceso y `/api/health/ready` respondieron HTTP 200. Pasaron CI Backend, CRM, Frontend, Next.js y Docker; 161 pruebas backend locales. El job auxiliar `report` falló sin afectar la integración ni el despliegue.

## Iteración 60 — datos de contacto en órdenes asignadas (2026-11-08)

La PWA muestra al instalador asignado el domicilio del proyecto y acciones para llamar al cliente o redactar un correo desde el teléfono. La respuesta del endpoint de instalaciones limita el objeto de contacto a nombre, ciudad, domicilio, teléfono y correo; ya no devuelve estado/procedencia del registro CRM. Las órdenes visibles para el rol instalador siguen filtradas a las que están asignadas a su cuenta. El aviso cuando la aplicación está cerrada sigue pendiente de canal push/mensajería configurado, y la experiencia debe probarse con el personal real.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-7 | Parcial funcional | El instalador de una orden asignada puede ver ubicación y medios de contacto del cliente y usar enlaces `tel:`/`mailto:`. Falta un canal de notificación en segundo plano y validación con instaladores reales. |
| US-14 | Parcial funcional | La lista limita instalaciones del instalador a sus asignaciones y ofrece un resumen mínimo de cliente. Falta validar toda la matriz de acceso por entidad/campo con responsables y cuentas reales. |

La migración `202611080072` registra nuevas versiones append-only de US-7 y US-14 y conserva intactas las fuentes literales.

La implementación se integró mediante el PR [#95](https://github.com/goodmorning-mx/arcoenergy/pull/95), merge commit `08fc60d0eae19512368dfd9134f437c275a9e1ef`. Factory completó DEV y la verificación de esquema/respaldo en el run [#42448484925](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42448484925). API, CRM y PWA reportan el mismo SHA y PostgreSQL informa `202611080072`; las versiones activas de US-7 y US-14 quedaron en Iteración 60. `/`, `/api/health/ready`, `/login`, `/crm/login`, `/app/login` y las rutas de versión respondieron HTTP 200. Chrome headless renderizó los tres accesos; el bundle PWA desplegado contiene los enlaces de llamada y correo. CI Backend, CRM, Frontend, Next.js y Docker pasó; Backend: 163 pruebas locales. El job auxiliar `report` falló sin afectar la integración ni el despliegue.

## Iteración 61 — avisos push de asignación a instaladores (2026-11-08)

La PWA permite al instalador activar o desactivar Web Push desde la vista de instalaciones. La suscripción queda vinculada al correo autenticado, puede existir en varios dispositivos y el API limita altas/bajas a la cuenta con rol `instalador`. Al crear una orden o aceptar una venta que crea una orden, el API programa un aviso a cada instalador suscrito y asignado; el payload incluye únicamente el folio y una ruta interna, sin datos personales del cliente. El service worker presenta el aviso aun con la PWA cerrada y abre `/app/` al tocarlo. Los endpoints de suscripción aceptan solo servicios push conocidos por HTTPS; la clave VAPID se deriva de un secreto persistente administrado por Factory.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-7 | Parcial funcional | La asignación incluye aviso push opcional con la app cerrada y conserva el detalle de contacto dentro de la PWA. Falta validar recepción/desactivación en los dispositivos reales del equipo. |
| US-40 | Parcial funcional | La PWA registra suscripciones Web Push y el service worker recibe avisos en segundo plano. Falta validar instalación y entrega en los teléfonos y sistemas operativos usados por campo. |

La migración `202611080073` agrega el almacenamiento de suscripciones y registra versiones nuevas de US-7/US-40 sin modificar los relatos literales. La clave `WEB_PUSH_VAPID_SECRET` se configura como secreto generado y persistido en el manifiesto de DEV de Factory; el API no habilita registro push si falta esa variable.

La rama `feature/installer-webpush` se integró en DEV mediante PR [#97](https://github.com/goodmorning-mx/arcoenergy/pull/97), merge commit `dd748fc9c5e2fb6553c3fc5e3233384fc5476c56`. Factory completó el reconciliador resources-v3 en el run [#42541277575](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42541277575): aplicación/despliegue, verificación de revisión de esquema y reconciliación de respaldos terminaron correctamente. El API vivo informa el SHA del merge y estado `ready`; la especificación OpenAPI publicada contiene las rutas de VAPID y suscripción. El sitio, CRM, PWA y `/login`, `/crm/login`, `/app/login` responden HTTP 200. La lectura anónima de la clave VAPID devuelve 401 porque requiere sesión y rol instalador; no hay cuentas/dispositivos reales de instalador disponibles para confirmar recepción push, que permanece pendiente. El CI de la rama del PR aprobó Backend, CRM, Frontend, Next.js y Docker/Chrome.

## Iteración 62 — responsables y avisos de reabasto (2026-11-09)

Administración puede asignar un instalador activo a la reposición de cada artículo junto con su mínimo. El responsable debe activar Web Push en la PWA. El API calcula disponibilidad incluyendo reservas de órdenes y emite un aviso cuando cae al mínimo; evita repetirlo mientras permanece bajo el umbral y rearma la alerta cuando se recupera. Considera las reservas al vender, las salidas/consumos, devoluciones, compras, correcciones de compras/ventas y cambios del umbral. Si el instalador se suscribe cuando el artículo ya está bajo, se le informa al registrar el dispositivo. El payload solo incluye nombre del material, existencia, mínimo y ruta interna.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-26 | Parcial funcional | Administración asigna un instalador activo como responsable; Web Push se envía al cruzar el mínimo y se rearma al reponerse. Falta validar la entrega en teléfonos reales y confirmar si almacén requiere otro rol. |
| US-40 | Parcial funcional | La PWA recibe push de reabasto en segundo plano y evita duplicar el aviso local cuando existe una suscripción. Falta validar instalación y recepción en dispositivos reales. |

La migración `202611090074` agrega responsable y estado de alerta al inventario y versiona US-26/US-40 sin editar su fuente original. `/version` ahora informa también la revisión Alembic para que Factory pueda verificar esquema vivo.

## Iteración 63 — avisos de seguimiento en CRM (2026-11-09)

El CRM permite a cada usuario activar avisos del navegador con permiso explícito. Mientras el CRM está abierto, actualiza la agenda cada minuto y muestra un aviso genérico para seguimientos vencidos o con fecha de hoy, sin exponer el nombre ni la nota del cliente en la pantalla de notificaciones. Cada seguimiento se avisa una vez por cuenta y navegador. La bandeja del CRM sigue mostrando el detalle y permite completar el contacto. El aviso no funciona cuando se cierra el CRM; push, correo o WhatsApp en segundo plano requieren definir y configurar el canal, y probarlo con el equipo real.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-4 | Parcial funcional | Se agregan avisos del navegador autorizados, con actualización periódica y deduplicación local; faltan avisos con CRM cerrado y validación con vendedores reales. |
| US-39 | Parcial funcional | El CRM presenta notificaciones genéricas de seguimientos dentro de una sesión abierta; faltan canal de fondo y cuentas reales para validar. |

La migración `202611090075` agrega versiones append-only para US-4 y US-39; conserva intactos los relatos originales. La alerta consulta los seguimientos que ya pertenecen al usuario autenticado y no crea ni reasigna tareas.

La implementación se integró en el PR [#100](https://github.com/goodmorning-mx/arcoenergy/pull/100), merge commit `e2276862ba0b36c796e1176ac39ae9b27c31e27b`. La reconciliación de Factory se integró en el PR [#419](https://github.com/goodmorning-mx/goodmorning-factory/pull/419), merge commit `86aa3ef53479ee6906e11c7def2417496cb3a9fe`, y el run [#42544540084](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42544540084) terminó correctamente después de aplicar recursos, verificar la revisión viva y reconciliar respaldos. La API DEV informa el commit `e2276862ba0b36c796e1176ac39ae9b27c31e27b`, esquema `202611090075` y estado `ready`; el bundle publicado del CRM contiene el control para activar avisos. `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. La suite backend local pasó con 186 pruebas, el build TypeScript/Vite de CRM pasó y 34 contratos de Factory pasaron. En el PR del producto GitHub Actions no ejecutó los jobs (todos fallaron antes de iniciar pasos por el límite de facturación); esa limitación no se oculta como CI aprobada.

## Iteración 64 — recordatorios push de seguimiento (2026-11-09)

La opción anterior de aviso solo mientras el CRM estaba abierto se sustituye por Web Push. La persona activa del equipo puede autorizar avisos desde Seguimientos; CRM reutiliza el service worker de la PWA y el servidor registra el dispositivo ligado al correo autenticado. Un proceso en la API revisa fechas vencidas o del día cada minuto y envía el aviso genérico a los dispositivos suscritos de la persona asignada. El registro de vencimiento usa una actualización condicional para que varias instancias no reclamen el mismo recordatorio a la vez; las fallas transitorias quedan listas para reintento. Al tocar la notificación se abre `/crm/`. El texto no incluye datos del cliente.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-4 | Parcial funcional | Recordatorio push independiente de CRM abierto, ligado a la persona responsable y sin datos de cliente; falta validación en dispositivos y navegadores comerciales reales. |
| US-39 | Parcial funcional | Administración y marketing pueden autorizar Web Push desde CRM; falta validar con las cuentas y dispositivos del equipo. |
| US-40 | Parcial funcional | El service worker PWA recibe el recordatorio y puede abrir CRM; falta validar la navegación cruzada y entrega en dispositivos reales. |

La migración `202611090076` renombra la columna de suscripciones a `user_email`, conserva sus propietarios, agrega marcas de reclamo/entrega a seguimientos y crea versiones append-only de US-4/US-39/US-40. Los reclamos abandonados vencen para reintentar; los avisos solo se envían al responsable vigente del seguimiento. El endpoint de suscripción confirma propiedad por cuenta y dispositivo.

El producto quedó integrado en DEV por el PR [#102](https://github.com/goodmorning-mx/arcoenergy/pull/102), merge commit `c2a6d0b1685afce32d6c688665e1f543b87a1c2c`. Factory integró el contrato de esquema por el PR [#420](https://github.com/goodmorning-mx/goodmorning-factory/pull/420) y el run [#42546327554](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42546327554) terminó correctamente: despliegue, revisión viva `202611090076` y reconciliación de respaldos aprobados. La API reportó el commit y esquema esperados y `health/ready` respondió `ready`; `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. El bundle publicado del CRM incluye la opción de activar avisos push y su service worker permite `/crm/`. Validación local previa: 190 pruebas backend, builds de CRM y PWA, 34 contratos de Factory. Los workflows de CI del PR de producto no ejecutaron pasos por el límite de facturación de GitHub; los resultados locales se registran separadamente y no como CI aprobada.

## Iteración 65 — disponibilidad de material por orden (2026-11-09)

La PWA y el CRM muestran cuánto material solicitado queda disponible para cada orden, cuánto falta para completarla y las cantidades solicitadas/entregadas/consumidas. El cálculo parte de la existencia física y conserva las reservas de las demás órdenes abiertas; elimina la inferencia incorrecta que presentaba el faltante global como si perteneciera a cada proyecto. No crea movimientos de almacén ni cambia las reservas. Para solicitudes nuevas, el flujo de venta sigue validando existencias antes de confirmar.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-8 | Parcial funcional | Disponibilidad y faltante calculados por orden en CRM/PWA considerando reservas de otras órdenes abiertas. Pendiente validar contra movimientos y existencias reales en campo. |
| US-40 | Parcial funcional | PWA diferencia material cubierto y faltante por proyecto incluso con snapshots almacenados; falta validar el flujo con instaladores y stock real. |

La migración `202611090077` agrega una versión append-only de US-8 que conserva intacta la fuente original. La prueba cubre dos órdenes concurrentes que solicitan el mismo inventario y verifica la disponibilidad individual de cada proyecto.

La implementación se integró en el PR [#104](https://github.com/goodmorning-mx/arcoenergy/pull/104), merge commit `6d43b93c5f9c76453d3101db0a96838363ed36d4`. Factory integró la revisión esperada `202611090077` por el PR [#421](https://github.com/goodmorning-mx/goodmorning-factory/pull/421); el run [#42547694163](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42547694163) terminó correctamente con despliegue, verificación de esquema y reconciliación de respaldos. La API DEV informa ese commit y esquema y está `ready`; `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. Los bundles publicados de CRM y PWA contienen los estados “Faltan” y “Cubierto” por orden. Validación local: 192 pruebas backend y builds de producción CRM/PWA aprobados. Los jobs del PR de producto no iniciaron pasos por el límite de facturación de GitHub.

## Iteración 66 — clasificación de gastos fijos y variables (2026-11-09)

A partir de la indicación literal del contador —«Control de gastos fijos y variables» y separar en el resultado del periodo «gastos de operación fijos y variables»—, los gastos nuevos de CRM requieren elegir tipo fijo o variable. Los gastos capturados desde la operación de campo se registran como variables. Las correcciones compensatorias conservan el tipo original. Los reportes por proyecto y periodo presentan ambos importes por separado; los registros anteriores quedan como “sin clasificar”, sin adivinar su naturaleza.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-17 | Parcial funcional | Captura CRM/PWA y bitácora identifican gasto fijo o variable; queda por validar con contabilidad la clasificación de casos mixtos y conceptos recurrentes. |
| US-38 | Parcial funcional | Reporte preliminar mensual y por proyecto separa los gastos fijos, variables y sin clasificar; estados financieros, devoluciones/bonificaciones y validación final del contador siguen pendientes. |

La migración `202611090078` añade `expense_type` con valor `unclassified` para filas existentes y agrega nuevas versiones append-only para US-17/US-38. Las fuentes originales se preservan.

La implementación se integró en el PR [#106](https://github.com/goodmorning-mx/arcoenergy/pull/106), merge commit `14c86bca86234c74cbcadef6daa52abb1d9c143e`. Factory integró el esquema esperado `202611090078` en el PR [#422](https://github.com/goodmorning-mx/goodmorning-factory/pull/422); el run [#42853228903](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42853228903) completó despliegue, verificación del esquema vivo y reconciliación de respaldos. La API DEV informa ese commit, esquema `202611090078` y estado `ready`; `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. Los bundles publicados muestran en CRM el desglose fijo/variable y en PWA que los gastos de campo son variables. Validación local: 193 pruebas backend y builds de producción CRM/PWA aprobados. Los jobs de CI del PR de producto fallaron antes de ejecutar pasos; el registro los diferencia de los resultados locales.

## Iteración 67 — devoluciones y bonificaciones en el resultado preliminar (2026-11-10)

El contador indicó la fórmula «VENTAS − costo de venta − gastos de operación fijos y variables + devoluciones y bonificaciones = resultado». Se agregó una bitácora separada para devoluciones y bonificaciones con proyecto opcional, fecha, importe, descripción y usuario responsable. Solo contador y administrador pueden registrar o corregir. Las correcciones agregan una reversa vinculada y no borran el registro original. El CRM presenta el total y su desglose por proyecto/mes. Cada ajuste se suma al resultado preliminar conforme al signo escrito por el contador, pero por sí solo no genera movimientos de caja, altera ventas ni cambia inventario.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-38 | Parcial funcional | El informe incluye y desglosa devoluciones/bonificaciones más gastos fijos/variables. Falta validación de fórmulas y tratamiento formal por contabilidad; no constituye estado financiero oficial. |
La migración `202611100079` agrega la tabla de ajustes y una versión append-only de US-38. La fuente literal de las user story cards se conserva. La implementación se integró por el PR [#108](https://github.com/goodmorning-mx/arcoenergy/pull/108), merge commit `5eba0ae2697d6db69be59a10eac3bd9500ebcb30`. El manifiesto de Factory quedó actualizado mediante el PR [#423](https://github.com/goodmorning-mx/goodmorning-factory/pull/423), merge commit `960fd586d7ef5fb9ffafff071f7cc24eb5b7cc98`. Factory terminó el despliegue DEV en el run [#42855547482](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42855547482): aplicó recursos, verificó la revisión de esquema y reconcilió respaldos externos. La API reporta el commit `5eba0ae2697d6db69be59a10eac3bd9500ebcb30`, esquema `202611100079` y estado `ready`; `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200 con shells y bundles de su portal; el CRM publicado muestra las etiquetas nuevas de ajustes. Validación local: 194 pruebas backend y build de producción CRM aprobados. Los jobs del CI del producto no comenzaron por el límite de facturación de GitHub; CodeQL y la validación de contrato de Factory sí pasaron. No hubo navegador in-app conectado para comprobar el render interactivo.

## Iteración 68 — entidad de proyecto con folio único (2026-11-10)

El contador solicitó que cada proyecto tenga un código para ligar gastos y salidas de material. Se incorpora una entidad de proyecto separada de la orden de trabajo, código único `AE-P-{año}-{sufijo}`, relación con el cliente, notas y una vista propia en CRM. Una orden puede apuntar a un proyecto existente o crear uno automáticamente; las ventas aceptadas también crean su proyecto. Gastos directos pueden ligarse al proyecto sin una orden específica, y el reporte preliminar agrega ventas, materiales, gastos y ajustes por proyecto, incluidas varias órdenes.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-32 | Parcial funcional | Proyecto con código, CRM, relación de órdenes y gastos, y costeo agrupado. Se migran las órdenes existentes conservando movimientos; falta que administración confirme el formato del código y si operativamente puede haber varias órdenes por proyecto. |

La migración `202611100080` agrega la entidad y relaciones, migra cada orden histórica a un proyecto independiente y agrega una nueva versión append-only de US-32. No modifica importes ni elimina historia. La implementación quedó en el PR [#110](https://github.com/goodmorning-mx/arcoenergy/pull/110), merge commit `99679921f3c1598c572b0e43da755464632b8ef2`. El manifiesto DEV de Factory quedó en el PR [#424](https://github.com/goodmorning-mx/goodmorning-factory/pull/424), merge commit `49875fd9b81e6219318f13f1eca13a7a981e17b1`; el run [#42859479932](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42859479932) terminó correctamente, verificó el esquema vivo y completó respaldos externos. DEV reporta API `ready`, esquema `202611100080` y commit `99679921f3c1598c572b0e43da755464632b8ef2`. `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200 con los bundles distintos esperados; el bundle servido del CRM contiene Proyectos y los bundles CRM/PWA no incluyen cadenas de modo demo/trial. La suite backend pasó 196 pruebas; los builds de CRM, PWA y web SEO terminaron correctamente. La inspección visual interactiva no pudo ejecutarse: no había navegador conectado. No se cargaron cuentas del equipo ni catálogos/precios aprobados nuevos; esos datos reales corresponden a ArcoEnergy. US-32 sigue parcial hasta que administración confirme el formato comercial del código y la cardinalidad proyecto/órdenes.

## Iteración 69 — subcategorías y alta rápida desde compras (2026-11-10)

La tarjeta US-20 registra los datos descriptivos del artículo y solicita poder darlo de alta desde el flujo de compra cuando aún no existe en el catálogo. El CRM ahora captura subcategoría y permite al contador crear ese artículo faltante en contexto; se inicia con cero existencia y la compra registra después el costo y la entrada mediante el flujo normal. No se crea un movimiento de inventario al dar de alta la ficha.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-20 | Parcial funcional | Categoría/subcategoría, marca, modelo, proveedor, unidad y código escaneable disponibles; alta rápida sin stock inicial dentro de compras. Falta validar la taxonomía con almacén y probar etiquetas con dispositivos físicos. |

La migración `202611100081` añade la subcategoría y agrega una versión append-only a US-20 sin modificar la fuente original. Producto integrado en el PR [#112](https://github.com/goodmorning-mx/arcoenergy/pull/112), merge commit `fc00dbc7aa25e1fde46eec1d879c91373d385bb0`. El manifiesto DEV de Factory quedó actualizado en el PR [#425](https://github.com/goodmorning-mx/goodmorning-factory/pull/425), merge commit `d5874955ee60ecdf6c5b95a93a01b6f448fca4db`; el run [#42861247672](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42861247672) terminó correctamente, verificó el esquema `202611100081` y reconcilió respaldos externos. `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` responden HTTP 200. Los recursos publicados de CRM incluyen alta rápida y subcategoría; CRM y PWA no presentan etiquetas de modo trial/demo. La API reporta el commit y esquema esperados. Validación local: 197 pruebas backend y builds de producción CRM/PWA aprobados. No se pudo ejecutar inspección interactiva en navegador conectado. La última revisión de cuentas encontró una cuenta con rol administrador; no se han confirmado cuentas reales de contador, marketing, instalador y cliente.

## Iteración 70 — gráficas y oportunidades en el dashboard (2026-11-10)

La revisión visual del dashboard en el PDF del contador mostró una gráfica de entradas/salidas de almacén junto con alertas y cifras principales. El CRM ya mostraba alertas de stock bajo, cobranza próxima/vencida y cuentas, pero no esa gráfica ni una distribución visual del inventario. Se agregaron en CRM dos widgets basados en datos reales: conteo diario de movimientos físicos de entrada/salida durante siete días, y distribución de artículos disponibles, bajo mínimo y sin existencia. El mismo bloque enlaza cobranza vencida y cotizaciones que esperan aprobación de precio. Los contadores de instalaciones, inventario, cotizaciones y cartera ahora se exponen solo si el usuario tiene el permiso correspondiente.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-37 | Parcial funcional | La matriz de los apartados del Word/PDF se actualizó contra DEV y el dashboard incluye la gráfica y resumen que aparecen en la referencia visual. Sigue faltando comparar con el sistema activo de César; quedan validaciones de métricas y umbrales con contador/administración. |
| US-39 | Parcial funcional | CRM incorpora indicadores visuales de almacén y accesos a acciones prioritarias, conservando dashboard web independiente. Falta definir indicadores adicionales con el negocio. |

La migración `202611100082` agrega una revisión append-only a US-37 y conserva el relato original. Producto integrado en el PR [#114](https://github.com/goodmorning-mx/arcoenergy/pull/114), merge commit `4de38c56278b194373f9775ef866c20e8073e887`. Factory integró el esquema `202611100082` mediante el PR [#426](https://github.com/goodmorning-mx/goodmorning-factory/pull/426), merge commit `8966a02ce55148612de7445441d7d53469559c16`; el run [#42864044382](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42864044382) terminó correctamente, verificó la revisión viva y reconcilió respaldos externos. DEV reporta API `ready`, commit `4de38c56278b194373f9775ef866c20e8073e887` y esquema `202611100082`; `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` responden HTTP 200. Los bundles servidos de CRM y PWA son distintos y no contienen etiquetas trial/demo; el bundle de CRM incluye los widgets de la iteración. Validación local: 198 pruebas backend y build de producción CRM aprobados. La sesión no tenía navegador interactivo conectado para validar render en pantalla. Las cuentas reales del equipo y decisiones sobre métricas siguen pendientes de ArcoEnergy.

## Iteración 71 — aislamiento del costo de inventario (2026-11-10)

La revisión por rol encontró que `/inventory/consume` serializaba el costo unitario de sus movimientos en la respuesta al instalador. La ficha de artículo ya ocultaba ese dato, y kardex/devoluciones aplicaban el permiso, pero el registro de consumo y su reintento offline no. Ambos resultados ahora pasan por un serializador común: solo `inventory:costs:read` o `inventory:manage` permite recibir `unit_cost`. Para no degradar la operación de campo, cantidad, artículo, orden y tipo de movimiento siguen disponibles. Las pruebas cubren consumo nuevo, repetición idempotente, devolución y conservación de visibilidad para cuentas con permiso contable.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Los endpoints de consumo nuevo y reintento offline ya no exponen costo unitario a instaladores; sigue pendiente validar la matriz completa con cuentas reales de cada rol. |

La migración `202611100083` agrega esta evidencia a US-14 como una versión nueva y conserva intacta su fuente literal. Producto integrado mediante PR [#116](https://github.com/goodmorning-mx/arcoenergy/pull/116), merge commit `9bdafd83158aed39fce83123a23d114c858fd6fd`. Factory actualizó el contrato de esquema mediante PR [#427](https://github.com/goodmorning-mx/goodmorning-factory/pull/427), merge commit `3d4427574e3ffbd077da795ca8072c1788f551e3`; el run [#42866399583](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42866399583) terminó correctamente. DEV reporta API `ready`, commit `9bdafd83158aed39fce83123a23d114c858fd6fd` y esquema `202611100083`; `/api/health/ready`, `/api/version`, `/`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. Validación local: 200 pruebas backend y builds de producción CRM/PWA aprobados. No se añadieron secretos ni configuración nueva.

## Iteración 72 — privacidad de costos en órdenes de trabajo (2026-11-10)

La revisión posterior de US-14 encontró que la lista PWA de órdenes serializaba `unit_cost` por cada material. Se agrega el mismo control por permiso a materiales solicitados: instaladores conservan cantidades y disponibilidad requeridas para su trabajo; solo contador/administración con permiso explícito reciben costos. Una regresión compara el payload para instalador y contador.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | El listado de órdenes oculta el costo unitario a instaladores y conserva información operativa. Sigue pendiente revisar el resto de campos y probar usuarios reales de los cinco roles. |

La migración `202611100084` agrega esta nueva versión a US-14 sin modificar la fuente literal. Producto integrado mediante PR [#118](https://github.com/goodmorning-mx/arcoenergy/pull/118), merge commit `ef24521a45e09b7641c3859cd0a233e420aaed7e`. Factory actualizó el contrato de esquema mediante PR [#428](https://github.com/goodmorning-mx/goodmorning-factory/pull/428), merge commit `a60720d8de939c38d3e38dbd4e3d73db896a41ef`; el run [#42867339105](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42867339105) terminó correctamente tras desplegar, verificar `202611100084` y reconciliar respaldos externos. DEV reporta API `ready`, commit `ef24521a45e09b7641c3859cd0a233e420aaed7e` y esquema `202611100084`; `/api/health/ready`, `/api/version`, `/`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. Validación local: 202 pruebas backend aprobadas. No se añadieron secretos ni variables de configuración.

## Iteración 73 — fechas locales de seguimiento (2026-11-10)

El CRM ofrecía las opciones de 3, 7, 15 y 30 días, pero calculaba la fecha con milisegundos UTC. Cerca de la medianoche local eso podía desplazar el contacto un día, y la fecha mínima del control también usaba UTC. El cálculo ahora avanza días de calendario en la zona horaria del navegador, incluyendo el inicio/fin de mes y cambios de horario estacional. Se conservan la fecha abierta, el comentario de bitácora y la asignación de responsable.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-4 | Parcial funcional | Presets y fecha mínima usan la fecha local; faltan validar el flujo con vendedores y cuentas/dispositivos reales. |

La migración `202611100085` registra una versión append-only de US-4 sin modificar su fuente literal. Las pruebas cubren una programación cerca de medianoche en Cancún y un cálculo que atraviesa el cambio de horario estacional en Nueva York. Producto integrado mediante PR [#120](https://github.com/goodmorning-mx/arcoenergy/pull/120), merge commit `54467db82af5099e84a2439a00198e417bb4ca4a`. Factory fijó el esquema esperado mediante PR [#429](https://github.com/goodmorning-mx/goodmorning-factory/pull/429), merge commit `a1b62da3185d381fb8b2bf44b804d16f99a101dd`; el run [#42869556391](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42869556391) finalizó correctamente, desplegó los recursos, verificó revisiones del esquema vivo y reconcilió respaldos externos. DEV reporta API `ready`, commit `54467db82af5099e84a2439a00198e417bb4ca4a` y esquema `202611100085`; `/health`, `/health/ready`, `/version`, `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. Validación local previa: 203 pruebas backend, 2 pruebas de fecha CRM y build de producción CRM aprobados. No se pudo inspeccionar el navegador interactivo porque no había una sesión de navegador conectada. Las cuentas y dispositivos reales del equipo siguen pendientes para validar las historias con sus usuarios.

## Iteración 74 — privacidad de documentos de instalación (2026-11-10)

La revisión de US-14 detectó que la lista de órdenes serializaba el ID privado del archivo de Drive de la solicitud de materiales. La PWA no necesita ese ID para trabajar, y el CRM obtiene los bytes por una ruta autenticada y autorizada. La respuesta ahora omite el ID y entrega `material_request_available`; el CRM usa esa señal para mostrar la acción de descarga, preservando el acceso al documento sin publicar su identificador interno.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | El API oculta el ID privado de Drive en los resultados de órdenes y mantiene una señal de disponibilidad para el CRM. Siguen pendientes la auditoría integral de todos los campos y las pruebas con cuentas reales de los cinco roles. |

La migración `202611100086` agrega una versión append-only de US-14 y conserva intacto el relato original. Producto integrado mediante PR [#122](https://github.com/goodmorning-mx/arcoenergy/pull/122), merge commit `ab245fec4d0f6c649e7c6e6e59e3125dae45cc40`. Factory actualizó el esquema esperado mediante PR [#430](https://github.com/goodmorning-mx/goodmorning-factory/pull/430), merge commit `258d920467797779caca234353a8acdd79d0439b`; el run [#42871394498](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42871394498) completó en su reintento el despliegue, la verificación del esquema vivo y la reconciliación de respaldos externos. DEV reporta API `ready`, commit `ab245fec4d0f6c649e7c6e6e59e3125dae45cc40` y esquema `202611100086`; los cinco recursos Coolify corren saludables con esa imagen. `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. El bundle CRM servido contiene `material_request_available` y no contiene `material_request_drive_file_id`. Validación local: 9 pruebas dirigidas, suite backend completa (204 pruebas), build de producción CRM; Factory: 34 pruebas de contrato, CodeQL y validación de provisioning aprobados. Los jobs CI de producto no pudieron ejecutarse porque GitHub los bloqueó por facturación de la cuenta; las verificaciones locales sí pasaron. No se cambiaron secretos ni configuración.

## Iteración 75 — privacidad de IDs de cotización y factura (2026-11-10)

La revisión de US-14 encontró que las respuestas CRM de cotizaciones y compras incluían los IDs internos de los PDFs y facturas archivados en Drive. Ninguna interfaz los necesita: los archivos se descargan por rutas autenticadas. Los serializadores ahora entregan `drive_available` e `invoice_available` y omiten ambos IDs; el botón de factura en Compras usa el indicador booleano.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Se ocultan IDs privados de Drive en respuestas de cotización y compra, conservando sus acciones autorizadas de descarga. Continúa pendiente auditar todos los campos y validar con cuentas reales de los cinco roles. |

La migración `202611100087` agrega una versión append-only de US-14 y conserva el relato literal. Producto integrado mediante PR [#124](https://github.com/goodmorning-mx/arcoenergy/pull/124), merge commit `db66567e72df142ac4145922654bda0b0e233a78`. Factory actualizó la revisión esperada mediante PR [#432](https://github.com/goodmorning-mx/goodmorning-factory/pull/432), merge commit `0df9182b5ca3f044e2d85105e0413c3de468ce6c`; el run [#42873459988](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42873459988) completó despliegue, verificación de revisión viva y reconciliación de respaldos externos. DEV reporta API `ready`, commit `db66567e72df142ac4145922654bda0b0e233a78` y esquema `202611100087`; los cinco recursos Coolify están saludables con esa imagen. `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. El bundle CRM activo contiene `invoice_available` y no contiene `invoice_drive_file_id` ni `drive_file_id`. Validación local: 18 pruebas dirigidas, suite backend completa (206 pruebas) y build CRM aprobados; Factory: 34 pruebas de contrato, CodeQL y validación de provisioning aprobados. GitHub no inició los jobs CI de producto por el bloqueo de facturación de la cuenta. No hubo cambios de secretos ni configuración.

## Iteración 76 — privacidad de archivos anidados en ventas (2026-11-10)

La revisión del resultado de ventas encontró que la orden anidada se serializaba directamente y podía incluir `material_request_drive_file_id`, aunque el listado de órdenes ya ocultaba ese identificador. El resultado de ventas ahora reutiliza el serializador protegido de órdenes y expone únicamente `material_request_available`. La descarga continúa en su endpoint autenticado. Una prueba regresiva invoca el resultado completo de ventas con un ID señuelo y confirma que no aparece en la respuesta serializada.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | También se protegen los IDs privados de Drive en órdenes anidadas dentro de ventas. Siguen pendientes la auditoría completa de cada campo y la validación de permisos con cuentas reales de los cinco roles. |

La migración `202611100088` añade la revisión append-only de US-14 y conserva la fuente literal. Producto integrado en el PR [#126](https://github.com/goodmorning-mx/arcoenergy/pull/126), merge commit `b7094e5829217b34733b0903b6e74f082952bf3d`. Factory actualizó la revisión esperada en el PR [#433](https://github.com/goodmorning-mx/goodmorning-factory/pull/433), merge commit `c6e47ad1d2e2c7f7c6f9b6fb8d860d53a38efcda`; el run [#42875164049](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42875164049) terminó correctamente al reconciliar el catálogo DEV. La API informa `ready`, el commit `b7094e5829217b34733b0903b6e74f082952bf3d` y el esquema `202611100088`; los cinco contenedores de aplicación observados en Coolify están saludables con esa imagen. `/`, `/crm/login`, `/app/login`, `/crm/` y `/app/` responden HTTP 200. Validación local: 3 pruebas dirigidas, suite backend completa (207 pruebas) y 34 pruebas de contrato de Factory aprobadas. Los jobs CI del PR de producto no iniciaron pasos por el bloqueo de facturación de GitHub; se registran por separado de las validaciones locales. No se cambiaron secretos ni configuración externa.

## Iteración 77 — privacidad en la respuesta del checklist (2026-11-10)

La continuación de la auditoría encontró que el endpoint para actualizar el checklist regresaba la orden con serialización genérica. Ahora usa la proyección protegida y mantiene la señal de disponibilidad de la solicitud de materiales sin revelar el ID privado de Drive. Una prueba regresiva ejecuta la actualización y comprueba la respuesta completa.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | La actualización del checklist ya oculta IDs privados de Drive. Sigue pendiente la revisión integral de campos y la comprobación con cuentas reales de los cinco roles. |

La migración `202611100089` agrega una versión append-only de US-14 y conserva intacta su fuente literal. Producto integrado mediante el PR [#128](https://github.com/goodmorning-mx/arcoenergy/pull/128), merge commit `02f15124f07321ae9bec0865cf34a8255b8e6180`. Factory actualizó la revisión esperada mediante el PR [#434](https://github.com/goodmorning-mx/goodmorning-factory/pull/434), merge commit `792799450948406cded7c9e00ea6db464294dc37`; el run [#42876507125](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42876507125) completó despliegue, verificación del esquema vivo y reconciliación de respaldos externos. La API DEV reporta `ready`, commit `02f15124f07321ae9bec0865cf34a8255b8e6180` y esquema `202611100089`; `/`, `/crm/login`, `/app/login`, `/crm/` y `/app/` responden HTTP 200. Validación local: 4 pruebas dirigidas, suite backend completa (208 pruebas) y 34 pruebas de contrato de Factory aprobadas. Los jobs CI del PR de producto no iniciaron pasos por el bloqueo de facturación de GitHub; no se registran como pruebas aprobadas. No se cambiaron secretos ni configuración externa.

## Iteración 78 — documentos de materiales limitados por asignación (2026-11-10)

El endpoint de documentos de solicitud de materiales aceptaba cualquier orden para usuarios con permiso de inventario, sin comprobar asignación. Un instalador podía leer o reemplazar un documento ajeno si conocía el identificador de la orden. Ahora carga y descarga verifican que la orden esté asignada a la cuenta del instalador. Administración y contabilidad conservan el acceso operativo que da su permiso de inventario.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | La carga y descarga de solicitudes de materiales para instaladores requiere asignación a la orden. Sigue pendiente auditar todos los demás campos/acciones y validar la matriz con cuentas reales de los cinco roles. |

La migración `202611100090` registra una nueva versión append-only de US-14 y conserva el relato literal. Producto integrado por el PR [#130](https://github.com/goodmorning-mx/arcoenergy/pull/130), merge commit `f382d707a96c296efd93c4fe69bfaafa8bdb2fcf`. Factory fijó el esquema esperado por el PR [#435](https://github.com/goodmorning-mx/goodmorning-factory/pull/435), merge commit `14d311a9e076033422205dfecdd60821993c06dc`; los runs [#42930067100](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42930067100) y [#42930067328](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42930067328) finalizaron correctamente con despliegue, revisión de esquema y reconciliación de respaldos/catálogo DEV. La API informa `ready`, commit `f382d707a96c296efd93c4fe69bfaafa8bdb2fcf` y esquema `202611100090`; los cinco recursos Coolify están saludables con esa imagen. `/`, `/crm/login`, `/app/login`, `/crm/` y `/app/` responden HTTP 200. Validación local: 10 pruebas dirigidas, suite backend completa (210 pruebas) y 34 pruebas de contrato de Factory aprobadas. Los jobs CI del PR de producto fallaron antes de iniciar pasos por el bloqueo de facturación de GitHub, así que no se presentan como aprobados. No se cambiaron secretos ni configuración externa.

## Iteración 79 — auditoría viva de rutas y acceso anónimo (2026-11-10)

Se comprobó la versión realmente servida en DEV. `/` presenta el sitio público; `/login` y `/crm/login` sirven el acceso CRM; `/app/login` sirve el acceso PWA; `/crm/` y `/app/` sirven aplicaciones distintas. Los bundles publicados inspeccionados no contienen etiquetas de trial/demo. Las rutas privadas de API para clientes, cotizaciones, instalaciones y portal cliente respondieron `401 Authentication required` sin sesión. La inspección estática encontró solo dos endpoints de producto sin identidad: recepción pública de prospectos y chat público, ambos intencionales. Esta auditoría confirma la separación de acceso, pero no prueba el render interactivo ni una sesión autenticada.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | API privada rechaza anónimos y rutas públicas quedan acotadas a prospectos/chat; faltan validar sesión, aislamiento y permisos con cuentas reales de los cinco roles. |
| US-39 | Parcial funcional | Sitio público, alias/login CRM y shell de CRM están publicados sin modo trial/demo; falta recorrer el flujo autenticado en navegador con el equipo. |
| US-40 | Parcial funcional | PWA y login móvil se publican en rutas propias, con API privada; falta validar login y operación con cuentas/dispositivos reales. |

La migración `202611100091` agrega una versión append-only para US-14, US-39 y US-40 sin alterar relatos fuente ni fabricar usuarios. Producto integrado en el PR [#132](https://github.com/goodmorning-mx/arcoenergy/pull/132), merge commit `a69d07ff2c41db36f72708cb822e08bd0fd9d096`. Factory actualizó el esquema esperado a `202611100091` en el PR [#436](https://github.com/goodmorning-mx/goodmorning-factory/pull/436), merge commit `62d9371d553d2219845ec4319c60659cd3fe024f`; el run [#42931948424](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42931948424) terminó correctamente con despliegue, verificación del esquema y reconciliación de respaldos. DEV reporta API `ready`, commit `a69d07ff2c41db36f72708cb822e08bd0fd9d096` y esquema `202611100091`. Smoke check posterior: `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` HTTP 200; cuatro colecciones API privadas HTTP 401 anónimas; los bundles servidos de CRM/PWA no contienen términos de trial/demo. La prueba de migración local pasó (1); 34 contratos de Factory pasaron. Los jobs CI de producto fallaron antes de ejecutar pasos, por lo que no se cuentan como aprobados. No se crearon cuentas ni se modificaron secretos.

## Iteración 80 — resultado preliminar filtrable por proyecto (2026-11-10)

El informe de CRM ya agrupaba costos por proyecto en la consulta mensual, pero no ofrecía una selección para aislar un proyecto ni mantenía sincronizada la lista de devoluciones/bonificaciones con ese filtro. Se agrega el selector proyecto + periodo. El API filtra el informe y sus ajustes por el mismo proyecto, agregando las órdenes de trabajo que pertenecen a él. La fórmula sigue mostrando ventas registradas menos costo del material consumido menos gastos capturados más devoluciones/bonificaciones. No se altera la base del costeo ni se presenta el resultado preliminar como estado contable formal.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-12 | Parcial funcional | El contador/administrador puede consultar costos materiales y gastos del proyecto; falta validar método de valuación y costo histórico con contabilidad. |
| US-38 | Parcial funcional | El resultado preliminar mensual se puede filtrar por proyecto y agrupa varias órdenes; falta aprobación de fechas, fórmula fiscal/contable y cierre formal. |

La migración `202611100092` añade versiones append-only a US-12 y US-38, conservando los relatos fuente. Producto integrado en el PR [#134](https://github.com/goodmorning-mx/arcoenergy/pull/134), merge commit `b9149b6c670e706d5a6771c1ff24c6a3e71fd940`. Factory fijó la revisión esperada en el PR [#438](https://github.com/goodmorning-mx/goodmorning-factory/pull/438), merge commit `f35a1d5d1eb89872943f69aa2d1de907f78e57f0`; el run [#42933620227](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42933620227) completó la reconciliación DEV. La API informa `ok`, el commit `b9149b6c670e706d5a6771c1ff24c6a3e71fd940` y esquema `202611100092`. `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` responden HTTP 200; clientes, cotizaciones, instalaciones y portal responden 401 sin sesión. Los bundles servidos de CRM/PWA no contienen marcas trial/demo. Validación enfocada: 4 pruebas backend aprobadas y 34 pruebas de contrato de Factory aprobadas. Los jobs de CI del PR de producto fallaron antes de ejecutar pasos; no se cuentan como validaciones. La auditoría confirma que no se presenta un modo trial/demo, pero no sustituye la validación interactiva con cuentas reales, que no fueron creadas.

## Iteración 81 — calendario de cobranza y caja (2026-11-11)

La agenda de cobranza comparaba fechas con UTC aunque las fechas de seguimiento ya respetaban el calendario de la aplicación. Cerca de la medianoche del contenedor, una cuota podía aparecer en estado distinto entre el CRM, el dashboard y el mensaje de WhatsApp. Se unificó el cálculo en `America/Cancun`, que ya utilizaba el CRM y el sistema de recordatorios, y se calcula la siguiente semana sumando días calendario a una fecha ISO. Gastos, movimientos de caja y compras toman la fecha de negocio; los vencimientos de proveedores y cuotas de clientes suman días calendario sin convertir primero la fecha a UTC. Los vencimientos a crédito de proveedores se derivan de la fecha de compra y los días de crédito configurados, y se recalculan al cambiar esa fecha salvo que el usuario ajuste manualmente el vencimiento.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-11 | Parcial funcional | La agenda y el mensaje de WhatsApp ahora comparten la fecha de negocio al clasificar cuotas próximas, de hoy o vencidas. Faltan validar planes, intereses y la zona horaria oficial con ArcoEnergy. |
| US-16 | Parcial funcional | El formulario de cobranza usa la fecha de negocio para capturar pagos; las reglas de distribución multi-cuota y mora siguen pendientes. |
| US-17 | Parcial funcional | El formulario de gastos usa la fecha de negocio. Falta validación contable de categorías y conceptos recurrentes. |
| US-18 | Funcional básico | Los movimientos manuales de caja/banco usan la fecha de negocio; conciliación bancaria sigue pendiente. |
| US-31 | Parcial funcional | El vencimiento sugerido de compra a crédito suma los días del proveedor a la fecha de compra, con edición manual. Sigue pendiente conciliación. |
| US-34 | Parcial funcional | Los movimientos y avisos basados en fecha usan un calendario común configurable; faltan otros ciclos de corrección y conciliación. |

La migración `202611110093` agrega revisiones append-only a las tarjetas anteriores y conserva los relatos originales. El calendario local se verificó además en una instalación limpia y queda desplegado en DEV al integrar esta iteración. La zona oficial del negocio sigue pendiente de confirmación.

## Iteración 82 — compatibilidad de instalación limpia para Web Push (2026-11-11)

La primera ejecución de CI con los repositorios públicos encontró dos defectos reproducibles. En la base limpia, la migración de push esperaba `installer_email`, mientras que la migración inicial crea `user_email` desde la metadata ORM vigente, lo que impedía iniciar el backend. Además, una prueba del dashboard usaba el día UTC del runner en lugar del calendario de negocio de la aplicación. La migración ahora indexa la columna realmente presente (legada o vigente) y la prueba usa `business_today()`.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-7 | Parcial funcional | Las suscripciones push pueden migrar desde cero con ambos esquemas históricos; falta validar notificaciones en dispositivos reales. |
| US-40 | Parcial funcional | Instalación limpia completa inicia y pasa health checks; falta validar login y push con cuentas y equipos reales. |

La migración `202611110094` registra las correcciones en versiones append-only sin cambiar los relatos fuente. Validación local: 219 pruebas backend aprobadas; `docker compose --profile hybrid up --build --wait` arranca todos los servicios con el esquema `202611110094`; health, sitio, logins CRM/PWA y shells CRM/PWA responden HTTP 200. El cambio se integró en el PR [#136](https://github.com/goodmorning-mx/arcoenergy/pull/136), commit `ccb910eca7c4af91bf10d17ecc51223fec40c8ff`; la CI de producto pasó en el run [#42937022912](https://github.com/goodmorning-mx/arcoenergy/actions/runs/42937022912). Factory fijó la revisión esperada en el PR [#441](https://github.com/goodmorning-mx/goodmorning-factory/pull/441), commit `cd8c37b802ef8e0f32738662bf17d13754d6d48b`. La reconciliación [#42937273809](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42937273809) verificó el esquema vivo y un respaldo externo; DEV reporta el commit y la revisión esperados. La validación CI inicial tuvo 217 pruebas aprobadas y una prueba de fecha fallida, además de exponer el fallo de migración; los arreglos pasan ahora 219/219.

## Iteración 83 — contrato de autenticación para todas las rutas privadas (2026-11-11)

La auditoría de la tarjeta US-14 ya verificaba algunas colecciones anónimas en producción. Para que esa protección no dependa de una lista manual incompleta, se añade una prueba del router completo: cada endpoint de producto debe declarar autenticación HTTP Bearer; las únicas excepciones son recepción pública de prospectos y conversación pública del agente. La prueba no inventa usuarios y mantiene como pendiente la matriz de datos por campo con personas reales.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | La suite falla si se agrega una ruta de producto sin Bearer fuera de los dos endpoints públicos; la auditoría funcional de permisos por entidad/campo y usuarios reales sigue pendiente. |

La revisión se registra en una nueva versión append-only de US-14; conserva relato y fuente originales.

La migración `202611110095` se integró mediante el PR [#137](https://github.com/goodmorning-mx/arcoenergy/pull/137), commit `1a91baac55cd6158d34debca4b9a1eaaea926ba2`; su CI pasó en [#42938073821](https://github.com/goodmorning-mx/arcoenergy/actions/runs/42938073821). Factory actualizó el contrato de DEV en el PR [#442](https://github.com/goodmorning-mx/goodmorning-factory/pull/442), commit `2122af4c1d3e2558e1e28146dd3615e74046835c`; la reconciliación [#42938540397](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42938540397) confirmó la revisión viva `202611110095` y un respaldo externo verificado. La API DEV reporta el commit integrado y esquema `202611110095`; `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` responden HTTP 200; clientes, cotizaciones, instalaciones, portal de cliente y equipo devuelven HTTP 401 sin sesión. La validación local completó 221 pruebas backend y una instalación híbrida limpia con todos los servicios saludables.

## Iteración 84 — auditoría anónima de las rutas de lectura (2026-11-11)

La prueba anterior aseguraba que cada ruta incluyera seguridad Bearer en el router, pero no llamaba al handler completo. Se añade una comprobación de integración local que recorre todas las rutas GET privadas del API y comprueba que un cliente sin sesión reciba 401/403. En DEV se recorrieron las 34 rutas GET privadas publicadas por OpenAPI: todas respondieron 401 y ninguna devolvió información.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | La protección anónima se verifica para las 34 rutas GET en DEV y se mantiene cubierta por una prueba automatizada local. Queda pendiente probar el acceso por rol, entidad y campo con usuarios reales de los cinco roles. |

La migración `202611110096` añade una revisión append-only a US-14 y conserva la fuente original.

## Iteración 85 — verificación de la matriz de permisos de roles (2026-11-11)

Se amplía US-14 para comprobar el comportamiento de membresía vigente de los cinco roles. Para cada permiso del catálogo, la prueba confirma que el rol autorizado puede continuar y que cualquier permiso ausente se rechaza con 403. Otra regla recorre todas las rutas privadas del API y exige que además de Bearer dependan de `require_permissions` o `require_any_permission`; solo recepción de prospectos y chat público del agente quedan fuera.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Las cinco matrices de permisos y la conexión de cada endpoint privado con un guard están automatizadas. Falta que responsables del negocio revisen el alcance funcional con cuentas reales, especialmente los datos visibles y asignaciones por proyecto. |

La migración `202611110097` registra esta revisión append-only en US-14 sin alterar el relato fuente.

## Iteración 86 — auditoría desplegada de rutas privadas (2026-11-11)

Con los repositorios habilitados para CI público, la comprobación se repitió contra DEV ya desplegado: las 35 rutas GET privadas publicadas por OpenAPI respondieron HTTP 401 sin sesión. La API reporta `ready`, commit `dcf384f0ad8dc09f7b2007da14685c2be6672663` y esquema `202611110097`; los manifiestos de versión de PWA y CRM reportan el mismo commit. `/`, `/app/login/`, `/crm/login/` y `/crm/` respondieron HTTP 200, y Chrome renderizó los formularios de `/app/login`, `/crm/login` y `/login`.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Las 35 rutas privadas de lectura se verificaron anónimamente en el despliegue. Quedan pendientes las pruebas de acceso por entidad/campo y la validación con cuentas reales de los cinco roles. |

La migración `202611110098` añade esta revisión append-only y conserva el relato original. El producto se integró mediante el PR [#141](https://github.com/goodmorning-mx/arcoenergy/pull/141); Factory actualizó el esquema esperado en el PR [#444](https://github.com/goodmorning-mx/goodmorning-factory/pull/444). La reconciliación [#42942363132](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42942363132) completó despliegue, revisión del esquema vivo y respaldo externo verificado. La CI del producto pasó en [#42941951969](https://github.com/goodmorning-mx/arcoenergy/actions/runs/42941951969); la comprobación Factory pasó en [#42942232535](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/42942232535). El smoke test actual también confirmó en Chrome los tres formularios de login. No se crearon cuentas ni se cambiaron secretos.

## Iteración 87 — accesos reales sin modo de prueba (2026-11-11)

Se volvió a recorrer DEV luego de integrar la matriz técnica: sitio, CRM y PWA sirven sus bundles publicados; `/login`, `/crm/login` y `/app/login` muestran formularios reales en Chrome. Los bundles activos de CRM/PWA no contienen texto de modo trial, demo o prueba gratuita. La API está lista en commit `2d833a00a81941d408d3c6f5d05066ca2ce6eff5`, esquema `202611110098`; las 35 rutas GET privadas devuelven `401` sin sesión.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-39 | Parcial funcional | Superficie pública/CRM activa sin modo de prueba; falta el recorrido autenticado con el administrador y personal real. |
| US-40 | Parcial funcional | PWA y login reales activos, sin marcadores demo, y API privada; faltan usuarios asignados, login y pruebas push con los teléfonos del equipo. |

La migración `202611110099` añade versiones append-only para ambas tarjetas y conserva sus relatos originales. No se crearon cuentas reales ni se cambiaron credenciales: la lista de personas/correos y el acceso inicial de administración deben configurarse por ArcoEnergy.

## Iteración 88 — auditoría de cuentas y configuración de Drive (2026-11-11)

La inspección de solo lectura al API y su base de datos DEV no mostró valores de cuenta ni credenciales: solo contó roles activos y verificó si las variables están configuradas. Hay una cuenta activa con rol administrador y ninguna activa con roles contador, marketing, instalador o cliente. En el contenedor API DEV, `GOOGLE_DRIVE_FOLDER_ID` y `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` están vacíos, por lo que los archivos no pueden archivarse en Drive desde este entorno.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-13 | Parcial funcional | Los flujos Drive existen en código, pero DEV no tiene carpeta ni credenciales autorizadas; falta definir permisos, retención y sincronización general. |
| US-14 | Parcial funcional | La matriz de permisos se probó técnicamente; aún no hay cuentas activas para cuatro roles con las cuales validar su alcance real. |
| US-39 | Parcial funcional | Hay una cuenta administradora activa y login real; faltan las cuentas autorizadas del personal y recorrer el sistema con ellas. |
| US-40 | Parcial funcional | La PWA funciona y exige autenticación, pero faltan cuentas de campo/cliente y pruebas en sus dispositivos. |

La migración `202611110100` agrega versiones append-only y preserva los relatos originales. No incluye nombres, correos, contraseñas ni secretos. Para completar estos flujos se necesita que ArcoEnergy autorice y configure la carpeta de Drive y entregue las identidades autorizadas para los cuatro roles restantes.

## Iteración 89 — disponibilidad comercial del cotizador agentico (2026-11-11)

La web pública renderiza el asistente integrado con `gm-agent`; el backend conecta herramientas de catálogo mediante `gm-mcp` y solo permite leer tamaños/precios aprobados. La llave del proveedor está presente en el runtime, pero esta auditoría no envió una consulta facturable. La consulta agregada a DEV encontró cero paquetes activos y cero aprobados, por lo que el sitio puede explicar el proceso y captar prospectos, pero no producir un precio solar.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-1 | Bloqueada por catálogo comercial | Hay cotizador manual en las interfaces; faltan datos y aprobación de los paquetes reales de 4 a 20 paneles. |
| US-41 | Parcial funcional | Chat público agentico y herramientas están conectados; falta cargar/aprobar catálogo y validar el recorrido de venta con consentimiento. |

La migración `202611110101` agrega revisiones append-only para US-1 y US-41, conserva las fuentes originales y no registra precios, mensajes, datos personales ni secretos.

## Iteración 90 — fidelidad de la fuente original de US-21 (2026-11-11)

Al contrastar las tarjetas con el Word original del contador se detectó que la primera versión de US-21 había guardado solo una parte del apartado “ENTRADAS (DE INVETARIO)”. La card inicial y su literal quedan intactos; esta iteración registra una nueva versión con el apartado completo, incluyendo lectura de factura/XML/fotografía, devolución de sobrantes y condición/medio de pago. El texto se compara automáticamente contra el DOCX fuente.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-21 | Fuente corregida en nueva versión | La versión 2 conserva el apartado completo como texto literal; deben acordarse las reglas de reconocimiento documental y la vinculación contable de devoluciones. |

La migración `202611110102` agrega la versión 2 de manera append-only. La prueba confirma que la fuente de la versión 1 no se altera y que el literal nuevo coincide con el apartado del Word.

## Iteración 91 — lectura asistida de factura PDF y fotografía (2026-11-11)

US-22 ya aceptaba PDF y fotografías como fuente adjunta, pero solo el XML CFDI producía datos para revisión. El CRM ahora puede leer el texto digital de un PDF o aplicar OCR en español/inglés a PDF escaneados e imágenes. La lectura usa archivos en memoria y devuelve texto temporal; no guarda una copia, no llena inventario y no registra compras. La persona debe validar la lectura y completar el formulario antes de confirmar.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-22 | Parcial funcional | CFDI estructurado, texto PDF y OCR de imagen/PDF escaneado disponibles como ayuda revisable; falta validar precisión con facturas reales y decidir qué campos pueden precargarse de forma segura. |

La migración `202611110103` añade una versión append-only de US-22 y conserva su relato literal. PDFium se utiliza bajo su distribución Apache-2.0/BSD-3-Clause y queda serializado en el proceso porque su motor no es seguro ante llamadas simultáneas; Tesseract procesa imágenes con límite de tiempo. La prueba cubre extracción PDF con capa de texto, OCR simulado con idioma `spa+eng`, validación del archivo, respuesta transitoria y conservación de la fuente de la tarjeta.

## Iteración 92 — candidatos estructurados de factura (2026-11-11)

La transcripción PDF/OCR ahora propone candidatos de RFC, folio/UUID, fecha y total, con la línea fuente para revisión. El usuario aplica cada campo de forma explícita al formulario; un RFC solo selecciona automáticamente un proveedor cuando hay una coincidencia activa única. El total extraído sirve como referencia visual y no cambia artículos, cantidades, costos ni cuentas. Se conserva la transcripción temporal y la lectura no registra compras ni movimientos.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-22 | Parcial funcional | Se pueden revisar y aplicar candidatos individuales de PDF/foto. Artículos, cantidades e importes siguen manuales; falta validar precisión con facturas reales y acordar reglas de impuestos, fletes y descuentos con contabilidad. |

La migración `202611110104` agrega una revisión append-only de US-22 y conserva el literal fuente. La cobertura automatizada comprueba RFC múltiples, folio, fecha, exclusión del subtotal como total y preservación de la tarjeta original.

La implementación quedó integrada en el PR [#148](https://github.com/goodmorning-mx/arcoenergy/pull/148), merge commit `c2f6f85a45ef306fd45088e37e1d01bbcdf490c5`; la CI pasó en [#43061326896](https://github.com/goodmorning-mx/arcoenergy/actions/runs/43061326896), incluidos backend, CRM, frontend, Next.js y Docker/Chrome con OCR real. Factory actualizó la revisión esperada mediante PR [#451](https://github.com/goodmorning-mx/goodmorning-factory/pull/451), merge commit `79a8014`; la reconciliación [#43062139545](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/43062139545) desplegó, verificó el esquema vivo `202611110104` y respaldos externos. La API DEV informa estado `ready`, commit `c2f6f85a45ef306fd45088e37e1d01bbcdf490c5` y revisión `202611110104`; sitio, accesos y shells CRM/PWA responden HTTP 200. El bundle CRM publicado contiene la revisión y aplicación de candidatos.

## Iteración 93 — compartir PDF de cotización con confirmación (2026-11-11)

En CRM, el selector de archivos nativo ahora se invoca desde una confirmación explícita después de descargar/preparar la cotización. Si el navegador no comparte archivos, el enlace de WhatsApp descarga el PDF y abre el mensaje en el mismo gesto de usuario, evitando depender de un popup iniciado después de la llamada de red. El estado informa si Drive archivó el PDF o no; el sistema no afirma que el mensaje fue enviado.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-3 | Parcial funcional | El flujo de compartir tiene una acción confirmada y un fallback WhatsApp/descarga que conserva la activación del navegador. Falta validar el uso con dispositivos reales y decidir si se requiere envío/confirmación automática por API. |

La migración `202611110105` añade una versión append-only de US-3 y conserva el relato fuente.
La implementación quedó integrada en el PR [#150](https://github.com/goodmorning-mx/arcoenergy/pull/150), merge commit `f413ea12dbdcf2d8b6e2594a7b03e1a9fb9f2b53`; la CI aprobó backend, CRM, frontend, Next.js y Docker/Chrome en [#43064448746](https://github.com/goodmorning-mx/arcoenergy/actions/runs/43064448746). Factory actualizó el esquema esperado mediante PR [#452](https://github.com/goodmorning-mx/goodmorning-factory/pull/452), merge commit `f2c73b4`; el run [#43064888923](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/43064888923) desplegó, verificó `202611110105` y confirmó el respaldo externo. DEV reporta API `ready`, commit `f413ea12dbdcf2d8b6e2594a7b03e1a9fb9f2b53` y revisión `202611110105`; `/`, logins y shells CRM/PWA responden HTTP 200. El bundle CRM servido contiene los controles del flujo de compartir.

## Iteración 94 — lectura asistida de solicitud de materiales (2026-11-11)

CRM permite adjuntar la foto o PDF de la orden de servicio al registrar una salida, pero no permitía leer el documento. Se agrega extracción transitoria de texto para formatos PDF/JPG/PNG/WebP desde el CRM. El texto aparece como referencia para la persona responsable; las cantidades se capturan y revisan manualmente antes de confirmar. Leer el archivo no lo guarda, no crea movimientos ni modifica el inventario; al confirmar la salida se conserva el flujo existente de archivado privado en Drive cuando esté configurado. La captura manual sigue disponible si la lectura falla o no reconoce la escritura.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-25 | Parcial funcional | La solicitud PDF/foto se puede leer y cotejar en CRM antes de capturar cantidades; el OCR es solo referencia, no registra salidas. Falta validar precisión con órdenes reales del almacén y la calidad de escritura manuscrita. |

La migración `202611110106` agrega la revisión 2 de US-25 sin modificar su relato original. La nueva API requiere `inventory:issue`, limita el archivo a 12 MiB, valida su formato y no conserva el documento ni cambia existencias. Producto integrado por PR [#152](https://github.com/goodmorning-mx/arcoenergy/pull/152), merge commit `6cc8d04d5473b86915ad147a8bbd17c7894ca849`; CI [#43068206634](https://github.com/goodmorning-mx/arcoenergy/actions/runs/43068206634) pasó backend, CRM, frontend, Next.js y Docker/Chrome. Factory actualizó el contrato de DEV en el PR [#453](https://github.com/goodmorning-mx/goodmorning-factory/pull/453), merge commit `9c187dc8fceab040d0ebc0fbafb15367b5d73905`; el run [#43068912788](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/43068912788) desplegó el producto, verificó la revisión viva y confirmó el respaldo externo. DEV reporta API `ready`, commit `6cc8d04d5473b86915ad147a8bbd17c7894ca849` y esquema `202611110106`; `/`, `/login`, `/crm/login`, `/app/login`, `/crm/` y `/app/` respondieron HTTP 200. OpenAPI declara `HTTPBearer` para la lectura; una petición anónima recibió `401`, y el bundle CRM servido incluye el control y la ruta de lectura. La suite backend pasó 247 pruebas; CRM pasó 4 pruebas, typecheck y build de producción. Una prueba en contenedor con Tesseract sobre la foto de orden manuscrita compartida extrajo texto parcial y reconoció solo 2 de 7 familias de materiales esperadas; no se imprimió ni persistió esa transcripción. Por ello, el OCR sigue siendo referencia no confiable: la persona debe cotejar el original y capturar las cantidades manualmente. Falta validar con formatos reales adicionales de almacén.

## Iteración 95 — escáner de cámara entre navegadores (2026-11-11)

La PWA ahora usa un decodificador local de ZXing al abrir la cámara, incluidos navegadores móviles donde `BarcodeDetector` no está implementado. La biblioteca se carga bajo demanda para no aumentar el bundle inicial. El escaneo identifica un artículo del inventario ya consultado; no registra movimientos. Siguen disponibles la captura manual y los lectores que escriben el código.

| Tarjeta | Estado revisado | Cambio entregado / alcance pendiente |
| --- | --- | --- |
| US-28 | Parcial funcional | La cámara ya no depende de `BarcodeDetector` y conserva búsqueda manual/lector teclado. Falta validarlo en teléfonos, formatos de etiqueta y lectores reales; queda pendiente confirmar el comportamiento de cámara sin conexión. |

La migración `202611110107` agrega una revisión append-only de US-28. Producto integrado por PR [#154](https://github.com/goodmorning-mx/arcoenergy/pull/154), merge commit `984f648628fda1a1efe2559aec127daac996eca1`; CI pasó backend, CRM, frontend, Next.js y Docker/Chrome en [#43071831401](https://github.com/goodmorning-mx/arcoenergy/actions/runs/43071831401) y tras el merge en [#43072191113](https://github.com/goodmorning-mx/arcoenergy/actions/runs/43072191113). DEV sirve la API lista y PWA con commit `984f648628fda1a1efe2559aec127daac996eca1`; `/app/` respondió HTTP 200. La validación automatizada de Chrome confirma que las rutas renderizan; la cámara física requiere validación con dispositivos de ArcoEnergy.

## Iteración 96 — cobertura de reportes operativos (2026-11-11)

Se contrastó US-29 con la implementación actual del CRM y del endpoint privado `/v1/reports/operations`. La superficie de reportes presenta la gráfica circular y tabla de existencias, movimientos del almacén con rango de fechas y CSV paginado, conteos/listas de clientes y proveedores, proyectos/órdenes agrupados por estado y gastos del periodo con categoría, tipo, descripción, proyecto, cuenta y responsable. La API filtra costos unitarios y caja/bancos según los permisos. Estos reportes descriptivos no se presentan como estados financieros oficiales.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-29 | Funcional básico | Cubre las secciones descritas en la tarjeta y sus criterios registrados; backend prueba agregados, paginación, fechas y ocultamiento de costos. Fórmulas contables y resultado oficial quedan en US-12/US-38, sujetos a validación del contador. |

La migración `202611110108` añade una nueva versión append-only de US-29 sin alterar la fuente. Evidencia de producto ya integrada: PR [#154](https://github.com/goodmorning-mx/arcoenergy/pull/154), CI [#43071831401](https://github.com/goodmorning-mx/arcoenergy/actions/runs/43071831401), merge commit `984f648628fda1a1efe2559aec127daac996eca1`; pruebas unitarias específicas en `backend/tests/test_operations_report.py`. Para esta revisión de tarjeta, se agregan prueba de preservación del texto original, CI del nuevo esquema y verificación posterior a despliegue.

## Iteración 97 — preparación offline del escáner (2026-11-11)

Al iniciar sesión con una cuenta instalador y conexión, la PWA carga en segundo plano el módulo ZXing mientras el service worker está listo. Su estrategia de caché de red guarda las solicitudes GET bajo `/app/`, incluido el chunk diferido del lector. Esto prepara la lectura con cámara para un posterior uso sin señal, sin cargar el módulo al iniciar sesión de otros roles. Si la precarga falla, queda la captura manual y el último inventario sincronizado.

| Tarjeta | Estado revisado | Cambio / alcance pendiente |
| --- | --- | --- |
| US-28 | Parcial funcional | El chunk de cámara se precarga para instaladores conectados y se almacena en la caché del service worker; manual y lector teclado siguen disponibles. Falta recorrer conexión → precarga → modo avión → lectura con teléfono/etiqueta reales. |

La migración `202611110109` registra una revisión append-only de US-28. La implementación comparte bundle diferido con PR [#154](https://github.com/goodmorning-mx/arcoenergy/pull/154); esta revisión suma la precarga al iniciar sesión de instalador. Se verifica typecheck y build local, pruebas de migración y la CI de producto con build Docker/Chrome. La cámara física en modo avión sigue pendiente de validación con ArcoEnergy.

## Iteración 98 — cobertura del seguimiento comercial (2026-11-11)

Se cotejó US-4 con su fuente de Goito. El drawer CRM permite añadir nota a la bitácora o programar seguimiento para 3, 7, 15 y 30 días, o seleccionar una fecha libre futura; captura el comentario del cliente y la persona responsable. La agenda/lista muestra seguimientos y la ficha conserva actividad. El recordatorio push es adicional: que el dispositivo no reciba una notificación no elimina ni oculta el seguimiento guardado.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-4 | Funcional básico | Cubre presets, fecha libre, responsable, comentario y bitácora. Pruebas backend verifican creación, asignación y alcance por usuario; el CRM compila. Falta validar recepción del aviso con vendedores y dispositivos reales. |

La migración `202611110110` agrega versión append-only de US-4 y conserva el texto fuente literal. La agenda, CRM y endpoints son anteriores; esta iteración registra la comprobación de criterios y añade prueba de integridad de la versión. 

## Iteración 99 — consulta de caja y bancos (2026-11-11)

Se contrastó US-18 con el CRM: la sección de cuentas carga caja y bancos autorizados con saldo; al seleccionar una cuenta abre su historial de movimientos. Administración puede dar de alta la cuenta y el saldo inicial para empezar el control. Los saldos salen de movimientos registrados y no se presentan como conciliación automática con el banco.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-18 | Funcional básico | La vista enumera cuentas y permite abrir el reporte de cada una. La API está protegida por permisos y sus operaciones de flujo se cubren en pruebas de backend; configuración de cuentas y saldos reales depende de administración. La conciliación bancaria no forma parte del criterio recibido. |

La migración `202611110111` añade una versión append-only de US-18 conservando la fuente. Se agrega prueba de integridad y la cobertura existente de `/accounts`, movimientos y flujo de efectivo se ejecuta en la suite backend.

## Iteración 100 — cobertura del registro de gastos (2026-11-11)

El CRM y la PWA permiten capturar fecha, monto, descripción, categoría y tipo fijo/variable; seleccionar la cuenta que pagó; asociar proyecto/orden y adjuntar comprobante desde campo. Los gastos aparecen en reportes y el registro se vincula a los movimientos de cuenta. La captura cumple los campos y relaciones descritos en US-17.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-17 | Funcional básico | Captura administrativa y móvil cubre fecha, monto, descripción, categoría, cuenta y vínculo opcional de proyecto. Gastos de campo aceptan comprobantes y mantienen estado Drive; contabilidad debe revisar casos mixtos, recurrencias y política de aprobación. |

La migración `202611110112` agrega una revisión append-only de US-17 sin editar la fuente. Pruebas actuales de backend verifican gastos, efectos en cuentas, correcciones y reportes; esta iteración agrega la prueba de integridad del registro de historia.

## Iteración 101 — cobranza de clientes y flujo de efectivo (2026-11-11)

Se verificó US-16 en CRM/API. El contador puede registrar un abono parcial o pago completo, su fecha, importe, cuenta de caja/banco y referencia opcional. El pago se enlaza con la deuda y crea el movimiento de entrada en la cuenta elegida; el saldo por cobrar se recalcula. El historial muestra cuenta, fecha, importe y referencia. Si un pago fue capturado por error, se corrige con una reversa trazable que conserva el original.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-16 | Funcional básico | Las pruebas backend verifican pagos parciales/completos, actualización de saldo, flujo de efectivo, cuenta reportada y reversas append-only. La asignación de un pago entre múltiples deudas/cuotas, mora y cancelaciones todavía requiere reglas contables. |

La migración `202611110113` añade la nueva versión de US-16 sin alterar su relato literal. La prueba de migración verifica la preservación de la fuente y los criterios nuevos. El endpoint existente requiere `receivables:write`; la vista se encuentra en la sección de cobranza del CRM.

## Iteración 102 — directorio y saldos de proveedores (2026-11-11)

Se cotejó US-30 con el directorio CRM y los datos de compras. El usuario autorizado puede registrar proveedor con nombre, datos de contacto, contado o crédito y días acordados. El listado muestra su condición y saldo por pagar derivado de compras/pagos; el detalle de compras conserva los movimientos ligados. Los proveedores no se eliminan en cascada.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-30 | Funcional básico | La API prueba alta/lista y la suite de compras verifica deuda y saldo tras abonos. El cliente debe confirmar campos adicionales y si quiere un estado explícito de proveedor inactivo/archivado. |

La migración `202611110114` añade la versión 2 de US-30 sin reescribir la fuente. El endpoint exige permisos `suppliers:read` para consultar y `suppliers:manage` para alta. Los pagos a proveedor se registran desde la compra asociada, conservando el vínculo contable.

## Iteración 103 — dashboard y dependencias legales (2026-11-11)

Se verificó US-19 contra el CRM y el endpoint de dashboard: presenta cartera vencida/próxima, saldos visibles por permiso, disponibilidad y faltantes de almacén, una gráfica de entradas/salidas de siete días y accesos a acciones prioritarias. Contabilidad y administración todavía deben aprobar los umbrales y métricas del negocio.

También se revisaron US-5 y US-6 contra el requisito original. No hay plantillas legales aprobadas ni reglas acordadas para guardar INE; tampoco se ha aprobado proveedor, consentimiento o proceso para firma/biometría. Las tarjetas nuevas registran esas dependencias de manera explícita. No se generan documentos ni se recoge información sensible hasta contar con las decisiones y materiales correspondientes; se mantiene la alternativa de firma física solicitada.

| Tarjeta | Estado revisado | Alcance pendiente |
| --- | --- | --- |
| US-19 | Funcional básico | El dashboard cubre los indicadores visibles y las gráficas operativas existentes. Falta que administración/contador confirme fórmulas, umbrales y prioridades. |
| US-5 | Bloqueada por material legal y privacidad | Requiere plantillas aprobadas y política de datos/consentimiento para INE del titular y responsable solidario. |
| US-6 | Bloqueada por decisión legal y proveedor | Requiere confirmar validez, consentimiento, proveedor de firma/verificación y manejo de excepción física. |

La migración `202611110115` añade versiones append-only para US-5, US-6 y US-19 sin alterar las fuentes originales. Las pruebas existentes de dashboard/API y la prueba nueva de migración validan criterios y conservación del texto literal.

## Iteración 104 — compras, saldos y pagos a proveedores (2026-11-11)

Se verificó US-31 en el flujo de compras CRM/API. Una compra a crédito guarda su proveedor, suma material al inventario y crea el saldo pendiente. Al pagar, el usuario elige fecha, importe y cuenta; el pago queda ligado a la compra y reduce la cuenta por pagar y el saldo de caja/banco. Los pagos parciales y las correcciones append-only conservan el historial.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-31 | Funcional básico | Las pruebas cubren compra a crédito, deuda con proveedor, pagos iniciales/parciales, saldos de cuenta y reversa trazable. La conciliación contra estados bancarios requiere reglas del contador. |

La migración `202611110116` añade la revisión 2 de US-31 sin reescribir el texto fuente. La prueba de historia verifica la preservación del literal; `test_purchases_payables.py` cubre la lógica contable operativa.

## Iteración 105 — costos directos y resultado preliminar (2026-11-11)

Se verificaron US-12 y US-38 contra CRM/API y las pruebas de reporte. El costo directo toma materiales consumidos confirmados por proyecto/orden; devoluciones reutilizables restan su costo. Si hay movimientos sin costo, el sistema indica el faltante y evita presentar un resultado total como si estuviera completo. El CRM reúne flujo de efectivo, cuentas por cobrar, valor/movimientos de almacén y gastos. El reporte preliminar por mes o proyecto aplica ventas − materiales − gastos + devoluciones/bonificaciones registradas y distingue el resultado de un estado financiero oficial.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-12 | Funcional básico | Pruebas de backend cubren costeo desde consumos, devoluciones y movimientos sin costo. El contador debe aprobar la valuación y el tratamiento de ajustes antes de cierre oficial. |
| US-38 | Parcial funcional | El reporte preliminar cubre mes/proyecto y desglose fijo/variable, con flujo, cartera, existencias y gastos disponibles en CRM. Fechas de corte, reclasificaciones y tratamiento fiscal requieren aprobación de contabilidad. |

La migración `202611110117` agrega versiones append-only para ambas tarjetas, preservando los textos fuente. `test_profitability_report.py`, `test_inventory_returns.py`, `test_accounts_cashflow.py` y `test_operations_report.py` ejercitan los componentes operativos; el cambio incluye una prueba de integridad de historia.


## Iteración 106 — resolución de conflictos offline en campo (2026-11-11)

La PWA ahora guarda en IndexedDB el estado y el motivo de los rechazos de acciones pendientes. La primera acción rechazada mantiene el orden FIFO y pausa la sincronización posterior; el instalador puede corregir la cantidad de un consumo o devolución para reintentar con el mismo `operation_id`, que el servidor valida de nuevo contra el inventario actual. Las operaciones se pueden retirar individualmente con confirmación. Si el servidor reporta que el identificador ya fue usado con otro payload, la interfaz no permite editarlo y advierte que se debe revisar el historial para evitar duplicar o perder un movimiento.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-9 | Funcional básico con resolución local de conflictos | Cola IndexedDB preservada entre recargas, detalle HTTP 4xx guardado, bloqueo FIFO y edición de cantidad para consumo/devolución. Falta validar sincronización simultánea y usabilidad con instaladores/dispositivos reales. |

La migración `202611110118` agrega una nueva versión append-only de US-9 y conserva la fuente literal original. El build PWA y la prueba de integridad de migración se ejecutan antes de integrar.

## Iteración 107 — inventario automático de autorización API (2026-11-11)

Se añadió una auditoría estática que recorre cada endpoint HTTP definido bajo `/v1` y falla si una ruta no declara `require_permissions` o `require_any_permission` en su decorador o firma. Solo permite sin autenticación los endpoints públicos de captación de prospectos y chat; si se agrega una nueva ruta pública, debe incorporarse explícitamente a la lista de excepciones revisada. Los endpoints de suscripción push conservan su permiso en el parámetro de identidad.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Todas las rutas privadas tienen una dependencia de permiso explícita según el inventario estático, además de las pruebas existentes de permisos por rol y aislamiento de cliente. La comprobación no sustituye la matriz aprobada por responsables ni pruebas con las cuentas reales de los cinco roles. |

La migración `202611110119` agrega una versión append-only de US-14 y conserva el texto fuente original. `test_api_route_authorization_inventory.py`, `test_role_authorization.py` y `test_roles.py` validan cobertura de dependencias, matriz de roles y aislamiento de datos.


## Iteración 108 — resguardo de ventas Plan 24 (2026-11-11)

Se detectó que una propuesta con forma de pago Plan 24 podía convertirse en venta de crédito ordinaria y generar cuotas estándar, aunque la tanda no tiene reglas definidas. La API ahora rechaza esa conversión antes de crear datos contables u operativos y el CRM mantiene visible la propuesta, explica el motivo y deshabilita la acción de registrar venta. Las propuestas Plan 24 siguen permitidas para conversación comercial; su conversión requiere aprobación de reglas del contador.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-15 | Parcial funcional con bloqueo de Plan 24 | Prueba backend confirma que la propuesta permanece intacta y que no se crean venta, orden o cartera. Contabilidad debe definir anticipo, distribución de pagos, incumplimiento y efectos asociados antes de habilitar la tanda. |
| US-36 | Parcial funcional | Entradas manuales elegibles ahora admiten reversa append-only con motivo y enlace. Compras, existencia inicial, entradas con actividad posterior y saldos insuficientes exigen conciliación; falta validar más ciclos de inventario con Contabilidad. |

La migración `202611110120` agrega la revisión append-only de US-15 y conserva su relato original. `test_sales_work_orders.py` cubre el bloqueo de la ruta de creación; la interfaz CRM distingue la propuesta pendiente de una venta registrable.


## Iteración 109 — reintentos de sincronización temporal (2026-11-11)

La PWA ahora distingue rechazos de negocio de fallas temporales del protocolo: HTTP 401, 408, 425, 429 y 5xx conservan la acción y no la marcan como conflicto que bloquee la cola tras recargar. Para 401 indica renovar la sesión; para 429 indica esperar; el control de reintento manual vuelve a enviar el mismo `operation_id`. Respuestas permanentes de permiso o validación siguen mostrando el detalle y pausando la cola FIFO para revisión.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-9 | Funcional básico con recuperación de fallas temporales | TypeScript distingue estados transitorios del conflicto permanente y mantiene idempotencia. La migración de historia conserva el texto original. Falta validar sesión vencida, limitación de solicitudes y retorno de conexión en teléfonos reales. |

La migración `202611110121` agrega una revisión append-only de US-9. El build de producción PWA y las pruebas backend de migración validan el cambio.


## Iteración 110 — corrección de entradas manuales de inventario (2026-11-11)

Desde el kardex, Administración puede corregir una entrada manual errónea indicando el motivo. El sistema conserva la entrada original y registra una reversa enlazada, actualiza existencias y la muestra como salida compensatoria. Bloquea correcciones repetidas, existencias iniciales, compras, artículos con movimientos posteriores y casos donde la existencia actual no cubre la entrada, para evitar ocultar historial o desajustar el costeo.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-36 | Parcial funcional con reversa de entrada manual | API, kardex y CRM admiten correcciones append-only. Las compras siguen usando su corrección de origen. Reversas con actividad posterior/costo promedio requieren conciliación contable; falta validar casos reales con el contador. |

La migración `202611110122` guarda una nueva versión de la tarjeta US-36 sin sobrescribir sus relatos previos. Pruebas backend cubren el movimiento compensatorio, las entradas no elegibles y los bloqueos de conciliación.


## Iteración 111 — disponibilidad por orden para instaladores (2026-11-11)

La consulta de instalaciones de la PWA filtra por asignación y entrega, por cada material solicitado, el nombre, cantidad pendiente, disponibilidad para esa orden y faltante calculado con las reservas de otras órdenes abiertas. La prueba de permisos ahora verifica el cálculo con un instalador asignado y confirma que no recibe la orden ajena; una prueba de manager conserva la comparación de órdenes concurrentes.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-8 | Funcional básico | Prueba backend valida cantidad solicitada, disponibilidad 2 y faltante 6 en dos órdenes concurrentes; la identidad instaladora solo recibe la orden asignada. Falta validación con almacén real y en los teléfonos de campo. |

La migración `202611110123` guarda una nueva versión append-only de US-8 y mantiene intacto el relato de Goito.


## Iteración 112 — auditoría funcional de inventario (2026-11-11)

Se cotejaron criterios fuente y pruebas actuales para catálogo, salida/consumo, bajo stock y kardex. La prueba de regresión seleccionada pasó 35 casos. La comprobación de UI visual en navegador no se pudo ejecutar en este entorno porque no hay navegador conectado; las builds y pruebas backend siguen siendo evidencia de funcionamiento, no sustituyen esa revisión ni la validación con dispositivos/datos reales.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-20 | Funcional básico | Catálogo conserva descripción, categoría/subcategoría, marca, modelo, proveedor, unidad y código; CRM imprime etiqueta QR y la PWA identifica por cámara/captura. Faltan validar unidades y etiquetas físicas con almacén. |
| US-24 | Funcional básico | Orden distingue solicitud, reserva/salida física y consumo; devolución enlazada corrige saldo y costo sin doble descuento. Falta acordar autorización formal de variaciones y validar la rutina física. |
| US-26 | Funcional básico | Mínimo y responsable de reposición se configuran por artículo; Web Push se entrega a sus dispositivos suscritos al activarse alerta. Falta validar la recepción en equipos reales. |
| US-27 | Funcional básico | CRM filtra kardex por artículo/fecha, pagina resultados y descarga el intervalo completo; los costos solo aparecen/exportan con permiso. Falta validar volumen real y costo histórico incompleto. |

La migración `202611110124` agrega versiones append-only para US-20, US-24, US-26 y US-27; conserva cada relato fuente y sus versiones anteriores.


## Iteración 113 — comparación actual de portales para US-37 (2026-11-11)

Se actualizó la matriz de las secciones visibles en el Word/PDF del contador frente a las pantallas actuales de CRM y PWA. La referencia incluye Dashboard, Inventario, Entradas, Salidas, Kardex, Escáner, Reportes, Proveedores, Proyectos, Usuarios y Configuración. La revisión de DEV registra commit `b5740b6232445af2d066e5e4a5e54b12a3251049`, esquema `202611110124` y HTTP 200 para API, web, CRM y PWA. La matriz separa las funciones implementadas de las brechas y no infiere pantallas que no estén en la fuente.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-37 | Parcial funcional | La matriz coteja cada sección visible de la fuente con CRM/PWA y registra la versión viva de DEV. Falta comparar visual y funcionalmente con el sistema actual de César; no se pudo hacer la inspección visual del portal en este entorno y Administración debe confirmar si necesita una pantalla única de Configuración. |

La migración `202611110125` agrega una versión append-only de US-37, conservando el relato fuente y las versiones previas.


## Iteración 114 — consentimiento y contacto del agente público (2026-11-11)

La prueba viva del endpoint `/v1/public/agent/chat` respondió HTTP 200; como el catálogo no tiene paquetes con precio aprobado, el agente no dio cifras. Se corrigió la instrucción para que nunca solicite datos personales en la conversación ni afirme que guardó un prospecto: remite al formulario comercial, que presenta el aviso de privacidad y consentimiento. La interfaz explica este límite antes de iniciar el chat.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-41 | Parcial funcional | Agente público conectado a herramienta de catálogo de solo lectura; endpoint vivo respondió y respetó precios no aprobados. Contacto ahora pasa por formulario con privacidad/consentimiento. Faltan paquetes comerciales reales aprobados y validar el recorrido de cotización completo. |

La migración `202611110126` agrega una versión append-only de US-41 sin alterar su fuente literal.


## Iteración 115 — ubicaciones literales de fuentes de audio y WhatsApp (2026-11-11)

Se cotejaron las 42 fuentes iniciales contra los artefactos disponibles. Las fuentes de US-1–20, US-22–33 y US-36–42 coinciden con sus extractos registrados después de normalizar formato; US-21 conserva su corrección completa en la versión 2. US-34 reúne dos clips ASR y US-35 selecciona mensajes literales no contiguos, por lo que esta iteración guarda ubicaciones específicas en lugar de tratarlos como un único pasaje continuo. Se registran los hashes de los audios originales y se mantiene visible que las transcripciones no han sido validadas por el remitente.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-33 | Procedencia ASR trazable | El relato literal se conserva; se enlaza al clip original 4:16:19 p.m., marcas 00:00–00:38, hash SHA-256 y transcripción. La frase «entradas alimentarios» permanece sin corregir hasta validación del stakeholder. |
| US-34 | Procedencia ASR trazable | El relato literal se conserva y se enlaza por separado a los clips 4:15:39 p.m. y 4:16:19 p.m., con hashes y rangos de tiempo. El primer clip está incompleto y la atribución del remitente sigue sin confirmarse. |
| US-35 | Extractos literales trazables | El relato literal se conserva como cinco segmentos y cada uno se enlaza a su mensaje y hora en el artefacto de Mario Groso; los segmentos seleccionados no representan mensajes omitidos. |
| US-42 | Parcial funcional | La base append-only conserva las versiones y ahora registra ubicaciones de fuente para US-33–35. Sigue pendiente cotejar con stakeholders las tarjetas reconstruidas, validar los ASR y definir almacenamiento/retención de fuentes sensibles. |

La migración `202611110127` agrega versiones nuevas sin sobrescribir el texto literal ni los metadatos históricos. Las pruebas verifican preservación de versiones, ubicaciones de los dos audios y correspondencia de sus hashes con el manifiesto de fuentes.


## Iteración 116 — cotejo del menú público Base44 para US-37 (2026-11-11)

Se abrió la URL pública de ArcoEnergy Inventario referida en el Word del contador. La raíz y su bundle de navegación respondieron HTTP 200. El bundle declara las 11 etiquetas y rutas que aparecen en el menú de la captura del PDF; se guarda su SHA-256 como evidencia reproducible. La consulta llegó solo a recursos públicos: no acredita pantallas renderizadas, información tras autenticación ni operaciones del sistema.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-37 | Parcial funcional | Menú de referencia vigente cotejado con el PDF: 11 etiquetas y rutas confirmadas mediante bundle público con hash. Falta comparación visual y de comportamiento autenticada con César; la matriz CRM/PWA continúa separando implementado y pendiente. |

La migración `202611110128` agrega una nueva versión append-only de US-37, conserva su relato literal y asocia el bundle público como evidencia de validación.


## Iteración 117 — lecturas anónimas en API DEV para US-14 (2026-11-11)

Se descargó el OpenAPI publicado por DEV en el commit `df4043e782e4504c3fb29c8dcd50e9cc125d0f4f`, esquema `202611110128`, y se consultaron sin credenciales las 34 operaciones GET declaradas bajo `/v1`. Las 34 devolvieron HTTP 401, incluyendo rutas con identificadores. El documento OpenAPI queda ligado a la tarjeta por su hash SHA-256 `8c73e79b4fc9c5fb1e71ec2017b1098789c4406ae41598ad9d85699dc4425589`.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Auditoría anónima viva: 34/34 GET de `/v1` devolvieron 401. Esto prueba requisito de sesión para lectura, no el alcance de datos por rol/organización/cliente/campo; faltan cuentas reales para validar esos permisos. |

La migración `202611110129` añade una versión append-only de US-14 sin modificar su relato literal. Las pruebas verifican que el artefacto, su hash y el resultado de la revisión queden registrados en una versión nueva.


## Iteración 118 — ubicaciones de fuente para las 42 history cards (2026-11-11)

Se completó el mapa de procedencia de las 42 tarjetas. Las versiones nuevas de US-1–32 y US-36–42 enlazan las fuentes espejo con hashes SHA-256 y ubicaciones de mensaje, párrafo/página o texto; US-33–35 conservan los enlaces específicos añadidos en la Iteración 115. Para documentos del contador se guardan referencias al Word original, al PDF y a la extracción textual. US-21 usa el apartado completo corregido en su versión 2. No se cambia ningún `source_literal` anterior. La prueba de fidelidad verifica que cada literal coincide con su fuente o queda descrito como compuesto por segmentos específicos.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-1–US-42 | Procedencia de fuente trazable | Las 42 tarjetas tienen artefactos y ubicaciones consultables en sus versiones recientes; hash y coincidencia de texto comprueban procedencia, no aprobación de la interpretación por el stakeholder. Los ASR (US-33/34) siguen pendientes de validación humana y las tarjetas reconstruidas requieren cotejo con sus autores. |
| US-42 | Parcial funcional | La base de datos, API y CRM mantienen versiones append-only. Esta iteración agrega procedencia exacta para los relatos existentes; quedan pendientes la validación humana de las transcripciones ASR, el cotejo de interpretaciones y la política de almacenamiento/retención de fuentes sensibles. |

La migración `202611110130` agrega 39 versiones con ubicación de fuente sin cambiar texto previo; US-33–35 ya cuentan con sus ubicaciones de audio/chat de la Iteración 115. Las pruebas cotejan los hashes de seis artefactos del repositorio y la preservación de las versiones literales.

## Iteración 119 — continuidad del asistente CRM (2026-11-11)

El panel del asistente CRM ahora se oculta sin desmontar el chat. Al cerrar y volver a abrir el panel durante la sesión, el hilo y el identificador de conversación permanecen disponibles. Esto evita reiniciar una consulta al alternar el panel. La conversación continúa siendo temporal en memoria del proceso; no se añade persistencia de mensajes sin acordar privacidad y retención.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-39 | Parcial funcional | La interfaz conserva el hilo al ocultar y reabrir el asistente durante la sesión. La continuidad no sobrevive a recargas o reinicios del API; retención durable requiere decisión de privacidad. |

La migración `202611110131` añade una revisión append-only de US-39 y conserva su relato literal.

## Iteración 120 — exportación privada de datos empresariales a Drive (2026-11-11)

El CRM añade una vista de integraciones solo para administración. Si la carpeta y la cuenta de servicio están conectadas, puede generar manualmente un JSON privado con una lectura consistente de las tablas de negocio, history cards y perfiles/roles de equipo. El archivo tiene un límite de 64 MB. Omite hashes de contraseña, sesiones, credenciales de notificación y registros técnicos de reintentos offline. Si Drive no está conectado o falla la carga, el CRM muestra el error y no informa que guardó el archivo. No hay programación automática ni restauración de la base de datos.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-13 | Parcial funcional | Se agrega exportación manual y privada del conjunto de datos empresariales desde el CRM; faltan credenciales/carpeta real en DEV, calendario automático, restauración y política de retención aprobada. |

La migración `202611110132` agrega una versión append-only de US-13 y conserva intacta su fuente literal.

## Iteración 121 — redirección de superficies protegidas al login (2026-11-11)

La prueba de Chrome del contenedor ahora inicia también en las raíces protegidas `/app/` y `/crm/` sin sesión. Exige que cada aplicación termine renderizando su formulario de inicio de sesión, además de revisar `/app/login`, `/crm/login` y el alias `/login`. No se agregan usuarios ficticios; DEV provisiona únicamente la cuenta bootstrap de administración definida por Factory, y el resto del equipo debe registrarse con identidades reales.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | CI valida en Chrome los accesos directos a las raíces de PWA y CRM sin sesión, además de las tres rutas explícitas de login. Sigue pendiente verificar privilegios y aislamiento con cuentas reales de cada rol y de clientes/instaladores asignados. |

La migración `202611110133` agrega la verificación a una versión nueva de US-14 sin sobrescribir el relato literal.

## Iteración 122 — captura asistida de CFDI XML para compras (2026-11-11)

El flujo de compras acepta CFDI XML 3.3 y 4.0 de ingreso en MXN, extrae proveedor, UUID/referencia, fecha, conceptos y montos, y prepara el formulario para revisión. Puede proponer proveedor por RFC y artículo por código exacto del catálogo. El XML se procesa en memoria y no crea una compra ni altera almacén por sí solo. Si el total difiere del neto de conceptos —por impuestos, descuentos globales u otros ajustes— el CRM exige revisión; no distribuye esos importes automáticamente.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-22 | Parcial funcional | Pruebas verifican CFDI 3.3/4.0, conceptos y el rechazo de DTD/entidades, monedas, tipos de comprobante y cantidades incompatibles. La captura requiere revisión antes de registrar. Falta validar con facturas reales y que Contabilidad defina impuestos, fletes y descuentos. |

La migración `202611110134` agrega una nueva versión append-only de US-22 y conserva su fuente literal.

## Iteración 123 — alta de cuentas cliente vinculadas a cartera (2026-11-11)

El administrador puede crear una identidad con rol `cliente` desde Equipo después de registrar su ficha en la cartera. La API valida el mismo correo antes de crear o asignar ese rol; el portal filtra propuestas, instalaciones y pagos por esa dirección y devuelve una proyección sin notas internas, correos de instaladores ni IDs privados de Drive. El CRM explica este requisito al seleccionar el rol.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | El alta de cliente requiere coincidencia de correo con su ficha y la prueba de alcance confirma que no se mezclan datos de otro correo. Falta validar el flujo con una cuenta real creada por administración y completar las pruebas de permisos en los dispositivos del equipo. |

La migración `202611110135` registra una versión nueva de US-14 y preserva su fuente original.

## Iteración 124 — respaldos empresariales periódicos y privados en Drive (2026-11-11)

Cuando Factory configura la carpeta privada y las credenciales de servicio de Google Drive, el backend genera un respaldo JSON empresarial inicial y luego lo repite cada 24 horas por defecto (intervalo ajustable entre 1 y 168 horas). El estado de cada ejecución queda registrado y la vista de integraciones en CRM muestra configuración, último intento, último éxito y errores seguros. La exportación manual existente permanece disponible. El trabajo usa un bloqueo de PostgreSQL para evitar ejecuciones duplicadas entre réplicas y no inicia ni afirma respaldos si Drive no está configurado.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-13 | Parcial funcional | Se añade programación durable y estado visible de respaldos privados. Falta configurar y verificar Drive en DEV; retención, restauración y recuperación ante corrupción requieren política acordada. |

La migración `202611110136` agrega una versión append-only de US-13 y conserva intacta su fuente literal. Las pruebas enfocadas cubren el primer respaldo, intervalo, falta de configuración, error de carga y preservación de la tarjeta.

## Iteración 125 — verificación del despliegue DEV del respaldo (2026-11-12)

Factory reconcilió los cinco servicios de ArcoEnergy DEV, terminó sus despliegues, verificó el esquema vivo `202611110136` y confirmó un respaldo externo de la base PostgreSQL. La evidencia pertenece al flujo de despliegue de Factory; no prueba que la nueva tarea haya escrito un archivo empresarial en Google Drive. La carpeta de Drive y la cuenta de servicio siguen sin configurarse, por lo que el programador informa espera y no afirma un respaldo empresarial.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-13 | Parcial funcional | Despliegue DEV y esquema `202611110136` verificados por [Factory run #384](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/43139093999); producto integrado en [PR #184](https://github.com/goodmorning-mx/arcoenergy/pull/184). Falta autorizar/configurar Drive y comprobar una carga real, retención y restauración. |

La migración `202611120137` agrega una nueva versión append-only de US-13 y conserva intacta su fuente literal.


## Iteración 126 — reutilización de clientes en cotizador PWA (2026-11-12)

El cotizador de campo permite buscar y seleccionar una ficha existente antes de emitir una propuesta. Al seleccionarla, los datos de identidad quedan ligados a esa ficha y el vendedor todavía puede indicar el lugar específico de instalación. Cuando se crea un cliente nuevo, su ID se conserva en el formulario aunque falle el paso posterior de cotización o PDF, de modo que reintentar no duplica la ficha. Cambiar la selección limpia el folio y el PDF de la propuesta anterior.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-1 | Parcial funcional | PWA reutiliza clientes existentes y evita duplicar el recién creado en un reintento. Falta validar con cartera y cuentas comerciales reales en DEV; no se carga precio no aprobado. |
| US-3 | Parcial funcional | La propuesta se asocia a la ficha elegida y se limpia el PDF/folio al cambiar de cliente. El guardado empresarial en Drive sigue pendiente de configurar y comprobar credenciales privadas. |

La migración `202611120138` agrega nuevas versiones append-only de US-1 y US-3, conservando intactos sus relatos literales.


## Iteración 127 — despliegue DEV de cotizador PWA y esquema (2026-11-12)

Factory run [#43146112522](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/43146112522) terminó correctamente. Sus logs registran que los cinco servicios de ArcoEnergy DEV terminaron, que la revisión viva de base de datos `202611120138` quedó verificada y que el respaldo externo de PostgreSQL se validó en Object Storage. Esto demuestra la aplicación del despliegue y su respaldo de infraestructura. La nueva revisión de Chrome detectó que entrar sin sesión por la raíz de `/app/` dejaba la pantalla vacía durante la redirección; se corrigieron PWA y CRM para mostrar el login inmediatamente y cambiar la URL al acceso correspondiente. El test de navegador debe volver a pasar antes de integrar esta revisión. No demuestra el acceso autenticado con vendedores/instaladores reales ni que el exportador empresarial haya escrito un JSON en Google Drive.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-1 | Parcial funcional | El código del cotizador PWA está en la versión de DEV desplegada. Falta recorrer selección y generación autenticada con cuentas comerciales reales y catálogo aprobado. |
| US-3 | Parcial funcional | El despliegue de los cinco servicios quedó verificado; la carga del PDF a Drive y el envío en contexto real de WhatsApp no se verificaron. |
| US-13 | Parcial funcional | Factory verificó esquema vivo `202611120138` y respaldo externo de PostgreSQL. La integración privada de Drive, su retención y restauración permanecen pendientes. |
| US-14 | Parcial funcional | El acceso sin sesión desde la raíz ahora renderiza el login y actualiza la URL sin depender de una navegación en blanco; falta CI de Chrome y validación de permisos con cuentas reales. |
| US-40 | Parcial funcional | PWA muestra su formulario de login al abrir `/app/` sin sesión; falta CI de Chrome y validación en dispositivos de campo reales. |

La migración `202611120139` agrega evidencia append-only a US-1, US-3, US-13, US-14 y US-40 sin cambiar sus relatos originales.


## Iteración 128 — verificación Chrome del acceso protegido (2026-11-12)

Después de corregir el render del login en las raíces protegidas, CI run [#43245435339](https://github.com/goodmorning-mx/arcoenergy/actions/runs/43245435339) pasó en Chrome las cinco rutas `/app/`, `/app/login`, `/crm/`, `/crm/login` y `/login` sin sesión. El test verificó que el PWA y el CRM muestran el formulario, en lugar de quedar en blanco. La compilación y validación Docker del mismo commit también pasaron. Esta prueba no cubre el inicio de sesión exitoso, permisos por rol ni dispositivos reales.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | Chrome verifica que las rutas protegidas renderizan el login. Falta comprobar el acceso y aislamiento con cuentas reales por rol. |
| US-40 | Parcial funcional | Chrome verifica el formulario de acceso en la PWA desde la raíz y la ruta explícita. Falta validar teléfonos y flujos autenticados de campo. |

La migración `202611120140` agrega esta evidencia a US-14 y US-40 sin sobrescribir sus fuentes.


## Iteración 129 — búsqueda y vínculos visibles en history cards (2026-11-12)

La vista administrativa del historial permite localizar versiones por ID, relato literal, historia normalizada, stakeholder o iteración. En el detalle de cada versión se distinguen las tarjetas relacionadas de los enlaces que justifican la interpretación desde sus fuentes. Esto facilita revisar la evolución sin ocultar versiones anteriores.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-42 | Parcial funcional | CRM busca dentro de las versiones y muestra vínculos entre tarjetas y fuentes; el historial sigue append-only. El cotejo de las reconstrucciones, transcripciones ASR y la política de retención privada siguen pendientes. |

La migración `202611120141` agrega la evidencia a US-42 y conserva intacto el relato literal.


## Iteración 130 — preparación segura de credenciales Drive en Factory (2026-11-12)

Factory ahora admite secretos gestionados opcionales por producto. El manifiesto de ArcoEnergy declara la variable vacía `GOOGLE_DRIVE_FOLDER_ID` hasta que administración defina la carpeta privada, y referencia `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` mediante un secreto opcional que solo se pasa al reconciliador de desarrollo. Los archivos de credenciales no se agregan al repositorio. Factory PR [#493](https://github.com/goodmorning-mx/goodmorning-factory/pull/493) integró la capacidad y su redacción segura; PR [#494](https://github.com/goodmorning-mx/goodmorning-factory/pull/494) conectó las variables del producto. Los checks CI de ambos PR pasaron. Esto prepara el camino de configuración; no significa que Google Drive esté conectado ni que haya recibido archivos.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-3 | Parcial funcional | Factory dispone el ID de carpeta y el secreto opcional para el archivo de cotizaciones. Faltan la carpeta/credencial autorizadas y validar carga, lectura y compartir el PDF real. |
| US-10 | Parcial funcional | El API puede recibir el mismo secreto opcional para archivar comprobantes. Falta configurar Drive y comprobar una carga/reintento real desde PWA. |
| US-13 | Parcial funcional | El manifiesto de DEV ya expone el punto de configuración privada sin exponer la credencial. Faltan valores autorizados, carga del archivo empresarial, retención y restauración. |

La migración `202611120142` agrega versiones append-only para US-3, US-10 y US-13, manteniendo intactas sus fuentes literales. El secreto de servicio y el ID de carpeta siguen sin estar configurados; por eso el producto debe seguir reportando Drive como desconectado.

## Iteración 131 — verificación del esquema de DEV desplegado (2026-11-12)

Tras publicar el repositorio, el push de Factory commit `fa20b0258879cae68ed1b4cbdf479934f9fc6a1f` ejecutó la reconciliación `resources-v3`: los pasos **Apply and deploy selected products** y **Verify live database schema revisions** terminaron correctamente en [workflow run 43262729763](https://github.com/goodmorning-mx/goodmorning-factory/actions/runs/43262729763). El manifiesto de ArcoEnergy fija la revisión esperada en `202611120142`; la migración correspondiente queda verificada en la base de datos viva de DEV según ese workflow. Esta evidencia confirma la migración desplegada, pero no prueba carga a Drive ni disponibilidad HTTP desde este entorno: la credencial y la carpeta siguen pendientes y los portales respondieron `EHOSTUNREACH` desde el entorno de verificación.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-3 | Parcial funcional | La revisión de esquema `202611120142` quedó aplicada en DEV; Factory mantiene la configuración de Drive opcional. Faltan carpeta y credencial aprobadas y probar carga, lectura y compartir un PDF real. |
| US-10 | Parcial funcional | La revisión de esquema de DEV quedó aplicada; el archivo privado sigue dependiendo de Drive. Faltan la configuración autorizada y una carga/reintento real desde PWA. |
| US-13 | Parcial funcional | Se confirmó la revisión esperada en la base de datos viva; no se ha comprobado exportación empresarial en Drive, retención ni restauración. |

La verificación es automatizada por Factory y no sustituye la prueba funcional de Drive ni una revisión desde una red externa de las rutas públicas.

## Iteración 132 — verificación externa de API, PWA y CRM en DEV (2026-11-12)

Después de integrar el verificador de CRM en PR [#194](https://github.com/goodmorning-mx/arcoenergy/pull/194), el workflow de push [43267461835](https://github.com/goodmorning-mx/arcoenergy/actions/runs/43267461835) terminó correctamente. Desde GitHub Actions, fuera de la red local de esta sesión, el verificador esperó y confirmó que API, PWA y CRM reportaran exactamente la SHA `04eadc7c915bb6becde4022e2605ef3e77f5b8dc`. CI [43267461892](https://github.com/goodmorning-mx/arcoenergy/actions/runs/43267461892) también pasó la construcción integrada, Chrome verificó que PWA y CRM renderizan, y las rutas `/app/version.json` y `/crm/version.json` fueron servidas. Esto confirma versiones y renderizado del entorno DEV; no valida sesiones con las cuentas reales de los cinco roles ni recorrido en teléfonos de los usuarios.

| Tarjeta | Estado revisado | Evidencia / alcance pendiente |
| --- | --- | --- |
| US-14 | Parcial funcional | La versión desplegada de API, PWA y CRM coincide con el commit de DEV y las rutas privadas pasan las verificaciones automatizadas. Falta probar autorización y aislamiento con cuentas reales de los cinco roles. |
| US-40 | Parcial funcional | La PWA y el CRM reportan el commit desplegado; ambos renderizan en la prueba Chrome de CI. Falta probar acceso autenticado y operación en teléfonos reales. |

La evidencia se limita al despliegue DEV automatizado y no acredita validación de negocio o dispositivos de campo.
