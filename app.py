"""
Aplicación web interactiva para el análisis de mortalidad en Colombia (2019).

Autor: jose-i-rm
Framework: Dash + Plotly
"""

import base64
import io
import json
import urllib.request
from typing import Optional, Tuple

import dash
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, State, dash_table, dcc, html

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------
GEOJSON_URL = (
    "https://raw.githubusercontent.com/caticoa3/colombia_mapa/master/"
    "co_2018_MGN_DPTO_POLITICO.geojson"
)

CIE10_HOMICIDIOS = ["X95"]  # Agresión con disparo de armas de fuego (no especificadas)

GRUPO_EDAD_MAP = {
    **dict.fromkeys(range(0, 5), "Mortalidad neonatal"),
    **dict.fromkeys(range(5, 7), "Mortalidad infantil"),
    **dict.fromkeys(range(7, 9), "Primera infancia"),
    **dict.fromkeys(range(9, 11), "Niñez"),
    11: "Adolescencia",
    **dict.fromkeys(range(12, 14), "Juventud"),
    **dict.fromkeys(range(14, 17), "Adultez temprana"),
    **dict.fromkeys(range(17, 20), "Adultez intermedia"),
    **dict.fromkeys(range(20, 25), "Vejez"),
    **dict.fromkeys(range(25, 29), "Longevidad / Centenarios"),
    29: "Edad desconocida",
}

CICLO_ORDEN = [
    "Mortalidad neonatal",
    "Mortalidad infantil",
    "Primera infancia",
    "Niñez",
    "Adolescencia",
    "Juventud",
    "Adultez temprana",
    "Adultez intermedia",
    "Vejez",
    "Longevidad / Centenarios",
    "Edad desconocida",
]

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# ---------------------------------------------------------------------------
# Inicialización de la app
# ---------------------------------------------------------------------------
app = Dash(__name__, suppress_callback_exceptions=True, title="Mortalidad Colombia 2019")
server = app.server  # Exposición obligatoria para entornos de producción (gunicorn)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def parse_uploaded_excel(contents: str) -> Optional[pd.DataFrame]:
    """Decodifica un archivo Excel cargado vía dcc.Upload."""
    if not contents:
        return None
    try:
        _, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        return pd.read_excel(io.BytesIO(decoded), engine="openpyxl")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] No se pudo leer el archivo cargado: {exc}")
        return None


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def _find_column(df: pd.DataFrame, candidates) -> Optional[str]:
    for cand in candidates:
        for col in df.columns:
            if cand.upper() == col.upper():
                return col
    for cand in candidates:
        for col in df.columns:
            if cand.upper() in col.upper():
                return col
    return None


