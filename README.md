# Actividad 4 — Aplicación web interactiva para el análisis de mortalidad en Colombia (2019)

🌐 **App en producción:** <https://actividad-4-aplicacion-web-interactiva.onrender.com/>

📦 **Repositorio:** <https://github.com/jose-i-rm/Actividad-4-Aplicacion-web-interactiva-para-el-analisis-de-mortalidad-en-Colombia>

## Introducción del proyecto

Este proyecto consiste en una **aplicación web interactiva** desarrollada en Python con el
framework **Dash** y la librería de visualización **Plotly Express**, orientada al análisis
exploratorio de los datos oficiales de **mortalidad no fetal en Colombia durante el año
2019**, publicados por el DANE.

La aplicación lee directamente los tres archivos Excel oficiales ubicados en la raíz del
repositorio (`Anexo1.NoFetal2019_CE_15-03-23.xlsx`,
`Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx`, `Divipola_CE_.xlsx`) y los cruza para producir
un conjunto de visualizaciones interactivas: mapas coropléticos, series de tiempo,
gráficos de barras, tablas, gráficos circulares e histogramas demográficos. Una
herramienta de **analítica de datos** pensada para investigadores, docentes y tomadores
de decisiones en salud pública.

## Objetivo

La aplicación busca **identificar patrones demográficos y de salud pública** a partir de
los registros de mortalidad de 2019. En particular permite analizar:

- La **distribución geográfica** de la mortalidad por departamento.
- La **estacionalidad mensual** de las defunciones a lo largo del año.
- Los **municipios con mayor índice de violencia armada** (homicidios CIE-10 `X95`).
- Los **municipios con menor mortalidad** registrada.
- Las **10 principales causas de muerte** según los códigos CIE-10.
- La **brecha de mortalidad por sexo** en cada departamento.
- La **distribución por ciclo de vida** (mortalidad neonatal, infantil, primera infancia,
  niñez, adolescencia, juventud, adultez, vejez, longevidad) según la codificación oficial
  del DANE para `GRUPO_EDAD1`.

## Estructura del proyecto

```
Actividad4_MIA/
├── app.py                                       # Aplicación Dash principal
├── requirements.txt                             # Dependencias Python
├── Procfile                                     # Arranque para PaaS (Render)
├── .python-version                              # Fija Python 3.11.9 en Render
├── .gitignore                                   # Exclusiones de Git
├── Anexo1.NoFetal2019_CE_15-03-23.xlsx          # Datos crudos de mortalidad
├── Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx      # Códigos CIE-10
├── Divipola_CE_.xlsx                            # División Político-Administrativa
├── data/                                        # Carpeta alternativa para los .xlsx
└── README.md                                    # Documentación
```

- **`app.py`**: inicializa Dash, lee los tres archivos Excel desde la raíz, consolida
  los datasets y construye las siete visualizaciones. Expone `server = app.server`
  para producción.
- **`requirements.txt`**: librerías necesarias (`dash`, `pandas`, `plotly`, `openpyxl`,
  `gunicorn`).
- **`Procfile`**: define el proceso `web: gunicorn app:server`.
- **`.python-version`**: fuerza a Render a usar **Python 3.11.9**, evitando fallos de
  compilación de `pandas` con versiones nuevas del intérprete.
- **Archivos Excel en la raíz**: la app los lee automáticamente al iniciar.

## Requisitos

**Requerimientos técnicos:**

- Python **3.11** (recomendado; en Render se fija con `.python-version`).
- Conexión a Internet para descargar el GeoJSON de los departamentos (mapa).
- Navegador moderno (Chrome, Edge, Firefox).

**Librerías mínimas:**

| Librería  | Versión | Propósito                       |
|-----------|---------|---------------------------------|
| dash      | 2.17.1  | Framework web reactivo          |
| pandas    | 2.2.2   | Manipulación de datos           |
| plotly    | 5.22.0  | Visualización interactiva       |
| openpyxl  | 3.1.5   | Lectura de archivos `.xlsx`     |
| gunicorn  | 22.0.0  | Servidor WSGI para producción   |

## Despliegue

Guía paso a paso para desplegar la aplicación de forma **gratuita en Render**:

1. **Subir el proyecto a GitHub.** Asegúrese de que el repositorio contiene `app.py`,
   `requirements.txt`, `Procfile`, `.python-version` y los tres archivos `.xlsx`.
2. **Crear cuenta en Render.** Ingrese a <https://render.com> y autentíquese con su
   cuenta de GitHub.
3. **Nuevo Web Service.** En el dashboard seleccione **New → Web Service** y elija el
   repositorio del proyecto.
4. **Configuración del servicio:**
   - **Name:** `actividad-4-aplicacion-web-interactiva`
   - **Region:** la más cercana (p. ej. *Oregon*).
   - **Branch:** `main`.
   - **Runtime:** `Python 3` (Render leerá `.python-version` y usará **3.11.9**).
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:server`
   - **Instance Type:** `Free`.
5. **Crear el servicio.** Haga clic en **Create Web Service**. Render clonará el
   repositorio, instalará las dependencias y arrancará Gunicorn.
6. **Acceder a la app.** Una vez finalizado el despliegue, la app estará disponible en:

   **<https://actividad-4-aplicacion-web-interactiva.onrender.com/>**

> **Nota:** en el plan Free, el servicio se suspende tras un periodo de inactividad y
> tarda algunos segundos en reactivarse al recibir tráfico nuevamente. La primera carga
> también puede tardar más debido a la lectura del Excel principal (~600 MB en RAM).

### ¿Por qué falló el primer despliegue?

Render usaba por defecto **Python 3.14**, para el cual `pandas==2.2.2` no tiene wheel
precompilada y la compilación desde fuente fallaba con un error de Cython/C++
(`standard attributes in middle of decl-specifiers`). El archivo `.python-version`
fuerza ahora **Python 3.11.9**, que cuenta con wheels oficiales de `pandas`.

## Software

Herramientas de desarrollo implicadas:

- **Python 3.11** — lenguaje de programación base.
- **Dash** — framework para aplicaciones web analíticas en Python.
- **Plotly (Plotly Express)** — motor de gráficos interactivos.
- **Pandas** — análisis y transformación tabular de datos.
- **openpyxl** — lectura de archivos Excel (`.xlsx`).
- **Gunicorn** — servidor WSGI utilizado en producción.
- **Visual Studio Code** — IDE recomendado para edición y depuración.
- **Git / GitHub** — control de versiones y hospedaje del repositorio.
- **Render** — plataforma PaaS gratuita para el despliegue.

## Instalación

Pasos para ejecutar el proyecto en un entorno **local**:

```bash
# 1. Clonar el repositorio
git clone https://github.com/jose-i-rm/Actividad-4-Aplicacion-web-interactiva-para-el-analisis-de-mortalidad-en-Colombia.git
cd Actividad-4-Aplicacion-web-interactiva-para-el-analisis-de-mortalidad-en-Colombia

# 2. Crear el entorno virtual (Python 3.11 recomendado)
python -m venv .venv

# 3. Activar el entorno virtual
#    Windows (PowerShell):
.venv\Scripts\Activate.ps1
#    Linux / macOS:
source .venv/bin/activate

# 4. Instalar las dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 5. Ejecutar la aplicación
python app.py
```

Abra el navegador en <http://127.0.0.1:8050>. La aplicación leerá automáticamente los
tres archivos Excel desde la raíz del proyecto y renderizará las siete visualizaciones
interactivas.
