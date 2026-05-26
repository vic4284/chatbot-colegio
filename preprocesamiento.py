import pandas as pd
import re
import os

# Rutas
RUTA_ENTRADA = "dataset/dataset_chatbot_registros.csv"
RUTA_SALIDA = "dataset/dataset_limpio.csv"

# Leer dataset original
df = pd.read_csv(RUTA_ENTRADA, encoding="utf-8-sig")

def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r'[^\w\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto

# Limpiar columna pregunta
df["pregunta"] = df["pregunta"].apply(limpiar_texto)

# Limpiar espacios en columnas importantes
df["emocion"] = df["emocion"].astype(str).str.strip().str.upper()
df["intencion"] = df["intencion"].astype(str).str.strip()
df["nivel_emocional"] = df["nivel_emocional"].astype(str).str.strip().str.upper()
df["recomendacion"] = df["recomendacion"].astype(str).str.strip()

# Eliminar filas vacías importantes
df = df.dropna(subset=["pregunta", "emocion", "intencion", "nivel_emocional", "recomendacion"])

# Crear carpeta dataset si no existe
os.makedirs("dataset", exist_ok=True)

# Guardar dataset limpio
df.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")

print("Dataset limpio generado correctamente")
print("Total de registros:", len(df))