# Arco Energy — Iteración de descubrimiento: portales, diseño y agente

- **Fecha:** 6 de noviembre de 2026
- **Tipo:** Iteración de descubrimiento y propuesta de diseño
- **Estado:** Plan inicial documentado; todavía no es especificación aprobada para implementación
- **Stakeholders citados en esta iteración:** Josué (solicitante del sistema), Mario Groso (contador) y Goito Profugo (requerimientos operativos previos)
- **Contexto:** Continuación de las history cards recopiladas en conversación y de los documentos del contador. Mantener la procedencia y evolución de las tarjetas; no sustituir retrospectivas previas.

## Objetivo de esta iteración

Organizar lo aprendido en una propuesta de producto para Arco Energy: qué va en el CRM, qué va en la PWA, qué va en la web pública, cómo encaja el agente y qué módulos `gm-*` pueden reutilizarse. Esta propuesta servirá como contexto para un goal futuro; no implica que los portales o integraciones ya estén implementados.

## Decisiones y dirección acordadas

1. El producto se organiza en tres portales independientes:
   - **CRM web administrativo:** panel de administración para computadora.
   - **PWA operativa:** interfaz móvil para empleados y personal de campo.
   - **Web pública:** presencia comercial y entrada al cotizador conversacional de IA, con SEO/GEO.
2. Cada portal tendrá navegación e interacción nativas para su contexto. Compartirán identidad visual, servicios y reglas de negocio; no serán una misma vista redimensionada.
3. La dirección visual será Material UI/UX, con identidad propia de Arco Energy. Se usarán cards/widgets para resúmenes y métricas; tablas para listas operativas densas; formularios por pasos para operaciones largas.
4. El producto será agéntico. Se propone un chat contextual a la derecha en el CRM, contraíble, y una experiencia de asistente móvil en la PWA. Las operaciones de escritura deben mostrar una vista previa/resumen y requerir confirmación, respetando permisos y dejando auditoría.
5. Las history cards actuales constituyen el registro de descubrimiento de esta iteración. Nuevos mensajes y validaciones se guardarán como nuevas iteraciones relacionadas, sin borrar el origen ni las versiones anteriores.
6. La lógica contable y las reglas todavía no confirmadas se validarán con Mario/Josué antes de automatizarlas.

## Distribución funcional propuesta

### CRM web administrativo

- **Inicio/reportes:** efectivo y movimientos del día, cobranza/cuentas por cobrar, inventario valorizado, gastos, ventas y resultados disponibles.
- **Ventas/cotizaciones:** cotizador manual de paquetes, selección de paneles/inversores, opciones de pago, PDF y conversión a proyecto. El cálculo automático a partir de recibo PDF queda para una etapa avanzada.
- **Clientes/seguimiento:** ficha, actividad/bitácora, historial de cotizaciones y proyectos, próximos seguimientos y mensajes preparados.
- **Proyectos/órdenes:** datos del proyecto, folio, orden de trabajo, asignación de instaladores, solicitud de materiales, consumos, gastos y evidencias.
- **Almacén:** catálogo, entradas, salidas, solicitudes, entregas, consumo, devoluciones, daños/mermas y kardex por artículo/proyecto.
- **Caja/bancos/cobranza:** cuentas, ingresos/egresos, cobros de contado y abonos a crédito, cartera y trazabilidad.
- **Compras/proveedores:** compras relacionadas a entradas de almacén, cuentas por pagar y corrección trazable de movimientos.
- **Gastos/costos:** gastos fijos/variables, viáticos, comprobantes y costeo por proyecto/periodo.
- **Documentos:** cotizaciones, contratos, pagarés, identificaciones, comprobantes, órdenes y evidencias, con referencias a Drive.
- **Administración:** usuarios, permisos, catálogos, folios, formatos, integraciones y auditoría.

Las cards/widgets se reservan principalmente para indicadores, alertas y resumen. Tablas y vistas detalladas serán la herramienta principal para buscar, comparar, filtrar y corregir registros.

### PWA operativa

