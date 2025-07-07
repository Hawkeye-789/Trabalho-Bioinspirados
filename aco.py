import sys
import time
import random

# ========== PARÂMETROS ==========

# ACO
num_formigas = 100 # Aumentei para um valor mais comum para ACO puro
num_iteracoes_aco = 100
evaporacao = 0.1
reforco_feromonio = 1.0
feromonio_inicial = 1.0
alfa_aco = 1.0 # Peso do feromônio
beta_aco = 2.0 # Peso da heurística (visibilidade)

# Parâmetros da Busca Local no ACO
max_iter_busca_local_aco = 5 # Número máximo de iterações para a busca local
chance_busca_local_aco = 0.3

# ========== FUNÇÕES AUXILIARES ==========

def calcular_makespan(tempo_processamento, ordem_jobs):
    num_jobs = len(ordem_jobs)
    num_maquinas = len(tempo_processamento[0])
    tempo_fim = [[0]*num_maquinas for _ in range(num_jobs)]
    for i in range(num_jobs):
        job = ordem_jobs[i]
        for m in range(num_maquinas):
            if i == 0 and m == 0:
                tempo_fim[i][m] = tempo_processamento[job][m]
            elif i == 0:
                tempo_fim[i][m] = tempo_fim[i][m-1] + tempo_processamento[job][m]
            elif m == 0:
                tempo_fim[i][m] = tempo_fim[i-1][m] + tempo_processamento[job][m]
            else:
                tempo_fim[i][m] = max(tempo_fim[i-1][m], tempo_fim[i][m-1]) + tempo_processamento[job][m]
    return tempo_fim[-1][-1]

def busca_local_swap(solucao_inicial, tempo_processamento):
    """
    Realiza uma busca local na solução usando a operação de swap.
    Tenta melhorar o makespan trocando pares de jobs até que não haja mais melhorias
    ou o número máximo de iterações seja atingido.
    """
    melhor_solucao = solucao_inicial[:]
    melhor_makespan = calcular_makespan(tempo_processamento, melhor_solucao)
    
    melhorou = True
    iteracoes = 0
    while iteracoes < max_iter_busca_local_aco:
        melhorou = False
        
        # Percorre todos os pares de jobs para tentar um swap
        for i in range(len(melhor_solucao)):
            for j in range(i + 1, len(melhor_solucao)):
                vizinho = melhor_solucao[:]
                vizinho[i], vizinho[j] = vizinho[j], vizinho[i] # Realiza o swap
                
                makespan_vizinho = calcular_makespan(tempo_processamento, vizinho)
                
                if makespan_vizinho < melhor_makespan:
                    melhor_makespan = makespan_vizinho
                    melhor_solucao = vizinho[:]
                    melhorou = True
        iteracoes += 1
    return melhor_solucao, melhor_makespan

def busca_local_insert(solucao_inicial, tempo_processamento):
    melhor_solucao = solucao_inicial[:]
    melhor_makespan = calcular_makespan(tempo_processamento, melhor_solucao)

    melhorou = True
    iteracoes = 0
    while iteracoes < max_iter_busca_local_aco:
        melhorou = False
        
        # Iterar sobre cada job para ser "removido"
        for i in range(len(melhor_solucao)):
            job_removido = melhor_solucao[i]
            temp_list = melhor_solucao[:i] + melhor_solucao[i+1:] # Remove o job
            
            # Iterar sobre cada posição para "inserir" o job
            for j in range(len(temp_list) + 1): # +1 para incluir a inserção no final
                vizinho = temp_list[:j] + [job_removido] + temp_list[j:]
                
                makespan_vizinho = calcular_makespan(tempo_processamento, vizinho)
                
                if makespan_vizinho < melhor_makespan:
                    melhor_makespan = makespan_vizinho
                    melhor_solucao = vizinho[:]
                    melhorou = True
        iteracoes += 1
    return melhor_solucao, melhor_makespan

