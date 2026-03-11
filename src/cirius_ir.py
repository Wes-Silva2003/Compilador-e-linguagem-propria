# cirius_ir.py - Gerador de Código Intermediário (IR)

# Este módulo converte a AST da linguagem Cirius em um
# código intermediário do tipo TAC (Three Address Code),
# uma forma mais simples de manipular e otimizar o código
# antes da geração final em C.

# Em resumo:
#   AST  ➜  TAC  ➜  Otimização  ➜  Código C

from cirius_ast import *

class IRInstruction:
    """Cada instrução TAC (Three Address Code) tem uma operação (op),
    um destino (dest) e até dois argumentos (arg1, arg2)."""

    def __init__(self, op, dest=None, arg1=None, arg2=None):
        self.op = op
        self.dest = dest
        self.arg1 = arg1
        self.arg2 = arg2

    def __repr__(self):
        """Mostra a instrução de forma legível (útil para debug)."""
        parts = [self.op]
        if self.dest is not None:
            parts.append(str(self.dest))
        if self.arg1 is not None:
            parts.append(str(self.arg1))
        if self.arg2 is not None:
            parts.append(str(self.arg2))
        return " ".join(parts)


class IRGenerator:
    def __init__(self):
        self.instructions = []    # Lista de instruções geradas
        self.temp_counter = 0     # Contador de variáveis temporárias (t1, t2, ...)
        self.label_counter = 0    # Contador de rótulos (L1, L2, ...)

    def new_temp(self):
        """Cria um novo registrador temporário (ex: t1, t2, t3...)."""
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self, prefix="L"):
        """Cria um novo rótulo (ex: L1, L2, END_IF1...)."""
        self.label_counter += 1
        return f"{prefix}{self.label_counter}"

    def generate(self, program: Program):
        """Percorre todo o programa e gera as instruções IR."""
        for func in program.functions:
            self.gen_function(func)
        return self.instructions


    def gen_function(self, func: FunctionDecl):
        """Gera o bloco IR para uma função (ex: func main() { ... })."""
        self.instructions.append(IRInstruction("FUNC_BEGIN", dest=func.name))
        self.gen_block(func.body)
        self.instructions.append(IRInstruction("FUNC_END", dest=func.name))


    def gen_block(self, block: Block):
        """Traduz um bloco de comandos para IR."""
        for stmt in block.statements:
            self.gen_statement(stmt)

 
    def gen_statement(self, stmt):
        """Traduz uma instrução individual da AST."""
        if isinstance(stmt, Assignment):
            value = self.gen_expression(stmt.expr)
            self.instructions.append(IRInstruction("ASSIGN", dest=stmt.target.name, arg1=value))

        elif isinstance(stmt, FunctionCall):
            args = [self.gen_expression(arg) for arg in stmt.args]
            for arg in args:
                self.instructions.append(IRInstruction("ARG", arg1=arg))
            self.instructions.append(IRInstruction("CALL", dest=stmt.name, arg1=len(args)))

        elif isinstance(stmt, PrintStatement):
            val = self.gen_expression(stmt.value)
            self.instructions.append(IRInstruction("PRINT", arg1=val))

        elif isinstance(stmt, InputStatement):
            temp = self.new_temp()
            self.instructions.append(IRInstruction("INPUT", dest=temp))
            return temp

        elif isinstance(stmt, ReturnStatement):
            val = self.gen_expression(stmt.value) if stmt.value else None
            self.instructions.append(IRInstruction("RETURN", arg1=val))

        elif isinstance(stmt, IfStatement):
            self.gen_if(stmt)

        elif isinstance(stmt, WhileStatement):
            self.gen_while(stmt)

        elif isinstance(stmt, ForStatement):
            self.gen_for(stmt)

        else:
            raise Exception(f"[IR] Geração não implementada para {type(stmt).__name__}")

  
    def gen_if(self, stmt: IfStatement):
        """Traduz estruturas condicionais completas."""
        label_end = self.new_label("END_IF")
        label_else_list = [self.new_label("ELIF") for _ in stmt.elifs]
        label_else_main = self.new_label("ELSE") if stmt.otherwise else label_end

        # Condição principal (if)
        cond_temp = self.gen_expression(stmt.cond)
        first_label = label_else_list[0] if stmt.elifs else label_else_main
        self.instructions.append(IRInstruction("IF_FALSE_GOTO", cond_temp, first_label))
        self.gen_block(stmt.then)
        self.instructions.append(IRInstruction("GOTO", label_end))

        # Elifs (casos intermediários)
        for i, (elif_cond, elif_block) in enumerate(stmt.elifs):
            label_next = label_else_list[i + 1] if i + 1 < len(stmt.elifs) else label_else_main
            self.instructions.append(IRInstruction("LABEL", dest=label_else_list[i]))
            cond_temp = self.gen_expression(elif_cond)
            self.instructions.append(IRInstruction("IF_FALSE_GOTO", cond_temp, label_next))
            self.gen_block(elif_block)
            self.instructions.append(IRInstruction("GOTO", label_end))

        # Bloco else (se existir)
        if stmt.otherwise:
            self.instructions.append(IRInstruction("LABEL", dest=label_else_main))
            self.gen_block(stmt.otherwise)

        # Fim da estrutura
        self.instructions.append(IRInstruction("LABEL", dest=label_end))


    def gen_while(self, stmt: WhileStatement):
        label_start = self.new_label("WHILE")
        label_end = self.new_label("END_WHILE")

        self.instructions.append(IRInstruction("LABEL", dest=label_start))
        cond_temp = self.gen_expression(stmt.cond)
        self.instructions.append(IRInstruction("IF_FALSE_GOTO", cond_temp, label_end))
        self.gen_block(stmt.body)
        self.instructions.append(IRInstruction("GOTO", label_start))
        self.instructions.append(IRInstruction("LABEL", dest=label_end))

   
    def gen_for(self, stmt: ForStatement):
        """Traduz laços do tipo: for i in 0..5 { ... }"""
        label_start = self.new_label("FOR")
        label_end = self.new_label("END_FOR")

        start_val = self.gen_expression(stmt.start)
        self.instructions.append(IRInstruction("ASSIGN", dest=stmt.var, arg1=start_val))

        self.instructions.append(IRInstruction("LABEL", dest=label_start))
        end_val = self.gen_expression(stmt.end)
        cond_temp = self.new_temp()
        self.instructions.append(IRInstruction("LT_EQ", dest=cond_temp, arg1=stmt.var, arg2=end_val))
        self.instructions.append(IRInstruction("IF_FALSE_GOTO", cond_temp, label_end))
        self.gen_block(stmt.body)
        self.instructions.append(IRInstruction("ADD", dest=stmt.var, arg1=stmt.var, arg2=1))
        self.instructions.append(IRInstruction("GOTO", label_start))
        self.instructions.append(IRInstruction("LABEL", dest=label_end))


    def gen_expression(self, expr):
        """Traduz expressões e retorna um registrador temporário com o resultado."""
        if isinstance(expr, Number):
            return expr.value

        elif isinstance(expr, String):
            return expr.value

        elif isinstance(expr, Boolean):
            return expr.value

        elif isinstance(expr, Var):
            return expr.name

        elif isinstance(expr, UnaryOp):
            right = self.gen_expression(expr.operand)
            temp = self.new_temp()
            self.instructions.append(IRInstruction(expr.op, dest=temp, arg1=right))
            return temp

        elif isinstance(expr, BinaryOp):
            left = self.gen_expression(expr.left)
            right = self.gen_expression(expr.right)
            temp = self.new_temp()
            self.instructions.append(IRInstruction(expr.op, dest=temp, arg1=left, arg2=right))
            return temp

        elif isinstance(expr, FunctionCall):
            args = [self.gen_expression(arg) for arg in expr.args]
            for arg in args:
                self.instructions.append(IRInstruction("ARG", arg1=arg))
            temp = self.new_temp()
            self.instructions.append(IRInstruction("CALL", dest=temp, arg1=expr.name, arg2=len(args)))
            return temp

        elif isinstance(expr, InputStatement):
            temp = self.new_temp()
            self.instructions.append(IRInstruction("INPUT", dest=temp))
            return temp

        else:
            raise Exception(f"[IR] Expressão não implementada: {type(expr).__name__}")
