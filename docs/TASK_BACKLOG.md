# Backlog e Rastreamento de Tarefas - Walmart Fraud Detection

Este documento serve como a fonte única da verdade para a sincronização entre os agentes de **Backend** e **Frontend**.

## 📋 Protocolo de Uso
1. **Nunca apague tarefas concluídas immediately**: Mova-as para a seção "Concluído" para histórico.
2. **Tags de Agente**: Use `[BACKEND]` ou `[FRONTEND]` no início da tarefa para indicar responsabilidade.
3. **Bloqueios**: Se uma tarefa estiver bloqueada por outra, adicione uma nota `(Bloqueado por: [Nome da Tarefa])`.
4. **Delegação**: Para delegar, crie uma nova tarefa na seção "A Fazer" com a tag do agente apropriado.

---

## 🚀 Em Progresso
*Nenhuma tarefa em andamento no momento.*

## 📌 A Fazer (Prioridade Alta)

### Frontend (Prioridade: Construção do Dashboard)
- [ ] `[FRONTEND]` **Configuração Inicial do Streamlit**: Criar `dashboard/app.py` com navegação básica (Sidebar) e configurar tema (`.streamlit/config.toml` ou CSS injetado).
- [ ] `[FRONTEND]` **Estilização Global**: Implementar CSS para replicar as cores do Walmart (Azul #004c91, Amarelo #ffc220) em `src/dashboard/styles.css` (ou string no python).
- [ ] `[FRONTEND]` **Página Home (Overview)**: Criar layout da página inicial consumindo métricas gerais.
- [ ] `[FRONTEND]` **Componentes de UI**: Criar funções reutilizáveis para Cards de KPI e Gráficos Padrão em `src/dashboard/components.py`.

### Backend (Prioridade: Suporte ao Dashboard)
- [ ] `[BACKEND]` **Validação do Data Cache**: Verificar se `src/dashboard/data_cache.py` está retornando os dados no formato exato que o frontend espera (ex: tipos de dados, tratamento de nulos).
- [ ] `[BACKEND]` **API de Filtros**: Implementar ou revisar métodos para suportar filtros de data/região se o dashboard exigir interatividade avançada.
- [ ] `[BACKEND]` **Hardening**: Adicionar tratamento de erros robusto caso os arquivos parquet não existam ou estejam corrompidos.

## 📅 Planejado (Backlog)
- [ ] `[FRONTEND]` Página de Análise de Motoristas.
- [ ] `[FRONTEND]` Página de Mapa (Inteligência Geográfica).
- [ ] `[BACKEND]` Otimização de performance do LRU Cache.
- [ ] `[GERAL]` Definição de testes automatizados para o dashboard.

## ✅ Concluído
- [x] `[FRONTEND]` Auditoria da barra superior do dashboard + implementação de acesso rápido de tema na sidebar com persistência (`src/dashboard/theme.py`, `src/dashboard/components.py`, `docs/TOPBAR_AUDIT_THEME_QUICK_ACCESS_REPORT.md`).
- [x] `[GERAL]` Análise inicial da arquitetura (`dashboard/ANATOMY.md`).
- [x] `[BACKEND]` Implementação inicial do cache de dados (`src/dashboard/data_cache.py`).
- [x] `[DATA]` Geração dos notebooks de análise e preparação de dados.
- [x] `[FRONTEND]` Padronização global claro/escuro com seletor Auto/Claro/Escuro, tokens centralizados e auditoria de hardcodes (`src/dashboard/theme.py`, `src/dashboard/components.py`, `dashboard/styles/main.css`, `scripts/audit_dashboard_theme.py`).
- [x] `[FRONTEND]` Refatoração da Página de Análise de Clientes com Customer Case Workbench (`dashboard/pages/4_Customers.py`).
- [x] `[FRONTEND]` Padronização visual da página Customers com baseline Geographic (`dashboard/pages/4_Customers.py`).
- [x] `[FRONTEND]` Tooltips adicionados aos cards KPI da Methodology (`dashboard/pages/7_Methodology.py`).
- [x] `[FRONTEND]` Melhoria de espaçamento e tooltips nos cards da seção How Fraud Behaves em Patterns (`dashboard/pages/8_Patterns.py`).
