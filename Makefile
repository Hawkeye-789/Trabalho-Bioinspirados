# Nome do executável e do código fonte
TARGET = bee_colony_fssp
SRC = bee-colony-caprichado.c

# Arquivo de entrada (ajuste conforme necessário)
INPUT = fssp_instance_05.txt

# Compilador e flags
CC = gcc
CFLAGS = -O3 -fopenmp -Wall -lm

# Compilar e executar
run: $(TARGET)
	./$(TARGET) $(INPUT)

# Compilação
$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

# Limpeza
clean:
	rm -f $(TARGET)