def prepare_datasets(
    df_mort: pd.DataFrame, df_cod: pd.DataFrame, df_divipola: pd.DataFrame
) -> pd.DataFrame:
    """Cruza los tres datasets y deja un DataFrame listo para los análisis."""
    df_mort = _normalize_columns(df_mort)
    df_cod = _normalize_columns(df_cod)
    df_divipola = _normalize_columns(df_divipola)

    # --- Códigos de muerte ---
    cod_col = _find_column(df_cod, ["CODIGO", "COD", "CIE10"])
    desc_col = _find_column(df_cod, ["DESCRIPCION", "NOMBRE", "CAUSA"])
    if cod_col and desc_col:
        df_cod = df_cod.rename(columns={cod_col: "COD_CAUSA", desc_col: "NOMBRE_CAUSA"})
        df_cod["COD_CAUSA"] = df_cod["COD_CAUSA"].astype(str).str.strip().str.upper()

    # --- Divipola ---
    cod_dpto = _find_column(df_divipola, ["COD_DEPARTAMENTO", "CODIGO_DEPARTAMENTO", "COD_DPTO", "CODDEPTO"])
    nom_dpto = _find_column(df_divipola, ["DEPARTAMENTO", "NOMBRE_DEPARTAMENTO", "NOM_DPTO"])
    cod_mpio = _find_column(df_divipola, ["COD_MUNICIPIO", "CODIGO_MUNICIPIO", "COD_MPIO", "CODMPIO"])
    nom_mpio = _find_column(df_divipola, ["MUNICIPIO", "NOMBRE_MUNICIPIO", "NOM_MPIO"])

    rename_dvp = {}
    if cod_dpto: rename_dvp[cod_dpto] = "COD_DEPARTAMENTO"
    if nom_dpto: rename_dvp[nom_dpto] = "DEPARTAMENTO"
    if cod_mpio: rename_dvp[cod_mpio] = "COD_MUNICIPIO"
    if nom_mpio: rename_dvp[nom_mpio] = "MUNICIPIO"
    df_divipola = df_divipola.rename(columns=rename_dvp)

    # Normalizar códigos
    if "COD_DEPARTAMENTO" in df_divipola.columns:
        df_divipola["COD_DEPARTAMENTO"] = (
            pd.to_numeric(df_divipola["COD_DEPARTAMENTO"], errors="coerce")
            .astype("Int64")
        )
    if "COD_MUNICIPIO" in df_divipola.columns:
        df_divipola["COD_MUNICIPIO"] = (
            pd.to_numeric(df_divipola["COD_MUNICIPIO"], errors="coerce")
            .astype("Int64")
        )

    # --- Mortalidad ---
    cod_dpto_m = _find_column(df_mort, ["COD_DEPARTAMENTO", "DEPARTAMENTO", "COD_DPTO", "DPTO"])
    cod_mpio_m = _find_column(df_mort, ["COD_MUNICIPIO", "MUNICIPIO", "COD_MPIO", "MPIO"])
    causa_col = _find_column(df_mort, ["COD_MUERTE", "CAUSA", "CIE10", "C_BAS1", "CODIGO_MUERTE"])
    sexo_col = _find_column(df_mort, ["SEXO"])
    mes_col = _find_column(df_mort, ["MES"])
    edad_col = _find_column(df_mort, ["GRUPO_EDAD1", "GRUPO_EDAD", "EDAD"])

    rename_m = {}
    if cod_dpto_m: rename_m[cod_dpto_m] = "COD_DEPARTAMENTO"
    if cod_mpio_m: rename_m[cod_mpio_m] = "COD_MUNICIPIO"
    if causa_col: rename_m[causa_col] = "COD_CAUSA"
    if sexo_col: rename_m[sexo_col] = "SEXO"
    if mes_col: rename_m[mes_col] = "MES"
    if edad_col: rename_m[edad_col] = "GRUPO_EDAD1"
    df_mort = df_mort.rename(columns=rename_m)

    if "COD_DEPARTAMENTO" in df_mort.columns:
        df_mort["COD_DEPARTAMENTO"] = pd.to_numeric(df_mort["COD_DEPARTAMENTO"], errors="coerce").astype("Int64")
    if "COD_MUNICIPIO" in df_mort.columns:
        df_mort["COD_MUNICIPIO"] = pd.to_numeric(df_mort["COD_MUNICIPIO"], errors="coerce").astype("Int64")
    if "COD_CAUSA" in df_mort.columns:
        df_mort["COD_CAUSA"] = df_mort["COD_CAUSA"].astype(str).str.strip().str.upper()
    if "MES" in df_mort.columns:
        df_mort["MES"] = pd.to_numeric(df_mort["MES"], errors="coerce").astype("Int64")
    if "GRUPO_EDAD1" in df_mort.columns:
        df_mort["GRUPO_EDAD1"] = pd.to_numeric(df_mort["GRUPO_EDAD1"], errors="coerce").astype("Int64")
    if "SEXO" in df_mort.columns:
        df_mort["SEXO"] = pd.to_numeric(df_mort["SEXO"], errors="coerce").map(
            {1: "Hombre", 2: "Mujer", 3: "Indeterminado"}
        ).fillna("Indeterminado")

    # Cruce con Divipola a nivel municipio (trae también departamento)
    dvp_mpio = df_divipola.drop_duplicates(subset=["COD_MUNICIPIO"]) if "COD_MUNICIPIO" in df_divipola.columns else None
    if dvp_mpio is not None and "COD_MUNICIPIO" in df_mort.columns:
        df_mort = df_mort.merge(
            dvp_mpio[[c for c in ["COD_MUNICIPIO", "MUNICIPIO", "COD_DEPARTAMENTO", "DEPARTAMENTO"] if c in dvp_mpio.columns]],
            on="COD_MUNICIPIO",
            how="left",
            suffixes=("", "_DVP"),
        )
        if "DEPARTAMENTO_DVP" in df_mort.columns:
            df_mort["DEPARTAMENTO"] = df_mort["DEPARTAMENTO"].fillna(df_mort["DEPARTAMENTO_DVP"]) if "DEPARTAMENTO" in df_mort.columns else df_mort["DEPARTAMENTO_DVP"]
            df_mort = df_mort.drop(columns=["DEPARTAMENTO_DVP"])
        if "COD_DEPARTAMENTO_DVP" in df_mort.columns:
            df_mort["COD_DEPARTAMENTO"] = df_mort["COD_DEPARTAMENTO"].fillna(df_mort["COD_DEPARTAMENTO_DVP"])
            df_mort = df_mort.drop(columns=["COD_DEPARTAMENTO_DVP"])

    # Cruce con códigos de muerte
    if "COD_CAUSA" in df_mort.columns and "COD_CAUSA" in df_cod.columns:
        df_mort = df_mort.merge(df_cod[["COD_CAUSA", "NOMBRE_CAUSA"]], on="COD_CAUSA", how="left")

    return df_mort


