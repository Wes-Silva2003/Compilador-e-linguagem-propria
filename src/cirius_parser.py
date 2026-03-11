# Parser (Analisador Sintático) da linguagem Cirius
#
# Esta etapa recebe os tokens gerados pelo lexer e monta
# uma Árvore Sintática Abstrata (AST), que representa o
# significado estrutural do programa.
#
# Aqui é onde o código começa a “fazer sentido”.

from cirius_ast import *

# Exceção personalizada para erros de parsing
class ParserError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0  # posição atual na lista de tokens


    def peek(self):
        """Olha o token atual sem consumir (avança)."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        # token fictício no final do arquivo
        from collections import namedtuple
        Token = namedtuple("Token", ["type", "value", "line", "column"])
        return Token("EOF", None, -1, -1)

    def consume(self, expected_type=None):
        """Pega o próximo token e avança o ponteiro."""
        if self.pos >= len(self.tokens):
            raise ParserError("Fim inesperado dos tokens.")
        token = self.tokens[self.pos]
        if expected_type and token.type != expected_type:
            raise ParserError(f"Esperado {expected_type}, mas encontrado {token.type} na linha {token.line}.")
        self.pos += 1
        return token

    def match(self, *types):
        """Tenta consumir um token se ele for de um dos tipos indicados."""
        if self.peek().type in types:
            return self.consume()
        return None


    def parse(self):
        """Inicia a análise sintática (gera a AST principal)."""
        functions = []
        while self.pos < len(self.tokens) and self.peek().type != "EOF":
            functions.append(self.parse_function())
        return Program(functions)


    def parse_function(self):
        """Lê uma função (ex: func main() { ... })"""
        self.consume("FUNC")
        name = self.consume("IDENT").value

        # parâmetros
        self.consume("LPAREN")
        params = []
        if self.peek().type != "RPAREN":
            params.append(self.consume("IDENT").value)
            while self.match("COMMA"):
                params.append(self.consume("IDENT").value)
        self.consume("RPAREN")

        # corpo da função
        self.consume("LBRACE")
        body = self.parse_block()
        self.consume("RBRACE")

        return FunctionDecl(name, params, body)

    def parse_block(self):
        """Lê um bloco de código dentro de chaves."""
        statements = []
        while self.peek().type not in ("RBRACE", "EOF"):
            if self.peek().type == "SEMICOLON":
                self.consume()
                continue
            statements.append(self.parse_statement())
        return Block(statements)


    def parse_statement(self):
        """Decide qual tipo de instrução está sendo lida."""
        token_type = self.peek().type

        if token_type == "IF":
            return self.parse_if()
        elif token_type == "WHILE":
            return self.parse_while()
        elif token_type == "FOR":
            return self.parse_for()
        elif token_type == "RETURN":
            return self.parse_return()
        elif token_type == "PRINT":
            return self.parse_print()
        elif token_type == "INPUT":
            return self.parse_input()
        elif token_type == "IDENT":
            return self.parse_assignment_or_call()
        else:
            raise ParserError(f"Instrução inesperada: {token_type}")


    def parse_if(self):
        """Lê uma estrutura if / elif / else."""
        self.consume("IF")
        cond = self.parse_expression()
        self.consume("LBRACE")
        then_branch = self.parse_block()
        self.consume("RBRACE")

        elifs = []
        while self.peek().type == "ELIF":
            self.consume("ELIF")
            c = self.parse_expression()
            self.consume("LBRACE")
            blk = self.parse_block()
            self.consume("RBRACE")
            elifs.append((c, blk))

        else_branch = None
        if self.peek().type == "ELSE":
            self.consume("ELSE")
            self.consume("LBRACE")
            else_branch = self.parse_block()
            self.consume("RBRACE")

        return IfStatement(cond, then_branch, elifs, else_branch)

    def parse_while(self):
        """Lê uma estrutura while."""
        self.consume("WHILE")
        cond = self.parse_expression()
        self.consume("LBRACE")
        body = self.parse_block()
        self.consume("RBRACE")
        return WhileStatement(cond, body)

    def parse_for(self):
        """Lê uma estrutura for (ex: for i in 0..5 { ... })"""
        self.consume("FOR")
        var = self.consume("IDENT").value
        self.consume("IN")
        start = self.parse_expression()
        self.consume("DOTS")
        end = self.parse_expression()
        self.consume("LBRACE")
        body = self.parse_block()
        self.consume("RBRACE")
        return ForStatement(var, start, end, body)

    def parse_return(self):
        """Lê um comando de retorno."""
        self.consume("RETURN")
        expr = None
        if self.peek().type not in ("SEMICOLON", "RBRACE", "EOF"):
            expr = self.parse_expression()
        return ReturnStatement(expr)

    def parse_print(self):
        """Lê uma chamada de print()."""
        self.consume("PRINT")
        self.consume("LPAREN")
        expr = self.parse_expression()
        self.consume("RPAREN")
        return PrintStatement(expr)

    def parse_input(self):
        """Lê uma chamada de input()."""
        self.consume("INPUT")
        self.consume("LPAREN")
        self.consume("RPAREN")
        return InputStatement()

    def parse_assignment_or_call(self):
        """Decide se é uma atribuição (x = 5) ou uma chamada (foo())."""
        name = self.consume("IDENT").value
        if self.peek().type == "ASSIGN":
            self.consume("ASSIGN")
            expr = self.parse_expression()
            return Assignment(Var(name), expr)
        elif self.peek().type == "LPAREN":
            self.consume("LPAREN")
            args = []
            if self.peek().type != "RPAREN":
                args.append(self.parse_expression())
                while self.match("COMMA"):
                    args.append(self.parse_expression())
            self.consume("RPAREN")
            return FunctionCall(name, args)
        else:
            raise ParserError("Esperado '=' ou '(' após identificador.")


    def parse_expression(self):
        return self.parse_logic_or()

    def parse_logic_or(self):
        expr = self.parse_logic_and()
        while self.peek().type == "OR":
            op = self.consume().type
            right = self.parse_logic_and()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_logic_and(self):
        expr = self.parse_equality()
        while self.peek().type == "AND":
            op = self.consume().type
            right = self.parse_equality()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_equality(self):
        expr = self.parse_comparison()
        while self.peek().type in ("EQ", "NE"):
            op = self.consume().type
            right = self.parse_comparison()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_comparison(self):
        expr = self.parse_term()
        while self.peek().type in ("GT", "LT", "GE", "LE"):
            op = self.consume().type
            right = self.parse_term()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_term(self):
        expr = self.parse_factor()
        while self.peek().type in ("PLUS", "MINUS"):
            op = self.consume().type
            right = self.parse_factor()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_factor(self):
        expr = self.parse_unary()
        while self.peek().type in ("MUL", "DIV", "MOD"):
            op = self.consume().type
            right = self.parse_unary()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_unary(self):
        if self.peek().type in ("NOT", "MINUS"):
            op = self.consume().type
            right = self.parse_unary()
            return UnaryOp(op, right)
        return self.parse_primary()

    def parse_primary(self):
        """Lê valores simples: número, string, booleano, variável, chamada de função..."""
        token = self.peek()

        if token.type == "NUMBER":
            return Number(self.consume().value)
        elif token.type == "STRING":
            return String(self.consume().value.strip('"'))
        elif token.type == "TRUE":
            self.consume()
            return Boolean(True)
        elif token.type == "FALSE":
            self.consume()
            return Boolean(False)
        elif token.type == "IDENT":
            name = self.consume().value
            if self.peek().type == "LPAREN":
                self.consume("LPAREN")
                args = []
                if self.peek().type != "RPAREN":
                    args.append(self.parse_expression())
                    while self.match("COMMA"):
                        args.append(self.parse_expression())
                self.consume("RPAREN")
                return FunctionCall(name, args)
            return Var(name)
        elif token.type == "INPUT":
            self.consume("INPUT")
            self.consume("LPAREN")
            self.consume("RPAREN")
            return InputStatement()
        elif token.type == "LPAREN":
            self.consume("LPAREN")
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr
        else:
            raise ParserError(f"Expressão inesperada: {token.type}")
