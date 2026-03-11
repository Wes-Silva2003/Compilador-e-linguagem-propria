# Interpretador da AST da linguagem Cirius
#
# Este módulo percorre a AST e executa o programa diretamente
# (modo "run" do compilador). É útil para testes rápidos sem gerar C.

from cirius_ast import *

# Exceção usada internamente para simular retorno de função
class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value


# Ambiente de execução com suporte a escopos encadeados
class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        """Busca variável no escopo atual, subindo para o pai se necessário."""
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Variável '{name}' não definida.")

    def assign(self, name, value):
        """Atribui no escopo atual (declara se não existir)."""
        self.vars[name] = value

    def set_existing(self, name, value):
        """Atribui em escopo já existente (procura o escopo onde a variável foi definida)."""
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.set_existing(name, value)
            return
        # se não existir, definimos no escopo atual (comportamento permissivo)
        self.vars[name] = value


# Intérprete que visita nós da AST
class Interpreter:
    def __init__(self):
        # Escopo global (contém funções definidas e builtins)
        self.globals = Environment()
        self._add_builtins()

    def _add_builtins(self):
        """Registra funções e utilitários embutidos."""
        # print -> aceita 1 argumento; implementamos de forma simples
        self.globals.assign("print", lambda *args: print(*args))
        # input -> lê string; interpretador espera inteiros para input() por compatibilidade com IR/tests
        self.globals.assign("input", lambda: input())
        # conversões úteis
        self.globals.assign("str", lambda x: str(x))
        self.globals.assign("int", lambda x: int(x))
        self.globals.assign("float", lambda x: float(x))
        self.globals.assign("bool", lambda x: bool(x))

 
    def interpret(self, node: Program):
        """Inicia a execução de um Program (lista de funções)."""
        try:
            # Registra todas as funções no escopo global (sem executá-las)
            for func_decl in node.functions:
                # armazenamos o nó da função para chamadas posteriores
                self.globals.assign(func_decl.name, func_decl)

            # procura a função main e a executa
            main_func = self.globals.get("main")
            if not main_func or not isinstance(main_func, FunctionDecl):
                raise RuntimeError("Função 'main' não encontrada ou inválida.")

            # Ao executar main, criamos um ambiente novo cuja parent é globals
            # para que funções possam acessar globals (builtins) quando necessário.
            call_env = Environment(parent=self.globals)
            try:
                self.visit_FunctionDecl(main_func, call_env)
            except ReturnValue as r:
                # ignora valor retornado de main (comportamento simples)
                return r.value

        except (NameError, TypeError, RuntimeError) as e:
            print(f"[Erro de Execução] {e}")


    def visit(self, node, env: Environment):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, env)

    def generic_visit(self, node, env: Environment):
        raise NotImplementedError(f"Nenhum visitor para {type(node).__name__}")


    def visit_Number(self, node: Number, env: Environment):
        return node.value

    def visit_String(self, node: String, env: Environment):
        return node.value

    def visit_Boolean(self, node: Boolean, env: Environment):
        return node.value

    def visit_Var(self, node: Var, env: Environment):
        return env.get(node.name)

    def visit_Assignment(self, node: Assignment, env: Environment):
        var_name = node.target.name
        value = self.visit(node.expr, env)
        env.assign(var_name, value)
        return value


    def visit_BinaryOp(self, node: BinaryOp, env: Environment):
        left = self.visit(node.left, env)
        right = self.visit(node.right, env)
        op = str(node.op).upper()  # normaliza para maiúsculas

        # Operações aritméticas
        if op in ('+', 'ADD', 'PLUS'):
            return left + right
        elif op in ('-', 'SUB', 'MINUS'):
            return left - right
        elif op in ('*', 'MUL', 'MULT'):
            return left * right
        elif op in ('/', 'DIV'):
            return left / right
        elif op in ('%', 'MOD'):
            return left % right

        # Comparações
        elif op in ('==', 'EQ'):
            return left == right
        elif op in ('!=', 'NE', 'NEQ'):
            return left != right
        elif op in ('>', 'GT'):
            return left > right
        elif op in ('<', 'LT'):
            return left < right
        elif op in ('>=', 'GE', 'GEQ'):
            return left >= right
        elif op in ('<=', 'LE', 'LEQ'):
            return left <= right

        # Operadores lógicos
        elif op in ('&&', 'AND'):
            return bool(left) and bool(right)
        elif op in ('||', 'OR'):
            return bool(left) or bool(right)

        else:
            raise RuntimeError(f"Operador desconhecido: {op}")
        

    def visit_Block(self, node: Block, env: Environment):
        block_env = Environment(parent=env)
        for stmt in node.statements:
            result = self.visit(stmt, block_env)
        return None

    def visit_IfStatement(self, node: IfStatement, env: Environment):
        cond_val = self.visit(node.cond, env)
        if cond_val:
            return self.visit(node.then, env)
        else:
            for elif_cond, elif_block in node.elifs:
                if self.visit(elif_cond, env):
                    return self.visit(elif_block, env)
            if node.otherwise:
                return self.visit(node.otherwise, env)
        return None

    def visit_WhileStatement(self, node: WhileStatement, env: Environment):
        while self.visit(node.cond, env):
            res = self.visit(node.body, env)
        return None

    def visit_ForStatement(self, node: ForStatement, env: Environment):
        start_val = self.visit(node.start, env)
        end_val = self.visit(node.end, env)
        loop_env = Environment(parent=env)
        for i in range(int(start_val), int(end_val) + 1):
            loop_env.assign(node.var, i)
            self.visit(node.body, loop_env)
        return None


    def visit_PrintStatement(self, node: PrintStatement, env: Environment):
        value = self.visit(node.value, env)
        print(value)

    def visit_InputStatement(self, node: InputStatement, env: Environment):
        try:
            text = input()
            return int(text)
        except ValueError:
            return text

    def visit_ReturnStatement(self, node: ReturnStatement, env: Environment):
        value = self.visit(node.value, env) if node.value is not None else None
        raise ReturnValue(value)

 
    def visit_FunctionDecl(self, node: FunctionDecl, env: Environment):
        func_env = Environment(parent=self.globals)
        self.visit(node.body, env)
        return None

    def visit_FunctionCall(self, node: FunctionCall, env: Environment):
        func = None
        try:
            func = env.get(node.name)
        except NameError:
            func = self.globals.get(node.name)

        # Função embutida (callable Python) 
        if callable(func) and not isinstance(func, FunctionDecl):
            args = [self.visit(arg, env) for arg in node.args]
            try:
                return func(*args)
            except Exception as e:
                raise RuntimeError(f"Erro ao chamar built-in '{node.name}': {e}")

        # Função definida pelo usuário
        if isinstance(func, FunctionDecl):
            if len(node.args) != len(func.params):
                raise TypeError(f"Função '{node.name}' espera {len(func.params)} argumento(s), mas recebeu {len(node.args)}.")

            arg_values = [self.visit(arg, env) for arg in node.args]
            call_env = Environment(parent=self.globals)
            for param_name, arg_val in zip(func.params, arg_values):
                call_env.assign(param_name, arg_val)

            try:
                self.visit(func.body, call_env)
            except ReturnValue as r:
                return r.value
            return None

        raise TypeError(f"'{node.name}' não é uma função ou não foi encontrada.")
