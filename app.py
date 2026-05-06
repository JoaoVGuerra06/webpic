from flask import Flask, render_template, request
import backup3icsus as dados
import traceback

app = Flask(__name__)

# =========================
# DICIONÁRIOS
# =========================

procedimentos = {
    "samu": dados.dfs1,
    "samu_orientacao": dados.dfs2,
    "Urgencia_em_atencao_basica": dados.dfs3
}

graficos = {
    "linhas": dados.plot_linhas,
    "barras": dados.plot_barras,
    "barras_stack": dados.plot_barras_stack,
    "heatmap": dados.plot_heatmap,
    "area": dados.plot_area
}

# =========================
# PÁGINA INICIAL
# =========================

@app.route("/")
def index():
    return render_template("index.html")

# =========================
# PÁGINA DE GRÁFICOS
# =========================

@app.route("/graficos", methods=["GET", "POST"])
def graficos_page():

    try:

        grafico_html = None

        if request.method == "POST":

            proc = request.form.get("procedimento")
            tipo = request.form.get("grafico")
            dataset = request.form.get("dataset")

            dfs = procedimentos.get(proc)
            func = graficos.get(tipo)

            fig = func(dfs, dataset, dados.cod_capitais)

            grafico_html = fig.to_html(full_html=False)

        return render_template(
            "graficos.html",
            grafico=grafico_html,
            procedimentos=procedimentos.keys(),
            graficos=graficos.keys()
        )

    except Exception:
        return f"<pre>{traceback.format_exc()}</pre>"

# =========================
# PÁGINA DE MAPAS
# =========================

@app.route("/mapas", methods=["GET", "POST"])
def mapas():

    try:

        mapa_html = None

        if request.method == "POST":

            tipo_mapa = request.form.get("tipo_mapa")
            procedimento = request.form.get("procedimento")

            # AQUI você vai colocar sua lógica futura
            # exemplo:
            # fig = dados.plot_mapa(...)
            # mapa_html = fig.to_html(full_html=False)

        return render_template(
            "mapas.html",
            mapa=mapa_html
        )

    except Exception:
        return f"<pre>{traceback.format_exc()}</pre>"

# =========================
# EXECUÇÃO
# =========================

if __name__ == "__main__":
    app.run(debug=True)
