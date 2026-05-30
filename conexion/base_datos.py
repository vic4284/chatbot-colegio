import os
import mysql.connector


def obtener_conexion():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "69.6.201.83"),
        database=os.getenv("DB_NAME", "alanvice_cole"),
        user=os.getenv("DB_USER", "alanvice_42"),
        password=os.getenv("DB_PASSWORD", "JQZ33daO7gyO"),
        port=int(os.getenv("DB_PORT", 3306))
    )


def obtener_id_estudiante(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT id_estudiante
        FROM estudiantes
        WHERE id_usuario = %s
        LIMIT 1
    """

    cursor.execute(sql, (id_usuario,))
    resultado = cursor.fetchone()

    cursor.close()
    conexion.close()

    if resultado:
        return resultado["id_estudiante"]

    return None


def obtener_id_emocion(nombre_emocion):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT id_emocion
        FROM emociones
        WHERE nombre_emocion = %s
        LIMIT 1
    """

    cursor.execute(sql, (nombre_emocion,))
    resultado = cursor.fetchone()

    cursor.close()
    conexion.close()

    if resultado:
        return resultado["id_emocion"]

    return None


def obtener_id_nivel_alerta(nombre_nivel):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT id_nivel_alerta
        FROM niveles_alerta
        WHERE nombre_nivel = %s
        LIMIT 1
    """

    cursor.execute(sql, (nombre_nivel,))
    resultado = cursor.fetchone()

    cursor.close()
    conexion.close()

    if resultado:
        return resultado["id_nivel_alerta"]

    return None


def guardar_analisis_emocional(
    id_usuario,
    emocion,
    intencion,
    nivel_emocional,
    puntaje_confianza,
    recomendacion
):
    id_estudiante = obtener_id_estudiante(id_usuario)

    if not id_estudiante:
        return False, "No se encontró estudiante asociado al id_usuario"

    id_emocion = obtener_id_emocion(emocion)
    id_nivel_alerta = obtener_id_nivel_alerta(nivel_emocional)

    if not id_emocion:
        return False, "No se encontró la emoción en la tabla emociones"

    if not id_nivel_alerta:
        return False, "No se encontró el nivel en la tabla niveles_alerta"

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO analisis_emociones (
            id_estudiante,
            id_emocion,
            id_nivel_alerta,
            intencion_detectada,
            nivel_emocional,
            puntaje_confianza,
            recomendacion,
            estado_seguimiento,
            fecha_analisis
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDIENTE', NOW())
    """

    valores = (
        id_estudiante,
        id_emocion,
        id_nivel_alerta,
        intencion,
        nivel_emocional,
        puntaje_confianza,
        recomendacion
    )

    cursor.execute(sql, valores)
    conexion.commit()

    cursor.close()
    conexion.close()

    return True, "Análisis emocional guardado correctamente"


def guardar_memoria_chatbot(id_usuario, rol, mensaje):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO memoria_chatbot (
            id_usuario,
            rol,
            mensaje,
            fecha_registro
        )
        VALUES (%s, %s, %s, NOW())
    """

    cursor.execute(sql, (id_usuario, rol, mensaje))
    conexion.commit()

    cursor.close()
    conexion.close()

    return True


def obtener_memoria_chatbot(id_usuario, limite=10):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """
        SELECT rol, mensaje
        FROM memoria_chatbot
        WHERE id_usuario = %s
        ORDER BY fecha_registro DESC
        LIMIT %s
    """

    cursor.execute(sql, (id_usuario, limite))
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    resultados.reverse()

    return resultados