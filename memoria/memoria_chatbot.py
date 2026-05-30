from conexion.base_datos import guardar_memoria_chatbot, obtener_memoria_chatbot


def guardar_mensaje_usuario(id_usuario, mensaje):
    if id_usuario and mensaje:
        guardar_memoria_chatbot(id_usuario, "user", mensaje)


def guardar_respuesta_bot(id_usuario, respuesta):
    if id_usuario and respuesta:
        guardar_memoria_chatbot(id_usuario, "assistant", respuesta)


def construir_historial_chatbot(id_usuario, limite=10):
    if not id_usuario:
        return ""

    historial = obtener_memoria_chatbot(id_usuario, limite)

    texto_historial = ""

    for item in historial:
        rol = item["rol"]
        mensaje = item["mensaje"]

        if rol == "user":
            texto_historial += f"Estudiante: {mensaje}\n"
        else:
            texto_historial += f"SEA: {mensaje}\n"

    return texto_historial