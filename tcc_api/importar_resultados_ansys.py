import csv
import os
from decimal import Decimal
from pathlib import Path

import mysql.connector


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_CSV = RAIZ_PROJETO / "resumo_malhas_ansys.csv"

ORIGEM_DADOS = "ansys_rst"

NOME_MATERIAL = "ASTM A36"
NOME_VIGA = "Viga retangular 3000 x 50 x 150 mm"

MALHAS_ESPERADAS = {
    Decimal("10"),
    Decimal("25"),
    Decimal("50"),
    Decimal("75"),
    Decimal("100"),
}


def converter_decimal(valor):
    return Decimal(
        str(valor).strip().replace(",", ".")
    )


def formatar_malha(valor):
    if valor == valor.to_integral_value():
        return str(int(valor))

    return format(valor.normalize(), "f")


def ler_resultados_csv():
    if not CAMINHO_CSV.exists():
        raise FileNotFoundError(
            f"Arquivo CSV não encontrado: {CAMINHO_CSV}"
        )

    resultados = []

    with CAMINHO_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:
        leitor = csv.DictReader(
            arquivo,
            delimiter=";"
        )

        for linha in leitor:
            resultados.append(
                {
                    "tamanho_malha_mm": converter_decimal(
                        linha["tamanho_malha_mm"]
                    ),
                    "tensao_von_mises_max_mpa": converter_decimal(
                        linha["tensao_von_mises_max_mpa"]
                    ),
                    "deslocamento_y_min_mm": converter_decimal(
                        linha["deslocamento_y_min_mm"]
                    ),
                    "deslocamento_y_max_mm": converter_decimal(
                        linha["deslocamento_y_max_mm"]
                    ),
                    "deslocamento_total_max_mm": converter_decimal(
                        linha["deslocamento_total_max_mm"]
                    ),
                    "fator_seguranca_min": converter_decimal(
                        linha["fator_seguranca_min"]
                    ),
                }
            )

    malhas_encontradas = {
        item["tamanho_malha_mm"]
        for item in resultados
    }

    if malhas_encontradas != MALHAS_ESPERADAS:
        raise ValueError(
            "As malhas encontradas no CSV não correspondem a "
            "10, 25, 50, 75 e 100 mm.\n"
            f"Encontradas: {sorted(malhas_encontradas)}"
        )

    return sorted(
        resultados,
        key=lambda item: item["tamanho_malha_mm"],
        reverse=True
    )


def localizar_viga_real(cursor):
    cursor.execute(
        """
        SELECT
            v.id
        FROM vigas v
        INNER JOIN materiais m
            ON m.id = v.material_id
        WHERE v.nome = %s
          AND m.nome = %s
          AND v.comprimento_mm = 3000.00
          AND v.largura_mm = 50.00
          AND v.altura_mm = 150.00
        ORDER BY v.id
        LIMIT 1
        """,
        (
            NOME_VIGA,
            NOME_MATERIAL,
        )
    )

    registro = cursor.fetchone()

    if registro is None:
        raise RuntimeError(
            "A viga real não foi encontrada no banco. "
            "Confira o cadastro de material e viga."
        )

    return registro["id"]


