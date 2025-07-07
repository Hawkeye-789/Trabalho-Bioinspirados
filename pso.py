import sys
import time
import random

# Parâmetros PSO
num_particulas = 100
dist_minima = 5
num_iteracoes_pso = 100
w = 0.2  # Inércia (não diretamente usada no PSO discreto com swaps, mas mantido como referência)
c1 = 0.5 # Coeficiente cognitivo
c2 = 1.0 # Coeficiente social

# ======== PARÂMETROS DA BUSCA LOCAL NO PSO ======== #
chance_busca_local_pso = 1.0 # Exemplo: 30% de chance de aplicar a busca local
max_iter_busca_local_pso = 5 # Número máximo de iterações para a busca local
num_melhores_para_busca_local = 5 # Número de melhores partículas para aplicar a busca local

# ======= LEITURA DO ARQUIVO =======

if len(sys.argv) < 2:
    print("Uso: python pso_fssp.py fssp_instance_XX.txt")
    sys.exit(1)

nome_arquivo = sys.argv[1]

with open(nome_arquivo, 'r') as f:
    linhas = f.readlines()

num_jobs, num_maquinas = map(int, linhas[0].strip().split())
tempo_processamento = [list(map(int, linha.strip().split())) for linha in linhas[1:]]

# ======= FUNÇÃO OBJETIVO =======

def calcular_makespan(tempo_processamento, ordem_jobs):
    num_jobs_ordem = len(ordem_jobs)
    num_maquinas_proc = len(tempo_processamento[0])
    tempo_fim = [[0] * num_maquinas_proc for _ in range(num_jobs_ordem)]

    for i in range(num_jobs_ordem):
        job = ordem_jobs[i]
        for m in range(num_maquinas_proc):
            if i == 0 and m == 0:
                tempo_fim[i][m] = tempo_processamento[job][m]
            elif i == 0:
                tempo_fim[i][m] = tempo_fim[i][m - 1] + tempo_processamento[job][m]
            elif m == 0:
                tempo_fim[i][m] = tempo_fim[i - 1][m] + tempo_processamento[job][m]
            else:
                tempo_fim[i][m] = max(tempo_fim[i - 1][m], tempo_fim[i][m - 1]) + tempo_processamento[job][m]

    return tempo_fim[-1][-1]

# ======= FUNÇÕES DE BUSCA LOCAL =======

def busca_local_swap(solucao_inicial, tempo_processamento, max_iter):
    """
    Realiza uma busca local na solução usando a operação de swap.
    Tenta melhorar o makespan trocando pares de jobs até que não haja mais melhorias
    ou o número máximo de iterações seja atingido.
    """
    melhor_solucao = solucao_inicial[:]
    melhor_makespan = calcular_makespan(tempo_processamento, melhor_solucao)
    
    iteracoes = 0
    while iteracoes < max_iter:
        melhoria_encontrada = False
        
        # Percorre todos os pares de jobs para tentar um swap
        for i in range(len(melhor_solucao)):
            for j in range(i + 1, len(melhor_solucao)):
                vizinho = melhor_solucao[:]
                vizinho[i], vizinho[j] = vizinho[j], vizinho[i] # Realiza o swap
                
                makespan_vizinho = calcular_makespan(tempo_processamento, vizinho)
                
                if makespan_vizinho < melhor_makespan:
                    melhor_makespan = makespan_vizinho
                    melhor_solucao = vizinho[:]
                    melhoria_encontrada = True # Uma melhoria foi encontrada
        
        # Se nenhuma melhoria foi encontrada em uma varredura completa, parar.
        if not melhoria_encontrada:
            break 
        iteracoes += 1
    return melhor_solucao, melhor_makespan

