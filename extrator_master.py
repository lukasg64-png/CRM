"""
EXTRATOR MASTER CRM - FARMÁCIAS SÃO JOÃO
Consolida todas as queries necessárias para o Dashboard CRM:
1. Visão Executiva (Receita, Clientes, Ticket Médio, Frequência)
2. Análise de Clientes (Omni, Cohort, Demográfico)
3. Exportação VIP (Top 500)
4. Aquisição & LTV (Novos Clientes, CAC, LTV por Canal)

Conexão: ODBC DSN=SNOWFLAKE_FSJ
"""
import pyodbc
import pandas as pd
import os
import sys
from datetime import datetime

# CONFIGURAÇÕES
DSN = "SNOWFLAKE_FSJ"
DATA_INICIO = "2025-01-01"
OUTPUT_DIR = "dados"

# DEFINIÇÃO DAS QUERIES PADRONIZADAS
QUERIES = {
    # 1. Visão Geral de Vendas (Diário/Canal)
    "df_v": f"""
        WITH VENDAS AS (
            SELECT VENDA_ID, CPF_CNPJ, VALOR_TOTAL, INCLUSAO_DATA,
                CASE
                    WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega') THEN 'APP'
                    WHEN TIPO_VENDA_DESCRICAO IN ('SITE', 'SITE Tele Entrega') THEN 'SITE'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 'LOJA FÍSICA'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Tele Entrega', 'Tele Encaminhada Lojas', 'Tele Vizinhança', 'Venda Tele Entrega Central') THEN 'TELEVENDAS'
                    ELSE 'OUTROS'
                END AS CANAL
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
            WHERE INCLUSAO_DATA >= '{DATA_INICIO}' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
        )
        SELECT 
            DATE(INCLUSAO_DATA) AS DATA_VENDA, 
            YEAR(INCLUSAO_DATA) AS ANO, 
            MONTH(INCLUSAO_DATA) AS MES, 
            DAY(INCLUSAO_DATA) AS DIA,
            CANAL, 
            COUNT(DISTINCT VENDA_ID) AS QTD_VENDAS, 
            COUNT(DISTINCT CPF_CNPJ) AS QTD_CLIENTES, 
            SUM(VALOR_TOTAL) AS RECEITA_TOTAL
        FROM VENDAS 
        GROUP BY 1, 2, 3, 4, 5
    """,

    # 2. Perfil Omni
    "df_omni": f"""
        WITH COMPRAS_CANAIS AS (
            SELECT CPF_CNPJ,
                MAX(CASE WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 1 ELSE 0 END) AS COMPROU_LOJA,
                MAX(CASE WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega', 'SITE', 'SITE Tele Entrega') THEN 1 ELSE 0 END) AS COMPROU_DIGITAL,
                COUNT(DISTINCT VENDA_ID) AS QTD_VENDAS, SUM(VALOR_TOTAL) AS RECEITA
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
            WHERE INCLUSAO_DATA >= '{DATA_INICIO}' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
            GROUP BY CPF_CNPJ
        )
        SELECT 
            CASE 
                WHEN COMPROU_LOJA = 1 AND COMPROU_DIGITAL = 1 THEN 'Omni (Loja + Digital)' 
                WHEN COMPROU_LOJA = 1 AND COMPROU_DIGITAL = 0 THEN 'Somente Loja Física' 
                WHEN COMPROU_LOJA = 0 AND COMPROU_DIGITAL = 1 THEN 'Somente Canais Digitais' 
                ELSE 'Outros' 
            END AS PERFIL_OMNI,
            COUNT(CPF_CNPJ) AS QTD_CLIENTES, 
            SUM(QTD_VENDAS) AS QTD_VENDAS, 
            SUM(RECEITA) AS RECEITA_TOTAL
        FROM COMPRAS_CANAIS GROUP BY 1
    """,

    # 3. LTV Consolidado por Canal
    "df_ltv_canal": f"""
        WITH VENDAS_CANAL AS (
            SELECT CPF_CNPJ,
                CASE
                    WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega') THEN 'APP'
                    WHEN TIPO_VENDA_DESCRICAO IN ('SITE', 'SITE Tele Entrega') THEN 'SITE'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 'LOJA FÍSICA'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Tele Entrega', 'Tele Entrega Central') THEN 'TELEVENDAS'
                    ELSE 'OUTROS'
                END AS CANAL,
                COUNT(DISTINCT VENDA_ID) AS QTD_VENDAS, SUM(VALOR_TOTAL) AS RECEITA
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
            WHERE INCLUSAO_DATA >= '{DATA_INICIO}' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
            GROUP BY CPF_CNPJ, CANAL
        )
        SELECT 
            CANAL, 
            COUNT(CPF_CNPJ) AS QTD_CLIENTES_UNICOS, 
            SUM(QTD_VENDAS) AS QTD_COMPRAS, 
            SUM(RECEITA) AS RECEITA_TOTAL,
            ROUND(SUM(RECEITA) / NULLIF(COUNT(CPF_CNPJ), 0), 2) AS LTV_MEDIO_CLIENTE,
            ROUND(SUM(QTD_VENDAS) / NULLIF(COUNT(CPF_CNPJ), 0), 2) AS FREQUENCIA_MEDIA,
            ROUND(SUM(RECEITA) / NULLIF(SUM(QTD_VENDAS), 0), 2) AS TICKET_MEDIO
        FROM VENDAS_CANAL GROUP BY CANAL
    """,

    # 4. Cohort de Retenção
    "df_cohort": f"""
        WITH PRIMEIRA_COMPRA AS (
            SELECT CPF_CNPJ, DATE_TRUNC('MONTH', MIN(INCLUSAO_DATA)) AS MES_COHORT
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS WHERE IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL GROUP BY CPF_CNPJ
        ),
        COMPRAS_ATIVAS AS (
            SELECT CPF_CNPJ, DATE_TRUNC('MONTH', INCLUSAO_DATA) AS MES_ATIVIDADE
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS WHERE INCLUSAO_DATA >= '{DATA_INICIO}' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL GROUP BY CPF_CNPJ, DATE_TRUNC('MONTH', INCLUSAO_DATA)
        )
        SELECT P.MES_COHORT, C.MES_ATIVIDADE, DATEDIFF('MONTH', P.MES_COHORT, C.MES_ATIVIDADE) AS MESES_DESDE_COHORT, COUNT(DISTINCT C.CPF_CNPJ) AS QTD_CLIENTES_ATIVOS
        FROM PRIMEIRA_COMPRA P JOIN COMPRAS_ATIVAS C ON P.CPF_CNPJ = C.CPF_CNPJ
        WHERE P.MES_COHORT >= '{DATA_INICIO}' AND C.MES_ATIVIDADE >= P.MES_COHORT GROUP BY 1, 2, 3
    """,

    # 5. Demográfico
    "df_demo": f"""
        WITH CLIENTES_ATIVOS AS (
            SELECT DISTINCT CPF_CNPJ, DATE_TRUNC('MONTH', INCLUSAO_DATA) AS MES_ATIVIDADE 
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS 
            WHERE INCLUSAO_DATA >= '{DATA_INICIO}' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
        )
        SELECT A.MES_ATIVIDADE, C.SEXO, DATEDIFF('YEAR', C.DATA_NASCIMENTO, CURRENT_DATE()) AS IDADE, C.UF, COUNT(*) AS COUNT
        FROM FSJ_PRD.GOLD.VW_CLIENTES C 
        JOIN CLIENTES_ATIVOS A ON C.CPF_CNPJ = A.CPF_CNPJ 
        WHERE C.DATA_NASCIMENTO IS NOT NULL AND C.FLAG_ANONIMIZACAO = FALSE
        GROUP BY 1, 2, 3, 4
    """,

    # 6. Clientes VIP (Top 500)
    "df_vip": f"""
        SELECT CPF_CNPJ, COUNT(DISTINCT VENDA_ID) AS FREQUENCIA, SUM(VALOR_TOTAL) AS RECEITA, MAX(INCLUSAO_DATA) AS ULTIMA_COMPRA
        FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS WHERE INCLUSAO_DATA >= '{DATA_INICIO}' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
        GROUP BY CPF_CNPJ ORDER BY RECEITA DESC LIMIT 500
    """,

    # 7. Novos Clientes (CAC Base)
    "df_novos_cac": f"""
        WITH BASE AS (
            SELECT CPF_CNPJ, DATE_TRUNC('MONTH', MIN(INCLUSAO_DATA)) AS MES_PRIMEIRA_COMPRA
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS WHERE IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL GROUP BY CPF_CNPJ
        )
        SELECT
            MES_PRIMEIRA_COMPRA AS MES_REFERENCIA,
            COUNT(DISTINCT CPF_CNPJ) AS QTD_CLIENTES_NOVOS,
            SUM(COUNT(DISTINCT CPF_CNPJ)) OVER (PARTITION BY YEAR(MES_PRIMEIRA_COMPRA) ORDER BY MES_PRIMEIRA_COMPRA ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS NOVOS_CLIENTES_YTD
        FROM BASE WHERE MES_PRIMEIRA_COMPRA >= '{DATA_INICIO}'
        GROUP BY 1 ORDER BY 1
    """,

    # 8. LTV Evolução Mensal por Canal
    "df_ltv_canal_mes": f"""
        WITH VENDAS AS (
            SELECT CPF_CNPJ, VENDA_ID, VALOR_TOTAL, DATE_TRUNC('MONTH', INCLUSAO_DATA) AS MES_VENDA,
                CASE
                    WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega') THEN 'APP'
                    WHEN TIPO_VENDA_DESCRICAO IN ('SITE', 'SITE Tele Entrega') THEN 'SITE'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 'LOJA FÍSICA'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Tele Entrega', 'Tele Entrega Central') THEN 'TELEVENDAS'
                    ELSE 'OUTROS'
                END AS CANAL
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
            WHERE INCLUSAO_DATA >= '{DATA_INICIO}' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
        )
        SELECT
            MES_VENDA AS MES_REFERENCIA, CANAL,
            COUNT(DISTINCT CPF_CNPJ) AS QTD_CLIENTES_UNICOS,
            COUNT(DISTINCT VENDA_ID) AS QTD_COMPRAS,
            ROUND(SUM(VALOR_TOTAL) / NULLIF(COUNT(DISTINCT CPF_CNPJ), 0), 2) AS RECEITA_MEDIA_POR_CLIENTE,
            ROUND(COUNT(DISTINCT VENDA_ID) / NULLIF(COUNT(DISTINCT CPF_CNPJ), 0), 2) AS FREQUENCIA_MEDIA,
            ROUND(SUM(VALOR_TOTAL) / NULLIF(COUNT(DISTINCT VENDA_ID), 0), 2) AS TICKET_MEDIO
        FROM VENDAS GROUP BY 1, 2 ORDER BY 1, 2
    """,

    # 9. Novos Clientes por Canal (Mix de Aquisição)
    "df_novos_por_canal": f"""
        WITH PRIMEIRA_COMPRA AS (
            SELECT CPF_CNPJ, MIN(INCLUSAO_DATA) AS DATA_PRIMEIRA, DATE_TRUNC('MONTH', MIN(INCLUSAO_DATA)) AS MES_PRIMEIRA
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS WHERE IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL GROUP BY CPF_CNPJ
        ),
        VENDAS_AQUISICAO AS (
            SELECT V.CPF_CNPJ,
                CASE
                    WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega') THEN 'APP'
                    WHEN TIPO_VENDA_DESCRICAO IN ('SITE', 'SITE Tele Entrega') THEN 'SITE'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 'LOJA FÍSICA'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Tele Entrega', 'Tele Entrega Central') THEN 'TELEVENDAS'
                    ELSE 'OUTROS'
                END AS CANAL_AQUISICAO
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS V
            JOIN PRIMEIRA_COMPRA PC ON V.CPF_CNPJ = PC.CPF_CNPJ AND V.INCLUSAO_DATA = PC.DATA_PRIMEIRA
        )
        SELECT PC.MES_PRIMEIRA AS MES_REFERENCIA, VA.CANAL_AQUISICAO AS CANAL, COUNT(DISTINCT PC.CPF_CNPJ) AS QTD_NOVOS_CLIENTES
        FROM PRIMEIRA_COMPRA PC JOIN VENDAS_AQUISICAO VA ON PC.CPF_CNPJ = VA.CPF_CNPJ
        WHERE PC.MES_PRIMEIRA >= '{DATA_INICIO}' GROUP BY 1, 2 ORDER BY 1, 2
    """
}

