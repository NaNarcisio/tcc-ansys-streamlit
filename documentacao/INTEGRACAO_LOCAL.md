# Execução local e rastreabilidade — TCC ANSYS / Python / MySQL / FastAPI / Streamlit

Este repositório contém **duas modalidades distintas**, que não devem ser confundidas:

- **Demonstração pública:** `streamlit_app.py` + `resultados_ansys.csv`, sem conexão com o MySQL nem ANSYS na nuvem. O arquivo é um snapshot gerado a partir das simulações.
- **Pipeline local executado:** arquivos de resultados ANSYS `.rst` → PyDPF (`tcc_api/extrair_malhas.py`) → CSV → importadores MySQL → FastAPI (`tcc_api/main.py`) → Streamlit (`tcc_api/dashboard_apoios_comparativo.py`).

Os arquivos binários `.rst` e backups do MySQL **não foram publicados neste repositório**. Para repetir a etapa de extração a partir de RST, são necessários os resultados ANSYS originais ou revisados, produzidos no software, e um ambiente PyDPF compatível. O código da extração está público; a disponibilidade do binário é uma dependência distinta.

## Dados e modelo

Viga retangular ASTM A36, comprimento **3,0 m**, seção **50 × 150 mm**, módulo de elasticidade **200 GPa**, coeficiente de Poisson **0,26**, limite de escoamento **250 MPa**. Aplicação de **8 kN/m** de carga distribuída (representada no modelo por **160 kPa** na face de largura 50 mm).

O estudo empregou cinco malhas: 100, 75, 50, 25 e 10 mm. O modelo revisado distingue as restrições nos apoios:

- Apoio em Z = 3 m: UX = UY = UZ = 0; rotações livres.
- Apoio em Z = 0 m: UX = UY = 0; UZ livre; ROTZ = 0; demais rotações livres.
- *Remote Displacement* com comportamento *Deformable*. Foi verificado o equilíbrio das reações Y, de aproximadamente 12 kN em cada apoio, além de momento de reação Z praticamente nulo no segundo apoio (8,3701 × 10⁻⁷ N·m) para a malha de 50 mm.

Este modelo tridimensional é uma aproximação física aos apoios ideais de uma viga de Euler-Bernoulli; reações coerentes, isoladamente, **não comprovam equivalência matemática perfeita**.

## Resultados reais do modelo revisado

| Malha (mm) | Von Mises máxima (MPa) | Deslocamento total máximo (mm) | FS mínimo |
|---:|---:|---:|---:|
|100|48,040557|3,016830|5,203936|
|75|48,025001|3,016833|5,205622|
|50|48,025677|3,016963|5,205549|
|25|48,030825|3,016992|5,204991|
|10|48,032104|3,016995|5,204852|

O CSV exato extraído pelo PyDPF, quando presente, está em `dados/resumo_malhas_apoios_revisados.csv`; os resultados do modelo original permanecem em `resumo_malhas_ansys.csv`. No MySQL, as origens são `ansys_rst` e `ansys_rst_rev`, respectivamente.

### Auditoria tensorial (10 mm, apoios revisados)

No centro do vão (Z = 1,5 m), o nó 26505 apresentou σzz = **+48,032849 MPa** e von Mises = **48,032104 MPa**; o nó 27999 apresentou σzz = **−48,032850 MPa**, σyy = **−0,160345 MPa** e von Mises = **47,952302 MPa**. As demais componentes de tensão, nesses pontos, foram pequenas relativamente ao módulo de σzz. O erro relativo entre o máximo |σzz| = 48,032850 MPa e a tensão de flexão analítica 48,000000 MPa é de aproximadamente **0,0684%**.

A tensão equivalente de von Mises é usada **separadamente** para a avaliação de escoamento e do fator de segurança; não é tratada como idêntica à tensão normal de flexão.

## Como reproduzir localmente (Windows)

1. Clone este repositório. Use Python 3.13 em um ambiente virtual: `py -3.13 -m venv .venv`.
2. Instale as dependências do pipeline: `.\.venv\Scripts\python.exe -m pip install -r requirements_local.txt` (o arquivo `requirements.txt` da raiz é específico da demonstração na nuvem).
3. Se possuir os arquivos RST, coloque-os em `malhas/100mm/file.rst`, `malhas/75mm/file.rst`, `malhas/50mm/file.rst`, `malhas/25mm/file.rst` e `malhas/10mm/file.rst`. Execute `python -m tcc_api.extrair_malhas` com seu Python do ambiente virtual. A saída é `resumo_malhas_ansys.csv`.
4. Para os **apoios revisados**, use `malhas_apoios_revisados/{tamanho}mm/file.rst`. A extração pode ser feita apontando `PASTA_MALHAS` e `ARQUIVO_CSV` no módulo `extrair_malhas` para gravar `dados/resumo_malhas_apoios_revisados.csv`, sem sobrescrever a origem anterior.
5. O arquivo `database/schema.sql` apresenta **esquema de referência reconstruído a partir dos scripts**, não é um dump do MySQL original. Em um banco de teste novo, crie as tabelas e o usuário local `tcc_app` com privilégios restritos. Não execute o script de criação sobre um banco de produção que já contenha dados sem validação prévia.
6. Configure a variável de ambiente **somente na sessão local**: `$env:TCC_DB_PASSWORD = Read-Host "Senha MySQL"`. Nunca a grave no GitHub.
7. Modelo original: `python -m tcc_api.importar_resultados_ansys`. Modelo revisado: `python -m tcc_api.importar_apoios_revisados` faz **somente validação**; após backup do MySQL, use `python -m tcc_api.importar_apoios_revisados --gravar --backup-confirmado`.
8. Inicie a API: `python -m uvicorn tcc_api.main:app --host 127.0.0.1 --port 8001`. Consulte `http://127.0.0.1:8001/resultados?origem=ansys_rst_rev`.
9. Em outro terminal, inicie o painel local: `python -m streamlit run tcc_api/dashboard_apoios_comparativo.py --server.port 8502` e abra `http://localhost:8502`.
10. Para testar as componentes de tensão dos apoios revisados: `python -m tcc_api.auditar_tensoes_revisados --malha 10`. Para conferir a API contra o CSV do modelo original, use `python -m tcc_api.verificar_api_csv` com a API funcionando.

Todas as execuções `python` acima devem usar o interpretador do ambiente virtual criado no passo 1. Dados da extração e do banco são identificados por origem para impedir mistura dos modelos.

## Restrições e segurança

- Nenhuma etapa de simulação é executada pelo dashboard: ele **consulta resultados preexistentes**. Os controles do modelo analítico recalculam somente equações de viga.
- A demonstração pública não expõe MySQL/FastAPI nem realiza nova extração RST.
- Nunca submeter `.env`, credenciais, certificados, `.venv`, dump de banco com dados pessoais ou arquivos temporários do solver.
- Testes automatizados: `python -m unittest discover -s tests -v`.
