from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "estado": "activo",
        "mensaje": "Servidor del chatbot SEA funcionando correctamente002"
    })

@app.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        data = request.get_json()
        mensaje = data.get("mensaje", "").strip()

        if not mensaje:
            return jsonify({
                "respuesta": "Escribe un mensaje para poder ayudarte.",
                "categoria": "general",
                "nivel_alerta": "bajo"
            })

        entrada_usuario = f"""
Mensaje del estudiante:
{mensaje}

Responde como SEA siguiendo tu personalidad.
Prioriza que la conversación continúe y que el estudiante se sienta escuchado.
"""

        respuesta = client.responses.create(
            model="gpt-5.4-mini",
            instructions=PERSONALIDAD_CHATBOT,
            input=entrada_usuario
        )

        return jsonify({
            "respuesta": respuesta.output_text,
            "categoria": "openai",
            "nivel_alerta": "pendiente"
        })

    except Exception as e:
        return jsonify({
            "respuesta": "Hubo un problema al conectar con el chatbot. Intenta nuevamente.",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))