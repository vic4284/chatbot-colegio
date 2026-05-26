from flask import Flask, request, jsonify
from openai import OpenAI
import os
import re
import joblib
import numpy as np

# Inicialización del servidor Flask
app = Flask(__name__)

# Conexión con OpenAI mediante variable de entorno
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cargar modelos NLP propios
vectorizador = joblib.load("modelos/vectorizador.pkl")
modelo_emocion = joblib.load("modelos/modelo_emocion.pkl")
modelo_intencion = joblib.load("modelos/modelo_intencion.pkl")
modelo_nivel = joblib.load("modelos/modelo_nivel_emocional.pkl")


def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r'[^\w\s+\-*/]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def obtener_confianza(modelo, texto_vectorizado):
    probabilidades = modelo.predict_proba(texto_vectorizado)[0]
    confianza = float(np.max(probabilidades))
    return round(confianza * 100, 2)


def analizar_mensaje(mensaje):
    mensaje_limpio = limpiar_texto(mensaje)
    mensaje_vectorizado = vectorizador.transform([mensaje_limpio])

    emocion = modelo_emocion.predict(mensaje_vectorizado)[0]
    intencion = modelo_intencion.predict(mensaje_vectorizado)[0]
    nivel_emocional = modelo_nivel.predict(mensaje_vectorizado)[0]

    confianza_emocion = obtener_confianza(modelo_emocion, mensaje_vectorizado)
    confianza_intencion = obtener_confianza(modelo_intencion, mensaje_vectorizado)
    confianza_nivel = obtener_confianza(modelo_nivel, mensaje_vectorizado)

    puntaje_confianza = round(
        (confianza_emocion + confianza_intencion + confianza_nivel) / 3,
        2
    )

    return {
        "emocion": emocion,
        "intencion": intencion,
        "nivel_emocional": nivel_emocional,
        "puntaje_confianza": puntaje_confianza
    }


def generar_recomendacion(emocion, nivel_emocional):
    if nivel_emocional == "CRITICO":
        return "Activar alerta crítica y recomendar contacto inmediato con psicología o un adulto responsable."

    if nivel_emocional == "ALTO":
        return "Registrar seguimiento prioritario y sugerir orientación con el área de psicología."

    if emocion == "ANSIEDAD":
        return "Sugerir respiración pausada, organizar tareas y buscar apoyo si la ansiedad continúa."

    if emocion == "TRISTEZA":
        return "Responder con empatía, validar la emoción y sugerir hablar con alguien de confianza."

    if emocion == "ESTRES":
        return "Recomendar organizar actividades, priorizar tareas y tomar pausas breves."

    if emocion == "ENOJO":
        return "Recomendar calmarse antes de responder y buscar diálogo respetuoso."

    if emocion == "DESMOTIVACION":
        return "Motivar con metas pequeñas y sugerir apoyo académico o emocional."

    if emocion == "MIEDO":
        return "Brindar contención y sugerir acudir a un adulto de confianza si existe amenaza."

    if emocion == "FELICIDAD":
        return "Reforzar positivamente el estado emocional y motivar a mantener hábitos saludables."

    return "Responder con orientación general y continuar la conversación."


PERSONALIDAD_CHATBOT = """
Eres SEA, un chatbot emocional y académico para estudiantes de secundaria.

Tu forma de hablar:
- Hablas en español de forma natural, juvenil, cercana y conversadora.
- Eres amigable, espontáneo y dinámico.
- Puedes usar emojis de forma moderada.
- En situaciones graves o delicadas usa pocos emojis o ninguno.

Tu objetivo principal:
- Hacer que el estudiante quiera seguir hablando.
- Escucharlo con calma.
- Obtener más información sobre cómo se siente.
- Ayudarlo a ordenar sus ideas.
- Dar consejos útiles y realistas.
- Detectar posibles problemas emocionales.

Cómo debes responder:
- Responde de forma cálida y humana.
- Haz siempre 1 o 2 preguntas para continuar la conversación.
- Mantén conversaciones naturales, no respuestas robóticas.
- Si el estudiante está triste, ansioso o frustrado, responde con empatía.
- Si el estudiante menciona autolesiones, suicidio o situaciones graves:
  - responde con máxima seriedad
  - evita bromas
  - recomienda buscar ayuda inmediata de un adulto, tutor o psicólogo escolar

Importante:
- No des diagnósticos médicos o psicológicos.
- No digas que eres psicólogo.
- No minimices emociones.
- No finalices rápido la conversación.
"""


@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "estado": "activo",
        "mensaje": "Servidor del chatbot SEA funcionando con OpenAI y NLP emocional001"
    })


@app.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        data = request.get_json()
        mensaje = data.get("mensaje", "").strip()

        if not mensaje:
            return jsonify({
                "respuesta": "Escribe un mensaje para poder ayudarte.",
                "emocion": "NEUTRAL",
                "intencion": "mensaje_vacio",
                "nivel_emocional": "ESTABLE",
                "puntaje_confianza": 0,
                "recomendacion": "Solicitar al estudiante que escriba un mensaje.",
                "categoria": "general",
                "nivel_alerta": "ESTABLE"
            })

        analisis = analizar_mensaje(mensaje)

        recomendacion = generar_recomendacion(
            analisis["emocion"],
            analisis["nivel_emocional"]
        )

        entrada_usuario = f"""
Mensaje del estudiante:
{mensaje}

Análisis emocional detectado por el modelo NLP propio:
- Emoción: {analisis["emocion"]}
- Intención: {analisis["intencion"]}
- Nivel emocional: {analisis["nivel_emocional"]}
- Recomendación interna: {recomendacion}

Responde como SEA siguiendo tu personalidad.
No menciones porcentajes ni detalles técnicos del modelo.
Prioriza que el estudiante se sienta escuchado y quiera continuar hablando.
"""

        respuesta = client.responses.create(
            model="gpt-5.4-mini",
            instructions=PERSONALIDAD_CHATBOT,
            input=entrada_usuario
        )

        return jsonify({
            "respuesta": respuesta.output_text,
            "emocion": analisis["emocion"],
            "intencion": analisis["intencion"],
            "nivel_emocional": analisis["nivel_emocional"],
            "puntaje_confianza": analisis["puntaje_confianza"],
            "recomendacion": recomendacion,
            "categoria": analisis["intencion"],
            "nivel_alerta": analisis["nivel_emocional"]
        })

    except Exception as e:
        return jsonify({
            "respuesta": "Hubo un problema al conectar con el chatbot. Intenta nuevamente.",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))