import time

def ler_instancia_fssp(nome_arquivo):
    with open(nome_arquivo, 'r') as f:
        linhas = f.readlines()
    
    num_jobs, num_maquinas = map(int, linhas[0].strip().split())
    
    tempo_processamento = []
    for linha in linhas[1:]:
        tempos = list(map(int, linha.strip().split()))
        tempo_processamento.append(tempos)
    
    return tempo_processamento, num_jobs, num_maquinas

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

def main():
    import sys
    if len(sys.argv) < 2:
        print("Uso: python script.py fssp_instance_XX.txt")
        return
    
    nome_arquivo = sys.argv[1]
    
    inicio = time.perf_counter()
    
    tempo_processamento, num_jobs, num_maquinas = ler_instancia_fssp(nome_arquivo)
    
    ordem_jobs = list(range(num_jobs))
    
    makespan = calcular_makespan(tempo_processamento, ordem_jobs)
    
    fim = time.perf_counter()
    
    print(f"Makespan: {makespan}")
    print(f"Tempo de execução: {fim - inicio:.6f} segundos")

if __name__ == "__main__":
    main()
