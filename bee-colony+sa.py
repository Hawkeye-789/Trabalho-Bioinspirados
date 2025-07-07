import random
import numpy as np
import sys
import math

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

def simulated_annealing(sequencia, tempos, temp_ini=1000, temp_fim=1, alpha=0.95, max_iter=100):
    atual = sequencia.copy()
    melhor = atual
    mk_atual = calcular_makespan(atual, tempos)
    mk_melhor = mk_atual
    T = temp_ini

    for _ in range(max_iter):
        novo = vizinho(atual)
        mk_novo = calcular_makespan(novo, tempos)
        delta = mk_novo - mk_atual

        if delta < 0 or random.random() < math.exp(-delta / T):
            atual = novo
            mk_atual = mk_novo
            if mk_novo < mk_melhor:
                melhor = novo
                mk_melhor = mk_novo

        T *= alpha
        if T < temp_fim:
            break

    return melhor, mk_melhor

def roleta(probabilidades):
    r = random.random()
    soma = 0
    for i, p in enumerate(probabilidades):
        soma += p
        if r <= soma:
            return i
    return len(probabilidades) - 1

def bee_colony_sa(tempos, n_bees=20, max_iter=2500, limit=100, sa_interval=200):
    n_jobs = len(tempos)
    jobs = list(range(n_jobs))

    food_sources = [random.sample(jobs, n_jobs) for _ in range(n_bees)]
    makespans = [calcular_makespan(fs, tempos) for fs in food_sources]
    trial = [0] * n_bees

    melhor_solucao = food_sources[np.argmin(makespans)]
    melhor_makespan = min(makespans)
    historico_melhor = [melhor_makespan]

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

        atual_melhor_idx = np.argmin(makespans)
        atual_melhor_mk = makespans[atual_melhor_idx]
        if atual_melhor_mk < melhor_makespan:
            melhor_makespan = atual_melhor_mk
            melhor_solucao = food_sources[atual_melhor_idx]

        historico_melhor.append(melhor_makespan)

        # Aplica simulated annealing a cada sa_interval iterações
        if it > 0 and it % sa_interval == 0:
            nova_sol, nova_mk = simulated_annealing(melhor_solucao, tempos)
            if nova_mk < melhor_makespan:
                melhor_solucao = nova_sol
                melhor_makespan = nova_mk

    return melhor_solucao, melhor_makespan

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

    melhor_seq, melhor_mk = bee_colony_sa(tempo_processamento)
    print("Melhor sequência encontrada:", melhor_seq)
    print("Makespan:", melhor_mk)
