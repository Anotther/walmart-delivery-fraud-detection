# Anatomia do Dashboard: Walmart Delivery Fraud Detection

Este documento define a estrutura, design e fluxo de dados para o Dashboard de Detecção de Fraudes. O objetivo é transformar o template conceitual HTML em uma aplicação funcional de dados, integrado ao backend python existente.

## 1. Identidade Visual e UX
Baseado no template fornecido, manteremos a identidade visual corporativa do Walmart.

### Paleta de Cores
- **Primária (Brand)**: `Walmart Blue #004c91` (Headers, Sidebars ativos)
- **Secundária (Brand)**: `Walmart Yellow #ffc220` (CTAs, Destaques)
- **Acentos**:
  - `Light Blue #0071ce`: Gradientes e estados de hover.
  - `Background`: `Gray-50 #F9FAFB`.
- **Semântica (Alertas)**:
  - `Critical (Danger)`: `#EF4444` (Riscos críticos, fraudes confirmadas).
  - `Warning`: `#F59E0B` (Suspeitas, risco médio).
  - `Success`: `#10B981` (Métricas positivas, entregas seguras).

### Tipografia e Estilo
- **Font-family**: Sans-serif (Inter ou System UI).
- **Cards**: Fundo branco, sombra suave (`shadow-lg`), bordas arredondadas (`rounded-lg`).
- **Layout**: Sidebar fixa à esquerda, conteúdo principal fluido à direita.

---

## 2. Arquitetura de Dados
O dashboard consumirá dados processados via `src.dashboard.data_cache`, garantindo performance e dados "near real-time".

- **Backend**: Python Module (`src.dashboard.data_cache.DashboardCache`).
- **Cache Strategy**: LRU Cache com TTL (15 min) para operações pesadas.
- **Refresh**: Botão de atualização manual para forçar recálculo.

---

## 3. Estrutura de Navegação (Sitemap)

O aplicativo será dividido em 6 módulos principais acessíveis via Sidebar:

1.  **Visão Geral (Home)**: Resumo executivo e KPIs de alto nível.
2.  **Monitor em Tempo Real**: Alertas e operações do dia.
3.  **Análise de Motoristas**: Perfil de risco e ranking de suspeitos.
4.  **Análise de Clientes**: Comportamento de consumo e reclamações.
5.  **Inteligência Geográfica**: Mapa de calor de fraudes por região.
6.  **Produtos & Perdas**: Análise de itens mais visados.

---

## 4. Detalhamento das Seções

### 4.1. Visão Geral (Home)
*O "Big Picture" para executivos e gerentes.*

**Componentes:**
- **Hero Section**: Bem-vindo com resumo rápido do impacto (ex: "Sistema protegeu $2.3M este mês").
- **KPI Cards (Row 1)**:
    - **Fraudes Detectadas (%)**: `get_overview_metrics()['overall_missing_rate']`.
    - **Prejuízo Estimado**: `get_overview_metrics()['estimated_loss']`.
    - **Pedidos Analisados**: `get_overview_metrics()['total_orders']`.
    - **Alertas Ativos**: Contagem de `get_risk_alerts()`.
- **Gráfico Principal**: Tendência de Fraudes (Mensal).
    - *Fonte*: `get_temporal_trends()['monthly']`.
    - *Visual*: Gráfico de linha/área combinando Volume de Pedidos vs. Taxa de Fraude.

### 4.2. Monitor em Tempo Real
*Foco operacional para analistas de fraude.*

**Componentes:**
- **Status do Sistema**: Indicador de uptime e última atualização.
- **KPIs do Dia (Live)**:
    - Pedidos Hoje, Fraudes Hoje (derivado de `get_temporal_trends()['daily']` para o dia atual).
- **Feed de Alertas (Risk Feed)**:
    - Lista scrollável de alertas de alta prioridade.
    - *Fonte*: `get_risk_alerts(threshold=75)`.
    - *Campos*: Entidade (Motorista/Cliente), Score de Risco, Motivo (ex: "Missing Rate > 50%").
    - *Ação*: Botão "Investigar details".
- **Gráfico Horário**:
    - *Fonte*: `get_temporal_trends()['hourly']`.
    - *Visual*: Bar chart de incidentes por hora do dia (Heatmap temporal).

### 4.3. Análise de Motoristas (Driver Intelligence)
*Identificação de fraudadores internos.*

**Componentes:**
- **Distribuição de Risco**:
    - *Fonte*: `get_risk_distribution()['driver_risk_distribution']`.
    - *Visual*: Donut Chart (Baixo, Médio, Alto, Crítico).
- **Top 10 Suspeitos**:
    - *Fonte*: `get_top_suspicious(n=10)['top_suspicious_drivers']`.
    - *Tabela*:
        - Nome (ID).
        - Entregas Totais.
        - **Taxa de Extravio** (Highlight vermelho se > 5%).
        - **Risk Score** (Barra de progresso colorida).
- **Filtros**: Por Qtd de Entregas, Score Mínimo.

### 4.4. Análise de Clientes (Customer Intelligence)
*Identificação de fraudes na ponta do consumidor.*

**Componentes:**
- **Top 10 Clientes Suspeitos**:
    - *Fonte*: `get_top_suspicious()['top_suspicious_customers']`.
    - *Tabela*: ID, Total Pedidos, Taxa de Reclamação, Score.
- **Segmentação**:
    - Análise por faixa de valor gasto vs. taxa de reclamação.

### 4.5. Inteligência Geográfica
*Onde as fraudes estão acontecendo.*

**Componentes:**
- **Mapa de Calor (Florida Central)**:
    - *Fonte*: `get_regional_summary()`.
    - *Visual*: Mapa Choropleth pintando regiões (Clermont, Apopka, etc.) baseada na `missing_rate`.
- **Ranking Regional**:
    - Tabela lateral com as regiões mais problemáticas e métricas específicas (entregas vs. perdas).

### 4.6. Produtos & Perdas
*O que está sendo roubado.*

**Componentes:**
- **Top Produtos Extraviados**:
    - *Fonte*: `get_product_summary()`.
    - *Tabela*: Nome do Produto, Categoria, Qtd Sumiço, Preço Unitário, Preço Total Perdido.
- **Categorias de Risco**:
    - Gráfico de barras agregando perdas por Categoria de produto (Eletrônicos, Mercado, etc.).

---

## 5. Implementação Técnica Sugerida

Para alinhar com a agilidade e ciência de dados:

1.  **Framework**: Streamlit (pela facilidade de integração com Pandas/Python).
2.  **Estilização**:
    - Utilizar CSS customizado (`st.markdown('<style>...</style>')`) para replicar o look-and-feel do template HTML (cores do Walmart, cards com sombra).
    - Usar `streamlit-option-menu` para a Sidebar estilizada.
    - Usar `plotly.express` para gráficos interativos consistentes.
3.  **Estrutura de Arquivos Estipulada**:
    - `dashboard/app.py`: Ponto de entrada.
    - `dashboard/pages/`: Módulos individuais (1_Overview.py, 2_Drivers.py, etc).
    - `src/dashboard/components.py`: Componentes UI reutilizáveis (Cards, Header).

## 6. Próximos Passos (Plano de Ação)
1.  [ ] Criar `dashboard/app.py` com a estrutura básica e navegação.
2.  [ ] Implementar o CSS global para match com o tema Walmart.
3.  [ ] Conectar a "Home" com `get_overview_metrics` e `get_temporal_trends`.
4.  [ ] Implementar página de Motoristas com tabela interativa.
5.  [ ] Implementar página de Alertas usando `get_risk_alerts`.