def busca_local_2opt(solucao_inicial, tempo_processamento):
    melhor_solucao = solucao_inicial[:]
    melhor_makespan = calcular_makespan(tempo_processamento, melhor_solucao)

    melhorou = True
    iteracoes = 0
    while iteracoes < max_iter_busca_local_aco:
        melhorou = False
        
        for i in range(len(melhor_solucao) - 1): # Primeiro ponto
            for j in range(i + 1, len(melhor_solucao)): # Segundo ponto (depois do primeiro)
                vizinho = melhor_solucao[:i] + \
                          melhor_solucao[i:j+1][::-1] + \
                          melhor_solucao[j+1:]
                
                makespan_vizinho = calcular_makespan(tempo_processamento, vizinho)
                
                if makespan_vizinho < melhor_makespan:
                    melhor_makespan = makespan_vizinho
                    melhor_solucao = vizinho[:]
                    melhorou = True
        iteracoes += 1
    return melhor_solucao, melhor_makespan

# ========== ACO ==========

def inicializar_feromonio(n):
    """Inicializa a matriz de feromônio com o valor inicial para todas as arestas."""
    return [[feromonio_inicial for _ in range(n)] for _ in range(n)]

def construir_solucao(feromonio, n, tempo_processamento):
    """
    Constrói uma solução (ordem de jobs) para uma formiga,
    considerando feromônio e heurística.
    """
    nao_visitados = list(range(n))
    atual = random.choice(nao_visitados) # Começa com um job aleatório
    solucao = [atual]
    nao_visitados.remove(atual)

    while nao_visitados:
        probabilidades = []
        for proximo_job in nao_visitados:
            # Heurística: Inverso da soma dos tempos de processamento do job.
            # Jobs com menor tempo total são preferidos.
            soma_tempos_job = sum(tempo_processamento[proximo_job])
            if soma_tempos_job == 0:
                visibilidade = 10000.0 # Valor alto para jobs com tempo de processamento zero
            else:
                visibilidade = 1.0 / soma_tempos_job
            
            # Cálculo da probabilidade usando feromônio e heurística
            prob = (feromonio[atual][proximo_job]**alfa_aco) * (visibilidade**beta_aco)
            probabilidades.append((proximo_job, prob))

        total_prob = sum(p for _, p in probabilidades)
        
        if total_prob == 0:
             # Se todas as probabilidades forem zero, escolha aleatoriamente para evitar erros
             proximo = random.choice(nao_visitados)
        else:
            pesos = [p / total_prob for _, p in probabilidades]
            proximo = random.choices([j for j, _ in probabilidades], weights=pesos, k=1)[0]
        
        solucao.append(proximo)
        nao_visitados.remove(proximo)
        atual = proximo
    return solucao

def atualizar_feromonio(feromonio, solucoes_formigas, makespans_formigas, melhor_solucao_global, melhor_makespan_global):
    """
    Atualiza a matriz de feromônio.
    A evaporação é aplicada a todas as arestas, e o feromônio é depositado
    pela melhor formiga da iteração e pela melhor solução global encontrada até agora.
    """
    n = len(feromonio)
    for i in range(n):
        for j in range(n):
            feromonio[i][j] *= (1 - evaporacao) # Evaporação

    # Encontra a melhor formiga desta iteração para depósito de feromônio
    melhor_formiga_iteracao = None
    melhor_makespan_iteracao = float('inf')
    for s, m in zip(solucoes_formigas, makespans_formigas):
        if m < melhor_makespan_iteracao:
            melhor_makespan_iteracao = m
            melhor_formiga_iteracao = s[:]

    # Depósito de feromônio pela melhor formiga da iteração
    if melhor_formiga_iteracao:
        for i in range(len(melhor_formiga_iteracao) - 1):
            a, b = melhor_formiga_iteracao[i], melhor_formiga_iteracao[i+1]
            feromonio[a][b] += reforco_feromonio / melhor_makespan_iteracao

    # Depósito de feromônio adicional pela melhor solução global (elitismo)
    if melhor_solucao_global:
        for i in range(len(melhor_solucao_global) - 1):
            a, b = melhor_solucao_global[i], melhor_solucao_global[i+1]
            feromonio[a][b] += (reforco_feromonio * 2) / melhor_makespan_global # Reforço maior para o global

