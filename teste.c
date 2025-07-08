#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include <limits.h>

#define TAM_POP 100
#define NUM_GERACOES 200
#define TAXA_MUTACAO 0.1
#define ELITISMO_K 2
#define TAM_TORNEIO 4
#define CLONALG_GERACOES 50
#define CLONALG_TAM_POP 50
#define CLONALG_TAXA_MUT 0.2
#define CLONALG_QTD_CLONES 7
#define NUM_EXECUCOES 200
#define MAX_JOBS 100
#define MAX_MAQS 20

int num_jobs, num_maquinas;
int tempo_proc[MAX_JOBS][MAX_MAQS];

void ler_instancia(const char *nome_arquivo) {
    FILE *fp = fopen(nome_arquivo, "r");
    if (!fp) {
        perror("Erro ao abrir arquivo");
        exit(1);
    }
    fscanf(fp, "%d %d", &num_jobs, &num_maquinas);
    for (int i = 0; i < num_jobs; i++)
        for (int j = 0; j < num_maquinas; j++)
            fscanf(fp, "%d", &tempo_proc[i][j]);
    fclose(fp);
}

int calcular_makespan(int *ordem) {
    int tempo_fim[MAX_JOBS][MAX_MAQS];
    for (int i = 0; i < num_jobs; i++) {
        int job = ordem[i];
        for (int m = 0; m < num_maquinas; m++) {
            if (i == 0 && m == 0)
                tempo_fim[i][m] = tempo_proc[job][m];
            else if (i == 0)
                tempo_fim[i][m] = tempo_fim[i][m - 1] + tempo_proc[job][m];
            else if (m == 0)
                tempo_fim[i][m] = tempo_fim[i - 1][m] + tempo_proc[job][m];
            else {
                int maior = tempo_fim[i - 1][m] > tempo_fim[i][m - 1] ? tempo_fim[i - 1][m] : tempo_fim[i][m - 1];
                tempo_fim[i][m] = maior + tempo_proc[job][m];
            }
        }
    }
    return tempo_fim[num_jobs - 1][num_maquinas - 1];
}

void copiar(int *dest, int *orig) {
    memcpy(dest, orig, num_jobs * sizeof(int));
}

void shuffle(int *vetor) {
    for (int i = num_jobs - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int tmp = vetor[i];
        vetor[i] = vetor[j];
        vetor[j] = tmp;
    }
}

void mutacao(int *ind, double taxa) {
    if ((double)rand() / RAND_MAX < taxa) {
        int i = rand() % num_jobs;
        int j = rand() % num_jobs;
        int tmp = ind[i];
        ind[i] = ind[j];
        ind[j] = tmp;
    }
}

void crossover_cx(int *pai1, int *pai2, int *filho) {
    int ciclo[MAX_JOBS] = {0};
    int start = 0;
    while (!ciclo[start]) {
        ciclo[start] = 1;
        start = -1;
        for (int i = 0; i < num_jobs; i++) {
            if (pai1[i] == pai2[start]) {
                start = i;
                break;
            }
        }
    }
    for (int i = 0; i < num_jobs; i++)
        filho[i] = ciclo[i] ? pai1[i] : pai2[i];
}

void selecionar_pais(int pop[TAM_POP][MAX_JOBS], int *pai1, int *pai2, int *fits) {
    int melhor1 = -1, melhor2 = -1, best1 = -1, best2 = -1;
    for (int i = 0; i < TAM_TORNEIO; i++) {
        int r = rand() % TAM_POP;
        if (melhor1 == -1 || fits[r] < best1) {
            melhor1 = r;
            best1 = fits[r];
        }
        r = rand() % TAM_POP;
        if (melhor2 == -1 || fits[r] < best2) {
            melhor2 = r;
            best2 = fits[r];
        }
    }
    copiar(pai1, pop[melhor1]);
    copiar(pai2, pop[melhor2]);
}

