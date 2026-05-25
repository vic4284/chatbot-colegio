import pandas as pd
import joblib
import re

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r'[^\w\s+\-*/]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


df = pd.read_csv("dataset_limpio.csv", encoding="utf-8-sig")
df = df.dropna(subset=["pregunta", "categoria"])

df["pregunta"] = df["pregunta"].apply(limpiar_texto)
df["categoria"] = df["categoria"].astype(str).str.strip()

X = df["pregunta"]
y = df["categoria"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y if y.value_counts().min() >= 2 else None
)

vectorizador = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=1,
    strip_accents="unicode",
    sublinear_tf=True
)

X_train_vect = vectorizador.fit_transform(X_train)
X_test_vect = vectorizador.transform(X_test)

modelo = LogisticRegression(
    max_iter=1500,
    class_weight="balanced"
)

modelo.fit(X_train_vect, y_train)

predicciones = modelo.predict(X_test_vect)
precision = accuracy_score(y_test, predicciones)

joblib.dump(modelo, "modelo_chatbot.pkl")
joblib.dump(vectorizador, "vectorizador.pkl")

print("Modelo entrenado correctamente")
print("Precisión:", round(precision * 100, 2), "%")