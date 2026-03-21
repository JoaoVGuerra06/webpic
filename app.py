from flask import Flask, render_template, request
import backup3icsus as dados
import traceback

app = Flask(__name__)

procedimentos = {
    "samu": dados.dfs1,
    "samu_orientacao": dados.dfs2
}

graficos = {
    "linhas": dados.plot_linhas,
    "barras": dados.plot_barras,
    "barras_stack": dados.plot_barras_stack,
    "heatmap": dados.plot_heatmap,
    "area": dados.plot_area
}

@app.route("/", methods=["GET", "POST"])
def index():
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
            "index.html",
            grafico=grafico_html,
            procedimentos=procedimentos.keys(),
            graficos=graficos.keys()
        )

    except Exception:
        return f"<pre>{traceback.format_exc()}</pre>"

if __name__ == "__main__":
    app.run()