def executar_aco(tempo_proc, num_jobs):
    """
    Executa o algoritmo ACO para resolver o FSSP.
    Aplica busca local apenas na melhor formiga de cada iteração, com uma dada probabilidade.
    """
    feromonio = inicializar_feromonio(num_jobs)

    melhor_makespan_global_aco = float('inf')
    melhor_solucao_global_aco = None

    for iter_aco in range(num_iteracoes_aco):
        solucoes_formigas_atuais = []
        makespans_formigas_atuais = []

        # Cada formiga constrói uma solução
        for _ in range(num_formigas):
            solucao = construir_solucao(feromonio, num_jobs, tempo_proc)
            makespan = calcular_makespan(tempo_proc, solucao)
            solucoes_formigas_atuais.append(solucao)
            makespans_formigas_atuais.append(makespan)

        # Encontra a melhor formiga desta iteração
        melhor_formiga_iter_idx = makespans_formigas_atuais.index(min(makespans_formigas_atuais))
        melhor_solucao_iter = solucoes_formigas_atuais[melhor_formiga_iter_idx]
        melhor_makespan_iter = makespans_formigas_atuais[melhor_formiga_iter_idx]

        # === AQUI ESTÁ A MUDANÇA: APLICA A BUSCA LOCAL COM 40% DE CHANCE ===
        solucao_a_otimizar = melhor_solucao_iter[:] # Começa com a melhor da iteração
        makespan_da_otimizacao = melhor_makespan_iter # Seu makespan inicial

        if random.random() < chance_busca_local_aco:
            solucao_otimizada, makespan_otimizado = busca_local_swap(solucao_a_otimizar, tempo_proc)
            # Se a busca local melhorou, usamos a solução otimizada
            if makespan_otimizado < makespan_da_otimizacao:
                solucao_a_otimizar = solucao_otimizada[:]
                makespan_da_otimizacao = makespan_otimizado
        # ==================================================================

        # Atualiza o melhor makespan global se a solução (otimizada ou não) for melhor
        if makespan_da_otimizacao < melhor_makespan_global_aco:
            melhor_makespan_global_aco = makespan_da_otimizacao
            melhor_solucao_global_aco = solucao_a_otimizar[:]
        
        # Atualiza o feromônio
        # Passa as soluções originais das formigas, mas usa a melhor solução global
        # para reforço de feromônio mais significativo (elitismo de feromônio)
        atualizar_feromonio(feromonio, solucoes_formigas_atuais, makespans_formigas_atuais, melhor_solucao_global_aco, melhor_makespan_global_aco)
        
        print(f"Iteração ACO {iter_aco+1}/{num_iteracoes_aco} - Melhor Makespan Atual: {melhor_makespan_global_aco}")

    return melhor_solucao_global_aco, melhor_makespan_global_aco


# ========== MAIN ==========

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python aco_com_busca_local.py fssp_instance_XX.txt")
        sys.exit(1)

    nome_arquivo = sys.argv[1]
    with open(nome_arquivo) as f:
        linhas = f.readlines()
    num_jobs, num_maquinas = map(int, linhas[0].split())
    tempo_processamento = [list(map(int, l.split())) for l in linhas[1:]]

    inicio = time.perf_counter()

    sol_aco, mk_aco = executar_aco(tempo_processamento, num_jobs)

    fim = time.perf_counter()

    print("\n--- ACO com Busca Local (apenas na melhor formiga da iteração) ---")
    print("Melhor solução encontrada:", sol_aco)
    print("Melhor Makespan:", mk_aco)
    print(f"Tempo total de execução: {fim - inicio:.2f} segundos")