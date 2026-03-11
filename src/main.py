#  cirius_main.py - Orquestrador do Compilador/Interpretador Cirius

# Este arquivo é o “cérebro” do projeto. Ele conecta todas as etapas:
#
#   Código-fonte .cir
#       ↓
#   Lexer → Parser → Análise Semântica → IR → Otimização → Código C
#       ↓
#   Execução direta (modo interpretador)
#
# Ele também fornece a interface de linha de comando (CLI) para:
#   Compilar: python cirius_main.py compile arquivo.cir
#   Executar: python cirius_main.py run arquivo.cir

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from cirius_lexer import Lexer             # Analisador Léxico
import cirius_parser                       # Analisador Sintático (renomeado corretamente)
from cirius_ast import Node, Program       # Estrutura da AST
from semantic import SemanticAnalyzer      # Analisador Semântico
from cirius_ir import IRGenerator          # Gerador de Código Intermediário (IR)
from optimize import Optimizer             # Otimizador do IR
from codegen import CodeGenerator          # Gerador de Código C
from interpreter import Interpreter        # Interpretador da AST


def ensure_dir(path: str):
    """Garante que o diretório exista (cria se não existir)."""
    Path(path).mkdir(parents=True, exist_ok=True)

def write_file(path: str, contents: str):
    """Salva texto em um arquivo, criando diretórios se necessário."""
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        f.write(contents)

def safe_json_dump(obj, path: str):
    """Salva objetos Python (AST, IR, etc.) em JSON de forma segura."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, 
                  default=lambda o: o.to_dict() if isinstance(o, Node) else o.__dict__)

def normalize_ir(ir_list: List[Any]) -> List[Dict[str, Any]]:
    """Converte o IR em formato JSON serializável."""
    normalized = []
    for instr in ir_list:
        if instr is None:
            continue
        if isinstance(instr, dict):
            normalized.append(instr)
        else:
            d = {"op": getattr(instr, "op", None)}
            for attr in ["dest", "arg1", "arg2"]:
                if hasattr(instr, attr):
                    val = getattr(instr, attr)
                    if val is not None:
                        d[attr] = val
            normalized.append(d)
    return normalized


def compile_pipeline(source: str, output_path: str, verbose=False):
    """
    Executa todo o pipeline de compilação:
    Lexer → Parser → Semântica → IR → Otimização → Geração de Código C
    """
    if verbose:
        print(f"\n[Compilando] Arquivo fonte → {output_path}")

    # Lexer — converte código-fonte em tokens
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    if verbose:
        print(f"[Lexer] {len(tokens)} tokens gerados com sucesso.")

    # Parser — transforma tokens em AST
    parser = cirius_parser.Parser(tokens)
    ast = parser.parse()
    if verbose:
        print("[Parser] AST construída corretamente.")

    # Análise Semântica — verifica escopos e tipos
    sema = SemanticAnalyzer()
    try:
        sema.analyze(ast)
        if verbose:
            print("[Semântica] Nenhum erro encontrado.")
    except Exception as e:
        print(f"[ERRO Semântico] {e}")
        return

    # IR — gera código intermediário (Three Address Code)
    irgen = IRGenerator()
    ir_code = normalize_ir(irgen.generate(ast))
    if verbose:
        print(f"[IR] {len(ir_code)} instruções geradas.")

    # Otimização — remove código redundante ou inútil
    optimizer = Optimizer()
    ir_optimized = optimizer.optimize(ir_code)

    # Geração de Código C — cria o arquivo .c final
    cg = CodeGenerator()
    c_code = cg.generate(ir_optimized)
    write_file(output_path, c_code)
    if verbose:
        print(f"[CodeGen] Código C gerado com sucesso em: {output_path}")
    print(f"[ Sucesso] Compilado → {output_path}")


def run_pipeline(source: str, verbose=False):
    """
    Executa o código Cirius diretamente, sem gerar C.
    Ideal para testes rápidos e depuração.
    """
    if verbose:
        print(f"\n[Executando] Iniciando modo interpretador...")

    # Lexer
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    if verbose:
        print(f"[Lexer] {len(tokens)} tokens gerados.")

    # Parser
    parser = cirius_parser.Parser(tokens)
    ast = parser.parse()
    if verbose:
        print("[Parser] AST construída com sucesso.")

    # Semântica
    sema = SemanticAnalyzer()
    try:
        sema.analyze(ast)
        if verbose:
            print("[Semântica] Nenhum erro semântico encontrado.")
    except Exception as e:
        print(f"[ERRO Semântico] {e}")
        return

    # Interpretador
    if verbose:
        print("[Interpretador] Iniciando execução da AST...")
    interpreter = Interpreter()
    interpreter.interpret(ast)
    if verbose:
        print("[Interpretador] Execução concluída com sucesso!")


def main():
    parser = argparse.ArgumentParser(description="🧠 Compilador/Interpretador da Linguagem Cirius")
    parser.add_argument("--verbose", action="store_true", help="Exibe logs detalhados do processo.")
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Comando a executar")

    # Comando de compilação
    parser_compile = subparsers.add_parser("compile", help="Compila um arquivo .cir para .c")
    parser_compile.add_argument("input_path", help="Caminho do arquivo .cir")
    parser_compile.add_argument("-o", "--output", help="Arquivo .c de saída (opcional)")

    # Comando de execução direta
    parser_run = subparsers.add_parser("run", help="Executa (interpreta) um arquivo .cir diretamente")
    parser_run.add_argument("input_path", help="Arquivo .cir para executar")

    args = parser.parse_args()

    # Lê o código-fonte informado
    source_code = Path(args.input_path).read_text(encoding="utf-8")

    # Decide o modo de operação
    if args.command == "compile":
        output_path = args.output or str(Path(args.input_path).with_suffix(".c"))
        compile_pipeline(source_code, output_path, args.verbose)
    elif args.command == "run":
        run_pipeline(source_code, args.verbose)

if __name__ == "__main__":
    main()
