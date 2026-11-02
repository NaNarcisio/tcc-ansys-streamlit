"""Testes independentes de ANSYS/MySQL para os CSV publicados no GitHub.

Os RST são arquivos binários locais e não fazem parte do repositório público.
"""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MALHAS = {10, 25, 50, 75, 100}


def ler(arquivo: Path):
    with arquivo.open(encoding='utf-8-sig', newline='') as handle:
        linhas = list(csv.DictReader(handle, delimiter=';'))
    mapa = {int(float(r['tamanho_malha_mm'])): r for r in linhas}
    if len(linhas) != len(mapa):
        raise AssertionError('Existem malhas duplicadas no arquivo.')
    return mapa


class TestResultadosPublicados(unittest.TestCase):
    def test_malhas_originais(self):
        dados = ler(ROOT / 'resumo_malhas_ansys.csv')
        self.assertEqual(set(dados), MALHAS)
        m10 = dados[10]
        tensao = float(m10['tensao_von_mises_max_mpa'])
        desloc = float(m10['deslocamento_total_max_mm'])
        fs = float(m10['fator_seguranca_min'])
        self.assertAlmostEqual(tensao, 48.011302, places=5)
        self.assertAlmostEqual(desloc, 3.016995, places=5)
        self.assertAlmostEqual(fs, 250/tensao, places=5)

    def test_malhas_apoios_revisados(self):
        arquivo = ROOT / 'dados' / 'resumo_malhas_apoios_revisados.csv'
        self.assertTrue(arquivo.is_file(), f'CSV revisado não publicado: {arquivo}')
        dados = ler(arquivo)
        self.assertEqual(set(dados), MALHAS)
        m10 = dados[10]
        tensao = float(m10['tensao_von_mises_max_mpa'])
        desloc = float(m10['deslocamento_total_max_mm'])
        fs = float(m10['fator_seguranca_min'])
        self.assertAlmostEqual(tensao, 48.032104, places=5)
        self.assertAlmostEqual(desloc, 3.016995, places=5)
        self.assertAlmostEqual(fs, 250/tensao, places=5)

    def test_auditoria_tensorial_apoios_revisados(self):
        arquivo = ROOT / 'dados' / 'auditoria_tensoes_apoios_revisados_10mm.csv'
        self.assertTrue(arquivo.is_file(), f'Auditoria não publicada: {arquivo}')
        with arquivo.open(encoding='utf-8-sig', newline='') as arq:
            registros = list(csv.DictReader(arq, delimiter=';'))
        por_tipo = {r['tipo_ponto']: r for r in registros}
        positivo = por_tipo['maximo_sigma_zz']
        negativo = por_tipo['minimo_sigma_zz']
        self.assertEqual(int(positivo['node_id']), 26505)
        self.assertEqual(int(negativo['node_id']), 27999)
        self.assertAlmostEqual(float(positivo['sigma_zz_mpa']), 48.032849, places=5)
        self.assertAlmostEqual(float(negativo['sigma_zz_mpa']), -48.032850, places=5)


if __name__ == '__main__':
    unittest.main()
