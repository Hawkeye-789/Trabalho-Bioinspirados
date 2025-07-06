import random
import csv
import itertools
import statistics

# ======= PARÂMETROS DO EXPERIMENTO ======= #
ws = [0.2, 0.5, 0.8]
c1s = [0.5, 1.0, 1.5]
c2s = [0.5, 1.0, 1.5]

num_iteracoes_pso = 100
num_particulas = 100
dist_minima = 5

arquivo_instancia = "fssp_instance_12.txt"

# ======= LEITURA DA INSTÂNCIA ======= #
with open(arquivo_instancia, 'r') as f:
    linhas = f.readlines()

num_jobs, num_maquinas = map(int, linhas[0].strip().split())
tempo_processamento = [list(map(int, linha.strip().split())) for linha in linhas[1:]]

# ======= FUNÇÃO OBJETIVO ======= #
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

# ======= CLASSE E FUNÇÕES DO PSO ======= #
class Particula:
    def __init__(self, permutacao, indice):
        self.indice = indice
        self.posicao = permutacao[:]
        self.velocidade = []
        self.melhor_posicao = permutacao[:]
        self.melhor_valor = float('inf')
        self.melhor_vizinha = permutacao[:]

def distancia_permutacao(p1, p2):
    return sum(1 for a, b in zip(p1, p2) if a != b)

def obter_diferencas(a, b):
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

def atualizar_particula(particula, enxame, w, c1, c2):
    vizinhos = []
    for offset in range(-2, 3):
        idx = (particula.indice + offset) % len(enxame)
        vizinhos.append(idx)
    melhor_vizinha_idx = min(vizinhos, key=lambda i: enxame[i].melhor_valor)
    particula.melhor_vizinha = enxame[melhor_vizinha_idx].melhor_posicao

    swaps_inercia = obter_diferencas(particula.posicao, aplicar_swaps(particula.posicao, particula.velocidade))
    swaps_cognitivo = obter_diferencas(particula.posicao, particula.melhor_posicao)
    swaps_social = obter_diferencas(particula.posicao, particula.melhor_vizinha)

    nova_pos = aplicar_swaps(particula.posicao, swaps_inercia, prob=w)
    nova_pos = aplicar_swaps(nova_pos, swaps_cognitivo, prob=c1)
    nova_pos = aplicar_swaps(nova_pos, swaps_social, prob=c2)

    particula.velocidade = obter_diferencas(particula.posicao, nova_pos)
    particula.posicao = nova_pos

def gerar_enxame(populacao, num_particulas, dist_minima):
    fitnesses = [(ind, calcular_makespan(tempo_processamento, ind)) for ind in populacao]
    fitnesses.sort(key=lambda x: x[1])
    enxame = []
    adicionados = []

    for ind, _ in fitnesses:
        if len(enxame) >= num_particulas:
            break
        if all(distancia_permutacao(ind, outro) >= dist_minima for outro in adicionados):
            particula = Particula(ind, len(enxame))
            enxame.append(particula)
            adicionados.append(ind)

    while len(enxame) < num_particulas:
        perm = random.sample(range(num_jobs), num_jobs)
        particula = Particula(perm, len(enxame))
        enxame.append(particula)
    return enxame

def executar_pso_discreto(w, c1, c2):
    populacao_inicial = [random.sample(range(num_jobs), num_jobs) for _ in range(num_particulas * 2)]
    enxame = gerar_enxame(populacao_inicial, num_particulas, dist_minima)

    melhor_global_valor = float('inf')
    melhor_global_pos = None

    for _ in range(num_iteracoes_pso):
        for particula in enxame:
            valor = calcular_makespan(tempo_processamento, particula.posicao)
            if valor < particula.melhor_valor:
                particula.melhor_valor = valor
                particula.melhor_posicao = particula.posicao[:]
            if valor < melhor_global_valor:
                melhor_global_valor = valor
                melhor_global_pos = particula.posicao[:]
        for particula in enxame:
            atualizar_particula(particula, enxame, w, c1, c2)

    return melhor_global_valor

# ======= EXPERIMENTO FATORIAL PSO ======= #
combinacoes = list(itertools.product(ws, c1s, c2s))
with open("resultados_fatoriais_pso_fssp.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["w", "c1", "c2", "media_makespan", "desvio_padrao"])

    total = len(combinacoes)
    for idx, (w, c1, c2) in enumerate(combinacoes, 1):
        resultados = []
        for rep in range(10):
            random.seed(rep)
            makespan = executar_pso_discreto(w, c1, c2)
            resultados.append(makespan)

        media = statistics.mean(resultados)
        desvio = statistics.stdev(resultados)
        writer.writerow([w, c1, c2, media, desvio])
        print(f"[{idx}/{total}] w={w}, c1={c1}, c2={c2} -> média={media:.2f}, desvio={desvio:.2f}")
