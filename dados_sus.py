# -*- coding: utf-8 -*-
"""
dados_sus.py
------------
Carrega e processa os dados do SUS a partir do novo formato unificado:
  - 1 CSV por procedimento (meses de 2018 a 2024)
  - Colunas no formato "2018/Jan", "2018/Fev", ..., "2024/Dez"
  - Separador ";" e 4 linhas de cabeçalho (skiprows=4)
  - "-" representa zero

A partir do CSV mensal único, gera automaticamente:
  - "meses_181920"  → meses de 2018, 2019 e 2020
  - "meses_232424"  → meses de 2023 e 2024
  - "meses_total"   → todos os meses disponíveis (exceto 2021 e 2022)
  - "anos_total"    → soma anual por capital (exceto 2021 e 2022)
"""

import pandas as pd
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────
# POPULAÇÕES DAS CAPITAIS (censo/estimativa)
# ─────────────────────────────────────────────────────────────
pop_capitais = {
    "110020": 517709,
    "120040": 389001,
    "130260": 2303732,
    "140010": 485477,
    "150140": 1397315,
    "160030": 489676,
    "172100": 328499,
    "211130": 1089215,
    "221100": 905692,
    "230440": 2578483,
    "240810": 784249,
    "250750": 897633,
    "261160": 1588376,
    "270430": 994952,
    "280030": 630932,
    "292740": 2564204,
    "310620": 2415872,
    "320530": 343378,
    "330455": 6730729,
    "355030": 11904961,
    "410690": 1830795,
    "420540": 587486,
    "431490": 1388794,
    "500270": 962883,
    "510340": 691875,
    "520870": 1503256,
    "530010": 2996899,
}

cod_capitais = {
    "110020": "Porto Velho",
    "120040": "Rio Branco",
    "130260": "Manaus",
    "140010": "Boa Vista",
    "150140": "Belém",
    "160030": "Macapá",
    "172100": "Palmas",
    "211130": "São Luís",
    "221100": "Teresina",
    "230440": "Fortaleza",
    "240810": "Natal",
    "250750": "João Pessoa",
    "261160": "Recife",
    "270430": "Maceió",
    "280030": "Aracaju",
    "292740": "Salvador",
    "310620": "Belo Horizonte",
    "320530": "Vitória",
    "330455": "Rio de Janeiro",
    "355030": "São Paulo",
    "410690": "Curitiba",
    "420540": "Florianópolis",
    "431490": "Porto Alegre",
    "500270": "Campo Grande",
    "510340": "Cuiabá",
    "520870": "Goiânia",
    "530010": "Brasília",
}
# Qualidade dos dados por procedimento
# "bom" = dados estáveis e completos | "precario" = incompletos ou instáveis
QUALIDADE_DADOS = {
    "apoio_matricial_trabalhador":      "precario",
    "urgencia_observacao_24h":          "bom",
    "urgencia_atencao_basica":          "bom",
    "urgencia_atencao_especializada":   "bom",
    "urgencia_observacao_8h":           "precario",
    "urgencia_remocao":                 "precario",
    "urgencia_pequeno_queimado":        "precario",
    "matriciamento_pontos_atencao":     "precario",
    "regulacao_samu_192":               "precario",
    "samu_192_com_orientacao":          "bom",
    "samu_192_regulacao":               "bom",
    "tenecteplase_40mg":                "precario",
    "tenecteplase_50mg":                "precario",
}
# ─────────────────────────────────────────────────────────────
# CATÁLOGO DOS 13 PROCEDIMENTOS
# chave  → identificador interno (usado na URL e no dicionário)
# label  → nome legível para o usuário
# url    → link raw do GitHub para o CSV
# ─────────────────────────────────────────────────────────────
BASE = "https://raw.githubusercontent.com/JoaoVGuerra06/PesquisaDataSus/main/"

