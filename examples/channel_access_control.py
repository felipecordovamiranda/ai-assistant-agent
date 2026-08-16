"""
Patrón: mismo agente, distinto nivel de acceso según el ROL de quien
pregunta y el CANAL por el que llega el mensaje.

Extracto representativo (renombrado y simplificado) - en el sistema real
esto resuelve un problema concreto: el mismo asistente atiende por dos
canales de mensajería distintos. Uno de ellos (interno, de confianza)
puede crear y modificar datos; el otro (más expuesto, pensado para
consultas rápidas) solo puede leer, sin importar el rol de quien
pregunte. Los roles a su vez acotan qué puede ver cada persona dentro de
lo permitido por el canal.

La restricción de canal se aplica SIEMPRE primero y sin excepción -
ningún rol, ni siquiera "administrador", puede saltársela. Es un límite
de seguridad real (qué herramientas recibe el modelo), no una sugerencia
de interfaz - si la herramienta no está en la lista, el modelo
físicamente no puede llamarla.
"""

from typing import Optional

HERRAMIENTAS_LECTURA = {
    "buscar_solicitudes_por_cliente",
    "consultar_estado_solicitud",
    "proxima_visita_agendada",
}
HERRAMIENTAS_ESCRITURA = {
    "crear_solicitud",
    "agendar_visita",
    "registrar_trabajo_completado",
}
TODAS_LAS_HERRAMIENTAS = HERRAMIENTAS_LECTURA | HERRAMIENTAS_ESCRITURA

# Rol más restringido: ve un subconjunto aún más chico que "solo lectura".
HERRAMIENTAS_ROL_CLIENTE = {"consultar_estado_solicitud", "proxima_visita_agendada"}


def filtrar_herramientas_disponibles(
    nombres_herramientas: set[str],
    rol: Optional[str],
    canal: str = "canal_interno",
) -> set[str]:
    """Devuelve el subconjunto de `nombres_herramientas` que puede usar
    esta combinación de rol + canal.

    1. El canal se aplica primero: "canal_consultas" (ej. un canal
       público/de bajo control) recorta SIEMPRE a solo lectura, sin
       importar el rol - decisión de negocio explícita, no técnica.
    2. Dentro de lo que deja pasar el canal, el rol puede recortar más:
       "cliente" es el más restringido (ni siquiera ve todo lo de
       lectura), los demás roles ven todo lo que el canal permite.
    """

    disponibles = set(nombres_herramientas)

    if canal == "canal_consultas":
        disponibles &= HERRAMIENTAS_LECTURA

    if rol == "cliente":
        disponibles &= HERRAMIENTAS_ROL_CLIENTE

    return disponibles


def tiene_acceso_a_datos_sensibles(rol: Optional[str]) -> bool:
    """Ejemplo de una regla de acceso más estricta que la general: solo
    ciertos roles pueden ver información financiera agregada, sin
    importar que ya hayan pasado el filtro de herramientas normal. Se
    separa de `filtrar_herramientas_disponibles` porque es una excepción
    puntual (una sola herramienta), no un patrón que valga la pena
    generalizar a todo el sistema de roles."""

    return rol is None or rol in ("administrador", "gerencia")


if __name__ == "__main__":
    # Ejemplo: alguien con rol "tecnico" preguntando por el canal de consultas
    # (el más restringido de los dos filtros) queda limitado a lo mínimo.
    resultado = filtrar_herramientas_disponibles(TODAS_LAS_HERRAMIENTAS, rol="tecnico", canal="canal_consultas")
    print(resultado)  # {'consultar_estado_solicitud', 'proxima_visita_agendada', ...} - nunca escritura
