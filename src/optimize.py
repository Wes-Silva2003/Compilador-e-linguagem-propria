# cirius_optimize.py - Otimizador de Código Intermediário (IR)

# Este módulo realiza otimizações simples sobre o código intermediário
# (Three Address Code - TAC), gerado pelo compilador da linguagem Cirius.

# Por enquanto, o foco está em uma otimização clássica:
# Eliminação de Código Morto (Dead Code Elimination)

# Essa técnica remove instruções que calculam valores nunca utilizados,
# reduzindo o tamanho e o custo de execução do programa.

from typing import List, Dict, Any, Set

class Optimizer:
    """Executa otimizações sobre o IR (código intermediário)."""

    def __init__(self):
        # Nenhum estado persistente é necessário por enquanto
        pass

    def dead_code_elimination(self, ir_code: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove instruções cujo destino (variável ou temporário)
        nunca é usado posteriormente no programa.
        """
        used_vars: Set[str] = set()

        # Passada reversa: identifica variáveis que são usadas
        # antes de serem sobrescritas. Isso ajuda a descobrir o que
        # realmente precisa ser mantido.
        for instr in reversed(ir_code):
            if instr.get("arg1") and isinstance(instr["arg1"], str):
                used_vars.add(instr["arg1"])
            if instr.get("arg2") and isinstance(instr["arg2"], str):
                used_vars.add(instr["arg2"])

        optimized_code = []

        # Segunda passada: mantém apenas instruções necessárias
        for instr in ir_code:
            dest = instr.get("dest")

            # Mantém instruções que:
            # - não têm destino (como GOTO, LABEL, PRINT)
            # - produzem valores usados posteriormente
            # - são essenciais para o fluxo (ex: FUNC_BEGIN)
            if (
                dest is None
                or dest in used_vars
                or instr["op"] in ("FUNC_BEGIN", "LABEL", "RETURN", "PRINT")
            ):
                optimized_code.append(instr)

        return optimized_code

    def optimize(self, ir_code: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executa o pipeline de otimizações.
        (Por enquanto, apenas a eliminação de código morto.)
        """
        print("\n[Optimizer] 🔧 Iniciando otimizações...")

        previous_len = len(ir_code) + 1

        # Executa múltiplas passagens até não haver mais mudanças
        while len(ir_code) < previous_len:
            previous_len = len(ir_code)
            ir_code = self.dead_code_elimination(ir_code)

        print(f"[Optimizer] ✅ Concluído! IR final contém {len(ir_code)} instruções.")
        return ir_code
