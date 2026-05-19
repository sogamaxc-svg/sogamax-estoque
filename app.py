"""
SOGAMAX - Análise de Estoque (CONFIABILIDADE OPERACIONAL)
Dashboard de Diretoria | Contagem Oficial, Filtros Dinâmicos, Exportação Excel
MODIFICADO: + Aba Todos os Produtos + 2 Cards Financeiros
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import warnings
import os
from datetime import datetime
from io import BytesIO

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SOGAMAX | Análise de Estoque",
    page_icon=,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS PREMIUM EXECUTIVO (MANTIDO)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0f1e; color: #e2e8f0; }
.main-header {
    background: linear-gradient(90deg, #1a2744 0%, #0d1530 100%);
    border-bottom: 1px solid rgba(99,179,237,0.3);
    padding: 25px 35px;
    margin: -60px -50px 30px -50px;
}
.header-title h1 { font-size: 1.8rem; font-weight: 800; margin: 0; color: #f0f4ff; letter-spacing: -0.02em; }
.metric-card {
    background: #161f3a;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    height: 100%;
}
.metric-label { color: #94a3b8; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.metric-value { color: #ffffff; font-size: 1.4rem; font-weight: 800; line-height: 1.1; }
.metric-sub { color: #64748b; font-size: 0.6rem; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px; }
.stTabs [data-baseweb="tab"] { background-color: #161f3a !important; color: #94a3b8 !important; padding: 12px 20px !important; font-weight: 700 !important; font-size: 0.75rem !important; }
.stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: #ffffff !important; border: 1px solid rgba(99,179,237,0.3) !important; border-bottom: none !important; }
.insight-card { background: rgba(30, 58, 138, 0.3); border-left: 4px solid #3b82f6; padding: 15px; border-radius: 4px; margin-bottom: 10px; }
.audit-badge { background: #1e293b; color: #38bdf8; padding: 4px 12px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; border: 1px solid #38bdf8; }
.priority-high { color: #ef4444; font-weight: 700; }
.priority-medium { color: #f59e0b; font-weight: 700; }
.priority-low { color: #10b981; font-weight: 700; }
.price-alert { background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 10px; border-radius: 4px; margin-bottom: 8px; }
.no-giro-alert { background: rgba(239, 68, 68, 0.15); border-left: 4px solid #dc2626; padding: 12px; border-radius: 4px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FORMATAÇÃO MONETÁRIA E PERCENTUAL BR
# ─────────────────────────────────────────────
def fmt_brl(val):
    try:
        if pd.isna(val) or val == 0: return "R$ 0,00"
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def fmt_pct(val):
    try:
        if pd.isna(val) or val == 0: return "0,00%"
        return f"{val*100:+.2f}%".replace(".", ",")
    except:
        return "0,00%"

def fmt_concorrencia(val):
    if pd.isna(val) or val == 0: return "SEM BASE"
    return fmt_brl(val)

# ─────────────────────────────────────────────
# MOTOR DE DECISÃO ESTRATÉGICA v5.8
# ─────────────────────────────────────────────

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
    dias_ultima_vb = float(row.get("DIAS DA ULTIMA VB", 0) or 0)
    
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
    # REGRA 4: MERCADO & PREÇO (CORRIGIDA)
    # ═══════════════════════════════════════════════════════════════════════════════

        # ═══════════════════════════════════════════════════════════════════════════════
    # REGRA 4: MERCADO & PREÇO (CORRIGIDA)
    # ═══════════════════════════════════════════════════════════════════════════════

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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CASO PADRÃO (nenhuma regra se aplica)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    return ("Baixa prioridade", "MANTER — sem ações críticas")


# ─────────────────────────────────────────────
# CARREGAMENTO DE DADOS
# ─────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "ANALISE DE ESTOQUE GERAL SOGAMAX.xlsx")

@st.cache_data(ttl=3600)
def load_and_audit_v49():
    if not os.path.exists(DATA_PATH):
        return None, "Arquivo não encontrado."
    
    try:
        xl = pd.ExcelFile(DATA_PATH)
        
        def clean_df(df):
            df.columns = [str(c).strip() for c in df.columns]
            df = df.dropna(how='all').reset_index(drop=True)
            if 'ID' in df.columns:
                return df.dropna(subset=['ID']).reset_index(drop=True)
            return df

        # Carregar abas
        df_todos = clean_df(pd.read_excel(xl, "TODOS OS PRODUTOS", engine="openpyxl"))
        df_parados_oficial = clean_df(pd.read_excel(xl, "PRODUTOS PARADOS ", engine="openpyxl"))
        df_validade_oficial = clean_df(pd.read_excel(xl, "PRODUTOS COM VALIDADE PROXIMA", engine="openpyxl"))
        
        # CONTAGEM OFICIAL v4.9
        parados_count_oficial = len(df_parados_oficial)
        validade_count_oficial = len(df_validade_oficial)
        
        # Auditoria de IDs parados (OFICIAL)
        parados_ids = set(df_parados_oficial['ID'].unique())
        validade_ids = set(df_validade_oficial['ID'].unique()) if 'ID' in df_validade_oficial.columns else set()
        
        # Merge de informações financeiras
        # NOTA: PRODUTOS PARADOS usa 'SOGAMAX', TODOS OS PRODUTOS usa 'VENDA SOGAMAX'
        cols_ref = [
        'ID',
        'SOGAMAX',
        'CUSTO SOGAMAX',
        'SANTA CRUZ',
        'PROFARMA',
        'VB 90',
        'DIAS DA ULTIMA VB',
        'VALIDADE'
      ]
        df_ref_financeiro = df_parados_oficial[[c for c in cols_ref if c in df_parados_oficial.columns]].drop_duplicates(subset=['ID'])
        
        df_final = pd.merge(df_todos, df_ref_financeiro, on='ID', how='left', suffixes=('', '_ref'))
        
        # Preenchimento de colunas financeiras
        for col in ['SOGAMAX', 'CUSTO SOGAMAX', 'SANTA CRUZ', 'PROFARMA', 'VB 90', 'DIAS DA ULTIMA VB']:
            ref_col = f"{col}_ref"
            if ref_col in df_final.columns:
                df_final[col] = df_final[col].fillna(df_final[ref_col])
                df_final.drop(columns=[ref_col], inplace=True)
        
        # Normalizar nome da coluna: se tem SOGAMAX, renomear para VENDA SOGAMAX
        if 'SOGAMAX' in df_final.columns and 'VENDA SOGAMAX' not in df_final.columns:
            df_final.rename(columns={'SOGAMAX': 'VENDA SOGAMAX'}, inplace=True)

        # Merge de Validade (OFICIAL)
        if 'VALIDADE' in df_validade_oficial.columns:
            df_val_map = df_validade_oficial[['ID', 'VALIDADE']].drop_duplicates(subset=['ID']) if 'ID' in df_validade_oficial.columns else pd.DataFrame()
            if not df_val_map.empty:
                df_final = pd.merge(df_final, df_val_map, on='ID', how='left', suffixes=('', '_val'))
                if 'VALIDADE_val' in df_final.columns:
                    df_final['VALIDADE'] = df_final['VALIDADE'].fillna(df_final['VALIDADE_val'])
                    df_final.drop(columns=['VALIDADE_val'], inplace=True)

        # Conversão Numérica
        for col in ['ESTOQUE', 'VB 90', 'VENDA SOGAMAX', 'CUSTO SOGAMAX', 'SANTA CRUZ', 'PROFARMA', 'DIAS DA ULTIMA VB']:
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
            # Se a coluna não existe, criar com zeros
            elif col == 'VENDA SOGAMAX':
                df_final['VENDA SOGAMAX'] = 0

        # Cálculos Financeiros
        df_final["VALOR VENDA ESTOQUE"] = df_final["ESTOQUE"] * df_final["VENDA SOGAMAX"]
        df_final["CUSTO ESTOQUE"] = df_final["ESTOQUE"] * df_final["CUSTO SOGAMAX"]
        
        # Média Concorrência
        def calc_media(row):
            vals = [v for v in [row.get("SANTA CRUZ", 0), row.get("PROFARMA", 0)] if v > 0]
            return np.mean(vals) if vals else 0
        df_final["MEDIA CONCORRENCIA"] = df_final.apply(calc_media, axis=1)
        df_final["DIFERENCA R$"] = df_final["VENDA SOGAMAX"] - df_final["MEDIA CONCORRENCIA"]
        df_final["DIFERENCA MERCADO %"] = np.where(df_final["MEDIA CONCORRENCIA"] > 0, 
                                                (df_final["VENDA SOGAMAX"] - df_final["MEDIA CONCORRENCIA"]) / df_final["MEDIA CONCORRENCIA"], 0)

        # Flags de Status (OFICIAL v4.9)
        df_final["IS_PARADO"] = df_final['ID'].isin(parados_ids)
        df_final["IS_VALIDADE"] = df_final['ID'].isin(validade_ids)
        df_final["IS_RUPTURA"] = (df_final["ESTOQUE"] == 0) & (df_final["VB 90"] > 0)
        df_final["IS_REPOSICAO"] = (df_final["ESTOQUE"] > 0) & (df_final["ESTOQUE"] < df_final["VB 90"]/3) & (df_final["VB 90"] > 0)
        df_final["IS_OK"] = (df_final["STATUS DE ESTOQUE"] == "OK") & (~df_final["IS_PARADO"])

        # Classificação IA
        def classify_v49(row):
            if row["IS_PARADO"]:
                dias = row.get("DIAS DA ULTIMA VB", 0)
                if dias > 365: return "Crítico"
                if 180 <= dias <= 365: return "Alto Risco"
                if row["MEDIA CONCORRENCIA"] == 0: return "Sem Benchmark"
                return "Atenção (Parado)"
            if row["IS_RUPTURA"]: return "Ruptura Imediata"
            if row["IS_REPOSICAO"]: return "Reposição Urgente"
            if row["IS_OK"]: return "Saudável (OK)"
            return "Monitorar"

        df_final["CLASSIFICAÇÃO IA"] = df_final.apply(classify_v49, axis=1)

        # Aplicar Motor de Decisão Estratégica v4.9
        df_final[["PRIORIDADE", "AÇÃO RECOMENDADA"]] = df_final.apply(
            lambda row: pd.Series(get_strategic_action_v6(row)), axis=1
        )

        # Auditoria v4.9 (OFICIAL)
        audit = {
            "TOTAL_TODOS": len(df_todos),
            "PARADOS_OFICIAL": parados_count_oficial,
            "VALIDADE_OFICIAL": validade_count_oficial,
            "RUPTURA": len(df_final[df_final["IS_RUPTURA"]]),
            "REPOSICAO": len(df_final[df_final["IS_REPOSICAO"]]),
            "OK": len(df_final[df_final["IS_OK"]]),
            "VALOR_TOTAL": df_final["VALOR VENDA ESTOQUE"].sum(),
            "CUSTO_TOTAL": df_final["CUSTO ESTOQUE"].sum(),
            "VALOR_PARADO": df_final[df_final["IS_PARADO"]]["VALOR VENDA ESTOQUE"].sum(),
            "CUSTO_PARADO": df_final[df_final["IS_PARADO"]]["CUSTO ESTOQUE"].sum(),
            "ACIMA_MERCADO_5PCT": len(df_final[df_final["DIFERENCA MERCADO %"] > 0.05]),
            "ACIMA_MERCADO_20PCT": len(df_final[df_final["DIFERENCA MERCADO %"] > 0.20]),
            "SEM_BENCHMARK": len(df_final[df_final["MEDIA CONCORRENCIA"] == 0]),
        }

        return (df_final, audit, df_todos), None
    except Exception as e:
        return None, f"Erro: {str(e)}"

# ─────────────────────────────────────────────
# FUNÇÕES DE EXPORTAÇÃO EXCEL
# ─────────────────────────────────────────────

def export_to_excel(df, sheet_name="Dados"):
    """Exporta DataFrame para Excel .xlsx"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output

