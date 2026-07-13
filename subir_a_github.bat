@echo off
REM === Publica este portafolio en GitHub ===
REM Ejecutar con doble clic (requiere Git instalado: https://git-scm.com/download/win)
cd /d "%~dp0"
echo Inicializando repositorio...
git init -b main
git add -A
git commit -m "Portafolio de Big Data: proyecto Dengue (Spark+ML) y Accidentes (Power BI)"
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/JesusFV04/portafolio-bigdata.git
echo.
echo Subiendo a GitHub (se abrira el inicio de sesion de GitHub en el navegador)...
git push -u origin main
echo.
echo Si dice "rejected" porque el repo ya tenia contenido, ejecuta:
echo    git push -u origin main --force
echo.
pause
