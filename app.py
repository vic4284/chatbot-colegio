from flask import Flask, request, jsonify
import joblib
import pandas as pd
import re
import mysql.connector
import random
import os

app = Flask(__name__)

modelo = joblib.load("modelo_chatbot.pkl")
vectorizador = joblib.load("vectorizador.pkl")
df = pd.read_csv("dataset_limpio.csv", encoding="utf-8-sig")


def reparar_texto(texto):
    texto = str(texto)
    if "Ã" in texto or "Â" in texto:
        try:
            texto = texto.encode("latin1").decode("utf-8")
        except:
            pass
    return texto


def limpiar_texto(texto):
    texto = reparar_texto(texto)
    texto = str(texto).lower().strip()
    texto = texto.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    texto = texto.replace("ñ", "n")
    texto = re.sub(r'[^\w\s+\-*/]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
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

    if nivel in ["alto", "alta", "critico", "critica"]:
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
        emocion_csv = reparar_texto(str(fila["emocion_detectada"])).strip().upper()
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


def detectar_operacion_matematica(texto):
    texto = limpiar_texto(texto)

    patron = r'(\d+)\s*([\+\-\*/])\s*(\d+)'
    coincidencia = re.search(patron, texto)

    if not coincidencia:
        return None

    num1 = int(coincidencia.group(1))
    operador = coincidencia.group(2)
    num2 = int(coincidencia.group(3))

    try:
        if operador == "+":
            resultado = num1 + num2
        elif operador == "-":
            resultado = num1 - num2
        elif operador == "*":
            resultado = num1 * num2
        elif operador == "/":
            if num2 == 0:
                return "No se puede dividir entre cero."
            resultado = num1 / num2
        else:
            return None

        if resultado == int(resultado):
            resultado = int(resultado)

        return f"{num1} {operador} {num2} = {resultado}"
    except:
        return None


def detectar_respuesta_directa(mensaje):
    texto = limpiar_texto(mensaje)

    operacion = detectar_operacion_matematica(texto)

    if operacion is not None:
        if "profesor" in texto and ("molesta" in texto or "molestar" in texto or "trata mal" in texto):
            return {
                "categoria": "matematicas_y_problema_docente",
                "emocion": "ESTRESADO",
                "nivel": "MEDIA",
                "respuesta": f"{operacion}\n\nTambién noté que mencionaste que tu profesor te molesta. Si eso te incomoda o te hace sentir mal, es importante que no lo guardes solo.\n\nRecomendación: habla con un adulto de confianza, tu tutor, tus padres o el área de psicología del colegio para que puedan orientarte.\n\n¿Quieres que te ayude con más ejercicios de matemáticas o quieres contarme qué pasó con tu profesor?"
            }

        return {
            "categoria": "matematicas_basicas",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": f"{operacion}\n\nRecomendación: si tienes más ejercicios, puedes escribirme la operación y te ayudo paso a paso.\n\n¿Quieres resolver otro ejercicio?"
        }

    riesgo = [
        "me quiero hacer dano", "quiero hacerme dano", "no quiero vivir",
        "quiero desaparecer", "quiero morir", "ya no puedo mas",
        "quisiera no existir", "me voy a lastimar", "me quiero suicidar",
        "quiero suicidarme"
    ]

    for palabra in riesgo:
        if palabra in texto:
            return {
                "categoria": "emergencia_riesgo",
                "emocion": "ANSIOSO",
                "nivel": "ALTA",
                "respuesta": "Lo que me estás diciendo es muy importante y necesita apoyo inmediato.\n\nRecomendación: busca ahora mismo a un adulto de confianza, un familiar, un profesor o el área de psicología. No te quedes solo en este momento.\n\n¿Estás en un lugar seguro ahora?"
            }

    saludos = [
        "hola", "ola", "holaa", "holaaa", "holi", "hila", "buenas",
        "buenos dias", "buenas tardes", "buenas noches", "hey", "hello"
    ]

    if texto in saludos:
        return {
            "categoria": "saludo",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "Hola 😊 Estoy aquí para ayudarte.\n\nPuedes contarme si necesitas apoyo emocional, ayuda con alguna materia o simplemente conversar.\n\n¿En qué te puedo ayudar hoy?"
        }

    preguntas_estado_bot = [
        "como estas", "como estas hoy", "que tal", "como te va",
        "estas bien", "como andas"
    ]

    if texto in preguntas_estado_bot:
        return {
            "categoria": "saludo_estado",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "Estoy aquí para escucharte y ayudarte 😊\n\nPuedes hablar conmigo sobre tus materias, tareas, emociones o alguna situación que estés viviendo en el colegio.\n\n¿Cómo te sientes tú hoy?"
        }

    if "profesor" in texto and ("molesta" in texto or "molestar" in texto or "trata mal" in texto or "me grita" in texto):
        return {
            "categoria": "problema_docente",
            "emocion": "ESTRESADO",
            "nivel": "MEDIA",
            "respuesta": "Lamento que estés pasando por eso. Si un profesor te molesta o te hace sentir incómodo, es importante tomarlo con seriedad.\n\nRecomendación: intenta contarle la situación a un adulto de confianza, a tus padres, tutor o al área de psicología del colegio. No es bueno guardar eso solo.\n\n¿Quieres contarme qué ocurrió exactamente?"
        }

    if "matematica" in texto or "matematicas" in texto or "matemetixas" in texto or "mate" in texto:
        if "tip" in texto or "mejorar" in texto or "aprender" in texto or "ayuda" in texto:
            return {
                "categoria": "apoyo_matematicas",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": "Claro 😊 Para mejorar en matemáticas te recomiendo practicar poco a poco y no memorizar sin entender.\n\nRecomendación:\n• repasa operaciones básicas\n• practica 15 a 20 minutos al día\n• resuelve ejercicios paso a paso\n• revisa tus errores sin frustrarte\n• pregunta cuando no entiendas un procedimiento\n\n¿Quieres que practiquemos con sumas, restas, multiplicaciones, divisiones o álgebra?"
            }

    materias = {
        "fisica": "Física estudia fenómenos como fuerza, movimiento, energía, calor y electricidad.",
        "quimica": "Química estudia la materia, sus cambios, mezclas, sustancias y reacciones.",
        "biologia": "Biología estudia los seres vivos, las células, el cuerpo humano, plantas, animales y ecosistemas.",
        "historia": "Historia estudia hechos importantes del pasado para comprender mejor el presente.",
        "geografia": "Geografía estudia la Tierra, mapas, regiones, clima, población y recursos naturales.",
        "lenguaje": "Lenguaje ayuda a mejorar lectura, escritura, comprensión, ortografía y comunicación.",
        "literatura": "Literatura estudia textos, cuentos, poemas, novelas y formas de expresión escrita.",
        "ingles": "Inglés ayuda a comunicarte en otro idioma mediante vocabulario, lectura, escritura y pronunciación."
    }

    for materia, descripcion in materias.items():
        if materia in texto:
            return {
                "categoria": f"apoyo_{materia}",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": f"{descripcion}\n\nRecomendación: dime qué tema específico no entiendes y te lo explico de forma sencilla con ejemplos.\n\n¿Sobre qué tema de {materia} necesitas ayuda?"
            }

    academico = [
        "dame tips", "tips para aprender", "aprender mejor", "estudiar mejor",
        "como estudio", "como puedo estudiar", "tarea", "examen", "exponer",
        "resumen", "lectura", "ortografia", "no entiendo", "explicame",
        "ayudame con mi tarea"
    ]

    for palabra in academico:
        if palabra in texto:
            return {
                "categoria": "apoyo_academico",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": "Claro, puedo ayudarte con temas del colegio.\n\nRecomendación: dime la materia y el tema exacto. Por ejemplo: matemáticas, física, química, biología, historia, geografía, lenguaje o inglés.\n\n¿Qué materia quieres practicar?"
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
                "respuesta": "Perfecto, gracias por aclararlo 😊\n\nRecomendación: si no hay un problema emocional, puedo ayudarte con estudios, tareas, organización o alguna materia.\n\n¿Sobre qué tema quieres conversar?"
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
                "respuesta": "Me alegra saber eso 😊 También es bueno reconocer cuando algo va bien.\n\nRecomendación: aprovecha ese ánimo para avanzar algo pequeño o disfrutar el momento sin presionarte.\n\n¿Qué pasó para que te sientas así?"
            }

    gracias = ["gracias", "muchas gracias", "ok gracias", "te agradezco"]

    if texto in gracias:
        return {
            "categoria": "agradecimiento",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "De nada 😊 Me alegra poder ayudarte.\n\nRecomendación: si algo vuelve a preocuparte o tienes dudas de alguna materia, puedes escribirme.\n\n¿Quieres hablar de algo más?"
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
        "no se que me pasa", "no me siento bien"
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

    categorias_no_continuar = [
        "saludo", "saludo_estado", "despedida", "agradecimiento",
        "estado_positivo", "apoyo_academico", "apoyo_matematicas",
        "matematicas_basicas"
    ]

    ultima_categoria = str(memoria[0]["categoria"])

    palabras_continuacion = [
        "si", "sí", "puede ser", "tal vez", "eso", "eso mismo",
        "con un psicologo", "con psicologo", "con psicologia",
        "con alguien", "claro", "ok"
    ]

    for palabra in palabras_continuacion:
        if palabra == texto:
            if ultima_categoria not in categorias_no_continuar:
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
        texto_final = reparar_texto(str(fila["respuesta_final"]))
        if texto_final.strip() != "" and texto_final.lower() != "nan":
            return texto_final

    respuesta = reparar_texto(str(fila["respuesta"])) if "respuesta" in df.columns else ""
    recomendacion = reparar_texto(str(fila["recomendacion"])) if "recomendacion" in df.columns else ""
    pregunta = reparar_texto(str(fila["pregunta_seguimiento"])) if "pregunta_seguimiento" in df.columns else ""

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
        "saludo", "saludo_estado", "despedida", "agradecimiento",
        "estado_positivo", "apoyo_academico", "apoyo_matematicas",
        "matematicas_basicas"
    ]

    if categoria_actual in categorias_no_emocionales:
        return respuesta

    if ultima_categoria == categoria_actual:
        return "Veo que seguimos hablando de este tema. " + respuesta

    if ultima_emocion in ["TRISTE", "ANSIOSO", "ESTRESADO"] and categoria_actual not in categorias_no_emocionales:
        return "Tomando en cuenta lo que me contaste antes, " + respuesta.lower()

    return respuesta


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "success": True,
        "message": "Chatbot escolar activo",
        "endpoint": "/chatbot"
    })


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

        if hasattr(modelo, "predict_proba"):
            probabilidades = modelo.predict_proba(mensaje_vect)[0]
            indice = probabilidades.argmax()
            confianza = probabilidades[indice]
            categoria = modelo.classes_[indice]

            if confianza < 0.35:
                categoria = "malestar_ambiguo"
                respuesta = "No entendí bien tu mensaje. Para ayudarte mejor, dime si se relaciona con una materia del colegio, una emoción o un problema con alguien.\n\nRecomendación: puedes escribir algo como: 'necesito ayuda en matemáticas', 'me siento triste' o 'tengo un problema con un compañero'.\n\n¿A qué tema te refieres?"
                emocion_detectada = "NEUTRAL"
                nivel_alerta = "BAJA"

                guardar_memoria(conexion, id_estudiante, mensaje, respuesta, categoria, emocion_detectada, nivel_alerta)
                registrado = registrar_analisis(conexion, id_estudiante, emocion_detectada, nivel_alerta)
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
        else:
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)