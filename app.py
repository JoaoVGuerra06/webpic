from flask import Flask, render_template, request
import backup3icsus as dados
import traceback

app = Flask(__name__)

# Mapear procedimentos disponíveis
procedimentos = {
    "samu": dados.dfs1,
    "samu_orientacao": dados.dfs2
}

# Mapear funções de gráficos
graficos = {
    "linhas": dados.plot_linhas,
    "barras": dados.plot_barras,
    "barras_stack": dados.plot_barras_stack,
    "heatmap": dados.plot_heatmap,
    "area": dados.plot_area
}

@app.route("/", methods=["GET", "POST"])
def index():
    grafico_html = None

    if request.method == "POST":
        try:
            proc = request.form["procedimento"]
            tipo = request.form["grafico"]
            dataset = request.form["dataset"]

            dfs = procedimentos.get(proc)
            func = graficos.get(tipo)

            # 🔒 validações importantes
            if dfs is None:
                return "<h1>Procedimento inválido</h1>"

            if func is None:
                return "<h1>Tipo de gráfico inválido</h1>"

            if dataset not in dfs:
                return f"<h1>Dataset inválido: {dataset}</h1>"

            # 🎯 gerar gráfico
            fig = func(dfs, dataset, dados.cod_capitais)

            if fig is None:
                return "<h1>Erro: função não retornou gráfico</h1>"

            grafico_html = fig.to_html(full_html=False)

        except Exception:
            grafico_html = f"<pre>{traceback.format_exc()}</pre>"

    return render_template(
        "index.html",
        grafico=grafico_html,
        procedimentos=procedimentos.keys(),
        graficos=graficos.keys()
    )

if __name__ == "__main__":
    app.run()
