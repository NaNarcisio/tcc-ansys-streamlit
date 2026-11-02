from pathlib import Path

import numpy as np
from ansys.dpf import post


# ============================================================
# CONFIGURAÇÕES
# ============================================================

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_RST = RAIZ_PROJETO / "file.rst"

LIMITE_ESCOAMENTO_MPA = 250.0


if not CAMINHO_RST.is_file():
    raise FileNotFoundError(
        f"Arquivo RST não encontrado: {CAMINHO_RST}"
    )


# ============================================================
# ABRIR SIMULAÇÃO
# ============================================================

print(f"Abrindo arquivo: {CAMINHO_RST}")

simulacao = post.load_simulation(str(CAMINHO_RST))

print("Arquivo RST carregado com sucesso.")


# ============================================================
# DESLOCAMENTO NA DIREÇÃO Y
# ============================================================

deslocamento_y = simulacao.displacement(
    components=["Y"]
)

campo_uy = deslocamento_y._fc[0]

uy_m = np.asarray(
    campo_uy.data,
    dtype=float
).reshape(-1)

uy_min_m = float(np.min(uy_m))
uy_max_m = float(np.max(uy_m))

uy_min_mm = uy_min_m * 1000
uy_max_mm = uy_max_m * 1000


# ============================================================
# DESLOCAMENTO TOTAL
# ============================================================

deslocamento = simulacao.displacement()
campo_u = deslocamento._fc[0]

u = np.asarray(
    campo_u.data,
    dtype=float
)

if u.ndim == 1:
    u = u.reshape(-1, 3)

u_total_m = np.linalg.norm(
    u,
    axis=1
)

u_total_max_mm = float(
    np.max(u_total_m) * 1000
)


# ============================================================
# TENSÃO DE VON MISES NODAL
# ============================================================

tensao_vm = simulacao.stress_eqv_von_mises_nodal()
campo_vm = tensao_vm._fc[0]

vm_pa = np.asarray(
    campo_vm.data,
    dtype=float
).reshape(-1)

vm_max_pa = float(np.max(vm_pa))
vm_max_mpa = vm_max_pa / 1e6


# ============================================================
# FATOR DE SEGURANÇA
# ============================================================

if vm_max_mpa <= 0:
    raise ValueError(
        "A tensão máxima extraída precisa ser maior que zero."
    )

fs_min = LIMITE_ESCOAMENTO_MPA / vm_max_mpa


# ============================================================
# RESULTADOS
# ============================================================

print("\n==========================================")
print("RESULTADOS REAIS EXTRAÍDOS DO ANSYS")
print("==========================================")

print(
    f"Tensão de von Mises máxima : "
    f"{vm_max_mpa:.6f} MPa"
)

print(
    f"Deslocamento Y mínimo      : "
    f"{uy_min_mm:.6f} mm"
)

print(
    f"Deslocamento Y máximo      : "
    f"{uy_max_mm:.6f} mm"
)

print(
    f"Deslocamento total máximo  : "
    f"{u_total_max_mm:.6f} mm"
)

print(
    f"Fator de segurança mínimo  : "
    f"{fs_min:.6f}"
)

print("------------------------------------------")
print(f"Unidade original da tensão: {campo_vm.unit}")
print(f"Unidade original do deslocamento: {campo_u.unit}")
print("==========================================")