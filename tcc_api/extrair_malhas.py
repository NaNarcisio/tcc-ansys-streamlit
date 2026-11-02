import csv
import re
from pathlib import Path

import numpy as np
from ansys.dpf import post


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_MALHAS = RAIZ_PROJETO / "malhas"
ARQUIVO_CSV = RAIZ_PROJETO / "resumo_malhas_ansys.csv"

LIMITE_ESCOAMENTO_MPA = 250.0
PADRAO_PASTA = re.compile(r"(\d+(?:[.,]\d+)?)mm", re.IGNORECASE)


def obter_tamanho_malha(nome_pasta):
    correspondencia = PADRAO_PASTA.fullmatch(nome_pasta)

    if not correspondencia:
        raise ValueError(
            f"Não foi possível identificar a malha na pasta: {nome_pasta}"
        )

    return float(correspondencia.group(1).replace(",", "."))


def converter_comprimento_para_mm(valor, unidade):
    fatores = {
        "m": 1000.0,
        "cm": 10.0,
        "mm": 1.0,
        "um": 0.001,
        "µm": 0.001,
    }

    unidade_normalizada = str(unidade).strip().lower()

    if unidade_normalizada not in fatores:
        raise ValueError(
            f"Unidade de comprimento não reconhecida: {unidade}"
        )

    return valor * fatores[unidade_normalizada]


def converter_tensao_para_mpa(valor, unidade):
    fatores = {
        "pa": 1e-6,
        "kpa": 1e-3,
        "mpa": 1.0,
        "gpa": 1000.0,
    }

    unidade_normalizada = str(unidade).strip().lower()

    if unidade_normalizada not in fatores:
        raise ValueError(
            f"Unidade de tensão não reconhecida: {unidade}"
        )

    return valor * fatores[unidade_normalizada]


def extrair_resultados(caminho_rst, tamanho_malha_mm):
    simulacao = post.load_simulation(str(caminho_rst))

    # Deslocamento na direção Y
    resultado_uy = simulacao.displacement(components=["Y"])
    campo_uy = resultado_uy._fc[0]
    valores_uy = np.asarray(
        campo_uy.data,
        dtype=float
    ).reshape(-1)

    # Deslocamento vetorial total
    resultado_u = simulacao.displacement()
    campo_u = resultado_u._fc[0]
    valores_u = np.asarray(campo_u.data, dtype=float)

    if valores_u.ndim != 2:
        raise RuntimeError(
            f"Formato inesperado do deslocamento: {valores_u.shape}"
        )

    deslocamento_total = np.linalg.norm(
        valores_u,
        axis=1
    )

    # Tensão equivalente de von Mises nodal
    resultado_vm = simulacao.stress_eqv_von_mises_nodal()
    campo_vm = resultado_vm._fc[0]
    valores_vm = np.asarray(
        campo_vm.data,
        dtype=float
    ).reshape(-1)

    tensao_max_mpa = converter_tensao_para_mpa(
        float(np.max(valores_vm)),
        campo_vm.unit
    )

    deslocamento_y_min_mm = converter_comprimento_para_mm(
        float(np.min(valores_uy)),
        campo_uy.unit
    )

    deslocamento_y_max_mm = converter_comprimento_para_mm(
        float(np.max(valores_uy)),
        campo_uy.unit
    )

    deslocamento_total_max_mm = converter_comprimento_para_mm(
        float(np.max(deslocamento_total)),
        campo_u.unit
    )

    fator_seguranca = (
        LIMITE_ESCOAMENTO_MPA / tensao_max_mpa
    )

    return {
        "tamanho_malha_mm": tamanho_malha_mm,
        "tensao_von_mises_max_mpa": tensao_max_mpa,
        "deslocamento_y_min_mm": deslocamento_y_min_mm,
        "deslocamento_y_max_mm": deslocamento_y_max_mm,
        "deslocamento_total_max_mm": deslocamento_total_max_mm,
        "fator_seguranca_min": fator_seguranca,
        "arquivo_rst": caminho_rst.relative_to(RAIZ_PROJETO).as_posix(),
    }


def salvar_csv(resultados):
    colunas = [
        "tamanho_malha_mm",
        "tensao_von_mises_max_mpa",
        "deslocamento_y_min_mm",
        "deslocamento_y_max_mm",
        "deslocamento_total_max_mm",
        "fator_seguranca_min",
        "arquivo_rst",
    ]

    with ARQUIVO_CSV.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=colunas,
            delimiter=";"
        )

        escritor.writeheader()
        escritor.writerows(resultados)


def main():
    pastas = [
        pasta
        for pasta in PASTA_MALHAS.iterdir()
        if pasta.is_dir()
        and PADRAO_PASTA.fullmatch(pasta.name)
    ]

    pastas.sort(
        key=lambda pasta: obter_tamanho_malha(pasta.name),
        reverse=True
    )

    resultados = []

    print("\nExtração dos arquivos RST iniciada.")
    print(f"Pasta pesquisada: {PASTA_MALHAS}\n")

    for pasta in pastas:
        tamanho_malha = obter_tamanho_malha(pasta.name)
        caminho_rst = pasta / "file.rst"

        if not caminho_rst.exists():
            print(f"Arquivo não encontrado: {caminho_rst}")
            continue

        print(
            f"Processando malha de {tamanho_malha:g} mm...",
            flush=True
        )

        resultado = extrair_resultados(
            caminho_rst,
            tamanho_malha
        )

        resultados.append(resultado)

        print(
            f"  Tensão máxima: "
            f"{resultado['tensao_von_mises_max_mpa']:.6f} MPa"
        )
        print(
            f"  Deslocamento total: "
            f"{resultado['deslocamento_total_max_mm']:.6f} mm"
        )
        print(
            f"  Fator de segurança: "
            f"{resultado['fator_seguranca_min']:.6f}\n"
        )

    if not resultados:
        raise RuntimeError(
            "Nenhum resultado foi extraído."
        )

    salvar_csv(resultados)

    print("==========================================")
    print(f"Malhas processadas: {len(resultados)}")
    print(f"CSV criado em: {ARQUIVO_CSV}")
    print("==========================================")


if __name__ == "__main__":
    main()