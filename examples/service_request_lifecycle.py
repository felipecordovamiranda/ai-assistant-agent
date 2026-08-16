"""
Patrón: el ciclo de vida de una solicitud de servicio modelado como
máquina de estados explícita, con transiciones válidas y reglas de
negocio propias de cada paso - no una simple lista de "tareas".

Extracto representativo (renombrado y simplificado). La entidad central
de un sistema de gestión de servicios en terreno no es la agenda/
calendario (esa es solo una vista derivada) - es la Solicitud, cuyo
identificador conecta todo lo que pasa después: diagnóstico, cotización,
aprobación, ejecución y facturación.

Este patrón importa porque evita el bug más común en este tipo de
sistemas: dejar que cualquier función cambie el estado libremente sin
validar que la transición tenga sentido (ej. facturar algo que nunca se
ejecutó, o saltarse la cotización de un trabajo que sí la necesita).
"""

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class EstadoSolicitud(str, enum.Enum):
    recibida = "recibida"
    diagnostico_realizado = "diagnostico_realizado"
    cotizacion_enviada = "cotizacion_enviada"
    aprobada = "aprobada"
    programada = "programada"
    ejecutada = "ejecutada"
    facturada = "facturada"


class TransicionInvalidaError(Exception):
    """Se lanza cuando el código intenta mover una solicitud a un estado
    que no es alcanzable desde su estado actual - preferible a dejar que
    el dato quede en un estado inconsistente sin que nadie se entere."""


_TRANSICIONES_VALIDAS: dict[EstadoSolicitud, set[EstadoSolicitud]] = {
    EstadoSolicitud.recibida: {EstadoSolicitud.diagnostico_realizado},
    EstadoSolicitud.diagnostico_realizado: {EstadoSolicitud.cotizacion_enviada, EstadoSolicitud.aprobada},
    EstadoSolicitud.cotizacion_enviada: {EstadoSolicitud.aprobada},
    EstadoSolicitud.aprobada: {EstadoSolicitud.programada},
    EstadoSolicitud.programada: {EstadoSolicitud.ejecutada},
    EstadoSolicitud.ejecutada: {EstadoSolicitud.facturada},
    EstadoSolicitud.facturada: set(),
}


@dataclass
class Solicitud:
    id: int
    tipo: str  # "correctiva" | "preventiva"
    estado: EstadoSolicitud = EstadoSolicitud.recibida
    cliente_ya_tiene_precio_acordado: bool = False
    orden_de_compra_recibida: bool = False
    validacion_directa_cliente: Optional[str] = None
    historial_cambios: list[tuple[EstadoSolicitud, datetime]] = field(default_factory=list)


def cambiar_estado(solicitud: Solicitud, nuevo_estado: EstadoSolicitud) -> None:
    """Aplica la transición si es válida, o lanza TransicionInvalidaError.
    Registra cada cambio con su fecha - ese historial es lo que permite
    reconstruir cuánto tardó cada etapa, útil para detectar cuellos de
    botella reales en el proceso (ej. "las cotizaciones tardan en promedio
    X días en aprobarse")."""

    if nuevo_estado not in _TRANSICIONES_VALIDAS[solicitud.estado]:
        raise TransicionInvalidaError(
            f"No se puede pasar de '{solicitud.estado.value}' a '{nuevo_estado.value}' directamente."
        )
    solicitud.estado = nuevo_estado
    solicitud.historial_cambios.append((nuevo_estado, datetime.now()))


def aprobar_sin_cotizacion_nueva(solicitud: Solicitud) -> None:
    """Regla de negocio real y no obvia: un cliente YA establecido, con
    un precio ya acordado en un ciclo anterior, no necesita pasar de
    nuevo por 'cotización enviada' - salta directo de 'diagnóstico' a
    'aprobada'. Esto NUNCA aplica a trabajo correctivo (cada diagnóstico
    correctivo es distinto, siempre necesita su propia cotización) - la
    función lo valida explícitamente en vez de confiar en que quien la
    llama se acuerde de la regla."""

    if solicitud.tipo == "correctiva":
        raise ValueError("Un trabajo correctivo siempre necesita su propia cotización.")
    if not solicitud.cliente_ya_tiene_precio_acordado:
        raise ValueError("Este cliente no tiene un precio ya acordado - debe pasar por cotización normal.")

    cambiar_estado(solicitud, EstadoSolicitud.aprobada)


def puede_facturarse(solicitud: Solicitud) -> bool:
    """Un trabajo correctivo puede facturarse por dos vías distintas
    (Orden de Compra recibida, O validación directa del cliente sobre el
    trabajo ya hecho) - no es una sola condición fija. Separar esta
    pregunta en su propia función evita repetir la misma lógica de
    negocio en cada lugar del sistema que necesita saber "¿puedo
    facturar esto?"."""

    if solicitud.estado != EstadoSolicitud.ejecutada:
        return False
    if solicitud.tipo == "preventiva":
        return True
    return solicitud.orden_de_compra_recibida or solicitud.validacion_directa_cliente is not None
