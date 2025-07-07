import sys
import time
import random
import numpy as np

# ======== PARÂMETROS GLOBAIS ======== #
tamanho_populacao = 100
num_geracoes = 100
taxa_mutacao = 0.2
metodo_selecao = 'torneio'  # 'torneio' ou 'roleta'
tamanho_torneio = 3
metodo_cruzamento = 'cx'  # 'cx' ou 'erx'
metodo_mutacao = 'swap'  # 'swap' ou 'deslocamento'
elitismo_k = 1

# FSSP
tempo_processamento = []
num_jobs = 0
num_maquinas = 0

# PSO
num_particulas = 100
dist_minima = 5
num_iteracoes_pso = 100
w = 0.2
c1 = 1.0
c2 = 0.5


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

#====== INICIAR POPULAÇÂO =====#

def criar_populacao():
    return [random.sample(range(num_jobs), num_jobs) for _ in range(tamanho_populacao)]

#====== MUTAÇÃO ======#

def mutacao_swap(individuo, taxa_mutacao):
    #Aplica mutação por troca de duas tarefas aleatórios em um indivíduo,
    #com uma chance dada pela taxa de mutação.
    novo_individuo = individuo[:]

    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(novo_individuo)), 2)
        novo_individuo[i], novo_individuo[j] = novo_individuo[j], novo_individuo[i]

    return novo_individuo

def mutacao_deslocamento_subsequencia(individuo, taxa_mutacao):
    novo_individuo = individuo[:]
    n = len(novo_individuo)

    if random.random() < taxa_mutacao:
        i, j = sorted(random.sample(range(n), 2))
        bloco = novo_individuo[i:j+1]
        del novo_individuo[i:j+1]

        posicoes_validas = list(range(len(novo_individuo) + 1))
        nova_posicao = random.choice(posicoes_validas)

        novo_individuo[nova_posicao:nova_posicao] = bloco

    return novo_individuo

def mutacao_atual(individuo, metodo_mutacao, taxa_mutacao):
    if metodo_mutacao == 'swap':
        return mutacao_swap(individuo, taxa_mutacao)
    elif metodo_mutacao == 'deslocamento':
        return mutacao_deslocamento_subsequencia(individuo, taxa_mutacao)
    else:
        raise ValueError(f"Método de mutação desconhecido: {metodo_mutacao}")



#====== CRUZAMENTO ======#

def crossover_cx(pai1, pai2):

    #Cycle Crossover (CX)
    #Retorna um filho mantendo ciclos de posição entre pai1 e pai2.

    tamanho = len(pai1)
    filho = [None] * tamanho
    usado = [False] * tamanho

    # Começamos o ciclo a partir da posição 0
    pos = 0
    while not usado[pos]:
        valor = pai1[pos]
        filho[pos] = valor
        usado[pos] = True
        pos = pai1.index(pai2[pos])

    # Preenche o restante com elementos do pai2
    for i in range(tamanho):
        if filho[i] is None:
            filho[i] = pai2[i]

    return filho

def construir_tabela_arestas(pai1, pai2):

    #Cria a tabela de vizinhos (arestas) de cada elemento com base nos dois pais.

    def vizinhos(lst, i):
        n = len(lst)
        idx = lst.index(i)
        return [lst[(idx - 1) % n], lst[(idx + 1) % n]]

    arestas = {}
    for gene in pai1:
        arestas[gene] = set(vizinhos(pai1, gene))
    for gene in pai2:
        arestas[gene].update(vizinhos(pai2, gene))

    return arestas

def crossover_erx(pai1, pai2):
    
    #Edge Recombination Crossover (ERX)
    #Cria um filho preservando as relações de vizinhança dos pais.
    
    arestas = construir_tabela_arestas(pai1, pai2)
    filho = []

    gene_atual = random.choice(pai1)  # Pode começar com qualquer gene
    while len(filho) < len(pai1):
        filho.append(gene_atual)

        # Remove gene_atual de todas as listas de vizinhança
        for vizinhos in arestas.values():
            vizinhos.discard(gene_atual)

        del arestas[gene_atual]  # Remove o gene atual do dicionário

        if arestas:
            # Escolhe próximo gene com menos vizinhos (prioridade)
            gene_atual = min(arestas, key=lambda k: len(arestas[k]))
        else:
            break

    return filho

