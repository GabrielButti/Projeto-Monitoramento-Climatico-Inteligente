import os
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do banco de dados

PG_USER = os.getenv("PG_USER")
PG_PASS = os.getenv("PG_PASS")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")

# Conexão SQLAlchemy

conn_str = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
engine = create_engine(conn_str, echo = False)

def buscar_historico(lat=-23.55, lon=-46.63, start="2025-08-01", end="2025-09-17"):
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}&start_date={start}&end_date={end}"
        "&hourly=temperature_2m,relativehumidity_2m,precipitation,windspeed_10m"
        "&timezone=America%2FSao_Paulo"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    dados = r.json()["hourly"]
    df = pd.DataFrame(dados)
    df["time"] = pd.to_datetime(df["time"])
    df["collected_at"] = datetime.utcnow()
    cols = ["time", "temperature_2m", "relativehumidity_2m", "precipitation", "windspeed_10m", "collected_at"]
    return df[cols]

def criando_tabela(engine):
    criar_sql = """
    CREATE TABLE IF NOT EXISTS clima_horario (
        time TIMESTAMP WITHOUT TIME ZONE,
        temperature_2m DOUBLE PRECISION,
        relativehumidity_2m DOUBLE PRECISION,
        precipitation DOUBLE PRECISION,
        windspeed_10m DOUBLE PRECISION,
        collected_at TIMESTAMP WITHOUT TIME ZONE,
        PRIMARY KEY (time)
    );
    """
    with engine.begin() as conn:
        conn.execute(text(criar_sql))

def sobrescrever_dataframe(df, engine):
    tabela_temp = "clima_temp"
    df.to_sql(tabela_temp, engine, if_exists = 'replace', index = False)
    sobrepor_sql = f"""
    INSERT INTO clima_horario (time, temperature_2m, relativehumidity_2m, precipitation, windspeed_10m, collected_at)
    SELECT time, temperature_2m, relativehumidity_2m, precipitation, windspeed_10m, collected_at
    FROM {tabela_temp}
    ON CONFLICT (time) DO UPDATE SET
        temperature_2m = EXCLUDED.temperature_2m,
        relativehumidity_2m = EXCLUDED.relativehumidity_2m,
        precipitation = EXCLUDED.precipitation,
        windspeed_10m = EXCLUDED.windspeed_10m,
        collected_at = EXCLUDED.collected_at;
    DROP TABLE IF EXISTS {tabela_temp};
    """
    with engine.begin() as conn:
        conn.execute(text(sobrepor_sql))

if __name__ == "__main__":
    # Histórico dos últimos 60 dias
    inicio = (datetime.utcnow() - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
    fim = datetime.utcnow().strftime("%Y-%m-%d")

    df_hist = buscar_historico(start=inicio, end=fim)
    criando_tabela(engine)
    sobrescrever_dataframe(df_hist, engine)
    print(f"Dados históricos de {inicio} a {fim} armazenados com sucesso.")
