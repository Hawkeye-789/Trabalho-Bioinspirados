import sys
import time
import random

# Parâmetros PSO
num_particulas = 100
dist_minima = 5
num_iteracoes_pso = 100
w = 0.7
c1 = 0.8
c2 = 0.8

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
    swaps = []
    a = a[:]
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

# ======= GERAÇÃO DO ENXAME =======

def gerar_enxame():
    enxame = []
    adicionadas = []

    while len(enxame) < num_particulas:
        nova = random.sample(range(num_jobs), num_jobs)
        if all(distancia_permutacao(nova, outro) >= dist_minima for outro in adicionadas):
            particula = Particula(nova, len(enxame))
            enxame.append(particula)
            adicionadas.append(nova)

    return enxame

# ======= ATUALIZAÇÃO =======

def atualizar_particula(particula, enxame):
    vizinhos = []
    for offset in range(-2, 3):
        idx = (particula.indice + offset) % len(enxame)
        vizinhos.append(idx)
    melhor_vizinha_idx = min(vizinhos, key=lambda i: enxame[i].melhor_valor)
    particula.melhor_vizinha = enxame[melhor_vizinha_idx].melhor_posicao

    swaps_cognitivo = obter_diferencas(particula.posicao, particula.melhor_posicao)
    swaps_social = obter_diferencas(particula.posicao, particula.melhor_vizinha)

    nova_posicao = aplicar_swaps(particula.posicao, swaps_cognitivo, prob=c1)
    nova_posicao = aplicar_swaps(nova_posicao, swaps_social, prob=c2)

    particula.posicao = nova_posicao

# ======= PSO DISCRETO PRINCIPAL =======

def executar_pso_discreto():
    enxame = gerar_enxame()
    melhor_global_valor = float('inf')
    melhor_global_posicao = None

    for _ in range(num_iteracoes_pso):
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

# ======= MAIN =======

def main():
    inicio = time.perf_counter()
    solucao, makespan = executar_pso_discreto()
    fim = time.perf_counter()

    print("\n--- PSO DISCRETO ---")
    print("Melhor solução encontrada:", solucao)
    print("Makespan:", makespan)
    print(f"Tempo de execução: {fim - inicio:.6f} segundos")

if __name__ == "__main__":
    main()
