# Actividad 4 — Aplicación web interactiva para el análisis de mortalidad en Colombia (2019)

## Introducción del proyecto

Este proyecto consiste en una **aplicación web interactiva** desarrollada en Python con el
framework **Dash** y la librería de visualización **Plotly Express**, orientada al análisis
exploratorio de los datos oficiales de **mortalidad no fetal en Colombia durante el año
2019**, publicados por el DANE.

A diferencia de un reporte estático, la aplicación permite al usuario **cargar sus propios
archivos Excel** (mediante un componente `dcc.Upload`) y, una vez procesados, habilita de
forma dinámica una serie de visualizaciones interactivas: mapas coropléticos, series de
tiempo, gráficos de barras, tablas, gráficos circulares e histogramas demográficos. Todo
ello pensado como una herramienta de **analítica de datos** para investigadores, docentes
y tomadores de decisiones en salud pública.

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
├── app.py              # Aplicación Dash principal (layout + callbacks + figuras)
├── requirements.txt    # Dependencias Python con versiones estables
├── Procfile            # Comando de arranque para entornos PaaS (Render, Heroku, etc.)
├── .gitignore          # Exclusiones de control de versiones (.venv, __pycache__, …)
├── data/               # Carpeta local para los archivos .xlsx de prueba
└── README.md           # Documentación del proyecto
```

- **`app.py`**: contiene la inicialización de la aplicación Dash, el `layout` con la zona
  de carga de archivos, los `callbacks` que consolidan los datasets y los constructores
  de cada figura. Expone `server = app.server` para producción.
- **`requirements.txt`**: lista de librerías necesarias (`dash`, `pandas`, `plotly`,
  `openpyxl`, `gunicorn`).
- **`Procfile`**: define el proceso `web` que ejecuta Gunicorn apuntando al objeto
  `server` de `app.py`.
- **`.gitignore`**: evita versionar entornos virtuales, archivos compilados de Python,
  configuraciones de IDE y artefactos del sistema operativo.
- **`data/`**: carpeta destinada a los tres archivos de Excel utilizados en las pruebas
  locales (no se cargan automáticamente; deben subirse desde la interfaz web).

## Requisitos

**Requerimientos técnicos:**

- Python **3.10 o superior**.
- Conexión a Internet para descargar el GeoJSON de los departamentos (mapa).
- Navegador moderno (Chrome, Edge, Firefox).

**Librerías mínimas:**

| Librería   | Versión | Propósito                                  |
|------------|---------|--------------------------------------------|
| dash       | 2.17.1  | Framework web reactivo                     |
| pandas     | 2.2.2   | Manipulación de datos                      |
| plotly     | 5.22.0  | Visualización interactiva                  |
| openpyxl   | 3.1.5   | Lectura de archivos `.xlsx`                |
| gunicorn   | 22.0.0  | Servidor WSGI para producción              |

## Despliegue

Guía paso a paso para desplegar la aplicación de forma **gratuita en Render**:

1. **Subir el proyecto a GitHub.** Asegúrese de que el repositorio
   [Actividad-4-Aplicacion-web-interactiva-para-el-analisis-de-mortalidad-en-Colombia](https://github.com/jose-i-rm/Actividad-4-Aplicacion-web-interactiva-para-el-analisis-de-mortalidad-en-Colombia)
   contiene `app.py`, `requirements.txt` y `Procfile`.
2. **Crear cuenta en Render.** Ingrese a <https://render.com> y autentíquese con su
   cuenta de GitHub.
3. **Nuevo Web Service.** En el dashboard de Render seleccione **New → Web Service** y
   elija el repositorio del proyecto.
4. **Configuración del servicio:**
   - **Name:** `mortalidad-colombia-2019` (o el que prefiera).
   - **Region:** la más cercana (p. ej. *Oregon*).
   - **Branch:** `main`.
   - **Runtime:** `Python 3`.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:server`
   - **Instance Type:** `Free`.
5. **Crear el servicio.** Haga clic en **Create Web Service**. Render clonará el
   repositorio, instalará las dependencias y arrancará Gunicorn.
6. **Acceder a la app.** Una vez finalizado el despliegue, Render expondrá una URL
   pública del tipo `https://mortalidad-colombia-2019.onrender.com`.
7. **Cargar los archivos Excel** desde la interfaz para habilitar las visualizaciones.

> **Nota:** en el plan Free, el servicio se suspende tras un periodo de inactividad y
> tarda algunos segundos en reactivarse al recibir tráfico nuevamente.

## Software

Herramientas de desarrollo implicadas:

- **Python 3.10+** — lenguaje de programación base.
- **Dash** — framework para construir aplicaciones web analíticas en Python.
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

# 2. Crear el entorno virtual
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

Abra el navegador en <http://127.0.0.1:8050> y, desde la sección **“1. Carga de
archivos”**, suba los tres ficheros:

- `NoFetal2019.xlsx`
- `CodigosDeMuerte.xlsx`
- `Divipola.xlsx`

Una vez consolidados los datos, el dashboard renderizará automáticamente las siete
visualizaciones interactivas.