def _load_geojson() -> Optional[dict]:
    try:
        with urllib.request.urlopen(GEOJSON_URL, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] No se pudo descargar el geojson: {exc}")
        return None


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def upload_box(component_id: str, label: str) -> dcc.Upload:
    return dcc.Upload(
        id=component_id,
        children=html.Div([html.B(label), html.Br(), "Arrastra o haz clic para cargar"]),
        style={
            "width": "100%", "height": "90px", "lineHeight": "20px",
            "borderWidth": "2px", "borderStyle": "dashed", "borderRadius": "8px",
            "textAlign": "center", "padding": "15px", "backgroundColor": "#fafafa",
        },
        multiple=False,
    )


app.layout = html.Div(
    style={"fontFamily": "Segoe UI, Arial, sans-serif", "maxWidth": "1300px", "margin": "0 auto", "padding": "20px"},
    children=[
        html.H1("Análisis de Mortalidad en Colombia – 2019", style={"textAlign": "center", "color": "#003366"}),
        html.P(
            "Aplicación interactiva para explorar patrones demográficos y de salud pública "
            "a partir de los datos oficiales de mortalidad del DANE.",
            style={"textAlign": "center", "color": "#555"},
        ),
        html.Hr(),

        html.H3("1. Carga de archivos"),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "15px"},
            children=[
                upload_box("upload-nofetal", "NoFetal2019.xlsx"),
                upload_box("upload-codigos", "CodigosDeMuerte.xlsx"),
                upload_box("upload-divipola", "Divipola.xlsx"),
            ],
        ),
        html.Div(id="upload-status", style={"marginTop": "10px", "fontStyle": "italic"}),

        dcc.Store(id="store-nofetal"),
        dcc.Store(id="store-codigos"),
        dcc.Store(id="store-divipola"),
        dcc.Store(id="store-prepared"),

        html.Hr(),
        html.Div(id="dashboard-container"),
    ],
)


# ---------------------------------------------------------------------------
# Callbacks: almacenamiento de archivos cargados
# ---------------------------------------------------------------------------
def _store_callback(upload_id: str, store_id: str):
    @app.callback(
        Output(store_id, "data"),
        Input(upload_id, "contents"),
        State(upload_id, "filename"),
        prevent_initial_call=True,
    )
    def _store(contents, filename):  # noqa: ANN001
        df = parse_uploaded_excel(contents)
        if df is None:
            return dash.no_update
        return df.to_json(date_format="iso", orient="split")


_store_callback("upload-nofetal", "store-nofetal")
_store_callback("upload-codigos", "store-codigos")
_store_callback("upload-divipola", "store-divipola")


@app.callback(
    Output("store-prepared", "data"),
    Output("upload-status", "children"),
    Input("store-nofetal", "data"),
    Input("store-codigos", "data"),
    Input("store-divipola", "data"),
)
def consolidate(n_data, c_data, d_data):
    status = []
    status.append("NoFetal2019: " + ("✓ cargado" if n_data else "pendiente"))
    status.append("CodigosDeMuerte: " + ("✓ cargado" if c_data else "pendiente"))
    status.append("Divipola: " + ("✓ cargado" if d_data else "pendiente"))
    status_text = " | ".join(status)

    if not (n_data and c_data and d_data):
        return None, status_text

    try:
        df_n = pd.read_json(io.StringIO(n_data), orient="split")
        df_c = pd.read_json(io.StringIO(c_data), orient="split")
        df_d = pd.read_json(io.StringIO(d_data), orient="split")
        prepared = prepare_datasets(df_n, df_c, df_d)
        return prepared.to_json(date_format="iso", orient="split"), status_text + " — Datos consolidados ✓"
    except Exception as exc:  # noqa: BLE001
        return None, f"{status_text} — Error consolidando: {exc}"


