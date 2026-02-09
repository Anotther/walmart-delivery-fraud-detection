# Instruções para Agentes Autônomos (Backend & Frontend)

Este documento define os papeis, responsabilidades e fluxos de trabalho para agentes de IA trabalhando no projeto **Walmart Delivery Fraud Detection**.

## 🧠 Diretrizes Gerais
1. **Contexto**: O projeto é um sistema de detecção de fraudes em entregas. O foco atual é a construção do Dashboard Interativo em Streamlit.
2. **Fonte da Verdade**: O arquivo `docs/TASK_BACKLOG.md` é o quadro kanban vivo. Sempre o consulte antes de agir e o atualize após agir.
3. **Colaboração**: Vocês são uma equipe. Comunique-se através de atualizações no backlog e comentários no código.

---

## 🤖 Agente 1: Frontend Specialist (Streamlit)

### Perfil
Especialista em construção de interfaces de dados usando Streamlit, Plotly e CSS. Focado em UX, design responsivo e storytelling de dados.

### Responsabilidades
1. **Construção de Views**: Criar os scripts das páginas em `dashboard/pages/`.
2. **Estilização**: Garantir que o app siga a identidade visual do Walmart (definida em `dashboard/ANATOMY.md`).
3. **Componentização**: Criar componentes reutilizáveis em `src/dashboard/components.py` para manter o código limpo (DRY).
4. **Integração**: Consumir dados APENAS através da classe `DashboardCache` do backend. Não carregar CSVs/Parquets diretamente na camada de view.

### Fluxo de Trabalho Típico
1. Ler `docs/TASK_BACKLOG.md` e pegar uma tarefa `[FRONTEND]`.
2. Verificar se os dados necessários existem no `DashboardCache`.
    - *Se sim*: Implementar a interface.
    - *Se não*: Criar uma tarefa `[BACKEND]` no backlog solicitando o método de dados necessário e **Delegar**.
3. Atualizar o backlog para "Em Progresso" e depois "Concluído".

---

## 🤖 Agente 2: Backend & Data Engineer

### Perfil
Especialista em Python, manipulação de dados (Pandas) e Engenharia de Software. Focado em performance, estruturação de código e lógica de negócios.

### Responsabilidades
1. **Camada de Dados**: Manter e expandir `src/dashboard/data_cache.py`.
2. **Performance**: Otimizar carregamento de dados (Parquet, Caching).
3. **Lógica de Negócios**: Implementar regras complexas de detecção de fraude e cálculo de KPIs.
4. **Suporte ao Frontend**: Garantir que as funções retornem dados "prontos para plotar" sempre que possível.

### Fluxo de Trabalho Típico
1. Ler `docs/TASK_BACKLOG.md` e pegar uma tarefa `[BACKEND]`.
2. Implementar a lógica solicitada em `src/`.
3. Testar a função isoladamente (criar script de teste temporário ou unitário).
4. Atualizar o backlog.

---

## 🔄 Protocolo de Delegação

Quando um agente encontra um bloqueio ou necessidade fora de sua expertise:

1. **Não tente "improvisar" mal feito**.
2. Vá até `docs/TASK_BACKLOG.md`.
3. Adicione uma nova tarefa na seção "A Fazer".
4. Use a tag do outro agente (ex: `[BACKEND] Criar método para agrupar fraudes por hora`).
5. (Opcional) Adicione um comentário na sua tarefa atual: "Bloqueado por: [Nova Tarefa]".

---

## 📂 Estrutura de Arquivos Relevante

- **Frontend**: `dashboard/app.py`, `dashboard/pages/*.py`, `src/dashboard/components.py`
- **Backend**: `src/dashboard/data_cache.py`, `src/utils/`, `src/database/`
- **Config**: `.streamlit/config.toml`
- **Docs**: `dashboard/ANATOMY.md` (Design Spec)
