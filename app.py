from flask import Flask, request, jsonify
import joblib
import pandas as pd
import re
import mysql.connector
import os
from sklearn.metrics.pairwise import cosine_similarity

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
    texto = texto.replace("×", "x")
    texto = re.sub(r'[^\w\s+\-*/x]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()


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

    texto = texto.replace("cuanto es", "")
    texto = texto.replace("cuanto seria", "")
    texto = texto.replace("resultado de", "")
    texto = texto.replace("resuelve", "")
    texto = texto.replace("mas", "+")
    texto = texto.replace("menos", "-")
    texto = texto.replace("por", "x")
    texto = texto.replace("multiplicado por", "x")
    texto = texto.replace("dividido entre", "/")
    texto = texto.replace("dividido por", "/")
    texto = texto.replace("entre", "/")

    patron = r'(\d+(?:\.\d+)?)\s*([\+\-\*/x])\s*(\d+(?:\.\d+)?)'
    coincidencia = re.search(patron, texto)

    if not coincidencia:
        return None

    num1 = float(coincidencia.group(1))
    operador = coincidencia.group(2)
    num2 = float(coincidencia.group(3))

    try:
        if operador == "+":
            resultado = num1 + num2
            simbolo = "+"
        elif operador == "-":
            resultado = num1 - num2
            simbolo = "-"
        elif operador in ["*", "x"]:
            resultado = num1 * num2
            simbolo = "x"
        elif operador == "/":
            if num2 == 0:
                return "No se puede dividir entre cero."
            resultado = num1 / num2
            simbolo = "/"
        else:
            return None

        if resultado == int(resultado):
            resultado = int(resultado)

        if num1 == int(num1):
            num1 = int(num1)
        if num2 == int(num2):
            num2 = int(num2)

        return f"{num1} {simbolo} {num2} = {resultado}"
    except:
        return None


def detectar_respuesta_directa(mensaje):
    texto = limpiar_texto(mensaje)

    # Correcciones simples de escritura
    texto = texto.replace("mycha", "mucha")
    texto = texto.replace("mucha tarea", "muchas tareas")
    texto = texto.replace("mucho tarea", "muchas tareas")
    texto = texto.replace("arto", "harto")
    texto = texto.replace("nesecito", "necesito")
    texto = texto.replace("necesitoo", "necesito")
    texto = texto.replace("necestio", "necesito")
    texto = texto.replace("examenes", "examenes")
    texto = texto.replace("pruevas", "pruebas")
    texto = texto.replace("defenza", "defensa")
    texto = texto.replace("defenzas", "defensas")

    operacion = detectar_operacion_matematica(texto)

    if operacion is not None:
        if "profesor" in texto and ("molesta" in texto or "reclama" in texto or "grita" in texto or "trata mal" in texto or "tarea" in texto or "tareas" in texto):
            return {
                "categoria": "matematicas_y_problema_docente",
                "emocion": "ESTRESADO",
                "nivel": "MEDIA",
                "respuesta": f"{operacion}\n\nTambién noté que mencionaste un problema con tu profesor. Si eso te incomoda o te genera presión, es importante hablarlo.\n\nRecomendación: organiza primero el ejercicio o la tarea más urgente. Si el trato o la carga te está afectando, habla con tus padres, tutor o el área de psicología.\n\n¿Quieres seguir con matemáticas o quieres contarme qué pasó con tu profesor?"
            }

        return {
            "categoria": "matematicas_basicas",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": f"{operacion}\n\nRecomendación: si tienes más ejercicios, escríbeme la operación y te ayudo paso a paso.\n\n¿Quieres resolver otro ejercicio?"
        }

    riesgo = [
        "me quiero hacer dano", "quiero hacerme dano", "no quiero vivir",
        "quiero desaparecer", "quiero morir", "ya no puedo mas",
        "quisiera no existir", "me voy a lastimar", "me quiero suicidar",
        "quiero suicidarme", "me quiero matar", "quiero matarme"
    ]

    for palabra in riesgo:
        if palabra in texto:
            return {
                "categoria": "emergencia_riesgo",
                "emocion": "ANSIOSO",
                "nivel": "ALTA",
                "respuesta": "Lo que me estás diciendo es muy importante y necesita apoyo inmediato.\n\nRecomendación: busca ahora mismo a un adulto de confianza, un familiar, un profesor o el área de psicología. No te quedes solo en este momento.\n\n¿Estás en un lugar seguro ahora?"
            }

    # VALIDACIÓN DE GROSERÍAS O LENGUAJE OFENSIVO
    groserias = [
        "pendejo", "pendeja", "idiota", "imbecil", "estupido", "estupida",
        "mierda", "carajo", "puta", "puto", "cabron", "cabrona",
        "cojudo", "cojuda", "huevon", "huevona", "boludo", "boluda",
        "maldito", "maldita", "joder", "chingar", "chingada", "chingado",
        "vete a la mierda", "callate", "basura", "inutil"
    ]

    contiene_groseria = any(groseria in texto for groseria in groserias)

    if contiene_groseria and (
        "no necesito" in texto or "no quiero ayuda" in texto or "no quiero nada" in texto or
        "nada" in texto or "mas rato" in texto or "luego" in texto
    ):
        return {
            "categoria": "lenguaje_inapropiado_sin_ayuda",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "Está bien, no hay problema. Podemos hablar más tarde si lo necesitas.\n\nTambién te recomiendo expresarte con respeto, sin groserías, para que la conversación sea más tranquila.\n\nCuando necesites ayuda con una materia, una tarea o quieras hablar sobre cómo te sientes, puedes escribirme."
        }

    if contiene_groseria:
        return {
            "categoria": "lenguaje_inapropiado",
            "emocion": "ENOJADO",
            "nivel": "BAJA",
            "respuesta": "Entiendo que puedes estar molesto, pero tratemos de conversar sin groserías.\n\nEstoy aquí para ayudarte, pero necesito que me expliques con respeto qué pasó.\n\n¿El problema es con una materia, una nota, un profesor, un compañero o cómo te sientes?"
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

    # Si el mensaje empieza con saludo, pero trae un problema real, se analiza el problema.
    for saludo in saludos:
        if texto.startswith(saludo + " "):
            texto = texto.replace(saludo + " ", "", 1).strip()
            break

    # CUANDO EL USUARIO DICE QUE NO NECESITA NADA O QUIERE HABLAR DESPUÉS
    sin_ayuda = [
        "no en nada", "en nada", "nada", "no necesito nada",
        "no necesito ayuda", "no necesito ayuda en nada", "no quiero ayuda",
        "no quiero nada", "por ahora nada", "solo queria saludar",
        "solo saludaba", "solo queria decir hola", "solo entre a saludar",
        "ninguna cosa", "ningun problema", "no hay nada", "todo bien",
        "mas rato hablamos", "luego hablamos", "despues hablamos",
        "hablamos luego", "hablamos despues", "otro rato", "mas tarde hablamos"
    ]

    for frase in sin_ayuda:
        if texto == frase or frase in texto:
            return {
                "categoria": "sin_necesidad_ayuda",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": "Está bien 😊 No hay problema.\n\nCuando necesites ayuda con una materia, una tarea o quieras hablar sobre cómo te sientes, puedes escribirme.\n\nEstoy aquí para apoyarte."
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

    # ANSIEDAD, NERVIOS Y ESTRÉS POR EVALUACIONES
    palabras_nervios = [
        "nervioso", "nerviosa", "ansioso", "ansiosa", "estresado", "estresada",
        "preocupado", "preocupada", "asustado", "asustada", "me da miedo",
        "tengo miedo", "me preocupa", "presionado", "presionada", "bloqueado",
        "bloqueada", "me bloqueo", "no puedo dormir", "me tiembla", "me pongo mal"
    ]

    evaluaciones = [
        "examen", "examenes", "prueba", "pruebas", "evaluacion", "evaluaciones",
        "final", "finales", "prueba final", "pruebas finales", "examen final",
        "examenes finales", "defensa", "defensas", "defensa final", "defensas finales",
        "exposicion", "exposiciones", "presentacion", "presentaciones",
        "oral", "examen oral", "tribunal", "jurado", "calificacion", "nota", "notas",
        "aplazar", "aplazaron", "reprobar", "reprobe", "recuperatorio", "recuperacion",
        "trabajo final", "proyecto final"
    ]

    if any(p in texto for p in palabras_nervios) and any(e in texto for e in evaluaciones):
        return {
            "categoria": "ansiedad_evaluacion",
            "emocion": "ANSIOSO",
            "nivel": "MEDIA",
            "respuesta": "Entiendo. Lo que describes parece nervios o ansiedad por una evaluación importante.\n\nEsto puede pasar antes de exámenes, pruebas finales, defensas, exposiciones o presentaciones, especialmente cuando sientes que todo debe salir bien.\n\nRecomendación: respira lento por unos segundos, divide lo que debes hacer en pasos pequeños y repasa primero lo más importante. No intentes resolver todo de golpe.\n\n¿Qué es lo que más te preocupa: olvidarte, equivocarte, que te evalúen o no alcanzar la nota?"
        }

    # PRESIÓN POR DEFENSAS, FINALES, PRESENTACIONES O SITUACIONES IMPORTANTES
    presion_general = [
        "todo debe funcionar", "todo tiene que salir bien", "si algo falla",
        "si sale mal", "estoy perdido", "estoy perdida", "me ira mal",
        "voy a fallar", "voy a fracasar", "no puedo fallar", "no debe fallar",
        "me van a aplazar", "me quiere aplazar", "me pueden aplazar",
        "me pueden reprobar", "me van a reprobar", "estoy contra el tiempo",
        "no me alcanza el tiempo", "me siento presionado", "me siento presionada"
    ]

    if any(p in texto for p in presion_general) or (
        any(e in texto for e in evaluaciones) and ("fallar" in texto or "falla" in texto or "perdido" in texto or "perdida" in texto)
    ):
        return {
            "categoria": "presion_academica_evaluacion",
            "emocion": "ESTRESADO",
            "nivel": "MEDIA",
            "respuesta": "Comprendo esa presión. Cuando una prueba final, defensa, exposición o evaluación parece definir todo, es normal sentirse saturado.\n\nRecomendación: enfócate en lo que sí puedes controlar: revisar lo esencial, preparar un orden de ideas, practicar una vez y descansar un poco antes de presentarte.\n\nSi sientes que la presión es demasiada, habla con alguien de confianza o con el área de psicología para recibir apoyo.\n\n¿Qué parte te preocupa más en este momento?"
        }

    # CONFLICTO O PRESIÓN CON DOCENTE EN EVALUACIONES
    docentes = ["profesor", "docente", "licenciado", "licenciada", "maestro", "maestra", "profe"]
    acciones_docente = [
        "quiere aplazar", "me quiere aplazar", "me va aplazar", "me va a aplazar",
        "me puede aplazar", "me quiere reprobar", "me va a reprobar",
        "me amenaza", "me presiona", "me exige", "me reclama", "me grita",
        "me trata mal", "me pone nervioso", "me pone nerviosa"
    ]

    if any(d in texto for d in docentes) and any(a in texto for a in acciones_docente):
        return {
            "categoria": "estres_docente_evaluacion",
            "emocion": "ESTRESADO",
            "nivel": "MEDIA",
            "respuesta": "Entiendo que eso te genere preocupación. Sentir presión por parte de un docente antes de una prueba, defensa o evaluación puede aumentar mucho los nervios.\n\nRecomendación: intenta separar dos cosas: lo que debes preparar y cómo te está afectando la presión. Si el trato te hace sentir mal, coméntalo con tus padres, tutor o el área de psicología.\n\n¿Te preocupa más la evaluación o la forma en que el docente te está tratando?"
        }

    # PREGUNTAS SOBRE LO QUE SABE HACER EL BOT
    materias_bot = [
        "matematica", "matematicas", "fisica", "quimica", "biologia",
        "geografia", "historia", "ciencias sociales", "sociales",
        "ciencias naturales", "naturales", "lenguaje", "ingles"
    ]

    preguntas_capacidad = [
        "sabes", "sabes de", "conoces", "entiendes", "dominas",
        "hablas", "puedes hablar", "puedes responder", "me puedes explicar"
    ]

    for verbo in preguntas_capacidad:
        if verbo in texto:
            for materia in materias_bot:
                if materia in texto:
                    return {
                        "categoria": "capacidades_bot",
                        "emocion": "NEUTRAL",
                        "nivel": "BAJA",
                        "respuesta": "Sí 😊 Puedo ayudarte con esa materia y también con otras áreas del colegio.\n\nPuedo apoyarte en Matemáticas, Física, Química, Biología, Geografía, Historia, Ciencias Sociales, Ciencias Naturales, Lenguaje e Inglés.\n\nDime qué tema exacto necesitas y continuamos desde ahí."
                    }

    if "que sabes hacer" in texto or "en que puedes ayudar" in texto or "que puedes hacer" in texto:
        return {
            "categoria": "capacidades_bot",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "Puedo ayudarte en dos partes principales 😊\n\n1. Apoyo académico: Matemáticas, Física, Química, Biología, Geografía, Historia, Ciencias Sociales, Ciencias Naturales, Lenguaje e Inglés.\n\n2. Apoyo emocional: puedo escucharte si te sientes triste, estresado, preocupado o si tienes problemas en el colegio.\n\n¿Qué necesitas ahora?"
        }

    # QUEJA SOBRE PROFESOR Y TAREAS
    if "profesor" in texto and ("tarea" in texto or "tareas" in texto or "mucha" in texto or "muchas" in texto or "demasiada" in texto or "demasiadas" in texto):
        return {
            "categoria": "estres_academico_docente",
            "emocion": "ESTRESADO",
            "nivel": "MEDIA",
            "respuesta": "Entiendo 😔 Cuando un profesor deja muchas tareas, puede sentirse pesado o estresante.\n\nRecomendación: intenta ordenar las tareas por prioridad: primero las más urgentes y luego las más fáciles. También puedes descansar unos minutos entre tareas.\n\nSi la carga es demasiada o te está afectando, sería bueno comentarlo con tus padres, tutor o el área de psicología.\n\n¿Te está costando terminar las tareas o más bien te sientes presionado por ese profesor?"
        }

    if "profesor" in texto and ("molesta" in texto or "reclama" in texto or "grita" in texto or "trata mal" in texto):
        return {
            "categoria": "conflicto_docente",
            "emocion": "ESTRESADO",
            "nivel": "MEDIA",
            "respuesta": "Entiendo que eso te preocupe. Cuando hay tensión con un docente, puede dar miedo hablar.\n\nRecomendación: busca un momento tranquilo para preguntar con respeto qué puedes mejorar. Si el trato te hace sentir mal, cuéntaselo a tus padres, tutor o psicología.\n\n¿Qué pasó exactamente con el docente?"
        }

    # CONTINUACIÓN DE CONVERSACIÓN SOBRE NOTAS / CALIFICACIONES
    if (
        "nota" in texto or "notas" in texto or "calificacion" in texto or
        "calificaciones" in texto or "reprobe" in texto or "reprobar" in texto or
        "baja nota" in texto or "mala nota" in texto or "malas notas" in texto or
        "examen" in texto or "prueba" in texto or "me aplazaron" in texto or
        "me fue mal" in texto or "me saque bajo" in texto or "me saque mala" in texto
    ):
        return {
            "categoria": "estres_academico_notas",
            "emocion": "ESTRESADO",
            "nivel": "MEDIA",
            "respuesta": "Ahora entiendo mejor. Te refieres a una nota, calificación, prueba o evaluación que te afectó.\n\nEs normal sentirse preocupado cuando una evaluación no sale como esperabas, pero una nota no define tu capacidad.\n\nRecomendación: revisa en qué parte fallaste, pregunta qué puedes mejorar y organiza un pequeño plan para recuperarte.\n\n¿Eso te hizo sentir triste, preocupado o presionado?"
        }

    # RESPUESTAS CORTAS DE CONTINUACIÓN
    if texto in [
        "si eso fue", "si fue eso", "eso fue", "fue eso", "si", "eso",
        "si fue", "eso mismo", "exacto", "asi es", "claro", "ok eso"
    ]:
        return {
            "categoria": "continuacion_ambigua",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "Entiendo, pero necesito que me des una pista más para ayudarte bien.\n\n¿Fue por una nota, por un profesor, por una prueba, por una defensa, por una tarea, por tus compañeros o por cómo te sentías?"
        }

    if "matematica" in texto or "matematicas" in texto or "matemetixas" in texto or "mate" in texto or "aritmetica" in texto or "algebra" in texto:
        return {
            "categoria": "apoyo_matematicas",
            "emocion": "NEUTRAL",
            "nivel": "BAJA",
            "respuesta": "Claro 😊 Matemáticas se mejora practicando paso a paso.\n\nPuedo ayudarte con:\n• sumas\n• restas\n• multiplicaciones\n• divisiones\n• fracciones\n• álgebra básica\n• problemas razonados\n\nRecomendación: empieza con ejercicios pequeños y revisa en qué paso te equivocas.\n\n¿Qué ejercicio o tema de matemáticas necesitas?"
        }

    materias = {
        "fisica": {
            "categoria": "apoyo_fisica",
            "respuesta": "La Física estudia el movimiento, la fuerza, la energía, la velocidad, la gravedad y otros fenómenos naturales.\n\nRecomendación: para aprender Física, relaciona cada fórmula con un ejemplo real. Por ejemplo: velocidad = distancia / tiempo.\n\n¿Quieres ayuda con movimiento, fuerza, energía o velocidad?"
        },
        "quimica": {
            "categoria": "apoyo_quimica",
            "respuesta": "La Química estudia la materia, los átomos, las moléculas, las sustancias y las reacciones químicas.\n\nRecomendación: empieza por entender átomo, elemento, compuesto y mezcla. Luego puedes avanzar a tabla periódica y reacciones.\n\n¿Qué tema de Química necesitas?"
        },
        "biologia": {
            "categoria": "apoyo_biologia",
            "respuesta": "La Biología estudia los seres vivos: células, cuerpo humano, animales, plantas, ecosistemas y funciones vitales.\n\nRecomendación: usa dibujos y esquemas para entender mejor cada parte.\n\n¿Quieres ayuda con célula, cuerpo humano, plantas, animales o ecosistemas?"
        },
        "geografia": {
            "categoria": "apoyo_geografia",
            "respuesta": "La Geografía estudia la Tierra, los mapas, continentes, países, climas, relieve, población y recursos naturales.\n\nRecomendación: usa mapas para ubicar lugares y relaciona cada región con su clima y características.\n\n¿Qué tema de Geografía necesitas?"
        },
        "historia": {
            "categoria": "apoyo_historia",
            "respuesta": "La Historia estudia hechos importantes del pasado para entender el presente.\n\nRecomendación: organiza los hechos en líneas de tiempo y separa causas, desarrollo y consecuencias.\n\n¿Qué tema de Historia estás viendo?"
        },
        "ciencias sociales": {
            "categoria": "apoyo_ciencias_sociales",
            "respuesta": "Las Ciencias Sociales estudian la sociedad, la historia, la geografía, la economía, la cultura y la forma en que las personas conviven.\n\nRecomendación: identifica primero el lugar, la época, los personajes y las causas del tema.\n\n¿Qué tema de Ciencias Sociales necesitas?"
        },
        "sociales": {
            "categoria": "apoyo_ciencias_sociales",
            "respuesta": "Las Ciencias Sociales estudian la sociedad, la historia, la geografía, la economía, la cultura y la convivencia humana.\n\nRecomendación: resume cada tema respondiendo: qué pasó, dónde pasó, cuándo pasó y por qué pasó.\n\n¿Qué tema de Sociales necesitas?"
        },
        "ciencias naturales": {
            "categoria": "apoyo_ciencias_naturales",
            "respuesta": "Las Ciencias Naturales estudian la naturaleza, los seres vivos, la materia, la energía, el ambiente y los fenómenos naturales.\n\nRecomendación: relaciona cada tema con ejemplos reales de tu entorno.\n\n¿Quieres ayuda con seres vivos, ecosistemas, materia, energía o medio ambiente?"
        },
        "naturales": {
            "categoria": "apoyo_ciencias_naturales",
            "respuesta": "Las Ciencias Naturales ayudan a comprender la naturaleza, los seres vivos, el cuerpo humano, la materia, la energía y el ambiente.\n\nRecomendación: usa ejemplos cotidianos para entender cada concepto.\n\n¿Qué tema de Naturales necesitas?"
        },
        "lenguaje": {
            "categoria": "apoyo_lenguaje",
            "respuesta": "Lenguaje ayuda a mejorar lectura, escritura, comprensión, ortografía, redacción y comunicación.\n\nRecomendación: lee textos cortos, subraya ideas principales y escribe resúmenes con tus propias palabras.\n\n¿Qué tema de Lenguaje necesitas?"
        },
        "ingles": {
            "categoria": "apoyo_ingles",
            "respuesta": "Inglés ayuda a aprender vocabulario, pronunciación, lectura, escritura y conversación básica.\n\nRecomendación: practica palabras cortas, frases simples y repite en voz alta.\n\n¿Qué tema de Inglés necesitas?"
        }
    }

    for materia, datos in materias.items():
        if materia in texto:
            return {
                "categoria": datos["categoria"],
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": datos["respuesta"]
            }

    academico = [
        "dame tips", "tips para aprender", "aprender mejor", "estudiar mejor",
        "como estudio", "como puedo estudiar", "tarea", "examen", "exponer",
        "resumen", "lectura", "ortografia", "no entiendo", "explicame",
        "ayudame con mi tarea", "ayuda en clase", "colegio", "materia"
    ]

    for palabra in academico:
        if palabra in texto:
            return {
                "categoria": "apoyo_academico",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": "Claro, puedo ayudarte con temas del colegio.\n\nPuedo apoyarte en:\n• Matemáticas\n• Física\n• Química\n• Biología\n• Geografía\n• Ciencias Sociales\n• Ciencias Naturales\n• Lenguaje\n• Inglés\n\nRecomendación: dime la materia y el tema exacto para darte una explicación más precisa.\n\n¿Qué materia quieres practicar?"
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

    despedida = ["adios", "chau", "hasta luego", "nos vemos", "me voy", "mas rato hablamos", "luego hablamos", "despues hablamos"]

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
        "matematicas_basicas", "capacidades_bot", "sin_necesidad_ayuda", "lenguaje_inapropiado", "lenguaje_inapropiado_sin_ayuda", "apoyo_fisica", "apoyo_quimica",
        "apoyo_biologia", "apoyo_geografia", "apoyo_historia",
        "apoyo_ciencias_sociales", "apoyo_ciencias_naturales",
        "apoyo_lenguaje", "apoyo_ingles"
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


def buscar_respuesta_dataset_por_similitud(mensaje_limpio, memoria):
    """
    Busca una respuesta directamente en el dataset_limpio.csv cuando el modelo
    tiene baja confianza o cuando la categoría predicha no encuentra respuestas.
    Esto permite que el chatbot siga usando el dataset y no dependa solo de reglas manuales.
    """
    if "pregunta" not in df.columns or df.empty:
        return None

    try:
        preguntas = df["pregunta"].fillna("").astype(str).apply(limpiar_texto)

        # Evita comparar con filas vacías
        indices_validos = preguntas[preguntas.str.strip() != ""].index
        if len(indices_validos) == 0:
            return None

        preguntas_validas = preguntas.loc[indices_validos]

        vect_preguntas = vectorizador.transform(preguntas_validas.tolist())
        vect_mensaje = vectorizador.transform([mensaje_limpio])

        similitudes = cosine_similarity(vect_mensaje, vect_preguntas)[0]
        mejor_posicion = similitudes.argmax()
        mejor_similitud = float(similitudes[mejor_posicion])

        # Umbral bajo/moderado para permitir que el dataset apoye al modelo
        if mejor_similitud < 0.22:
            return None

        indice_real = indices_validos[mejor_posicion]
        fila = df.loc[indice_real]

        categoria = str(fila["categoria"]) if "categoria" in df.columns else "dataset_respuesta"
        respuesta = construir_respuesta_humana(fila)

        # Evitar repetir exactamente la misma respuesta de la memoria
        respuestas_anteriores = [str(item["respuesta_bot"]) for item in memoria]
        if respuesta in respuestas_anteriores and "categoria" in df.columns:
            respuestas_categoria = df[df["categoria"] == categoria]
            if not respuestas_categoria.empty:
                fila = elegir_respuesta_no_repetida(respuestas_categoria, memoria)
                respuesta = construir_respuesta_humana(fila)

        nivel_alerta_csv = fila["nivel_alerta"] if "nivel_alerta" in df.columns else "BAJA"
        emocion_detectada, nivel_alerta = obtener_emocion_y_nivel(categoria, nivel_alerta_csv, fila)

        return {
            "categoria": categoria,
            "respuesta": respuesta,
            "emocion": emocion_detectada,
            "nivel": nivel_alerta,
            "fila": fila,
            "similitud": mejor_similitud
        }

    except:
        return None



def interpretar_respuesta_a_pregunta_seguimiento(mensaje, memoria):
    """
    Interpreta respuestas cortas o contextuales del estudiante cuando el bot
    acaba de hacer una pregunta de seguimiento desde el dataset o desde reglas.
    Esto evita que el chatbot responda "no entendí" cuando el estudiante sí
    está respondiendo a la pregunta anterior.
    """
    if not memoria:
        return None

    texto = limpiar_texto(mensaje)
    ultima_respuesta = reparar_texto(str(memoria[0].get("respuesta_bot", "")))
    ultima_limpia = limpiar_texto(ultima_respuesta)

    if ultima_limpia.strip() == "":
        return None

    emociones = {
        "triste": ("TRISTE", "tristeza"),
        "tristeza": ("TRISTE", "tristeza"),
        "solo": ("TRISTE", "soledad"),
        "sola": ("TRISTE", "soledad"),
        "soledad": ("TRISTE", "soledad"),
        "ansioso": ("ANSIOSO", "ansiedad"),
        "ansiosa": ("ANSIOSO", "ansiedad"),
        "ansiedad": ("ANSIOSO", "ansiedad"),
        "nervioso": ("ANSIOSO", "nervios"),
        "nerviosa": ("ANSIOSO", "nervios"),
        "miedo": ("ANSIOSO", "miedo"),
        "asustado": ("ANSIOSO", "miedo"),
        "asustada": ("ANSIOSO", "miedo"),
        "estres": ("ESTRESADO", "estrés"),
        "estresado": ("ESTRESADO", "estrés"),
        "estresada": ("ESTRESADO", "estrés"),
        "preocupado": ("ESTRESADO", "preocupación"),
        "preocupada": ("ESTRESADO", "preocupación"),
        "presionado": ("ESTRESADO", "presión"),
        "presionada": ("ESTRESADO", "presión"),
        "enojo": ("ENOJADO", "enojo"),
        "enojado": ("ENOJADO", "enojo"),
        "enojada": ("ENOJADO", "enojo"),
        "rabia": ("ENOJADO", "enojo"),
        "cansado": ("ESTRESADO", "cansancio"),
        "cansada": ("ESTRESADO", "cansancio"),
        "agotado": ("ESTRESADO", "cansancio"),
        "agotada": ("ESTRESADO", "cansancio")
    }

    contextos = {
        "colegio": "el colegio",
        "curso": "el colegio",
        "clase": "el colegio",
        "profesor": "un docente",
        "docente": "un docente",
        "profe": "un docente",
        "familia": "tu familia",
        "mama": "tu familia",
        "papa": "tu familia",
        "hermano": "tu familia",
        "hermana": "tu familia",
        "amigo": "tus amigos",
        "amiga": "tus amigos",
        "amigos": "tus amigos",
        "compañero": "tus compañeros",
        "companero": "tus compañeros",
        "compañeros": "tus compañeros",
        "companeros": "tus compañeros",
        "personal": "algo personal",
        "casa": "tu casa o familia"
    }

    evaluacion = [
        "examen", "examenes", "prueba", "pruebas", "final", "finales",
        "defensa", "defensas", "exposicion", "exposiciones", "presentacion",
        "presentaciones", "tribunal", "jurado", "nota", "notas", "calificacion",
        "calificaciones", "aplazar", "reprobar", "fallar", "equivocarme",
        "olvidarme", "no alcanzar", "salir mal", "no funcione", "funcionar"
    ]

    quiere_hablar = [
        "quiero hablar", "prefiero hablar", "hablar", "contarte", "quiero contarte",
        "te cuento", "quiero decirte", "necesito hablar"
    ]

    quiere_calmarse = [
        "calmarme", "forma de calmarme", "quiero calmarme", "prefiero calmarme",
        "respirar", "tranquilizarme", "tranquilo", "tranquila", "consejo",
        "ayudame a calmarme", "como me calmo"
    ]

    afirmaciones = ["si", "sí", "si eso", "eso", "eso mismo", "exacto", "asi es", "claro", "puede ser"]
    negaciones = ["no", "no se", "nose", "no lo se", "no estoy seguro", "no estoy segura"]

    # 1) El bot preguntó por la emoción principal.
    if (
        "que emocion" in ultima_limpia or
        "como te sientes" in ultima_limpia or
        "te hizo sentir triste" in ultima_limpia or
        "preocupado o presionado" in ultima_limpia or
        "preocupada o presionada" in ultima_limpia
    ):
        for clave, datos in emociones.items():
            if clave in texto:
                emocion, nombre = datos
                nivel = "MEDIA" if emocion in ["TRISTE", "ANSIOSO", "ESTRESADO", "ENOJADO"] else "BAJA"
                return {
                    "categoria": "seguimiento_emocion",
                    "emocion": emocion,
                    "nivel": nivel,
                    "respuesta": f"Gracias por aclararlo. Entonces la emoción que más aparece ahora es {nombre}.\n\nEs importante reconocerlo porque así se puede buscar una mejor forma de manejarlo.\n\nRecomendación: respira despacio unos segundos, intenta ponerle nombre a lo que sientes y cuéntale esto a un adulto de confianza o al área de psicología si sigue aumentando.\n\n¿Quieres contarme qué situación provocó esa emoción?"
                }

        if texto in afirmaciones:
            return {
                "categoria": "seguimiento_emocion_ambigua",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": "Entiendo. Para ayudarte mejor, dime qué emoción se parece más a lo que sientes: tristeza, ansiedad, estrés, miedo, enojo, cansancio o preocupación."
            }

    # 2) El bot preguntó si tiene que ver con colegio, familia, amigos o algo personal.
    if (
        "colegio la familia amigos" in ultima_limpia or
        "colegio familia amigos" in ultima_limpia or
        "tiene que ver con el colegio" in ultima_limpia or
        "familia amigos o algo personal" in ultima_limpia
    ):
        for clave, contexto in contextos.items():
            if clave in texto:
                emocion = "ESTRESADO" if contexto in ["el colegio", "un docente"] else "TRISTE"
                return {
                    "categoria": "seguimiento_contexto",
                    "emocion": emocion,
                    "nivel": "MEDIA",
                    "respuesta": f"Entiendo, entonces esto se relaciona con {contexto}.\n\nGracias por aclararlo. Eso ayuda a comprender mejor lo que estás viviendo.\n\nRecomendación: intenta identificar qué parte de esa situación te afecta más: lo que pasó, lo que alguien dijo, la presión que sientes o el miedo a que vuelva a pasar.\n\n¿Qué fue lo que más te afectó de esa situación?"
                }

        if texto in afirmaciones or texto in negaciones:
            return {
                "categoria": "seguimiento_contexto_ambigua",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": "Está bien. Para ubicar mejor la situación, dime solo una opción: colegio, familia, amigos, compañeros, profesor o algo personal."
            }

    # 3) El bot preguntó si quiere hablar o una forma de calmarse.
    if (
        "quieres hablar" in ultima_limpia and "calmarte" in ultima_limpia or
        "prefieres que primero te sugiera una forma" in ultima_limpia or
        "forma de calmarte" in ultima_limpia
    ):
        if any(p in texto for p in quiere_calmarse):
            return {
                "categoria": "seguimiento_calmarse",
                "emocion": "ANSIOSO",
                "nivel": "MEDIA",
                "respuesta": "Está bien, primero intentemos bajar un poco la intensidad.\n\nHaz esto por unos segundos:\n1. Inhala lento por la nariz.\n2. Mantén el aire un momento.\n3. Exhala despacio.\n4. Repite y mira a tu alrededor nombrando 3 cosas que ves.\n\nRecomendación: cuando te sientas un poco más tranquilo, intenta contar qué pasó en una sola frase.\n\n¿Te sientes un poco más calmado ahora?"
            }

        if any(p in texto for p in quiere_hablar):
            return {
                "categoria": "seguimiento_quiere_hablar",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": "Claro, podemos hablar paso a paso.\n\nCuéntame con calma qué ocurrió. No necesitas escribir perfecto ni responder rápido.\n\nRecomendación: empieza por decirme quién estuvo involucrado o en qué lugar pasó.\n\n¿Qué fue lo primero que ocurrió?"
            }

        if texto in afirmaciones:
            return {
                "categoria": "seguimiento_quiere_hablar",
                "emocion": "NEUTRAL",
                "nivel": "BAJA",
                "respuesta": "Está bien, te escucho. Cuéntame un poco más de lo que pasó, paso a paso."
            }

    # 4) El bot preguntó qué pasó antes o qué quiere contar primero.
    if (
        "que paso antes" in ultima_limpia or
        "antes de que decidieras escribirme" in ultima_limpia or
        "que te gustaria contarme primero" in ultima_limpia or
        "que fue lo primero que ocurrio" in ultima_limpia or
        "que fue lo que mas te afecto" in ultima_limpia
    ):
        if any(e in texto for e in evaluacion):
            return {
                "categoria": "seguimiento_evaluacion",
                "emocion": "ESTRESADO",
                "nivel": "MEDIA",
                "respuesta": "Ahora entiendo mejor. Lo que te preocupa está relacionado con una evaluación, prueba, defensa, exposición o calificación.\n\nEs normal sentir presión cuando algo parece muy importante.\n\nRecomendación: separa el problema en partes: qué debes preparar, qué ya tienes avanzado y qué puedes practicar primero.\n\n¿Qué es lo que más miedo te da: fallar, olvidarte, equivocarte o que te evalúen?"
            }

        for clave, contexto in contextos.items():
            if clave in texto:
                return {
                    "categoria": "seguimiento_relato_contexto",
                    "emocion": "ESTRESADO",
                    "nivel": "MEDIA",
                    "respuesta": f"Gracias por contármelo. Entonces lo que pasó tiene relación con {contexto}.\n\nRecomendación: intenta pensar qué fue lo que más te afectó: una palabra, una acción, una presión o una preocupación.\n\n¿Cómo te sentiste después de eso?"
                }

        if len(texto.split()) >= 3:
            return {
                "categoria": "seguimiento_relato_general",
                "emocion": "NEUTRAL",
                "nivel": "MEDIA",
                "respuesta": "Gracias por explicarlo. Entiendo que eso pudo afectarte.\n\nRecomendación: intenta no cargarlo solo. Si esto te sigue preocupando, habla con alguien de confianza o con el área de psicología.\n\n¿Qué emoción apareció más fuerte después de eso?"
            }

    # 5) El bot preguntó por una preocupación específica en evaluaciones.
    if (
        "que es lo que mas te preocupa" in ultima_limpia or
        "que parte te preocupa mas" in ultima_limpia or
        "olvidarte equivocarte" in ultima_limpia or
        "que te evaluen" in ultima_limpia or
        "no alcanzar la nota" in ultima_limpia
    ):
        if "olvid" in texto:
            motivo = "olvidarte lo que estudiaste"
        elif "equivoc" in texto or "fallar" in texto or "falla" in texto:
            motivo = "equivocarte o fallar"
        elif "evaluen" in texto or "evaluar" in texto or "tribunal" in texto or "jurado" in texto:
            motivo = "que te evalúen"
        elif "nota" in texto or "calificacion" in texto or "alcanzar" in texto:
            motivo = "no alcanzar la nota"
        else:
            motivo = "la presión de la evaluación"

        return {
            "categoria": "seguimiento_preocupacion_evaluacion",
            "emocion": "ANSIOSO",
            "nivel": "MEDIA",
            "respuesta": f"Entiendo, entonces lo que más te preocupa es {motivo}.\n\nRecomendación: practica una parte pequeña primero. Si es una defensa o exposición, ensaya el inicio y las ideas principales. Si es una prueba, repasa los puntos más importantes.\n\nNo tienes que resolver todo de golpe; empieza por lo más urgente.\n\n¿Quieres que te sugiera una forma rápida para calmar los nervios antes de la evaluación?"
        }

    return None

def mejorar_respuesta_con_contexto(respuesta, memoria, categoria_actual):
    if not memoria:
        return respuesta

    ultima_categoria = str(memoria[0]["categoria"])
    ultima_emocion = str(memoria[0]["emocion"])

    categorias_no_emocionales = [
        "saludo", "saludo_estado", "despedida", "agradecimiento",
        "estado_positivo", "apoyo_academico", "apoyo_matematicas",
        "matematicas_basicas", "capacidades_bot", "sin_necesidad_ayuda", "lenguaje_inapropiado", "lenguaje_inapropiado_sin_ayuda", "apoyo_fisica", "apoyo_quimica",
        "apoyo_biologia", "apoyo_geografia", "apoyo_historia",
        "apoyo_ciencias_sociales", "apoyo_ciencias_naturales",
        "apoyo_lenguaje", "apoyo_ingles"
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
    respuesta_seguimiento = None

    # Si no hubo una respuesta directa crítica, se revisa si el usuario
    # está contestando la última pregunta de seguimiento que hizo el bot.
    if respuesta_directa is None:
        respuesta_seguimiento = interpretar_respuesta_a_pregunta_seguimiento(mensaje, memoria)

    fila = None

    if respuesta_directa is not None:
        categoria = respuesta_directa["categoria"]
        respuesta = respuesta_directa["respuesta"]
        emocion_detectada = respuesta_directa["emocion"]
        nivel_alerta = respuesta_directa["nivel"]

    elif respuesta_seguimiento is not None:
        categoria = respuesta_seguimiento["categoria"]
        respuesta = respuesta_seguimiento["respuesta"]
        emocion_detectada = respuesta_seguimiento["emocion"]
        nivel_alerta = respuesta_seguimiento["nivel"]

    else:
        mensaje_limpio = limpiar_texto(mensaje)
        mensaje_vect = vectorizador.transform([mensaje_limpio])

        if hasattr(modelo, "predict_proba"):
            probabilidades = modelo.predict_proba(mensaje_vect)[0]
            indice = probabilidades.argmax()
            confianza = probabilidades[indice]
            categoria = modelo.classes_[indice]

            if confianza < 0.35:
                # Primero intentamos responder usando el dataset_limpio.csv por similitud.
                # Si el dataset encuentra algo parecido, se usa esa respuesta.
                respuesta_dataset = buscar_respuesta_dataset_por_similitud(mensaje_limpio, memoria)

                if respuesta_dataset is not None:
                    categoria = respuesta_dataset["categoria"]
                    respuesta = respuesta_dataset["respuesta"]
                    emocion_detectada = respuesta_dataset["emocion"]
                    nivel_alerta = respuesta_dataset["nivel"]

                    respuesta = mejorar_respuesta_con_contexto(
                        respuesta,
                        memoria,
                        categoria
                    )

                    registrado = registrar_analisis(conexion, id_estudiante, emocion_detectada, nivel_alerta)

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

                categoria = "malestar_ambiguo"
                respuesta = "No entendí completamente tu mensaje, pero puedo seguir la conversación si me das una pista.\n\nDime si se relaciona con:\n• una nota\n• una tarea\n• un profesor\n• un compañero\n• una emoción\n• una materia\n\nPor ejemplo: 'fue por una nota', 'fue por mi profesor' o 'me siento triste por eso'."
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
            # Si la categoría predicha no existe en el dataset, intentamos buscar por similitud.
            respuesta_dataset = buscar_respuesta_dataset_por_similitud(mensaje_limpio, memoria)

            if respuesta_dataset is not None:
                categoria = respuesta_dataset["categoria"]
                respuesta = respuesta_dataset["respuesta"]
                emocion_detectada = respuesta_dataset["emocion"]
                nivel_alerta = respuesta_dataset["nivel"]
            else:
                respuesta = "No entendí bien tu mensaje. Puedes explicármelo con otras palabras.\n\nRecomendación: dime si buscas apoyo emocional, ayuda con estudios o solo conversar.\n\n¿Puedes explicarme un poco más?"
                emocion_detectada = "NEUTRAL"
                nivel_alerta = "BAJA"
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