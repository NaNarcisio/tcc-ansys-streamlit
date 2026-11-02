import json
from urllib.request import urlopen

url = "http://127.0.0.1:8001/resultados"

with urlopen(url, timeout=10) as resposta:
    dados = json.load(resposta)

print(f"Resultados recebidos: {dados['quantidade']}")

for resultado in dados["resultados"]:
    print(f"\nSimulação: {resultado['simulacao']}")
    print(f"Material: {resultado['material']}")
    print(f"Origem: {resultado['origem_dados']}")
    print(f"Tensão: {resultado['tensao_von_mises_max_mpa']} MPa")
    print(f"Deslocamento: {resultado['deslocamento_total_max_mm']} mm")