PROCEDIMENTOS_CONFIG = {
    "apoio_matricial_trabalhador": {
        "label": "Apoio Matricial em Saúde do Trabalhador",
        "url": BASE + "APOIO%20MATRICIAL%20EM%20SAUDE%20DO%20TRABALHADOR%20NA%20ATENCAO%20ESPECIALIZADA%2C%20URGENCIA%20E%20EMERGENCIA/apoiomatricialemsaudedotrabalhador.csv",
    },
    "urgencia_observacao_24h": {
        "label": "Atendimento de Urgência com Observação até 24h (Atenção Especializada)",
        "url": BASE + "ATENDIMENTO%20DE%20URGENCIA%20Com%20OBSERVACAO%20ATE%2024%20HORAS%20EM%20ATENCAO%20ESPECIALIZADA/atendimentodeurgenciacomatencaode24horas.csv",
    },
    "urgencia_atencao_basica": {
        "label": "Atendimento de Urgência em Atenção Básica",
        "url": BASE + "ATENDIMENTO%20DE%20URGENCIA%20EM%20ATENCAO%20BASICA/atendimentodeurgenciaematencaobasica.csv",
    },
    "urgencia_atencao_especializada": {
        "label": "Atendimento de Urgência em Atenção Especializada",
        "url": BASE + "ATENDIMENTO%20DE%20URGENCIA%20EM%20ATENCAO%20ESPECIALIZADA/atendimentodeurgenciaematencaoespecializada.csv",
    },
    "urgencia_observacao_8h": {
        "label": "Atendimento de Urgência em Atenção Primária com Observação até 8h",
        "url": BASE + "ATENDIMENTO%20DE%20URGENCIA%20EM%20ATENCAO%20PRIMARIA%20COM%20OBSERVACAO%20ATE%208%20HORAS/atendimentodeurgenciaematencaoprimariacomobservacaodeate8horas.csv",
    },
    "urgencia_remocao": {
        "label": "Atendimento de Urgência em Atenção Primária com Remoção",
        "url": BASE + "ATENDIMENTO%20DE%20URGENCIA%20EM%20ATENCAO%20PRIMARIA%20COM%20REMOCAO/atendimentodeurgenciacomremocao.csv",
    },
    "urgencia_pequeno_queimado": {
        "label": "Atendimento de Urgência em Pequeno Queimado",
        "url": BASE + "ATENDIMENTO%20DE%20URGENCIA%20EM%20PEQUENO%20QUEIMADO/atendimentodeurgenciaempequenoqueimado.csv",
    },
    "matriciamento_pontos_atencao": {
        "label": "Matriciamento de Equipes dos Pontos de Atenção da Urgência e Emergência",
        "url": BASE + "MATRICIAMENTO%20DE%20EQUIPES%20DOS%20PONTOS%20DE%20ATENCAO%20DA%20URGENCIA%20E%20EMERGENCIA%2C%20E%20DOS%20SERVICOS%20HOSPITAL/matriciamentodeequipesdospontosdeatencao.csv",
    },
    "regulacao_samu_192": {
        "label": "Regulação Médica de Urgência da Central SAMU 192 com Acionamento de Múltiplos Meios",
        "url": BASE + "REGULACAO%20MEDICA%20DE%20URGENCIA%20DA%20CENTRAL%20SAMU%20192%20Com%20ACIONAMENTO%20DE%20MULTIPLOS%20MEIOS/regulacaomedicadeurgencia192.csv",
    },
    "samu_192_com_orientacao": {
        "label": "SAMU 192: Atendimento com Orientação",
        "url": BASE + "SAMU%20192%3A%20ATENDIMENTO%20DAS%20CHAMADAS%20RECEBIDAS%20PELA%20CENTRAL%20DE%20REGULACAO%20DAS%20URGENCIAS%20COM%20ORIENTAC/samu192comorientac.csv",
    },
    "samu_192_regulacao": {
        "label": "SAMU 192: Atendimento das Chamadas Recebidas pela Central de Regulação das Urgências",
        "url": BASE + "SAMU%20192%3AATENDIMENTO%20DAS%20CHAMADAS%20RECEBIDAS%20PELA%20CENTRAL%20DE%20REGULACAO%20DAS%20URGENCIAS/samu192regulacaodasurgencias.csv",
    },
    "tenecteplase_40mg": {
        "label": "Tenecteplase 40mg Injetável – Uso nas Urgências Pré-Hospitalares",
        "url": BASE + "TENECTEPLASE%2040%20MG%20INJETAVEL%20(POR%20FRASCO%20AMPOLA)%20DE%20USO%20NAS%20URGENCIAS%20PRE-HOSPITALARES/tenecteplase40.csv",
    },
    "tenecteplase_50mg": {
        "label": "Tenecteplase 50mg Injetável – Uso nas Urgências Pré-Hospitalares",
        "url": BASE + "TENECTEPLASE%2050%20MG%20INJETAVEL%20(POR%20FRASCO%20AMPOLA)%20DE%20USO%20NAS%20URGENCIAS%20PRE-HOSPITALARES/tenecteplase50.csv",
    },
}

