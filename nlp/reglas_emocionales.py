import re


def limpiar_basico(texto):
    texto = str(texto).lower().strip()
    texto = texto.replace("á", "a").replace("é", "e").replace("í", "i")
    texto = texto.replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    texto = re.sub(r'[^\w\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def contiene(texto, palabras):
    return any(palabra in texto for palabra in palabras)


def analizar_por_reglas(mensaje):
    texto = limpiar_basico(mensaje)

    # 1. RIESGO CRÍTICO
    if contiene(texto, [
        "no quiero vivir", "quiero desaparecer", "quiero morirme",
        "quiero hacerme daño", "me quiero hacer daño", "no aguanto mas",
        "ya no quiero seguir", "quiero lastimarme"
    ]):
        return {
            "emocion": "RIESGO_EMOCIONAL",
            "intencion": "riesgo_autolesion",
            "nivel_emocional": "CRITICO",
            "puntaje_confianza": 99.0,
            "origen": "regla_prioritaria"
        }

    # 2. SALUDO / CONVERSACIÓN NORMAL
    if contiene(texto, [
        "hola", "buenos dias", "buenas tardes", "buenas noches",
        "solo pase a saludar", "solo pase a saludar", "vine a saludar",
        "solo saludo", "solo queria saludar"
    ]):
        return {
            "emocion": "NEUTRAL",
            "intencion": "saludo",
            "nivel_emocional": "ESTABLE",
            "puntaje_confianza": 98.0,
            "origen": "regla"
        }

    # 3. BIENESTAR
    if contiene(texto, [
        "bien", "muy bien", "bastante bien", "todo bien",
        "me siento bien", "estoy bien", "excelente", "feliz",
        "contento", "tranquilo", "todo tranquilo"
    ]):
        return {
            "emocion": "FELICIDAD",
            "intencion": "expresar_bienestar",
            "nivel_emocional": "ESTABLE",
            "puntaje_confianza": 97.0,
            "origen": "regla"
        }

    # 4. CONFLICTO CON PROFESOR
    if contiene(texto, [
        "mi profesor me molesta", "el profesor me molesta",
        "mi docente me molesta", "mi profesor me trata mal",
        "el profesor me trata mal", "mi profesor me grita",
        "mi docente me grita", "mi profesor me humilla"
    ]):
        return {
            "emocion": "ENOJO",
            "intencion": "conflicto_docente",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 97.0,
            "origen": "regla"
        }

    # 5. CONFLICTO CON COMPAÑEROS
    if contiene(texto, [
        "me pelee con mis compañeros", "me pelee con un compañero",
        "discutil con mis compañeros", "me enoje con mis compañeros",
        "mis compañeros me molestan", "mis compañeros me insultan",
        "se burlan de mi", "me hacen bullying", "me trataron mal en clase"
    ]):
        return {
            "emocion": "ENOJO",
            "intencion": "conflicto_companeros",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 97.0,
            "origen": "regla"
        }

    # 6. TRISTEZA
    if contiene(texto, [
        "me siento mal", "estoy mal", "me siento triste",
        "estoy triste", "quiero llorar", "me siento solo",
        "nadie me entiende", "no tengo ganas de nada"
    ]):
        return {
            "emocion": "TRISTEZA",
            "intencion": "buscar_apoyo",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 96.0,
            "origen": "regla"
        }

    # 7. ANSIEDAD
    if contiene(texto, [
        "estoy nervioso", "tengo ansiedad", "me siento ansioso",
        "me preocupa mucho", "tengo miedo al examen",
        "no puedo dormir", "me angustia"
    ]):
        return {
            "emocion": "ANSIEDAD",
            "intencion": "buscar_calma",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 96.0,
            "origen": "regla"
        }

    # 8. ESTRÉS
    if contiene(texto, [
        "estoy estresado", "tengo muchas tareas",
        "no me alcanza el tiempo", "estoy saturado",
        "mucha presion", "demasiadas tareas"
    ]):
        return {
            "emocion": "ESTRES",
            "intencion": "sobrecarga_academica",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 96.0,
            "origen": "regla"
        }

    # 9. DESMOTIVACIÓN
    if contiene(texto, [
        "no quiero estudiar", "ya no tengo ganas de estudiar",
        "no tengo motivacion", "me da igual estudiar",
        "no me interesa nada", "perdi las ganas"
    ]):
        return {
            "emocion": "DESMOTIVACION",
            "intencion": "falta_interes",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 96.0,
            "origen": "regla"
        }

    return None