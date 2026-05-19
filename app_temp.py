   # ═══════════════════════════════════════════════
   # REGRA 4: MERCADO & PREÇO (NOVA)
   # ═══════════════════════════════════════════════

# Mesmo parado, analisar mercado também
if media_concorrencia > 0:

    dif_pct = ((venda_sogamax - media_concorrencia) / media_concorrencia) * 100

    # Muito acima do mercado
    if dif_pct >= 20:
        return ("Alta prioridade", "REDUZIR PREÇO URGENTE")

    # Acima do mercado
    elif 10 <= dif_pct < 20:
        return ("Média prioridade", "AJUSTAR PREÇO")

    # Muito abaixo
    elif dif_pct <= -15:
        return ("Média prioridade", "REVISAR MARGEM")

    # Competitivo
    else:
        return ("Baixa prioridade", "PREÇO COMPETITIVO")

# Sem benchmark
return ("Baixa prioridade", "SEM BASE DE MERCADO")