# Anos a excluir dos gráficos (pandemia + lacuna nos dados)
ANOS_EXCLUIDOS = {2021, 2022}

# ─────────────────────────────────────────────────────────────
# FUNÇÕES DE PROCESSAMENTO
# ─────────────────────────────────────────────────────────────

def _carregar_csv_bruto(url: str) -> pd.DataFrame:
    """Lê o CSV no novo formato unificado."""
    df = pd.read_csv(
        url,
        sep=";",
        skiprows=4,          # 4 linhas de cabeçalho descritivo
        encoding="latin1",
        dtype=str,
    )
    # Remove coluna "Total" se existir
    df = df.drop(columns=["Total"], errors="ignore")
    return df


def _extrair_codigo(capital_str: str) -> str:
    """Extrai o código IBGE de 6 dígitos da string da capital."""
    import re
    m = re.search(r"(\d{6})", str(capital_str))
    return m.group(1) if m else None


def _colunas_por_anos(df: pd.DataFrame, anos: set) -> list:
    """Retorna nomes de colunas cujo ano (prefixo 'AAAA/') está no conjunto."""
    resultado = []
    for col in df.columns:
        try:
            ano = int(col.split("/")[0])
            if ano in anos:
                resultado.append(col)
        except (ValueError, IndexError):
            pass
    return resultado


