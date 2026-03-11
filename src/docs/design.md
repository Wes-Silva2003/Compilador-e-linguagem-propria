# Arquitetura do Compilador Cirius

Este documento descreve a arquitetura proposta para o compilador do Cirius, implementado em Python.
Ele detalha responsabilidades dos módulos, formatos de dados (AST/IR), interfaces entre fases e recomendações de implementação.

## Visão geral do pipeline

1. **Front-end**
   - **Lexer (src/lexer.py)**: Tokeniza o código-fonte (.cir) em uma sequência de tokens.
   - **Parser (src/parser.py)**: Constrói a AST a partir da gramática (utilizando Lark).
   - **Semantic Analyzer (src/semantic.py)**: Percorre a AST, valida tipos, escopos, declarações e constrói a tabela de símbolos.

2. **Middle-end**
   - **IR Generator (src/ir.py)**: Converte a AST em uma representação intermediária (Three Address Code - TAC).
   - **Optimizer (src/optimize.py)**: Implementa otimizações sobre o IR (constant folding, dead-code elimination, copy propagation).

3. **Back-end**
   - **Code Generator (src/codegen.py)**: Emite código C a partir do IR (transpilação para C).
   - **Runtime / VM (opcional)**: Se optar por gerar bytecode, aqui estaria a VM que interpreta o bytecode.

## Estrutura de diretórios proposta
```
cirius-compiler/
├─ src/
│  ├─ lexer.py            # Tokenização
│  ├─ parser.py           # Parsing + AST generation
│  ├─ ast.py              # Estruturas de dados para AST (opcional)
│  ├─ semantic.py         # Análise semântica e tabela de símbolos
│  ├─ ir.py               # Geração de IR (TAC)
│  ├─ optimize.py         # Otimizações sobre o IR
│  ├─ codegen.py          # Transpilador para C
│  └─ main.py             # CLI do compilador
├─ tests/
├─ docs/
│  ├─ grammar.ebnf
│  └─ design.md
├─ README.md
```

## Formato AST
- A AST pode ser representada como dicionários aninhados (JSON-like) para facilidade de debug e serialização.
- Exemplo de nó função:
```json
{
  "type": "function",
  "name": "main",
  "params": [],
  "body": {
    "type": "block",
    "body": [ ...statements... ]
  }
}
```

## Tabela de símbolos
- Deve armazenar: nome, tipo (se declarado), escopo, posição (linha/col), informações de função (params/retorno).
- Implementar como uma pilha de dicionários: ao entrar em um bloco/função, empilha novo escopo; ao sair, desempilha.

## IR - Three Address Code (TAC)
- Cada instrução TAC será representada como uma tupla: `(op, arg1, arg2, result)`.
- Exemplo: `t1 = a + b` -> `("add", "a", "b", "t1")`

## Otimizações sugeridas (ordem de implementação)
1. Constant Folding
2. Copy Propagation
3. Dead Code Elimination
4. (Opcional) Loop-Invariant Code Motion

## Ferramentas e integrações
- **Lark**: parser.  
- **pytest**: testes.  
- **GitHub Actions**: CI para rodar testes e lint.  
- **Graphviz**: opcional, para desenhar AST/IR.

## CLI proposta (src/main.py)
```bash
usage: python main.py <input.cir> -o <output.c>
```
- Etapas: ler código -> lex -> parse -> semantic -> ir -> optimize (opcional) -> codegen -> emitir arquivo `.c`

## Boas práticas de engenharia
- Branch por feature, PRs revisados, commits pequenos.  
- Testes unitários para cada fase (lexer, parser, semantic, ir, codegen).  
- Exemplo de teste integrado: compilar `tests/hello.cir` e comparar saída com esperado.

## Pontos de atenção / riscos
- Geração de código C válida: mapear corretamente tipos do Cirius para C.  
- Gerenciamento de strings e IO ao transpilar para C (usar `printf` e `scanf` adequadamente).  
- Tratamento de erros sintáticos e semânticos: mensagens claras para o usuário.

## Próximos passos
1. Implementar semantic.py (tabela de símbolos e validações).  
2. Construir ir.py (TAC generator) para estruturas de controle.  
3. Implementar codegen.py que emite C a partir do TAC.  
4. Adicionar otimizações e testes de regressão.
