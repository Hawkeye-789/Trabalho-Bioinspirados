import itertools
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random
import time
import sys

from ag_clonalg_fssp import (
    tempo_processamento, num_jobs, calcular_makespan,
    algoritmo_genetico, clonalg
)

# Parâmetros
execucoes_por_config = 100

# Espaço de busca dos hiperparâmetros
taxa_mutacao_vals = [0.1, 0.2, 0.4]
tamanho_torneio_vals = [2, 3, 4]
metodo_mutacao_vals = ['swap']  # por simplicidade
clonalg_qtd_clones_vals = [3, 5, 7]
clonalg_taxa_mutacao_vals = [0.2, 0.3, 0.4]

# Resultados
resultados = []

print("Iniciando testes fatoriais com Genético seguido de Clonalg...")

for taxa_mutacao, tamanho_torneio, clonalg_qtd_clones, clonalg_taxa_mutacao in itertools.product(
    taxa_mutacao_vals,
    tamanho_torneio_vals,
    clonalg_qtd_clones_vals,
    clonalg_taxa_mutacao_vals
):
    fitness_execs = []
    historicos_execs = []

    for _ in range(execucoes_por_config):
        # Define os parâmetros dinamicamente
        from ag_clonalg_fssp import (
            taxa_mutacao as tm, tamanho_torneio as tt,
            clonalg_qtd_clones as cq, clonalg_taxa_mutacao as ct
        )
        tm = taxa_mutacao
        tt = tamanho_torneio
        cq = clonalg_qtd_clones
        ct = clonalg_taxa_mutacao

        populacao_ag = algoritmo_genetico()
        melhor, makespan = clonalg(populacao_ag)
        fitness_execs.append(makespan)

    melhor = np.min(fitness_execs)
    media = np.mean(fitness_execs)
    desvio = np.std(fitness_execs)

    resultados.append({
        'taxa_mutacao': taxa_mutacao,
        'tamanho_torneio': tamanho_torneio,
        'clones': clonalg_qtd_clones,
        'mut_clonalg': clonalg_taxa_mutacao,
        'melhor': melhor,
        'media': media,
        'desvio': desvio
    })

# Tabela
top30 = sorted(resultados, key=lambda x: x['melhor'])[:30]
df = pd.DataFrame(top30)

fig, ax = plt.subplots(figsize=(12, len(df)*0.4))
ax.axis('off')
table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.2)
plt.title("Top 30 - Genético seguido de Clonalg", fontweight="bold", pad=20)
plt.savefig("tabela_top30_genetico_clonalg.png", bbox_inches='tight')
plt.close()

print("✅ Testes finalizados.")
print("📊 Resultados salvos em tabela_top30_genetico_clonalg.png")
