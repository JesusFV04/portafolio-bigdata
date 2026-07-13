# 🚀 Cómo publicar el portafolio (GitHub Pages + Power BI)

Guía paso a paso, sin instalar nada (todo desde el navegador).

> ✅ **Todo ya está listo con tu nombre y datos.** Solo falta subirlo. Elige UNA de estas 3 formas:

### ⚡ Forma A — Script (la más rápida, si tienes Git instalado)
Doble clic en **`subir_a_github.bat`** (Windows). Hará todo y abrirá el inicio de sesión de GitHub en el navegador. Si dice "rejected", abre una terminal en la carpeta y ejecuta: `git push -u origin main --force`.

### 🖱️ Forma B — GitHub Desktop (sin comandos)
Instala GitHub Desktop → *File → Add local repository* → elige la carpeta `portafolio-bigdata` → *Publish repository* (deja el nombre `portafolio-bigdata`, público) → un clic.

### 🌐 Forma C — Subida web (sin instalar nada)
Sigue la Parte 1 de abajo (arrastrar y soltar en github.com).

Después de cualquiera de las tres, activa GitHub Pages (Parte 2).

---


---

## Parte 1 · Subir el repositorio a GitHub

1. Crea una cuenta en https://github.com (si no tienes) e inicia sesión.
2. Arriba a la derecha, **+ → New repository**.
   - **Repository name:** `portafolio-bigdata`
   - Marca **Public**. **No** marques "Add a README" (ya tenemos uno).
   - **Create repository**.
3. En la página del repo vacío, haz clic en **uploading an existing file** (enlace azul).
4. **Arrastra TODO el contenido** de la carpeta `portafolio-bigdata` (los archivos y subcarpetas: `index.html`, `assets/`, `proyecto-dengue/`, `praxis/`, `README.md`, etc.).
   - 💡 Los CSV pesados ya fueron excluidos, así que no habrá archivos que superen el límite.
5. Abajo, escribe un mensaje (p. ej. "primer commit") y pulsa **Commit changes**.

---

## Parte 2 · Activar GitHub Pages

1. En el repo, ve a **Settings** (pestaña superior) → **Pages** (menú izquierdo).
2. En **Source**, elige **Deploy from a branch**.
3. En **Branch**, selecciona **main** y carpeta **/ (root)**. Pulsa **Save**.
4. Espera 1–2 minutos y recarga. Aparecerá tu URL:
   `https://TU-USUARIO.github.io/portafolio-bigdata/`
5. ¡Ese es tu portafolio en vivo! Ponlo en el `README.md` y en tu CV.

---

## Parte 3 · Los dashboards (ya resuelto, sin depender de Power BI)

**Dengue — dashboard interactivo EN VIVO (ya embebido).**
El portafolio ya incrusta el dashboard interactivo en HTML (proyecto-dengue/03_dashboard). Funciona solo en GitHub Pages, sin cuentas ni permisos. No tienes que hacer nada.

**Dengue — versión en Looker Studio (opcional, recomendado para el CV).**
Como tu Power BI institucional no deja «Publicar en la web», puedes replicar el mismo tablero en **Google Looker Studio** (gratis, con tu Gmail, sí permite embeber). Sigue la guía `proyecto-dengue/05_guia_powerbi/Guia_Looker_Studio.docx`. Al final te da un `<iframe>` que puedes:
- mandarme para que lo integre, o
- pegar tú en `index.html` (bloque `id="pbi-dengue"`), como segunda vista junto al HTML.

**Praxis (accidentes) — se queda en Power BI, sin publicar.**
El portafolio ya muestra la captura del tablero terminado y permite descargar el archivo `.pbix`. Si el profe quiere verlo interactivo, lo abres en Power BI Desktop. No requiere publicación.

---

## ✅ Checklist
- [ ] Repo creado y archivos subidos
- [ ] GitHub Pages activado (tengo mi URL)
- [ ] (Opcional) Dashboard de dengue replicado y publicado en Looker Studio → iframe integrado
- [ ] URL de Pages añadida al README y al CV
