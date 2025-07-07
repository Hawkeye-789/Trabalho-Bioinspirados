import random
import numpy as np
import sys
import math
import copy

# === Makespan ===
def calcular_makespan(seq, tempos):
    n, m = len(seq), len(tempos[0])
    completions = np.zeros((n, m))
    for i, job in enumerate(seq):
        for j in range(m):
            if i == 0 and j == 0:
                completions[i][j] = tempos[job][j]
            elif i == 0:
                completions[i][j] = completions[i][j-1] + tempos[job][j]
            elif j == 0:
                completions[i][j] = completions[i-1][j] + tempos[job][j]
            else:
                completions[i][j] = max(completions[i-1][j], completions[i][j-1]) + tempos[job][j]
    return completions[-1][-1]

# === NEH Heurística ===
def neh(tempos):
    num_jobs = len(tempos)
    soma = [(i, sum(tempos[i])) for i in range(num_jobs)]
    ordenados = [i for i, _ in sorted(soma, key=lambda x: -x[1])]
    sequencia = [ordenados[0]]
    for i in ordenados[1:]:
        melhor_seq = None
        melhor_mk = float('inf')
        for pos in range(len(sequencia)+1):
            temp_seq = sequencia[:pos] + [i] + sequencia[pos:]
            mk = calcular_makespan(temp_seq, tempos)
            if mk < melhor_mk:
                melhor_mk = mk
                melhor_seq = temp_seq
        sequencia = melhor_seq
    return sequencia

# === Vizinhança (swap ou insert) ===
def vizinho(seq):
    nova = seq[:]
    if random.random() < 0.5:
        i, j = random.sample(range(len(seq)), 2)
        nova[i], nova[j] = nova[j], nova[i]
    else:
        i, j = random.sample(range(len(seq)), 2)
        job = nova.pop(i)
        nova.insert(j, job)
    return nova

# === Crossover OX ===
def order_crossover(p1, p2):
    n = len(p1)
    a, b = sorted(random.sample(range(n), 2))
    filho = [None] * n
    filho[a:b] = p1[a:b]
    idx = b
    for i in range(n):
        gene = p2[(b+i)%n]
        if gene not in filho:
            if idx >= n: idx = 0
            filho[idx] = gene
            idx += 1
    return filho

# === Busca local (iterativa) ===
def busca_local(seq, tempos, tentativas=5):
    melhor = seq[:]
    melhor_mk = calcular_makespan(melhor, tempos)
    for _ in range(tentativas):
        viz = vizinho(melhor)
        mk = calcular_makespan(viz, tempos)
        if mk < melhor_mk:
            melhor, melhor_mk = viz, mk
    return melhor, melhor_mk

# === Algoritmo Principal ===
def bee_colony_turbinado(tempos, n_bees=20, max_iter=2500, limit=100, arquivo_tam=5):
    n_jobs = len(tempos)
    jobs = list(range(n_jobs))

    # Inicialização
    food_sources = [neh(tempos)] + [random.sample(jobs, n_jobs) for _ in range(n_bees - 1)]
    makespans = [calcular_makespan(fs, tempos) for fs in food_sources]
    trial = [0] * n_bees
    arquivo = []

    melhor_solucao = food_sources[np.argmin(makespans)]
    melhor_makespan = min(makespans)

    for it in range(max_iter):
        # Employed bees
        for i in range(n_bees):
            viz_seq = vizinho(food_sources[i])
            mk = calcular_makespan(viz_seq, tempos)
            if mk < makespans[i]:
                food_sources[i] = viz_seq
                makespans[i] = mk
                trial[i] = 0
            else:
                trial[i] += 1

        # Onlooker bees (roleta)
        fit = [np.exp(-mk / (min(makespans)+1e-9)) for mk in makespans]
        soma = sum(fit)
        probs = [f / soma for f in fit]

        for _ in range(n_bees):
            r = random.random()
            soma = 0
            for i, p in enumerate(probs):
                soma += p
                if soma >= r:
                    viz_seq = vizinho(food_sources[i])
                    mk = calcular_makespan(viz_seq, tempos)
                    if mk < makespans[i]:
                        food_sources[i] = viz_seq
                        makespans[i] = mk
                        trial[i] = 0
                    else:
                        trial[i] += 1
                    break

        # Scout bees
        for i in range(n_bees):
            if trial[i] >= limit:
                if arquivo:
                    nova = random.choice(arquivo)
                else:
                    nova = random.sample(jobs, n_jobs)
                food_sources[i] = nova
                makespans[i] = calcular_makespan(nova, tempos)
                trial[i] = 0

        # Atualiza arquivo global
        for i in range(n_bees):
            if len(arquivo) < arquivo_tam or calcular_makespan(food_sources[i], tempos) < calcular_makespan(arquivo[-1], tempos):
                arquivo.append(food_sources[i][:])
                arquivo = sorted(arquivo, key=lambda s: calcular_makespan(s, tempos))[:arquivo_tam]

        # Busca local nos 3 melhores
        melhores_idx = np.argsort(makespans)[:3]
        for idx in melhores_idx:
            nova, mk = busca_local(food_sources[idx], tempos)
            if mk < makespans[idx]:
                food_sources[idx] = nova
                makespans[idx] = mk

        # Crossover a cada 50 iterações
        if it > 0 and it % 50 == 0:
            top_bees = [food_sources[i] for i in np.argsort(makespans)[:4]]
            filhos = []
            for i in range(len(top_bees)):
                for j in range(i+1, len(top_bees)):
                    f = order_crossover(top_bees[i], top_bees[j])
                    filhos.append(f)
            for f in filhos[:min(len(filhos), 3)]:
                mk = calcular_makespan(f, tempos)
                worst_idx = np.argmax(makespans)
                food_sources[worst_idx] = f
                makespans[worst_idx] = mk

        # Atualização do melhor global
        idx = np.argmin(makespans)
        if makespans[idx] < melhor_makespan:
            melhor_makespan = makespans[idx]
            melhor_solucao = food_sources[idx][:]

    return melhor_solucao, melhor_makespan

# === Leitura de arquivo via linha de comando ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python script.py fssp_instance_XX.txt")
        sys.exit("Finalizando o programa")

    nome_arquivo = sys.argv[1]
    with open(nome_arquivo, 'r') as f:
        linhas = f.readlines()

    num_jobs, num_maquinas = map(int, linhas[0].strip().split())
    tempo_processamento = [list(map(int, linha.strip().split())) for linha in linhas[1:]]

    melhor_seq, melhor_mk = bee_colony_turbinado(tempo_processamento)
    print("Melhor sequência encontrada:", melhor_seq)
    print("Makespan:", melhor_mk)
