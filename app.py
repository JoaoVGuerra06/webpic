from flask import Flask, render_template, request
import dados_sus as sus
import traceback

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
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
            "index.html",
            grafico=grafico_html,
            erro=erro,
            procedimentos=sus.labels_procedimentos,
            graficos=list(sus.funcoes_graficos.keys()),
            datasets=sus.DATASETS_INFO,
        )

    except Exception:
        return f"<pre>{traceback.format_exc()}</pre>"


if __name__ == "__main__":
    app.run(debug=True)
