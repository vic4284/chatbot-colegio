import joblib
import re

# Cargar modelo y vectorizador
modelo = joblib.load("modelo_chatbot.pkl")
vectorizador = joblib.load("vectorizador.pkl")

def limpiar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto

while True:
    mensaje = input("Escribe un mensaje (o escribe salir): ")

    if mensaje.lower() == "salir":
        print("Programa finalizado")
        break

    mensaje_limpio = limpiar_texto(mensaje)
    mensaje_vect = vectorizador.transform([mensaje_limpio])
    prediccion = modelo.predict(mensaje_vect)

    print("Categoría detectada:", prediccion[0])