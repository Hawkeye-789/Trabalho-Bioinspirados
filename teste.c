#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <time.h>
#include <math.h>

#define MAX_JOBS 1000
#define MAX_MACHINES 100

#define REPETICOES 200

int num_jobs, num_machines;
int tempos[MAX_JOBS][MAX_MACHINES];

// ... sua função calcular_makespan, swap, gerar_vizinho, copia_seq, busca_local_rvnd (mesmo código que enviou) ...

double calcular_makespan(int *sequencia) {
    double completions[MAX_JOBS][MAX_MACHINES] = {{0.0}};
    for (int i = 0; i < num_jobs; i++) {
        int job = sequencia[i];
        for (int m = 0; m < num_machines; m++) {
            if (i == 0 && m == 0)
                completions[i][m] = tempos[job][m];
            else if (i == 0)
                completions[i][m] = completions[i][m - 1] + tempos[job][m];
            else if (m == 0)
                completions[i][m] = completions[i - 1][m] + tempos[job][m];
            else
                completions[i][m] = fmax(completions[i][m - 1], completions[i - 1][m]) + tempos[job][m];
        }
    }
    return completions[num_jobs - 1][num_machines - 1];
}

void swap(int *a, int *b) {
    int tmp = *a;
    *a = *b;
    *b = tmp;
}

void gerar_vizinho(int *orig, int *dest) {
    memcpy(dest, orig, sizeof(int) * num_jobs);
    if (rand() % 2 == 0) {
        int i = rand() % num_jobs;
        int j = rand() % num_jobs;
        while (j == i) j = rand() % num_jobs;
        swap(&dest[i], &dest[j]);
    } else {
        int i = rand() % num_jobs;
        int j = rand() % num_jobs;
        while (j == i) j = rand() % num_jobs;
        int job = dest[i];
        if (i < j) {
            for (int k = i; k < j; k++) dest[k] = dest[k + 1];
        } else {
            for (int k = i; k > j; k--) dest[k] = dest[k - 1];
        }
        dest[j] = job;
    }
}

void copia_seq(int *dest, int *src) {
    memcpy(dest, src, sizeof(int) * num_jobs);
}

void busca_local_rvnd(int *solucao, double *valor) {
    int vizinhancas[3] = {0, 1, 2}; // 0: swap, 1: insert, 2: inversao
    int usada[3];
    int temp[MAX_JOBS];

    while (1) {
        for (int i = 0; i < 3; i++) usada[i] = 0;
        int restantes = 3;
        int melhorou = 0;

        while (restantes > 0) {
            int idx;
            do {
                idx = rand() % 3;
            } while (usada[idx]);
            usada[idx] = 1;
            restantes--;

            copia_seq(temp, solucao);
            int i = rand() % num_jobs;
            int j = rand() % num_jobs;
            while (j == i) j = rand() % num_jobs;

            if (idx == 0) { // SWAP
                swap(&temp[i], &temp[j]);
            } else if (idx == 1) { // INSERT
                int job = temp[i];
                if (i < j) {
                    for (int k = i; k < j; k++) temp[k] = temp[k + 1];
                } else {
                    for (int k = i; k > j; k--) temp[k] = temp[k - 1];
                }
                temp[j] = job;
            } else if (idx == 2) { // INVERSÃO
                if (i > j) { int tmp = i; i = j; j = tmp; }
                while (i < j) {
                    swap(&temp[i], &temp[j]);
                    i++; j--;
                }
            }

            double novo_valor = calcular_makespan(temp);
            if (novo_valor < *valor) {
                copia_seq(solucao, temp);
                *valor = novo_valor;
                melhorou = 1;
                break; // volta para tentar todas vizinhanças novamente
            }
        }

        if (!melhorou) break; // nenhuma vizinhança melhorou
    }
}

