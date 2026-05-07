from flask import Flask, render_template, request
import dados_sus as sus
import pandas as pd
import plotly.express as px
import geopandas as gpd
import json
import traceback

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────
# GeoJSON dos estados brasileiros (carregado uma vez na startup)
# ─────────────────────────────────────────────────────────────
_geojson = None

def get_geojson():
    global _geojson
    if _geojson is None:
        url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        gdf = gpd.read_file(url)
        gdf = gdf.drop(columns=["created_at", "updated_at"], errors="ignore")
        _geojson = json.loads(gdf.to_json())
    return _geojson

# Mapeamento capital → estado (para o mapa coroplético por estado)
CAPITAL_PARA_ESTADO = {
    "Porto Velho": "Rondônia",       "Rio Branco": "Acre",
    "Manaus": "Amazonas",            "Boa Vista": "Roraima",
    "Belém": "Pará",                 "Macapá": "Amapá",
    "Palmas": "Tocantins",           "São Luís": "Maranhão",
    "Teresina": "Piauí",             "Fortaleza": "Ceará",
    "Natal": "Rio Grande do Norte",  "João Pessoa": "Paraíba",
    "Recife": "Pernambuco",          "Maceió": "Alagoas",
    "Aracaju": "Sergipe",            "Salvador": "Bahia",
    "Belo Horizonte": "Minas Gerais","Vitória": "Espírito Santo",
    "Rio de Janeiro": "Rio de Janeiro","São Paulo": "São Paulo",
    "Curitiba": "Paraná",            "Florianópolis": "Santa Catarina",
    "Porto Alegre": "Rio Grande do Sul","Campo Grande": "Mato Grosso do Sul",
    "Cuiabá": "Mato Grosso",         "Goiânia": "Goiás",
    "Brasília": "Distrito Federal",
}

def _montar_dados_mapa(proc_key: str):
    """
    A partir do df 'anos_total' do procedimento, gera:
      - df_long  → formato longo para o mapa animado
      - dados_json → JSON para o gráfico de detalhe no JS
    Retorna (None, None) se não houver dados.
    """
    dfs = sus.todos_procedimentos.get(proc_key, {})
    df_anos = dfs.get("anos_total")

    if df_anos is None or df_anos.empty:
        return None, None

    # df_anos: índice = código IBGE, colunas = "2018", "2019", ...
    # Converte índice em nome de capital
    df_anos = df_anos.copy()
    df_anos.index = df_anos.index.map(lambda c: sus.cod_capitais.get(str(c), str(c)))
    df_anos.index.name = "Capital"
    df_anos = df_anos.reset_index()

    # Adiciona nome do estado
    df_anos["nome_estado"] = df_anos["Capital"].map(CAPITAL_PARA_ESTADO)

    # Formato longo
    anos_cols = [c for c in df_anos.columns if c not in ("Capital", "nome_estado")]
    df_long = df_anos.melt(
        id_vars=["Capital", "nome_estado"],
        value_vars=anos_cols,
        var_name="Ano",
        value_name="Valor"
    ).dropna(subset=["nome_estado", "Valor"])

    df_long["Valor"] = pd.to_numeric(df_long["Valor"], errors="coerce").round(2)
    df_long = df_long.dropna(subset=["Valor"])

    # Ranking por ano
    df_long["Ranking"] = (
        df_long.groupby("Ano")["Valor"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    dados_json = df_long.to_json(orient="records", force_ascii=False)
    return df_long, dados_json


def _gerar_mapa_html(df_long: pd.DataFrame, geojson: dict, titulo: str) -> str:
    fig = px.choropleth(
        df_long,
        geojson=geojson,
        locations="nome_estado",
        featureidkey="properties.name",
        color="Valor",
        animation_frame="Ano",
        hover_name="nome_estado",
        hover_data={"Valor": ":.2f", "Ranking": True, "Ano": False},
        color_continuous_scale="YlOrRd",
        labels={"Valor": "Atend./100k hab"},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        title=titulo,
        font=dict(color="#fff", family="Arial, sans-serif"),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id="mapa")


# ─────────────────────────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/grafico", methods=["GET", "POST"])
def grafico():
    try:
        grafico_html = None
        erro = None

        if request.method == "POST":
            proc_key    = request.form.get("procedimento")
            tipo_graf   = request.form.get("grafico")
            dataset_key = request.form.get("dataset")

            func = sus.funcoes_graficos.get(tipo_graf)
            if func is None:
                erro = f"Tipo de gráfico desconhecido: {tipo_graf}"
            else:
                fig = func(proc_key, dataset_key)
                grafico_html = fig.to_html(full_html=False)

        return render_template(
            "grafico.html",
            grafico=grafico_html,
            erro=erro,
            procedimentos=sus.labels_procedimentos,
            graficos=list(sus.funcoes_graficos.keys()),
            datasets=sus.DATASETS_INFO,
        )
    except Exception:
        return f"<pre>{traceback.format_exc()}</pre>"


@app.route("/mapa", methods=["GET", "POST"])
def mapa():
    try:
        mapa_html    = None
        dados_json   = None
        proc_selecionado = None

        if request.method == "POST":
            proc_selecionado = request.form.get("procedimento")
            df_long, dados_json = _montar_dados_mapa(proc_selecionado)

            if df_long is not None:
                geojson = get_geojson()
                titulo  = sus.labels_procedimentos.get(proc_selecionado, proc_selecionado)
                mapa_html = _gerar_mapa_html(df_long, geojson, titulo)
            else:
                mapa_html = None

        return render_template(
            "mapa.html",
            mapa_html=mapa_html,
            dados_json=dados_json,
            proc_selecionado=proc_selecionado,
            procedimentos=sus.labels_procedimentos,
        )
    except Exception:
        return f"<pre>{traceback.format_exc()}</pre>"


if __name__ == "__main__":
    app.run(debug=True)
