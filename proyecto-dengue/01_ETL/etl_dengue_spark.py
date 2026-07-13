# -*- coding: utf-8 -*-
"""
ETL de Vigilancia Epidemiológica de Dengue en el Perú (2000-2024)
=================================================================
Proyecto final del curso de Big Data.

Este script implementa un proceso ETL (Extract - Transform - Load) sobre la
serie histórica nacional de notificaciones de dengue del CDC-Perú (MINSA),
usando Apache Spark (PySpark) como motor de procesamiento distribuido.

Fuente de datos (Extract):
    Plataforma Nacional de Datos Abiertos - MINSA / CDC-Perú
    "Vigilancia Epidemiológica de dengue" (serie 2000-2024)
    https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiológica-de-dengue
    Licencia: Open Data Commons Attribution License (ODC-BY)

Alineación con el sílabo:
    - Unidad 1 (Fundamentos de Big Data): las 3V -> Volumen (>1M registros),
      Variedad (14 atributos geo/temporales/clínicos), Velocidad (actualización
      semanal de RENACE).
    - Unidad 2 (Software libre): procesamiento distribuido con Apache Spark,
      transformaciones tipo MapReduce sobre un DataFrame particionado.
    - Unidad 3/4 (análisis y minería): salidas agregadas y dataset limpio para
      modelado en Power BI y para el modelo de ML (ver ml_dengue_spark.py).

Salidas (Load):
    02_datos_procesados/
        fact_dengue.csv               -> tabla de hechos limpia (grano: caso)
        dim_tiempo.csv                -> dimensión tiempo (año-semana)
        dim_geografia.csv             -> dimensión geográfica (departamento...)
        agg_casos_por_anio.csv
        agg_casos_por_anio_semana.csv -> estacionalidad
        agg_casos_por_departamento.csv
        agg_casos_por_severidad.csv
        agg_casos_por_grupo_edad.csv
        agg_casos_por_sexo.csv
        agg_dep_anio.csv              -> mapa de calor departamento x año
        kpis.json                     -> indicadores clave para el dashboard

Autor: (completar) — Curso de Big Data, UNDC, 2026-I
"""

import os
import json
import shutil
import glob

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

# --------------------------------------------------------------------------- #
# 0. Configuración de rutas
# --------------------------------------------------------------------------- #
BASE = os.environ.get("PROJ_BASE", ".")
INPUT_CSV = os.environ.get(
    "DENGUE_CSV",
    os.path.join(BASE, "datos_abiertos_vigilancia_dengue_2000_2024.csv"),
)
OUT_DIR = os.path.join(BASE, "02_datos_procesados")
os.makedirs(OUT_DIR, exist_ok=True)


def write_single_csv(sdf, path, order_cols=None):
    """Escribe un Spark DataFrame como un único CSV con cabecera.
    Spark escribe carpetas particionadas; aquí consolidamos a un solo archivo
    para que sea directamente consumible por Power BI y el dashboard HTML."""
    if order_cols:
        sdf = sdf.orderBy(*order_cols)
    # Spark escribe en un directorio de trabajo LOCAL (/tmp) para evitar
    # problemas de permisos con los checksums .crc en carpetas montadas.
    import tempfile
    tmp = tempfile.mkdtemp(prefix="sparkout_")
    (sdf.coalesce(1)
        .write.mode("overwrite")
        .option("header", True)
        .csv(tmp))
    part = glob.glob(os.path.join(tmp, "part-*.csv"))[0]
    shutil.copyfile(part, path)          # copia el resultado al destino final
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"  -> {os.path.basename(path)}")


