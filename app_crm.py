import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
from datetime import datetime, timedelta
import os

warnings.filterwarnings('ignore', category=UserWarning)

PT_MONTHS = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

def format_dt_pt(dt):
    if pd.isna(dt): return ""
    return f"{PT_MONTHS[dt.month]}/{str(dt.year)[2:]}"

CANAL_CORES = {
    'APP':         '#22c55e', # Verde principal
    'SITE':        '#16a34a', # Verde escuro
    'LOJA FISICA': '#64748b', # Cinza azulado
    'TELEVENDAS':  '#94a3b8', # Cinza claro
    'OUTROS':      '#1e293b'  # Escuro
}

st.set_page_config(page_title="Farmácias São João | CRM Analytics", page_icon="💊", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# DESIGN SYSTEM & CACHE
# ==========================================
def apply_custom_style():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        .stApp { background-color: #0f1117; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        div[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f2017 0%, #0f1117 100%) !important; border-right: 1px solid #1a3a28; }
        .metric-card { background: #1a2332; border: 1px solid #1e3a28; border-left: 3px solid #22c55e; border-radius: 10px; padding: 20px 24px; margin-bottom: 16px; }
        .metric-title { font-size: 12px; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; }
        .metric-value { font-size: 30px; font-weight: 700; color: #ffffff; margin: 8px 0; }
        .metric-delta.positive { color: #22c55e; font-size: 13px; font-weight: 600; }
        .metric-delta.negative { color: #ef4444; font-size: 13px; font-weight: 600; }
        h1, h2, h3 { color: #ffffff !important; font-weight: 700 !important; }
        div[data-testid="stButton"] > button { background-color: #16a34a !important; color: #ffffff !important; border-radius: 8px !important; font-weight: 600 !important; border: none !important; width: 100%; }
        div[data-testid="stButton"] > button:hover { background-color: #15803d !important; }
        button[data-baseweb="tab"][aria-selected="true"] div[data-testid="stMarkdownContainer"] p { color: #22c55e !important; font-weight: 600 !important; }
        div[data-baseweb="tab-highlight"] { background-color: #22c55e !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=43200)
def load_all_datasets():
    arquivos = ["df_v", "df_omni", "df_canal_ltv", "df_cohort", "df_demo", "df_vip",
                "df_novos_cac", "df_ltv_canal", "df_ltv_canal_mes", "df_novos_por_canal"]
    dfs = {}
    for arquivo in arquivos:
        caminho = f"dados/{arquivo}.csv"
        if os.path.exists(caminho):
            try: dfs[arquivo] = pd.read_csv(caminho)
            except: dfs[arquivo] = pd.DataFrame()
        else: dfs[arquivo] = pd.DataFrame()
    return dfs

# ==========================================
# CARGA E TRATAMENTO DE DADOS
# ==========================================
apply_custom_style()
dfs = load_all_datasets()

df_v = dfs.get("df_v", pd.DataFrame()).copy()
if not df_v.empty: df_v['DATA_VENDA'] = pd.to_datetime(df_v['DATA_VENDA'])

df_cohort = dfs.get("df_cohort", pd.DataFrame()).copy()
if not df_cohort.empty:
    if 'MES_COHORT' in df_cohort.columns: df_cohort['MES_COHORT'] = pd.to_datetime(df_cohort['MES_COHORT'])
    if 'MES_ATIVIDADE' in df_cohort.columns: df_cohort['MES_ATIVIDADE'] = pd.to_datetime(df_cohort['MES_ATIVIDADE'])

df_demo = dfs.get("df_demo", pd.DataFrame()).copy()
if not df_demo.empty:
    if 'MES_ATIVIDADE' in df_demo.columns: df_demo['MES_ATIVIDADE'] = pd.to_datetime(df_demo['MES_ATIVIDADE'])

df_omni = dfs.get("df_omni", pd.DataFrame()).copy()
if not df_omni.empty:
    if 'MES_ATIVIDADE' in df_omni.columns: df_omni['MES_ATIVIDADE'] = pd.to_datetime(df_omni['MES_ATIVIDADE'])

df_vip = dfs.get("df_vip", pd.DataFrame()).copy()
if not df_vip.empty: df_vip['ULTIMA_COMPRA'] = pd.to_datetime(df_vip['ULTIMA_COMPRA'])

df_novos_cac = dfs.get("df_novos_cac", pd.DataFrame()).copy()
if not df_novos_cac.empty:
    if 'MES_REFERENCIA' in df_novos_cac.columns: df_novos_cac['MES_REFERENCIA'] = pd.to_datetime(df_novos_cac['MES_REFERENCIA'])

df_ltv_canal_mes = dfs.get("df_ltv_canal_mes", pd.DataFrame()).copy()
if not df_ltv_canal_mes.empty:
    if 'MES_REFERENCIA' in df_ltv_canal_mes.columns: df_ltv_canal_mes['MES_REFERENCIA'] = pd.to_datetime(df_ltv_canal_mes['MES_REFERENCIA'])

df_novos_por_canal = dfs.get("df_novos_por_canal", pd.DataFrame()).copy()
if not df_novos_por_canal.empty:
    if 'MES_REFERENCIA' in df_novos_por_canal.columns: df_novos_por_canal['MES_REFERENCIA'] = pd.to_datetime(df_novos_por_canal['MES_REFERENCIA'])

    # --- budget de marketing (linha 5 da planilha: Total Realizado Midia) ---
    df_budget = pd.DataFrame()
    if os.path.exists("dados/df_budget.csv"):
        df_budget = pd.read_csv("dados/df_budget.csv")
        df_budget['MES_REFERENCIA'] = pd.to_datetime(df_budget['MES_REFERENCIA'])
        df_budget['CUSTO_TOTAL_MIDIA'] = pd.to_numeric(df_budget['CUSTO_TOTAL_MIDIA'], errors='coerce')

    return (df_v, dfs.get("df_omni", pd.DataFrame()), dfs.get("df_canal_ltv", pd.DataFrame()),
            df_cohort, dfs.get("df_demo", pd.DataFrame()), df_vip,
            df_novos_cac, df_ltv_canal, df_ltv_canal_mes, df_novos_por_canal, df_budget)

try:
    with st.spinner("Carregando inteligencia financeira..."):
        (df_v, df_omni, df_canal_ltv, df_cohort, df_demo, df_vip,
         df_novos_cac, df_ltv_canal, df_ltv_canal_mes, df_novos_por_canal, df_budget) = load_data()

    if df_v.empty or df_omni.empty:
        st.warning("Alguns dados estao sendo atualizados em segundo plano.")
except Exception as e:
    st.error(f"Erro: {e}")
    st.stop()


# ==========================================
# SIDEBAR / MENU & FILTROS DE DATA
# ==========================================
st.sidebar.markdown(
    '<div style="padding:16px 0 8px 0;">'
    '<span style="color:#22c55e;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">FARMACIAS SAO JOAO</span><br>'
    '<span style="color:#ffffff;font-size:22px;font-weight:700;">CRM Analytics</span>'
    '</div>',
    unsafe_allow_html=True
)

# Status de Saude dos Dados
with st.sidebar.expander("📊 Status do Banco Local", expanded=False):
    arquivos_nec = ["df_v", "df_omni", "df_cohort", "df_demo", "df_vip", "df_novos_cac"]
    for f in arquivos_nec:
        exists = os.path.exists(f"dados/{f}.csv")
        status = "🟢" if exists else "🔴"
        st.caption(f"{status} {f}.csv")

camada = st.sidebar.radio("Modulo", ["1. Visao Executiva", "2. Analise de Clientes", "3. Exportar VIPs", "4. Aquisicao & LTV"])
st.sidebar.divider()

st.sidebar.subheader("Parametros")
max_date = df_v['DATA_VENDA'].max() if not df_v.empty else datetime.today()
min_date = df_v['DATA_VENDA'].min() if not df_v.empty else datetime.today()

col_d1, col_d2 = st.sidebar.columns(2)
start_date = col_d1.date_input("De", value=max_date.replace(day=1), min_value=min_date, max_value=max_date)
end_date = col_d2.date_input("Ate", value=max_date, min_value=min_date, max_value=max_date)

canais = st.sidebar.multiselect("Canais", df_v['CANAL'].unique(), default=df_v['CANAL'].unique())
orcamento_marketing = st.sidebar.number_input("Orcamento de Marketing (R$)", value=50000, step=5000)

if st.sidebar.button("Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

df_v = df_v[df_v['CANAL'].isin(canais)]


# ==========================================
# LÓGICA YOY (YEAR OVER YEAR)
# ==========================================
def calc_delta(atual, anterior):
    if anterior == 0 or pd.isna(anterior): return 0.0
    return ((atual / anterior) - 1) * 100

def render_card(title, value, delta_pct, tooltip=""):
    d_class = "positive" if delta_pct >= 0 else "negative"
    sign = "+" if delta_pct >= 0 else ""
    return f'''
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta {d_class}">{sign}{delta_pct:.1f}% YoY</div>
        <div class="metric-footer">{tooltip}</div>
    </div>'''

start_date_ts = pd.to_datetime(start_date)
end_date_ts = pd.to_datetime(end_date)

df_atual = df_v[(df_v['DATA_VENDA'] >= start_date_ts) & (df_v['DATA_VENDA'] <= end_date_ts)]
start_date_ly = start_date_ts - pd.DateOffset(years=1)
end_date_ly = end_date_ts - pd.DateOffset(years=1)
df_anterior = df_v[(df_v['DATA_VENDA'] >= start_date_ly) & (df_v['DATA_VENDA'] <= end_date_ly)]


# ==========================================
# 1. CAMADA EXECUTIVA
# ==========================================
if camada == "1. Visao Executiva":
    st.markdown("<h1>Visao Executiva</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#64748b;font-size:14px;margin-top:-12px;margin-bottom:24px;'>Performance geral do periodo <b>{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}</b> comparado ao mesmo periodo de {start_date_ly.year}.</p>", unsafe_allow_html=True)
    
    # --- Cálculo de Deltas (Ano Anterior) ---
    receita_atual = df_atual['RECEITA_TOTAL'].sum()
    receita_anterior = df_anterior['RECEITA_TOTAL'].sum()
    delta_receita = ((receita_atual / receita_anterior) - 1) * 100 if receita_anterior > 0 else 0

    clientes_atual = df_atual['QTD_CLIENTES'].nunique()
    clientes_anterior = df_anterior['QTD_CLIENTES'].nunique()
    delta_clientes = ((clientes_atual / clientes_anterior) - 1) * 100 if clientes_anterior > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-title'>Receita Total</div>
            <div class='metric-value'>R$ {receita_atual:,.0f}</div>
            <div class='metric-delta {"positive" if delta_receita >= 0 else "negative"}'>
                {'▲' if delta_receita >= 0 else '▼'} {abs(delta_receita):.1f}% vs. ano ant.
            </div>
        </div>""", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-title'>Clientes Ativos</div>
            <div class='metric-value'>{clientes_atual:,.0f}</div>
            <div class='metric-delta {"positive" if delta_clientes >= 0 else "negative"}'>
                {'▲' if delta_clientes >= 0 else '▼'} {abs(delta_clientes):.1f}% vs. ano ant.
            </div>
        </div>""", unsafe_allow_html=True)

    p_at = df_atual['QTD_VENDAS'].sum()
    p_ant = df_anterior['QTD_VENDAS'].sum()
    
    ticket_medio_atual = receita_atual / p_at if p_at > 0 else 0
    ticket_medio_anterior = receita_anterior / p_ant if p_ant > 0 else 0
    delta_tm = ((ticket_medio_atual / ticket_medio_anterior) - 1) * 100 if ticket_medio_anterior > 0 else 0

    freq_atual = p_at / clientes_atual if clientes_atual > 0 else 0
    freq_anterior = p_ant / clientes_anterior if clientes_anterior > 0 else 0
    delta_freq = ((freq_atual / freq_anterior) - 1) * 100 if freq_anterior > 0 else 0

    with col3:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-title'>Ticket Medio</div>
            <div class='metric-value'>R$ {ticket_medio_atual:,.2f}</div>
            <div class='metric-delta {"positive" if delta_tm >= 0 else "negative"}'>
                {'▲' if delta_tm >= 0 else '▼'} {abs(delta_tm):.1f}% vs. ano ant.
            </div>
        </div>""", unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-title'>Frequencia</div>
            <div class='metric-value'>{freq_atual:,.2f}x</div>
            <div class='metric-delta {"positive" if delta_freq >= 0 else "negative"}'>
                {'▲' if delta_freq >= 0 else '▼'} {abs(delta_freq):.1f}% vs. ano ant.
            </div>
        </div>""", unsafe_allow_html=True)

    # Indicador de ultima atualizacao na sidebar
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Dados sincronizados em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h2>Tendencia de Receita por Mes</h2>", unsafe_allow_html=True)

    df_mensal = df_v.groupby(['ANO', 'MES'])['RECEITA_TOTAL'].sum().reset_index()
    st.markdown("<h2 style='font-size:20px;margin-bottom:0;'>Historico de Receita por Canal</h2>", unsafe_allow_html=True)
    st.caption(f"Evolucao diaria da receita bruta por canal de venda no periodo selecionado.")

    # Agrupando por dia e canal para garantir que o grafico de area funcione corretamente
    df_daily = df_atual.groupby(['DATA_VENDA', 'CANAL'])['RECEITA_TOTAL'].sum().reset_index()
    
    fig_hist = px.area(df_daily.sort_values('DATA_VENDA'), 
                       x='DATA_VENDA', y='RECEITA_TOTAL', color='CANAL', 
                       color_discrete_map=CANAL_CORES,
                       line_group='CANAL')
    
    fig_hist.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        xaxis=dict(title='', tickformat='%d/%m/%y', gridcolor='#1e293b'), 
        yaxis=dict(title='Receita (R$)', gridcolor='#1e293b'),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    st.plotly_chart(fig_hist, use_container_width=True)


# ==========================================
# 2. CAMADA ANALÍTICA
# ==========================================
elif camada == "2. Analise de Clientes":
    st.markdown("<h1>Analise de Clientes</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#64748b;font-size:14px;margin-top:-12px;margin-bottom:24px;'>Perfil de comportamento, demografia e retencao dos clientes ativos entre <b>{start_date.strftime('%d/%m/%y')} e {end_date.strftime('%d/%m/%y')}</b>.</p>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Novos vs Recorrentes", "🔄 Mix Omnichannel", "👥 Demografico", "🧬 Cohort"])

    with tab1:
        st.markdown("<h2 style='font-size:20px;'>Composicao da Base de Clientes</h2>", unsafe_allow_html=True)
        st.caption("Visao da base de clientes ativos dividida entre Novos (primeira compra no mes) e Recorrentes (historico completo).")
        # Conforme solicitado, este grafico ignora o filtro global e mostra TODO o historico
        df_cohort_full = df_cohort.copy()
        df_cohort_full['TIPO_CLIENTE'] = df_cohort_full['MESES_DESDE_COHORT'].apply(lambda x: 'Novo Cliente' if x == 0 else 'Recorrente')
        composicao_mes = df_cohort_full.groupby(['MES_ATIVIDADE', 'TIPO_CLIENTE'])['QTD_CLIENTES_ATIVOS'].sum().reset_index()

        if not composicao_mes.empty:
            composicao_mes['PERIODO'] = composicao_mes['MES_ATIVIDADE'].dt.strftime('%b/%y')
            fig_comp = px.bar(composicao_mes, x='PERIODO', y='QTD_CLIENTES_ATIVOS', color='TIPO_CLIENTE',
                               color_discrete_map={'Novo Cliente': '#22c55e', 'Recorrente': '#1e3a28'})
            fig_comp.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), barmode='stack',
                                   xaxis_title='', yaxis_title='Clientes Ativos')
            st.plotly_chart(fig_comp, use_container_width=True)

            novos_por_mes = df_cohort[df_cohort['MESES_DESDE_COHORT']==0].groupby('MES_COHORT')['QTD_CLIENTES_ATIVOS'].sum().reset_index()
            novos_mes_atual = novos_por_mes.iloc[-1]['QTD_CLIENTES_ATIVOS'] if not novos_por_mes.empty else 0
            cac = orcamento_marketing / novos_mes_atual if novos_mes_atual > 0 else 0

            cC1, cC2, cC3 = st.columns(3)
            cC1.markdown(render_card("Novos Clientes (Ult. Mes)", f"{novos_mes_atual:,.0f}", 0, "Cohort mais recente"), unsafe_allow_html=True)
            cC2.markdown(render_card("Investimento Marketing", f"R$ {orcamento_marketing:,.2f}", 0, "Parametro informado"), unsafe_allow_html=True)
            cC3.markdown(render_card("CAC Medio", f"R$ {cac:.2f}", 0, "Custo de Aquisicao"), unsafe_allow_html=True)

    with tab2:
        st.markdown("<h2 style='font-size:20px;'>Comportamento Omnichannel</h2>", unsafe_allow_html=True)
        st.caption("Participacao dos perfis de compra na receita total e LTV (Lifetime Value) historico.")
        if not df_omni.empty:
            # Filtro de data para Omni
            if 'MES_ATIVIDADE' in df_omni.columns:
                df_o_f = df_omni[(df_omni['MES_ATIVIDADE'] >= start_date_ts) & (df_omni['MES_ATIVIDADE'] <= end_date_ts)].copy()
                # Re-agrupar para somar os meses selecionados
                df_omni_plot = df_o_f.groupby('PERFIL_OMNI').agg({'QTD_CLIENTES':'sum', 'RECEITA_TOTAL':'sum', 'QTD_VENDAS':'sum'}).reset_index()
            else:
                st.warning("⚠️ Dados Omnichannel desatualizados. Rode '01_Sincronizar_Total.bat' para habilitar filtros.")
                df_omni_plot = df_omni.groupby('PERFIL_OMNI').agg({'QTD_CLIENTES':'sum', 'RECEITA_TOTAL':'sum', 'QTD_VENDAS':'sum'}).reset_index()

            if not df_omni_plot.empty:
                df_omni_plot['LTV'] = df_omni_plot['RECEITA_TOTAL'] / df_omni_plot['QTD_CLIENTES']
                cO1, cO2 = st.columns(2)
                with cO1:
                    fig_o1 = px.pie(df_omni_plot, names='PERFIL_OMNI', values='RECEITA_TOTAL', hole=0.6,
                                    color_discrete_sequence=['#22c55e', '#16a34a', '#64748b', '#1e293b'])
                    fig_o1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'))
                    st.plotly_chart(fig_o1, use_container_width=True)

                with cO2:
                    fig_o2 = px.bar(df_omni_plot, x='PERFIL_OMNI', y='LTV', color='PERFIL_OMNI', text_auto='.2f',
                                    color_discrete_sequence=['#22c55e', '#16a34a', '#64748b', '#1e293b'])
                    fig_o2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), showlegend=False)
                    st.plotly_chart(fig_o2, use_container_width=True)
            else:
                st.info("Sem dados Omnichannel para o periodo selecionado.")

    with tab3:
        st.markdown("<h2 style='font-size:20px;'>Perfil Demografico dos Clientes</h2>", unsafe_allow_html=True)
        st.caption("Distribuicao de genero e faixa etaria da base de clientes ativos no periodo.")
        if not df_demo.empty:
            # Tratamento de erro caso a coluna nova ainda nao tenha sido baixada pelo extrator
            if 'MES_ATIVIDADE' in df_demo.columns:
                # Filtro de data para demografico
                df_demo_f = df_demo[(df_demo['MES_ATIVIDADE'] >= start_date_ts) & (df_demo['MES_ATIVIDADE'] <= end_date_ts)].copy()
                df_demo_valid = df_demo_f[(df_demo_f['IDADE'] >= 18) & (df_demo_f['IDADE'] <= 100)]
                
                if not df_demo_valid.empty:
                    cP1, cP2 = st.columns(2)
                    with cP1:
                        df_sex_agg = df_demo_valid.groupby('SEXO')['COUNT'].sum().reset_index()
                        fig_sex = px.pie(df_sex_agg, names='SEXO', values='COUNT', hole=0.6, color_discrete_sequence=['#22c55e', '#16a34a', '#64748b'])
                        fig_sex.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'))
                        st.plotly_chart(fig_sex, use_container_width=True)

                    with cP2:
                        df_age_agg = df_demo_valid.groupby('IDADE')['COUNT'].sum().reset_index()
                        fig_age = px.bar(df_age_agg, x='IDADE', y='COUNT', color_discrete_sequence=['#22c55e'])
                        fig_age.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'))
                        st.plotly_chart(fig_age, use_container_width=True)
                else:
                    st.info("Sem dados demograficos para o periodo selecionado.")
            else:
                st.warning("⚠️ Estrutura de dados antiga detectada. Rode o arquivo '01_Sincronizar_Total.bat' para habilitar os filtros demograficos.")
                # Mostra o snapshot antigo como fallback
                df_demo_valid = df_demo[(df_demo['IDADE'] >= 18) & (df_demo['IDADE'] <= 100)]
                cP1, cP2 = st.columns(2)
                with cP1:
                    df_sex_agg = df_demo_valid.groupby('SEXO')['COUNT'].sum().reset_index()
                    fig_sex = px.pie(df_sex_agg, names='SEXO', values='COUNT', hole=0.6, color_discrete_sequence=['#22c55e', '#16a34a', '#64748b'])
                    st.plotly_chart(fig_sex, use_container_width=True)
                with cP2:
                    df_age_agg = df_demo_valid.groupby('IDADE')['COUNT'].sum().reset_index()
                    fig_age = px.bar(df_age_agg, x='IDADE', y='COUNT', color_discrete_sequence=['#22c55e'])
                    st.plotly_chart(fig_age, use_container_width=True)

    with tab4:
        st.markdown("<h2 style='font-size:20px;'>Matriz de Retencao (Cohort)</h2>", unsafe_allow_html=True)
        st.caption("Percentual de clientes que voltam a comprar nos meses seguintes a sua primeira compra (Aquisicao).")
        df_c_filter = df_cohort[(df_cohort['MES_COHORT'] >= start_date_ts) & (df_cohort['MES_COHORT'] <= end_date_ts)]
        if not df_c_filter.empty:
            c_sizes = df_c_filter[df_c_filter['MESES_DESDE_COHORT']==0].set_index('MES_COHORT')['QTD_CLIENTES_ATIVOS']
            c_piv = df_c_filter.pivot(index='MES_COHORT', columns='MESES_DESDE_COHORT', values='QTD_CLIENTES_ATIVOS')
            r_mat = c_piv.divide(c_sizes, axis=0) * 100
            r_mat.index = r_mat.index.strftime('%Y-%m')

            fig_c = go.Figure(data=go.Heatmap(z=r_mat.values, x=r_mat.columns, y=r_mat.index,
                                              colorscale=['#0f1117', '#22c55e'], text=r_mat.round(1).astype(str)+'%',
                                              texttemplate="%{text}", hoverongaps=False))
            fig_c.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'),
                                xaxis_title='Meses desde a entrada (0 = mes de aquisicao)', yaxis_autorange='reversed', height=600)
            st.plotly_chart(fig_c, use_container_width=True)


# ==========================================
# 3. CAMADA ACIONÁVEL
# ==========================================
elif camada == "3. Exportar VIPs":
    st.markdown("<h1>Exportacao: Clientes VIP</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;font-size:14px;margin-top:-12px;margin-bottom:24px;'>Top 500 clientes por receita gerada no periodo. Use para campanhas de retencao e fidelizacao.</p>", unsafe_allow_html=True)
    if not df_vip.empty:
        df_vip['TICKET_MEDIO'] = df_vip['RECEITA'] / df_vip['FREQUENCIA']
        df_vip['ULTIMA_COMPRA'] = df_vip['ULTIMA_COMPRA'].dt.strftime('%d/%m/%Y')

        st.dataframe(df_vip.style.format({"RECEITA": "R$ {:.2f}", "TICKET_MEDIO": "R$ {:.2f}"}), use_container_width=True)

        csv = df_vip.to_csv(index=False).encode('utf-8')
        st.download_button(label="Exportar Lista (CSV)", data=csv, file_name='clientes_vip.csv', mime='text/csv')


# ==========================================
# 4. ACQUISITION & LTV
# ==========================================
elif camada == "4. Aquisicao & LTV":
    st.markdown("<h1>Aquisicao de Clientes & LTV</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#64748b;font-size:14px;margin-top:-12px;margin-bottom:24px;'>Analise do custo de aquisicao (CAC) e o valor gerado por cada canal entre <b>{start_date.strftime('%B/%Y')} e {end_date.strftime('%B/%Y')}</b>.</p>", unsafe_allow_html=True)

    st.markdown("<h2 style='font-size:20px;margin-bottom:8px;'>Investimento em Marketing (Mídia)</h2>", unsafe_allow_html=True)
    st.caption("Insira os valores investidos por mes para calcular o CAC real. Os valores sao salvos localmente.")

    # Monta tabela de edicao com TODOS os meses presentes em df_novos_cac
    if not df_novos_cac.empty:
        meses_todos = df_novos_cac[['MES_REFERENCIA']].copy()
        meses_todos = meses_todos[meses_todos['MES_REFERENCIA'] >= pd.Timestamp('2025-10-01')] # Foco no periodo recente
        meses_todos = meses_todos.sort_values('MES_REFERENCIA')

        # Junta com budget carregado do CSV
        meses_todos = meses_todos.merge(df_budget[['MES_REFERENCIA','CUSTO_TOTAL_MIDIA']], on='MES_REFERENCIA', how='left')
        meses_todos = meses_todos.drop_duplicates('MES_REFERENCIA')
        
        meses_todos['Mes'] = meses_todos['MES_REFERENCIA'].apply(format_dt_pt)
        # Garante que nao apareca "None" visualmente
        df_editor = meses_todos[['Mes', 'CUSTO_TOTAL_MIDIA']].copy()
        df_editor.columns = ['Mes', 'Investimento (R$)']

        edited = st.data_editor(
            df_editor,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Mes":               st.column_config.TextColumn("Mes", disabled=True, width="small"),
                "Investimento (R$)": st.column_config.NumberColumn(
                    "Investimento Total Midia (R$)",
                    help="Linha 5 da planilha — Total Realizado Midia. Preencha os meses em branco.",
                    min_value=0, step=1000, format="R$ %.0f"
                ),
            },
            key="editor_budget"
        )

        # Reconstroi df_budget com os valores editados (incluindo novos meses preenchidos)
        meses_todos['CUSTO_TOTAL_MIDIA'] = edited['Investimento (R$)'].values
        df_budget_editado = meses_todos[['MES_REFERENCIA', 'CUSTO_TOTAL_MIDIA']].copy()
    else:
        df_budget_editado = df_budget.copy() if not df_budget.empty else pd.DataFrame(columns=['MES_REFERENCIA','CUSTO_TOTAL_MIDIA'])

    st.markdown("---")

    # =========================================
    # SECAO 1: CLIENTES NOVOS POR MES
    # =========================================
    st.markdown("<h2 style='font-size:20px;'>Performance de Aquisicao e CAC</h2>", unsafe_allow_html=True)
    st.caption("Comparativo entre a entrada de Novos Clientes e o custo por cliente adquirido (CAC).")

    if not df_novos_cac.empty:
        df_nc = df_novos_cac.copy()
        # Filtra para mostrar apenas de Set/25 em diante para focar no periodo relevante
        df_nc = df_nc[df_nc['MES_REFERENCIA'] >= pd.Timestamp('2025-09-01')]
        df_nc = df_nc[df_nc['MES_REFERENCIA'] < pd.Timestamp.now().replace(day=1)]
        df_nc['PERIODO'] = df_nc['MES_REFERENCIA'].apply(format_dt_pt)

        # Junta com budget EDITADO pelo usuario na tabela acima
        if not df_budget_editado.empty:
            df_nc = df_nc.merge(df_budget_editado[['MES_REFERENCIA','CUSTO_TOTAL_MIDIA']], on='MES_REFERENCIA', how='left')
        else:
            df_nc['CUSTO_TOTAL_MIDIA'] = pd.NA

        # CAC = Total Realizado Midia / Novos Clientes no mes
        df_nc['CAC'] = df_nc['CUSTO_TOTAL_MIDIA'] / df_nc['QTD_CLIENTES_NOVOS'].replace(0, pd.NA)

        # KPIs do ultimo mes com budget disponivel
        df_nc_com_budget = df_nc.dropna(subset=['CUSTO_TOTAL_MIDIA'])
        if not df_nc_com_budget.empty:
            ultimo      = df_nc_com_budget.iloc[-1]
            penultimo   = df_nc_com_budget.iloc[-2] if len(df_nc_com_budget) >= 2 else None
        else:
            ultimo    = df_nc.iloc[-1]
            penultimo = df_nc.iloc[-2] if len(df_nc) >= 2 else None

        novos_atual   = int(ultimo['QTD_CLIENTES_NOVOS'])
        novos_ant     = int(penultimo['QTD_CLIENTES_NOVOS']) if penultimo is not None else 0
        ytd_atual     = int(df_nc.iloc[-1]['NOVOS_CLIENTES_YTD'])
        budget_ultimo = ultimo['CUSTO_TOTAL_MIDIA'] if pd.notna(ultimo.get('CUSTO_TOTAL_MIDIA')) else None
        cac_ultimo    = ultimo['CAC'] if pd.notna(ultimo.get('CAC')) else None
        delta_novos   = calc_delta(novos_atual, novos_ant)

        kA, kB, kC, kD = st.columns(4)
        kA.markdown(render_card(
            "Novos Clientes (Ult. Mes com Budget)",
            f"{novos_atual:,.0f}",
            delta_novos,
            f"vs {penultimo['PERIODO'] if penultimo is not None else ''}"
        ), unsafe_allow_html=True)
        kB.markdown(render_card(
            "Novos Clientes YTD",
            f"{ytd_atual:,.0f}",
            0,
            "Acumulado no ano corrente"
        ), unsafe_allow_html=True)
        kC.markdown(render_card(
            "Total Realizado Midia (Ult. Mes)",
            f"R$ {budget_ultimo:,.0f}" if budget_ultimo is not None else "Sem dado",
            0,
            "Linha 5 da planilha de midia"
        ), unsafe_allow_html=True)
        kD.markdown(render_card(
            "CAC (Custo por Novo Cliente)",
            f"R$ {cac_ultimo:,.2f}" if cac_ultimo is not None else "Sem dado",
            0,
            "Total Midia / Novos Clientes no mes"
        ), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Aviso sobre meses recentes sem budget
        df_recent = df_nc[df_nc['MES_REFERENCIA'] >= pd.Timestamp('2025-12-01')]
        meses_sem = df_recent[df_recent['CUSTO_TOTAL_MIDIA'].isna()]['PERIODO'].tolist()
        if meses_sem:
            st.warning(f"⚠️ Preencha o investimento para: {', '.join(meses_sem)} na tabela acima para ver o CAC.")

        fig_nc = go.Figure()
        fig_nc.add_trace(go.Bar(
            x=df_nc['PERIODO'], y=df_nc['QTD_CLIENTES_NOVOS'],
            name='Novos Clientes', marker_color='#22c55e',
            text=df_nc['QTD_CLIENTES_NOVOS'].apply(lambda v: f"{v:,.0f}"),
            textposition='outside'
        ))
        fig_nc.add_trace(go.Scatter(
            x=df_nc['PERIODO'], y=df_nc['CAC'],
            name='CAC (R$) — linha 5', yaxis='y2',
            mode='lines+markers',
            line=dict(color='#ef4444', width=2),
            marker=dict(size=7, symbol='circle')
        ))
        fig_nc.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#eaecef'),
            yaxis=dict(title='Novos Clientes', gridcolor='#2b3139'),
            yaxis2=dict(title='CAC (R$)', overlaying='y', side='right', gridcolor='rgba(0,0,0,0)', range=[0, df_nc['CAC'].max() * 1.2 if not df_nc['CAC'].empty else 10]),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis_title='', height=420
        )
        st.plotly_chart(fig_nc, use_container_width=True)

        # Tabela detalhada
        with st.expander("Ver tabela detalhada de novos clientes"):
            df_show = df_nc[['PERIODO', 'QTD_CLIENTES_NOVOS', 'NOVOS_CLIENTES_YTD', 'CAC']].copy()
            df_show.columns = ['Periodo', 'Novos Clientes', 'Acumulado YTD', 'CAC (R$)']
            df_show['CAC (R$)'] = df_show['CAC (R$)'].apply(lambda v: f"R$ {v:,.2f}" if pd.notna(v) else '-')
            df_show['Novos Clientes'] = df_show['Novos Clientes'].apply(lambda v: f"{v:,.0f}")
            df_show['Acumulado YTD'] = df_show['Acumulado YTD'].apply(lambda v: f"{v:,.0f}")
            st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.warning("Dados de novos clientes nao encontrados. Execute o extrator.")

    st.markdown("---")

    # =========================================
    # SECAO 2: LTV E FREQUENCIA POR CANAL
    # =========================================
    st.markdown("<h2>2. LTV e Frequencia por Canal</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#707a8a;font-size:13px;'>LTV = Receita total acumulada do cliente / N clientes do canal. "
        "Frequencia = media de compras por cliente.</p>",
        unsafe_allow_html=True
    )

    if not df_ltv_canal.empty:
        df_lc = df_ltv_canal.copy()
        df_lc['COR'] = df_lc['CANAL'].map(CANAL_CORES).fillna('#707a8a')

        cL1, cL2, cL3 = st.columns(3)

        with cL1:
            st.markdown("<h3 style='font-size:16px;'>LTV Medio por Canal</h3>", unsafe_allow_html=True)
            fig_ltv = go.Figure(go.Bar(
                x=df_lc['CANAL'], y=df_lc['LTV_MEDIO_CLIENTE'],
                marker_color=df_lc['COR'],
                text=df_lc['LTV_MEDIO_CLIENTE'].apply(lambda v: f"R$ {v:,.0f}"),
                textposition='outside'
            ))
            fig_ltv.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#eaecef'), showlegend=False,
                yaxis=dict(gridcolor='#2b3139'), xaxis_title='', yaxis_title='R$', height=320
            )
            st.plotly_chart(fig_ltv, use_container_width=True)

        with cL2:
            st.markdown("<h3 style='font-size:16px;'>Frequencia Media por Canal</h3>", unsafe_allow_html=True)
            fig_freq = go.Figure(go.Bar(
                x=df_lc['CANAL'], y=df_lc['FREQUENCIA_MEDIA'],
                marker_color=df_lc['COR'],
                text=df_lc['FREQUENCIA_MEDIA'].apply(lambda v: f"{v:.2f}x"),
                textposition='outside'
            ))
            fig_freq.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#eaecef'), showlegend=False,
                yaxis=dict(gridcolor='#2b3139'), xaxis_title='', yaxis_title='Compras/Cliente', height=320
            )
            st.plotly_chart(fig_freq, use_container_width=True)

        with cL3:
            st.markdown("<h3 style='font-size:16px;'>Ticket Medio por Canal</h3>", unsafe_allow_html=True)
            fig_tm = go.Figure(go.Bar(
                x=df_lc['CANAL'], y=df_lc['TICKET_MEDIO'],
                marker_color=df_lc['COR'],
                text=df_lc['TICKET_MEDIO'].apply(lambda v: f"R$ {v:.2f}"),
                textposition='outside'
            ))
            fig_tm.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#eaecef'), showlegend=False,
                yaxis=dict(gridcolor='#2b3139'), xaxis_title='', yaxis_title='R$', height=320
            )
            st.plotly_chart(fig_tm, use_container_width=True)

        # Tabela resumo
        st.markdown("<h3 style='font-size:16px;'>Resumo Consolidado por Canal</h3>", unsafe_allow_html=True)
        df_tab = df_lc[['CANAL', 'QTD_CLIENTES_UNICOS', 'QTD_COMPRAS', 'RECEITA_TOTAL',
                         'LTV_MEDIO_CLIENTE', 'FREQUENCIA_MEDIA', 'TICKET_MEDIO']].copy()
        df_tab.columns = ['Canal', 'Clientes Unicos', 'Total Compras', 'Receita Total',
                          'LTV Medio (R$)', 'Frequencia Media', 'Ticket Medio (R$)']
        # calcula share
        df_tab['Share Receita (%)'] = (df_tab['Receita Total'] / df_tab['Receita Total'].sum() * 100).round(1)
        df_tab['Receita Total']    = df_tab['Receita Total'].apply(lambda v: f"R$ {v:,.0f}")
        df_tab['LTV Medio (R$)']   = df_tab['LTV Medio (R$)'].apply(lambda v: f"R$ {v:,.2f}")
        df_tab['Ticket Medio (R$)']= df_tab['Ticket Medio (R$)'].apply(lambda v: f"R$ {v:,.2f}")
        df_tab['Frequencia Media'] = df_tab['Frequencia Media'].apply(lambda v: f"{v:.2f}x")
        df_tab['Share Receita (%)']= df_tab['Share Receita (%)'].apply(lambda v: f"{v:.1f}%")
        st.dataframe(df_tab, use_container_width=True, hide_index=True)

    st.markdown("---")

    # =========================================
    # SECAO 3: EVOLUCAO MENSAL DO LTV POR CANAL
    # =========================================
    st.markdown("<h2 style='font-size:20px;'>LTV e Frequencia por Canal de Entrada</h2>", unsafe_allow_html=True)
    st.caption("Metricas de valor acumulado (LTV) e recompra dos clientes baseadas no canal da primeira compra.")

    if not df_ltv_canal_mes.empty:
        df_lm = df_ltv_canal_mes.copy()
        df_lm = df_lm[df_lm['MES_REFERENCIA'] < pd.Timestamp.now().replace(day=1)]
        df_lm['PERIODO'] = df_lm['MES_REFERENCIA'].dt.strftime('%b/%y')

        metric_opcao = st.selectbox(
            "Metrica a visualizar:",
            ['RECEITA_MEDIA_POR_CLIENTE', 'FREQUENCIA_MEDIA', 'TICKET_MEDIO'],
            format_func=lambda x: {
                'RECEITA_MEDIA_POR_CLIENTE': 'LTV Mensal (Receita Media/Cliente)',
                'FREQUENCIA_MEDIA':          'Frequencia Media (Compras/Cliente)',
                'TICKET_MEDIO':              'Ticket Medio por Compra'
            }[x],
            key="sel_metric_ltv"
        )

        canais_ltv = [c for c in df_lm['CANAL'].unique() if c != 'OUTROS']
        CANAL_CORES_LTV = {
            'APP':         '#fcd535',
            'SITE':        '#0ecb81',
            'LOJA FISICA': '#3498db',
            'TELEVENDAS':  '#9b59b6',
        }

        fig_ev = go.Figure()
        for canal in canais_ltv:
            df_c = df_lm[df_lm['CANAL'] == canal].sort_values('MES_REFERENCIA')
            fig_ev.add_trace(go.Scatter(
                x=df_c['PERIODO'], y=df_c[metric_opcao],
                name=canal,
                mode='lines+markers',
                line=dict(color=CANAL_CORES_LTV.get(canal, '#707a8a'), width=2),
                marker=dict(size=5)
            ))
        fig_ev.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#eaecef'),
            yaxis=dict(gridcolor='#2b3139'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis_title='', height=400
        )
        st.plotly_chart(fig_ev, use_container_width=True)

    st.markdown("---")

    # =========================================
    # SECAO 4: NOVOS CLIENTES POR CANAL DE AQUISICAO
    # =========================================
    st.markdown("<h2>4. Novos Clientes por Canal de Aquisicao</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#707a8a;font-size:13px;'>Canal em que o cliente realizou a PRIMEIRA compra.</p>",
        unsafe_allow_html=True
    )

    if not df_novos_por_canal.empty:
        df_np = df_novos_por_canal.copy()
        df_np = df_np[df_np['MES_REFERENCIA'] < pd.Timestamp.now().replace(day=1)]
        df_np['PERIODO'] = df_np['MES_REFERENCIA'].dt.strftime('%b/%y')
        df_np_filt = df_np[df_np['CANAL'] != 'OUTROS']

        fig_np = px.bar(
            df_np_filt, x='PERIODO', y='QTD_NOVOS_CLIENTES', color='CANAL',
            barmode='stack',
            color_discrete_map=CANAL_CORES_LTV,
            text_auto=True
        )
        fig_np.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#eaecef'),
            yaxis=dict(gridcolor='#2b3139', title='Novos Clientes'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis_title='', height=400
        )
        st.plotly_chart(fig_np, use_container_width=True)
