# src/app.py
import streamlit as st
import pandas as pd
import joblib
from prophet.plot import plot_plotly
import plotly.express as px
import glob

st.set_page_config(layout="wide", page_title="Monitoramento Climático")

st.title("Monitoramento Climático Inteligente — Previsão Horária")

# Carrega dados processados (último CSV)
csv_horario = glob.glob("data/processed/media_horaria/*.csv")
if not csv_horario:
    st.error("Nenhum dado processado encontrado. Rode process_pyspark.py")
else:
    df = pd.read_csv(csv_horario[0])
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["hour"].astype(str) + ":00:00")
    st.dataframe(df.tail(10))

# Carrega modelo
try:
    m = joblib.load("models/previsao_horaria.pkl")
    future = m.make_future_dataframe(periods=48, freq="H")
    forecast = m.predict(future)
    fig = plot_plotly(m, forecast)
    st.plotly_chart(fig, use_container_width=True)

    st.write("Previsão próxima 24h")
    st.dataframe(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(24))
except Exception as e:
    st.error(f"Erro ao carregar modelo: {e}")

# Exibir tendências e estatísticas
if 'df' in locals():
    st.subheader("Estatísticas diárias (últimos 30 dias)")
    daily = df.groupby("date").agg({"media_temp": "mean", "min_temp": "min", "max_temp":"max"}).reset_index()
    fig2 = px.line(daily, x="date", y="media_temp", title="Temperatura média diária")
    st.plotly_chart(fig2, use_container_width=True)
