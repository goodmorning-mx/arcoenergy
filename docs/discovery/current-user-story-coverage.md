# Cobertura vigente de las user story cards

Fecha de corte: 2026-11-13. Esta matriz resume el último registro encontrado por tarjeta en [history-cards.md](history-cards.md). El registro es append-only: cada fila apunta al último estado/evidencia registrado, no modifica el relato original ni implica validación del stakeholder. “Funcional básico” significa que hay código y evidencia técnica para el alcance descrito; las verificaciones de negocio/dispositivo se indican aparte.

| Tarjeta | Última iteración registrada | Estado registrado y trabajo que falta |
| --- | --- | --- |
| US-1 | 127 · despliegue DEV del cotizador PWA | Parcial. Falta recorrido autenticado con usuarios comerciales y catálogo aprobado. |
| US-2 | 2 · producto autenticado y operación de campo | Pendiente/diferida: análisis automático del recibo de luz, fórmula y aprobación. El cliente indicó que es fase avanzada posterior. |
| US-3 | 148 · verificación del agente CRM en DEV | Parcial. DEV responde con schema 202611130150 y API/PWA/CRM están arriba; Drive sigue sin ID de carpeta ni credencial de cuenta de servicio. Falta configurar y probar carga, lectura y compartición. |
| US-4 | 148 · verificación del agente CRM en DEV | Funcional básico: presets, fecha libre, responsable, comentarios y bitácora. El agente CRM también programa seguimientos con vista previa, confirmación explícita, permiso vigente e idempotencia. Falta validar avisos con vendedores/dispositivos reales y definir operaciones agenticas adicionales. |
| US-5 | 103 · dashboard y dependencias legales | Bloqueada por plantillas contractuales aprobadas y política de privacidad/consentimiento para INE. |
| US-6 | 103 · dashboard y dependencias legales | Bloqueada por decisión legal, consentimiento, proveedor de firma/verificación y excepción en papel. |
| US-7 | 82 · compatibilidad de instalación limpia para Web Push | Parcial: asignación y push implementados; falta validar recepción en dispositivos reales. |
| US-8 | 111 · disponibilidad por orden para instaladores | Funcional básico: faltantes por orden/reservas y permisos probados. Falta validación con almacén y teléfonos reales. |
| US-9 | 142 · reintento de operación de campo tras renovar sesión | Funcional básico: una respuesta 401 fuerza refresh y un reintento idempotente; si no se recupera, la PWA conserva la acción en IndexedDB. Chrome CI cubre el flujo con API simulada. Falta validar sesiones reales y teléfonos de campo. |
| US-10 | 148 · verificación del agente CRM en DEV | Parcial: captura/cola offline está desplegada; DEV confirma schema 202611130150, pero no tiene ID de carpeta ni credencial de Drive. Falta probar archivo real y aprobar la política de comprobantes. |
| US-11 | 81 · calendario de cobranza y caja | Parcial: agenda y textos para pago próximo/hoy/vencido. Falta confirmar planes, intereses y zona horaria de negocio. |
| US-12 | 105 · costos directos y resultado preliminar | Funcional básico: costo por consumos/devoluciones y faltantes de costo visibles. Falta aprobación contable de valuación y ajustes. |
| US-13 | 148 · verificación del agente CRM en DEV | Parcial: API responde con schema 202611130150; DEV no tiene ID de carpeta ni credencial de Drive. Falta configurar y probar respaldo, retención y restauración reales. |
| US-14 | 147 · cuentas, roles y permisos vigentes | Funcional en DEV para persistencia de sesión, las tres cuentas solicitadas y consulta de permiso actual antes de confirmar una acción del agente. Refresh rolling de 36,500 días; logout/password reset/desactivación revocan. Faltan cuentas reales de instalador/cliente y validación de aislamiento por entidad/campo. |
| US-15 | 136 · desglose fiscal y condiciones de venta | Parcial. El paquete calcula componentes y total, pero no guarda subtotal fiscal/impuestos; la venta admite contado/crédito y bloquea Plan 24. Contabilidad debe definir tratamiento y tasa fiscal, pagos mixtos, fecha de proyecto y efectos asociados antes de cerrar la historia. |
| US-16 | 101 · cobranza de clientes y flujo de efectivo | Funcional básico: pagos parciales/completos, caja y reversas. Falta definir distribución entre deudas, mora y cancelaciones. |
| US-17 | 100 · cobertura del registro de gastos | Funcional básico: gastos por fecha, cuenta y proyecto, incluida captura móvil. Falta política contable de casos mixtos, recurrencia y aprobación. |
| US-18 | 99 · consulta de caja y bancos | Funcional básico: cuentas, saldos y reportes protegidos por permiso. Administración debe cargar saldos reales; no incluye conciliación bancaria. |
| US-19 | 103 · dashboard y dependencias legales | Funcional básico: indicadores/gráficas operativas. Falta que administración/contador confirme fórmulas, umbrales y prioridades. |
| US-20 | 112 · auditoría funcional de inventario | Funcional básico: catálogo, atributos, QR impreso y lectura móvil. Falta validar unidades y etiquetas físicas con almacén. |
| US-21 | 90 · fidelidad de la fuente original de US-21 | Fuente corregida en versión 2. Falta acordar reconocimiento documental y vinculación contable de devoluciones. |
| US-22 | 122 · captura asistida de CFDI XML para compras | Parcial: CFDI XML 3.3/4.0 validado y revisable. Faltan facturas reales y reglas contables de impuestos, fletes y descuentos. |
| US-23 | 19 · devolución reutilizable y merma de obra | Funcional básico: retorno reutilizable repone stock; merma dañada conserva costo sin reingreso. Falta política de inspección/reparación. |
| US-24 | 112 · auditoría funcional de inventario | Funcional básico: solicitud, reserva/salida, consumo y devolución diferenciados. Falta autorizar variaciones y validar el proceso físico. |
| US-25 | 133 · cotejo de OCR con orden manuscrita real | Parcial: la prueba aislada no leyó confiablemente cantidades/filas; sigue siendo revisión manual y no muta inventario. Hace falta OCR manuscrito aprobado o captura humana. |
| US-26 | 112 · auditoría funcional de inventario | Funcional básico: mínimos, responsable y Web Push implementados. Falta recepción en los equipos reales. |
| US-27 | 112 · auditoría funcional de inventario | Funcional básico: kardex con filtros, paginación y CSV; costos protegidos. Falta validar volúmenes y movimientos históricos sin costo. |
| US-28 | 134 · verificación de shell PWA y API offline | Parcial: login y bundle PWA cargan offline en Chrome; falta escáner con instalador autenticado, flujo completo y etiquetas/teléfonos reales. |
| US-29 | 96 · cobertura de reportes operativos | Funcional básico: agregados, fechas, paginación y permisos probados. La validación contable corresponde a US-12/US-38. |
| US-30 | 102 · directorio y saldos de proveedores | Funcional básico: directorio y relación con compras/pagos. Falta confirmar campos y política para proveedores inactivos. |
| US-31 | 104 · compras, saldos y pagos a proveedores | Funcional básico: compras contado/crédito, pagos parciales y reversas probados. La conciliación requiere reglas contables. |
| US-32 | 68 · entidad de proyecto con folio único | Parcial: entidad/código de proyecto agrupa órdenes y gastos. Falta confirmar formato del folio y cardinalidad operativa. |
| US-33 | 115 · ubicaciones literales de fuentes de audio y WhatsApp | Procedencia ASR trazable; la transcripción sigue sin validar por su autor. |
| US-34 | 115 · ubicaciones literales de fuentes de audio y WhatsApp | Procedencia ASR trazable; falta validar transcripción, integridad del clip y atribución del remitente. |
| US-35 | 115 · ubicaciones literales de fuentes de audio y WhatsApp | Extractos literales ligados a mensajes/horas; requieren cotejo de stakeholder para confirmar interpretación. |
| US-36 | 135 · explicación visible de conciliación en el kardex | Parcial: la UI muestra por qué no se permite revertir una entrada con movimientos posteriores o existencia insuficiente. Falta implementar conciliación según la valuación contable aprobada y probar ciclos reales. |
| US-37 | 116 · cotejo del menú público Base44 | Parcial: menú público y rutas cotejados. Falta comparación autenticada visual/funcional con el sistema de César. |
| US-38 | 137 · cobertura de devoluciones y bonificaciones | Parcial. El resultado por mes/proyecto suma ajustes de devoluciones y bonificaciones registrados, con reversa y bitácora; backend y CRM lo presentan como preliminar. Faltan validar fechas de corte, tratamiento fiscal/contable, reclasificaciones y cierre formal. |
| US-39 | 148 · verificación del agente CRM en DEV | Parcial: `gm-agent` presenta vistas previas con detalles y permite confirmar seguimientos; el hilo se conserva mientras la sesión está activa. Persistencia tras recarga exige decisión de privacidad/retención. |
| US-40 | 143 · sesión renovable sin vencimiento por inactividad | Funcional en DEV: PWA renueva sesión y reintenta una acción de campo tras 401 con el mismo identificador; fallos conservan la cola local. CI usa identidad simulada. Faltan cuentas reales de instalador/cliente y validación en teléfonos físicos. |
| US-41 | 114 · consentimiento y contacto del agente público | Parcial: agente de solo lectura y flujo de contacto con consentimiento. Faltan catálogo/precios aprobados y validación comercial de punta a punta. |
| US-42 | 148 · verificación del agente CRM en DEV | PostgreSQL DEV registra 43 tarjetas y 351 versiones append-only en schema 150; cero relatos fuente vacíos. US-43 está en v3 y US-42 en v8. Falta cotejo humano de reconstrucciones/transcripciones y política de retención de fuentes sensibles. |
| US-43 | 148 · verificación del agente CRM en DEV | Funcional en DEV: el CRM agenda seguimientos con vista previa, confirmación explícita, autorización vigente e idempotencia; API, PWA y CRM reportan el commit `63f7c0c77c369aa2202640456c80bf445136ca50` y schema 150. CI valida Docker, OCR, render, sesiones y login offline. Faltan priorizar las demás operaciones y decidir el alcance de datos procesados por el modelo. |

## Dependencias para continuar

- **ArcoEnergy / administración:** cuentas reales y datos de operación; catálogo, equipos y precios aprobados; conexión y política de Drive; confirmación de formato de proyecto, unidades y procesos de almacén.
- **Contabilidad:** reglas de Plan 24, distribución/mora/cancelaciones, valuación de inventario y cierre financiero.
- **Legal / dirección:** plantillas, consentimiento, resguardo de identificaciones y proveedor de firma/verificación facial.
- **Stakeholders:** validar tarjetas reconstruidas y ASR; dar acceso de lectura al sistema legado de César.
- **Equipo de campo:** probar PWA, push, lectura de etiquetas y sincronización offline en dispositivos reales.

La revisión local de la Iteración 148 pasó 320 pruebas backend, compiló CRM y verificó la migración en Docker con base limpia. En DEV se verificaron API `/health` y `/version`, PWA y CRM; las tres superficies reportan el commit `63f7c0c77c369aa2202640456c80bf445136ca50` y API schema 150. PostgreSQL confirma 43 tarjetas, 351 versiones y cero relatos fuente vacíos. CI validó OCR, render de PWA/CRM, sesiones persistentes y login PWA offline. Esta evidencia no sustituye validación de negocio ni en dispositivos físicos.
