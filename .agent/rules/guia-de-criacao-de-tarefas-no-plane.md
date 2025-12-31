---
trigger: always_on
---

---

name: task-coordinator
description: "Coordena tarefas no Plane.so usando análise multidimensional e decisões contextuais inteligentes. Use quando precisar: (1) Capturar tarefas vagas e destrinchar em issues acionáveis, (2) Priorizar trabalho diário com tempo limitado, (3) Decidir estruturação (módulo vs issues, labels customizadas), (4) Categorizar por impacto (Critical Path, High Value, Quality of Life), (5) Balancear urgência vs importância (Matriz Eisenhower), (6) Criar estratégias de tempo (Deep Work, Melhoria Contínua, Quick Wins), (7) Organizar domínios LF.OS (11 projetos). Ferramentas plane:get_projects, plane:create_issue, plane:create_module, plane:create_label"

---

# Task Coordinator

Transforms vague tasks into structured, prioritized issues in Plane using multidimensional analysis.

## Quick Start

**Captura de tarefa vaga:**

```
User: "Melhorar Grafana mas sem perder tempo"
→ Analyze: Retorno (Médio), Urgência (Baixa), ROI (Baixo)
→ Strategy: Timebox 2h/semana, label "melhoria-continua"
→ Output: Módulo + 3 issues priorizadas
```

**Lista diária:**

```
User: "Tenho 4h hoje, Deep Work"
→ Query: plane:list_project_issues(all projects)
→ Filter: p0/p1 only, effort ≤ 4h
→ Sort: Priority desc, effort asc
→ Select: Greedy fill até 240min
```

**Bug crítico:**

```
User: "n8n falhando 50%"
→ Analyze: Alto impacto + urgente + bloqueante
→ Create: p0-crítico, labels [bug, n8n, bloqueante]
→ Plan: Fix imediato + otimizações futuras
```

## Decision Framework

Evaluate each task through 4 dimensions:

**1. Retorno vs Esforço**

- Critical Path → p0-crítico
- High Value → p1-alto
- Quality of Life → p2-médio
- Nice-to-Have → p3-baixo

**2. Urgência vs Importância (Eisenhower)**

```
          URGENTE         NÃO URGENTE
IMPORTANTE  p0 (fazer)     p1/p2 (agendar)
NÃO IMP     p3 (delegar)   não criar
```

**3. Natureza**

- Bug → `bug` label
- Otimização → `otimização`
- Feature → `feature`
- Create labels when recurrent (3+ uses)

**4. Granularidade**

- < 4h → Issue única
- \> 4h → Destrinchar
- 3+ related → Módulo

## Workflow

**Capture:**

1. Clarify if vague
2. Assess 4 dimensions
3. Determine priority (p0-p3)
4. Estimate effort (xs-xl)
5. Check if blocks others → add `bloqueante`

**Structure:**

1. Atomic (< 4h) or split?
2. Part of module (3+ tasks)?
3. Need custom labels?
4. HTML description with UUIDs

**Prioritize:**

1. List all Todo/In Progress
2. Filter by context (deep_work, melhoria, quick_wins)
3. Sort by priority + effort
4. Greedy select until time filled

**Execute:**

1. Work on selected tasks
2. Add comments on progress
3. Update state to Done
4. Suggest next task

## Context System

**LF.OS Structure:**

- 11 domains (WORK, INFRA, DEV, HOME, FINAN, SAUDE, etc)
- Each domain = Plane project
- Full IDs in `references/plane_ids.md`

**Labels System:**

- **Mandatory**: tipo + prioridade + esforço (3 mínimas)
- **Optional**: área, contexto (create when needed)
- **Colors**: Consistent palette (see references/labels.md)

**Naming:** `M[módulo].[sub].[task]: Descrição`

- M1.1: CV Master
- M1.1.0: Auditoria
- M1.2.3: Headline

## Templates

**Bug Crítico:**

```json
{
  "name": "[COMPONENT]: [Bug]",
  "priority": "urgent",
  "state": STATE_TODO,
  "labels": ["bug", "p0-crítico", "[effort]", "bloqueante"],
  "description_html": generate_description(...)
}
```

**Melhoria Contínua:**

```json
{
  "name": "[ÁREA]: Melhorar [aspecto]",
  "priority": "medium",
  "labels": ["otimização", "p2-médio", "[effort]", "melhoria-continua"],
  "description_html": "<p>Timebox: [X]h - não exceder</p>"
}
```

See `references/templates.md` for complete templates and `scripts/create_task.py` for automated creation.

## HTML Format

Plane uses structured HTML (NOT Markdown):

```html
<p class="editor-paragraph-block" data-id="[uuid4]">Text</p>
<h3 class="editor-heading-block" data-id="[uuid4]">Section</h3>
<ul class="list-disc pl-7 space-y-(--list-spacing-y) tight" data-id="[uuid4]">
  <li class="not-prose space-y-2" data-id="[uuid4]">
    <p class="editor-paragraph-block" data-id="[uuid4]">Item</p>
  </li>
</ul>
```

Use `scripts/generate_html.py` to create descriptions programmatically.

## Time Strategies

| Block             | When         | Labels                               |
| ----------------- | ------------ | ------------------------------------ |
| Deep Work         | 2-4h focused | p0, p1 + [m-4h, l-1dia]              |
| Melhoria Contínua | 1-2h/week    | p2 + [otimização, melhoria-continua] |
| Quick Wins        | 30min/day    | [xs-15min, s-1h] + p1/p2             |

## Rules

**Priorização:**

- P0 = bloqueante verdadeiro (sacred)
- Default = P2 (when in doubt)
- Avoid excessive P3 (consider not doing)

**Labels:**

- Min 3, max 7
- Create freely if 3+ uses
- Consistent colors

**Scope:**

- 1 task = 1 verb
- If "e" in name → split
- < 4h = atomic

**Modules:**

- 3+ related tasks
- Clear deliverables
- Naming: [Área] - [Objetivo] [Tempo?]

## Anti-Patterns

❌ Perfeccionismo: "Refatorar tudo" (xl-multi-dia, p3)  
✅ Incremental: Pequenas melhorias (m-4h, p2)

❌ Granularidade excessiva: "Abrir VSCode" (5min)  
✅ Atômico: "Implementar validação" (s-1h)

❌ Labels redundantes: task + tarefa + to-do  
✅ Essenciais: task + p1-alto + s-1h

## Detailed References

For comprehensive guidance:

- **Plane IDs**: `references/plane_ids.md` - All project/state/label IDs
- **Templates**: `references/templates.md` - Complete template library
- **Labels**: `references/labels.md` - Full label catalog with colors
- **Workflows**: `references/workflows.md` - Detailed workflow examples
- **Cases**: `references/cases.md` - Real-world scenario walkthroughs
