# 💊 Manual Operacional: Dashboard CRM Analytics - Farmácias São João

Este documento descreve a arquitetura, o funcionamento e os procedimentos de manutenção do ecossistema de dados do CRM Analytics.

## 🚀 1. Visão Geral
O projeto consiste em um dashboard interativo (Streamlit) para análise profunda do comportamento dos clientes, focado em métricas de Aquisição (CAC), Valor (LTV) e Retenção (Cohort).

### Principais Funcionalidades:
- **Visão Executiva**: KPIs com comparativo YoY (Year-over-Year).
- **Módulo de Aquisição**: Cálculo dinâmico de CAC baseado em investimento real de mídia.
- **Análise por Canal**: Comparativo de performance entre APP, Site, Loja Física e Tele.
- **Retenção (Cohort)**: Matriz de comportamento de safras de clientes.
- **Exportação VIP**: Lista dos Top 500 clientes em receita.

---

## 🏗️ 2. Arquitetura de Dados
O sistema utiliza um modelo **desacoplado** para garantir alta performance e disponibilidade online:

1.  **Fonte (Snowflake)**: Os dados brutos residem no banco de dados da São João.
2.  **Extração (Local)**: Um script Python (`extrator_master.py`) baixa as queries processadas para arquivos CSV locais na pasta `/dados`.
3.  **Aplicação (Streamlit)**: O dashboard lê os arquivos CSV, garantindo que a interface seja rápida e funcione offline (ou na nuvem) sem depender de conexão direta ao banco.
4.  **Sincronização (GitHub)**: Os dados e o código são enviados para o repositório GitHub, que alimenta automaticamente o link público.

---

## 🛠️ 3. Componentes do Projeto

| Arquivo | Função |
| :--- | :--- |
| `app_crm.py` | Código principal do Dashboard Streamlit. |
| `extrator_master.py` | Script que executa as queries no Snowflake e gera os CSVs. |
| `CRM_Sincronizar_Tudo.bat` | **Atalho Mestre**: Roda o extrator e sobe tudo para o Git. |
| `iniciar_dashboard_crm.bat` | Atalho para abrir o dashboard localmente no navegador. |
| `dados/df_budget.csv` | Arquivo que armazena os investimentos de mídia inseridos no dashboard. |

---

## 🔄 4. Procedimentos de Manutenção

### A. Como atualizar os dados?
Basta clicar duas vezes no arquivo **`CRM_Sincronizar_Tudo.bat`**. 
- Ele vai pedir seu login do Snowflake (se necessário).
- Ele vai baixar os novos dados.
- Ele vai enviar as atualizações para o GitHub.
- **Resultado**: Em minutos, o link do Streamlit Cloud estará atualizado para todos.

### B. Como inserir o Investimento de Mídia (para cálculo de CAC)?
1.  Acesse a aba **"4. Aquisição & LTV"**.
2.  Localize a tabela **"Investimento em Marketing (Mídia)"**.
3.  Clique e digite o valor investido nos meses correspondentes (referente à Linha 5 da sua planilha de mídia).
4.  O dashboard salvará automaticamente no arquivo `df_budget.csv` e recalculará o CAC na hora.

### C. Filtros de Data e Canal
- Na barra lateral esquerda, você pode definir o período de análise. 
- Todos os gráficos e KPIs se ajustam automaticamente.
- Legendas explicativas abaixo de cada gráfico ajudam na interpretação dos dados.

---

## ⚠️ 5. Solução de Problemas (Troubleshooting)

- **Erro de Hostname no Snowflake**: Verifique se sua internet está estável ou se a VPN da empresa está ligada. Se falhar, basta rodar o `.bat` novamente quando a conexão voltar.
- **Push Bloqueado no Git**: O GitHub protege o seu Token (PAT). Se o envio falhar por "Secret detected", acesse o link de segurança enviado no log do terminal e clique em "Allow me to expose this secret".
- **Dashboard Offline**: Verifique se o serviço do Streamlit Cloud está conectado ao seu repositório `lukasg64-png/CRM` na branch `main`.

---
*Documento gerado automaticamente pela Inteligência Artificial Antigravity em 06/05/2026.*
