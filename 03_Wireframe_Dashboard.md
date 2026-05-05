# Wireframe e Arquitetura do Dashboard

## Menu Lateral (Sidebar)
*   **Logo/Ícone da Empresa**
*   **Parâmetros:**
    *   Dropdown de "Filtrar Canais"
    *   Input/Slider de "Orçamento de Mídia Extra" (Para cálculo de CAC)
*   **Navegação Principal (Radio Buttons):**
    1.  Camada Executiva (MTD/YTD)
    2.  Camada Analítica (Demografia, Retenção, Mídia)
    3.  Camada Acionável (RFM e Exportação)

---

## Aba 1: Camada Executiva (Visão de Topo)
*   **Cabeçalho:** *Pacing do Mês Atual & Acumulado do Ano*
*   **Linha 1 (Cards MTD Exatos):**
    *   [Receita MTD | Variação YoY%]
    *   [Clientes Ativos MTD | Variação YoY%]
    *   [Ticket Médio MTD | Variação YoY%]
    *   [Frequência MTD | Variação YoY%]
*   **Linha 2 (Evolução YTD):**
    *   [Gráfico de Barras: Curva de Faturamento por Mês Fechado (Ano Atual vs Ano Anterior)]

---

## Aba 2: Camada Analítica (Aprofundamento)
Nesta seção, teremos sub-abas horizontais (`st.tabs`):

**Sub-aba 2.1: Aquisição, Mídia & CAC**
*   **Cards:** [Novos Clientes no Mês] | [Orçamento Mídia] | [CAC Médio]
*   **Gráfico:** Linha de tendência de Novos Clientes nos últimos 12 meses.
*   **Tabela:** Volume de clientes novos adquiridos e custo dividido por canal principal.

**Sub-aba 2.2: LTV & Omnichannel**
*   **Gráfico Pizza:** Share de Receita (Omni vs Somente Loja vs Somente Digital)
*   **Gráfico Barras:** LTV Médio por Perfil Omnichannel (Quem gasta mais na vida útil?)
*   **Gráfico Barras Horizontal:** LTV e Frequência abertos por Canal específico (APP, SITE, TELEVENDAS, LOJA).

**Sub-aba 2.3: Perfil & Demografia**
*   **Gráficos:** Distribuição de Sexo (Pizza) e Faixa Etária (Histograma/Barras) calculados pelo cruzamento da `VW_CLIENTES`.
*   **Top Cidades:** Ranking em barras horizontais.

**Sub-aba 2.4: Retenção (Coorte)**
*   **Heatmap:** Matriz de safras x meses sobrevividos após aquisição (Mês 0, Mês 1, etc.).

---

## Aba 3: Camada Acionável (Data to Action)
*   **Tabela Analítica (Lista de Contatos):**
    *   Uma base consolidada mostrando CPF/CNPJ, Nome (mascarado), E-mail, Celular, Segmento (Novo, Recorrente, Risco), Ticket Médio.
    *   **Botão:** `Download CSV` para extração da audiência diretamente para o CRM ou Meta Ads.
*   **Regras de LGPD:** Clientes marcados com `FLAG_ANONIMIZACAO` = TRUE serão automaticamente excluídos dessa visualização para resguardar compliance.
