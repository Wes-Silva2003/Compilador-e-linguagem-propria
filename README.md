# Compilador Cirius

**Centro Universitário Adventista de São Paulo (UNASP)**

**Curso:** Ciência da Computação

**Disciplina:** Projeto e Implementação de Compiladores

Este repositório contém o projeto final da disciplina, que consiste no design e implementação de um compilador completo para uma nova linguagem de programação, denominada **Cirius**.

O compilador é desenvolvido em Python e implementa o pipeline completo, desde a análise léxica do código-fonte Cirius até a **transpilação** (geração de código-alvo) para a linguagem C.

## 1\. A Linguagem Cirius

**Cirius** é uma fusão de **C** e **Sirius** (a estrela mais brilhante), refletindo a filosofia do projeto: uma linguagem com a clareza de uma estrela guia, mas com a base poderosa da linguagem C, que serve como seu alvo de transpilação.

Trata-se de uma linguagem imperativa, de alto nível, projetada com foco em simplicidade e didatismo.

### Recursos Implementados

A linguagem suporta os recursos essenciais definidos na proposta do projeto, incluindo:

  * **Tipos de Dados:** Suporte implícito para Números (inteiros e float), Strings e Booleanos.
  * **Estruturas de Controle:**
      * Condicionais: `if`, `elif`, `else`.
      * Laços de Repetição: `while` e `for` (com range `..`).
  * **Funções:** Definição (`func`) e chamada de funções com parâmetros e retorno.
  * **Operadores:** Aritméticos (`+`, `-`, `*`, `/`, `%`), Relacionais (`==`, `!=`, `>`, `<`, `>=`, `<=`) e Lógicos (`and`, `or`, `not`).
  * **Entrada e Saída:** Funções embutidas `print()` e `input()`.

### Exemplo de Código (`tests/cond.cir`)

```c
// Exemplo de condicional e I/O
func main() {
    idade = input();
    if idade < 18 {
        print("Menor de idade");
    } elif idade >= 18 and idade < 65 {
        print("Adulto");
    } else {
        print("Idoso");
    }
}
```

## 2\. Arquitetura do Compilador

O projeto segue o pipeline clássico de compilação, dividido em *front-end*, *middle-end* e *back-end*, conforme detalhado no [Documento de Design](./src/docs/design.md).

O orquestrador principal é o `src/main.py`, que gerencia o fluxo entre as fases.

### Front-End

1.  **Análise Léxica**

      * **Arquivo:** `src/lexer.py`
      * **Descrição:** Converte o código-fonte em uma sequência de *tokens* (e.g., `NUMBER`, `IDENT`, `IF`, `PLUS`) usando Expressões Regulares.

2.  **Análise Sintática (Parsing)**

      * **Arquivo:** `src/cirius_parser.py`
      * **Descrição:** Recebe os *tokens* e constrói uma Árvore Sintática Abstrata (AST), validando a estrutura do código com base na gramática da linguagem.
      * **Definição da AST:** `src/cirius_ast.py`

3.  **Análise Semântica**

      * **Arquivo:** `src/semantic.py`
      * **Descrição:** Percorre a AST para verificar regras lógicas, como declaração de variáveis, escopo e aridade (número de argumentos) de funções. Utiliza uma **Tabela de Símbolos** (`SymbolTable`) para gerenciar escopos.

### Middle-End

4.  **Geração de Código Intermediário (IR)**

      * **Arquivo:** `src/ir.py`
      * **Descrição:** Converte a AST validada em uma representação intermediária mais simples. A IR escolhida foi o **Código de Três Endereços (TAC - Three-Address Code)**, conforme sugerido na documentação de design.

5.  **Otimização de Código**

      * **Arquivo:** `src/optimizer.py` (arquivo renomeado de `optimize.py` para `optimizer.py` para consistência, mas usando `optimize.py` conforme seus arquivos)
      * **Descrição:** Aplica passadas de otimização sobre o Código Intermediário (TAC). A otimização implementada foi a **Eliminação de Código Morto (Dead Code Elimination)**, que remove instruções que calculam valores nunca utilizados.

### Back-End

O projeto implementa duas formas de *backend*:

6.  **Geração de Código Alvo (Transpilação)**

      * **Arquivo:** `src/codegen.py`
      * **Descrição:** Traduz (transpila) o Código Intermediário (IR) otimizado para a **linguagem C**, gerando um arquivo `.c` como saída.

7.  **Interpretador (Execução Direta)**

      * **Arquivo:** `src/interpreter.py`
      * **Descrição:** Como alternativa à compilação, o `main.py` pode usar este módulo para executar a AST (pós-análise semântica) diretamente, sem gerar código C.

## 3\. Documentação do Projeto

Conforme os requisitos, a documentação técnica está separada nos seguintes arquivos:

  * **Gramática (EBNF):** A definição formal da sintaxe da linguagem Cirius.
      * `src/docs/grammar.ebnf`
  * **Design do Compilador:** Detalhes da arquitetura, pipeline e decisões de design de cada fase.
      * `src/docs/design.md`

## 4\. Testes

O projeto inclui um conjunto de programas de teste escritos em Cirius para verificar a correção de cada fase do compilador e da linguagem.

  * **Localização:** `src/tests/`
  * **Exemplos:**
      * `hello.cir`: Teste básico de I/O.
      * `cond.cir`: Teste de condicionais `if/elif/else`.
      * `loop.cir`: Teste de laço `for`.

## 5\. Como Executar

O `src/main.py` é a interface de linha de comando para interagir com o compilador.

### Pré-requisitos

  * Python 3.8 ou superior.
  * (Opcional) Um compilador C (como `gcc`) para compilar a saída `.c` gerada.

### Modo 1: Compilar (Transpilar para C)

Este modo executa o pipeline completo (Lexer → Parser → Semântica → IR → Otimização → CodeGen) e gera um arquivo `.c`.

```bash
python src/main.py compile src/tests/loop.cir
```

### Modo 2: Executar (Interpretar)

Este modo executa o código Cirius diretamente usando o interpretador (Lexer → Parser → Semântica → Interpreter).

```bash
# Sintaxe: python -m src.main run <arquivo_entrada.cir>
python src/main.py run src/tests/hello.cir
```

## 6\. Autores

  * Estela Vidal
  * Mateus de Souza
  * Welinton Thiago

  * Wesley Santos




