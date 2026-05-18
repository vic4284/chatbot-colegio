import sys
import joblib
import pandas as pd
import json
import re

mensaje = sys.argv[1]

modelo = joblib.load("modelo_chatbot.pkl")
vectorizador = joblib.load("vectorizador.pkl")
df = pd.read_csv("dataset_limpio.csv")

def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto

def construir_respuesta_humana(fila):
    if "respuesta_final" in df.columns:
        return str(fila["respuesta_final"])

    respuesta = str(fila["respuesta"]) if "respuesta" in df.columns else ""
    recomendacion = str(fila["recomendacion"]) if "recomendacion" in df.columns else ""
    pregunta = str(fila["pregunta_seguimiento"]) if "pregunta_seguimiento" in df.columns else ""

    texto = respuesta

    if recomendacion != "" and recomendacion.lower() != "nan":
        texto += "\n\nRecomendación: " + recomendacion

    if pregunta != "" and pregunta.lower() != "nan":
        texto += "\n\n" + pregunta

    return texto

mensaje_limpio = limpiar_texto(mensaje)
mensaje_vect = vectorizador.transform([mensaje_limpio])
categoria = modelo.predict(mensaje_vect)[0]

respuestas_categoria = df[df["categoria"] == categoria]

if respuestas_categoria.empty:
    respuesta = "No entendí bien tu mensaje. Puedes explicármelo con otras palabras. Estoy aquí para escucharte."
    nivel_alerta = "BAJA"
    emocion = "NEUTRAL"
else:
    fila = respuestas_categoria.sample(1).iloc[0]
    respuesta = construir_respuesta_humana(fila)
    nivel_alerta = fila["nivel_alerta"] if "nivel_alerta" in df.columns else "BAJA"
    emocion = fila["emocion_detectada"] if "emocion_detectada" in df.columns else "NEUTRAL"

resultado = {
    "success": True,
    "respuesta": respuesta,
    "categoria": categoria,
    "emocion_detectada": emocion,
    "nivel_alerta": nivel_alerta
}

print(json.dumps(resultado, ensure_ascii=False))