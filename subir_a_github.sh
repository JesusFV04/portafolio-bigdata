#!/usr/bin/env bash
# === Publica este portafolio en GitHub ===
cd "$(dirname "$0")" || exit 1
git init -b main
git add -A
git commit -m "Portafolio de Big Data: proyecto Dengue (Spark+ML) y Accidentes (Power BI)"
git branch -M main
git remote remove origin 2>/dev/null
git remote add origin https://github.com/JesusFV04/portafolio-bigdata.git
echo "Subiendo a GitHub..."
git push -u origin main --force
echo "Si fue rechazado por contenido previo:  git push -u origin main --force"
