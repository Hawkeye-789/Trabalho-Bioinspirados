import random
import numpy as np
import sys

def calcular_makespan(sequencia, tempos):
    n_jobs = len(sequencia)
    n_machines = len(tempos[0])
    completions = np.zeros((n_jobs, n_machines))

    for i, job in enumerate(sequencia):
        for m in range(n_machines):
            if i == 0 and m == 0:
                completions[i][m] = tempos[job][m]
            elif i == 0:
                completions[i][m] = completions[i][m - 1] + tempos[job][m]
            elif m == 0:
                completions[i][m] = completions[i - 1][m] + tempos[job][m]
            else:
                completions[i][m] = max(completions[i][m - 1], completions[i - 1][m]) + tempos[job][m]

    return completions[-1][-1]

def vizinho(sequencia):
    nova = sequencia.copy()
    if random.random() < 0.5:
        i, j = random.sample(range(len(nova)), 2)
        nova[i], nova[j] = nova[j], nova[i]
    else:
        i, j = random.sample(range(len(nova)), 2)
        job = nova.pop(i)
        nova.insert(j, job)
    return nova

def order_crossover(p1, p2):
    n = len(p1)
    a, b = sorted(random.sample(range(n), 2))
    filho = [None] * n
    filho[a:b] = p1[a:b]
    idx = b
    for i in range(n):
        gene = p2[(b + i) % n]
        if gene not in filho:
            if idx >= n:
                idx = 0
            filho[idx] = gene
            idx += 1
    return filho

def mutacao(sequencia):
    return vizinho(sequencia)

def aplicar_genetico(solucoes, tempos):
    k = len(solucoes) // 2
    melhores_idx = np.argsort([calcular_makespan(s, tempos) for s in solucoes])[:k]
    melhores = [solucoes[i] for i in melhores_idx]

    filhos = []
    for _ in range(k):
        p1, p2 = random.sample(melhores, 2)
        filho = order_crossover(p1, p2)
        filho = mutacao(filho)
        filhos.append(filho)

    piores_idx = np.argsort([calcular_makespan(s, tempos) for s in solucoes])[-k:]
    for i, idx in enumerate(piores_idx):
        solucoes[idx] = filhos[i]
    return solucoes

def bee_colony_ga(tempos, n_bees=20, max_iter=2500, limit=100, ga_interval=100):
    n_jobs = len(tempos)
    jobs = list(range(n_jobs))

    food_sources = [random.sample(jobs, n_jobs) for _ in range(n_bees)]
    makespans = [calcular_makespan(fs, tempos) for fs in food_sources]
    trial = [0] * n_bees

    melhor_solucao = food_sources[np.argmin(makespans)]
    melhor_makespan = min(makespans)

    for it in range(max_iter):
        for i in range(n_bees):
            vizinho_seq = vizinho(food_sources[i])
            vizinho_mk = calcular_makespan(vizinho_seq, tempos)
            if vizinho_mk < makespans[i]:
                food_sources[i] = vizinho_seq
                makespans[i] = vizinho_mk
                trial[i] = 0
            else:
                trial[i] += 1

        best_mk = min(makespans)
        fit = [np.exp(-mk / (best_mk + 1e-9)) for mk in makespans]
        soma_fit = sum(fit)
        probs = [f / soma_fit for f in fit]

        for _ in range(n_bees):
            i = roleta(probs)
            vizinho_seq = vizinho(food_sources[i])
            vizinho_mk = calcular_makespan(vizinho_seq, tempos)
            if vizinho_mk < makespans[i]:
                food_sources[i] = vizinho_seq
                makespans[i] = vizinho_mk
                trial[i] = 0
            else:
                trial[i] += 1

        for i in range(n_bees):
            if trial[i] >= limit:
                nova_seq = random.sample(jobs, n_jobs)
                food_sources[i] = nova_seq
                makespans[i] = calcular_makespan(nova_seq, tempos)
                trial[i] = 0

        if it > 0 and it % ga_interval == 0:
            food_sources = aplicar_genetico(food_sources, tempos)
            makespans = [calcular_makespan(fs, tempos) for fs in food_sources]

        atual_melhor_idx = np.argmin(makespans)
        atual_melhor_mk = makespans[atual_melhor_idx]
        if atual_melhor_mk < melhor_makespan:
            melhor_makespan = atual_melhor_mk
            melhor_solucao = food_sources[atual_melhor_idx]

    return melhor_solucao, melhor_makespan

def roleta(probabilidades):
    r = random.random()
    soma = 0
    for i, p in enumerate(probabilidades):
        soma += p
        if r <= soma:
            return i
    return len(probabilidades) - 1

# -----------------------
# Leitura do arquivo
# -----------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python script.py fssp_instance_XX.txt")
        sys.exit("Finalizando o programa")

    nome_arquivo = sys.argv[1]

    with open(nome_arquivo, 'r') as f:
        linhas = f.readlines()

    num_jobs, num_maquinas = map(int, linhas[0].strip().split())
    tempo_processamento = []
    for linha in linhas[1:]:
        tempos = list(map(int, linha.strip().split()))
        tempo_processamento.append(tempos)

    melhor_seq, melhor_mk = bee_colony_ga(tempo_processamento)
    print("Melhor sequência encontrada:", melhor_seq)
    print("Makespan:", melhor_mk)
