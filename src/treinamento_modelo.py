import pandas as pd
from prophet import Prophet
import joblib
import glob
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import os

# Ativar pasta onde Spark salvou os arquivos CSV

csv_horario = glob.glob("data/processed/media_horaria/part-*.csv")[0]
df = pd.read_csv(csv_horario)
df["ds"] = pd.to_datetime(df["date"] + " " + df["hour"].astype(str) + ":00:00")
df = df[["ds", "media_temp"]].rename(columns={"media_temp": "y"})

# Ordenar cronologicamente
df = df.sort_values('ds')

# Treinamento do Modelo Histórico

model = Prophet(daily_seasonality=True, weekly_seasonality=True)
model.fit(df)

# Salvando o Modelo Treinado
joblib.dump(model, "models/previsao_horaria.pkl")
