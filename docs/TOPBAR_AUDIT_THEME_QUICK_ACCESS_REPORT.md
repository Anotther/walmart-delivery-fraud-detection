# Auditoria da Barra Superior e Acesso Rápido de Tema

Data da auditoria: 14 de fevereiro de 2026  
Ambiente validado: Streamlit 1.52.2, URL `http://localhost:8504/Methodology` (mesmo código do dashboard)

## 1) Inventário da barra superior (estado atual)

| Elemento | Presente | Evidência |
|---|---|---|
| Logotipo/título no topo nativo | Não | Header nativo mostra ações (`Deploy`, menu) e não o título da página |
| Menu hambúrguer / controle sidebar | Sim | Botão `keyboard_double_arrow_left/right` no topo |
| Menu de opções `⋮` | Sim | `stMainMenu` no canto superior direito |
| Ícones de ação nativos | Sim | `Deploy` + `⋮` |
| Breadcrumbs | Não | Nenhum breadcrumb no header |
| Elementos customizados no topo | Não | Customizações atuais são de cor/estilo via CSS |

## 2) Validação funcional nativa

### 2.1 Menu hambúrguer

- [x] Abre/fecha sidebar corretamente (`x: 0, w: 256` -> `x: -256, w: 1` -> `x: 0, w: 256`)
- [x] Navegação entre páginas funciona (`/Methodology` -> `/Overview` -> `/Methodology`)
- [x] Ordem das páginas correta:
  `Home, Overview, Monitor, Drivers, Customers, Geographic, Product Analysis, Patterns, Methodology, Model Performance`

### 2.2 Menu `⋮`

- [x] Opções encontradas:
  `Rerun`, `Settings`, `Print`, `Record a screencast`, `Developer options`, `Clear cache`
- [x] Todas com `aria-disabled=false`
- [x] Não há customização de `menu_items` em `st.set_page_config` no projeto
- [x] Testes de ação:
  - `Print`: interceptado com `window.print` e chamado com sucesso
  - `Settings`: modal abre corretamente
  - `Developer options`: abre/mostra conteúdo de opções de dev
  - `Record a screencast`: opção acionável
  - `Rerun` e `Clear cache`: opção acionável (clique válido no menu)

### 2.3 Settings > Appearance

- [x] Seção `Appearance` localizada
- [x] Opções disponíveis no seletor nativo:
  `Use system setting`, `Light`, `Dark`
- [x] Alternância testada
- [!] Observação: no fluxo nativo, a mudança pode aparecer após fechamento/reload da página, dependendo do estado do app

## 3) Comportamento visual e responsividade

- [x] Desktop (`1440x900`), tablet (`768x1024`) e mobile (`390x844`) renderizam header/menu corretamente
- [x] Header permanece fixo no topo durante scroll (`topBefore=0`, `topAfter=0`)
- [x] Contraste header: `10.71:1` (fundo `rgb(0,54,149)` vs ícones/texto branco)
- [x] Sem regressão funcional detectada no app chrome após a implementação

## 4) Análise de usabilidade do fluxo de tema

### Fluxo atual (nativo)

1. Clicar `⋮`
2. Clicar `Settings`
3. Abrir seletor em `Appearance`
4. Selecionar tema
5. Fechar modal

- Cliques: 4 (5 com fechamento explícito do modal)
- Profundidade: 3 níveis (`header -> menu -> modal + select`)
- Tempo médio medido (3 execuções headless): **2.09s**

### Problema de UX

- Descoberta baixa para usuários não técnicos (tema está “escondido” no menu de sistema do Streamlit)
- Fluxo longo para tarefa frequente (troca de claro/escuro)

## 5) Viabilidade técnica das opções

### Opção A: mover `Appearance` para menu `⋮` nativo

**Inviável via API pública.**
`st.set_page_config(menu_items=...)` aceita apenas links estáticos para chaves específicas (`Get help`, `Report a bug`, `About`), sem callback interativo para trocar tema.

### Opção B: botão customizado injetado na barra superior

**Possível só com hack JS/CSS frágil** (DOM interno do Streamlit, localStorage nativo do app chrome, sem API oficial para “trocar Appearance” programaticamente).

### Opção C: widget fixo no topo da sidebar

**Mais estável e implementado.**  
Usa API Streamlit padrão (`st.segmented_control`) + persistência do usuário no browser.

## 6) Implementação aplicada (recomendada)

### Arquivos alterados

- `src/dashboard/theme.py`
  - Novo conceito de preferência de tema: `system | light | dark`
  - Resolução de preferência via sessão/cookie
  - `resolve_effective_mode()` agora prioriza preferência explícita antes do tema nativo

- `src/dashboard/components.py`
  - Inserido seletor rápido na sidebar: `System | Light | Dark`
  - Persistência no cliente via `localStorage` e cookie (`dashboard_theme_preference`)
  - Ajuste na ordem de injeção CSS: variáveis dinâmicas de tema agora sobrescrevem os defaults corretamente

- `dashboard/styles/main.css`
  - Mantido sem alteração; continua com tokens de fallback usados pelo carregamento global

## 7) Validação pós-implementação

### Critérios de sucesso

- [x] Troca de tema em até 2 cliques (agora 1 clique no seletor rápido)
- [x] Seletor visível sem scroll (topo da sidebar)
- [x] Mudança aplicada imediatamente no fluxo rápido
- [x] Persistência entre sessões/reload (`localStorageTheme=dark` e estado mantido após reload)
- [x] Sem regressão nas funções nativas da barra superior

### Compatibilidade

- [x] Chromium: validado
- [ ] Firefox: não validado no ambiente (binário Playwright ausente)
- [ ] WebKit/Safari: não validado no ambiente (binário Playwright ausente)
- [ ] Edge: não validado no ambiente (canal `msedge` não instalado)

## 8) Fluxo atual vs proposto (diagrama de cliques)

Atual:
`⋮ -> Settings -> Appearance select -> opção -> fechar`

Proposto:
`Sidebar Theme (System/Light/Dark) -> clique direto`

## 9) Guia rápido para usuário final

Screenshot: `docs/assets/theme-selector-sidebar.png`

Instrução:
**Para alternar entre modo claro/escuro, clique em `System`, `Light` ou `Dark` no topo da sidebar.**