def main():
    start_time = datetime.now()
    print("="*60)
    print(f"  EXTRATOR MASTER CRM - INICIADO ÀS {start_time.strftime('%H:%M:%S')}")
    print("="*60)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"[*] Conectando ao Snowflake (DSN={DSN})...")
    try:
        conn = pyodbc.connect(f"DSN={DSN};")
        print("[OK] Conectado.")
    except Exception as e:
        print(f"[ERRO] Falha na conexão: {e}")
        return

    total_queries = len(QUERIES)
    for i, (nome, sql) in enumerate(QUERIES.items(), 1):
        print(f"\n[{i}/{total_queries}] Processando {nome}...")
        try:
            df = pd.read_sql(sql, conn)
            caminho = os.path.join(OUTPUT_DIR, f"{nome}.csv")
            df.to_csv(caminho, index=False, encoding="utf-8-sig")
            print(f"   -> Sucesso: {len(df)} registros salvos em {caminho}")
        except Exception as e:
            print(f"   -> ERRO em {nome}: {e}")

    conn.close()
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*60)
    print(f"  EXTRAÇÃO CONCLUÍDA EM {duration.total_seconds():.1f}s")
    print(f"  DADOS DISPONÍVEIS NA PASTA: ./{OUTPUT_DIR}")
    print("="*60)

if __name__ == "__main__":
    main()
