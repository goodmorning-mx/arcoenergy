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
