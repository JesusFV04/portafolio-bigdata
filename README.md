# 📊 Portafolio de Big Data — Análisis y Visualización de Datos

Portafolio del curso de **Big Data** (Escuela Profesional de Ingeniería de Sistemas, Universidad Nacional de Cañete). Reúne dos trabajos que recorren el ciclo de vida del dato, del ETL a la decisión.

> 🌐 **Portafolio en vivo:** https://jesusfv04.github.io/portafolio-bigdata/

---

## 🦟 Proyecto 1 · Vigilancia del Dengue en el Perú (pipeline de Big Data)

Pipeline de extremo a extremo sobre **1 029 421 notificaciones reales** de dengue del CDC-Perú (2000–2024).

- **ETL distribuido** con Apache Spark (PySpark): limpieza, estandarización y modelo dimensional en esquema estrella.
- **Minería de datos / ML**: comparación de **8 modelos** de pronóstico (Random Forest, Gradient Boosting, SARIMA/SARIMAX, líneas base) con **integración de datos climáticos** de NASA POWER; validación *walk-forward* y por departamento.
- **Visualización y decisión**: tablero con capa accionable (canal endémico, priorización territorial, proyección y recomendaciones).

**Hallazgos:** la epidemia 2023–2024 concentró el 51,3 % de los casos históricos; el epicentro se desplazó de Piura a Lima; fuerte acoplamiento con El Niño; mejor modelo (Gradient Boosting con clima) R² = 0,60.

**Herramientas:** `Apache Spark` · `PySpark` · `Spark MLlib` · `scikit-learn` · `statsmodels` · `Power BI` · `NASA POWER`

📂 Ver `proyecto-dengue/` · 📄 Artículo (APA 7) · 📘 Informe completo · 🛠️ Guía Power BI y **Guía Looker Studio** · ⚙️ Código en `proyecto-dengue/01_ETL/`

> El portafolio incluye el **dashboard interactivo en vivo** (HTML, sin dependencias). Como alternativa publicable con Gmail, hay una guía para replicarlo en **Google Looker Studio**.

### Reproducir el ETL
```bash
cd proyecto-dengue/01_ETL
python -m venv sparkenv && source sparkenv/bin/activate   # Windows: sparkenv\Scripts\activate
pip install -r requirements.txt
# Descarga el CSV oficial (108 MB) desde datosabiertos.gob.pe y colócalo en proyecto-dengue/
python etl_dengue_spark.py         # ETL con Spark
python ml2_clima_comparacion.py    # modelado con clima
```
> Los CSV crudos (>100 MB) no se versionan en GitHub; se regeneran con el ETL. La fuente es pública: Plataforma Nacional de Datos Abiertos (MINSA/CDC-Perú).

---

## 🚗 Proyecto 2 · Reporte de Accidentes de Tránsito 2022 (EE.UU.)

Tablero analítico en **Power BI** sobre accidentes de tránsito en Estados Unidos (2022): limpieza y transformación con Power Query, indicadores clave (fallecimientos, total de accidentes, bajas promedio) y visualizaciones de decesos por mes y por estado.

**Herramientas:** `Power BI` · `Power Query` · `Excel` · `DAX`

📂 Ver `praxis/` (archivo `.pbix`, PDFs del proceso y dataset).

---

## 🗂️ Estructura del repositorio
```
portafolio-bigdata/
├── index.html                 Portafolio (GitHub Pages)
├── assets/img/                Imágenes del portafolio
├── proyecto-dengue/           Proyecto de Big Data (dengue)
│   ├── 01_ETL/                Scripts Spark (ETL y ML) + README
│   ├── 02_datos_procesados/   Agregados, dimensiones, clima, resultados
│   ├── 03_dashboard/          Dashboard interactivo (HTML)
│   ├── 04_articulo/           Artículo científico (APA 7) + figuras
│   ├── 05_guia_powerbi/       Guía de replicación en Power BI
│   └── 07_informe/            Informe completo del proyecto
└── praxis/                    Dashboard de accidentes (Power BI)
```

---

## ⚠️ Nota metodológica
El proyecto de dengue es una **demostración (prueba de concepto)** sobre datos históricos reales. La serie oficial de microdatos abiertos se cierra en 2024, por lo que **no es un sistema de vigilancia en vivo**; el mismo pipeline, alimentado con datos actualizados, sería operativo.

## 📚 Fuentes
- MINSA / CDC-Perú — *Vigilancia Epidemiológica de dengue* (Datos Abiertos, ODC-BY).
- NASA POWER — datos meteorológicos.
- Dataset de accidentes de tránsito de EE.UU. 2022.

---
_Autor: **Jesus Abel Figueroa Valencia** · Estudiante de Ingeniería de Sistemas (VII ciclo) · UNDC · 2026_  
_Contacto: 2301010109@gmail.com_
