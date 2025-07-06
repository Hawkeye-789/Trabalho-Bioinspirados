import csv
import itertools
import statistics
import random

# === PARÂMETROS DO EXPERIMENTO === #

tamanhos_pop = [100]
num_geracoes_list = [100]
taxas_mutacao = [0.05, 0.1, 0.2]
metodos_selecao = ['torneio', 'roleta']
tamanhos_torneio = [2, 3, 5]
metodos_cruzamento = ['cx', 'erx']
metodos_mutacao = ['swap', 'deslocamento']
elitismos_k = [0, 1]

# Arquivo da instância
nome_arquivo = "fssp_instance_05.txt"

# === LER INSTÂNCIA === #

with open(nome_arquivo, 'r') as f:
    linhas = f.readlines()

num_jobs, num_maquinas = map(int, linhas[0].strip().split())
tempo_processamento = [list(map(int, linha.strip().split())) for linha in linhas[1:]]

# === GERAÇÃO DE COMBINAÇÕES DE PARÂMETROS === #

todas_combinacoes = list(itertools.product(
    tamanhos_pop,
    num_geracoes_list,
    taxas_mutacao,
    metodos_selecao,
    tamanhos_torneio,
    metodos_cruzamento,
    metodos_mutacao,
    elitismos_k
))

# === FUNÇÕES AUXILIARES === #

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

def algoritmo_genetico(tamanho_populacao, num_geracoes, taxa_mutacao,
                       metodo_selecao, tamanho_torneio,
                       metodo_cruzamento, metodo_mutacao, elitismo_k):
    
    def criar_populacao():
        return [random.sample(range(num_jobs), num_jobs) for _ in range(tamanho_populacao)]

    def mutacao_swap(individuo):
        novo = individuo[:]
        if random.random() < taxa_mutacao:
            i, j = random.sample(range(num_jobs), 2)
            novo[i], novo[j] = novo[j], novo[i]
        return novo

    def mutacao_deslocamento(individuo):
        novo = individuo[:]
        if random.random() < taxa_mutacao:
            i, j = sorted(random.sample(range(num_jobs), 2))
            bloco = novo[i:j+1]
            del novo[i:j+1]
            pos = random.randint(0, len(novo))
            novo[pos:pos] = bloco
        return novo

    def mutacao(ind):
        if metodo_mutacao == 'swap':
            return mutacao_swap(ind)
        else:
            return mutacao_deslocamento(ind)

    def crossover_cx(p1, p2):
        size = len(p1)
        filho = [None] * size
        usado = [False] * size
        pos = 0
        while not usado[pos]:
            val = p1[pos]
            filho[pos] = val
            usado[pos] = True
            pos = p1.index(p2[pos])
        for i in range(size):
            if filho[i] is None:
                filho[i] = p2[i]
        return filho

    def crossover_erx(p1, p2):
        def vizinhos(lst, i):
            idx = lst.index(i)
            return [lst[(idx - 1) % num_jobs], lst[(idx + 1) % num_jobs]]
        arestas = {g: set(vizinhos(p1, g) + vizinhos(p2, g)) for g in p1}
        filho, atual = [], random.choice(p1)
        while len(filho) < num_jobs:
            filho.append(atual)
            for vs in arestas.values():
                vs.discard(atual)
            arestas.pop(atual, None)
            if arestas:
                atual = min(arestas, key=lambda k: len(arestas[k]))
        return filho

    def cruzamento(p1, p2):
        if metodo_cruzamento == 'cx':
            return crossover_cx(p1, p2)
        else:
            return crossover_erx(p1, p2)

    def selecao_roleta(pop, fits):
        soma = sum(fits)
        probs = [f/soma for f in fits]
        return random.choices(pop, weights=probs, k=1)[0]

    def selecao_torneio(pop, fits):
        indices = random.sample(range(len(pop)), tamanho_torneio)
        return pop[max(indices, key=lambda i: fits[i])]

    def selecionar_pais(pop, fits):
        if metodo_selecao == 'roleta':
            return selecao_roleta(pop, fits), selecao_roleta(pop, fits)
        else:
            return selecao_torneio(pop, fits), selecao_torneio(pop, fits)

    def aplicar_elitismo(pop, fits, k):
        elites = sorted(range(len(fits)), key=lambda i: fits[i], reverse=True)[:k]
        return [pop[i] for i in elites]

    populacao = criar_populacao()
    melhor_global = float('inf')
    taxa_mutacao_dinamica = taxa_mutacao

    for g in range(num_geracoes):
        makespans = [calcular_makespan(tempo_processamento, ind) for ind in populacao]
        fitnesses = [1/m for m in makespans]
        melhor = min(makespans)

        if melhor < melhor_global:
            melhor_global = melhor
            ultima_melhora = g
        elif g - ultima_melhora > 5:
            taxa_mutacao_dinamica = min(1.0, taxa_mutacao_dinamica * 1.2)
        else:
            taxa_mutacao_dinamica = taxa_mutacao

        nova = aplicar_elitismo(populacao, fitnesses, elitismo_k)
        while len(nova) < tamanho_populacao:
            p1, p2 = selecionar_pais(populacao, fitnesses)
            filho = cruzamento(p1, p2)
            filho = mutacao(filho)
            nova.append(filho)
            if random.random() < 0.1:
                nova[random.randint(0, len(nova)-1)] = random.sample(range(num_jobs), num_jobs)

        populacao = nova

    final = [calcular_makespan(tempo_processamento, ind) for ind in populacao]
    return min(final)


# === EXECUTAR EXPERIMENTO E SALVAR CSV === #

with open('resultados_fatoriais_ag_fssp.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["pop", "ger", "mut", "sel", "k", "cx", "mt", "elitismo", "media_makespan", "desvio_padrao"])

    for idx, (pop, ger, mut, sel, k, cx, mt, elit) in enumerate(todas_combinacoes, 1):
        melhores = []
        for rep in range(10):
            random.seed(rep)  # Reprodutibilidade
            resultado = algoritmo_genetico(pop, ger, mut, sel, k, cx, mt, elit)
            melhores.append(resultado)

        media = statistics.mean(melhores)
        desvio = statistics.stdev(melhores)
        writer.writerow([pop, ger, mut, sel, k, cx, mt, elit, media, desvio])
        print(f"[{idx}/{len(todas_combinacoes)}] média={media:.2f}, desvio={desvio:.2f}")