void executar_algoritmo(const char *arquivo) {
    ler_instancia(arquivo);
    int pop[TAM_POP][MAX_JOBS], nova_pop[TAM_POP][MAX_JOBS], fits[TAM_POP];

    for (int exec = 0; exec < NUM_EXECUCOES; exec++) {
        for (int i = 0; i < TAM_POP; i++) {
            for (int j = 0; j < num_jobs; j++) pop[i][i] = j;
            shuffle(pop[i]);
        }

        for (int g = 0; g < NUM_GERACOES; g++) {
            for (int i = 0; i < TAM_POP; i++)
                fits[i] = calcular_makespan(pop[i]);

            for (int i = 0; i < ELITISMO_K; i++) {
                int best = 0;
                for (int j = 1; j < TAM_POP; j++)
                    if (fits[j] < fits[best]) best = j;
                copiar(nova_pop[i], pop[best]);
                fits[best] = INT_MAX;
            }

            while (ELITISMO_K < TAM_POP) {
                int pai1[MAX_JOBS], pai2[MAX_JOBS], filho[MAX_JOBS];
                selecionar_pais(pop, pai1, pai2, fits);
                crossover_cx(pai1, pai2, filho);
                mutacao(filho, TAXA_MUTACAO);
                copiar(nova_pop[ELITISMO_K++], filho);
            }

            for (int i = 0; i < TAM_POP; i++)
                copiar(pop[i], nova_pop[i]);
        }

        // CLONALG
        int pool[CLONALG_TAM_POP][MAX_JOBS];
        for (int i = 0; i < CLONALG_TAM_POP; i++)
            copiar(pool[i], pop[i]);

        for (int g = 0; g < CLONALG_GERACOES; g++) {
            int clones[CLONALG_TAM_POP * CLONALG_QTD_CLONES][MAX_JOBS];
            int total = 0;
            for (int i = 0; i < CLONALG_TAM_POP; i++) {
                for (int c = 0; c < CLONALG_QTD_CLONES; c++) {
                    copiar(clones[total], pool[i]);
                    mutacao(clones[total], CLONALG_TAXA_MUT);
                    total++;
                }
            }
            for (int i = 0; i < total; i++) {
                int idx = rand() % CLONALG_TAM_POP;
                if (calcular_makespan(clones[i]) < calcular_makespan(pool[idx]))
                    copiar(pool[idx], clones[i]);
            }
        }

        // Resultado da execução
        int melhor_makespan = INT_MAX;
        for (int i = 0; i < CLONALG_TAM_POP; i++) {
            int mk = calcular_makespan(pool[i]);
            if (mk < melhor_makespan) melhor_makespan = mk;
        }
        printf("Execucao %d: %d\n", exec + 1, melhor_makespan);
    }
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Uso: %s <instancia_fssp>\n", argv[0]);
        return 1;
    }
    srand(time(NULL));#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <limits.h>
#include <math.h>

#define TAMANHO_POPULACAO 100
#define NUM_GERACOES 200
#define TAXA_MUTACAO 0.1
#define ELITISMO_K 2
#define TAMANHO_TORNEIO 4

#define CLONALG_GERACOES 50
#define CLONALG_TAM_POP 50
#define CLONALG_TAXA_MUTACAO 0.2
#define CLONALG_QTD_CLONES 7

#define MAX_JOBS 100
#define MAX_MAQS 100

int tempo[MAX_JOBS][MAX_MAQS];
int num_jobs, num_maquinas;

typedef struct {
    int ordem[MAX_JOBS];
    int makespan;
} Individuo;

int calcular_makespan(int ordem[]) {
    int tempo_fim[MAX_JOBS][MAX_MAQS] = {0};

    for (int i = 0; i < num_jobs; i++) {
        int job = ordem[i];
        for (int m = 0; m < num_maquinas; m++) {
            if (i == 0 && m == 0)
                tempo_fim[i][m] = tempo[job][m];
            else if (i == 0)
                tempo_fim[i][m] = tempo_fim[i][m-1] + tempo[job][m];
            else if (m == 0)
                tempo_fim[i][m] = tempo_fim[i-1][m] + tempo[job][m];
            else
                tempo_fim[i][m] = fmax(tempo_fim[i-1][m], tempo_fim[i][m-1]) + tempo[job][m];
        }
    }

    return tempo_fim[num_jobs-1][num_maquinas-1];
}

void copiar(Individuo *dest, Individuo src) {
    memcpy(dest->ordem, src.ordem, sizeof(int) * num_jobs);
    dest->makespan = src.makespan;
}

void shuffle(int *vetor, int n) {
    for (int i = n-1; i > 0; i--) {
        int j = rand() % (i+1);
        int tmp = vetor[i];
        vetor[i] = vetor[j];
        vetor[j] = tmp;
    }
}

Individuo criar_individuo() {
    Individuo ind;
    for (int i = 0; i < num_jobs; i++) ind.ordem[i] = i;
    shuffle(ind.ordem, num_jobs);
    ind.makespan = calcular_makespan(ind.ordem);
    return ind;
}

void mutacao(Individuo *ind, int n, double taxa) {
    if ((double)rand() / RAND_MAX < taxa) {
        int i = rand() % n;
        int j = rand() % n;
        int tmp = ind->ordem[i];
        ind->ordem[i] = ind->ordem[j];
        ind->ordem[j] = tmp;
        ind->makespan = calcular_makespan(ind->ordem);
    }
}

