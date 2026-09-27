from html import escape
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


ARQUIVO_DADOS = Path(__file__).with_name("resultados_ansys.csv")

COR_FUNDO = "#0A1420"
COR_PAINEL = "#0F1D2E"
COR_PAINEL_ALT = "#122236"
COR_GRADE = "#1C3049"
COR_LINHA = "#25405E"
COR_TEXTO = "#E8EEF5"
COR_SUAVE = "#7C93AC"
COR_AZUL = "#4FA8E0"
COR_VERDE = "#3ECF8E"
COR_LARANJA = "#F2994A"
COR_VERMELHA = "#E85D5D"

MODULO_ELASTICIDADE_PA = 200e9
LIMITE_ESCOAMENTO_PA = 250e6


st.set_page_config(
    page_title="Painel Estrutural — ASTM A36",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    f"""
    <style>
    :root {{
        --bg: {COR_FUNDO};
        --panel: {COR_PAINEL};
        --panel-alt: {COR_PAINEL_ALT};
        --grid: {COR_GRADE};
        --line: {COR_LINHA};
        --text: {COR_TEXTO};
        --muted: {COR_SUAVE};
        --steel: {COR_AZUL};
        --mint: {COR_VERDE};
        --amber: {COR_LARANJA};
        --red: {COR_VERMELHA};
    }}

    .stApp {{
        background: var(--bg);
        color: var(--text);
    }}

    [data-testid="stHeader"] {{
        background: rgba(10, 20, 32, 0.90);
        border-bottom: 1px solid var(--line);
    }}

    [data-testid="stSidebar"] {{
        background: var(--panel-alt);
        border-right: 1px solid var(--line);
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1.25rem;
    }}

    .block-container {{
        max-width: 1680px;
        /* Reserva espaço para a barra fixa do Streamlit. */
        padding-top: 5.25rem !important;
        padding-bottom: 2rem;
    }}

    /* Evita que o primeiro elemento volte a subir por causa das margens
       responsivas aplicadas pelo Streamlit. */
    [data-testid="stMainBlockContainer"] {{
        padding-top: 5.25rem !important;
    }}

    h1, h2, h3, p, label, [data-testid="stCaptionContainer"] {{
        color: var(--text);
    }}

    .engineering-header {{
        padding: 0 0 1.25rem 0;
        margin-bottom: 1.25rem;
        border-bottom: 1px solid var(--line);
    }}

    .engineering-eyebrow {{
        color: var(--steel);
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.74rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }}

    .engineering-title {{
        color: var(--text);
        font-size: 2rem;
        line-height: 1.2;
        font-weight: 700;
        margin: 0;
    }}

    .engineering-subtitle {{
        color: var(--muted);
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.78rem;
        line-height: 1.55;
        margin-top: 0.45rem;
        max-width: 1100px;
    }}

    .section-band {{
        color: var(--steel);
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.76rem;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        margin: 1.1rem 0 0.7rem 0;
    }}

    .technical-card {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 0.45rem;
        padding: 1rem 1.1rem;
        min-height: 112px;
    }}

    .technical-card.good {{
        border-color: rgba(62, 207, 142, 0.65);
    }}

    .technical-label {{
        color: var(--muted);
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.68rem;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        min-height: 2.2em;
    }}

    .technical-value {{
        color: var(--text);
        font-size: 1.62rem;
        font-weight: 650;
        line-height: 1.25;
        margin-top: 0.35rem;
        white-space: nowrap;
    }}

    .technical-unit {{
        color: var(--muted);
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.76rem;
        font-weight: 400;
        margin-left: 0.25rem;
    }}

    .source-tag {{
        display: inline-block;
        color: var(--steel);
        border: 1px solid rgba(79, 168, 224, 0.45);
        border-radius: 0.3rem;
        padding: 0.28rem 0.48rem;
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.66rem;
        letter-spacing: 0.06em;
        margin-bottom: 0.75rem;
    }}

    .info-card {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 0.45rem;
        padding: 1rem 1.1rem;
        margin-bottom: 0.75rem;
    }}

    .info-card.good {{
        border-color: rgba(62, 207, 142, 0.65);
    }}

    .info-title {{
        color: var(--muted);
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }}

    .info-line {{
        color: var(--text);
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.78rem;
        line-height: 1.65;
    }}

    .muted {{ color: var(--muted); }}
    .safe {{ color: var(--mint); }}
    .warn {{ color: var(--amber); }}
    .danger {{ color: var(--red); }}

    .status-pill {{
        display: inline-block;
        border-radius: 999px;
        padding: 0.25rem 0.62rem;
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
    }}

    .status-safe {{
        color: var(--mint);
        border: 1px solid rgba(62, 207, 142, 0.55);
        background: rgba(62, 207, 142, 0.08);
    }}

    .status-warn {{
        color: var(--amber);
        border: 1px solid rgba(242, 153, 74, 0.55);
        background: rgba(242, 153, 74, 0.08);
    }}

    .status-danger {{
        color: var(--red);
        border: 1px solid rgba(232, 93, 93, 0.55);
        background: rgba(232, 93, 93, 0.08);
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid var(--line);
        border-radius: 0.45rem;
        overflow: hidden;
    }}

    [data-testid="stAlert"] {{
        border: 1px solid var(--line);
        background: var(--panel-alt);
        color: var(--text);
    }}

    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {{
        background: var(--panel);
        border-color: var(--line);
    }}

    hr {{
        border-color: var(--line);
    }}

    .method-card {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 0.45rem;
        padding: 1rem;
        min-height: 126px;
    }}

    .method-label {{
        color: var(--muted);
        font-size: 0.72rem;
        margin-bottom: 0.45rem;
    }}

    .method-line {{
        color: var(--text);
        font-size: 1rem;
        font-weight: 600;
        margin: 0.22rem 0;
    }}

    .engineering-footer {{
        color: var(--muted);
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.7rem;
        line-height: 1.65;
        margin-top: 1.5rem;
        padding-top: 0.85rem;
        border-top: 1px solid var(--line);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def numero_br(valor, casas=2):
    if valor is None or pd.isna(valor):
        return "—"

    return f"{float(valor):.{casas}f}".replace(".", ",")


def cartao_metrica(rotulo, valor, unidade="", destaque=""):
    classe = f" {destaque}" if destaque else ""
    unidade_html = (
        f'<span class="technical-unit">{escape(unidade)}</span>'
        if unidade
        else ""
    )

    return f"""
    <div class="technical-card{classe}">
        <div class="technical-label">{escape(rotulo)}</div>
        <div class="technical-value">
            {escape(str(valor))}{unidade_html}
        </div>
    </div>
    """


def faixa_secao(numero, titulo):
    st.markdown(
        f'<div class="section-band">{numero}. {escape(titulo)}</div>',
        unsafe_allow_html=True,
    )


def estilizar_grafico(grafico):
    return (
        grafico
        .configure(background="transparent")
        .configure_view(stroke=COR_LINHA)
        .configure_axis(
            labelColor=COR_SUAVE,
            titleColor=COR_SUAVE,
            gridColor=COR_GRADE,
            domainColor=COR_LINHA,
            tickColor=COR_LINHA,
            labelFont="Consolas",
            titleFont="Consolas",
        )
        .configure_title(
            color=COR_TEXTO,
            font="Segoe UI",
            fontSize=13,
            anchor="start",
        )
        .configure_legend(
            labelColor=COR_SUAVE,
            titleColor=COR_SUAVE,
        )
    )


def carregar_resultados():
    try:
        dados = pd.read_csv(ARQUIVO_DADOS)
    except (OSError, pd.errors.ParserError) as erro:
        st.error("Os resultados públicos do estudo não puderam ser carregados.")
        st.caption(f"Detalhe técnico: {erro}")
        st.stop()

    colunas_obrigatorias = {
        "simulacao_id",
        "simulacao",
        "viga",
        "material",
        "tamanho_malha_mm",
        "origem_dados",
        "tensao_von_mises_max_mpa",
        "deslocamento_total_max_mm",
        "deslocamento_y_min_mm",
        "deslocamento_y_max_mm",
        "fator_seguranca_min",
    }
    ausentes = colunas_obrigatorias.difference(dados.columns)
    if ausentes:
        st.error("O arquivo público não contém todas as colunas esperadas.")
        st.caption("Colunas ausentes: " + ", ".join(sorted(ausentes)))
        st.stop()

    resultados = [
        item
        for item in dados.to_dict(orient="records")
        if str(item.get("origem_dados", "")).strip().lower()
        == "ansys_rst"
    ]

    if not resultados:
        st.warning("O arquivo público não contém resultados reais do ANSYS.")
        st.stop()

    return sorted(
        resultados,
        key=lambda item: float(item["tamanho_malha_mm"]),
        reverse=True,
    )


def calcular_modelo_analitico(
    tipo_carregamento,
    vao_m,
    carga,
    largura_mm,
    altura_mm,
    quantidade_pontos=101,
):
    largura_m = largura_mm / 1000
    altura_m = altura_mm / 1000
    inercia_m4 = largura_m * altura_m**3 / 12
    fibra_extrema_m = altura_m / 2

    x = np.linspace(0, vao_m, quantidade_pontos)

    if tipo_carregamento == "Distribuída":
        carga_n_m = carga * 1000
        reacao_n = carga_n_m * vao_m / 2

        momento_nm = (
            reacao_n * x
            - carga_n_m * x**2 / 2
        )
        cortante_n = reacao_n - carga_n_m * x
        deslocamento_m = (
            carga_n_m
            * x
            * (vao_m**3 - 2 * vao_m * x**2 + x**3)
            / (24 * MODULO_ELASTICIDADE_PA * inercia_m4)
        )

    else:
        carga_n = carga * 1000
        reacao_n = carga_n / 2
        distancia_apoio = np.minimum(x, vao_m - x)

        momento_nm = reacao_n * distancia_apoio
        cortante_n = np.where(
            x < vao_m / 2,
            reacao_n,
            -reacao_n,
        )
        cortante_n[np.isclose(x, vao_m / 2)] = 0

        deslocamento_m = np.empty_like(x)
        lado_esquerdo = x <= vao_m / 2

        deslocamento_m[lado_esquerdo] = (
            carga_n
            * x[lado_esquerdo]
            * (
                3 * vao_m**2
                - 4 * x[lado_esquerdo] ** 2
            )
            / (48 * MODULO_ELASTICIDADE_PA * inercia_m4)
        )

        x_refletido = vao_m - x[~lado_esquerdo]
        deslocamento_m[~lado_esquerdo] = (
            carga_n
            * x_refletido
            * (3 * vao_m**2 - 4 * x_refletido**2)
            / (48 * MODULO_ELASTICIDADE_PA * inercia_m4)
        )

    tensao_pa = (
        np.abs(momento_nm)
        * fibra_extrema_m
        / inercia_m4
    )

    tensao_mpa = tensao_pa / 1e6
    deslocamento_mm = deslocamento_m * 1000

    fator_seguranca = np.divide(
        LIMITE_ESCOAMENTO_PA,
        tensao_pa,
        out=np.full_like(tensao_pa, np.nan),
        where=tensao_pa > 1,
    )

    dados = pd.DataFrame(
        {
            "x_m": x,
            "momento_kn_m": momento_nm / 1000,
            "cortante_kn": cortante_n / 1000,
            "tensao_mpa": tensao_mpa,
            "deslocamento_mm": deslocamento_mm,
            "fator_seguranca": fator_seguranca,
        }
    )

    tensao_maxima = float(np.max(tensao_mpa))
    deslocamento_maximo = float(np.max(deslocamento_mm))
    fs_minimo = (
        250 / tensao_maxima
        if tensao_maxima > 0
        else float("inf")
    )

    return {
        "dados": dados,
        "inercia_m4": inercia_m4,
        "tensao_maxima_mpa": tensao_maxima,
        "deslocamento_maximo_mm": deslocamento_maximo,
        "fator_seguranca_minimo": fs_minimo,
    }


def obter_status(fator_seguranca):
    if fator_seguranca < 1.5:
        return "CRÍTICO", "danger", "status-danger"

    if fator_seguranca < 3:
        return "ATENÇÃO", "warn", "status-warn"

    return "SEGURO", "safe", "status-safe"


resultados = carregar_resultados()


st.markdown(
    """
    <div class="engineering-header">
        <div class="engineering-eyebrow">
            ANSYS 2026 R1 → PyDPF/Python → CSV → Streamlit
        </div>
        <div class="engineering-title">
            Painel Estrutural — Viga em Aço ASTM A36
        </div>
        <div class="engineering-subtitle">
            Demonstração pública com uma cópia dos resultados reais extraídos dos
            arquivos RST. O sistema local completo utiliza MySQL e FastAPI. Os
            controles não reexecutam o ANSYS nem alteram os resultados apresentados.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("### Parâmetros")
    st.caption(
        "Os controles abaixo modificam somente o modelo analítico."
    )

    malhas_disponiveis = sorted(
        {
            float(item["tamanho_malha_mm"])
            for item in resultados
        }
    )

    malha_selecionada = st.selectbox(
        "Resultado ANSYS exibido",
        options=malhas_disponiveis,
        index=0,
        format_func=lambda valor: f"Malha {valor:g} mm",
    )

    st.divider()

    tipo_carregamento = st.radio(
        "Tipo de carregamento",
        options=["Distribuída", "Pontual no meio do vão"],
        horizontal=True,
    )

    vao_m = st.slider(
        "Vão L (m)",
        min_value=1.0,
        max_value=6.0,
        value=3.0,
        step=0.1,
    )

    if tipo_carregamento == "Distribuída":
        carga = st.slider(
            "Carga distribuída (kN/m)",
            min_value=1.0,
            max_value=20.0,
            value=8.0,
            step=0.5,
        )
    else:
        carga = st.slider(
            "Carga pontual (kN)",
            min_value=2.0,
            max_value=40.0,
            value=15.0,
            step=0.5,
        )

    largura_mm = st.slider(
        "Largura b (mm)",
        min_value=20,
        max_value=150,
        value=50,
        step=5,
    )

    altura_mm = st.slider(
        "Altura h (mm)",
        min_value=50,
        max_value=300,
        value=150,
        step=5,
    )

    st.divider()
    st.markdown(
        """
        **Material — ASTM A36**

        `E = 200 GPa`  
        `ν = 0,26`  
        `σy = 250 MPa`
        """
    )


resultado_real = min(
    resultados,
    key=lambda item: abs(
        float(item["tamanho_malha_mm"])
        - malha_selecionada
    ),
)

modelo = calcular_modelo_analitico(
    tipo_carregamento=tipo_carregamento,
    vao_m=vao_m,
    carga=carga,
    largura_mm=largura_mm,
    altura_mm=altura_mm,
)

status_analitico, classe_analitica, pill_analitica = obter_status(
    modelo["fator_seguranca_minimo"]
)
status_real, classe_real, pill_real = obter_status(
    float(resultado_real["fator_seguranca_min"])
)


faixa_secao("1", "Dados reais do estudo — ANSYS 2026 R1 / PyDPF")

st.markdown(
    f"""
    <div class="info-card good">
        <div class="source-tag">RESULTADOS REAIS — SNAPSHOT CSV / file.rst</div>
        <div class="info-title">
            Modelo numérico selecionado — malha de
            {numero_br(resultado_real['tamanho_malha_mm'], 0)} mm
        </div>
        <div class="info-line">
            <strong>{escape(str(resultado_real['viga']))}</strong>
            <span class="muted"> · </span>
            {escape(str(resultado_real['material']))}
            <span class="muted"> · origem:</span>
            {escape(str(resultado_real['origem_dados']))}
            &nbsp;&nbsp;
            <span class="status-pill {pill_real}">{status_real}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

colunas_reais = st.columns(5)
metricas_reais = [
    (
        "Tensão de von Mises máxima",
        numero_br(resultado_real["tensao_von_mises_max_mpa"], 6),
        "MPa",
    ),
    (
        "Deslocamento total máximo",
        numero_br(resultado_real["deslocamento_total_max_mm"], 6),
        "mm",
    ),
    (
        "Deslocamento Y mínimo",
        numero_br(resultado_real["deslocamento_y_min_mm"], 6),
        "mm",
    ),
    (
        "Fator de segurança mínimo",
        numero_br(resultado_real["fator_seguranca_min"], 6),
        "",
    ),
    (
        "Tamanho da malha",
        numero_br(resultado_real["tamanho_malha_mm"], 0),
        "mm",
    ),
]

for coluna, (rotulo, valor, unidade) in zip(
    colunas_reais,
    metricas_reais,
):
    with coluna:
        st.markdown(
            cartao_metrica(
                rotulo,
                valor,
                unidade,
                "good" if rotulo == "Fator de segurança mínimo" else "",
            ),
            unsafe_allow_html=True,
        )

st.caption(
    "Deslocamento Y máximo: "
    f"{numero_br(resultado_real['deslocamento_y_max_mm'], 6)} mm. "
    "Os valores deste bloco permanecem fixos quando os sliders são alterados."
)


faixa_secao("2", "Modelo analítico interativo — Euler–Bernoulli")

colunas_analiticas = st.columns(4)
metricas_analiticas = [
    (
        "Analítico — tensão máxima",
        numero_br(modelo["tensao_maxima_mpa"], 3),
        "MPa",
        "",
    ),
    (
        "Analítico — deslocamento máximo",
        numero_br(modelo["deslocamento_maximo_mm"], 3),
        "mm",
        "",
    ),
    (
        "Analítico — fator de segurança",
        numero_br(modelo["fator_seguranca_minimo"], 3),
        "",
        classe_analitica,
    ),
    (
        "Status analítico",
        status_analitico,
        "",
        classe_analitica,
    ),
]

for coluna, (rotulo, valor, unidade, destaque) in zip(
    colunas_analiticas,
    metricas_analiticas,
):
    with coluna:
        st.markdown(
            cartao_metrica(rotulo, valor, unidade, destaque),
            unsafe_allow_html=True,
        )

st.markdown(
    f"""
    <div class="info-card">
        <div class="info-title">Parâmetros analíticos atuais</div>
        <div class="info-line">
            Carregamento: <strong>{escape(tipo_carregamento)}</strong>
            <span class="muted"> · </span>
            L = {numero_br(vao_m, 2)} m
            <span class="muted"> · </span>
            b × h = {largura_mm} × {altura_mm} mm
            <span class="muted"> · </span>
            I = {modelo['inercia_m4']:.6e} m⁴
            <span class="muted"> · </span>
            <span class="status-pill {pill_analitica}">{status_analitico}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

dados_analiticos = modelo["dados"].copy()
dados_analiticos["deformada_mm"] = -dados_analiticos[
    "deslocamento_mm"
]

linha_deformada = (
    alt.Chart(dados_analiticos)
    .mark_line(color=COR_AZUL, strokeWidth=5)
    .encode(
        x=alt.X("x_m:Q", title="Posição ao longo do vão (m)"),
        y=alt.Y(
            "deformada_mm:Q",
            title="Deslocamento vertical (mm)",
            scale=alt.Scale(zero=True),
        ),
        tooltip=[
            alt.Tooltip("x_m:Q", title="x (m)", format=".3f"),
            alt.Tooltip(
                "deslocamento_mm:Q",
                title="δ (mm)",
                format=".4f",
            ),
            alt.Tooltip(
                "tensao_mpa:Q",
                title="σ (MPa)",
                format=".3f",
            ),
        ],
    )
    .properties(
        title="Modelo analítico — deformada da viga",
        height=230,
    )
)

linha_referencia = (
    alt.Chart(pd.DataFrame({"y": [0]}))
    .mark_rule(color=COR_SUAVE, strokeDash=[5, 5])
    .encode(y="y:Q")
)

st.altair_chart(
    estilizar_grafico(linha_referencia + linha_deformada),
    width="stretch",
)

grafico_tensao_analitica = (
    alt.Chart(dados_analiticos)
    .mark_area(
        line={"color": COR_AZUL, "strokeWidth": 2},
        color=COR_AZUL,
        opacity=0.20,
    )
    .encode(
        x=alt.X("x_m:Q", title="x (m)"),
        y=alt.Y(
            "tensao_mpa:Q",
            title="Tensão de flexão (MPa)",
        ),
        tooltip=[
            alt.Tooltip("x_m:Q", title="x (m)", format=".3f"),
            alt.Tooltip(
                "tensao_mpa:Q",
                title="Tensão (MPa)",
                format=".3f",
            ),
        ],
    )
    .properties(
        title="Tensão equivalente ao longo do vão",
        height=260,
    )
)

grafico_momento = (
    alt.Chart(dados_analiticos)
    .mark_line(color=COR_VERDE, strokeWidth=2)
    .encode(
        x=alt.X("x_m:Q", title="x (m)"),
        y=alt.Y(
            "momento_kn_m:Q",
            title="Momento fletor (kN·m)",
        ),
        tooltip=[
            alt.Tooltip("x_m:Q", title="x (m)", format=".3f"),
            alt.Tooltip(
                "momento_kn_m:Q",
                title="Momento (kN·m)",
                format=".3f",
            ),
        ],
    )
    .properties(
        title="Momento fletor ao longo do vão",
        height=260,
    )
)

coluna_analitica_1, coluna_analitica_2 = st.columns(2)

with coluna_analitica_1:
    st.altair_chart(
        estilizar_grafico(grafico_tensao_analitica),
        width="stretch",
    )

with coluna_analitica_2:
    st.altair_chart(
        estilizar_grafico(grafico_momento),
        width="stretch",
    )

with st.expander("Resultados analíticos ao longo do vão"):
    passo = max(len(dados_analiticos) // 10, 1)
    tabela_analitica = dados_analiticos.iloc[::passo].copy()
    tabela_analitica = tabela_analitica.rename(
        columns={
            "x_m": "x (m)",
            "momento_kn_m": "M (kN·m)",
            "cortante_kn": "V (kN)",
            "tensao_mpa": "σ (MPa)",
            "deslocamento_mm": "δ (mm)",
            "fator_seguranca": "FS",
        }
    )[
        [
            "x (m)",
            "M (kN·m)",
            "V (kN)",
            "σ (MPa)",
            "δ (mm)",
            "FS",
        ]
    ]

    st.dataframe(
        tabela_analitica,
        width="stretch",
        hide_index=True,
        column_config={
            "x (m)": st.column_config.NumberColumn(format="%.3f"),
            "M (kN·m)": st.column_config.NumberColumn(format="%.3f"),
            "V (kN)": st.column_config.NumberColumn(format="%.3f"),
            "σ (MPa)": st.column_config.NumberColumn(format="%.3f"),
            "δ (mm)": st.column_config.NumberColumn(format="%.4f"),
            "FS": st.column_config.NumberColumn(format="%.3f"),
        },
    )


faixa_secao("3", "Validação numérica e convergência de malha")

dados_malha = pd.DataFrame(resultados).copy()
colunas_numericas = [
    "tamanho_malha_mm",
    "tensao_von_mises_max_mpa",
    "deslocamento_total_max_mm",
    "deslocamento_y_min_mm",
    "deslocamento_y_max_mm",
    "fator_seguranca_min",
]

for coluna in colunas_numericas:
    dados_malha[coluna] = pd.to_numeric(
        dados_malha[coluna],
        errors="coerce",
    )

dados_malha = dados_malha.sort_values(
    "tamanho_malha_mm",
    ascending=False,
)

eixo_malha = alt.X(
    "tamanho_malha_mm:Q",
    title="Tamanho da malha (mm)",
    scale=alt.Scale(reverse=True, zero=False),
    axis=alt.Axis(values=[100, 75, 50, 25, 10], format=".0f"),
)

grafico_convergencia_tensao = (
    alt.Chart(dados_malha)
    .mark_line(point=True, color=COR_AZUL, strokeWidth=2)
    .encode(
        x=eixo_malha,
        y=alt.Y(
            "tensao_von_mises_max_mpa:Q",
            title="Tensão máxima (MPa)",
            scale=alt.Scale(zero=False),
        ),
        tooltip=[
            alt.Tooltip(
                "tamanho_malha_mm:Q",
                title="Malha (mm)",
                format=".0f",
            ),
            alt.Tooltip(
                "tensao_von_mises_max_mpa:Q",
                title="Tensão (MPa)",
                format=".6f",
            ),
        ],
    )
    .properties(
        title="Convergência da tensão de von Mises",
        height=265,
    )
)

grafico_convergencia_deslocamento = (
    alt.Chart(dados_malha)
    .mark_line(point=True, color=COR_LARANJA, strokeWidth=2)
    .encode(
        x=eixo_malha,
        y=alt.Y(
            "deslocamento_total_max_mm:Q",
            title="Deslocamento máximo (mm)",
            scale=alt.Scale(zero=False),
        ),
        tooltip=[
            alt.Tooltip(
                "tamanho_malha_mm:Q",
                title="Malha (mm)",
                format=".0f",
            ),
            alt.Tooltip(
                "deslocamento_total_max_mm:Q",
                title="Deslocamento (mm)",
                format=".6f",
            ),
        ],
    )
    .properties(
        title="Convergência do deslocamento total",
        height=265,
    )
)

coluna_convergencia_1, coluna_convergencia_2 = st.columns(2)

with coluna_convergencia_1:
    st.altair_chart(
        estilizar_grafico(grafico_convergencia_tensao),
        width="stretch",
    )

with coluna_convergencia_2:
    st.altair_chart(
        estilizar_grafico(grafico_convergencia_deslocamento),
        width="stretch",
    )

dados_refinados = dados_malha.sort_values("tamanho_malha_mm")

if len(dados_refinados) >= 2:
    malha_final = dados_refinados.iloc[0]
    malha_anterior = dados_refinados.iloc[1]

    variacao_tensao = abs(
        (
            malha_final["tensao_von_mises_max_mpa"]
            - malha_anterior["tensao_von_mises_max_mpa"]
        )
        / malha_final["tensao_von_mises_max_mpa"]
    ) * 100

    variacao_deslocamento = abs(
        (
            malha_final["deslocamento_total_max_mm"]
            - malha_anterior["deslocamento_total_max_mm"]
        )
        / malha_final["deslocamento_total_max_mm"]
    ) * 100

    st.markdown(
        f"""
        <div class="info-card good">
            <div class="info-title safe">✓ Estabilidade dos indicadores no refinamento</div>
            <div class="info-line">
                Entre as malhas de
                {numero_br(malha_anterior['tamanho_malha_mm'], 0)} mm e
                {numero_br(malha_final['tamanho_malha_mm'], 0)} mm,
                a tensão variou <strong>{numero_br(variacao_tensao, 5)}%</strong>
                e o deslocamento variou
                <strong>{numero_br(variacao_deslocamento, 5)}%</strong>.
                Esses valores indicam estabilidade das grandezas acompanhadas.
                A malha de 10 mm permanece como referência entre as configurações testadas.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

tabela_real = dados_malha.rename(
    columns={
        "simulacao_id": "ID",
        "simulacao": "Simulação",
        "tamanho_malha_mm": "Malha (mm)",
        "tensao_von_mises_max_mpa": "Tensão máxima (MPa)",
        "deslocamento_total_max_mm": "Deslocamento total (mm)",
        "deslocamento_y_min_mm": "Deslocamento Y mín. (mm)",
        "deslocamento_y_max_mm": "Deslocamento Y máx. (mm)",
        "fator_seguranca_min": "FS mínimo",
    }
)

tabela_real.insert(
    0,
    "Modelo",
    tabela_real["Malha (mm)"].apply(
        lambda valor: "★ Definitivo" if float(valor) == 10 else "Refinamento"
    ),
)

st.dataframe(
    tabela_real[
        [
            "Modelo",
            "Malha (mm)",
            "Tensão máxima (MPa)",
            "Deslocamento total (mm)",
            "Deslocamento Y mín. (mm)",
            "Deslocamento Y máx. (mm)",
            "FS mínimo",
            "Simulação",
        ]
    ],
    width="stretch",
    hide_index=True,
    column_config={
        "Malha (mm)": st.column_config.NumberColumn(format="%.0f"),
        "Tensão máxima (MPa)": st.column_config.NumberColumn(format="%.6f"),
        "Deslocamento total (mm)": st.column_config.NumberColumn(
            format="%.6f"
        ),
        "Deslocamento Y mín. (mm)": st.column_config.NumberColumn(
            format="%.6f"
        ),
        "Deslocamento Y máx. (mm)": st.column_config.NumberColumn(
            format="%.6f"
        ),
        "FS mínimo": st.column_config.NumberColumn(format="%.6f"),
    },
)


faixa_secao("4", "Contexto metodológico — tradicional × integrado")

metodo_1, metodo_2, metodo_3 = st.columns(3)

with metodo_1:
    st.markdown(
        """
        <div class="method-card">
            <div class="method-label">Pós-processamento</div>
            <div class="method-line">Tradicional: <span class="warn">manual</span></div>
            <div class="method-line">Integrado: <span class="safe">automatizado</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with metodo_2:
    st.markdown(
        """
        <div class="method-card">
            <div class="method-label">Atualização dos dados</div>
            <div class="method-line">Tradicional: <span class="warn">exportação isolada</span></div>
            <div class="method-line">Integrado: <span class="safe">pipeline reproduzível</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with metodo_3:
    st.markdown(
        """
        <div class="method-card">
            <div class="method-label">Acessibilidade</div>
            <div class="method-line">Tradicional: <span class="warn">ambiente técnico</span></div>
            <div class="method-line">Integrado: <span class="safe">navegador local</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="engineering-footer">
        <strong>Interpretação:</strong> os blocos “Dados reais do estudo” e
        “Convergência de malha” utilizam uma cópia pública dos valores extraídos
        dos arquivos RST por PyDPF. No sistema local, os mesmos resultados foram
        gravados no MySQL e consultados pela FastAPI.
        Os controles laterais recalculam apenas o modelo analítico de
        Euler–Bernoulli. A comparação metodológica é qualitativa e não constitui
        ensaio experimental de tempo ou produtividade.
    </div>
    """,
    unsafe_allow_html=True,
)
