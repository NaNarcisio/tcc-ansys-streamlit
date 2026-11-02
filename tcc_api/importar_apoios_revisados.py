"""Importa os cinco resultados dos apoios revisados SEM substituir o modelo original.

Uso na raiz do projeto:
  python -m tcc_api.importar_apoios_revisados
  python -m tcc_api.importar_apoios_revisados --gravar --backup-confirmado

A origem 'ansys_rst_rev' cabe no VARCHAR(20) existente no MySQL.
"""
from __future__ import annotations

import argparse
import csv
import os
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV_REVISADO = RAIZ / "dados" / "resumo_malhas_apoios_revisados.csv"
ORIGEM = "ansys_rst_rev"
MALHAS_ESPERADAS = {Decimal(n) for n in ("10", "25", "50", "75", "100")}
CAMPOS = (
    "tensao_von_mises_max_mpa",
    "deslocamento_total_max_mm",
    "deslocamento_y_min_mm",
    "deslocamento_y_max_mm",
    "fator_seguranca_min",
)


def decimal_br(valor: str) -> Decimal:
    return Decimal(str(valor).strip().replace(",", "."))


def ler_e_validar_csv() -> list[dict]:
    if not CSV_REVISADO.is_file():
        raise FileNotFoundError(f"CSV revisado não encontrado: {CSV_REVISADO}")

    registros = []
    with CSV_REVISADO.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")
        obrigatorios = {"tamanho_malha_mm", *CAMPOS}
        faltantes = obrigatorios.difference(leitor.fieldnames or [])
        if faltantes:
            raise ValueError(f"Colunas ausentes no CSV: {sorted(faltantes)}")

        for linha in leitor:
            item = {"tamanho_malha_mm": decimal_br(linha["tamanho_malha_mm"])}
            for campo in CAMPOS:
                item[campo] = decimal_br(linha[campo])
                if not item[campo].is_finite():
                    raise ValueError(f"Valor inválido na malha {item['tamanho_malha_mm']}: {campo}")
            if item["tensao_von_mises_max_mpa"] <= 0:
                raise ValueError("A tensão máxima deve ser positiva.")
            if item["deslocamento_total_max_mm"] < 0:
                raise ValueError("O deslocamento total deve ser não negativo.")
            if item["fator_seguranca_min"] <= 0:
                raise ValueError("O fator de segurança deve ser positivo.")
            registros.append(item)

    malhas = [r["tamanho_malha_mm"] for r in registros]
    if len(registros) != 5 or set(malhas) != MALHAS_ESPERADAS:
        raise ValueError(
            f"Esperadas cinco malhas únicas (10,25,50,75,100). Encontradas: {malhas}"
        )

    for r in registros:
        fs_estimado = Decimal("250") / r["tensao_von_mises_max_mpa"]
        if abs(fs_estimado - r["fator_seguranca_min"]) > Decimal("0.0001"):
            raise ValueError(
                f"Fator de segurança incompatível na malha {r['tamanho_malha_mm']} mm."
            )

    return sorted(registros, key=lambda r: r["tamanho_malha_mm"], reverse=True)


