@echo off
REM === Publica este portafolio en GitHub (reemplaza el contenido inicial del repo) ===
REM Requiere Git instalado: https://git-scm.com/download/win
cd /d "%~dp0"
echo Preparando el repositorio...
git init -b main
git add -A
git commit -m "Portafolio de Big Data: proyecto Dengue (Spark+ML) y Accidentes (Power BI)"
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/JesusFV04/portafolio-bigdata.git
echo.
echo Subiendo a GitHub (se abrira el inicio de sesion en el navegador)...
git push -u origin main --force
echo.
echo Listo. Si no hubo errores, tu portafolio ya esta en GitHub.
echo Ahora activa GitHub Pages: Settings ^> Pages ^> Branch main / root.
echo.
pause
