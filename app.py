"""
Aplicación web interactiva para el análisis de mortalidad en Colombia (2019).

Lee directamente los archivos Excel ubicados en la raíz del proyecto:
  - Anexo1.NoFetal2019_CE_15-03-23.xlsx
  - Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx
  - Divipola_CE_.xlsx

Autor: jose-i-rm
Framework: Dash + Plotly
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import plotly.express as px
from dash import Dash, dash_table, dcc, html

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# Resolución flexible: permite tanto los nombres "Anexo*..." como los nombres
# limpios solicitados originalmente.
DATA_FILES = {
    "mortalidad": ["Anexo1.NoFetal2019_CE_15-03-23.xlsx", "NoFetal2019.xlsx"],
    "codigos":    ["Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx", "CodigosDeMuerte.xlsx"],
    "divipola":   ["Divipola_CE_.xlsx", "Divipola.xlsx"],
}

GEOJSON_URL = (
    "https://raw.githubusercontent.com/caticoa3/colombia_mapa/master/"
    "co_2018_MGN_DPTO_POLITICO.geojson"
)

CIE10_HOMICIDIOS = ("X95",)  # Agresión con disparo de armas de fuego (no especificadas)

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
    "Mortalidad neonatal", "Mortalidad infantil", "Primera infancia", "Niñez",
    "Adolescencia", "Juventud", "Adultez temprana", "Adultez intermedia",
    "Vejez", "Longevidad / Centenarios", "Edad desconocida",
]

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


# ---------------------------------------------------------------------------
# Lectura y preparación de datos
# ---------------------------------------------------------------------------
def _resolve_file(candidates: list[str]) -> Path:
    for name in candidates:
        path = BASE_DIR / name
        if path.exists():
            return path
        path_data = BASE_DIR / "data" / name
        if path_data.exists():
            return path_data
    raise FileNotFoundError(
        f"No se encontró ninguno de los archivos esperados: {candidates}"
    )


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


def load_and_prepare() -> pd.DataFrame:
    """Carga los tres Excel y devuelve el dataset consolidado."""
    df_mort = pd.read_excel(_resolve_file(DATA_FILES["mortalidad"]), engine="openpyxl")
    df_cod = pd.read_excel(_resolve_file(DATA_FILES["codigos"]), engine="openpyxl")
    df_divipola = pd.read_excel(_resolve_file(DATA_FILES["divipola"]), engine="openpyxl")

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

    if "COD_DEPARTAMENTO" in df_divipola.columns:
        df_divipola["COD_DEPARTAMENTO"] = pd.to_numeric(df_divipola["COD_DEPARTAMENTO"], errors="coerce").astype("Int64")
    if "COD_MUNICIPIO" in df_divipola.columns:
        df_divipola["COD_MUNICIPIO"] = pd.to_numeric(df_divipola["COD_MUNICIPIO"], errors="coerce").astype("Int64")

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

    # Cruce con Divipola
    if "COD_MUNICIPIO" in df_divipola.columns and "COD_MUNICIPIO" in df_mort.columns:
        keep = [c for c in ["COD_MUNICIPIO", "MUNICIPIO", "COD_DEPARTAMENTO", "DEPARTAMENTO"] if c in df_divipola.columns]
        dvp_mpio = df_divipola[keep].drop_duplicates(subset=["COD_MUNICIPIO"])
        df_mort = df_mort.merge(dvp_mpio, on="COD_MUNICIPIO", how="left", suffixes=("", "_DVP"))
        for col in ("DEPARTAMENTO", "COD_DEPARTAMENTO"):
            dvp_col = f"{col}_DVP"
            if dvp_col in df_mort.columns:
                if col in df_mort.columns:
                    df_mort[col] = df_mort[col].fillna(df_mort[dvp_col])
                else:
                    df_mort[col] = df_mort[dvp_col]
                df_mort = df_mort.drop(columns=[dvp_col])

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
# Constructores de figuras
# ---------------------------------------------------------------------------
def build_choropleth(df: pd.DataFrame):
    if "DEPARTAMENTO" not in df.columns:
        return px.scatter(title="Datos insuficientes para el mapa")
    agg = df.groupby("DEPARTAMENTO", dropna=True).size().reset_index(name="TOTAL_MUERTES")
    geojson = _load_geojson()
    if geojson is None:
        fig = px.bar(
            agg.sort_values("TOTAL_MUERTES", ascending=True),
            x="TOTAL_MUERTES", y="DEPARTAMENTO", orientation="h",
            title="Muertes por departamento (mapa no disponible offline)",
            color="TOTAL_MUERTES", color_continuous_scale="Reds",
        )
        fig.update_layout(height=700)
        return fig
    agg["DEPARTAMENTO_NORM"] = agg["DEPARTAMENTO"].str.upper().str.strip()
    fig = px.choropleth(
        agg, geojson=geojson, locations="DEPARTAMENTO_NORM",
        featureidkey="properties.DPTO_CNMBR",
        color="TOTAL_MUERTES", color_continuous_scale="Reds",
        hover_name="DEPARTAMENTO",
        labels={"TOTAL_MUERTES": "Total muertes"},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=600)
    return fig


def build_line_chart(df: pd.DataFrame):
    if "MES" not in df.columns:
        return px.scatter(title="Columna MES no disponible")
    agg = df.groupby("MES").size().reset_index(name="TOTAL").dropna(subset=["MES"]).sort_values("MES")
    agg["MES_NOMBRE"] = agg["MES"].map(MESES_ES)
    fig = px.line(agg, x="MES_NOMBRE", y="TOTAL", markers=True,
                  labels={"MES_NOMBRE": "Mes", "TOTAL": "Total muertes"})
    fig.update_traces(line_color="#003366")
    return fig


def build_violent_cities(df: pd.DataFrame):
    if "COD_CAUSA" not in df.columns or "MUNICIPIO" not in df.columns:
        return px.scatter(title="Datos insuficientes para homicidios")
    mask = df["COD_CAUSA"].str.startswith(CIE10_HOMICIDIOS, na=False)
    sub = df[mask]
    if sub.empty:
        return px.scatter(title="No se encontraron registros para los códigos X95")
    agg = sub.groupby("MUNICIPIO").size().reset_index(name="HOMICIDIOS").nlargest(5, "HOMICIDIOS")
    fig = px.bar(agg, x="MUNICIPIO", y="HOMICIDIOS", color="HOMICIDIOS",
                 color_continuous_scale="Reds", text="HOMICIDIOS")
    fig.update_traces(textposition="outside")
    return fig


def build_lowest_cities(df: pd.DataFrame):
    if "MUNICIPIO" not in df.columns:
        return px.scatter(title="Columna MUNICIPIO no disponible")
    agg = df.groupby("MUNICIPIO").size().reset_index(name="TOTAL")
    agg = agg[agg["TOTAL"] > 0].nsmallest(10, "TOTAL")
    return px.pie(agg, names="MUNICIPIO", values="TOTAL", hole=0.3)


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
# Inicialización de la app y carga única de datos
# ---------------------------------------------------------------------------
app = Dash(__name__, title="Mortalidad Colombia 2019")
server = app.server  # Exposición obligatoria para entornos de producción (gunicorn)

print("[INFO] Cargando datasets…")
DF = load_and_prepare()
print(f"[INFO] Dataset consolidado: {len(DF):,} registros.")

_table_data, _table_cols = build_top_causes(DF)


def _section(title: str, child):
    return html.Div([html.H3(title, style={"color": "#003366", "marginTop": "30px"}), child])


app.layout = html.Div(
    style={"fontFamily": "Segoe UI, Arial, sans-serif",
           "maxWidth": "1300px", "margin": "0 auto", "padding": "20px"},
    children=[
        html.H1("Análisis de Mortalidad en Colombia – 2019",
                style={"textAlign": "center", "color": "#003366"}),
        html.P(
            "Aplicación interactiva para explorar patrones demográficos y de salud "
            "pública a partir de los datos oficiales de mortalidad del DANE (2019).",
            style={"textAlign": "center", "color": "#555"},
        ),
        html.Hr(),

        _section("1. Mapa: muertes por departamento",
                 dcc.Graph(figure=build_choropleth(DF))),
        _section("2. Muertes totales por mes (2019)",
                 dcc.Graph(figure=build_line_chart(DF))),
        _section("3. 5 municipios más violentos (homicidios CIE-10 X95)",
                 dcc.Graph(figure=build_violent_cities(DF))),
        _section("4. 10 municipios con menor mortalidad",
                 dcc.Graph(figure=build_lowest_cities(DF))),
        _section(
            "5. Top 10 causas de muerte",
            dash_table.DataTable(
                data=_table_data, columns=_table_cols,
                style_cell={"textAlign": "left", "padding": "8px", "fontFamily": "Segoe UI"},
                style_header={"backgroundColor": "#003366", "color": "white", "fontWeight": "bold"},
                style_table={"overflowX": "auto"},
                page_size=10,
            ),
        ),
        _section("6. Muertes por sexo y departamento",
                 dcc.Graph(figure=build_stacked_sex(DF))),
        _section("7. Distribución por ciclo de vida (GRUPO_EDAD1)",
                 dcc.Graph(figure=build_life_cycle(DF))),
    ],
)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=True)
