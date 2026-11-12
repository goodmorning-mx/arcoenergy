# Cobertura vigente de las 42 user story cards

Fecha de corte: 2026-11-12. Esta matriz resume el último registro encontrado por tarjeta en [history-cards.md](history-cards.md). El registro es append-only: cada fila apunta al último estado/evidencia registrado, no modifica el relato original ni implica validación del stakeholder. “Funcional básico” significa que hay código y evidencia técnica para el alcance descrito; las verificaciones de negocio/dispositivo se indican aparte.

| Tarjeta | Última iteración registrada | Estado registrado y trabajo que falta |
| --- | --- | --- |
| US-1 | 127 · despliegue DEV del cotizador PWA | Parcial. Falta recorrido autenticado con usuarios comerciales y catálogo aprobado. |
| US-2 | 2 · producto autenticado y operación de campo | Pendiente/diferida: análisis automático del recibo de luz, fórmula y aprobación. El cliente indicó que es fase avanzada posterior. |
| US-3 | 131 · verificación del esquema de DEV desplegado | Parcial. Factory confirmó la revisión 202611120142 en la base de datos viva; Drive aún requiere carpeta/credencial aprobadas y prueba real de carga/lectura/compartición. |
| US-4 | 98 · cobertura del seguimiento comercial | Funcional básico: presets, fecha libre, responsable, comentarios y bitácora. Falta validar avisos con vendedores/dispositivos reales. |
| US-5 | 103 · dashboard y dependencias legales | Bloqueada por plantillas contractuales aprobadas y política de privacidad/consentimiento para INE. |
| US-6 | 103 · dashboard y dependencias legales | Bloqueada por decisión legal, consentimiento, proveedor de firma/verificación y excepción en papel. |
| US-7 | 82 · compatibilidad de instalación limpia para Web Push | Parcial: asignación y push implementados; falta validar recepción en dispositivos reales. |
| US-8 | 111 · disponibilidad por orden para instaladores | Funcional básico: faltantes por orden/reservas y permisos probados. Falta validación con almacén y teléfonos reales. |
| US-9 | 109 · reintentos de sincronización temporal | Funcional básico: cola offline idempotente y recuperación de fallos. Falta validar sesiones vencidas, límites de API y reconexión en campo. |
| US-10 | 131 · verificación del esquema de DEV desplegado | Parcial: captura/cola offline y archivo privado usan Drive y la revisión 202611120142 quedó desplegada. Falta configurar secreto/carpeta y confirmar carga real; falta política de aprobación de comprobantes. |
| US-11 | 81 · calendario de cobranza y caja | Parcial: agenda y textos para pago próximo/hoy/vencido. Falta confirmar planes, intereses y zona horaria de negocio. |
| US-12 | 105 · costos directos y resultado preliminar | Funcional básico: costo por consumos/devoluciones y faltantes de costo visibles. Falta aprobación contable de valuación y ajustes. |
| US-13 | 131 · verificación del esquema de DEV desplegado | Parcial: Factory expone configuración opcional segura y DEV verificó esquema 202611120142. Falta secreto/carpeta aprobados y confirmar exportación, retención y restauración en Drive. |
| US-14 | 128 · verificación Chrome del acceso protegido | Parcial: login separado y rutas protegidas verificadas. Falta probar acceso y aislamiento con cuentas reales de los cinco roles. |
| US-15 | 108 · resguardo de ventas Plan 24 | Parcial/bloqueada para Plan 24: el sistema impide crear efectos sin reglas. Contabilidad debe definir anticipo, calendario, incumplimiento y efectos. |
| US-16 | 101 · cobranza de clientes y flujo de efectivo | Funcional básico: pagos parciales/completos, caja y reversas. Falta definir distribución entre deudas, mora y cancelaciones. |
| US-17 | 100 · cobertura del registro de gastos | Funcional básico: gastos por fecha, cuenta y proyecto, incluida captura móvil. Falta política contable de casos mixtos, recurrencia y aprobación. |
| US-18 | 99 · consulta de caja y bancos | Funcional básico: cuentas, saldos y reportes protegidos por permiso. Administración debe cargar saldos reales; no incluye conciliación bancaria. |
| US-19 | 103 · dashboard y dependencias legales | Funcional básico: indicadores/gráficas operativas. Falta que administración/contador confirme fórmulas, umbrales y prioridades. |
| US-20 | 112 · auditoría funcional de inventario | Funcional básico: catálogo, atributos, QR impreso y lectura móvil. Falta validar unidades y etiquetas físicas con almacén. |
| US-21 | 90 · fidelidad de la fuente original de US-21 | Fuente corregida en versión 2. Falta acordar reconocimiento documental y vinculación contable de devoluciones. |
| US-22 | 122 · captura asistida de CFDI XML para compras | Parcial: CFDI XML 3.3/4.0 validado y revisable. Faltan facturas reales y reglas contables de impuestos, fletes y descuentos. |
| US-23 | 19 · devolución reutilizable y merma de obra | Funcional básico: retorno reutilizable repone stock; merma dañada conserva costo sin reingreso. Falta política de inspección/reparación. |
| US-24 | 112 · auditoría funcional de inventario | Funcional básico: solicitud, reserva/salida, consumo y devolución diferenciados. Falta autorizar variaciones y validar el proceso físico. |
| US-25 | 94 · lectura asistida de solicitud de materiales | Parcial: OCR de referencia para cotejo, sin registrar salida automáticamente. Falta medir precisión con órdenes reales manuscritas. |
| US-26 | 112 · auditoría funcional de inventario | Funcional básico: mínimos, responsable y Web Push implementados. Falta recepción en los equipos reales. |
| US-27 | 112 · auditoría funcional de inventario | Funcional básico: kardex con filtros, paginación y CSV; costos protegidos. Falta validar volúmenes y movimientos históricos sin costo. |
| US-28 | 97 · preparación offline del escáner | Parcial: lector de cámara precargable y alternativas manual/teclado. Falta recorrido completo offline con teléfonos y etiquetas reales. |
| US-29 | 96 · cobertura de reportes operativos | Funcional básico: agregados, fechas, paginación y permisos probados. La validación contable corresponde a US-12/US-38. |
| US-30 | 102 · directorio y saldos de proveedores | Funcional básico: directorio y relación con compras/pagos. Falta confirmar campos y política para proveedores inactivos. |
| US-31 | 104 · compras, saldos y pagos a proveedores | Funcional básico: compras contado/crédito, pagos parciales y reversas probados. La conciliación requiere reglas contables. |
| US-32 | 68 · entidad de proyecto con folio único | Parcial: entidad/código de proyecto agrupa órdenes y gastos. Falta confirmar formato del folio y cardinalidad operativa. |
| US-33 | 115 · ubicaciones literales de fuentes de audio y WhatsApp | Procedencia ASR trazable; la transcripción sigue sin validar por su autor. |
| US-34 | 115 · ubicaciones literales de fuentes de audio y WhatsApp | Procedencia ASR trazable; falta validar transcripción, integridad del clip y atribución del remitente. |
| US-35 | 115 · ubicaciones literales de fuentes de audio y WhatsApp | Extractos literales ligados a mensajes/horas; requieren cotejo de stakeholder para confirmar interpretación. |
| US-36 | 110 · corrección de entradas manuales de inventario | Parcial: reversas append-only para varios orígenes; faltan ciclos con actividad posterior/costo promedio y validación contable. |
| US-37 | 116 · cotejo del menú público Base44 | Parcial: menú público y rutas cotejados. Falta comparación autenticada visual/funcional con el sistema de César. |
| US-38 | 105 · costos directos y resultado preliminar | Parcial: fórmula preliminar mensual/por proyecto, gastos y ajustes. Cierre oficial, fechas, impuestos y reclasificaciones requieren aprobación contable. |
| US-39 | 119 · continuidad del asistente CRM | Parcial: el hilo se conserva mientras la sesión está activa. Persistencia tras recarga exige decisión de privacidad/retención. |
| US-40 | 128 · verificación Chrome del acceso protegido | Parcial: login PWA verificado en rutas raíz y explícita. Faltan usuarios y teléfonos reales para probar operación autenticada. |
| US-41 | 114 · consentimiento y contacto del agente público | Parcial: agente de solo lectura y flujo de contacto con consentimiento. Faltan catálogo/precios aprobados y validación comercial de punta a punta. |
| US-42 | 129 · búsqueda y vínculos visibles en history cards | Registro append-only y búsqueda CRM implementados. Falta cotejo humano de reconstrucciones/transcripciones y política de fuentes sensibles. |

## Dependencias para continuar

- **ArcoEnergy / administración:** cuentas reales y datos de operación; catálogo, equipos y precios aprobados; conexión y política de Drive; confirmación de formato de proyecto, unidades y procesos de almacén.
- **Contabilidad:** reglas de Plan 24, distribución/mora/cancelaciones, valuación de inventario y cierre financiero.
- **Legal / dirección:** plantillas, consentimiento, resguardo de identificaciones y proveedor de firma/verificación facial.
- **Stakeholders:** validar tarjetas reconstruidas y ASR; dar acceso de lectura al sistema legado de César.
- **Equipo de campo:** probar PWA, push, lectura de etiquetas y sincronización offline en dispositivos reales.

La revisión técnica local del 2026-11-12 ejecutó 304 pruebas backend, compiló CRM, PWA y sitio público y pasó las 4 pruebas del CRM. Esa evidencia no sustituye validación de negocio, dispositivos reales ni verificación del entorno DEV en vivo.