def busca_local_insert(solucao_inicial, tempo_processamento, max_iter):
    """
    Realiza uma busca local na solução usando a operação de inserção.
    Tenta melhorar o makespan movendo um job para outra posição.
    """
    melhor_solucao = solucao_inicial[:]
    melhor_makespan = calcular_makespan(tempo_processamento, melhor_solucao)

    iteracoes = 0
    while iteracoes < max_iter:
        melhoria_encontrada = False
        
        for i in range(len(melhor_solucao)):
            job_removido = melhor_solucao[i]
            temp_list = melhor_solucao[:i] + melhor_solucao[i+1:] # Remove o job
            
            for j in range(len(temp_list) + 1):
                vizinho = temp_list[:j] + [job_removido] + temp_list[j:]
                
                makespan_vizinho = calcular_makespan(tempo_processamento, vizinho)
                
                if makespan_vizinho < melhor_makespan:
                    melhor_makespan = makespan_vizinho
                    melhor_solucao = vizinho[:]
                    melhoria_encontrada = True
        
        if not melhoria_encontrada:
            break
        iteracoes += 1
    return melhor_solucao, melhor_makespan


# ======= CLASSE PARTÍCULA =======

class Particula:
    def __init__(self, permutacao, indice):
        self.indice = indice
        self.posicao = permutacao[:]
        self.melhor_posicao = permutacao[:]
        self.melhor_valor = calcular_makespan(tempo_processamento, permutacao)
        self.melhor_vizinha = permutacao[:]

# ======= UTILITÁRIOS =======

def distancia_permutacao(p1, p2):
    return sum(1 for a, b in zip(p1, p2) if a != b)

def obter_diferencas(a, b):
    # Retorna uma lista de swaps para transformar a em b
    swaps = []
    a_copy = list(a) # Trabalha com uma cópia mutável
    
    # Mapeia a posição atual de cada elemento em a_copy
    pos_map = {val: idx for idx, val in enumerate(a_copy)}

    for i in range(len(a_copy)):
        if a_copy[i] != b[i]:
            val_to_find = b[i]
            j = pos_map[val_to_find] # Encontra a posição do elemento que deveria estar aqui
            
            # Registra o swap
            swaps.append((i, j))
            
            # Realiza o swap em a_copy
            val_at_i = a_copy[i]
            a_copy[i], a_copy[j] = a_copy[j], a_copy[i]
            
            # Atualiza o mapa de posições para os elementos que foram movidos
            pos_map[val_to_find] = i
            pos_map[val_at_i] = j
    return swaps

def aplicar_swaps(permutacao, swaps, prob=1.0):
    permutacao = permutacao[:] # Trabalha com uma cópia para não alterar a original
    for i, j in swaps:
        if random.random() < prob:
            # Garante que os índices sejam válidos
            if 0 <= i < len(permutacao) and 0 <= j < len(permutacao):
                permutacao[i], permutacao[j] = permutacao[j], permutacao[i]
    return permutacao

# ======= GERAÇÃO DO ENXAME =======

def gerar_enxame():
    enxame = []
    
    while len(enxame) < num_particulas:
        nova = random.sample(range(num_jobs), num_jobs)
        # Permite adicionar se ainda há espaço e a distância é aceitável, ou se é uma das primeiras
        if all(distancia_permutacao(nova, p.posicao) >= dist_minima for p in enxame) or len(enxame) < num_particulas / 4:
            particula = Particula(nova, len(enxame))
            enxame.append(particula)
        elif len(enxame) < num_particulas: # fallback para preencher se a distancia_minima for muito restritiva
            particula = Particula(nova, len(enxame))
            enxame.append(particula)
    return enxame

# ======= ATUALIZAÇÃO =======