def export_multiple_sheets(sheets_dict):
    """Exporta múltiplas abas para um único arquivo Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in sheets_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output

# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────

def main():
    st.markdown(f"""
    <div class="main-header">
        <div class="header-title">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h1> SOGAMAX | Análise Estratégica de Estoque</h1>
                <div class="audit-badge">CONFIABILIDADE OPERACIONAL • {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
            </div>
            <p style="color:#94a3b8; font-size:0.8rem; margin-top:5px;">Contagem Oficial, Filtros Dinâmicos, Exportação Excel</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    data, error = load_and_audit_v49()
    if error:
        st.error(error)
        return
    
    df, audit, df_todos = data

    # Sidebar
    with st.sidebar:
        st.markdown("<h3 style='color:#63b3ed'>Filtros Globais</h3>", unsafe_allow_html=True)
        sel_curva = st.multiselect("Curva ABC", sorted(df["CURVA"].dropna().unique().astype(str)))
        sel_marca = st.multiselect("Marca", sorted(df["MARCA"].dropna().unique().astype(str)))
        st.divider()
        st.markdown("#### Auditoria Oficial")
        st.caption(f"Total (TODOS OS PRODUTOS): {audit['TOTAL_TODOS']}")
        st.caption(f"Parados (OFICIAL): {audit['PARADOS_OFICIAL']}")
        st.caption(f"Validade Próxima (OFICIAL): {audit['VALIDADE_OFICIAL']}")
        st.caption(f"Em Ruptura: {audit['RUPTURA']}")
        st.caption(f"Sem Benchmark: {audit['SEM_BENCHMARK']}")

    df_f = df.copy()
    if sel_curva: df_f = df_f[df_f["CURVA"].isin(sel_curva)]
    if sel_marca: df_f = df_f[df_f["MARCA"].isin(sel_marca)]

    # Tabs - ADICIONADA ABA "TODOS OS PRODUTOS"
    t = st.tabs([" VISÃO EXECUTIVA", " PRODUTOS PARADOS ", " PRODUTOS OK", " MERCADO & PREÇO", " RUPTURA & REPOSIÇÃO", " VALIDADE", " TODOS OS PRODUTOS", " INSIGHTS", " AUDITORIA"])

    # 1. VISÃO EXECUTIVA
    with t[0]:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: metric_v49("Total Produtos", f"{audit['TOTAL_TODOS']}", "Base Completa")
        with c2: metric_v49("Produtos Parados", f"{audit['PARADOS_OFICIAL']}", "Aba Oficial", "#fc8181")
        with c3: metric_v49("Em Ruptura", f"{audit['RUPTURA']}", "Estoque 0 + Venda", "#f6ad55")
        with c4: metric_v49("Estoque Baixo", f"{audit['REPOSICAO']}", "Risco de Ruptura", "#f6e05e")
        with c5: metric_v49("Produtos OK", f"{audit['OK']}", "Giro Saudável", "#68d391")

        st.markdown("<br>", unsafe_allow_html=True)
        
        c_f1, c_f2, c_f3, c_f4 = st.columns(4)
        with c_f1: metric_v49("Valor Total Estoque", fmt_brl(audit['VALOR_TOTAL']), "Estoque × Preço")
        with c_f2: metric_v49("Custo Total Estoque", fmt_brl(audit['CUSTO_TOTAL']), "Estoque × Custo")
        with c_f3: metric_v49("Valor Parado (E*P)", fmt_brl(audit['VALOR_PARADO']), "Capital Imobilizado", "#fc8181")
        
        # Calcular margem potencial usando dados de TODOS OS PRODUTOS
        valor_venda_geral_temp = df_todos["ESTOQUE"].fillna(0).astype(float).mul(
            df_todos.get("VENDA SOGAMAX", df_todos.get("VENDA SOGAMAX", pd.Series(0))).fillna(0).astype(float)
        ).sum()
        custo_geral_temp = df_todos["ESTOQUE"].fillna(0).astype(float).mul(
            df_todos.get("CUSTO SOGAMAX ", df_todos.get("CUSTO SOGAMAX", pd.Series(0))).fillna(0).astype(float)
        ).sum()
        margem_geral = valor_venda_geral_temp - custo_geral_temp
        
        with c_f4: metric_v49("Margem Potencial", fmt_brl(margem_geral), "Lucro em Estoque", "#68d391")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # NOVOS CARDS FINANCEIROS - ESTOQUE GERAL
        c_geral1, c_geral2 = st.columns(2)
        
        # Card 1: Valor venda estoque geral
        valor_venda_geral = df_todos["ESTOQUE"].fillna(0).astype(float).mul(
            df_todos.get("VENDA SOGAMAX", df_todos.get("VENDA SOGAMAX", pd.Series(0))).fillna(0).astype(float)
        ).sum()
        with c_geral1:
            metric_v49("Valor Venda Estoque Geral", fmt_brl(valor_venda_geral), "Estoque × Venda Sogamax", "#63b3ed")
        
        # Card 2: Custo estoque geral
        custo_geral = df_todos["ESTOQUE"].fillna(0).astype(float).mul(
            df_todos.get("CUSTO SOGAMAX ", df_todos.get("CUSTO SOGAMAX", pd.Series(0))).fillna(0).astype(float)
        ).sum()
        with c_geral2:
            metric_v49("Custo Estoque Geral", fmt_brl(custo_geral), "Estoque × Custo Sogamax", "#a78bfa")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Alertas
        st.markdown(f"""
        <div class="no-giro-alert">
            <b> CONTAGEM OFICIAL:</b> Existem {audit['PARADOS_OFICIAL']} produtos classificados como parados na aba PRODUTOS PARADOS.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="price-alert">
            <b> COMPETITIVIDADE:</b> {audit['ACIMA_MERCADO_5PCT']} produtos acima do mercado (+5%). 
            Destes, {audit['ACIMA_MERCADO_20PCT']} FORA DO MERCADO (+20%).
        </div>
        """, unsafe_allow_html=True)
        
        col_l, col_r = st.columns(2)
        with col_l:
            fig = px.pie(df_f, names="CLASSIFICAÇÃO IA", title="Composição Estratégica do Estoque", hole=0.4)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        with col_r:
            top_m = df_f[df_f["IS_PARADO"]].groupby("MARCA")["VALOR VENDA ESTOQUE"].sum().nlargest(10).reset_index()
            fig_b = px.bar(top_m, x="VALOR VENDA ESTOQUE", y="MARCA", orientation='h', title="Top 10 Marcas com Capital Imobilizado")
            fig_b.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_b, use_container_width=True)

    # Função para renderizar tabelas com filtros e exportação
    def show_table_with_filters(df_table, title, tab_key, cols_extra=[]):
        st.markdown(f"### {title} ({len(df_table)} itens)")
        
        # Filtros locais
        st.markdown("**Filtros desta tabela:**")
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
        with col_f1:
            sel_marca_local = st.multiselect("Marca", sorted(df_table["MARCA"].dropna().unique().astype(str)), key=f"{tab_key}_marca")
        with col_f2:
            sel_curva_local = st.multiselect("Curva", sorted(df_table["CURVA"].dropna().unique().astype(str)), key=f"{tab_key}_curva")
        with col_f3:
            sel_prioridade = st.multiselect("Prioridade", sorted(df_table["PRIORIDADE"].dropna().unique().astype(str)), key=f"{tab_key}_prio")
        with col_f4:
            sel_classif = st.multiselect("Classificação IA", sorted(df_table["CLASSIFICAÇÃO IA"].dropna().unique().astype(str)), key=f"{tab_key}_classif")
        with col_f5:
            sel_status = st.multiselect("Status", sorted(df_table["STATUS DE ESTOQUE"].dropna().unique().astype(str)), key=f"{tab_key}_status")
        
        # Aplicar filtros locais
        df_filtered = df_table.copy()
        if sel_marca_local: df_filtered = df_filtered[df_filtered["MARCA"].isin(sel_marca_local)]
        if sel_curva_local: df_filtered = df_filtered[df_filtered["CURVA"].isin(sel_curva_local)]
        if sel_prioridade: df_filtered = df_filtered[df_filtered["PRIORIDADE"].isin(sel_prioridade)]
        if sel_classif: df_filtered = df_filtered[df_filtered["CLASSIFICAÇÃO IA"].isin(sel_classif)]
        if sel_status: df_filtered = df_filtered[df_filtered["STATUS DE ESTOQUE"].isin(sel_status)]
        
        # Preparar dados para exibição
        cols_base = ["ID", "EAN", "DESCRIÇÃO", "MARCA", "Grupo", "CURVA", "ESTOQUE", "VB 90", "DIAS DA ULTIMA VB", "VENDA SOGAMAX", "CUSTO SOGAMAX"]
        cols_final = cols_base + cols_extra + ["VALIDADE", "PRIORIDADE", "AÇÃO RECOMENDADA"]
        
        # Preparar dados para exibição
        cols_base = ["ID", "EAN", "DESCRIÇÃO", "MARCA", "Grupo", "CURVA", "ESTOQUE", "VB 90", "DIAS DA ULTIMA VB", "VENDA SOGAMAX", "CUSTO SOGAMAX"]
        cols_final = cols_base + cols_extra + ["VALIDADE", "PRIORIDADE", "AÇÃO RECOMENDADA"]

        # Manter apenas colunas existentes
        cols_existentes = [c for c in cols_final if c in df_filtered.columns]

        d = df_filtered[cols_existentes].copy()
        
        # Formatação de Moeda
        for c in ["VENDA SOGAMAX", "CUSTO SOGAMAX", "VALOR VENDA ESTOQUE", "SANTA CRUZ", "PROFARMA", "MEDIA CONCORRENCIA", "DIFERENCA R$"]:
            if c in d.columns:
                d[c] = d[c].apply(lambda x: fmt_concorrencia(x) if "CONCORRENCIA" in c or "SANTA" in c or "PROFARMA" in c else fmt_brl(x))
        
        # Formatação de Porcentagem
        if "DIFERENCA MERCADO %" in d.columns:
            d["DIFERENCA MERCADO %"] = d["DIFERENCA MERCADO %"].apply(fmt_pct)
            
        # Formatação de Validade
        d["VALIDADE"] = d["VALIDADE"].apply(lambda x: "SEM VALIDADE" if pd.isna(x) or str(x).strip() == "" else str(x)[:10])
        
        st.dataframe(d, hide_index=True, use_container_width=True)
        
        # Botão de exportação
        col_exp1, col_exp2 = st.columns([1, 4])
        with col_exp1:
            excel_data = export_to_excel(d, sheet_name=title[:31])
            st.download_button(
                label="📥 Baixar Excel",
                data=excel_data,
                file_name=f"SOGAMAX_{tab_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Abas com filtros e exportação
    with t[1]: 
        cols_parados = ["SANTA CRUZ", "PROFARMA", "MEDIA CONCORRENCIA", "DIFERENCA R$", "DIFERENCA MERCADO %", "VALOR VENDA ESTOQUE"]
        show_table_with_filters(df_f[df_f["IS_PARADO"]], "Produtos Parados (Aba Oficial)", "parados", cols_parados)
        
    with t[2]: 
        show_table_with_filters(df_f[df_f["IS_OK"]], "Produtos com Giro Saudável", "ok")
    
    with t[3]: 
        cols_mercado = ["SANTA CRUZ", "PROFARMA", "MEDIA CONCORRENCIA", "DIFERENCA MERCADO %"]
        df_acima = df_f[df_f["DIFERENCA MERCADO %"] > 0.05].sort_values("DIFERENCA MERCADO %", ascending=False)
        show_table_with_filters(df_acima, "Análise de Competitividade", "mercado", cols_mercado)
        
    with t[4]: 
        show_table_with_filters(df_f[df_f["IS_RUPTURA"] | df_f["IS_REPOSICAO"]], "Gestão de Ruptura e Reposição", "ruptura")
    
    with t[5]: 
        df_val = df_f[df_f["IS_VALIDADE"]].copy()
        show_table_with_filters(df_val, "Produtos com Validade Próxima (Aba Oficial)", "validade")
    
    # NOVA ABA: TODOS OS PRODUTOS - CONSULTA GERAL
    with t[6]:
        st.markdown(f"### Todos os Produtos - Consulta Geral ({len(df_todos)} itens)")
        
        # Filtros locais para Todos os Produtos
        st.markdown("**Filtros desta tabela:**")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            sel_marca_todos = st.multiselect("Marca", sorted(df_todos["MARCA"].dropna().unique().astype(str)), key="todos_marca")
        with col_f2:
            sel_curva_todos = st.multiselect("Curva", sorted(df_todos["CURVA"].dropna().unique().astype(str)), key="todos_curva")
        with col_f3:
            sel_grupo_todos = st.multiselect("Grupo", sorted(df_todos.get("Grupo", pd.Series()).dropna().unique().astype(str)), key="todos_grupo")
        with col_f4:
            sel_status_todos = st.multiselect("Status", sorted(df_todos.get("STATUS DE ESTOQUE", pd.Series()).dropna().unique().astype(str)), key="todos_status")
        
        # Aplicar filtros
        df_todos_filtered = df_todos.copy()
        if sel_marca_todos: df_todos_filtered = df_todos_filtered[df_todos_filtered["MARCA"].isin(sel_marca_todos)]
        if sel_curva_todos: df_todos_filtered = df_todos_filtered[df_todos_filtered["CURVA"].isin(sel_curva_todos)]
        if sel_grupo_todos: df_todos_filtered = df_todos_filtered[df_todos_filtered["Grupo"].isin(sel_grupo_todos)]
        if sel_status_todos: df_todos_filtered = df_todos_filtered[df_todos_filtered["STATUS DE ESTOQUE"].isin(sel_status_todos)]
        
        # Colunas esperadas para Todos os Produtos
        cols_todos = ["ID", "EAN", "DESCRIÇÃO", "MARCA", "Grupo", "ESTOQUE", "CURVA", "VB 90", "VALIDADE", "VENDA SOGAMAX", "CUSTO SOGAMAX ", "STATUS DE ESTOQUE", "ESTOQUE PARADO", "ALERTA"]
        
        # Verificar quais colunas existem
        cols_disponveis = [c for c in cols_todos if c in df_todos_filtered.columns]
        
        d_todos = df_todos_filtered[cols_disponveis].copy()
        
        # Formatação de Moeda
        for c in ["VENDA SOGAMAX", "VENDA SOGAMAX", "CUSTO SOGAMAX ", "CUSTO SOGAMAX"]:
            if c in d_todos.columns:
                d_todos[c] = d_todos[c].apply(fmt_brl)
        
        # Formatação de Validade
        if "VALIDADE" in d_todos.columns:
            d_todos["VALIDADE"] = d_todos["VALIDADE"].apply(lambda x: "SEM VALIDADE" if pd.isna(x) or str(x).strip() == "" else str(x)[:10])
        
        st.dataframe(d_todos, hide_index=True, use_container_width=True)
        
        # Botão de exportação
        col_exp1, col_exp2 = st.columns([1, 4])
        with col_exp1:
            excel_data = export_to_excel(d_todos, sheet_name="Todos os Produtos")
            st.download_button(
                label="📥 Baixar Excel",
                data=excel_data,
                file_name=f"SOGAMAX_TODOS_PRODUTOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with t[7]:
        st.markdown("### Insights Estratégicos")
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            st.markdown(f"""
            <div class="insight-card">
                <b>Capital Imobilizado:</b> {fmt_brl(audit['VALOR_PARADO'])} estão parados em {audit['PARADOS_OFICIAL']} produtos (aba oficial).
            </div>
            <div class="insight-card">
                <b>Risco de Ruptura:</b> {audit['RUPTURA']} itens estão com estoque zerado apesar de possuírem venda ativa.
            </div>
            """, unsafe_allow_html=True)
        with c_i2:
            st.markdown(f"""
            <div class="insight-card">
                <b>Validade Próxima:</b> {audit['VALIDADE_OFICIAL']} produtos requerem atenção especial por validade.
            </div>
            <div class="insight-card">
                <b>Eficiência de Giro:</b> {audit['OK']} produtos garantem o fluxo de caixa atual.
            </div>
            """, unsafe_allow_html=True)

    with t[8]:
        st.markdown("### Auditoria Técnica v5.0")
        
        # BLOCO EXPLICATIVO - COMO SÃO CALCULADOS OS INDICADORES
        st.markdown("####  Como são calculados os indicadores")
        st.markdown("""
        <div class="insight-card" style="background: rgba(59, 130, 246, 0.1); border-left-color: #3b82f6;">
        <b>Valor Total Estoque:</b> Soma de (Estoque × Preço de Venda Sogamax) de todos os produtos<br>
        <b>Custo Total Estoque:</b> Soma de (Estoque × Custo Sogamax) de todos os produtos<br>
        <b>Valor Parado:</b> Soma de (Estoque × Preço de Venda) apenas dos produtos parados (>90 dias sem venda)<br>
        <b>Margem Potencial:</b> Diferença entre Valor Total e Custo Total (lucro potencial do estoque)<br>
        <b>% Produtos Parados:</b> (Produtos parados / Total de produtos) × 100<br>
        <b>Ruptura:</b> Produtos com estoque = 0 E com venda nos últimos 90 dias (VB90 > 0)<br>
        <b>Estoque Baixo:</b> Produtos com estoque baixo E com presença de venda (risco de ruptura)<br>
        <b>Produtos OK:</b> Produtos com giro saudável (venda recente E estoque adequado)<br>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Resumo de auditoria
        audit_display = {
            "Total de Produtos (TODOS OS PRODUTOS)": audit['TOTAL_TODOS'],
            "Produtos Parados (OFICIAL)": audit['PARADOS_OFICIAL'],
            "Validade Próxima (OFICIAL)": audit['VALIDADE_OFICIAL'],
            "Em Ruptura": audit['RUPTURA'],
            "Estoque Baixo": audit['REPOSICAO'],
            "Produtos OK": audit['OK'],
            "Sem Benchmark": audit['SEM_BENCHMARK'],
            "Acima do Mercado (+5%)": audit['ACIMA_MERCADO_5PCT'],
            "Fora do Mercado (+20%)": audit['ACIMA_MERCADO_20PCT'],
        }
        
        st.json(audit_display)
        
        st.divider()
        
        st.markdown("####  Legenda de Prioridades")
        st.markdown("""
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
        <div class="insight-card" style="background: rgba(239, 68, 68, 0.1); border-left-color: #ef4444;">
        <b style="color: #ef4444;">Alta Prioridade</b><br>
        Requer ação imediata. Produtos com risco crítico (vencimento, fora do mercado, parado >365 dias).
        </div>
        <div class="insight-card" style="background: rgba(245, 158, 11, 0.1); border-left-color: #f59e0b;">
        <b style="color: #f59e0b;">Média Prioridade</b><br>
        Requer atenção. Produtos com problemas moderados (baixo giro, preço alto, estoque alto).
        </div>
        <div class="insight-card" style="background: rgba(16, 185, 129, 0.1); border-left-color: #10b981;">
        <b style="color: #10b981;">Baixa Prioridade</b><br>
        Monitorar. Produtos com giro saudável ou sem problemas imediatos.
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.markdown("#### Distribuição de Prioridades")
        priority_dist = df["PRIORIDADE"].value_counts().to_dict()
        st.json(priority_dist)
        
        st.divider()
        st.markdown("#### Exportação Completa")
        
        # Preparar abas para exportação completa
        sheets_dict = {
            "Parados": df[df["IS_PARADO"]].copy(),
            "OK": df[df["IS_OK"]].copy(),
            "Ruptura_Reposicao": df[df["IS_RUPTURA"] | df["IS_REPOSICAO"]].copy(),
            "Validade": df[df["IS_VALIDADE"]].copy(),
            "Auditoria": pd.DataFrame([audit_display]),
        }
        
        excel_completo = export_multiple_sheets(sheets_dict)
        st.download_button(
            label="📥 Baixar Excel Completo (Todas as Abas)",
            data=excel_completo,
            file_name=f"SOGAMAX_COMPLETO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def metric_v49(label, value, sub, color="#ffffff"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color}">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
