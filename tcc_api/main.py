import os
from decimal import Decimal

import mysql.connector
from fastapi import FastAPI, HTTPException, Query


app = FastAPI(
    title="API do TCC - Análise de Vigas",
    version="2.0.0"
)


def abrir_conexao():
    senha = os.getenv("TCC_DB_PASSWORD")

    if not senha:
        raise RuntimeError(
            "A variável TCC_DB_PASSWORD não está definida."
        )

    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="tcc_app",
        password=senha,
        database="tcc_viga",
        connection_timeout=10
    )


def converter_decimais(registros):
    for registro in registros:
        for campo, valor in registro.items():
            if isinstance(valor, Decimal):
                registro[campo] = float(valor)

    return registros


@app.get("/")
def inicio():
    return {
        "mensagem": "API do TCC funcionando",
        "projeto": "Análise estrutural de vigas",
        "versao": "2.0.0"
    }


@app.get("/resultados")
def listar_resultados(
    origem: str | None = Query(
        default=None,
        max_length=20,
        description="Exemplo: ansys_rst ou treino"
    )
):
    conexao = None
    cursor = None

    consulta = """
        SELECT
            s.id AS simulacao_id,
            s.nome AS simulacao,
            v.nome AS viga,
            m.nome AS material,
            s.tamanho_malha_mm,
            s.origem_dados,
            r.tensao_von_mises_max_mpa,
            r.deslocamento_total_max_mm,
            r.deslocamento_y_min_mm,
            r.deslocamento_y_max_mm,
            r.fator_seguranca_min
        FROM simulacoes s
        INNER JOIN vigas v
            ON v.id = s.viga_id
        INNER JOIN materiais m
            ON m.id = v.material_id
        INNER JOIN resultados r
            ON r.simulacao_id = s.id
    """

    parametros = ()

    if origem:
        consulta += """
            WHERE s.origem_dados = %s
        """
        parametros = (origem,)

    consulta += """
        ORDER BY
            s.origem_dados,
            s.tamanho_malha_mm DESC
    """

    try:
        conexao = abrir_conexao()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(consulta, parametros)
        resultados = cursor.fetchall()

        resultados = converter_decimais(resultados)

        return {
            "quantidade": len(resultados),
            "filtro_origem": origem,
            "resultados": resultados
        }

    except RuntimeError as erro:
        raise HTTPException(
            status_code=500,
            detail=str(erro)
        ) from erro

    except mysql.connector.Error as erro:
        print(f"Erro MySQL: {erro}")

        raise HTTPException(
            status_code=500,
            detail="Não foi possível consultar o banco de dados."
        ) from erro

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()