def percapita_novo(url: str) -> dict[str, pd.DataFrame]:
    """
    Lê um CSV unificado e devolve um dicionário com 4 DataFrames per capita:
      - "meses_181920"  → meses de 2018–2020
      - "meses_2324"    → meses de 2023–2024
      - "meses_total"   → todos os meses exceto 2021 e 2022
      - "anos_total"    → soma anual por capital (exceto 2021 e 2022)

    Linhas sem correspondência populacional são descartadas silenciosamente.
    DataFrames vazios (procedimento sem dados) são retornados como estão.
    """
    try:
        df_bruto = _carregar_csv_bruto(url)
    except Exception as e:
        print(f"[AVISO] Não foi possível carregar {url}: {e}")
        return {}

    # --- 1. Identificar coluna de capital e extrair código IBGE ---
    col_capital = df_bruto.columns[0]
    df_bruto["_codigo"] = df_bruto[col_capital].apply(_extrair_codigo)

    # --- 2. Filtrar apenas capitais conhecidas ---
    pop_df = pd.DataFrame({
        "_codigo": list(pop_capitais.keys()),
        "_pop": list(pop_capitais.values()),
    })
    df = df_bruto.merge(pop_df, on="_codigo", how="inner").set_index("_codigo")

    if df.empty:
        print(f"[AVISO] Nenhuma capital reconhecida para {url}")
        return {}

    # Descarta colunas não-numéricas (capital original, etc.)
    colunas_mes = [c for c in df.columns if "/" in c]
    pop_serie = df["_pop"]

    def _montar_df_percapita(colunas: list) -> pd.DataFrame:
        """Converte subconjunto de colunas para per capita (por 100k hab)."""
        if not colunas:
            return pd.DataFrame()
        sub = df[colunas].copy()
        sub = sub.replace("-", 0).apply(pd.to_numeric, errors="coerce").fillna(0)
        return sub.div(pop_serie, axis=0) * 100_000

    # --- 3. Montar os 4 DataFrames ---
    anos_disponiveis = set()
    for c in colunas_mes:
        try:
            anos_disponiveis.add(int(c.split("/")[0]))
        except ValueError:
            pass

    anos_validos = anos_disponiveis - ANOS_EXCLUIDOS
    anos_181920  = anos_validos & {2018, 2019, 2020}
    anos_2324    = anos_validos & {2023, 2024}

    resultado = {
        "meses_181920": _montar_df_percapita(_colunas_por_anos(df, anos_181920)),
        "meses_2324":   _montar_df_percapita(_colunas_por_anos(df, anos_2324)),
        "meses_total":  _montar_df_percapita(_colunas_por_anos(df, anos_validos)),
        "anos_total":   pd.DataFrame(),
    }

    # --- 4. Anos totais: soma por ano ---
    if anos_validos:
        blocos_anuais = {}
        for ano in sorted(anos_validos):
            cols = _colunas_por_anos(df, {ano})
            if cols:
                sub = df[cols].replace("-", 0).apply(pd.to_numeric, errors="coerce").fillna(0)
                blocos_anuais[str(ano)] = sub.sum(axis=1)

        if blocos_anuais:
            df_anos = pd.DataFrame(blocos_anuais)
            resultado["anos_total"] = df_anos.div(pop_serie, axis=0) * 100_000

    return resultado


# ─────────────────────────────────────────────────────────────
# CARREGAMENTO EM MASSA DOS 13 PROCEDIMENTOS
# ─────────────────────────────────────────────────────────────

print("Carregando dados do SUS...")

todos_procedimentos: dict[str, dict[str, pd.DataFrame]] = {}

for chave, config in PROCEDIMENTOS_CONFIG.items():
    print(f"  → {config['label'][:60]}...")
    todos_procedimentos[chave] = percapita_novo(config["url"])

print("Dados carregados.\n")

# Rótulos legíveis para o HTML (chave → label)
labels_procedimentos = {k: v["label"] for k, v in PROCEDIMENTOS_CONFIG.items()}

# Datasets disponíveis e seus rótulos de exibição
DATASETS_INFO = {
    "meses_181920": "Meses 2018–2020",
    "meses_2324":   "Meses 2023–2024",
    "meses_total":  "Meses (total, sem 2021/2022)",
    "anos_total":   "Soma Anual (sem 2021/2022)",
}

# ─────────────────────────────────────────────────────────────
# FUNÇÕES DE PLOTAGEM
# ─────────────────────────────────────────────────────────────

def _titulo(proc_key: str, dataset_key: str) -> str:
    label_proc    = labels_procedimentos.get(proc_key, proc_key)
    label_dataset = DATASETS_INFO.get(dataset_key, dataset_key)
    return f"{label_proc}<br><sup>{label_dataset}</sup>"


def _df_valido(todos_procedimentos, proc_key: str, dataset_key: str):
    """Retorna o DataFrame correspondente ou None se vazio/ausente."""
    dfs = todos_procedimentos.get(proc_key, {})
    df = dfs.get(dataset_key)
    if df is None or df.empty:
        return None
    return df