# ---------------------------------------------------------------------------
# Callback principal: renderiza el dashboard cuando los datos están listos
# ---------------------------------------------------------------------------
@app.callback(
    Output("dashboard-container", "children"),
    Input("store-prepared", "data"),
)
def render_dashboard(prepared_json):
    if not prepared_json:
        return html.Div(
            "Cargue los tres archivos Excel para habilitar las visualizaciones.",
            style={"textAlign": "center", "padding": "40px", "color": "#888"},
        )

    df = pd.read_json(io.StringIO(prepared_json), orient="split")

    # 1) Mapa coroplético
    map_fig = build_choropleth(df)

    # 2) Línea: muertes por mes
    line_fig = build_line_chart(df)

    # 3) Barras: 5 ciudades más violentas (homicidios X95)
    bar_violent_fig = build_violent_cities(df)

    # 4) Circular: 10 municipios con menor mortalidad
    pie_fig = build_lowest_cities(df)

    # 5) Tabla: 10 principales causas de muerte
    table_data, table_cols = build_top_causes(df)

    # 6) Stacked bar: muertes por sexo y departamento
    stacked_fig = build_stacked_sex(df)

    # 7) Histograma por ciclo de vida
    hist_fig = build_life_cycle(df)

    section = lambda title, child: html.Div(  # noqa: E731
        [html.H3(title, style={"color": "#003366", "marginTop": "30px"}), child]
    )

    return html.Div(
        [
            section("2.1 Mapa: muertes por departamento", dcc.Graph(figure=map_fig)),
            section("2.2 Muertes totales por mes (2019)", dcc.Graph(figure=line_fig)),
            section("2.3 5 municipios más violentos (homicidios CIE-10 X95)", dcc.Graph(figure=bar_violent_fig)),
            section("2.4 10 municipios con menor mortalidad", dcc.Graph(figure=pie_fig)),
            section(
                "2.5 Top 10 causas de muerte",
                dash_table.DataTable(
                    data=table_data,
                    columns=table_cols,
                    style_cell={"textAlign": "left", "padding": "8px", "fontFamily": "Segoe UI"},
                    style_header={"backgroundColor": "#003366", "color": "white", "fontWeight": "bold"},
                    style_table={"overflowX": "auto"},
                    page_size=10,
                ),
            ),
            section("2.6 Muertes por sexo y departamento", dcc.Graph(figure=stacked_fig)),
            section("2.7 Distribución por ciclo de vida (GRUPO_EDAD1)", dcc.Graph(figure=hist_fig)),
        ]
    )


# ---------------------------------------------------------------------------
# Constructores de figuras
# ---------------------------------------------------------------------------
def build_choropleth(df: pd.DataFrame):
    if "DEPARTAMENTO" not in df.columns:
        return px.scatter(title="Datos insuficientes para el mapa")

    agg = df.groupby("DEPARTAMENTO", dropna=True).size().reset_index(name="TOTAL_MUERTES")
    geojson = _load_geojson()

    if geojson is None:
        # Fallback: barras horizontales por departamento
        fig = px.bar(
            agg.sort_values("TOTAL_MUERTES", ascending=True),
            x="TOTAL_MUERTES", y="DEPARTAMENTO", orientation="h",
            title="Muertes por departamento (mapa no disponible offline)",
            color="TOTAL_MUERTES", color_continuous_scale="Reds",
        )
        fig.update_layout(height=700)
        return fig

    # Normalización de nombres para hacer match con el geojson
    agg["DEPARTAMENTO_NORM"] = agg["DEPARTAMENTO"].str.upper().str.strip()

    fig = px.choropleth(
        agg,
        geojson=geojson,
        locations="DEPARTAMENTO_NORM",
        featureidkey="properties.DPTO_CNMBR",
        color="TOTAL_MUERTES",
        color_continuous_scale="Reds",
        hover_name="DEPARTAMENTO",
        labels={"TOTAL_MUERTES": "Total muertes"},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=600)
    return fig


