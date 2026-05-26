import pandas as pd
import joblib
import re
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


RUTA_DATASET = "dataset/dataset_limpio.csv"
CARPETA_MODELOS = "modelos"

os.makedirs(CARPETA_MODELOS, exist_ok=True)


def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r'[^\w\s+\-*/]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def entrenar_modelo(df, columna_objetivo, nombre_modelo, vectorizador):
    df_temp = df.dropna(subset=["pregunta", columna_objetivo])

    X = df_temp["pregunta"]
    y = df_temp[columna_objetivo].astype(str).str.strip()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.value_counts().min() >= 2 else None
    )

    X_train_vect = vectorizador.fit_transform(X_train)
    X_test_vect = vectorizador.transform(X_test)

    modelo = LogisticRegression(
        max_iter=2000,
        class_weight="balanced"
    )

    modelo.fit(X_train_vect, y_train)

    predicciones = modelo.predict(X_test_vect)
    precision = accuracy_score(y_test, predicciones)

    joblib.dump(modelo, f"{CARPETA_MODELOS}/{nombre_modelo}.pkl")

    print(f"Modelo {nombre_modelo} entrenado correctamente")
    print(f"Precisión {nombre_modelo}: {round(precision * 100, 2)} %")
    print("------------------------------------")

    return precision


df = pd.read_csv(RUTA_DATASET, encoding="utf-8-sig")

df = df.dropna(subset=[
    "pregunta",
    "emocion",
    "intencion",
    "nivel_emocional",
    "recomendacion"
])

df["pregunta"] = df["pregunta"].apply(limpiar_texto)

df["emocion"] = df["emocion"].astype(str).str.strip().str.upper()
df["intencion"] = df["intencion"].astype(str).str.strip()
df["nivel_emocional"] = df["nivel_emocional"].astype(str).str.strip().str.upper()
df["recomendacion"] = df["recomendacion"].astype(str).str.strip()


vectorizador = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=1,
    strip_accents="unicode",
    sublinear_tf=True
)

joblib.dump(vectorizador, f"{CARPETA_MODELOS}/vectorizador.pkl")


# Modelo 1: emoción detectada
precision_emocion = entrenar_modelo(
    df,
    "emocion",
    "modelo_emocion",
    vectorizador
)

# Modelo 2: intención detectada
precision_intencion = entrenar_modelo(
    df,
    "intencion",
    "modelo_intencion",
    vectorizador
)

# Modelo 3: nivel emocional
precision_nivel = entrenar_modelo(
    df,
    "nivel_emocional",
    "modelo_nivel_emocional",
    vectorizador
)


print("Entrenamiento finalizado correctamente")
print("Resumen de precisión:")
print("Emoción:", round(precision_emocion * 100, 2), "%")
print("Intención:", round(precision_intencion * 100, 2), "%")
print("Nivel emocional:", round(precision_nivel * 100, 2), "%")