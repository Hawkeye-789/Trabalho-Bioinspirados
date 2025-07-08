import subprocess
import statistics

nome_script = "ag_clonalg_fssp.py"
nome_arquivo = "fssp_instance_05.txt"
resultados = []

for i in range(10):
    print(f"Executando {i + 1}/10...")
    resultado = subprocess.run(
        ["python", nome_script, nome_arquivo],
        capture_output=True,
        text=True
    )

    saida = resultado.stdout
    print(saida)

    for linha in saida.splitlines():
        if "Makespan:" in linha:
            try:
                valor = int(linha.strip().split(":")[1])
                resultados.append(valor)
            except:
                print("Erro ao ler makespan da linha:", linha)
            break

print("\n===== Resultados =====")
print("Makespans:", resultados)

if resultados:
    print("Melhor:", min(resultados))
    print("Média:", round(statistics.mean(resultados), 2))
    print("Desvio padrão:", round(statistics.stdev(resultados), 2))
else:
    print("Nenhum makespan foi capturado.")
