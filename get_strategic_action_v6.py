"""
MOTOR DE DECISÃO ESTRATÉGICA v6.0 - REESCRITO COM NOVAS REGRAS
Segue EXATAMENTE as 4 regras do usuário:
1. VALIDADE (Prioridade Máxima)
2. PRODUTOS PARADOS (IS_PARADO = True)
3. RUPTURA & REPOSIÇÃO
4. MERCADO & PREÇO
"""

import pandas as pd
from datetime import datetime

def get_strategic_action_v6(row):
    """
    Retorna: (PRIORIDADE, AÇÃO RECOMENDADA)
    Prioridade: "Alta prioridade", "Média prioridade", "Baixa prioridade"
    
    ORDEM GLOBAL DE PRIORIDADE:
    1. Validade
    2. Produtos parados
    3. Ruptura / reposição
    4. Mercado & preço
    """
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # EXTRAÇÃO DE VARIÁVEIS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    estoque = float(row.get("ESTOQUE", 0) or 0)
    vb90 = float(row.get("VB 90", 0) or 0)
    venda_sogamax = float(row.get("VENDA SOGAMAX", 0) or 0)
    media_concorrencia = float(row.get("MEDIA CONCORRENCIA", 0) or 0)
    valor_venda_estoque = float(row.get("VALOR VENDA ESTOQUE", 0) or 0)
    dias_ultima_vb = float(row.get("DIAS DA ÚLTIMA VB", 0) or 0)
    
    is_parado = row.get("IS_PARADO", False)
    is_ruptura = row.get("IS_RUPTURA", False)
    is_reposicao = row.get("IS_REPOSICAO", False)
    
    # Cálculo de dias para vencer
    dias_validade = 999
    try:
        if pd.notna(row.get("VALIDADE")) and not isinstance(row.get("VALIDADE"), str):
            dt_val = pd.to_datetime(row.get("VALIDADE"))
            dias_validade = (dt_val - datetime.now()).days
    except:
        pass
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # REGRA 1: VALIDADE (PRIORIDADE MÁXIMA)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Se vencido
    if dias_validade < 0:
        return ("Alta prioridade", "BLOQUEAR VENDA / BAIXAR ESTOQUE")
    
    # Se até 60 dias
    if 0 <= dias_validade <= 60:
        return ("Alta prioridade", "LIQUIDAR IMEDIATAMENTE (desconto agressivo)")
    
    # Se 61 a 120 dias
    if 61 <= dias_validade <= 120:
        return ("Alta prioridade", "CRIAR CAMPANHA DE GIRO (promoção / combos)")
    
    # Se 121 a 180 dias
    if 121 <= dias_validade <= 180:
        return ("Média prioridade", "PRIORIZAR VENDA (time comercial / exposição)")
    
    # Se > 180 dias: continuar analisando outras regras
    # (não retornar ação aqui, deixar passar para as próximas regras)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # REGRA 2: PRODUTOS PARADOS (IS_PARADO = True)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if is_parado:
        # Se DIAS DA ÚLTIMA VB > 365
        if dias_ultima_vb > 365:
            return ("Alta prioridade", "ACIONAR COMERCIAL — bonificar, devolver ou transferir")
        
        # Se entre 180 e 365 dias
        if 180 < dias_ultima_vb <= 365:
            return ("Alta prioridade", "CRIAR CAMPANHA DE GIRO (desconto / combos)")
        
        # Se entre 90 e 180 dias
        if 90 < dias_ultima_vb <= 180:
            return ("Média prioridade", "ATIVAR VENDA (equipe comercial / exposição)")
        
        # Se VB90 = 0 e VALOR ESTOQUE > 5000
        if vb90 == 0 and valor_venda_estoque > 5000:
            return ("Alta prioridade", "LIQUIDAR ESTOQUE (ação agressiva)")
        
        # Se preço > mercado +10%
        if media_concorrencia > 0:
            dif_pct = ((venda_sogamax - media_concorrencia) / media_concorrencia) * 100
            if dif_pct >= 10:
                return ("Alta prioridade", "AJUSTAR PREÇO (acima do mercado)")
        
        # Se preço < mercado -10%
        if media_concorrencia > 0:
            dif_pct = ((venda_sogamax - media_concorrencia) / media_concorrencia) * 100
            if dif_pct <= -10:
                return ("Média prioridade", "OPORTUNIDADE DE MARGEM (avaliar aumento)")
        
        # Se sem base de concorrência
        if media_concorrencia == 0 or media_concorrencia is None:
            return ("Média prioridade", "REVISAR CADASTRO / POSICIONAMENTO")
        
        # Caso padrão
        return ("Média prioridade", "CRIAR CAMPANHA DE VENDA")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # REGRA 3: RUPTURA & REPOSIÇÃO
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if is_ruptura or is_reposicao:
        # Se ESTOQUE = 0
        if estoque == 0:
            # Se VB90 >= 20
            if vb90 >= 20:
                return ("Alta prioridade", "RECOMPRAR URGENTE (alta demanda)")
            
            # Se VB90 entre 5 e 19
            if 5 <= vb90 < 20:
                return ("Alta prioridade", "RECOMPRAR (demanda ativa)")
            
            # Se VB90 entre 1 e 4
            if 1 <= vb90 < 5:
                return ("Média prioridade", "AVALIAR REPOSIÇÃO (baixa demanda)")
            
            # Se VB90 = 0
            if vb90 == 0:
                return ("Baixa prioridade", "NÃO REABASTECER (sem demanda)")
        
        # Se ESTOQUE < VB90/3
        if estoque > 0 and estoque < (vb90 / 3):
            # Se VB90 >= 20
            if vb90 >= 20:
                return ("Alta prioridade", "REPOSIÇÃO URGENTE (risco de ruptura)")
            
            # Se VB90 entre 5 e 19
            if 5 <= vb90 < 20:
                return ("Média prioridade", "REPOSIÇÃO (demanda ativa)")
            
            # Se VB90 baixo (1 a 4)
            if 1 <= vb90 < 5:
                return ("Baixa prioridade", "AVALIAR REPOSIÇÃO (baixo giro)")
        
        # Caso padrão
        return ("Baixa prioridade", "ESTOQUE ADEQUADO (manter estratégia)")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # REGRA 4: MERCADO & PREÇO
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Somente se: IS_PARADO = False E IS_RUPTURA = False
    if not is_parado and not is_ruptura:
        # Se SEM BASE
        if media_concorrencia == 0 or media_concorrencia is None:
            return ("Média prioridade", "REDUZIR PREÇO")
        
        # Cálculo de diferença de preço
        dif_pct = ((venda_sogamax - media_concorrencia) / media_concorrencia) * 100
        
        # Preço acima do mercado (+5%+) = Alta prioridade
        if dif_pct >= 5:
            return ("Alta prioridade", "REDUZIR PREÇO")
        
        # Preço competitivo (-5% a +5%) = Média prioridade
        if -5 <= dif_pct < 5:
            return ("Média prioridade", "REDUZIR PREÇO")
        
        # Preço abaixo do mercado (<-5%) = Baixa prioridade
        if dif_pct < -5:
            return ("Baixa prioridade", "REDUZIR PREÇO")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CASO PADRÃO (nenhuma regra se aplica)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    return ("Baixa prioridade", "MANTER — sem ações críticas")


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 80)
    print("MOTOR DE DECISÃO ESTRATÉGICA v6.0 - TESTES")
    print("=" * 80)
    
    # Teste 1: Produto parado com estoque alto
    test1 = {
        "ESTOQUE": 150,
        "VB 90": 0,
        "VENDA SOGAMAX": 100,
        "MEDIA CONCORRENCIA": 90,
        "VALOR VENDA ESTOQUE": 15000,
        "DIAS DA ÚLTIMA VB": 400,
        "IS_PARADO": True,
        "IS_RUPTURA": False,
        "IS_REPOSICAO": False,
        "VALIDADE": None
    }
    print("\nTeste 1 - Produto parado com dias > 365:")
    print(f"  → {get_strategic_action_v6(test1)}")
    
    # Teste 2: Ruptura com demanda alta
    test2 = {
        "ESTOQUE": 0,
        "VB 90": 25,
        "VENDA SOGAMAX": 50,
        "MEDIA CONCORRENCIA": 45,
        "VALOR VENDA ESTOQUE": 0,
        "DIAS DA ÚLTIMA VB": 10,
        "IS_PARADO": False,
        "IS_RUPTURA": True,
        "IS_REPOSICAO": False,
        "VALIDADE": None
    }
    print("\nTeste 2 - Ruptura com demanda alta (VB90 >= 20):")
    print(f"  → {get_strategic_action_v6(test2)}")
    
    # Teste 3: Mercado & Preço - preço acima
    test3 = {
        "ESTOQUE": 50,
        "VB 90": 10,
        "VENDA SOGAMAX": 120,
        "MEDIA CONCORRENCIA": 100,
        "VALOR VENDA ESTOQUE": 6000,
        "DIAS DA ÚLTIMA VB": 30,
        "IS_PARADO": False,
        "IS_RUPTURA": False,
        "IS_REPOSICAO": False,
        "VALIDADE": None
    }
    print("\nTeste 3 - Mercado & Preço (preço +20% acima):")
    print(f"  → {get_strategic_action_v6(test3)}")
    
    print("\n" + "=" * 80)