def atualizar_particula(particula, enxame):
    # Encontra a melhor vizinha (topologia de anel de 5 vizinhos)
    vizinhos = []
    for offset in range(-2, 3):
        if offset == 0: continue # Não inclui a própria partícula como vizinho
        idx = (particula.indice + offset) % len(enxame)
        vizinhos.append(enxame[idx]) # Adiciona o objeto Particula
    
    # Encontra a melhor partícula entre os vizinhos
    melhor_vizinha_obj = min(vizinhos, key=lambda p: p.melhor_valor)
    particula.melhor_vizinha = melhor_vizinha_obj.melhor_posicao[:] # Copia a melhor posição da melhor vizinha

    # Calcula os swaps para as componentes cognitivas e sociais
    swaps_cognitivo = obter_diferencas(particula.posicao, particula.melhor_posicao)
    swaps_social = obter_diferencas(particula.posicao, particula.melhor_vizinha)

    # Aplica os swaps para gerar a nova posição
    nova_posicao = aplicar_swaps(particula.posicao, swaps_cognitivo, prob=c1)
    nova_posicao = aplicar_swaps(nova_posicao, swaps_social, prob=c2)

    particula.posicao = nova_posicao

# ======= PSO DISCRETO PRINCIPAL =======

def executar_pso_discreto():
    enxame = gerar_enxame()
    melhor_global_valor = float('inf')
    melhor_global_posicao = None

    # Inicializa o melhor global com a melhor partícula inicial
    for particula in enxame:
        if particula.melhor_valor < melhor_global_valor:
            melhor_global_valor = particula.melhor_valor
            melhor_global_posicao = particula.melhor_posicao[:]

    for iter_pso in range(num_iteracoes_pso):
        # Atualiza o melhor valor e posição de cada partícula e o melhor global
        for particula in enxame:
            valor_atual = calcular_makespan(tempo_processamento, particula.posicao)

            if valor_atual < particula.melhor_valor:
                particula.melhor_valor = valor_atual
                particula.melhor_posicao = particula.posicao[:]

            if valor_atual < melhor_global_valor:
                melhor_global_valor = valor_atual
                melhor_global_posicao = particula.posicao[:]
        
        # --- APLICAÇÃO DA BUSCA LOCAL NAS MELHORES PARTÍCULAS COM CHANCE ---
        # 1. Classifica as partículas pelo seu melhor valor (pbest)
        particulas_ordenadas = sorted(enxame, key=lambda p: p.melhor_valor)
        
        # 2. Seleciona as N melhores para potencial busca local
        melhores_para_bl = particulas_ordenadas[:num_melhores_para_busca_local]

        # 3. Aplica busca local em cada uma delas com a chance definida
        for particula_alvo in melhores_para_bl:
            if random.random() < chance_busca_local_pso:
                # Usa a melhor posição da partícula como ponto de partida para a busca local
                solucao_otimizada_bl, makespan_otimizada_bl = busca_local_swap(
                    particula_alvo.melhor_posicao, tempo_processamento, max_iter_busca_local_pso
                )
                
                # Se a busca local melhorou a melhor posição da partícula
                if makespan_otimizada_bl < particula_alvo.melhor_valor:
                    particula_alvo.melhor_valor = makespan_otimizada_bl
                    particula_alvo.melhor_posicao = solucao_otimizada_bl[:]
                    
                    # Se esta melhoria também for melhor que o global, atualiza o global
                    if makespan_otimizada_bl < melhor_global_valor:
                        melhor_global_valor = makespan_otimizada_bl
                        melhor_global_posicao = solucao_otimizada_bl[:]
        # ---------------------------------------------------------------------

        # Atualiza a posição de cada partícula com base nos swaps
        for particula in enxame:
            atualizar_particula(particula, enxame)

        print(f"Iteração PSO {iter_pso+1}/{num_iteracoes_pso} - Melhor Makespan Atual: {melhor_global_valor}")

    return melhor_global_posicao, melhor_global_valor

# ======= MAIN =======

def main():
    inicio = time.perf_counter()
    solucao, makespan = executar_pso_discreto()
    fim = time.perf_counter()

    print("\n--- PSO DISCRETO HÍBRIDO (Busca Local nas Top N Partículas) ---")
    print("Melhor solução encontrada:", solucao)
    print("Makespan:", makespan)
    print(f"Tempo de execução: {fim - inicio:.6f} segundos")

if __name__ == "__main__":
    main()