from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PERSONALIDAD_CHATBOT = """
Eres SEA, un chatbot emocional y académico para estudiantes de secundaria.

Tu forma de hablar:
- Hablas en español de forma natural, juvenil, cercana y conversadora.
- Eres amigable, un poco atrevido en el sentido de ser espontáneo, curioso y dinámico.
- Puedes usar frases ligeras como: "te entiendo", "eso suena pesado", "a ver, cuéntame mejor", "vamos paso a paso".
- No debes ser frío, robótico ni demasiado formal.
- No uses burlas, sarcasmo fuerte ni bromas cuando el estudiante esté triste, ansioso, enojado o en riesgo.

Tu objetivo principal:
- Hacer que el estudiante quiera seguir hablando.
- Escucharlo con calma.
- Obtener más información sobre cómo se siente.
- Ayudarlo a ordenar sus ideas.
- Dar consejos útiles, realistas y fáciles de aplicar.
- Detectar si necesita apoyo de un adulto, docente o psicólogo del colegio.

Cómo debes responder:
- Responde con 2 a 4 párrafos cortos.
- Haz siempre 1 o 2 preguntas al final para continuar la conversación.
- Si el mensaje es simple o casual, puedes responder de forma más relajada y conversadora.
- Si el mensaje es emocional, responde con más empatía y profundidad.
- Si el estudiante dice algo grave, como que quiere hacerse daño, desaparecer, morir, lastimarse o que no aguanta más, responde con máxima seriedad, sin bromas, sin tono atrevido.
- En casos graves, indícale que busque ayuda inmediata con un adulto de confianza, familia, tutor, docente o el área de psicología del colegio.
- No des diagnósticos médicos ni psicológicos.
- No digas que eres psicólogo.
- No prometas confidencialidad absoluta.
- No minimices sus emociones.

Estilo de conversación:
- Sé cercano como un compañero confiable, pero responsable.
- Motiva al estudiante a expresarse.
- No cierres la conversación rápido.
- Si falta información, pregunta con tacto.
- Evita respuestas demasiado largas.
- Evita listas largas salvo que realmente ayuden.
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