def build_line_chart(df: pd.DataFrame):
    if "MES" not in df.columns:
        return px.scatter(title="Columna MES no disponible")
    agg = df.groupby("MES").size().reset_index(name="TOTAL")
    agg = agg.dropna(subset=["MES"]).sort_values("MES")
    agg["MES_NOMBRE"] = agg["MES"].map(MESES_ES)
    fig = px.line(agg, x="MES_NOMBRE", y="TOTAL", markers=True,
                  labels={"MES_NOMBRE": "Mes", "TOTAL": "Total muertes"})
    fig.update_traces(line_color="#003366")
    return fig


def build_violent_cities(df: pd.DataFrame):
    if "COD_CAUSA" not in df.columns or "MUNICIPIO" not in df.columns:
        return px.scatter(title="Datos insuficientes para homicidios")
    mask = df["COD_CAUSA"].str.startswith(tuple(CIE10_HOMICIDIOS), na=False)
    sub = df[mask]
    if sub.empty:
        return px.scatter(title="No se encontraron registros para los códigos X95")
    agg = sub.groupby("MUNICIPIO").size().reset_index(name="HOMICIDIOS")
    agg = agg.nlargest(5, "HOMICIDIOS")
    fig = px.bar(agg, x="MUNICIPIO", y="HOMICIDIOS", color="HOMICIDIOS",
                 color_continuous_scale="Reds", text="HOMICIDIOS")
    fig.update_traces(textposition="outside")
    return fig


def build_lowest_cities(df: pd.DataFrame):
    if "MUNICIPIO" not in df.columns:
        return px.scatter(title="Columna MUNICIPIO no disponible")
    agg = df.groupby("MUNICIPIO").size().reset_index(name="TOTAL")
    agg = agg[agg["TOTAL"] > 0].nsmallest(10, "TOTAL")
    fig = px.pie(agg, names="MUNICIPIO", values="TOTAL", hole=0.3)
    return fig


def build_top_causes(df: pd.DataFrame) -> Tuple[list, list]:
    if "COD_CAUSA" not in df.columns:
        return [], []
    grp_cols = ["COD_CAUSA"] + (["NOMBRE_CAUSA"] if "NOMBRE_CAUSA" in df.columns else [])
    agg = df.groupby(grp_cols, dropna=False).size().reset_index(name="TOTAL_CASOS")
    agg = agg.sort_values("TOTAL_CASOS", ascending=False).head(10)
    if "NOMBRE_CAUSA" not in agg.columns:
        agg["NOMBRE_CAUSA"] = "—"
    agg = agg.rename(columns={
        "COD_CAUSA": "Código de Causa",
        "NOMBRE_CAUSA": "Nombre de la Causa",
        "TOTAL_CASOS": "Total de Casos",
    })
    cols = [{"name": c, "id": c} for c in ["Código de Causa", "Nombre de la Causa", "Total de Casos"]]
    return agg.to_dict("records"), cols


def build_stacked_sex(df: pd.DataFrame):
    if "DEPARTAMENTO" not in df.columns or "SEXO" not in df.columns:
        return px.scatter(title="Datos insuficientes para gráfico por sexo")
    agg = df.groupby(["DEPARTAMENTO", "SEXO"]).size().reset_index(name="TOTAL")
    fig = px.bar(
        agg, x="DEPARTAMENTO", y="TOTAL", color="SEXO", barmode="stack",
        color_discrete_map={"Hombre": "#1f77b4", "Mujer": "#e377c2", "Indeterminado": "#7f7f7f"},
    )
    fig.update_layout(xaxis_tickangle=-45, height=550)
    return fig


def build_life_cycle(df: pd.DataFrame):
    if "GRUPO_EDAD1" not in df.columns:
        return px.scatter(title="Columna GRUPO_EDAD1 no disponible")
    sub = df.copy()
    sub["CICLO_VIDA"] = sub["GRUPO_EDAD1"].map(GRUPO_EDAD_MAP).fillna("Edad desconocida")
    agg = sub.groupby("CICLO_VIDA").size().reset_index(name="TOTAL")
    agg["CICLO_VIDA"] = pd.Categorical(agg["CICLO_VIDA"], categories=CICLO_ORDEN, ordered=True)
    agg = agg.sort_values("CICLO_VIDA")
    fig = px.bar(agg, x="CICLO_VIDA", y="TOTAL", color="CICLO_VIDA", text="TOTAL")
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, xaxis_tickangle=-30, height=500)
    return fig


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
