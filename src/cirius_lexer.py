# cirius_lexer.py - Analisador Léxico da Linguagem Cirius

# O analisador léxico (ou *lexer*) é o primeiro passo do compilador.
# Ele transforma o código-fonte puro em uma sequência de "tokens",
# que são as menores unidades significativas da linguagem (palavras-chave,
# números, operadores, identificadores, etc).

# Exemplo:
#   Código-fonte → func main() { x = 10; print(x); }
#   Tokens → [FUNC, IDENT(main), LPAR, RPAR, LBRACE, IDENT(x), ASSIGN, NUMBER(10), ...]


import re
from collections import namedtuple

# Cada token carrega:
# - type  → o tipo do token (ex: NUMBER, IF, IDENT, etc)
# - value → o valor associado (ex: 42, "texto", nome de variável)
# - line  → a linha onde foi encontrado
# - column → a posição na linha

Token = namedtuple("Token", ["type", "value", "line", "column"])

KEYWORDS = {
    "func", "if", "elif", "else", "while", "for", "in",
    "print", "input", "return", "true", "false",
    "and", "or", "not", "break", "continue"
}


TOKEN_SPECIFICATION = [
    # Comentários (ignorados pelo compilador)
    ("COMMENT", r"//.*|#.*|/\*[\s\S]*?\*/"),

    # Literais (números e textos)
    ("FLOAT", r"\d+\.\d+"),
    ("NUMBER", r"\d+"),
    ("STRING", r'"[^"\n]*"'),

    # Palavras-chave reservadas
    ("FUNC", r"\bfunc\b"),
    ("IF", r"\bif\b"),
    ("ELIF", r"\belif\b"),
    ("ELSE", r"\belse\b"),
    ("WHILE", r"\bwhile\b"),
    ("FOR", r"\bfor\b"),
    ("IN", r"\bin\b"),
    ("PRINT", r"\bprint\b"),
    ("INPUT", r"\binput\b"),
    ("RETURN", r"\breturn\b"),
    ("TRUE", r"\btrue\b"),
    ("FALSE", r"\bfalse\b"),
    ("AND", r"\band\b"),
    ("OR", r"\bor\b"),
    ("NOT", r"\bnot\b"),
    ("BREAK", r"\bbreak\b"),
    ("CONTINUE", r"\bcontinue\b"),

    # Operadores compostos
    ("INC", r"\+\+"), ("DEC", r"--"),
    ("PLUS_ASSIGN", r"\+="), ("MINUS_ASSIGN", r"-="),
    ("MUL_ASSIGN", r"\*="), ("DIV_ASSIGN", r"/="),

    # Operadores relacionais
    ("EQ", r"=="), ("NE", r"!="), ("GE", r">="), ("LE", r"<="),
    ("GT", r">"), ("LT", r"<"),

    # Operadores aritméticos simples
    ("PLUS", r"\+"), ("MINUS", r"-"), ("MUL", r"\*"), ("DIV", r"/"), ("MOD", r"%"),
    ("ASSIGN", r"="),

    # Operadores bit a bit
    ("AND_BIT", r"&"), ("OR_BIT", r"\|"), ("XOR_BIT", r"\^"), ("NOT_BIT", r"~"),
    ("LSHIFT", r"<<"), ("RSHIFT", r">>"),

    # Símbolos e pontuação
    ("LPAREN", r"\("), ("RPAREN", r"\)"),
    ("LBRACE", r"\{"), ("RBRACE", r"\}"),
    ("DOTS", r"\.\."), ("SEMICOLON", r";"), ("COMMA", r","),

    # Identificadores (nomes de variáveis e funções)
    ("IDENT", r"[a-zA-Z_][a-zA-Z0-9_]*"),

    # Espaços e quebras de linha (ignorados)
    ("SKIP", r"[ \t\n]+"),

    # Qualquer caractere inválido gera erro léxico
    ("MISMATCH", r"."),
]

# Compila a expressão regular principal (um “scanner” gigante)
TOK_REGEX = "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION)
TOK_REGEX_COMPILED = re.compile(TOK_REGEX)


class Lexer:
    """Transforma o código-fonte Cirius em uma sequência de tokens."""

    def __init__(self, code: str):
        self.code = code


    def tokenize(self):
        """Percorre o código e retorna uma lista de tokens válidos."""
        line_num = 1
        line_start = 0
        tokens = []

        for match in TOK_REGEX_COMPILED.finditer(self.code):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start + 1

            # Ignora espaços e comentários
            if kind in {"SKIP", "COMMENT"}:
                line_num += value.count("\n")
                if "\n" in value:
                    line_start = match.end()
                continue

            # Converte números para int ou float
            if kind == "NUMBER":
                value = int(value)
            elif kind == "FLOAT":
                value = float(value)

            # Verifica se o identificador é palavra-chave
            elif kind == "IDENT" and value in KEYWORDS:
                kind = value.upper()

            # Token inesperado
            elif kind == "MISMATCH":
                raise RuntimeError(f"[Erro Léxico] Caractere inesperado '{value}' na linha {line_num}")

            # Adiciona o token à lista
            tokens.append(Token(kind, value, line_num, column))

        return tokens


if __name__ == "__main__":
    # Exemplo de código para testar o Lexer diretamente
    code = '''
    func main() {
        x = input();
        y = x % 2;
        if x > 0 and y == 1 {
            print("Número positivo e ímpar");
        } elif x == 0 {
            print("Zero");
        } else {
            print("Outro caso");
        }
    }
    '''

    lexer = Lexer(code)
    for token in lexer.tokenize():
        print(token)
