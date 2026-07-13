# -*- coding: utf-8 -*-
"""
Modelo predictivo de casos de dengue con Spark MLlib
====================================================
Complementa el ETL (etl_dengue_spark.py) con un componente de MINERIA DE DATOS
(Unidad 4 del silabo) y uso de la libreria de Machine Learning distribuida de
Apache Spark (MLlib), en linea con el articulo base (Sylvestre et al., 2022) que
identifica a los metodos data-driven -y en particular Random Forest- como los
mas usados para la prediccion y vigilancia del dengue.

Enfoque:
    Serie de tiempo semanal nacional (casos por anio-semana). Se construyen
    caracteristicas de estacionalidad (seno/coseno de la semana) y rezagos
    (lags 1, 2, 4 y 52 semanas), con el objetivo en escala logaritmica.
    Se entrena un Random Forest Regressor para pronosticar los casos de la
    semana. Validacion out-of-time: entrenamiento hasta 2023, prueba en 2024.

Salidas:
    02_datos_procesados/ml_predicciones.csv   -> real vs. predicho (test)
    02_datos_procesados/ml_metricas.json      -> RMSE, MAE, R2, importancias
"""

import os
import json
import math
import glob
import shutil
import tempfile

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator

BASE = os.environ.get("PROJ_BASE", ".")
OUT_DIR = os.path.join(BASE, "02_datos_procesados")
FACT = os.path.join(OUT_DIR, "fact_dengue.csv")


def write_single_csv(sdf, path):
    tmp = tempfile.mkdtemp(prefix="sparkout_")
    sdf.coalesce(1).write.mode("overwrite").option("header", True).csv(tmp)
    part = glob.glob(os.path.join(tmp, "part-*.csv"))[0]
    shutil.copyfile(part, path)
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    spark = (SparkSession.builder.appName("ML_Dengue_Peru")
             .master("local[*]").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")

    # 1. Serie semanal nacional a partir de la tabla de hechos
    fact = spark.read.option("header", True).csv(FACT)
    serie = (fact.groupBy("ano", "semana")
             .agg(F.sum(F.col("casos").cast("int")).alias("casos"))
             .withColumn("ano", F.col("ano").cast("int"))
             .withColumn("semana", F.col("semana").cast("int"))
             .orderBy("ano", "semana"))

    serie = serie.withColumn("t", F.col("ano") * 53 + F.col("semana"))
    w = Window.orderBy("t")

    # 2. Feature engineering: estacionalidad + rezagos
    serie = (serie
             .withColumn("sin_sem", F.sin(2 * math.pi * F.col("semana") / 52.0))
             .withColumn("cos_sem", F.cos(2 * math.pi * F.col("semana") / 52.0))
             .withColumn("lag1", F.lag("casos", 1).over(w))
             .withColumn("lag2", F.lag("casos", 2).over(w))
             .withColumn("lag4", F.lag("casos", 4).over(w))
             .withColumn("lag52", F.lag("casos", 52).over(w)))

    data = serie.dropna()

    # Objetivo en escala logaritmica log(1+casos): estabiliza la varianza y
    # evita que los picos epidemicos dominen el error. Se revierte con exp(x)-1.
    data = data.withColumn("y_log", F.log1p(F.col("casos")))

    features = ["semana", "sin_sem", "cos_sem", "lag1", "lag2", "lag4", "lag52"]
    assembler = VectorAssembler(inputCols=features, outputCol="features")
    data = assembler.transform(data)

    # 3. Validacion out-of-time: train <= 2023, test = 2024
    train = data.filter(F.col("ano") <= 2023)
    test = data.filter(F.col("ano") == 2024)
    print("Train:", train.count(), "semanas | Test:", test.count(), "semanas")

    # 4. Random Forest (MLlib) sobre el objetivo log-transformado
    rf = RandomForestRegressor(featuresCol="features", labelCol="y_log",
                               numTrees=150, maxDepth=8, seed=42)
    model = rf.fit(train)
    pred = model.transform(test)
    pred = pred.withColumn("prediction", F.expm1(F.col("prediction")))

    # 5. Metricas (escala original de casos)
    def metric(name):
        return RegressionEvaluator(labelCol="casos", predictionCol="prediction",
                                   metricName=name).evaluate(pred)
    rmse, mae, r2 = metric("rmse"), metric("mae"), metric("r2")
    print("RMSE=%.1f  MAE=%.1f  R2=%.3f" % (rmse, mae, r2))

    importances = dict(zip(features,
                       [round(float(x), 4) for x in model.featureImportances.toArray()]))

    # 5b. Evaluacion complementaria con particion aleatoria 80/20
    #     (mide la capacidad del modelo de aprender la dinamica semanal cuando
    #     todos los regimenes -incluida la epidemia- estan representados en el
    #     entrenamiento; es una tarea de interpolacion, no de pronostico futuro)
    tr_r, te_r = data.randomSplit([0.8, 0.2], seed=42)
    m_r = rf.fit(tr_r)
    p_r = m_r.transform(te_r).withColumn("prediction", F.expm1(F.col("prediction")))
    def metric_r(name):
        return RegressionEvaluator(labelCol="casos", predictionCol="prediction",
                                   metricName=name).evaluate(p_r)
    rmse_r, mae_r, r2_r = metric_r("rmse"), metric_r("mae"), metric_r("r2")
    print("Random 80/20 -> RMSE=%.1f MAE=%.1f R2=%.3f" % (rmse_r, mae_r, r2_r))

    # 6. Guardar predicciones y metricas
    out = (pred.select("ano", "semana",
                       F.col("casos").alias("casos_real"),
                       F.round("prediction", 0).alias("casos_predicho"))
           .orderBy("ano", "semana"))
    write_single_csv(out, os.path.join(OUT_DIR, "ml_predicciones.csv"))

    metricas = {
        "modelo": "RandomForestRegressor (Spark MLlib)",
        "n_arboles": 150,
        "profundidad_max": 8,
        "features": features,
        "train_periodo": "2000-2023",
        "test_periodo": "2024",
        "RMSE": round(rmse, 1),
        "MAE": round(mae, 1),
        "R2": round(r2, 3),
        "importancia_variables": importances,
        "eval_random_split": {"RMSE": round(rmse_r, 1), "MAE": round(mae_r, 1),
                               "R2": round(r2_r, 3), "descripcion": "particion aleatoria 80/20 (interpolacion)"},
    }
    with open(os.path.join(OUT_DIR, "ml_metricas.json"), "w", encoding="utf-8") as fh:
        json.dump(metricas, fh, ensure_ascii=False, indent=2)
    print("Metricas:", json.dumps(metricas, ensure_ascii=False))
    print("ML COMPLETADO OK")
    spark.stop()


if __name__ == "__main__":
    main()
