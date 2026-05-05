"""
Extrator: Aquisição, CAC, LTV e Frequência por Canal
Conexão: ODBC DSN=SNOWFLAKE_FSJ
Saída:   dados/df_novos_cac.csv
         dados/df_ltv_canal.csv
         dados/df_ltv_canal_mes.csv
         dados/df_novos_por_canal.csv
"""
import pyodbc
import pandas as pd
import os

DATA_INICIO = "2025-01-01"   # ajuste conforme necessário

QUERIES = {

    # ----------------------------------------------------------
    # Q1: Clientes Novos por Mês + acumulado YTD
    # (CAC não incluído aqui — depende de input do Marketing)
    # ----------------------------------------------------------
    "df_novos_cac": f"""
        WITH BASE AS (
            SELECT
                CPF_CNPJ,
                DATE_TRUNC('MONTH', MIN(INCLUSAO_DATA)) AS MES_PRIMEIRA_COMPRA
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
            WHERE IDENTIFICADOR = 'V'
              AND CPF_CNPJ IS NOT NULL
            GROUP BY CPF_CNPJ
        )
        SELECT
            MES_PRIMEIRA_COMPRA                           AS MES_REFERENCIA,
            TO_CHAR(MES_PRIMEIRA_COMPRA, 'MON/YYYY')      AS PERIODO,
            COUNT(DISTINCT CPF_CNPJ)                      AS QTD_CLIENTES_NOVOS,
            SUM(COUNT(DISTINCT CPF_CNPJ)) OVER (
                PARTITION BY YEAR(MES_PRIMEIRA_COMPRA)
                ORDER BY MES_PRIMEIRA_COMPRA
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )                                             AS NOVOS_CLIENTES_YTD
        FROM BASE
        WHERE MES_PRIMEIRA_COMPRA >= '{DATA_INICIO}'
        GROUP BY MES_PRIMEIRA_COMPRA
        ORDER BY MES_PRIMEIRA_COMPRA
    """,

    # ----------------------------------------------------------
    # Q2: LTV e Frequência consolidado por Canal (histórico)
    # ----------------------------------------------------------
    "df_ltv_canal": f"""
        WITH VENDAS AS (
            SELECT
                CPF_CNPJ,
                VENDA_ID,
                VALOR_TOTAL,
                CASE
                    WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega')               THEN 'APP'
                    WHEN TIPO_VENDA_DESCRICAO IN ('SITE', 'SITE Tele Entrega')             THEN 'SITE'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 'LOJA FÍSICA'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Tele Entrega', 'Tele Encaminhada Lojas',
                                                   'Tele Vizinhança', 'Venda Tele Entrega Central') THEN 'TELEVENDAS'
                    ELSE 'OUTROS'
                END AS CANAL
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
            WHERE IDENTIFICADOR = 'V'
              AND CPF_CNPJ IS NOT NULL
              AND INCLUSAO_DATA >= '{DATA_INICIO}'
        )
        SELECT
            CANAL,
            COUNT(DISTINCT CPF_CNPJ)                      AS QTD_CLIENTES_UNICOS,
            COUNT(DISTINCT VENDA_ID)                      AS QTD_COMPRAS,
            ROUND(SUM(VALOR_TOTAL), 2)                    AS RECEITA_TOTAL,
            ROUND(SUM(VALOR_TOTAL)
                  / NULLIF(COUNT(DISTINCT CPF_CNPJ), 0), 2) AS LTV_MEDIO_CLIENTE,
            ROUND(COUNT(DISTINCT VENDA_ID)
                  / NULLIF(COUNT(DISTINCT CPF_CNPJ), 0), 2) AS FREQUENCIA_MEDIA,
            ROUND(SUM(VALOR_TOTAL)
                  / NULLIF(COUNT(DISTINCT VENDA_ID), 0), 2)  AS TICKET_MEDIO
        FROM VENDAS
        GROUP BY CANAL
        ORDER BY LTV_MEDIO_CLIENTE DESC
    """,

    # ----------------------------------------------------------
    # Q3: LTV e Frequência por Canal × Mês
    # ----------------------------------------------------------
    "df_ltv_canal_mes": f"""
        WITH VENDAS AS (
            SELECT
                CPF_CNPJ,
                VENDA_ID,
                VALOR_TOTAL,
                DATE_TRUNC('MONTH', INCLUSAO_DATA) AS MES_VENDA,
                CASE
                    WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega')               THEN 'APP'
                    WHEN TIPO_VENDA_DESCRICAO IN ('SITE', 'SITE Tele Entrega')             THEN 'SITE'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 'LOJA FÍSICA'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Tele Entrega', 'Tele Encaminhada Lojas',
                                                   'Tele Vizinhança', 'Venda Tele Entrega Central') THEN 'TELEVENDAS'
                    ELSE 'OUTROS'
                END AS CANAL
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
            WHERE IDENTIFICADOR = 'V'
              AND CPF_CNPJ IS NOT NULL
              AND INCLUSAO_DATA >= '{DATA_INICIO}'
        )
        SELECT
            MES_VENDA                                     AS MES_REFERENCIA,
            TO_CHAR(MES_VENDA, 'MON/YYYY')                AS PERIODO,
            CANAL,
            COUNT(DISTINCT CPF_CNPJ)                      AS QTD_CLIENTES_UNICOS,
            COUNT(DISTINCT VENDA_ID)                      AS QTD_COMPRAS,
            ROUND(SUM(VALOR_TOTAL), 2)                    AS RECEITA_TOTAL,
            ROUND(SUM(VALOR_TOTAL)
                  / NULLIF(COUNT(DISTINCT CPF_CNPJ), 0), 2) AS RECEITA_MEDIA_POR_CLIENTE,
            ROUND(COUNT(DISTINCT VENDA_ID)
                  / NULLIF(COUNT(DISTINCT CPF_CNPJ), 0), 2) AS FREQUENCIA_MEDIA,
            ROUND(SUM(VALOR_TOTAL)
                  / NULLIF(COUNT(DISTINCT VENDA_ID), 0), 2)  AS TICKET_MEDIO
        FROM VENDAS
        GROUP BY MES_VENDA, CANAL
        ORDER BY MES_VENDA, CANAL
    """,

    # ----------------------------------------------------------
    # Q4: Clientes Novos por Canal de Aquisição
    # (canal da PRIMEIRA compra + métricas do mês de entrada)
    # ----------------------------------------------------------
    "df_novos_por_canal": f"""
        WITH PRIMEIRA_COMPRA AS (
            SELECT
                CPF_CNPJ,
                DATE_TRUNC('MONTH', MIN(INCLUSAO_DATA)) AS MES_PRIMEIRA_COMPRA
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
            WHERE IDENTIFICADOR = 'V'
              AND CPF_CNPJ IS NOT NULL
            GROUP BY CPF_CNPJ
        ),
        VENDAS AS (
            SELECT
                CPF_CNPJ,
                VENDA_ID,
                VALOR_TOTAL,
                DATE_TRUNC('MONTH', INCLUSAO_DATA) AS MES_VENDA,
                CASE
                    WHEN TIPO_VENDA_DESCRICAO IN ('APP', 'APP Tele Entrega')               THEN 'APP'
                    WHEN TIPO_VENDA_DESCRICAO IN ('SITE', 'SITE Tele Entrega')             THEN 'SITE'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Balcão', 'Venda Caixa', 'Auto Atendimento') THEN 'LOJA FÍSICA'
                    WHEN TIPO_VENDA_DESCRICAO IN ('Venda Tele Entrega', 'Tele Encaminhada Lojas',
                                                   'Tele Vizinhança', 'Venda Tele Entrega Central') THEN 'TELEVENDAS'
                    ELSE 'OUTROS'
                END AS CANAL
            FROM FSJ_PRD.GOLD.VW_ANALISE_VENDAS
            WHERE IDENTIFICADOR = 'V'
              AND CPF_CNPJ IS NOT NULL
              AND INCLUSAO_DATA >= '{DATA_INICIO}'
        )
        SELECT
            PC.MES_PRIMEIRA_COMPRA                        AS MES_REFERENCIA,
            TO_CHAR(PC.MES_PRIMEIRA_COMPRA, 'MON/YYYY')   AS PERIODO,
            V.CANAL,
            COUNT(DISTINCT PC.CPF_CNPJ)                   AS QTD_NOVOS_CLIENTES,
            ROUND(SUM(V.VALOR_TOTAL), 2)                  AS RECEITA_NO_MES_AQUISICAO,
            ROUND(SUM(V.VALOR_TOTAL)
                  / NULLIF(COUNT(DISTINCT PC.CPF_CNPJ), 0), 2) AS TICKET_MEDIO_NOVOS,
            ROUND(COUNT(DISTINCT V.VENDA_ID)
                  / NULLIF(COUNT(DISTINCT PC.CPF_CNPJ), 0), 2) AS FREQ_NO_MES_AQUISICAO
        FROM PRIMEIRA_COMPRA PC
        JOIN VENDAS V
          ON  V.CPF_CNPJ  = PC.CPF_CNPJ
          AND V.MES_VENDA = PC.MES_PRIMEIRA_COMPRA
        WHERE PC.MES_PRIMEIRA_COMPRA >= '{DATA_INICIO}'
        GROUP BY PC.MES_PRIMEIRA_COMPRA, V.CANAL
        ORDER BY PC.MES_PRIMEIRA_COMPRA, V.CANAL
    """,
}