Individuo crossover(Individuo p1, Individuo p2, int n) {
    Individuo filho;
    int usado[MAX_JOBS] = {0};

    int pos = 0;
    while (!usado[pos]) {
        int val = p1.ordem[pos];
        filho.ordem[pos] = val;
        usado[pos] = 1;
        for (int i = 0; i < n; i++) {
            if (p1.ordem[i] == p2.ordem[pos]) {
                pos = i;
                break;
            }
        }
    }

    for (int i = 0; i < n; i++)
        if (!usado[i])
            filho.ordem[i] = p2.ordem[i];

    filho.makespan = calcular_makespan(filho.ordem);
    return filho;
}

Individuo torneio(Individuo pop[], int tamanho, int k) {
    int melhor = rand() % tamanho;
    for (int i = 1; i < k; i++) {
        int candidato = rand() % tamanho;
        if (pop[candidato].makespan < pop[melhor].makespan)
            melhor = candidato;
    }
    return pop[melhor];
}

void ordenar(Individuo pop[], int n) {
    for (int i = 0; i < n-1; i++)
        for (int j = i+1; j < n; j++)
            if (pop[j].makespan < pop[i].makespan) {
                Individuo tmp = pop[i];
                pop[i] = pop[j];
                pop[j] = tmp;
            }
}

void executar_algoritmo(Individuo *melhor_final) {
    Individuo pop[TAMANHO_POPULACAO];
    Individuo nova_pop[TAMANHO_POPULACAO];

    for (int i = 0; i < TAMANHO_POPULACAO; i++)
        pop[i] = criar_individuo();

    for (int g = 0; g < NUM_GERACOES; g++) {
        ordenar(pop, TAMANHO_POPULACAO);
        for (int i = 0; i < ELITISMO_K; i++)
            copiar(&nova_pop[i], pop[i]);

        int idx_novo = ELITISMO_K;
        for (int i = 0; i < TAMANHO_POPULACAO - ELITISMO_K; i++) {
            Individuo pai1 = torneio(pop, TAMANHO_POPULACAO, TAMANHO_TORNEIO);
            Individuo pai2 = torneio(pop, TAMANHO_POPULACAO, TAMANHO_TORNEIO);
            Individuo filho = crossover(pai1, pai2, num_jobs);
            mutacao(&filho, num_jobs, TAXA_MUTACAO);
            copiar(&nova_pop[idx_novo], filho);
            idx_novo++;
        }

        memcpy(pop, nova_pop, sizeof(Individuo) * TAMANHO_POPULACAO);
    }

    // CLONALG
    Individuo pool[CLONALG_TAM_POP * (CLONALG_QTD_CLONES + 1)];
    for (int i = 0; i < CLONALG_TAM_POP; i++)
        pool[i] = pop[i];

    for (int g = 0; g < CLONALG_GERACOES; g++) {
        ordenar(pool, CLONALG_TAM_POP);
        int idx = CLONALG_TAM_POP;
        for (int i = 0; i < CLONALG_TAM_POP; i++) {
            for (int c = 0; c < CLONALG_QTD_CLONES; c++) {
                Individuo clone = pool[i];
                mutacao(&clone, num_jobs, CLONALG_TAXA_MUTACAO);
                pool[idx++] = clone;
            }
        }
        ordenar(pool, idx);
    }

    copiar(melhor_final, pool[0]);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Uso: %s fssp_instance_XX.txt\n", argv[0]);
        return 1;
    }

    FILE *fp = fopen(argv[1], "r");
    if (!fp) {
        perror("Erro ao abrir arquivo");
        return 1;
    }

    fscanf(fp, "%d %d", &num_jobs, &num_maquinas);
    for (int i = 0; i < num_jobs; i++)
        for (int j = 0; j < num_maquinas; j++)
            fscanf(fp, "%d", &tempo[i][j]);
    fclose(fp);

    srand(time(NULL));

    Individuo melhor;
    clock_t inicio = clock();

    executar_algoritmo(&melhor);

    clock_t fim = clock();
    double tempo_execucao = (double)(fim - inicio) / CLOCKS_PER_SEC;

    printf("Melhor makespan: %d\n", melhor.makespan);
    printf("Ordem: ");
    for (int i = 0; i < num_jobs; i++) printf("%d ", melhor.ordem[i]);
    printf("\nTempo de execução: %.4f segundos\n", tempo_execucao);

    return 0;
}

    executar_algoritmo(argv[1]);
    return 0;
}
