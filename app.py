from flask import Flask, request, jsonify
import joblib
import pandas as pd
import re
import mysql.connector
import random

app = Flask(__name__)

modelo = joblib.load("modelo_chatbot.pkl")
vectorizador = joblib.load("vectorizador.pkl")
df = pd.read_csv("dataset_limpio.csv")


def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto


def conectar_bd():
    try:
        return mysql.connector.connect(
            host="69.6.201.83",
            user="alanvice_42",
            password="JQZ33daO7gyO",
            database="alanvice_cole",
            port=3306
        )
    except:
        return None


def obtener_id_estudiante(conexion, id_usuario):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_estudiante
        FROM estudiantes
        WHERE id_usuario = %s
        LIMIT 1
    """, (id_usuario,))
    fila = cursor.fetchone()
    cursor.close()
    return int(fila["id_estudiante"]) if fila else 0


def normalizar_nivel(nivel):
    nivel = limpiar_texto(nivel)

    if nivel in ["alto", "alta", "critico", "crítico", "critica", "crítica"]:
        return "ALTA"
    if nivel in ["medio", "media"]:
        return "MEDIA"
    if nivel in ["bajo", "baja"]:
        return "BAJA"

    return "BAJA"


def obtener_emocion_y_nivel(categoria, nivel_csv, fila=None):
    categoria_limpia = limpiar_texto(categoria)
    nivel = normalizar_nivel(nivel_csv)

    if fila is not None and "emocion_detectada" in df.columns:
        emocion_csv = str(fila["emocion_detectada"]).strip().upper()
        if emocion_csv != "" and emocion_csv != "NAN":
            return emocion_csv, nivel

    if "feliz" in categoria_limpia or "positivo" in categoria_limpia:
        return "FELIZ", "BAJA"

    if "ansiedad" in categoria_limpia or "miedo" in categoria_limpia:
        return "ANSIOSO", nivel

    if "estres" in categoria_limpia or "academico" in categoria_limpia or "examen" in categoria_limpia:
        return "ESTRESADO", nivel

    if "triste" in categoria_limpia or "soledad" in categoria_limpia:
        return "TRISTE", nivel

    if "enojo" in categoria_limpia:
        return "ENOJADO", nivel

    if "riesgo" in categoria_limpia or "emergencia" in categoria_limpia or "bullying" in categoria_limpia:
        return "ANSIOSO", "ALTA"

    return "NEUTRAL", nivel


def obtener_id_emocion(conexion, nombre_emocion):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_emocion
        FROM emociones
        WHERE nombre_emocion = %s
        LIMIT 1
    """, (nombre_emocion,))
    fila = cursor.fetchone()

    if fila:
        cursor.close()
        return int(fila["id_emocion"])

    cursor.execute("""
        INSERT INTO emociones (nombre_emocion)
        VALUES (%s)
    """, (nombre_emocion,))
    conexion.commit()

    id_emocion = cursor.lastrowid
    cursor.close()
    return int(id_emocion)


def obtener_id_nivel(conexion, nombre_nivel):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_nivel_alerta
        FROM niveles_alerta
        WHERE nombre_nivel = %s
        LIMIT 1
    """, (nombre_nivel,))
    fila = cursor.fetchone()

    if fila:
        cursor.close()
        return int(fila["id_nivel_alerta"])

    cursor.execute("""
        INSERT INTO niveles_alerta (nombre_nivel)
        VALUES (%s)
    """, (nombre_nivel,))
    conexion.commit()

    id_nivel = cursor.lastrowid
    cursor.close()
    return int(id_nivel)


def registrar_analisis(conexion, id_estudiante, emocion, nivel):
    id_emocion = obtener_id_emocion(conexion, emocion)
    id_nivel = obtener_id_nivel(conexion, nivel)

    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO analisis_emociones
        (id_estudiante, id_emocion, id_nivel_alerta, fecha_analisis)
        VALUES (%s, %s, %s, CONVERT_TZ(UTC_TIMESTAMP(), '+00:00', '-04:00'))
    """, (id_estudiante, id_emocion, id_nivel))

    conexion.commit()
    cursor.close()
    return True