def cruzamento_atual(pai1, pai2, metodo_cruzamento):

    if metodo_cruzamento == 'cx':
        return crossover_cx(pai1, pai2)
    elif metodo_cruzamento == 'erx':
        return crossover_erx(pai1, pai2)
    else:
        raise ValueError(f"Método de cruzamento desconhecido: {metodo_cruzamento}")


#====== METODO DE SELEÇÃO ======#

def selecao_torneio(populacao, fitnesses, tamanho_torneio=3):
    indices = random.sample(range(len(populacao)), tamanho_torneio)
    melhor_indice = max(indices, key=lambda i: fitnesses[i])
    return populacao[melhor_indice]

def selecao_roleta(populacao, fitnesses):
    soma = sum(fitnesses)
    if soma == 0:
        return random.choice(populacao)
    probabilidades = [f / soma for f in fitnesses]
    return random.choices(populacao, weights=probabilidades, k=1)[0]

def selecionar_pais(populacao, fitnesses, metodo='torneio', tamanho_torneio=3):
    #Seleciona dois pais da população usando o método especificado.

    if metodo == 'torneio':
        pai1 = selecao_torneio(populacao, fitnesses, tamanho_torneio)
        pai2 = selecao_torneio(populacao, fitnesses, tamanho_torneio)
    elif metodo == 'roleta':
        pai1 = selecao_roleta(populacao, fitnesses)
        pai2 = selecao_roleta(populacao, fitnesses)
    else:
        raise ValueError(f"Método de seleção desconhecido: {metodo}")
    
    return pai1, pai2

#====== ELITISMO ======#

def elitismo(populacao, fitnesses, k):

    elite_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)[:k]
    elite = [populacao[i] for i in elite_indices]
    return elite


#====== ALGORITMO GENETICO======#

def algoritmo_genetico():
    # Inicializa população com permutações aleatórias de jobs
    populacao = criar_populacao()

    melhor_global = float('inf')
    ultima_melhora = 0
    taxa_mutacao_atual = taxa_mutacao


    for geracao in range(num_geracoes):

        # === Avaliação ===
        makespans = [calcular_makespan(tempo_processamento, ind) for ind in populacao]
        fitnesses = [1 / m for m in makespans]

        melhor = min(makespans)

        # === Verifica se houve melhoria ===
        if melhor < melhor_global:
            melhor_global = melhor
            ultima_melhora = geracao
        else:
            # Se não melhora há mais de 5 gerações, aumenta mutação
            if geracao - ultima_melhora > 5:
                taxa_mutacao_atual = min(1.0, taxa_mutacao_atual * 1.2)
            else:
                taxa_mutacao_atual = taxa_mutacao



        # Elitismo: selecionar os k melhores indivíduos
        nova_populacao = elitismo(populacao, fitnesses, elitismo_k)

        # Gerar novos indivíduos até completar a população
        while len(nova_populacao) < tamanho_populacao:
            pai1, pai2 = selecionar_pais(populacao, fitnesses, metodo=metodo_selecao, tamanho_torneio=tamanho_torneio)

            # Cruzamento
            filho = cruzamento_atual(pai1, pai2, metodo_cruzamento)

            # Mutação
            filho = mutacao_atual(filho, metodo_mutacao, taxa_mutacao_atual)

            nova_populacao.append(filho)

            # === Chance de adicionar novos indivíduos aleatórios ===
            chance_injecao = 0.1  # 10% de chance por geração
            if random.random() < chance_injecao:
                num_injetados = random.randint(1, 3)
                for _ in range(num_injetados):
                    novo_individuo = random.sample(range(num_jobs), num_jobs)
                    nova_populacao[random.randint(0, len(nova_populacao)-1)] = novo_individuo

        populacao = nova_populacao

    # Avaliar população final
    fitnesses = [1 / calcular_makespan(tempo_processamento, ind) for ind in populacao]
    melhor_indice = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
    melhor_solucao = populacao[melhor_indice]
    melhor_makespan = calcular_makespan(tempo_processamento, melhor_solucao)
    enxame = gerar_enxame(populacao, tempo_processamento, num_particulas, dist_minima)


    return melhor_solucao, melhor_makespan, enxame



#====== FORMAÇÃO DO ENXAME ======#

class Particula:
    def __init__(self, permutacao, indice):
        self.indice = indice
        self.posicao = permutacao[:]  # permutação dos jobs
        self.melhor_posicao = permutacao[:]
        self.melhor_valor = float('inf')
        self.melhor_vizinha = permutacao[:]  # inicializada com uma cópia
        self.velocidade = []  # lista de swaps da última iteração




