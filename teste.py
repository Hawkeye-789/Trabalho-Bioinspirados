import random
import numpy as np
import sys
import matplotlib.pyplot as plt

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

def operador_swap(sequencia):
    nova = sequencia.copy()
    i, j = random.sample(range(len(nova)), 2)
    nova[i], nova[j] = nova[j], nova[i]
    return nova

def operador_insert(sequencia):
    nova = sequencia.copy()
    i, j = random.sample(range(len(nova)), 2)
    job = nova.pop(i)
    nova.insert(j, job)
    return nova

def gerar_vizinho(sequencia):
    return operador_swap(sequencia) if random.random() < 0.5 else operador_insert(sequencia)

def busca_local(sequencia, tempos, max_iter=20):
    atual = sequencia.copy()
    melhor = atual
    melhor_mk = calcular_makespan(melhor, tempos)
    for _ in range(max_iter):
        viz = gerar_vizinho(melhor)
        mk = calcular_makespan(viz, tempos)
        if mk < melhor_mk:
            melhor = viz
            melhor_mk = mk
    return melhor, melhor_mk

def scout_from_best(best_seq):
    nova = best_seq.copy()
    n = len(nova)
    i, j = sorted(random.sample(range(n), 2))
    nova[i:j] = reversed(nova[i:j])  # inversão de bloco
    return list(nova)

def roleta(probabilidades):
    r = random.random()
    soma = 0
    for i, p in enumerate(probabilidades):
        soma += p
        if r <= soma:
            return i
    return len(probabilidades) - 1

def bee_colony_fssp(tempos, n_bees=20, max_iter=5000, limit=100):
    n_jobs = len(tempos)
    jobs = list(range(n_jobs))

    food_sources = [random.sample(jobs, n_jobs) for _ in range(n_bees)]
    makespans = [calcular_makespan(fs, tempos) for fs in food_sources]
    trial = [0] * n_bees

    melhor_solucao = food_sources[np.argmin(makespans)]
    melhor_makespan = min(makespans)
    convergencia = [melhor_makespan]

    for it in range(max_iter):
        # Fase de employed bees
        for i in range(n_bees):
            vizinho_seq = gerar_vizinho(food_sources[i])
            vizinho_mk = calcular_makespan(vizinho_seq, tempos)
            if vizinho_mk < makespans[i]:
                food_sources[i] = vizinho_seq
                makespans[i] = vizinho_mk
                trial[i] = 0
            else:
                trial[i] += 1

        # Fase de onlooker bees
        best_mk = min(makespans)
        fit = [np.exp(-mk / (best_mk + 1e-9)) for mk in makespans]
        soma_fit = sum(fit)
        probs = [f / soma_fit for f in fit]

        for _ in range(n_bees):
            i = roleta(probs)
            vizinho_seq = gerar_vizinho(food_sources[i])
            vizinho_mk = calcular_makespan(vizinho_seq, tempos)
            if vizinho_mk < makespans[i]:
                food_sources[i] = vizinho_seq
                makespans[i] = vizinho_mk
                trial[i] = 0
            else:
                trial[i] += 1

        # Fase de scout bees
        for i in range(n_bees):
            if trial[i] >= limit:
                nova_seq = scout_from_best(melhor_solucao)
                nova_mk = calcular_makespan(nova_seq, tempos)
                food_sources[i] = nova_seq
                makespans[i] = nova_mk
                trial[i] = 0

        # Busca local nas duas melhores soluções
        melhores_indices = np.argsort(makespans)[:2]
        for i in melhores_indices:
            nova_seq, nova_mk = busca_local(food_sources[i], tempos)
            if nova_mk < makespans[i]:
                food_sources[i] = nova_seq
                makespans[i] = nova_mk

        # Atualizar melhor solução global
        atual_melhor_idx = np.argmin(makespans)
        atual_melhor_mk = makespans[atual_melhor_idx]
        if atual_melhor_mk < melhor_makespan:
            melhor_makespan = atual_melhor_mk
            melhor_solucao = food_sources[atual_melhor_idx]

        convergencia.append(melhor_makespan)

    return melhor_solucao, melhor_makespan, convergencia

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python script.py fssp_instance.txt")
        sys.exit(1)

    nome_arquivo = sys.argv[1]
    with open(nome_arquivo, 'r') as f:
        linhas = f.readlines()

    num_jobs, num_maquinas = map(int, linhas[0].strip().split())
    tempo_processamento = [list(map(int, linha.strip().split())) for linha in linhas[1:]]

    melhor_seq, melhor_mk, convergencia = bee_colony_fssp(tempo_processamento)

    print("Melhor sequência:", melhor_seq)
    print("Makespan:", melhor_mk)

    plt.plot(convergencia)
    plt.title("Convergência do Bee Colony")
    plt.xlabel("Iteração")
    plt.ylabel("Melhor Makespan")
    plt.grid(True)
    plt.show()
