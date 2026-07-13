# Pipeline de Big Data — Vigilancia de Dengue en el Perú (2000–2024)

Proceso ETL + modelo de Machine Learning sobre la serie histórica nacional de
notificaciones de dengue del CDC-Perú (MINSA), con **Apache Spark (PySpark)**.

## Fuente de datos
Plataforma Nacional de Datos Abiertos — MINSA / CDC-Perú
*"Vigilancia Epidemiológica de dengue"* (serie 2000–2024), licencia ODC-BY.
Archivo: `datos_abiertos_vigilancia_dengue_2000_2024.csv` (~108 MB, 1 029 421 registros).
https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiológica-de-dengue

## Requisitos
- Python 3.10+
- Java 8/11/17 (para Spark)
- `pip install -r requirements.txt`

## Ejecución
```bash
export PROJ_BASE="/ruta/al/proyecto/Articulo"   # carpeta que contiene el CSV
python etl_dengue_spark.py     # ETL: limpieza, modelo estrella, agregaciones
python ml_dengue_spark.py      # Modelo Random Forest (Spark MLlib)
```
Las salidas se escriben en `../02_datos_procesados/`.

## Alineación con el sílabo
- **Unidad 1 — Fundamentos (3V):** Volumen (>1M registros), Variedad (14 atributos),
  Velocidad (actualización semanal de RENACE).
- **Unidad 2 — Software libre:** procesamiento distribuido con Apache Spark
  (transformaciones tipo MapReduce: `groupBy`/`agg` sobre un DataFrame particionado).
- **Unidad 3 — Software licenciado:** el modelo estrella y las agregaciones
  alimentan el dashboard en **Power BI**; el mismo código corre en Databricks.
- **Unidad 4 — Análisis y minería:** Random Forest con Spark MLlib para
  pronóstico de casos semanales.

## Salidas (`02_datos_procesados/`)
| Archivo | Descripción |
|---|---|
| `fact_dengue.csv` | Tabla de hechos limpia (grano: caso notificado) |
| `dim_tiempo.csv`, `dim_geografia.csv` | Dimensiones (modelo estrella) |
| `agg_casos_por_anio.csv` | Casos y casos graves por año |
| `agg_casos_por_anio_semana.csv` | Serie semanal (estacionalidad) |
| `agg_casos_por_departamento.csv` | Casos por departamento |
| `agg_casos_por_severidad.csv` | Distribución por severidad |
| `agg_casos_por_grupo_edad.csv`, `agg_casos_por_sexo.csv` | Demografía |
| `agg_dep_anio.csv` | Matriz departamento × año |
| `ml_predicciones.csv`, `ml_metricas.json` | Resultados del modelo |
| `kpis.json` | Indicadores clave para el dashboard |

## Modelo avanzado con clima (ml2_clima_comparacion.py)
Estudio comparativo a resolución mensual que integra variables climáticas de NASA POWER
(temperatura, humedad, precipitación) para los 5 departamentos más afectados. Compara ocho
modelos (persistencia, naive estacional, SARIMA, SARIMAX, Random Forest y Gradient Boosting,
con y sin clima), con validación out-of-time (2024) y walk-forward (2019–2024), y replica el
mejor modelo por departamento. Requiere `clima_mensual.csv` en 02_datos_procesados.
Salidas: ml2_metricas.json, ml2_pred_nacional_2024.csv, ml2_serie_mensual.csv.
