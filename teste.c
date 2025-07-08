#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>


#define TAM_POP 500
#define NUM_GERACOES 500
#define TAXA_MUTACAO 0.2
#define TORNEIO 3
#define EXECUCOES 200

int num_jobs, num_maquinas;
int **tempo_processamento;

void embaralhar(int *vet, int tam) {
    for (int i = tam - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int tmp = vet[i];
        vet[i] = vet[j];
        vet[j] = tmp;
    }
}

int calcular_makespan(int *ordem) {
    int **fim = malloc(num_jobs * sizeof(int*));
    for (int i = 0; i < num_jobs; i++)
        fim[i] = calloc(num_maquinas, sizeof(int));

    for (int i = 0; i < num_jobs; i++) {
        int job = ordem[i];
        for (int m = 0; m < num_maquinas; m++) {
            if (i == 0 && m == 0)
                fim[i][m] = tempo_processamento[job][m];
            else if (i == 0)
                fim[i][m] = fim[i][m-1] + tempo_processamento[job][m];
            else if (m == 0)
                fim[i][m] = fim[i-1][m] + tempo_processamento[job][m];
            else
                fim[i][m] = (fim[i-1][m] > fim[i][m-1] ? fim[i-1][m] : fim[i][m-1]) + tempo_processamento[job][m];
        }
    }

    int resultado = fim[num_jobs - 1][num_maquinas - 1];
    for (int i = 0; i < num_jobs; i++) free(fim[i]);
    free(fim);
    return resultado;
}

void copiar(int *dest, int *src) {
    for (int i = 0; i < num_jobs; i++) dest[i] = src[i];
}

void mutacao_swap(int *ind) {
    if ((rand() / (double) RAND_MAX) < TAXA_MUTACAO) {
        int i = rand() % num_jobs;
        int j = rand() % num_jobs;
        int tmp = ind[i];
        ind[i] = ind[j];
        ind[j] = tmp;
    }
}

void crossover_cx(int *pai1, int *pai2, int *filho) {
    int tamanho = num_jobs;
    int *usado = calloc(tamanho, sizeof(int));
    int pos = 0;

    while (!usado[pos]) {
        filho[pos] = pai1[pos];
        usado[pos] = 1;
        int val = pai2[pos];
        pos = 0;
        while (pai1[pos] != val) pos++;
    }

    for (int i = 0; i < tamanho; i++)
        if (!usado[i]) filho[i] = pai2[i];

    free(usado);
}

int torneio(int **pop, int *fitness) {
    int melhor = rand() % TAM_POP;
    for (int i = 1; i < TORNEIO; i++) {
        int x = rand() % TAM_POP;
        if (fitness[x] < fitness[melhor]) melhor = x;
    }
    return melhor;
}

int algoritmo_genetico_fssp() {
    const int ELITISMO_K = 2;
    int **pop = malloc(TAM_POP * sizeof(int*));
    int *fitness = malloc(TAM_POP * sizeof(int));
    for (int i = 0; i < TAM_POP; i++) {
        pop[i] = malloc(num_jobs * sizeof(int));
        for (int j = 0; j < num_jobs; j++) pop[i][j] = j;
        embaralhar(pop[i], num_jobs);
    }

    for (int g = 0; g < NUM_GERACOES; g++) {
        for (int i = 0; i < TAM_POP; i++)
            fitness[i] = calcular_makespan(pop[i]);

        int **nova_pop = malloc(TAM_POP * sizeof(int*));
        for (int i = 0; i < ELITISMO_K; i++) {
            nova_pop[i] = malloc(num_jobs * sizeof(int));
            int melhor = 0;
            for (int j = 1; j < TAM_POP; j++)
                if (fitness[j] < fitness[melhor]) melhor = j;
            copiar(nova_pop[i], pop[melhor]);
            fitness[melhor] = 100000000;
        }

        int index_nova = ELITISMO_K;
        while (index_nova < TAM_POP) {
            int pai1 = torneio(pop, fitness);
            int pai2 = torneio(pop, fitness);
            nova_pop[index_nova] = malloc(num_jobs * sizeof(int));
            crossover_cx(pop[pai1], pop[pai2], nova_pop[index_nova]);
            mutacao_swap(nova_pop[index_nova]);
            index_nova++;
        }

        for (int i = 0; i < TAM_POP; i++) free(pop[i]);
        free(pop);
        pop = nova_pop;
    }

    int melhor = calcular_makespan(pop[0]);
    for (int i = 1; i < TAM_POP; i++) {
        int val = calcular_makespan(pop[i]);
        if (val < melhor) melhor = val;
    }

    for (int i = 0; i < TAM_POP; i++) free(pop[i]);
    free(pop); free(fitness);
    return melhor;
}

void ler_arquivo(const char *nome) {
    FILE *f = fopen(nome, "r");
    if (!f) {
        perror("Erro ao abrir arquivo");
        exit(1);
    }

    fscanf(f, "%d %d", &num_jobs, &num_maquinas);

    tempo_processamento = malloc(num_jobs * sizeof(int*));
    for (int i = 0; i < num_jobs; i++) {
        tempo_processamento[i] = malloc(num_maquinas * sizeof(int));
        for (int j = 0; j < num_maquinas; j++)
            fscanf(f, "%d", &tempo_processamento[i][j]);
    }

    fclose(f);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Uso: %s arquivo_instancia.txt\n", argv[0]);
        return 1;
    }

    srand(time(NULL));
    ler_arquivo(argv[1]);

    int melhor_global = 100000000;
    double soma = 0;
    int resultados[EXECUCOES];

    for (int i = 0; i < EXECUCOES; i++) {
        int resultado = algoritmo_genetico_fssp();
        resultados[i] = resultado;

        if (resultado < melhor_global)
            melhor_global = resultado;

        soma += resultado;
    }

    double media = soma / EXECUCOES;

    // Cálculo do desvio padrão
    double soma_dif_quad = 0;
    for (int i = 0; i < EXECUCOES; i++) {
        double diff = resultados[i] - media;
        soma_dif_quad += diff * diff;
    }
    double desvio_padrao = sqrt(soma_dif_quad / EXECUCOES);

    printf("Melhor makespan encontrado: %d\n", melhor_global);
    printf("Média dos makespans: %.2f\n", media);
    printf("Desvio padrão: %.2f\n", desvio_padrao);

    for (int i = 0; i < num_jobs; i++) free(tempo_processamento[i]);
    free(tempo_processamento);

    return 0;
}
