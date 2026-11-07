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

Fuentes literales recuperadas: [Word original](sources/contador-comentarios-mejoras-original.docx), [PDF original](sources/contador-mejoras-original.pdf) y [transcripción textual del Word](sources/contador-comentarios-mejoras-transcripcion.md).

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
- **Estado:** asistente consulta tamaños y devuelve total/inversor únicamente desde paquetes aprobados; la consulta directa del catálogo del CRM exige permiso. Formulario de prospecto con consentimiento. Requiere configurar la clave administrada de OpenAI en DEV; Drive, WhatsApp Business y carga de recibos no se declaran integrados.

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
| US-3 | Parcial | PDF foliado y enlace WhatsApp; Drive y envío/adjunto automatizado no están configurados. |
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

### Corrección necesaria para desplegar Iteración 16

El despliegue automático de DEV del commit `4d68416` se revirtió porque PostgreSQL rechaza el nombre de una llave foránea de más de 63 caracteres en la migración de reservas de materiales. Se acorta y se alinea el nombre en el modelo y en la migración. Hasta que se integre y despliegue esta corrección, DEV sigue sirviendo el commit API anterior `7d201b9`; no se considera desplegada la Iteración 16.
