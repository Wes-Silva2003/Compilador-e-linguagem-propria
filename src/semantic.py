# cirius_semantic.py - Analisador Semântico da Linguagem Cirius

# O Analisador Semântico é responsável por verificar se o código-fonte
# "faz sentido" logicamente — além de estar correto sintaticamente.

# Ele checa coisas como:
# Uso de variáveis antes da declaração
# Chamadas de funções existentes
# Quantidade correta de parâmetros
# Escopos locais e globais bem definidos
#
# Caso encontre erros, ele interrompe o processo e informa ao usuário.

from cirius_ast import *

class SemanticError(Exception):
    """Lançada quando algo semântico está incorreto (ex: variável não declarada)."""
    pass


class BuiltinFunction:
    """Representa uma função embutida da linguagem (ex: print, input, str)."""
    def __init__(self, name: str, arity: int):
        self.name = name
        self.arity = arity


class SymbolTable:
    """
    Tabela de símbolos com suporte a escopos aninhados.
    Cada escopo (função, bloco) possui sua própria tabela.
    """
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def define(self, name: str, value):
        """Adiciona um novo símbolo ao escopo atual."""
        if name in self.symbols:
            raise SemanticError(f"Símbolo '{name}' já declarado neste escopo.")
        self.symbols[name] = value

    def resolve(self, name: str):
        """Procura o símbolo em escopos locais e depois globais."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.resolve(name)
        raise SemanticError(f"Símbolo '{name}' não declarado.")


class SemanticAnalyzer:
    """Percorre a AST e aplica regras semânticas sobre ela."""

    def __init__(self):
        # Escopo global armazena variáveis e funções principais
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self._add_builtins()

    def _add_builtins(self):
        """Registra funções padrão como print(), str(), input()."""
        self.global_scope.define("print", BuiltinFunction("print", 1))
        self.global_scope.define("str", BuiltinFunction("str", 1))
        self.global_scope.define("input", BuiltinFunction("input", 0))

    def analyze(self, node):
        """Inicia a análise de um nó (AST)."""
        method = f"visit_{type(node).__name__}"
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise SemanticError(f"[Semântico] Nenhum visitor implementado para {type(node).__name__}")

    def visit_Program(self, node: Program):
        """Percorre todas as funções do programa."""
        for func in node.functions:
            self.analyze(func)

    def visit_FunctionDecl(self, node: FunctionDecl):
        """Registra e analisa uma função."""
        self.global_scope.define(node.name, node)

        # Cria novo escopo local para a função
        previous_scope = self.current_scope
        self.current_scope = SymbolTable(parent=self.global_scope)

        # Declara parâmetros no escopo da função
        for param in node.params:
            self.current_scope.define(param, "param")

        # Analisa corpo da função
        self.analyze(node.body)
        self.current_scope = previous_scope


    def visit_Block(self, node: Block):
        """Analisa um bloco de código (escopo local)."""
        previous_scope = self.current_scope
        self.current_scope = SymbolTable(parent=previous_scope)

        for stmt in node.statements:
            self.analyze(stmt)

        self.current_scope = previous_scope

    def visit_Assignment(self, node: Assignment):
        """Verifica se a variável está declarada e analisa a expressão."""
        self.analyze(node.expr)
        if isinstance(node.target, Var):
            # Se a variável não existir, é declarada automaticamente
            if node.target.name not in self.current_scope.symbols:
                self.current_scope.define(node.target.name, "var")
        else:
            self.analyze(node.target)

    def visit_Var(self, node: Var):
        """Confirma que a variável foi previamente declarada."""
        self.current_scope.resolve(node.name)


    def visit_Number(self, node: Number): pass
    def visit_String(self, node: String): pass
    def visit_Boolean(self, node: Boolean): pass

    def visit_BinaryOp(self, node: BinaryOp):
        """Verifica ambos os lados da operação binária."""
        self.analyze(node.left)
        self.analyze(node.right)

    def visit_UnaryOp(self, node: UnaryOp):
        """Verifica operandos em operações unárias (ex: not x)."""
        self.analyze(node.operand)

    
    def visit_IfStatement(self, node: IfStatement):
        self.analyze(node.cond)
        self.analyze(node.then)

        # Analisa elifs, se houver
        for cond, blk in node.elifs:
            self.analyze(cond)
            self.analyze(blk)

        # Analisa bloco else
        if node.otherwise:
            self.analyze(node.otherwise)

    def visit_WhileStatement(self, node: WhileStatement):
        self.analyze(node.cond)
        self.analyze(node.body)

    def visit_ForStatement(self, node: ForStatement):
        """Cria um escopo local e define a variável do loop."""
        prev_scope = self.current_scope
        self.current_scope = SymbolTable(parent=prev_scope)

        self.current_scope.define(node.var, "var")
        self.analyze(node.start)
        self.analyze(node.end)
        self.analyze(node.body)

        self.current_scope = prev_scope

    
    def visit_ReturnStatement(self, node: ReturnStatement):
        """Verifica se o valor retornado é válido."""
        if node.value:
            self.analyze(node.value)

    def visit_FunctionCall(self, node: FunctionCall):
        """Verifica se a função existe e se os argumentos estão corretos."""
        func = self.global_scope.resolve(node.name)

        # Funções definidas pelo usuário
        if isinstance(func, FunctionDecl):
            if len(node.args) != len(func.params):
                raise SemanticError(
                    f"Função '{node.name}' espera {len(func.params)} argumento(s), mas recebeu {len(node.args)}."
                )

        # Funções embutidas
        elif isinstance(func, BuiltinFunction):
            if func.arity != len(node.args):
                raise SemanticError(
                    f"Função embutida '{node.name}' espera {func.arity} argumento(s), mas recebeu {len(node.args)}."
                )

        else:
            raise SemanticError(f"'{node.name}' não é uma função válida.")

        # Analisa os argumentos individualmente
        for arg in node.args:
            self.analyze(arg)


    def visit_PrintStatement(self, node: PrintStatement):
        self.analyze(node.value)

    def visit_InputStatement(self, node: InputStatement):
        """Input não tem filhos semânticos, apenas valida a existência."""
        pass