def obtener_memoria(conexion, id_estudiante):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT mensaje_usuario, respuesta_bot, categoria, emocion, nivel_alerta
        FROM memoria_chatbot
        WHERE id_estudiante = %s
        ORDER BY id_memoria DESC
        LIMIT 5
    """, (id_estudiante,))
    filas = cursor.fetchall()
    cursor.close()
    return filas


def guardar_memoria(conexion, id_estudiante, mensaje_usuario, respuesta_bot, categoria, emocion, nivel_alerta):
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO memoria_chatbot
        (id_estudiante, mensaje_usuario, respuesta_bot, categoria, emocion, nivel_alerta, fecha)
        VALUES (%s, %s, %s, %s, %s, %s, CONVERT_TZ(UTC_TIMESTAMP(), '+00:00', '-04:00'))
    """, (
        id_estudiante,
        mensaje_usuario,
        respuesta_bot,
        categoria,
        emocion,
        nivel_alerta
    ))
    conexion.commit()
    cursor.close()


def detectar_respuesta_directa(mensaje):
    texto = limpiar_texto(mensaje)

    riesgo = [
        "me quiero hacer daño", "quiero hacerme daño", "no quiero vivir",
        "quiero desaparecer", "quiero morir", "ya no puedo mas",
        "quisiera no existir", "me voy a lastimar"
    ]

    for palabra in riesgo:
        if palabra in texto:
            return {
                "categoria": "emergencia_riesgo",
                "emocion": "ANSIOSO",
                "nivel": "ALTA",
                "respuesta": "Lo que me estás diciendo es importante y necesita apoyo inmediato.\n\nRecomendación: busca ahora mismo a un adulto de confianza, un familiar, un profesor o el área de psicología. No te quedes solo en este momento.\n\n¿Estás en un lugar seguro ahora?"
            }

    negacion_malestar = [
        "no estoy mal", "estoy bien", "estoy perfectamente bien",
        "no me siento mal", "no estoy triste", "no estoy solo",
        "no tengo problema", "estoy normal"
    ]

    for palabra in negacion_malestar:
        if palabra in texto:
            return {
                "categoria": "estado_positivo",
                "emocion": "FELIZ",
                "nivel": "BAJA",
                "respuesta": "Perfecto, gracias por aclararlo. Entonces dejamos de lado la parte emocional.\n\nRecomendación: dime en qué necesitas ayuda ahora: estudio, tareas, organización, una materia o algún consejo práctico.\n\n¿Sobre qué tema quieres conversar?"
            }

    positivo = [
        "estoy feliz", "me siento feliz", "estoy contento", "estoy contenta",
        "me fue bien", "estoy alegre", "jajaja", "jaja", "xd", "todo bien"
    ]

    for palabra in positivo:
        if palabra in texto:
            return {
                "categoria": "estado_positivo",
                "emocion": "FELIZ",
                "nivel": "BAJA",
                "respuesta": "Me alegra saber eso. También es bueno reconocer cuando algo va bien.\n\nRecomendación: aprovecha ese ánimo para avanzar algo pequeño o disfrutar el momento sin presionarte.\n\n¿Qué pasó para que te sientas así?"
            }

    academico = [
        "dame tips", "tips para aprender", "aprender mejor", "estudiar mejor",
        "como estudio", "cómo estudio", "lengua", "matematica", "matemática",
        "fisica", "física", "quimica", "química", "historia", "biologia",
        "biología", "tarea", "examen", "exponer", "resumen", "lectura",
        "ortografia", "ortografía"
    ]

    for palabra in academico:
        if palabra in texto:
            return {
                "categoria": "apoyo_academico",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": "Claro, puedo ayudarte con eso.\n\nRecomendación: para aprender mejor, divide el tema en partes pequeñas, lee una parte, subraya ideas principales y luego explica con tus propias palabras lo que entendiste. Si es Lengua, practica lectura, resumen, ortografía y redacción con ejemplos cortos.\n\n¿Quieres tips para estudiar, leer mejor, escribir mejor o prepararte para un examen?"
            }

    saludo = ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey"]

    if texto in saludo:
        return {
            "categoria": "saludo",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "Hola, aquí estoy para ayudarte.\n\nPuedes contarme si necesitas apoyo emocional, ayuda con estudios o simplemente conversar un momento.\n\n¿En qué te puedo ayudar hoy?"
        }

    gracias = ["gracias", "muchas gracias", "ok gracias", "te agradezco"]

    if texto in gracias:
        return {
            "categoria": "agradecimiento",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "De nada. Me alegra poder ayudarte.\n\nRecomendación: si algo vuelve a preocuparte, puedes contarlo con calma y buscamos una solución paso a paso.\n\n¿Quieres hablar de algo más?"
        }

    despedida = ["adios", "chau", "hasta luego", "nos vemos", "me voy"]

    if texto in despedida:
        return {
            "categoria": "despedida",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "Está bien. Gracias por conversar conmigo.\n\nRecomendación: si después necesitas apoyo, puedes volver a escribir.\n\nCuídate."
        }

    ambiguo = [
        "me siento mal", "estoy mal", "me siento raro", "me siento rara",
        "no se que me pasa", "no sé que me pasa", "no me siento bien"
    ]

    for palabra in ambiguo:
        if palabra in texto:
            return {
                "categoria": "malestar_ambiguo",
                "emocion": "NEUTRAL",
                "nivel": "MEDIA",
                "respuesta": "Quiero entenderte mejor antes de asumir algo.\n\nRecomendación: intenta identificar qué se parece más a lo que sientes: tristeza, estrés, enojo, miedo, cansancio o preocupación.\n\n¿Qué emoción se acerca más a lo que sientes ahora?"
            }

    return None


