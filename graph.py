import matplotlib.pyplot as plt
import pandas as pd
import glob
import os

# Certifique-se de que os arquivos CSV estão no diretório correto
# e seguem o padrão de nome "convergencia_run_*.csv"
arquivos = glob.glob("convergencia_execucao_*.csv")

# Verificação para ter certeza de que arquivos foram encontrados
if not arquivos:
    print("Nenhum arquivo CSV encontrado com o padrão 'convergencia_run_*.csv'.")
    print("Verifique o diretório ou o padrão do nome do arquivo.")
else:
    plt.figure(figsize=(10, 6)) # Opcional: define o tamanho da figura para melhor visualização

    for arquivo in arquivos:
        df = pd.read_csv(arquivo)
        nome_curto = os.path.basename(arquivo).replace(".csv", "").replace("convergencia_e", "E")
        
        # === CORREÇÃO AQUI: Use os nomes exatos das colunas do CSV ===
        plt.plot(df["Iteracao"], df["MelhorMakespan"], label=nome_curto)

    plt.xlabel("Iteração")
    plt.ylabel("Melhor Makespan")
    plt.title("Convergência - Algoritmo de Colônia de Abelhas")
    plt.legend()
    plt.grid(True)
    plt.tight_layout() # Ajusta o layout para evitar sobreposição
    plt.savefig("grafico_convergencia_abc.png")
    plt.show()