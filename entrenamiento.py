import re


def limpiar_basico(texto):
    texto = str(texto).lower().strip()
    texto = texto.replace("á", "a").replace("é", "e").replace("í", "i")
    texto = texto.replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    texto = re.sub(r'[^\w\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def tiene(texto, palabras):
    return any(palabra in texto for palabra in palabras)


def analizar_por_reglas(mensaje):
    texto = limpiar_basico(mensaje)

    # RIESGO CRÍTICO
    if tiene(texto, [
        "quiero desaparecer", "no quiero vivir", "quiero morirme",
        "quiero hacerme daño", "me quiero hacer daño", "quiero lastimarme",
        "no aguanto mas", "ya no quiero seguir"
    ]):
        return {
            "emocion": "RIESGO_EMOCIONAL",
            "intencion": "riesgo_autolesion",
            "nivel_emocional": "CRITICO",
            "puntaje_confianza": 99.0,
            "origen": "regla_prioritaria"
        }

    # SALUDOS
    if tiene(texto, [
        "hola", "buenos dias", "buenas tardes", "buenas noches",
        "solo pase a saludar", "vine a saludar", "solo queria saludar",
        "solo saludo", "pasaba a saludar"
    ]):
        return {
            "emocion": "NEUTRAL",
            "intencion": "saludo",
            "nivel_emocional": "ESTABLE",
            "puntaje_confianza": 98.0,
            "origen": "regla"
        }

    # BIENESTAR
    if tiene(texto, [
        "estoy bien", "me siento bien", "bastante bien", "muy bien",
        "todo bien", "super bien", "excelente", "feliz", "contento",
        "alegre", "tranquilo", "todo tranquilo"
    ]):
        return {
            "emocion": "FELICIDAD",
            "intencion": "expresar_bienestar",
            "nivel_emocional": "ESTABLE",
            "puntaje_confianza": 97.0,
            "origen": "regla"
        }

    # CONFLICTO CON PROFESOR
    if tiene(texto, [
        "profesor me molesta", "docente me molesta",
        "profesor me trata mal", "docente me trata mal",
        "profesor me grita", "docente me grita",
        "profesor me humilla", "docente me humilla",
        "mi profesor me molesta", "mi profesor me trata mal"
    ]):
        return {
            "emocion": "ENOJO",
            "intencion": "conflicto_docente",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 97.0,
            "origen": "regla"
        }

    # CONFLICTO CON COMPAÑEROS
    if tiene(texto, [
        "me pelee con mis compañeros", "me pelee con un compañero",
        "pelee con mis compañeros", "pelea con mis compañeros",
        "mis compañeros me molestan", "mis compañeros me insultan",
        "se burlan de mi", "me hacen bullying", "me trataron mal",
        "mis compañeros me tratan mal"
    ]):
        return {
            "emocion": "ENOJO",
            "intencion": "conflicto_companeros",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 97.0,
            "origen": "regla"
        }

    # MIEDO / BULLYING
    if tiene(texto, [
        "tengo miedo de ir al colegio", "me da miedo ir al colegio",
        "me amenazan", "me siento amenazado", "tengo miedo",
        "me asusta", "no quiero ir al recreo"
    ]):
        return {
            "emocion": "MIEDO",
            "intencion": "buscar_seguridad",
            "nivel_emocional": "ALTO",
            "puntaje_confianza": 97.0,
            "origen": "regla"
        }

    # TRISTEZA
    if tiene(texto, [
        "me siento mal", "estoy mal", "me siento triste",
        "estoy triste", "quiero llorar", "me siento solo",
        "nadie me entiende", "no tengo ganas de nada",
        "me siento vacio", "me siento apagado"
    ]):
        return {
            "emocion": "TRISTEZA",
            "intencion": "buscar_apoyo",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 96.0,
            "origen": "regla"
        }

    # ANSIEDAD
    if tiene(texto, [
        "estoy nervioso", "me siento nervioso", "tengo ansiedad",
        "me siento ansioso", "me preocupa mucho", "me angustia",
        "no puedo dormir", "tengo miedo al examen",
        "me da miedo exponer"
    ]):
        return {
            "emocion": "ANSIEDAD",
            "intencion": "buscar_calma",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 96.0,
            "origen": "regla"
        }

    # ESTRÉS
    if tiene(texto, [
        "estoy estresado", "me siento estresado", "tengo muchas tareas",
        "demasiadas tareas", "no me alcanza el tiempo",
        "estoy saturado", "mucha presion", "tengo mucha presion"
    ]):
        return {
            "emocion": "ESTRES",
            "intencion": "sobrecarga_academica",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 96.0,
            "origen": "regla"
        }

    # DESMOTIVACIÓN
    if tiene(texto, [
        "no quiero estudiar", "ya no tengo ganas de estudiar",
        "no tengo motivacion", "me da igual estudiar",
        "no me interesa nada", "perdi las ganas",
        "no tengo ganas de hacer tareas"
    ]):
        return {
            "emocion": "DESMOTIVACION",
            "intencion": "falta_interes",
            "nivel_emocional": "MODERADO",
            "puntaje_confianza": 96.0,
            "origen": "regla"
        }

    return None