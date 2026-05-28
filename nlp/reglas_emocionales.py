import re


def limpiar_basico(texto):
    texto = str(texto).lower().strip()
    texto = texto.replace("á", "a").replace("é", "e").replace("í", "i")
    texto = texto.replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    texto = re.sub(r'[^\w\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def analizar_por_reglas(mensaje):
    texto = limpiar_basico(mensaje)

    reglas = [
        (["hola", "buenos dias", "buenas tardes", "buenas noches"], "NEUTRAL", "saludo", "ESTABLE", 98.0),

        (["bien", "muy bien", "bastante bien", "todo bien", "me siento bien", "estoy bien", "excelente", "feliz", "contento"],
         "FELICIDAD", "expresar_bienestar", "ESTABLE", 97.0),

        (["normal", "tranquilo", "estoy tranquilo", "todo tranquilo", "mas o menos bien"],
         "NEUTRAL", "expresar_estado", "ESTABLE", 94.0),

        (["me siento mal", "estoy mal", "me siento triste", "estoy triste", "quiero llorar", "me siento solo"],
         "TRISTEZA", "buscar_apoyo", "MODERADO", 96.0),

        (["estoy nervioso", "tengo ansiedad", "me siento ansioso", "me preocupa mucho", "tengo miedo al examen"],
         "ANSIEDAD", "buscar_calma", "MODERADO", 96.0),

        (["estoy estresado", "tengo muchas tareas", "no me alcanza el tiempo", "estoy saturado", "mucha presion"],
         "ESTRES", "sobrecarga_academica", "MODERADO", 96.0),

        (["mi profesor me molesta", "el profesor me molesta", "mi docente me molesta", "mi profesor me trata mal"],
         "ENOJO", "conflicto_docente", "MODERADO", 97.0),

        (["mis compañeros me molestan", "se burlan de mi", "me hacen bullying", "me insultan"],
         "MIEDO", "temor_bullying", "ALTO", 97.0),

        (["no quiero vivir", "quiero desaparecer", "quiero hacerme daño", "no aguanto mas", "ya no quiero seguir"],
         "RIESGO_EMOCIONAL", "riesgo_autolesion", "CRITICO", 99.0),
    ]

    for patrones, emocion, intencion, nivel, confianza in reglas:
        for patron in patrones:
            if patron in texto:
                return {
                    "emocion": emocion,
                    "intencion": intencion,
                    "nivel_emocional": nivel,
                    "puntaje_confianza": confianza,
                    "origen": "regla"
                }

    return None