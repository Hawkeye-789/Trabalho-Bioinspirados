#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <time.h>
#include <omp.h>
#include <math.h>

#define MAX_JOBS 1000
#define MAX_MACHINES 100

int num_jobs, num_machines;
int tempos[MAX_JOBS][MAX_MACHINES];

// ------------------- Utilitários --------------------
void swap(int *a, int *b) {
    int tmp = *a;
    *a = *b;
    *b = tmp;
}

void copia_seq(int *dest, int *src) {
    memcpy(dest, src, sizeof(int) * num_jobs);
}

void fisher_yates_shuffle(int *array, int n) {
    for (int i = n - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        swap(&array[i], &array[j]);
    }
}

// ------------------- Makespan --------------------
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

// ------------------- Busca Local --------------------
void busca_local(int *sequencia, double *melhor_mk) {
    int melhor[MAX_JOBS];
    copia_seq(melhor, sequencia);
    double mk_atual = *melhor_mk;

    for (int it = 0; it < 20; it++) {
        int vizinho[MAX_JOBS];
        copia_seq(vizinho, melhor);
        int i = rand() % num_jobs;
        int j = rand() % num_jobs;
        swap(&vizinho[i], &vizinho[j]);
        double mk = calcular_makespan(vizinho);
        if (mk < mk_atual) {
            copia_seq(melhor, vizinho);
            mk_atual = mk;
        }
    }
    copia_seq(sequencia, melhor);
    *melhor_mk = mk_atual;
}

// ------------------- NEH Heurística --------------------
int compara_NEH(const void *a, const void *b) {
    int ja = *(int *)a;
    int jb = *(int *)b;
    int sa = 0, sb = 0;
    for (int m = 0; m < num_machines; m++) {
        sa += tempos[ja][m];
        sb += tempos[jb][m];
    }
    return sb - sa;
}

void gerar_NEH(int *seq) {
    memset(seq, -1, sizeof(int) * MAX_JOBS);
    int ordem[MAX_JOBS];
    for (int i = 0; i < num_jobs; i++) ordem[i] = i;
    qsort(ordem, num_jobs, sizeof(int), compara_NEH);

    int temp_seq[MAX_JOBS];
    temp_seq[0] = ordem[0];
    for (int n = 1; n < num_jobs; n++) {
        double menor = INT_MAX;
        for (int i = 0; i <= n; i++) {
            int temp[MAX_JOBS];
            for (int j = 0; j < i; j++) temp[j] = temp_seq[j];
            temp[i] = ordem[n];
            for (int j = i; j < n; j++) temp[j + 1] = temp_seq[j];
            double mk = calcular_makespan(temp);
            if (mk < menor) {
                menor = mk;
                memcpy(seq, temp, sizeof(int) * (n + 1));
            }
        }
        memcpy(temp_seq, seq, sizeof(int) * (n + 1));
    }
}

// ------------------- Vizinho + Diversificação --------------------
void gerar_vizinho(int *orig, int *dest, int intensidade) {
    copia_seq(dest, orig);
    for (int it = 0; it < intensidade; it++) {
        int i = rand() % num_jobs;
        int j = rand() % num_jobs;
        swap(&dest[i], &dest[j]);
    }
}

// ------------------- Bee Colony Principal --------------------
void bee_colony(int n_bees, int max_iter, int limit) {
    int food_sources[n_bees][MAX_JOBS];
    double makespans[n_bees];
    int trial[n_bees];
    int melhor_solucao[MAX_JOBS];
    memset(melhor_solucao, -1, sizeof(melhor_solucao));
    double melhor_makespan = INT_MAX;

    #pragma omp parallel for
    for (int i = 0; i < n_bees; i++) {
        gerar_NEH(food_sources[i]);
        fisher_yates_shuffle(food_sources[i], num_jobs);
        makespans[i] = calcular_makespan(food_sources[i]);
        trial[i] = 0;
        #pragma omp critical
        {
            if (makespans[i] < melhor_makespan) {
                melhor_makespan = makespans[i];
                copia_seq(melhor_solucao, food_sources[i]);
            }
        }
    }

    for (int it = 0; it < max_iter; it++) {
        #pragma omp parallel for
        for (int i = 0; i < n_bees; i++) {
            int vizinho[MAX_JOBS];
            gerar_vizinho(food_sources[i], vizinho, 1);
            double mk = calcular_makespan(vizinho);
            if (mk < makespans[i]) {
                copia_seq(food_sources[i], vizinho);
                makespans[i] = mk;
                trial[i] = 0;
                #pragma omp critical
                {
                    if (mk < melhor_makespan) {
                        melhor_makespan = mk;
                        copia_seq(melhor_solucao, vizinho);
                    }
                }
            } else {
                trial[i]++;
            }
        }

        #pragma omp parallel for
        for (int i = 0; i < n_bees; i++) {
            if (trial[i] >= limit) {
                gerar_vizinho(melhor_solucao, food_sources[i], 5);
                makespans[i] = calcular_makespan(food_sources[i]);
                trial[i] = 0;
            }
        }

        for (int k = 0; k < 2; k++) {
            int best_idx = -1;
            double best_mk = INT_MAX;
            for (int i = 0; i < n_bees; i++) {
                if (makespans[i] < best_mk) {
                    best_mk = makespans[i];
                    best_idx = i;
                }
            }
            busca_local(food_sources[best_idx], &makespans[best_idx]);
            if (makespans[best_idx] < melhor_makespan) {
                melhor_makespan = makespans[best_idx];
                copia_seq(melhor_solucao, food_sources[best_idx]);
            }
            makespans[best_idx] = INT_MAX;
        }
    }

    printf("Melhor makespan: %.2f\n", melhor_makespan);
    printf("Melhor sequência: ");
    for (int i = 0; i < num_jobs; i++) printf("%d ", melhor_solucao[i]);
    printf("\n");
}

// ------------------- Entrada --------------------
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
    srand(time(NULL));
    ler_instancia(argv[1]);
    bee_colony(20, 5000, 100);
    return 0;
}