// Função bee_colony modificada para retornar melhor makespan via ponteiro
void bee_colony(int n_bees, int max_iter, int limit, double *melhor_makespan_out) {
    int iteracoes_sem_melhora = 0;
    int intervalo_reinicializacao = 300;
    int food_sources[n_bees][MAX_JOBS];
    double makespans[n_bees];
    int trial[n_bees];
    int melhor_solucao[MAX_JOBS];
    double melhor_makespan = INT_MAX;

    for (int i = 0; i < n_bees; i++) {
        for (int j = 0; j < num_jobs; j++) food_sources[i][j] = j;
        for (int j = 0; j < num_jobs; j++) {
            int k = rand() % num_jobs;
            swap(&food_sources[i][j], &food_sources[i][k]);
        }
        makespans[i] = calcular_makespan(food_sources[i]);
        trial[i] = 0;
        if (makespans[i] < melhor_makespan) {
            melhor_makespan = makespans[i];
            copia_seq(melhor_solucao, food_sources[i]);
        }
    }

    for (int it = 0; it < max_iter; it++) {
        for (int i = 0; i < n_bees; i++) {
            int vizinho[MAX_JOBS];
            gerar_vizinho(food_sources[i], vizinho);
            double mk = calcular_makespan(vizinho);
            if (mk < makespans[i]) {
                copia_seq(food_sources[i], vizinho);
                makespans[i] = mk;
                trial[i] = 0;

                // Hibridização com busca local
                busca_local_rvnd(food_sources[i], &makespans[i]);

                if (makespans[i] < melhor_makespan) {
                    melhor_makespan = makespans[i];
                    copia_seq(melhor_solucao, food_sources[i]);
                    iteracoes_sem_melhora = 0; // zera contador
                } else {
                    iteracoes_sem_melhora++;
                }

            } else {
                trial[i]++;
            }
        }

        for (int i = 0; i < n_bees; i++) {
            if (trial[i] >= limit) {
                for (int j = 0; j < num_jobs; j++) food_sources[i][j] = melhor_solucao[j];
                int a = rand() % num_jobs;
                int b = rand() % num_jobs;
                while (b == a) b = rand() % num_jobs;
                swap(&food_sources[i][a], &food_sources[i][b]);
                makespans[i] = calcular_makespan(food_sources[i]);
                trial[i] = 0;
            }
        }

        if (iteracoes_sem_melhora >= intervalo_reinicializacao) {
            int qtd_reinicializar = n_bees / 2;
            for (int i = 0; i < qtd_reinicializar; i++) {
                for (int j = 0; j < num_jobs; j++) food_sources[i][j] = j;
                for (int j = 0; j < num_jobs; j++) {
                    int k = rand() % num_jobs;
                    swap(&food_sources[i][j], &food_sources[i][k]);
                }
                makespans[i] = calcular_makespan(food_sources[i]);
                trial[i] = 0;

                // opcional: aplica busca local nas novas soluções
                // busca_local_rvnd(food_sources[i], &makespans[i]);

                if (makespans[i] < melhor_makespan) {
                    melhor_makespan = makespans[i];
                    copia_seq(melhor_solucao, food_sources[i]);
                    iteracoes_sem_melhora = 0; // reset se melhorar
                }
            }
            printf(">>> Reinicialização executada na iteração %d\n", it);
            iteracoes_sem_melhora = 0; // zera mesmo que não tenha melhorado
        }
    }

    *melhor_makespan_out = melhor_makespan;
}

void ler_instancia(const char *nome_arquivo) {
    FILE *fp = fopen(nome_arquivo, "r");
    if (!fp) {
        perror("Erro ao abrir arquivo");
        exit(1);
    }
    fscanf(fp, "%d %d", &num_jobs, &num_machines);
    for (int i = 0; i < num_jobs; i++) {
        for (int j = 0; j < num_machines; j++) {
            fscanf(fp, "%d", &tempos[i][j]);
        }
    }
    fclose(fp);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Uso: %s instancia.txt\n", argv[0]);
        return 1;
    }

    ler_instancia(argv[1]);

    double melhores[REPETICOES];
    double tempos[REPETICOES];

    double melhor_makespan_global = INT_MAX;
    double tempo_do_melhor = 0.0;

    for (int i = 0; i < REPETICOES; i++) {
        srand(time(NULL) + i); // semente diferente a cada execução para variar resultados

        clock_t inicio = clock();
        double resultado;
        bee_colony(20, 5000, 100, &resultado);
        clock_t fim = clock();

        double tempo_execucao = (double)(fim - inicio) / CLOCKS_PER_SEC;

        melhores[i] = resultado;
        tempos[i] = tempo_execucao;

        if (resultado < melhor_makespan_global) {
            melhor_makespan_global = resultado;
            tempo_do_melhor = tempo_execucao;
        }

        printf("Execução %3d: Makespan = %.2f | Tempo = %.4f s\n", i + 1, resultado, tempo_execucao);
    }

    double soma_makespan = 0.0, soma_tempo = 0.0;
    for (int i = 0; i < REPETICOES; i++) {
        soma_makespan += melhores[i];
        soma_tempo += tempos[i];
    }

    printf("\n========== RESULTADOS FINAIS ==========\n");
    printf("Melhor makespan encontrado: %.2f\n", melhor_makespan_global);
    printf("Tempo do melhor resultado: %.4f segundos\n", tempo_do_melhor);
    printf("Média dos makespans: %.2f\n", soma_makespan / REPETICOES);
    printf("Média dos tempos: %.4f segundos\n", soma_tempo / REPETICOES);

    return 0;
}
