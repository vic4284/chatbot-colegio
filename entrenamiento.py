import pandas as pd
import joblib
import re
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support
)


# =========================
# RUTAS DEL PROYECTO
# =========================

RUTA_DATASET = "dataset/dataset_limpio.csv"
CARPETA_MODELOS = "modelos"
CARPETA_RESULTADOS = "resultados_modelo"

os.makedirs(CARPETA_MODELOS, exist_ok=True)
os.makedirs(CARPETA_RESULTADOS, exist_ok=True)


# =========================
# LIMPIEZA DE TEXTO
# =========================

def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r'[^\w\s+\-*/]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


# =========================
# ENTRENAMIENTO Y EVALUACIÓN
# =========================

def entrenar_modelo(X_vect, y, nombre_modelo):
    X_train, X_test, y_train, y_test = train_test_split(
        X_vect,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.value_counts().min() >= 2 else None
    )

    modelo = LogisticRegression(
        max_iter=3000,
        class_weight="balanced"
    )

    modelo.fit(X_train, y_train)

    predicciones = modelo.predict(X_test)

    accuracy = accuracy_score(y_test, predicciones)

    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_test,
        predicciones,
        average="macro",
        zero_division=0
    )

    reporte = classification_report(
        y_test,
        predicciones,
        zero_division=0
    )

    matriz = confusion_matrix(y_test, predicciones)

    joblib.dump(modelo, f"{CARPETA_MODELOS}/{nombre_modelo}.pkl")

    with open(f"{CARPETA_RESULTADOS}/reporte_{nombre_modelo}.txt", "w", encoding="utf-8") as archivo:
        archivo.write(f"REPORTE DEL MODELO: {nombre_modelo}\n")
        archivo.write("=" * 60 + "\n\n")
        archivo.write(f"Accuracy: {round(accuracy * 100, 2)} %\n")
        archivo.write(f"Precision macro: {round(precision_macro * 100, 2)} %\n")
        archivo.write(f"Recall macro: {round(recall_macro * 100, 2)} %\n")
        archivo.write(f"F1-score macro: {round(f1_macro * 100, 2)} %\n\n")
        archivo.write("Reporte de clasificación:\n")
        archivo.write(reporte)
        archivo.write("\n\nMatriz de confusión:\n")
        archivo.write(str(matriz))

    print(f"Modelo {nombre_modelo} entrenado correctamente")
    print(f"Accuracy: {round(accuracy * 100, 2)} %")
    print(f"Precision macro: {round(precision_macro * 100, 2)} %")
    print(f"Recall macro: {round(recall_macro * 100, 2)} %")
    print(f"F1-score macro: {round(f1_macro * 100, 2)} %")
    print("Reporte guardado en:", f"{CARPETA_RESULTADOS}/reporte_{nombre_modelo}.txt")
    print("------------------------------------")

    return {
        "modelo": nombre_modelo,
        "accuracy": accuracy,
        "precision": precision_macro,
        "recall": recall_macro,
        "f1_score": f1_macro
    }


# =========================
# CARGA DEL DATASET
# =========================

df = pd.read_csv(RUTA_DATASET, encoding="utf-8-sig")

df = df.dropna(subset=[
    "pregunta",
    "emocion",
    "intencion",
    "nivel_emocional",
    "recomendacion"
])


# =========================
# PREPARACIÓN DE DATOS
# =========================

df["pregunta"] = df["pregunta"].apply(limpiar_texto)
df["emocion"] = df["emocion"].astype(str).str.strip().str.upper()
df["intencion"] = df["intencion"].astype(str).str.strip()
df["nivel_emocional"] = df["nivel_emocional"].astype(str).str.strip().str.upper()

X = df["pregunta"]


# =========================
# VECTORIZACIÓN TF-IDF
# =========================

vectorizador = FeatureUnion([
    ("tfidf_palabras", TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        strip_accents="unicode",
        sublinear_tf=True
    )),
    ("tfidf_caracteres", TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        strip_accents="unicode",
        sublinear_tf=True
    ))
])

X_vect = vectorizador.fit_transform(X)

joblib.dump(vectorizador, f"{CARPETA_MODELOS}/vectorizador.pkl")


# =========================
# ENTRENAMIENTO DE MODELOS
# =========================

resultado_emocion = entrenar_modelo(
    X_vect,
    df["emocion"],
    "modelo_emocion"
)

resultado_intencion = entrenar_modelo(
    X_vect,
    df["intencion"],
    "modelo_intencion"
)

resultado_nivel = entrenar_modelo(
    X_vect,
    df["nivel_emocional"],
    "modelo_nivel_emocional"
)


# =========================
# RESUMEN FINAL
# =========================

resultados = pd.DataFrame([
    resultado_emocion,
    resultado_intencion,
    resultado_nivel
])

resultados["accuracy"] = (resultados["accuracy"] * 100).round(2)
resultados["precision"] = (resultados["precision"] * 100).round(2)
resultados["recall"] = (resultados["recall"] * 100).round(2)
resultados["f1_score"] = (resultados["f1_score"] * 100).round(2)

resultados.to_csv(
    f"{CARPETA_RESULTADOS}/resumen_metricas_modelos.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Entrenamiento finalizado correctamente")
print("Resumen de métricas:")
print(resultados)
print("Archivo resumen guardado en:", f"{CARPETA_RESULTADOS}/resumen_metricas_modelos.csv")