def importar(registros: list[dict]) -> None:
    senha = os.environ.get("TCC_DB_PASSWORD")
    if not senha:
        raise RuntimeError("Configure TCC_DB_PASSWORD antes de gravar.")

    import mysql.connector

    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="tcc_app",
        password=senha,
        database="tcc_viga",
        connection_timeout=10,
    )
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cursor.execute(
            """
            SELECT v.id
            FROM vigas v
            JOIN materiais m ON m.id = v.material_id
            WHERE v.nome = %s AND m.nome = %s
              AND v.comprimento_mm = %s
              AND v.largura_mm = %s
              AND v.altura_mm = %s
            ORDER BY v.id LIMIT 1
            """,
            (
                "Viga retangular 3000 x 50 x 150 mm",
                "ASTM A36",
                Decimal("3000"),
                Decimal("50"),
                Decimal("150"),
            ),
        )
        viga = cursor.fetchone()
        if not viga:
            raise RuntimeError("Cadastro da viga ASTM A36 não encontrado no banco.")
        viga_id = viga["id"]

        for r in registros:
            malha = r["tamanho_malha_mm"]
            cursor.execute(
                """
                SELECT id FROM simulacoes
                WHERE viga_id = %s
                  AND tamanho_malha_mm = %s
                  AND origem_dados = %s
                """,
                (viga_id, malha, ORIGEM),
            )
            existente = cursor.fetchone()
            nome = f"ANSYS apoios revisados - malha {int(malha)} mm"
            carregamento = "Pressão de 160 kPa equivalente a 8 kN/m no vão de 3 m."
            contorno = (
                "Z=3 m: UX=UY=UZ=0, rotações livres; "
                "Z=0 m: UX=UY=0, UZ livre, ROTZ=0 e demais rotações livres. "
                "Remote Displacement deformable."
            )
            if existente:
                simulacao_id = existente["id"]
                cursor.execute(
                    """
                    UPDATE simulacoes
                    SET nome = %s,
                        descricao_carregamento = %s,
                        condicoes_contorno = %s
                    WHERE id = %s AND origem_dados = %s
                    """,
                    (nome, carregamento, contorno, simulacao_id, ORIGEM),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO simulacoes
                    (viga_id, nome, tamanho_malha_mm, descricao_carregamento,
                     condicoes_contorno, origem_dados)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (viga_id, nome, malha, carregamento, contorno, ORIGEM),
                )
                simulacao_id = cursor.lastrowid

            valores = tuple(r[c] for c in CAMPOS)
            cursor.execute(
                "SELECT id FROM resultados WHERE simulacao_id = %s",
                (simulacao_id,),
            )
            if cursor.fetchone():
                cursor.execute(
                    """
                    UPDATE resultados
                    SET tensao_von_mises_max_mpa=%s,
                        deslocamento_total_max_mm=%s,
                        deslocamento_y_min_mm=%s,
                        deslocamento_y_max_mm=%s,
                        fator_seguranca_min=%s
                    WHERE simulacao_id=%s
                    """,
                    valores + (simulacao_id,),
                )
                acao = "atualizado"
            else:
                cursor.execute(
                    """
                    INSERT INTO resultados
                    (tensao_von_mises_max_mpa, deslocamento_total_max_mm,
                     deslocamento_y_min_mm, deslocamento_y_max_mm,
                     fator_seguranca_min, simulacao_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    valores + (simulacao_id,),
                )
                acao = "inserido"

            print(f"Malha {int(malha):3d} mm: registro {acao} (ID {simulacao_id})")

        conn.commit()
        print("\nGravação concluída: origem ansys_rst_rev. Dados originais preservados.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gravar", action="store_true",
        help="Executa a importação no MySQL. Sem essa opção somente valida o CSV.",
    )
    parser.add_argument(
        "--backup-confirmado", action="store_true",
        help="Confirma que foi realizado backup do banco antes da escrita.",
    )
    args = parser.parse_args()

    registros = ler_e_validar_csv()
    print(f"CSV validado: {CSV_REVISADO}")
    print(f"Origem a registrar: {ORIGEM}")
    for r in registros:
        print(
            f"{int(r['tamanho_malha_mm']):3d} mm | "
            f"von Mises {r['tensao_von_mises_max_mpa']:.6f} MPa | "
            f"deslocamento {r['deslocamento_total_max_mm']:.6f} mm | "
            f"FS {r['fator_seguranca_min']:.6f}"
        )

    if args.gravar:
        if not args.backup_confirmado:
            parser.error(
                "Antes de gravar, faça backup do banco e informe --backup-confirmado."
            )
        importar(registros)
    else:
        print("\nSomente validação: nenhum registro foi alterado no MySQL.")


if __name__ == "__main__":
    main()
