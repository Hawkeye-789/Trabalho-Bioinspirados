
import sys
import time
import random
import numpy as np

# ======== PARÂMETROS GLOBAIS ======== #
tamanho_populacao = 100
num_geracoes = 200
taxa_mutacao = 0.2
metodo_selecao = 'torneio'
tamanho_torneio = 3
metodo_cruzamento = 'cx'
metodo_mutacao = 'swap'
elitismo_k = 2

# FSSP
tempo_processamento = []
num_jobs = 0
num_maquinas = 0

# CLONALG
clonalg_geracoes = 50
clonalg_tamanho_pop = 50
clonalg_taxa_mutacao = 0.3
clonalg_qtd_clones = 5

#====== LEITURA DO ARQUIVO ======#

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

#====== FUNÇÃO OBJETIVO ======#

def calcular_makespan(tempo_processamento, ordem_jobs):
    num_jobs = len(ordem_jobs)
    num_maquinas = len(tempo_processamento[0])
    tempo_fim = [[0] * num_maquinas for _ in range(num_jobs)]

    for i in range(num_jobs):
        job = ordem_jobs[i]
        for m in range(num_maquinas):
            if i == 0 and m == 0:
                tempo_fim[i][m] = tempo_processamento[job][m]
            elif i == 0:
                tempo_fim[i][m] = tempo_fim[i][m - 1] + tempo_processamento[job][m]
            elif m == 0:
                tempo_fim[i][m] = tempo_fim[i - 1][m] + tempo_processamento[job][m]
            else:
                tempo_fim[i][m] = max(tempo_fim[i - 1][m], tempo_fim[i][m - 1]) + tempo_processamento[job][m]

    return tempo_fim[-1][-1]

#====== INICIAR POPULAÇÂO ======#

def criar_populacao():
    return [random.sample(range(num_jobs), num_jobs) for _ in range(tamanho_populacao)]

#====== MUTAÇÃO ======#

def mutacao_swap(individuo, taxa_mutacao):
    novo_individuo = individuo[:]
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(novo_individuo)), 2)
        novo_individuo[i], novo_individuo[j] = novo_individuo[j], novo_individuo[i]
    return novo_individuo

def mutacao_atual(individuo, metodo_mutacao, taxa_mutacao):
    if metodo_mutacao == 'swap':
        return mutacao_swap(individuo, taxa_mutacao)
    else:
        raise ValueError(f"Método de mutação desconhecido: {metodo_mutacao}")

#====== CRUZAMENTO ======#

def crossover_cx(pai1, pai2):
    tamanho = len(pai1)
    filho = [None] * tamanho
    usado = [False] * tamanho
    pos = 0
    while not usado[pos]:
        valor = pai1[pos]
        filho[pos] = valor
        usado[pos] = True
        pos = pai1.index(pai2[pos])
    for i in range(tamanho):
        if filho[i] is None:
            filho[i] = pai2[i]
    return filho

def cruzamento_atual(pai1, pai2, metodo_cruzamento):
    if metodo_cruzamento == 'cx':
        return crossover_cx(pai1, pai2)
    else:
        raise ValueError(f"Método de cruzamento desconhecido: {metodo_cruzamento}")

#====== SELEÇÃO ======#

def selecao_torneio(populacao, fitnesses, tamanho_torneio=3):
    indices = random.sample(range(len(populacao)), tamanho_torneio)
    melhor_indice = max(indices, key=lambda i: fitnesses[i])
    return populacao[melhor_indice]

def selecionar_pais(populacao, fitnesses, metodo='torneio', tamanho_torneio=3):
    pai1 = selecao_torneio(populacao, fitnesses, tamanho_torneio)
    pai2 = selecao_torneio(populacao, fitnesses, tamanho_torneio)
    return pai1, pai2

#====== ELITISMO ======#

def elitismo(populacao, fitnesses, k):
    elite_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)[:k]
    return [populacao[i] for i in elite_indices]

#====== ALGORITMO GENÉTICO ======#

def algoritmo_genetico():
    populacao = criar_populacao()
    melhor_global = float('inf')
    ultima_melhora = 0
    taxa_mutacao_atual = taxa_mutacao

    for geracao in range(num_geracoes):
        makespans = [calcular_makespan(tempo_processamento, ind) for ind in populacao]
        fitnesses = [1 / m for m in makespans]
        melhor = min(makespans)
        if melhor < melhor_global:
            melhor_global = melhor
            ultima_melhora = geracao
        else:
            if geracao - ultima_melhora > 5:
                taxa_mutacao_atual = min(1.0, taxa_mutacao_atual * 1.2)
            else:
                taxa_mutacao_atual = taxa_mutacao

        nova_populacao = elitismo(populacao, fitnesses, elitismo_k)

        while len(nova_populacao) < tamanho_populacao:
            pai1, pai2 = selecionar_pais(populacao, fitnesses, metodo=metodo_selecao, tamanho_torneio=tamanho_torneio)
            filho = cruzamento_atual(pai1, pai2, metodo_cruzamento)
            filho = mutacao_atual(filho, metodo_mutacao, taxa_mutacao_atual)
            nova_populacao.append(filho)

        populacao = nova_populacao

    return populacao

#====== CLONALG ======#

def clonalg(populacao_inicial):
    populacao = populacao_inicial[:clonalg_tamanho_pop]
    for _ in range(clonalg_geracoes):
        populacao.sort(key=lambda ind: calcular_makespan(tempo_processamento, ind))
        clones = []
        for i in range(len(populacao)):
            for _ in range(clonalg_qtd_clones):
                clone = mutacao_atual(populacao[i], metodo_mutacao, clonalg_taxa_mutacao)
                clones.append(clone)
        populacao += clones
        populacao.sort(key=lambda ind: calcular_makespan(tempo_processamento, ind))
        populacao = populacao[:clonalg_tamanho_pop]
    melhor = populacao[0]
    melhor_makespan = calcular_makespan(tempo_processamento, melhor)
    return melhor, melhor_makespan

#====== MAIN ======#

def main():
    inicio = time.perf_counter()
    populacao_ag = algoritmo_genetico()
    melhor, makespan = clonalg(populacao_ag)
    fim = time.perf_counter()
    print("Melhor solução encontrada:", melhor)
    print("Makespan:", makespan)
    print(f"Tempo de execução: {fim - inicio:.6f} segundos")

if __name__ == "__main__":
    main()
