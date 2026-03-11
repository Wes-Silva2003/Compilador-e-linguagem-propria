# Gerador de Código C para o compilador Cirius
#
# Recebe uma lista de instruções IR (cada instrução é um dict
# com chaves como "op", "dest", "arg1", "arg2") e produz um
# arquivo-fonte em C que tenta representar o comportamento do IR.
#
# Observações práticas:
# - Evita redeclaração: cada variável é declarada apenas uma vez.
# - Tradução simples de operadores aritméticos e comparadores.
# - Gera printf/scanf básicos; faz distinção simples entre strings
#   (quando o argumento é uma string entre aspas) e números.
# - Não tenta ser um compilador C perfeito — gera código legível e
#   compilável para a maioria dos exemplos do projeto.

from typing import List, Dict, Any


class CodeGenerator:
    def __init__(self):
        self.output_lines: List[str] = []
        self.indent_level = 0
        self.declared_vars = set()   # evita redeclarações
        self.current_function = None
        self.function_has_return = {}  # marca se função usa RETURN (para gerar return 0 se necessário)

    def emit(self, line: str = ""):
        """Adiciona uma linha ao output com indentação."""
        indent = "    " * self.indent_level
        self.output_lines.append(f"{indent}{line}")

    def indent(self):
        self.indent_level += 1

    def dedent(self):
        self.indent_level = max(0, self.indent_level - 1)

    def reset(self):
        self.output_lines = []
        self.indent_level = 0
        self.declared_vars.clear()
        self.current_function = None
        self.function_has_return.clear()


    def generate(self, ir: List[Dict[str, Any]]) -> str:
        """Gera o código-fonte C a partir do IR (lista de dicionários)."""
        self.reset()
        # includes básicos
        self.emit('#include <stdio.h>')
        self.emit('#include <stdlib.h>')
        self.emit('')
        # percorre instruções
        for instr in ir:
            # suporte a possíveis None ou instruções vazias
            if instr is None:
                continue
            self.gen_instruction(instr)
        # se não geramos função main com retorno, adicionamos um main vazio? Não — assumimos que existe func main.
        return "\n".join(self.output_lines)


    def fmt_operand(self, op):
        """
        Retorna a representação em C de um operando.
        - Se op for um inteiro ou float, retorna literal.
        - Se for uma string já entre aspas => mantêm como string.
        - Caso contrário, supõe-se ser um nome de variável/temporária.
        """
        if op is None:
            return "0"
        if isinstance(op, (int, float)):
            return str(op)
        # Se veio algo como 't1' ou 'x' -> usar tal qual
        # Se for string com aspas (por exemplo: '"Olá"') mantenha
        if isinstance(op, str):
            # já está entre aspas?
            if len(op) >= 2 and ((op[0] == '"' and op[-1] == '"') or (op[0] == "'" and op[-1] == "'")):
                return op
            # numeric-looking string? tenta deixar como está
            return op
        return str(op)

    def is_string_literal(self, op):
        return isinstance(op, str) and len(op) >= 2 and ((op[0] == '"' and op[-1] == '"') or (op[0] == "'" and op[-1] == "'"))


    def op_to_symbol(self, op: str) -> str:
        mapping = {
            "ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/", "MOD": "%",
            "GT": ">", "LT": "<", "GE": ">=", "LE": "<=", "EQ": "==", "NE": "!=",
        }
        return mapping.get(op, op)


    def gen_instruction(self, instr: Dict[str, Any]):
        op = instr.get("op")
        dest = instr.get("dest")
        arg1 = instr.get("arg1")
        arg2 = instr.get("arg2")

        # Normaliza nomes que podem vir como objetos (garantir str)
        if isinstance(dest, (int, float)):
            dest = str(dest)
        if isinstance(arg1, (int, float)):
            arg1 = arg1
        if isinstance(arg2, (int, float)):
            arg2 = arg2

        # Funções
        if op == "FUNC_BEGIN":
            # Início de função. Geramos void <name>() por simplicidade.
            self.current_function = dest
            self.function_has_return.setdefault(dest, False)
            self.emit(f"void {dest}(void) " + "{")
            self.indent()
            return

        if op == "FUNC_END":
            # Se não teve return explícito e a função é main, adiciona return 0 (opcional)
            if self.current_function:
                if self.current_function == "main":
                    # se não teve return, garantir exit 0
                    if not self.function_has_return.get(self.current_function, False):
                        self.emit("return;")
                # reset contextual
            self.dedent()
            self.emit("}")
            self.emit("")  # linha em branco entre funções
            self.current_function = None
            return

        # Labels e saltos
        if op == "LABEL":
            # remove indentação para labels (estilo C)
            self.emit(f"{dest}: ;")
            return

        if op == "GOTO":
            self.emit(f"goto {dest};")
            return

        if op == "IF_FALSE_GOTO":
            # arg1 é condição (pode ser temporário); dest é label
            cond = self.fmt_operand(arg1)
            # se cond é temporário contendo 0/1, podemos inverter com !
            self.emit(f"if (!({cond})) goto {dest};")
            return

        # Entrada / Saída
        if op == "PRINT":
            # arg1 pode ser literal string ou variável/expressão
            if self.is_string_literal(arg1):
                # imprime string diretamente
                s = arg1
                # remove trailing newline if user included? mantemos como dado
                self.emit(f'printf("%s\\n", {s});')
            else:
                # tratamos como número/variável; usar %d
                operand = self.fmt_operand(arg1)
                self.emit(f'printf("%d\\n", {operand});')
            return

        if op == "INPUT":
            # arg1: quando usado como statement, dest é a variável onde armazenar
            if dest is None:
                # se não tivermos destino, cria um temporário (não esperado mas seguro)
                self.emit("// [WARN] INPUT sem destino; ignorando.")
                return
            # declarar se necessário
            if dest not in self.declared_vars:
                self.emit(f"int {dest};")
                self.declared_vars.add(dest)
            self.emit(f'scanf("%d", &{dest});')
            return

        # Chamada de função / ARG / CALL
        if op == "ARG":
            # ARG é tratado no momento do CALL na maior parte dos codegens reais.
            # Aqui, vamos simplificar: empilhamos em comentários (não implementado stack real).
            # Em IR mais sofisticado, ARGs seriam colocados em ordem e CALL geraria código adequado.
            self.emit(f"// ARG {self.fmt_operand(arg1)}")
            return

        if op == "CALL":
            # Variantes no IR: pode ser CALL with dest=temp (para função que retorna)
            # arg1: destino ou nome? no seu IR: CALL dest=temp, arg1=functionName (ou vice-versa)
            # Vamos cobrir os casos mais prováveis:
            func_name = None
            ret_temp = None
            # detecta padrões:
            if dest and isinstance(arg1, str):
                # dest=temp, arg1=functionName => CALL temp <- functionName(arg2 args)
                ret_temp = dest
                func_name = arg1
            elif dest and isinstance(dest, str) and isinstance(arg1, int):
                # às vezes IR usa CALL dest=functionName, arg1=num_args
                func_name = dest
                ret_temp = None
            else:
                # fallback
                func_name = arg1 if isinstance(arg1, str) else None
                ret_temp = dest

            # Chamada simples sem passagem de argumentos reais (ARGs são só comentados aqui)
            if ret_temp:
                # temporário que recebe retorno - declarar como int
                if ret_temp not in self.declared_vars:
                    self.emit(f"int {ret_temp};")
                    self.declared_vars.add(ret_temp)
                self.emit(f"/* CALL {func_name} -> {ret_temp} */")
                self.emit(f"{ret_temp} = 0; /* chamada não implementada no codegen */")
            else:
                self.emit(f"/* CALL {func_name} */")
            return

        # Return
        if op == "RETURN":
            self.function_has_return[self.current_function] = True
            if arg1 is None:
                self.emit("return;")
            else:
                # se for main, usamos return; caso general, assumimos void functions: comentar
                self.emit("/* return value generation not implemented; ignoring */")
            return

        # Atribuições normais
        if op == "ASSIGN":
            # arg1 pode ser literal ou temporário/var
            rhs = self.fmt_operand(arg1)
            # declaramos a variável apenas na primeira atribuição no C gerado
            if dest not in self.declared_vars:
                # inferimos int por padrão
                self.emit(f"int {dest} = {rhs};")
                self.declared_vars.add(dest)
            else:
                self.emit(f"{dest} = {rhs};")
            return

        # Operações binárias (ADD, SUB, MUL, DIV, MOD, comparadores)
        if op in ("ADD", "SUB", "MUL", "DIV", "MOD", "GT", "LT", "GE", "LE", "EQ", "NE"):
            symbol = self.op_to_symbol(op)
            left = self.fmt_operand(arg1)
            right = self.fmt_operand(arg2)
            # declarar dest se necessário
            if dest and dest not in self.declared_vars:
                self.emit(f"int {dest} = {left} {symbol} {right};")
                self.declared_vars.add(dest)
            elif dest:
                self.emit(f"{dest} = {left} {symbol} {right};")
            else:
                # expressão sem destino: apenas um comentário de segurança
                self.emit(f"/* {left} {symbol} {right} */")
            return

        # Operações unárias ou outros ops passados diretamente do IR
        if op in ("NEG", "NOT"):
            operand = self.fmt_operand(arg1)
            if dest and dest not in self.declared_vars:
                if op == "NEG":
                    self.emit(f"int {dest} = -({operand});")
                else:
                    self.emit(f"int {dest} = !({operand});")
                self.declared_vars.add(dest)
            elif dest:
                if op == "NEG":
                    self.emit(f"{dest} = -({operand});")
                else:
                    self.emit(f"{dest} = !({operand});")
            else:
                self.emit(f"/* unary {op} {operand} */")
            return

        # Caso padrão: operação desconhecida
        self.emit(f"/* [ERRO] operação não suportada no codegen: {op} dest={dest} arg1={arg1} arg2={arg2} */")
