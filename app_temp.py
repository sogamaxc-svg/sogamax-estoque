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