- Inicio personal con trabajos, tareas y notificaciones según rol.
- Para instaladores: instalaciones asignadas, orden de trabajo, ubicación/contacto necesarios, consulta de materiales, registro de consumo/devolución/daño, gastos de campo y evidencia fotográfica.
- Formularios breves, controles táctiles grandes, cámara accesible y estado de sincronización visible.
- El comportamiento sin conexión está por diseñar. Se podrán evaluar borradores locales, pero no confirmar como definitivos movimientos de inventario/finanzas hasta sincronización segura.
- La PWA será móvil primero y no duplicará el panel administrativo completo.

### Web pública y cotizador IA

- Páginas comerciales de Arco Energy, soluciones, proceso, preguntas frecuentes, contacto, privacidad y llamadas a cotizar.
- SEO/GEO, contenido indexable, metadatos, estructura semántica y rendimiento móvil.
- Cotizador conversacional para capturar necesidad y datos del prospecto, confirmar el resumen y transferirlo al equipo/CRM.
- La IA debe consultar catálogo y reglas aprobadas; no inventar precios ni promesas técnicas.
- Propuesta inicial: IA prepara la solicitud y un vendedor genera la propuesta formal con el cotizador manual; recibo PDF y cálculo automático quedan para fase avanzada.

## Roles iniciales y orientación de permisos

Roles nombrados en el proyecto: **administrador, contador, marketing, instalador y cliente**.

| Rol | Orientación inicial — por validar |
|---|---|
| Administrador | Gestión y acceso global autorizado, configuración y asignaciones |
| Contador | Caja/bancos, cobranza, compras/proveedores, gastos, inventario y reportes contables |
| Marketing | Prospectos, clientes, cotizaciones y seguimiento; acceso financiero restringido |
| Instalador | Sus órdenes, materiales necesarios, gastos y evidencias |
| Cliente | Sin portal confirmado aún; definir si consultará cotizaciones, pagos, documentos o avance |

La autorización debe aplicarse en backend/API además de la interfaz. La matriz detallada de capacidades y restricciones no está aprobada todavía.

## Módulos GoodMorning revisados

Revisión preliminar de documentación, manifiestos y contratos locales disponibles en el entorno. Antes de implementar, confirmar versiones compatibles con el repositorio/factory de Arco Energy.

| Módulo | Contrato observado | Uso posible en Arco Energy |
|---|---|---|
| `gm-agent` | Full-stack; proveedor OpenAI, conversación, tool-calling, contexto, gates de confirmación y captura vía `gm-billing`; frontend `AgentChat`/`AgentLauncher` sin estilos de producto | Lógica y chat embebido en CRM/PWA; Arco aporta adaptadores y herramientas de negocio |
| `gm-mcp` | Registro de herramientas/adaptadores, contexto confiable usuario/organización/producto, permisos de lectura/escritura, gateway Streamable HTTP y confirmaciones/intenciones | Exponer operaciones del producto al agente. Camino previsto: herramienta MCP → servicio Arco Energy → PostgreSQL; MCP no consulta directamente la BD del producto |
| `gm-auth` | Usuarios, organizaciones, membresías, roles, permisos, sesiones, recuperación y auditoría; componentes React de auth | Identidad, guardas UI y dependencias de permisos en endpoints/adaptadores MCP |
| `gm-pwa` | Prompt de instalación, instrucciones iOS, online/offline, registro de service worker, aviso de actualización y activación iniciada por usuario | Runtime común para PWA; el producto configura manifest y service worker. API/auth debe permanecer network-only |
| `gm-billing` | Medición/ledger de uso de IA por organización/usuario/proveedor/modelo | Seguimiento del costo/uso del agente; no es contabilidad del negocio Arco Energy |
| `gm-payments` | Stripe Checkout, estado de pago, reembolsos y webhook idempotente | Solo si se confirma que el cliente pagará en línea; no sustituye caja, bancos o cobranza interna |

Referencias de código disponibles localmente en `/home/goodmorning/gm-agent`, `/home/goodmorning/gm-mcp`, `/home/goodmorning/gm-auth`, `/home/goodmorning/gm-pwa`, `/home/goodmorning/src/gm-billing` y `/home/goodmorning/src/gm-payments`.

## Modelo de relación de negocio propuesto

