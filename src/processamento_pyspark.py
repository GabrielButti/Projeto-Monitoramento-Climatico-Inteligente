from pyspark.sql import SparkSession
from pyspark.sql.functions import to_date, hour, avg, min as spark_min, max as spark_max
import os 
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

PG_USER = os.getenv("PG_USER")
PG_PASS = os.getenv("PG_PASS")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")

jdbc_url = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"
db_propriedades = {
    "user": PG_USER,
    "password": PG_PASS,
    "driver": "org.postgresql.Driver"
}

spark = SparkSession.builder.appName("ProcessamentoClimatico").config("spark.hadoop.hadoop.native.io", "false").getOrCreate()

# Ler dados do PostgreSQL

df = spark.read.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "clima_horario") \
    .option("user", PG_USER) \
    .option("password", PG_PASS) \
    .option("driver", "org.postgresql.Driver") \
    .load()

# Tratar nulos e criar colunas auxiliares

df = df.dropna(subset=["temperature_2m"]) \
       .withColumn("date", to_date("time")) \
       .withColumn("hour", hour("time"))

# Conversão de time para timestamp e criação de colunas auxiliares

df = df.withColumn("date", to_date("time")).withColumn("hour", hour("time"))

# Agregações Horárias e Diárias

media_horaria = df.groupBy("date", "hour").agg(
    avg("temperature_2m").alias("media_temp"),
    spark_min("temperature_2m").alias("min_temp"),
    spark_max("temperature_2m").alias("max_temp"),
).orderBy("date", "hour")

media_diaria = df.groupBy("date").agg(
    avg("temperature_2m").alias("media_temp"),
    spark_min("temperature_2m").alias("min_temp"),
    spark_max("temperature_2m").alias("max_temp"),
).orderBy("date")

# Salvando Agregações como CSV e no Banco de Dados

os.makedirs("data/processed", exist_ok=True)
media_horaria.coalesce(1).write.mode("overwrite").option("header", "true").csv("data/processed/media_horaria")
media_diaria.coalesce(1).write.mode("overwrite").option("header", "true").csv("data/processed/media_diaria")

media_horaria.write.jdbc(url=jdbc_url, table="media_horaria", mode="overwrite", properties=db_propriedades)
media_diaria.write.jdbc(url=jdbc_url, table="media_diaria", mode="overwrite", properties=db_propriedades)

print("Agregações horárias e diárias salvas com sucesso em CSV e no banco de dados.")
