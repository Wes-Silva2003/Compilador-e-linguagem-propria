# Cirius AST (Árvore Sintática Abstrata)
#
# Este arquivo define as estruturas de dados usadas para representar
# o código-fonte da linguagem Cirius de forma hierárquica.
# Cada classe aqui representa um "nó" da árvore sintática.
#
# Exemplo: um `if`, um `for`, uma atribuição, um número, etc.


class Node:
    """Classe base para todos os nós da AST.
    Serve como ponto de partida para todas as outras estruturas."""
    
    def to_dict(self):
        """Converte o nó em um dicionário (usado para salvar em JSON)."""
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        """Cria um nó novamente a partir de um dicionário (para recarregar ASTs salvas)."""
        obj = cls.__new__(cls)
        obj.__dict__.update(d)
        return obj


class Program(Node):
    """Representa o programa inteiro — uma lista de funções."""
    def __init__(self, functions=None):
        self.functions = functions or []


class FunctionDecl(Node):
    """Declaração de função (ex: func main() { ... })."""
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body


class Block(Node):
    """Um bloco de código (ex: o conteúdo dentro de chaves {})."""
    def __init__(self, statements=None):
        self.statements = statements or []


class Assignment(Node):
    """Atribuição de valor (ex: x = 10)."""
    def __init__(self, target, expr):
        self.target = target
        self.expr = expr


class Var(Node):
    """Uma variável (ex: x, idade, resultado)."""
    def __init__(self, name):
        self.name = name


class Number(Node):
    """Número inteiro ou decimal."""
    def __init__(self, value):
        self.value = value


class String(Node):
    """Texto entre aspas (ex: "Olá")."""
    def __init__(self, value):
        self.value = value


class Boolean(Node):
    """Valor lógico: true ou false."""
    def __init__(self, value):
        self.value = value


class BinaryOp(Node):
    """Operação com dois lados (ex: x + y, a > b)."""
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class UnaryOp(Node):
    """Operação com um único operando (ex: -x, not ativo)."""
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand


class IfStatement(Node):
    """Estrutura condicional (if / elif / else)."""
    def __init__(self, cond, then, elifs=None, otherwise=None):
        self.cond = cond          # condição principal (ex: x > 10)
        self.then = then          # bloco executado se a condição for verdadeira
        self.elifs = elifs or []  # lista de pares (condição, bloco)
        self.otherwise = otherwise  # bloco else, se existir


class WhileStatement(Node):
    """Estrutura de repetição while."""
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body


class ForStatement(Node):
    """Estrutura de repetição for (ex: for i in 0..5 { ... })."""
    def __init__(self, var, start, end, body):
        self.var = var
        self.start = start
        self.end = end
        self.body = body


class ReturnStatement(Node):
    """Comando de retorno dentro de uma função."""
    def __init__(self, value=None):
        self.value = value


class PrintStatement(Node):
    """Impressão no terminal (ex: print("Olá!"))."""
    def __init__(self, value):
        self.value = value


class InputStatement(Node):
    """Leitura de entrada do usuário (ex: input())."""
    def __init__(self):
        pass


class FunctionCall(Node):
    """Representa uma chamada de função (ex: soma(x, y))."""
    def __init__(self, name, args=None):
        self.name = name
        self.args = args or []