def corregir_categoria_con_memoria(mensaje, categoria_predicha, memoria):
    texto = limpiar_texto(mensaje)

    if not memoria:
        return categoria_predicha

    ultima_categoria = str(memoria[0]["categoria"])

    palabras_continuacion = [
        "si", "sí", "puede ser", "tal vez", "eso", "eso mismo",
        "con un psicologo", "con psicologo", "con psicologia",
        "con psicología", "con alguien", "claro", "ok"
    ]

    for palabra in palabras_continuacion:
        if palabra in texto:
            if ultima_categoria not in ["saludo", "despedida", "agradecimiento", "estado_positivo", "apoyo_academico"]:
                return ultima_categoria

    return categoria_predicha


def elegir_respuesta_no_repetida(respuestas_categoria, memoria):
    columna = "respuesta_final" if "respuesta_final" in respuestas_categoria.columns else "respuesta"

    anteriores = [str(item["respuesta_bot"]) for item in memoria]

    disponibles = respuestas_categoria.copy()
    disponibles = disponibles[~disponibles[columna].astype(str).isin(anteriores)]

    if disponibles.empty:
        disponibles = respuestas_categoria

    return disponibles.sample(1).iloc[0]


def construir_respuesta_humana(fila):
    if "respuesta_final" in df.columns:
        texto_final = str(fila["respuesta_final"])
        if texto_final.strip() != "" and texto_final.lower() != "nan":
            return texto_final

    respuesta = str(fila["respuesta"]) if "respuesta" in df.columns else ""
    recomendacion = str(fila["recomendacion"]) if "recomendacion" in df.columns else ""
    pregunta = str(fila["pregunta_seguimiento"]) if "pregunta_seguimiento" in df.columns else ""

    texto = respuesta

    if recomendacion.strip() != "" and recomendacion.lower() != "nan":
        texto += "\n\nRecomendación: " + recomendacion

    if pregunta.strip() != "" and pregunta.lower() != "nan":
        texto += "\n\n" + pregunta

    return texto


