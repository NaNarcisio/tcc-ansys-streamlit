# Painel Estrutural — Viga em Aço ASTM A36

Versão pública de demonstração do dashboard do TCC de Narcisio Gregory Santos Mazzarella.

## Conteúdo

- `streamlit_app.py`: aplicação Streamlit;
- `resultados_ansys.csv`: cópia dos cinco resultados reais extraídos dos arquivos RST;
- `requirements.txt`: dependências usadas pela hospedagem;
- `.streamlit/config.toml`: tema e configuração da aplicação.

Esta versão pública lê um snapshot CSV para funcionar sem o computador do autor. O fluxo local documentado no TCC utiliza ANSYS, Python/PyDPF, MySQL, FastAPI e Streamlit. Nenhuma senha, credencial, arquivo RST ou dado de treino integra este pacote.

## Publicar no Streamlit Community Cloud

1. Crie um repositório no GitHub, por exemplo `dashboard-tcc-ansys`.
2. Envie **todo o conteúdo desta pasta**, incluindo a pasta `.streamlit`.
3. Entre em <https://share.streamlit.io> com a sua conta GitHub.
4. Selecione **Create app** e informe o repositório criado.
5. Use `streamlit_app.py` como arquivo principal.
6. Escolha um endereço, por exemplo `tcc-ansys-narcisio.streamlit.app`, se estiver disponível.
7. Clique em **Deploy** e, após abrir o painel, defina-o como público nas configurações de compartilhamento.

O link gerado poderá ser enviado à professora e continuará funcionando com o computador do autor desligado.

## Executar localmente

```powershell
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```