def main():
    spark = (SparkSession.builder
             .appName("ETL_Dengue_Peru")
             .master("local[*]")
             .config("spark.sql.shuffle.partitions", "8")
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")

    # ------------------------------------------------------------------- #
    # 1. EXTRACT
    # ------------------------------------------------------------------- #
    print("[1/4] EXTRACT: leyendo CSV crudo con Spark ...")
    raw = (spark.read
           .option("header", True)
           .option("sep", ";")
           .option("encoding", "UTF-8")
           .csv(INPUT_CSV))
    n_raw = raw.count()
    print(f"      Registros crudos: {n_raw:,}")

    # ------------------------------------------------------------------- #
    # 2. TRANSFORM (limpieza + enriquecimiento)
    # ------------------------------------------------------------------- #
    print("[2/4] TRANSFORM: limpieza y estandarización ...")

    df = raw

    # 2.1 Normalizar strings (trim + mayúsculas) en campos categóricos
    for c in ["departamento", "provincia", "distrito", "enfermedad", "sexo",
              "tipo_edad", "diagnostic"]:
        df = df.withColumn(c, F.upper(F.trim(F.col(c))))

    # 2.2 Tipos numéricos
    df = (df
          .withColumn("ano", F.col("ano").cast(IntegerType()))
          .withColumn("semana", F.col("semana").cast(IntegerType()))
          .withColumn("edad_raw", F.col("edad").cast(IntegerType())))

    # 2.3 Sexo -> etiqueta legible; valores fuera de {M,F} -> "NO ESPECIFICADO"
    df = df.withColumn(
        "sexo",
        F.when(F.col("sexo") == "M", F.lit("Masculino"))
         .when(F.col("sexo") == "F", F.lit("Femenino"))
         .otherwise(F.lit("No especificado")))

    # 2.4 Edad en años: tipo_edad A=años, M=meses, D=días -> convertir todo a años
    df = df.withColumn(
        "edad_anios",
        F.when(F.col("tipo_edad") == "A", F.col("edad_raw"))
         .when(F.col("tipo_edad") == "M", (F.col("edad_raw") / 12.0))
         .when(F.col("tipo_edad") == "D", (F.col("edad_raw") / 365.0))
         .otherwise(F.col("edad_raw")))

    # 2.5 Grupo etario (quinquenal agrupado en rangos de salud pública)
    df = df.withColumn(
        "grupo_edad",
        F.when(F.col("edad_anios") < 5, "0-4")
         .when(F.col("edad_anios") < 12, "5-11")
         .when(F.col("edad_anios") < 18, "12-17")
         .when(F.col("edad_anios") < 30, "18-29")
         .when(F.col("edad_anios") < 45, "30-44")
         .when(F.col("edad_anios") < 60, "45-59")
         .when(F.col("edad_anios") >= 60, "60+")
         .otherwise("Sin dato"))

    # 2.6 Severidad y CIE-10 (A97.0/1/2)
    df = df.withColumn(
        "severidad",
        F.when(F.col("enfermedad").contains("SIN SIGNOS"), "Sin signos de alarma")
         .when(F.col("enfermedad").contains("CON SIGNOS"), "Con signos de alarma")
         .when(F.col("enfermedad").contains("GRAVE"), "Grave")
         .otherwise("Otro"))

    # 2.7 Marca de caso grave (para el modelo y KPIs)
    df = df.withColumn("es_grave",
                       F.when(F.col("severidad") == "Grave", 1).otherwise(0))

    # 2.8 Filtros de calidad: años y semanas válidas
    df = df.filter(
        (F.col("ano").between(2000, 2024)) &
        (F.col("semana").between(1, 53)))

    # 2.9 Clave de tiempo (año-semana ISO), ej. 2024-W07
    df = df.withColumn(
        "id_tiempo",
        F.concat(F.col("ano"), F.lit("-W"),
                 F.lpad(F.col("semana").cast("string"), 2, "0")))

    # 2.10 Cada fila del origen = 1 caso notificado
    df = df.withColumn("casos", F.lit(1))

    # Tabla de hechos final (selección de columnas relevantes)
    fact = df.select(
        "id_tiempo", "ano", "semana",
        "departamento", "provincia", "distrito", "ubigeo",
        "diresa",
        "severidad", "diagnostic", "es_grave",
        "sexo", "edad_anios", "grupo_edad",
        "casos")

    fact = fact.cache()
    n_fact = fact.count()
    print(f"      Registros tras limpieza: {n_fact:,} "
          f"(descartados: {n_raw - n_fact:,})")

    # ------------------------------------------------------------------- #
    # 3. Agregaciones (transformaciones tipo MapReduce -> groupBy/agg)
    # ------------------------------------------------------------------- #
    print("[3/4] Generando agregaciones y dimensiones ...")

    agg_anio = (fact.groupBy("ano")
                .agg(F.sum("casos").alias("casos"),
                     F.sum("es_grave").alias("casos_graves"))
                .orderBy("ano"))

    agg_anio_semana = (fact.groupBy("ano", "semana")
                       .agg(F.sum("casos").alias("casos"))
                       .orderBy("ano", "semana"))

    agg_dep = (fact.groupBy("departamento")
               .agg(F.sum("casos").alias("casos"),
                    F.sum("es_grave").alias("casos_graves"))
               .orderBy(F.desc("casos")))

    agg_sev = (fact.groupBy("severidad")
               .agg(F.sum("casos").alias("casos"))
               .orderBy(F.desc("casos")))

    agg_edad = (fact.groupBy("grupo_edad")
                .agg(F.sum("casos").alias("casos"))
                .orderBy("grupo_edad"))

    agg_sexo = (fact.groupBy("sexo")
                .agg(F.sum("casos").alias("casos")))

    agg_dep_anio = (fact.groupBy("departamento", "ano")
                    .agg(F.sum("casos").alias("casos")))

    # Dimensiones (modelo estrella para Power BI)
    dim_tiempo = (fact.select("id_tiempo", "ano", "semana").distinct()
                  .orderBy("ano", "semana"))
    dim_geo = (fact.select("departamento", "provincia", "distrito", "ubigeo")
               .distinct().orderBy("departamento", "provincia", "distrito"))

    # ------------------------------------------------------------------- #
    # 4. LOAD (escritura de salidas)
    # ------------------------------------------------------------------- #
    print("[4/4] LOAD: escribiendo salidas en 02_datos_procesados ...")

    write_single_csv(fact, os.path.join(OUT_DIR, "fact_dengue.csv"))
    write_single_csv(dim_tiempo, os.path.join(OUT_DIR, "dim_tiempo.csv"))
    write_single_csv(dim_geo, os.path.join(OUT_DIR, "dim_geografia.csv"))
    write_single_csv(agg_anio, os.path.join(OUT_DIR, "agg_casos_por_anio.csv"))
    write_single_csv(agg_anio_semana, os.path.join(OUT_DIR, "agg_casos_por_anio_semana.csv"))
    write_single_csv(agg_dep, os.path.join(OUT_DIR, "agg_casos_por_departamento.csv"))
    write_single_csv(agg_sev, os.path.join(OUT_DIR, "agg_casos_por_severidad.csv"))
    write_single_csv(agg_edad, os.path.join(OUT_DIR, "agg_casos_por_grupo_edad.csv"))
    write_single_csv(agg_sexo, os.path.join(OUT_DIR, "agg_casos_por_sexo.csv"))
    write_single_csv(agg_dep_anio, os.path.join(OUT_DIR, "agg_dep_anio.csv"))

    # KPIs para el dashboard
    total = fact.agg(F.sum("casos")).collect()[0][0]
    graves = fact.agg(F.sum("es_grave")).collect()[0][0]
    row_max = agg_anio.orderBy(F.desc("casos")).first()
    dep_top = agg_dep.first()
    n_dep = fact.select("departamento").distinct().count()
    pct_2324 = (agg_anio.filter(F.col("ano").isin(2023, 2024))
                .agg(F.sum("casos")).collect()[0][0])

    kpis = {
        "total_casos": int(total),
        "total_graves": int(graves),
        "pct_graves": round(100.0 * graves / total, 2),
        "anios_cubiertos": "2000-2024",
        "anio_pico": int(row_max["ano"]),
        "casos_anio_pico": int(row_max["casos"]),
        "departamento_top": dep_top["departamento"],
        "casos_departamento_top": int(dep_top["casos"]),
        "n_departamentos": int(n_dep),
        "casos_2023_2024": int(pct_2324),
        "pct_2023_2024": round(100.0 * pct_2324 / total, 2),
    }
    with open(os.path.join(OUT_DIR, "kpis.json"), "w", encoding="utf-8") as fh:
        json.dump(kpis, fh, ensure_ascii=False, indent=2)
    print("  -> kpis.json")
    print("\nKPIs:", json.dumps(kpis, ensure_ascii=False))
    print("\nETL COMPLETADO OK")
    spark.stop()


if __name__ == "__main__":
    main()
