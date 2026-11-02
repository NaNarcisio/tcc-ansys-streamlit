"""Extrai componentes nodais de tensão para auditoria da comparação estrutural.

Execução na raiz do projeto:
    python -m tcc_api.auditar_tensoes --malha 10

Requer PyDPF e servidor DPF/ANSYS funcional. NÃO corrige os apoios nem gera
um novo modelo numérico; lê somente o arquivo RST existente.
"""

import argparse
import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CAMPOS = ("sigma_xx_mpa", "sigma_yy_mpa", "sigma_zz_mpa",
          "tau_xy_mpa", "tau_yz_mpa", "tau_xz_mpa")


def converter_para_mpa(valores, unidade):
    fatores = {"pa": 1e-6, "kpa": 1e-3, "mpa": 1.0, "gpa": 1e3}
    uni = str(unidade).strip().lower()
    if uni not in fatores:
        raise ValueError(f"Unidade de tensão inesperada: {unidade!r}")
    return np.asarray(valores, dtype=float) * fatores[uni]


def campo_nodal_data(campo, ncolunas):
    if str(campo.location).lower() != "nodal":
        raise RuntimeError(f"Resultado esperado nodal, recebido: {campo.location}")
    valores = np.asarray(campo.data, dtype=float).reshape(-1, ncolunas)
    ids = np.asarray(campo.scoping.ids, dtype=int)
    if valores.shape[0] != len(ids):
        raise RuntimeError("Desalinhamento entre linhas de campo e IDs nodais")
    if len(ids) != len(set(ids)):
        raise RuntimeError("Existem IDs nodais repetidos no resultado")
    return ids, valores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--malha', default='10', choices=['100','75','50','25','10'])
    args=parser.parse_args()
    rst=ROOT/'malhas'/f'{args.malha}mm'/'file.rst'
    if not rst.exists():
        raise SystemExit(f"Arquivo ausente: {rst}")
    from ansys.dpf import post, core as dpf  # importa após verificar o caminho
    sim = post.load_simulation(str(rst))
    s = sim.stress_nodal()._fc[0]
    vm = sim.stress_eqv_von_mises_nodal()._fc[0]
    ids_s, vals_s = campo_nodal_data(s,6)
    ids_v, vals_v = campo_nodal_data(vm,1)
    vals_s = converter_para_mpa(vals_s,s.unit)
    vals_v = converter_para_mpa(vals_v,vm.unit).reshape(-1)
    s_por_id = {int(nid): vals_s[i] for i,nid in enumerate(ids_s)}
    vm_por_id = {int(nid): float(vals_v[i]) for i,nid in enumerate(ids_v)}
    comuns = sorted(set(s_por_id) & set(vm_por_id))
    if not comuns:
        raise RuntimeError('Nenhum nó comum entre tensão e von Mises')

    # Comparar SEMPRE grandezas no mesmo nó. "máximo" isolado de cada campo
    # pode acontecer em nós diferentes e não caracteriza um estado de tensão.
    n_vm = max(comuns, key=lambda n: vm_por_id[n])
    n_zz = max(comuns, key=lambda n: abs(s_por_id[n][2]))
    n_zz_pos = max(comuns, key=lambda n: s_por_id[n][2])
    n_zz_neg = min(comuns, key=lambda n: s_por_id[n][2])
    pontos = [('maximo_von_mises',n_vm),
              ('maximo_abs_sigma_zz',n_zz),
              ('maximo_sigma_zz',n_zz_pos),
              ('minimo_sigma_zz',n_zz_neg)]
    mesh = dpf.Model(str(rst)).metadata.meshed_region
    linhas=[]
    for etiqueta,nid in pontos:
        # As coordenadas ficam na unidade nativa do arquivo RST;
        # confirmar em Mechanical antes de apresentá-las como mm ou m.
        coords = mesh.nodes.node_by_id(int(nid)).coordinates
        linha = {'tipo_ponto':etiqueta,'malha_mm':args.malha,
                 'node_id':int(nid),'x_rst':float(coords[0]),
                 'y_rst':float(coords[1]),'z_rst':float(coords[2]),
                 'von_mises_mpa':vm_por_id[nid]}
        linha.update({nome:float(val) for nome,val in zip(CAMPOS,s_por_id[nid])})
        linhas.append(linha)

    destino=ROOT/'dados'/f'auditoria_tensoes_{args.malha}mm.csv'
    with destino.open('w',encoding='utf-8-sig',newline='') as f:
        gravador=csv.DictWriter(f,fieldnames=list(linhas[0]),delimiter=';')
        gravador.writeheader(); gravador.writerows(linhas)
    print(f"Arquivo produzido: {destino}")
    for linha in linhas:
        print(f"{linha['tipo_ponto']}: nó {linha['node_id']}, "
              f"sigma_zz={linha['sigma_zz_mpa']:.6f} MPa, "
              f"von Mises={linha['von_mises_mpa']:.6f} MPa")
    print('ATENÇÃO: conferir eixo Z, sistema de coordenadas, posição dos apoios')
    print('e unidade das coordenadas antes de citar os valores no TCC.')
    print('A tensão nodal pode resultar de média/extrapolação; não presumir')
    print('que extremos de von Mises e sigma_zz ocorrem na mesma posição.')

if __name__=='__main__':
    main()
