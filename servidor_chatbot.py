from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PERSONALIDAD_CHATBOT = """
Eres MEA EL MEON, un chatbot emocional y académico para estudiantes de secundaria.

"""

@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "estado": "activo",
        "mensaje": "Servidor del chatbot SEA funcionando correctamente"
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

        respuesta = client.responses.create(
            model="gpt-5.4-mini",
            instructions=PERSONALIDAD_CHATBOT,
            input=mensaje
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