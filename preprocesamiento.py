import pandas as pd
import re

df = pd.read_csv("dataset_chatbot_registros.csv")

def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto

df["pregunta"] = df["pregunta"].apply(limpiar_texto)

df.to_csv("dataset_limpio.csv", index=False)

print("Dataset limpio generado correctamente")