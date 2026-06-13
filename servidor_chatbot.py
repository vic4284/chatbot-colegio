# Importaciones principales

from flask import Flask, request, jsonify
from openai import OpenAI

from conexion.base_datos import guardar_analisis_emocional, obtener_datos_estudiante
from nlp.reglas_emocionales import analizar_por_reglas
from memoria.memoria_chatbot import (
    guardar_mensaje_usuario,
    guardar_respuesta_bot,
    construir_historial_chatbot
)

import os
import re
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity


# Inicialización del servidor Flask

app = Flask(__name__)

# Cliente de OpenAI para generar respuestas conversacionales
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Carga de modelos entrenados

vectorizador = joblib.load("modelos/vectorizador.pkl")
modelo_emocion = joblib.load("modelos/modelo_emocion.pkl")
modelo_intencion = joblib.load("modelos/modelo_intencion.pkl")
modelo_nivel = joblib.load("modelos/modelo_nivel_emocional.pkl")

# Dataset usado como referencia para comparación por similitud
df_dataset = pd.read_csv("dataset/dataset_limpio.csv", encoding="utf-8-sig")


# Limpieza básica del texto

def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r'[^\w\s+\-*/]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


# Preparación del dataset para similitud

df_dataset["pregunta"] = df_dataset["pregunta"].apply(limpiar_texto)
matriz_dataset = vectorizador.transform(df_dataset["pregunta"])


# Calcula el nivel de seguridad del modelo

def obtener_confianza(modelo, texto_vectorizado):
    probabilidades = modelo.predict_proba(texto_vectorizado)[0]
    confianza = float(np.max(probabilidades))
    return round(confianza * 100, 2)


# Busca el mensaje más parecido dentro del dataset

def analizar_por_similitud(mensaje_vectorizado):
    similitudes = cosine_similarity(mensaje_vectorizado, matriz_dataset)[0]
    indice = int(np.argmax(similitudes))
    similitud = float(similitudes[indice])

    if similitud >= 0.45:
        fila = df_dataset.iloc[indice]

        return {
            "emocion": str(fila["emocion"]).strip().upper(),
            "intencion": str(fila["intencion"]).strip(),
            "nivel_emocional": str(fila["nivel_emocional"]).strip().upper(),
            "puntaje_confianza": round(similitud * 100, 2),
            "origen": "similitud_dataset"
        }

    return None


# Analiza el mensaje usando reglas, modelos NLP y similitud

def analizar_mensaje(mensaje):
    # Primero se aplican reglas para casos claros o prioritarios
    resultado_regla = analizar_por_reglas(mensaje)

    if resultado_regla:
        return resultado_regla

    # Si no hay regla aplicable, se usa el modelo entrenado
    mensaje_limpio = limpiar_texto(mensaje)
    mensaje_vectorizado = vectorizador.transform([mensaje_limpio])

    emocion = modelo_emocion.predict(mensaje_vectorizado)[0]
    intencion = modelo_intencion.predict(mensaje_vectorizado)[0]
    nivel_emocional = modelo_nivel.predict(mensaje_vectorizado)[0]

    # Confianza individual de cada clasificación
    confianza_emocion = obtener_confianza(modelo_emocion, mensaje_vectorizado)
    confianza_intencion = obtener_confianza(modelo_intencion, mensaje_vectorizado)
    confianza_nivel = obtener_confianza(modelo_nivel, mensaje_vectorizado)

    # Confianza general del análisis
    puntaje_confianza = round(
        (confianza_emocion + confianza_intencion + confianza_nivel) / 3,
        2
    )

    # Si la confianza es baja, se intenta comparar con ejemplos del dataset
    if puntaje_confianza < 85:
        resultado_similitud = analizar_por_similitud(mensaje_vectorizado)

        if resultado_similitud:
            return resultado_similitud

    return {
        "emocion": emocion,
        "intencion": intencion,
        "nivel_emocional": nivel_emocional,
        "puntaje_confianza": puntaje_confianza,
        "origen": "modelo"
    }


# Genera una recomendación según emoción y nivel detectado

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


# Instrucciones de comportamiento del chatbot

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


# Ruta para verificar que el servidor está activo

@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "estado": "activo",
        "mensaje": "Servidor SEA funcionando con nombre, genero, memoria conversacional, reglas, NLP y OpenAI001_ULTIMOO"
    })


# Endpoint principal del chatbot

