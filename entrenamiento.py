import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score

df = pd.read_csv("dataset_limpio.csv")

X = df["pregunta"]
y = df["categoria"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

vectorizador = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=1
)

X_train_vect = vectorizador.fit_transform(X_train)
X_test_vect = vectorizador.transform(X_test)

modelo = LinearSVC()
modelo.fit(X_train_vect, y_train)

predicciones = modelo.predict(X_test_vect)
precision = accuracy_score(y_test, predicciones)

joblib.dump(modelo, "modelo_chatbot.pkl")
joblib.dump(vectorizador, "vectorizador.pkl")

print("Modelo entrenado correctamente")
print("Precisión:", round(precision * 100, 2), "%")