def mejorar_respuesta_con_contexto(respuesta, memoria, categoria_actual):
    if not memoria:
        return respuesta

    ultima_categoria = str(memoria[0]["categoria"])
    ultima_emocion = str(memoria[0]["emocion"])

    categorias_no_emocionales = [
        "saludo", "despedida", "agradecimiento",
        "estado_positivo", "apoyo_academico"
    ]

    if categoria_actual in categorias_no_emocionales:
        return respuesta

    if ultima_categoria == categoria_actual:
        return "Veo que seguimos hablando de este tema. " + respuesta

    if ultima_emocion in ["TRISTE", "ANSIOSO", "ESTRESADO"] and categoria_actual not in categorias_no_emocionales:
        return "Tomando en cuenta lo que me contaste antes, " + respuesta.lower()

    return respuesta


@app.route("/chatbot", methods=["POST"])
def chatbot():
    mensaje = request.form.get("mensaje", "").strip()
    id_usuario = request.form.get("id_usuario", "0")

    if mensaje == "":
        return jsonify({
            "success": False,
            "message": "Mensaje vacío"
        })

    try:
        id_usuario = int(id_usuario)
    except:
        id_usuario = 0

    if id_usuario <= 0:
        return jsonify({
            "success": False,
            "message": "No se recibió el usuario del estudiante"
        })

    conexion = conectar_bd()

    if conexion is None:
        return jsonify({
            "success": False,
            "message": "No se pudo conectar a la base de datos"
        })

    id_estudiante = obtener_id_estudiante(conexion, id_usuario)

    if id_estudiante <= 0:
        conexion.close()
        return jsonify({
            "success": False,
            "message": "No se encontró el estudiante vinculado al usuario"
        })

    memoria = obtener_memoria(conexion, id_estudiante)

    respuesta_directa = detectar_respuesta_directa(mensaje)

    fila = None

    if respuesta_directa is not None:
        categoria = respuesta_directa["categoria"]
        respuesta = respuesta_directa["respuesta"]
        emocion_detectada = respuesta_directa["emocion"]
        nivel_alerta = respuesta_directa["nivel"]

    else:
        mensaje_limpio = limpiar_texto(mensaje)
        mensaje_vect = vectorizador.transform([mensaje_limpio])
        categoria = modelo.predict(mensaje_vect)[0]

        categoria = corregir_categoria_con_memoria(mensaje, categoria, memoria)

        respuestas_categoria = df[df["categoria"] == categoria]

        if respuestas_categoria.empty:
            respuesta = "No entendí bien tu mensaje. Puedes explicármelo con otras palabras.\n\nRecomendación: dime si buscas apoyo emocional, ayuda con estudios o solo conversar.\n\n¿Puedes explicarme un poco más?"
            nivel_alerta_csv = "BAJA"
        else:
            fila = elegir_respuesta_no_repetida(respuestas_categoria, memoria)
            respuesta = construir_respuesta_humana(fila)
            nivel_alerta_csv = fila["nivel_alerta"] if "nivel_alerta" in df.columns else "BAJA"

        emocion_detectada, nivel_alerta = obtener_emocion_y_nivel(
            categoria,
            nivel_alerta_csv,
            fila
        )

        respuesta = mejorar_respuesta_con_contexto(
            respuesta,
            memoria,
            categoria
        )

    registrado = registrar_analisis(
        conexion,
        id_estudiante,
        emocion_detectada,
        nivel_alerta
    )

    guardar_memoria(
        conexion,
        id_estudiante,
        mensaje,
        respuesta,
        categoria,
        emocion_detectada,
        nivel_alerta
    )

    conexion.close()

    return jsonify({
        "success": True,
        "mensaje_usuario": mensaje,
        "respuesta": respuesta,
        "categoria": categoria,
        "emocion_detectada": emocion_detectada,
        "nivel_alerta": nivel_alerta,
        "id_usuario": id_usuario,
        "id_estudiante": id_estudiante,
        "registrado": registrado
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)