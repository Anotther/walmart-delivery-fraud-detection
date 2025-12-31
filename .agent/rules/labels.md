---
trigger: always_on
---

# Label Catalog

Complete label reference with colors and usage guidelines.

## Color Palette

```python
CORES = {
    # Severidade
    "crítico": "#dc2626",
    "alto": "#f97316",
    "médio": "#eab308",
    "baixo": "#6b7280",

    # Natureza
    "bug": "#ef4444",
    "feature": "#3b82f6",
    "otimização": "#10b981",
    "refactor": "#8b5cf6",
    "debt": "#f59e0b",

    # Contexto
    "bloqueante": "#dc2626",
    "quick-win": "#22c55e",
    "experimental": "#a855f7",
    "melhoria-continua": "#14b8a6",
}
```

## When to Create Labels

✅ **Create when:**

- Category recurrent (3+ issues)
- Useful for filters
- Changes task handling

❌ **Don't create when:**

- One-time case
- Similar exists
- Won't add value to filters

## Common Custom Labels

### Natureza Técnica

```json
{
  "bug": { "color": "#ef4444", "description": "Algo quebrado" },
  "feature": { "color": "#3b82f6", "description": "Criar novo" },
  "otimização": { "color": "#10b981", "description": "Melhorar existente" },
  "refactor": { "color": "#8b5cf6", "description": "Reestruturar" },
  "tech-debt": { "color": "#f59e0b", "description": "Dívida técnica" }
}
```

### Contexto Especial

```json
{
  "bloqueante": {
    "color": "#dc2626",
    "description": "Bloqueia outras tarefas"
  },
  "quick-win": {
    "color": "#22c55e",
    "description": "Alto impacto, baixo esforço"
  },
  "melhoria-continua": {
    "color": "#14b8a6",
    "description": "Melhorias incrementais"
  },
  "experimental": { "color": "#a855f7", "description": "Testar algo novo" }
}
```

### Ferramentas/Áreas

```json
{
  "n8n": { "color": "#ea4b71", "description": "Workflows n8n" },
  "grafana": { "color": "#f46800", "description": "Dashboards Grafana" },
  "homelab": { "color": "#0ea5e9", "description": "Servidor homelab" }
}
```