def main():
    print("=" * 60)
    print("  Extrator: Aquisição, CAC, LTV e Frequência por Canal")
    print("=" * 60)

    print("\n[*] Conectando ao Snowflake via ODBC (DSN=SNOWFLAKE_FSJ)...")
    try:
        conn = pyodbc.connect("DSN=SNOWFLAKE_FSJ;")
        print("[OK] Conexao estabelecida.\n")
    except Exception as e:
        print(f"[ERRO] Falha na conexao: {e}")
        return

    os.makedirs("dados", exist_ok=True)

    resultados = {}
    for nome, sql in QUERIES.items():
        print(f"[>>] Executando: {nome} ...")
        try:
            df = pd.read_sql(sql, conn)
            caminho = f"dados/{nome}.csv"
            df.to_csv(caminho, index=False, encoding="utf-8-sig")
            resultados[nome] = len(df)
            print(f"   [OK] {len(df)} linhas -> {caminho}")
        except Exception as e:
            print(f"   [ERRO] {nome}: {e}")

    conn.close()

    print("\n" + "=" * 60)
    print("  RESUMO DA EXTRACAO")
    print("=" * 60)
    for nome, linhas in resultados.items():
        print(f"  {nome:<30} {linhas:>6} linhas")
    print("\n[DONE] Extracao finalizada! CSVs salvos em ./dados/")


if __name__ == "__main__":
    main()
