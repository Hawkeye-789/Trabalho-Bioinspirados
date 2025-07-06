import sys
import time
import random

# ======== PARÂMETROS DO AG ======== #
tamanho_populacao = 100
num_geracoes = 200
taxa_mutacao = 0.2
metodo_selecao = 'torneio'  # 'torneio' ou 'roleta'
tamanho_torneio = 3
metodo_cruzamento = 'cx'  # 'cx' ou 'erx'
metodo_mutacao = 'swap'  # 'swap' ou 'deslocamento'
elitismo_k = 2

# ======== LEITURA DO ARQUIVO ======== #

if len(sys.argv) < 2:
    print("Uso: python ag_fssp.py fssp_instance_XX.txt")
    sys.exit(1)

nome_arquivo = sys.argv[1]

with open(nome_arquivo, 'r') as f:
    linhas = f.readlines()

num_jobs, num_maquinas = map(int, linhas[0].strip().split())
tempo_processamento = [list(map(int, linha.strip().split())) for linha in linhas[1:]]

# ======== FUNÇÃO OBJETIVO ======== #

def calcular_makespan(tempo_processamento, ordem_jobs):
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

# ======== GERAÇÃO INICIAL ======== #

def criar_populacao():
    return [random.sample(range(num_jobs), num_jobs) for _ in range(tamanho_populacao)]

# ======== MUTAÇÃO ======== #

def mutacao_swap(individuo, taxa_mutacao):
    novo_individuo = individuo[:]
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(novo_individuo)), 2)
        novo_individuo[i], novo_individuo[j] = novo_individuo[j], novo_individuo[i]
    return novo_individuo

def mutacao_deslocamento(individuo, taxa_mutacao):
    novo_individuo = individuo[:]
    n = len(novo_individuo)
    if random.random() < taxa_mutacao:
        i, j = sorted(random.sample(range(n), 2))
        bloco = novo_individuo[i:j+1]
        del novo_individuo[i:j+1]
        nova_pos = random.randint(0, len(novo_individuo))
        novo_individuo[nova_pos:nova_pos] = bloco
    return novo_individuo

def mutacao_atual(individuo):
    if metodo_mutacao == 'swap':
        return mutacao_swap(individuo, taxa_mutacao)
    elif metodo_mutacao == 'deslocamento':
        return mutacao_deslocamento(individuo, taxa_mutacao)
    else:
        raise ValueError(f"Método de mutação inválido: {metodo_mutacao}")

# ======== CRUZAMENTO ======== #

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

def crossover_erx(pai1, pai2):
    def vizinhos(lst, i):
        n = len(lst)
        idx = lst.index(i)
        return [lst[(idx - 1) % n], lst[(idx + 1) % n]]

    arestas = {gene: set(vizinhos(pai1, gene)) | set(vizinhos(pai2, gene)) for gene in pai1}
    filho = []
    gene_atual = random.choice(pai1)

    while len(filho) < len(pai1):
        filho.append(gene_atual)
        for viz in arestas.values():
            viz.discard(gene_atual)
        arestas.pop(gene_atual, None)
        if arestas:
            gene_atual = min(arestas, key=lambda k: len(arestas[k]))
    return filho

def cruzamento_atual(pai1, pai2):
    if metodo_cruzamento == 'cx':
        return crossover_cx(pai1, pai2)
    elif metodo_cruzamento == 'erx':
        return crossover_erx(pai1, pai2)
    else:
        raise ValueError(f"Método de cruzamento inválido: {metodo_cruzamento}")

# ======== SELEÇÃO ======== #

def selecao_torneio(populacao, fitnesses):
    indices = random.sample(range(len(populacao)), tamanho_torneio)
    melhor = max(indices, key=lambda i: fitnesses[i])
    return populacao[melhor]

def selecao_roleta(populacao, fitnesses):
    soma = sum(fitnesses)
    probs = [f / soma for f in fitnesses]
    return random.choices(populacao, weights=probs, k=1)[0]

def selecionar_pais(populacao, fitnesses):
    if metodo_selecao == 'torneio':
        return selecao_torneio(populacao, fitnesses), selecao_torneio(populacao, fitnesses)
    elif metodo_selecao == 'roleta':
        return selecao_roleta(populacao, fitnesses), selecao_roleta(populacao, fitnesses)
    else:
        raise ValueError(f"Método de seleção inválido: {metodo_selecao}")

# ======== ELITISMO ======== #

def elitismo(populacao, fitnesses, k):
    elite_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)[:k]
    return [populacao[i] for i in elite_indices]

# ======== ALGORITMO GENÉTICO ======== #

def algoritmo_genetico():
    populacao = criar_populacao()
    melhor_global = float('inf')
    ultima_melhora = 0
    taxa_mutacao_dinamica = taxa_mutacao

    for geracao in range(num_geracoes):
        makespans = [calcular_makespan(tempo_processamento, ind) for ind in populacao]
        fitnesses = [1 / m for m in makespans]
        melhor = min(makespans)

        if melhor < melhor_global:
            melhor_global = melhor
            ultima_melhora = geracao
        elif geracao - ultima_melhora > 5:
            taxa_mutacao_dinamica = min(1.0, taxa_mutacao_dinamica * 1.2)
        else:
            taxa_mutacao_dinamica = taxa_mutacao

        nova_populacao = elitismo(populacao, fitnesses, elitismo_k)

        while len(nova_populacao) < tamanho_populacao:
            pai1, pai2 = selecionar_pais(populacao, fitnesses)
            filho = cruzamento_atual(pai1, pai2)
            filho = mutacao_atual(filho)
            nova_populacao.append(filho)

            if random.random() < 0.1:
                novo = random.sample(range(num_jobs), num_jobs)
                nova_populacao[random.randint(0, len(nova_populacao)-1)] = novo

        populacao = nova_populacao

    fitnesses = [1 / calcular_makespan(tempo_processamento, ind) for ind in populacao]
    melhor_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
    return populacao[melhor_idx], calcular_makespan(tempo_processamento, populacao[melhor_idx])

# ======== MAIN ======== #

def main():
    inicio = time.perf_counter()
    solucao, makespan = algoritmo_genetico()
    fim = time.perf_counter()

    print("\n--- AG ---")
    print("Melhor solução encontrada:", solucao)
    print("Makespan:", makespan)
    print(f"Tempo de execução: {fim - inicio:.6f} segundos")

if __name__ == "__main__":
    main()
