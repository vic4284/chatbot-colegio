from flask import Flask, request, jsonify
from openai import OpenAI
import os

# Inicialización del servidor Flask
app = Flask(__name__)

# Conexión con OpenAI mediante variable de entorno
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Personalidad principal del chatbot SEA
PERSONALIDAD_CHATBOT = """
Eres SEA, un chatbot emocional y académico para estudiantes de secundaria.

Tu forma de hablar:
- Hablas en español de forma natural, juvenil, cercana y conversadora.
- Eres amigable, espontáneo y dinámico 😄
- Puedes usar emojis de forma moderada para expresar cercanía y emociones.
- Usa emojis como 😊😅🙌✨🤔💙👍 dependiendo del contexto.
- NO abuses de emojis.
- NO uses emojis de burla o exagerados.
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
- Si el mensaje es casual, puedes responder de forma más relajada 😄
- Si el estudiante está triste, ansioso o frustrado, responde con empatía 💙
- Si el estudiante menciona autolesiones, suicidio o situaciones graves:
  - responde con máxima seriedad
  - evita bromas
  - evita emojis innecesarios
  - recomienda buscar ayuda inmediata de un adulto, tutor o psicólogo escolar

Importante:
- No des diagnósticos médicos o psicológicos.
- No digas que eres psicólogo.
- No minimices emociones.
- No finalices rápido la conversación.
- Motiva siempre al estudiante a seguir expresándose.

Estilo:
- Conversador
- Cercano
- Natural
- Emocionalmente inteligente
- Responsable
"""

# Ruta principal para verificar funcionamiento del servidor
@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "estado": "activo",
        "mensaje": "Servidor del chatbot SEA funcionando correctamente002"
    })

# Endpoint principal del chatbot
@app.route("/chatbot", methods=["POST"])
def chatbot():

    try:

        # Recepción del mensaje desde Android
        data = request.get_json()
        mensaje = data.get("mensaje", "").strip()

        # Validación de mensaje vacío
        if not mensaje:
            return jsonify({
                "respuesta": "Escribe un mensaje para poder ayudarte.",
                "categoria": "general",
                "nivel_alerta": "bajo"
            })

        # Contexto enviado al modelo
        entrada_usuario = f"""
Mensaje del estudiante:
{mensaje}

Responde como SEA siguiendo tu personalidad.
Prioriza que la conversación continúe y que el estudiante se sienta escuchado.
"""

        # Generación de respuesta mediante OpenAI
        respuesta = client.responses.create(
            model="gpt-5.4-mini",
            instructions=PERSONALIDAD_CHATBOT,
            input=entrada_usuario
        )

        # Respuesta enviada a Android
        return jsonify({
            "respuesta": respuesta.output_text,
            "categoria": "openai",
            "nivel_alerta": "pendiente"
        })

    # Manejo general de errores
    except Exception as e:

        return jsonify({
            "respuesta": "Hubo un problema al conectar con el chatbot. Intenta nuevamente.",
            "error": str(e)
        }), 500


# Ejecución principal del servidor Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))