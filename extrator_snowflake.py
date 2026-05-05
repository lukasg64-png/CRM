import pyodbc
import pandas as pd
import os

def extrair_e_salvar():
    print("Conectando ao Snowflake via ODBC...")
    conn = pyodbc.connect("DSN=SNOWFLAKE_FSJ;")
    
    queries = {
        "df_v": """
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
                WHERE INCLUSAO_DATA >= '2025-01-01' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
            )
            SELECT DATE(INCLUSAO_DATA) AS DATA_VENDA, YEAR(INCLUSAO_DATA) AS ANO, MONTH(INCLUSAO_DATA) AS MES, DAY(INCLUSAO_DATA) AS DIA,
            CANAL, COUNT(DISTINCT VENDA_ID) AS QTD_VENDAS, COUNT(DISTINCT CPF_CNPJ) AS QTD_CLIENTES, SUM(VALOR_TOTAL) AS RECEITA_TOTAL
            FROM VENDAS GROUP BY 1, 2, 3, 4, 5
        """,
        "df_omni": """
            WITH COMPRAS_CANAIS AS (
                SELECT CPF_CNPJ,
                    MAX(CASE WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 1 ELSE 0 END) AS COMPROU_LOJA,
                    MAX(CASE WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega', 'SITE', 'SITE Tele Entrega') THEN 1 ELSE 0 END) AS COMPROU_DIGITAL,
                    COUNT(DISTINCT VENDA_ID) AS QTD_VENDAS, SUM(VALOR_TOTAL) AS RECEITA
                FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
                WHERE INCLUSAO_DATA >= '2025-01-01' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
                GROUP BY CPF_CNPJ
            )
            SELECT CASE WHEN COMPROU_LOJA = 1 AND COMPROU_DIGITAL = 1 THEN 'Omni (Loja + Digital)' WHEN COMPROU_LOJA = 1 AND COMPROU_DIGITAL = 0 THEN 'Somente Loja Física' WHEN COMPROU_LOJA = 0 AND COMPROU_DIGITAL = 1 THEN 'Somente Canais Digitais' ELSE 'Outros' END AS PERFIL_OMNI,
            COUNT(CPF_CNPJ) AS QTD_CLIENTES, SUM(QTD_VENDAS) AS QTD_VENDAS, SUM(RECEITA) AS RECEITA_TOTAL
            FROM COMPRAS_CANAIS GROUP BY 1
        """,
        "df_canal_ltv": """
            WITH VENDAS_CANAL AS (
                SELECT CPF_CNPJ,
                    CASE
                        WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega') THEN 'APP'
                        WHEN TIPO_VENDA_DESCRICAO IN ('SITE', 'SITE Tele Entrega') THEN 'SITE'
                        WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 'LOJA FÍSICA'
                        WHEN TIPO_VENDA_DESCRICAO IN ('Venda Tele Entrega', 'Tele Encaminhada Lojas', 'Tele Vizinhança', 'Venda Tele Entrega Central') THEN 'TELEVENDAS'
                        ELSE 'OUTROS'
                    END AS CANAL,
                    COUNT(DISTINCT VENDA_ID) AS QTD_VENDAS, SUM(VALOR_TOTAL) AS RECEITA
                FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
                WHERE INCLUSAO_DATA >= '2025-01-01' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
                GROUP BY CPF_CNPJ, CANAL
            )
            SELECT CANAL, COUNT(CPF_CNPJ) AS QTD_CLIENTES, SUM(QTD_VENDAS) AS QTD_VENDAS, SUM(RECEITA) AS RECEITA_TOTAL
            FROM VENDAS_CANAL GROUP BY CANAL
        """,
        "df_cohort": """
            WITH PRIMEIRA_COMPRA AS (
                SELECT CPF_CNPJ, DATE_TRUNC('MONTH', MIN(INCLUSAO_DATA)) AS MES_COHORT
                FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS WHERE IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL GROUP BY CPF_CNPJ
            ),
            COMPRAS_ATIVAS AS (
                SELECT CPF_CNPJ, DATE_TRUNC('MONTH', INCLUSAO_DATA) AS MES_ATIVIDADE
                FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS WHERE INCLUSAO_DATA >= '2025-01-01' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL GROUP BY CPF_CNPJ, DATE_TRUNC('MONTH', INCLUSAO_DATA)
            )
            SELECT P.MES_COHORT, C.MES_ATIVIDADE, DATEDIFF('MONTH', P.MES_COHORT, C.MES_ATIVIDADE) AS MESES_DESDE_COHORT, COUNT(DISTINCT C.CPF_CNPJ) AS QTD_CLIENTES_ATIVOS
            FROM PRIMEIRA_COMPRA P JOIN COMPRAS_ATIVAS C ON P.CPF_CNPJ = C.CPF_CNPJ
            WHERE P.MES_COHORT >= '2025-01-01' AND C.MES_ATIVIDADE >= P.MES_COHORT GROUP BY 1, 2, 3
        """,
        "df_demo": """
            WITH CLIENTES_ATIVOS AS (
                SELECT DISTINCT CPF_CNPJ FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS WHERE INCLUSAO_DATA >= '2025-01-01' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
            )
            SELECT C.SEXO, DATEDIFF('YEAR', C.DATA_NASCIMENTO, CURRENT_DATE()) AS IDADE, C.UF, COUNT(*) AS COUNT
            FROM FSJ_PRD.GOLD.VW_CLIENTES C JOIN CLIENTES_ATIVOS A ON C.CPF_CNPJ = A.CPF_CNPJ WHERE C.DATA_NASCIMENTO IS NOT NULL AND C.FLAG_ANONIMIZACAO = FALSE
            GROUP BY 1, 2, 3
        """,
        "df_vip": """
            SELECT CPF_CNPJ, COUNT(DISTINCT VENDA_ID) AS FREQUENCIA, SUM(VALOR_TOTAL) AS RECEITA, MAX(INCLUSAO_DATA) AS ULTIMA_COMPRA
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS WHERE INCLUSAO_DATA >= '2025-01-01' AND IDENTIFICADOR = 'V' AND CPF_CNPJ IS NOT NULL
            GROUP BY CPF_CNPJ ORDER BY RECEITA DESC LIMIT 500
        """
    }

    if not os.path.exists("dados"):
        os.makedirs("dados")

    for nome, query in queries.items():
        print(f"Baixando dados para {nome}.csv ...")
        df = pd.read_sql(query, conn)
        df.to_csv(f"dados/{nome}.csv", index=False)
        print(f"-> Concluído: {len(df)} linhas baixadas.")

    conn.close()
    print("Extração finalizada com sucesso! Você já pode subir a pasta 'dados' no GitHub.")

if __name__ == "__main__":
    extrair_e_salvar()
