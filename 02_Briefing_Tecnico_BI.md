# Briefing Técnico & BI: Dashboard CRM 360º

## 1. Origem dos Dados (Data Sources)
A aplicação consome diretamente o Data Warehouse no Snowflake via conexão ODBC DSN (`SNOWFLAKE_FSJ`).
*   **Vendas/Transações:** `FSJ_PRD.GOLD.VW_ANALISE_VENDAS`
*   **Cadastros Demográficos:** `FSJ_PRD.GOLD.VW_CLIENTES`

## 2. Regras de Negócio e Cálculos

### 2.1. Definição de Receita
*   **Métrica:** `RECEITA_TOTAL` ou `VALOR_TOTAL`.
*   **Filtros aplicados:** `IDENTIFICADOR = 'V'` (apenas vendas) e `CPF_CNPJ IS NOT NULL` (apenas transações identificadas com cliente).
*   **Atenção:** Vendas realizadas antes de `2025-01-01` são cortadas da visualização MTD/YTD para alinhamento com a base histórica de crescimento.

### 2.2. Cálculo de Clientes Novos por Mês
*   Considera-se cliente novo aquele cujo a sua `PRIMEIRA_COMPRA` (`MIN(INCLUSAO_DATA)`) na tabela de Vendas ocorreu no mês de análise, cruzando com a `DATA_INCLUSAO` da tabela de Clientes se necessário.

### 2.3. Custo de Aquisição de Clientes (CAC)
*   **Fórmula:** `Orçamento de Marketing / Quantidade de Clientes Novos no Mês`
*   **Ação BI:** Como o orçamento de marketing/mídia não reside nativamente nas views de Vendas, o dashboard possuirá um input paramétrico (ou campo para upload de `.csv` de custos) gerido pelo time de Marketing para viabilizar o cálculo dinâmico.

### 2.4. LTV (Lifetime Value) por Canal
*   **Fórmula:** `Receita Total Acumulada do Cliente / Número de Clientes daquele Segmento/Canal`
*   A distribuição por canais é feita pela taxonomia `TIPO_VENDA_DESCRICAO`:
    *   **APP:** 'APP', 'APP Tele Entrega'
    *   **SITE:** 'SITE', 'SITE Tele Entrega'
    *   **LOJA FÍSICA:** 'Venda Balcão', 'Venda Caixa', 'Auto Atendimento'
    *   **TELEVENDAS:** 'Venda Tele Entrega', 'Tele Encaminhada Lojas', 'Tele Vizinhança', 'Venda Tele Entrega Central'

### 2.5. Churn e Matriz de Retenção
*   O Churn pode ser dinamicamente classificado (ex: 90 dias sem compras = Risco, 180 dias = Churn / Hibernando).
*   A Coorte (Retenção) agrupa os clientes pelo mês de primeira compra e mede a reincidência de transações nos meses `N+1`, `N+2`, etc.

## 3. Data Quality & Governança (Checklist)
*   [ ] Taxa de Preenchimento (Fill Rate): Monitorar % de nulos em `CPF_CNPJ`, `EMAIL`, `TELEFONE` e `CIDADE`.
*   [ ] LGPD: Observar a `DATA_ANONIMIZACAO` e `FLAG_ANONIMIZACAO`. Se anonimizado, o cliente não pode aparecer em listas acionáveis de re-marketing.
*   [ ] Deduplicação: Uso do campo `ID` ou `CPF_CNPJ` da `VW_CLIENTES` como chave-mestra unívoca.
