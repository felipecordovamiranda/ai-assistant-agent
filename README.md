# AI Assistant Agent

Asistente de IA conversacional para una empresa de climatización (mantención de Chillers y Fan Coils), pensado para automatizar el ciclo de vida completo de una solicitud de servicio — desde la recepción hasta la facturación — sin dejar de ser una herramienta que un equipo pequeño pueda operar por chat.

## Sobre este repositorio

Este repo es un **extracto representativo** del proyecto real (en producción, uso interno), no el código de negocio completo. La carpeta [`examples/`](examples/) tiene 3 archivos que muestran los patrones de diseño reales — reescritos con nombres genéricos, sin la lógica de negocio específica de ninguna empresa — pensados para leerse de forma aislada:

- [`conversational_agent.py`](examples/conversational_agent.py) — agente con tool-calling y cadena de proveedores de LLM con fallback automático.
- [`channel_access_control.py`](examples/channel_access_control.py) — control de acceso por canal + rol, aplicado como límite real de qué herramientas recibe el modelo (no solo una restricción de interfaz).
- [`service_request_lifecycle.py`](examples/service_request_lifecycle.py) — el ciclo de vida de una solicitud de servicio como máquina de estados explícita, con reglas de negocio propias de cada transición.

## Qué hace el sistema real

- **Agente conversacional con herramientas** (LLM + tool calling): responde consultas de negocio y ejecuta acciones reales (crear solicitudes, registrar cotizaciones, agendar visitas, registrar trabajos ejecutados) en lenguaje natural, sin menús rígidos.
- **Multicanal, con roles distintos por canal:**
  - **Telegram** — canal principal, acceso completo (consultas + escritura), con un sistema de aprobación de usuarios y 4 roles (administrador, gerencia, técnico, cliente).
  - **WhatsApp** — canal de consultas de solo lectura y alertas, vía la Cloud API oficial de Meta (webhook + roles por número), sin ingesta de datos.
- **Multimodal**: transcribe notas de voz, describe imágenes y video para registrar levantamientos a partir de fotos de hojas de servicio en terreno.
- **Modelo de negocio como máquina de estados real**: cada solicitud (preventiva o correctiva) recorre un ciclo de vida explícito con reglas y transiciones válidas (levantamiento → cotización → aprobación → orden de compra → ejecución → facturación), no solo una lista de tareas.
- **Generación de documentos reales**: cotizaciones y BOM se arman a partir de plantillas Word/Excel reales de la empresa, preservando formato exacto.
- **Automatización de correo**: monitorea un buzón de ventas, clasifica correos entrantes con un modelo liviano y responde automáticamente cuando corresponde.
- **Recordatorios y alertas proactivas**: resumen diario de pendientes (cotizaciones estancadas, levantamientos atrasados, trabajos por agendar) entregado por chat.

## Arquitectura

```
Telegram / WhatsApp
        │
        ▼
Agente LLM (Groq / Gemini, protocolo compatible OpenAI, con fallback entre proveedores)
        │
        ▼
Capa de servicios (Python) ── reglas de negocio, máquina de estados
        │
        ▼
FastAPI + SQLAlchemy + SQLite
```

- El bot de Telegram funciona por *polling*, sin necesitar un servidor público.
- El webhook de WhatsApp corre dentro de la misma API (FastAPI), expuesto vía túnel.
- Cadena de modelos con fallback automático entre proveedores para no depender de una sola cuota de uso.

## Stack técnico

Python · FastAPI · SQLAlchemy · `python-telegram-bot` · APIs de LLM compatibles con OpenAI (Groq, Gemini) · WhatsApp Cloud API · `python-docx` / `openpyxl` para generación de documentos.

## Estado

El sistema real está en desarrollo activo, en uso real dentro de la operación diaria de la empresa (no es un prototipo de demostración). Pensado desde el inicio con una capa de servicios independiente del canal de entrada, para poder reutilizarse en otras empresas de mantenimiento con un modelo de negocio similar.