def obter_ou_criar_simulacao(
    cursor,
    viga_id,
    tamanho_malha
):
    texto_malha = formatar_malha(tamanho_malha)
    nome_simulacao = (
        f"Análise ANSYS - malha {texto_malha} mm"
    )

    cursor.execute(
        """
        SELECT id
        FROM simulacoes
        WHERE viga_id = %s
          AND tamanho_malha_mm = %s
          AND origem_dados = %s
        ORDER BY id
        LIMIT 1
        """,
        (
            viga_id,
            tamanho_malha,
            ORIGEM_DADOS,
        )
    )

    simulacao = cursor.fetchone()

    if simulacao is not None:
        simulacao_id = simulacao["id"]

        cursor.execute(
            """
            UPDATE simulacoes
            SET nome = %s,
                descricao_carregamento = %s,
                condicoes_contorno = %s
            WHERE id = %s
            """,
            (
                nome_simulacao,
                "Modelo numérico conforme arquivo RST do ANSYS.",
                "Condições conforme o modelo original do ANSYS.",
                simulacao_id,
            )
        )

        return simulacao_id, "atualizada"

    cursor.execute(
        """
        INSERT INTO simulacoes (
            viga_id,
            nome,
            tamanho_malha_mm,
            descricao_carregamento,
            condicoes_contorno,
            origem_dados
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            viga_id,
            nome_simulacao,
            tamanho_malha,
            "Modelo numérico conforme arquivo RST do ANSYS.",
            "Condições conforme o modelo original do ANSYS.",
            ORIGEM_DADOS,
        )
    )

    return cursor.lastrowid, "criada"


def gravar_resultado(
    cursor,
    simulacao_id,
    resultado
):
    cursor.execute(
        """
        SELECT id
        FROM resultados
        WHERE simulacao_id = %s
        """,
        (simulacao_id,)
    )

    registro = cursor.fetchone()

    valores = (
        resultado["tensao_von_mises_max_mpa"],
        resultado["deslocamento_total_max_mm"],
        resultado["deslocamento_y_min_mm"],
        resultado["deslocamento_y_max_mm"],
        resultado["fator_seguranca_min"],
    )

    if registro is not None:
        cursor.execute(
            """
            UPDATE resultados
            SET tensao_von_mises_max_mpa = %s,
                deslocamento_total_max_mm = %s,
                deslocamento_y_min_mm = %s,
                deslocamento_y_max_mm = %s,
                fator_seguranca_min = %s
            WHERE simulacao_id = %s
            """,
            valores + (simulacao_id,)
        )

        return "atualizado"

    cursor.execute(
        """
        INSERT INTO resultados (
            simulacao_id,
            tensao_von_mises_max_mpa,
            deslocamento_total_max_mm,
            deslocamento_y_min_mm,
            deslocamento_y_max_mm,
            fator_seguranca_min
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (simulacao_id,) + valores
    )

    return "inserido"


def main():
    senha = os.getenv("TCC_DB_PASSWORD")

    if not senha:
        raise RuntimeError(
            "A variável TCC_DB_PASSWORD não está definida."
        )

    resultados_csv = ler_resultados_csv()

    conexao = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="tcc_app",
        password=senha,
        database="tcc_viga",
        connection_timeout=10
    )

    cursor = conexao.cursor(dictionary=True)

    try:
        conexao.start_transaction()

        viga_id = localizar_viga_real(cursor)

        print(f"\nViga real localizada. ID: {viga_id}\n")

        for resultado in resultados_csv:
            malha = resultado["tamanho_malha_mm"]

            simulacao_id, acao_simulacao = (
                obter_ou_criar_simulacao(
                    cursor,
                    viga_id,
                    malha
                )
            )

            acao_resultado = gravar_resultado(
                cursor,
                simulacao_id,
                resultado
            )

            print(
                f"Malha {formatar_malha(malha)} mm: "
                f"simulação {acao_simulacao}; "
                f"resultado {acao_resultado}."
            )

        conexao.commit()

        cursor.execute(
            """
            SELECT
                s.id AS simulacao_id,
                s.tamanho_malha_mm,
                r.tensao_von_mises_max_mpa,
                r.deslocamento_total_max_mm,
                r.deslocamento_y_min_mm,
                r.deslocamento_y_max_mm,
                r.fator_seguranca_min
            FROM simulacoes s
            INNER JOIN resultados r
                ON r.simulacao_id = s.id
            WHERE s.origem_dados = %s
            ORDER BY s.tamanho_malha_mm DESC
            """,
            (ORIGEM_DADOS,)
        )

        registros = cursor.fetchall()

        print("\n==========================================")
        print("RESULTADOS REAIS GRAVADOS NO MYSQL")
        print("==========================================")

        for registro in registros:
            print(
                f"Malha "
                f"{float(registro['tamanho_malha_mm']):.0f} mm | "
                f"Tensão "
                f"{float(registro['tensao_von_mises_max_mpa']):.6f} MPa | "
                f"Deslocamento "
                f"{float(registro['deslocamento_total_max_mm']):.6f} mm | "
                f"FS "
                f"{float(registro['fator_seguranca_min']):.6f}"
            )

        print("------------------------------------------")
        print(f"Quantidade de resultados: {len(registros)}")
        print("Importação concluída com sucesso.")
        print("==========================================")

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    main()