```text
Prospecto → Cliente → Cotización → Venta/Proyecto
                                  ├── Orden de trabajo
                                  │    ├── Solicitud/entrega de materiales
                                  │    ├── Consumo/devolución/daño
                                  │    ├── Instaladores/evidencias
                                  │    └── Gastos del proyecto
                                  ├── Cobros → Caja o banco
                                  └── Documentos

Compra → Proveedor → Entrada a almacén
                   └→ Pago → Caja o banco

Operación → movimientos relacionados → historial/auditoría
```

Las operaciones relacionadas deben conservar referencias, efectos y trazabilidad. No se debe inferir todavía el momento de descuento de inventario ni el tratamiento de impuestos, costos de venta, pagos parciales, daños o devoluciones sin validación del stakeholder.

## Iteraciones de construcción sugeridas para el goal futuro

0. **Línea base y recorrido:** revisar cada sección del sistema de César contra el Word de Mario; documentar lo existente, diferencias y dudas; validar matriz de roles.
1. **Clientes/cotización:** prospectos, seguimiento, cotizador manual, PDF y páginas públicas iniciales.
2. **Proyecto/orden/PWA:** conversión a proyecto, orden con folio, asignación y lista móvil de trabajo.
3. **Inventario operativo:** catálogo, solicitud, entrega, consumo, devolución y daño; acordar cuándo se mueve la existencia.
4. **Caja, bancos, ventas, cobranza y proveedores:** modelar cada efecto paralelo con el contador y mantener correcciones auditables.
5. **Gastos y reportes:** control diario y estado de resultados/costeo por proyecto y mes, con fórmulas aprobadas por Mario/Josué.
6. **Documentación y capacidades avanzadas:** contratos, pagarés, firma/verificación, cotización desde recibo PDF y portal cliente si se confirma alcance.

La reutilización del sistema para otros clientes es una dirección futura expresada por Mario; conviene evitar acoplamientos innecesarios, pero no convertir todavía Arco Energy en una plataforma multiempresa genérica sin definir ese alcance.

## Preguntas abiertas para futuras history cards

1. ¿Cuál es el inventario actual del sistema de César por sección y qué debe conservarse o modificarse?
2. ¿En qué momento se descuenta el stock: al solicitar, entregar o registrar el consumo real?
3. ¿Cómo se registran daños, devoluciones, mermas y costos asociados?
4. ¿Qué estados, folios y responsables tiene cada etapa de cotización/proyecto/orden?
5. ¿Qué operaciones financieras pueden hacer cada rol? ¿Quién puede corregir, anular o aprobar?
6. ¿Qué informes necesita Josué exactamente y con qué definición de ingresos, costo de venta, gastos, devoluciones/bonificaciones e impuestos?
7. ¿Qué flujos del cliente final justifican el rol/portal `cliente`?
8. ¿Qué proveedor y alcance se necesita para WhatsApp, Drive, firma electrónica y validación de identidad?
9. ¿Qué datos se almacenan localmente en la PWA y cuáles requieren conexión obligatoria?
10. ¿Qué alcance concreto tiene la futura reutilización del sistema para otros negocios?

## Fuentes y procedencia

- History cards anteriores US-1 a US-34 y retrospectiva de Goito/contador registradas en la conversación del proyecto.
- Nuevas history cards de esta conversación: **US-35** movimientos contables relacionados; **US-36** corregir movimientos sin perder historial; aclaración de orden de trabajo y material; **US-37** revisar sistema por secciones conforme al Word; **US-38** controles diarios y resultados por proyecto/mes.
- Mensajes de Mario Groso del 5 de noviembre de 2026 y foto del formato de Orden de Trabajo/Solicitud de Materiales.
- Documentos previamente compartidos: `COMENTARIOS Y MEJORAS PARA EL SISTEMA DE ARCO ENERGY.docx` y `MEJORAS AL SISTEMA ARCO ENERGY.pdf`.
- Documentación/contratos locales de los módulos `gm-*` listados arriba.

## Alcance de este documento

Este archivo conserva el plan acordado y las propuestas de organización para retomarlas en un goal futuro. No cambia el runtime, no crea todavía pantallas funcionales y no equivale a aprobación de reglas contables, permisos detallados o integraciones externas.