@app.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        data = request.get_json()

        if data is None:
            return jsonify({
                "respuesta": "No se recibió información válida.",
                "error": "JSON vacío o incorrecto"
            }), 400

        mensaje = data.get("mensaje", "").strip()
        id_usuario = data.get("id_usuario")

        nombre_estudiante = "Estudiante"
        genero_estudiante = "NO_ESPECIFICADO"

        # Obtener nombre y género desde la tabla estudiantes
        if id_usuario:
            try:
                datos_estudiante = obtener_datos_estudiante(id_usuario)

                if datos_estudiante:
                    nombres = datos_estudiante.get("nombres") or ""
                    apellidos = datos_estudiante.get("apellidos") or ""
                    genero_estudiante = datos_estudiante.get("genero") or "NO_ESPECIFICADO"

                    nombre_estudiante = f"{nombres} {apellidos}".strip()

                    if not nombre_estudiante:
                        nombre_estudiante = "Estudiante"

            except Exception:
                pass

        # Validación cuando el estudiante no envía texto
        if not mensaje:
            return jsonify({
                "respuesta": "Escribe un mensaje para poder ayudarte.",
                "emocion": "NEUTRAL",
                "intencion": "mensaje_vacio",
                "nivel_emocional": "ESTABLE",
                "puntaje_confianza": 0,
                "recomendacion": "Solicitar al estudiante que escriba un mensaje.",
                "categoria": "general",
                "nivel_alerta": "ESTABLE",
                "estado_seguimiento": "PENDIENTE",
                "origen_analisis": "validacion",
                "guardado_bd": False,
                "mensaje_bd": "No se guardó porque el mensaje estaba vacío",
                "nombre_estudiante": nombre_estudiante,
                "genero_estudiante": genero_estudiante
            })

        # Guarda el mensaje para mantener memoria de conversación
        try:
            guardar_mensaje_usuario(id_usuario, mensaje)
        except Exception:
            pass

        # Obtiene el historial reciente del estudiante
        try:
            historial_chatbot = construir_historial_chatbot(id_usuario, limite=10)
        except Exception:
            historial_chatbot = ""

        # Análisis emocional del mensaje actual
        analisis = analizar_mensaje(mensaje)

        # Recomendación interna según el análisis
        recomendacion = generar_recomendacion(
            analisis["emocion"],
            analisis["nivel_emocional"]
        )

        guardado_bd = False
        mensaje_bd = "No se recibió id_usuario"

        # Guarda el análisis emocional para el seguimiento psicológico
        if id_usuario:
            try:
                guardado_bd, mensaje_bd = guardar_analisis_emocional(
                    id_usuario=id_usuario,
                    emocion=analisis["emocion"],
                    intencion=analisis["intencion"],
                    nivel_emocional=analisis["nivel_emocional"],
                    puntaje_confianza=analisis["puntaje_confianza"],
                    recomendacion=recomendacion
                )
            except Exception as error_bd:
                guardado_bd = False
                mensaje_bd = f"Error al guardar en BD: {str(error_bd)}"

        # Información enviada a OpenAI para generar la respuesta natural
        entrada_usuario = f"""
Datos del estudiante:
- Nombre: {nombre_estudiante}
- Género: {genero_estudiante}

Historial reciente de conversación:
{historial_chatbot}

Mensaje actual del estudiante:
{mensaje}

Análisis emocional detectado:
- Emoción: {analisis["emocion"]}
- Intención: {analisis["intencion"]}
- Nivel emocional: {analisis["nivel_emocional"]}
- Recomendación interna: {recomendacion}

Responde como SEA siguiendo tu personalidad.
Usa el historial solo para mantener continuidad de la conversación.
Puedes llamar al estudiante por su nombre cuando sea natural.
Adapta el lenguaje según su género cuando corresponda.
No menciones porcentajes ni detalles técnicos del modelo.
Prioriza que el estudiante se sienta escuchado y quiera continuar hablando.
"""

        # Genera la respuesta conversacional del chatbot
        respuesta = client.responses.create(
            model="gpt-5.4-mini",
            instructions=PERSONALIDAD_CHATBOT,
            input=entrada_usuario
        )

        respuesta_texto = respuesta.output_text

        # Guarda la respuesta del chatbot en la memoria
        try:
            guardar_respuesta_bot(id_usuario, respuesta_texto)
        except Exception:
            pass

        return jsonify({
            "respuesta": respuesta_texto,
            "emocion": analisis["emocion"],
            "intencion": analisis["intencion"],
            "nivel_emocional": analisis["nivel_emocional"],
            "puntaje_confianza": analisis["puntaje_confianza"],
            "recomendacion": recomendacion,
            "categoria": analisis["intencion"],
            "nivel_alerta": analisis["nivel_emocional"],
            "estado_seguimiento": "PENDIENTE",
            "origen_analisis": analisis.get("origen", "modelo"),
            "guardado_bd": guardado_bd,
            "mensaje_bd": mensaje_bd,
            "nombre_estudiante": nombre_estudiante,
            "genero_estudiante": genero_estudiante
        })

    except Exception as e:
        return jsonify({
            "respuesta": "Hubo un problema al conectar con el chatbot. Intenta nuevamente.",
            "error": str(e)
        }), 500


# Ejecución local del servidor

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))