def distancia_permutacao(p1, p2):
    return sum(1 for a, b in zip(p1, p2) if a != b)



def adicionar_ao_enxame(selecionados, candidato, dist_minima):
    for s in selecionados:
        if distancia_permutacao(s, candidato) < dist_minima:
            return False  # Muito próximo de outro
    selecionados.append(candidato)
    return True

def gerar_enxame(populacao, tempo_processamento, num_particulas, dist_minima):
    fitnesses = [(ind, calcular_makespan(tempo_processamento, ind)) for ind in populacao]
    fitnesses.sort(key=lambda x: x[1])

    enxame = []
    permutacoes_adicionadas = []

    for ind, _ in fitnesses:
        if len(enxame) >= num_particulas:
            break
        if all(distancia_permutacao(ind, outro) >= dist_minima for outro in permutacoes_adicionadas):
            particula = Particula(ind, len(enxame))
            enxame.append(particula)
            permutacoes_adicionadas.append(ind)

    return enxame

#====== VELOCIDADE ======#

def obter_diferencas(a, b):
    """Retorna os swaps necessários para transformar a em b."""
    a = a[:]
    swaps = []
    for i in range(len(a)):
        if a[i] != b[i]:
            j = a.index(b[i])
            swaps.append((i, j))
            a[i], a[j] = a[j], a[i]
    return swaps

def aplicar_swaps(permutacao, swaps, prob=1.0):
    permutacao = permutacao[:]
    for i, j in swaps:
        if random.random() < prob:
            permutacao[i], permutacao[j] = permutacao[j], permutacao[i]
    return permutacao





#===== ATUALIZAR PARTICULAS ======#

def atualizar_particula(particula, enxame):
    vizinhos = []
    for offset in range(-2, 3):
        idx = (particula.indice + offset) % len(enxame)
        vizinhos.append(idx)
    melhor_vizinha_idx = min(vizinhos, key=lambda i: enxame[i].melhor_valor)
    particula.melhor_vizinha = enxame[melhor_vizinha_idx].melhor_posicao

    # === Obter componentes ===
    swaps_inercia = particula.velocidade[:]  # reutiliza swaps anteriores
    swaps_cognitivo = obter_diferencas(particula.posicao, particula.melhor_posicao)
    swaps_social = obter_diferencas(particula.posicao, particula.melhor_vizinha)

    # === Aplicar os swaps ===
    nova_posicao = aplicar_swaps(particula.posicao, swaps_inercia, prob=w)
    nova_posicao = aplicar_swaps(nova_posicao, swaps_cognitivo, prob=c1)
    nova_posicao = aplicar_swaps(nova_posicao, swaps_social, prob=c2)

    # === Atualizar partícula ===
    particula.velocidade = obter_diferencas(particula.posicao, nova_posicao)
    particula.posicao = nova_posicao




#====== PSO ======#

def executar_pso_discreto(enxame, tempo_processamento):
    melhor_global_valor = float('inf')
    melhor_global_posicao = None

    for iteracao in range(num_iteracoes_pso):
        for particula in enxame:
            valor_atual = calcular_makespan(tempo_processamento, particula.posicao)

            if valor_atual < particula.melhor_valor:
                particula.melhor_valor = valor_atual
                particula.melhor_posicao = particula.posicao[:]

            if valor_atual < melhor_global_valor:
                melhor_global_valor = valor_atual
                melhor_global_posicao = particula.posicao[:]

        for particula in enxame:
            atualizar_particula(particula, enxame)
    
    return melhor_global_posicao, melhor_global_valor







def main():
    inicio = time.perf_counter()

    solucao, makespan, enxame_inicial = algoritmo_genetico()
    solucao_pso, makespan_pso = executar_pso_discreto(enxame_inicial, tempo_processamento)

    fim = time.perf_counter()
    print("\n--- Genetico ---")
    print("Melhor solução encontrada:", solucao)
    print("Makespan:", makespan)
    
    print("\n--- PSO ---")
    print("Melhor solução encontrada pelo PSO:", solucao_pso)
    print("Makespan PSO:", makespan_pso)

    print(f"Tempo de execução: {fim - inicio:.6f} segundos")


if __name__ == "__main__":
    main()