def plot_linhas(proc_key: str, dataset_key: str) -> go.Figure:
    df = _df_valido(todos_procedimentos, proc_key, dataset_key)
    fig = go.Figure()
    if df is None:
        fig.update_layout(title="Sem dados para este procedimento/período.")
        return fig
    for codigo in df.index:
        nome = cod_capitais.get(str(codigo), str(codigo))
        fig.add_trace(go.Scatter(x=df.columns, y=df.loc[codigo], mode="lines", name=nome))
    fig.update_layout(
        title=_titulo(proc_key, dataset_key),
        xaxis_title="Período",
        yaxis_title="Atendimentos por 100k hab",
        width=1200, height=700,
    )
    return fig


def plot_barras(proc_key: str, dataset_key: str) -> go.Figure:
    df = _df_valido(todos_procedimentos, proc_key, dataset_key)
    fig = go.Figure()
    if df is None:
        fig.update_layout(title="Sem dados para este procedimento/período.")
        return fig
    buttons = []
    for i, codigo in enumerate(df.index):
        nome = cod_capitais.get(str(codigo), str(codigo))
        fig.add_trace(go.Bar(x=df.columns, y=df.loc[codigo], name=nome, visible=(i == 0)))
        visible = [False] * len(df)
        visible[i] = True
        buttons.append(dict(label=nome, method="update",
                            args=[{"visible": visible}, {"title": f"{nome}"}]))
    fig.update_layout(
        updatemenus=[dict(active=0, buttons=buttons, x=0.01, xanchor="left", y=1.15)],
        title=_titulo(proc_key, dataset_key),
        xaxis_title="Período",
        yaxis_title="Atendimentos por 100k hab",
        width=1200, height=700,
    )
    return fig


def plot_barras_stack(proc_key: str, dataset_key: str) -> go.Figure:
    df = _df_valido(todos_procedimentos, proc_key, dataset_key)
    fig = go.Figure()
    if df is None:
        fig.update_layout(title="Sem dados para este procedimento/período.")
        return fig
    for codigo in df.index:
        nome = cod_capitais.get(str(codigo), str(codigo))
        fig.add_trace(go.Bar(x=df.columns, y=df.loc[codigo], name=nome))
    fig.update_layout(
        barmode="stack",
        title=_titulo(proc_key, dataset_key),
        xaxis_title="Período",
        yaxis_title="Atendimentos por 100k hab",
        width=1200, height=700,
    )
    return fig


def plot_heatmap(proc_key: str, dataset_key: str) -> go.Figure:
    df = _df_valido(todos_procedimentos, proc_key, dataset_key)
    fig = go.Figure()
    if df is None:
        fig.update_layout(title="Sem dados para este procedimento/período.")
        return fig
    nomes = [cod_capitais.get(str(c), str(c)) for c in df.index]
    fig.add_trace(go.Heatmap(z=df.values, x=df.columns, y=nomes, colorscale="turbo"))
    fig.update_layout(
        title=_titulo(proc_key, dataset_key),
        xaxis_title="Período",
        yaxis_title="Capital",
        width=1200, height=700,
    )
    return fig


def plot_area(proc_key: str, dataset_key: str) -> go.Figure:
    df = _df_valido(todos_procedimentos, proc_key, dataset_key)
    fig = go.Figure()
    if df is None:
        fig.update_layout(title="Sem dados para este procedimento/período.")
        return fig
    for codigo in df.index:
        nome = cod_capitais.get(str(codigo), str(codigo))
        fig.add_trace(go.Scatter(x=df.columns, y=df.loc[codigo],
                                 mode="lines", stackgroup="one", name=nome))
    fig.update_layout(
        title=_titulo(proc_key, dataset_key),
        xaxis_title="Período",
        yaxis_title="Atendimentos por 100k hab",
        width=1200, height=700,
    )
    return fig


# Mapa de funções de plotagem (usado pelo app.py)
funcoes_graficos = {
    "linhas":       plot_linhas,
    "barras":       plot_barras,
    "barras_stack": plot_barras_stack,
    "heatmap":      plot_heatmap,
    "area":         plot_area,
}
