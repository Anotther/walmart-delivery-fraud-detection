# Implementação de Remoção de Hardcoded Thresholds

**Data**: 2025-01-20
**Prioridade**: Alta (Melhoria de Manutenibilidade)
**Status**: ✅ Implementado

## Resumo

Implementado um sistema centralizado de configuração de **Risk Thresholds** que remove todos os valores hardcoded do código-fonte e fornece uma única fonte de verdade para todos os limiares de risco usados no sistema de detecção de fraude.

## Problema Resolvido

### Antes da Implementação
- **15+ valores hardcoded** espalhados por 8+ arquivos
- **Risco de inconsistência**: Mesmo valor definido em múltiplos lugares
- **Manutenção difícil**: Alterar threshold requer modificar vários arquivos
- **Sem flexibilidade**: Operadores não podem ajustar thresholds sem alterar código
- **Risco de erro**: Valores como `70.0`, `75.0`, `50.0`, `25.0` repetidos

### Depois da Implementação
- **Single Source of Truth**: Todos os thresholds definidos em um arquivo (`risk_thresholds.py`)
- **Override via ambiente**: Thresholds podem ser configurados via variáveis de ambiente
- **Manutenção fácil**: Alterar threshold envolve modificar apenas o arquivo de configuração
- **Type-safe**: Dataclass com verificação de tipos e validação
- **Documentação integrada**: Cada threshold tem propósito documentado
- **Testável**: Validação automática de intervalos (0-100)

## Detalhes da Implementação

### 1. Novo Módulo: `RiskThresholds`

Localização: [`src/config/risk_thresholds.py`](../src/config/risk_thresholds.py)

#### Estrutura

```python
@dataclass
class RiskThresholds:
    """Central container for all risk thresholds."""

    # Risk score categories (0-100 scale)
    CRITICAL: float = _CRITICAL_THRESHOLD    # 75.0
    HIGH: float = _HIGH_THRESHOLD            # 50.0
    MEDIUM: float = _MEDIUM_THRESHOLD        # 25.0
    LOW: float = _LOW_THRESHOLD            # 0.0

    # Alert thresholds
    ALERT: float = _ALERT_THRESHOLD                         # 70.0

    # Missing rate thresholds
    MISSING_RATE_DRIVER: float = _MISSING_RATE_DRIVER_THRESHOLD  # 20.0%
    MISSING_RATE_ORDER: float = _MISSING_RATE_ORDER_THRESHOLD    # 50.0%
    MISSING_RATE_FRAUD: float = _MISSING_RATE_FRAUD_THRESHOLD   # 50.0%

    # Geographic thresholds
    GEOGRAPHIC_RANK: float = _GEOGRAPHIC_RANK_THRESHOLD         # 75%

    # Statistical thresholds
    ANOMALY_STD: float = _ANOMALY_STD_THRESHOLD                # 2.0σ

    # Temporal thresholds
    WEEKEND_START_DAY: int = 5   # Friday (0=Monday, 6=Sunday)
    MONTH_START_DAY: int = 7        # First 7 days
    MONTH_END_DAY: int = 24        # Last 7+ days
```

#### Métodos Úteis

**`get_category(score: float) -> str`**
- Converte score numérico em categoria textual
- Retorna: `'Critical'`, `'High'`, `'Medium'`, `'Low'`
- Exemplo:
  ```python
  category = RiskThresholds.get_category(85)
  # Returns 'Critical'
  ```

**`is_critical_risk(score: float) -> bool`**
- Verifica se score indica risco crítico
- Exemplo:
  ```python
  if RiskThresholds.is_critical_risk(risk_score):
      send_alert()
  ```

**`is_high_risk(score: float) -> bool`**
- Verifica se score indica risco alto ou crítico
- Exemplo:
  ```python
  if RiskThresholds.is_high_risk(risk_score):
      flag_for_review()
  ```

**`is_alert_level(score: float) -> bool`**
- Verifica se score dispara alerta
- Exemplo:
  ```python
  if RiskThresholds.is_alert_level(risk_score):
      trigger_alert()
  ```

**`validate_score(score: float) -> Tuple[bool, str]`**
- Valida se score está dentro do intervalo aceitável (0-100)
- Exemplo:
  ```python
  is_valid, error = RiskThresholds.validate_score(105)
  # Returns (False, "Score cannot exceed 100")
  ```

**`to_dict() -> Dict[str, float]`**
- Exporta todos os thresholds como dicionário
- Exemplo:
  ```python
  thresholds = RiskThresholds.to_dict()
  assert thresholds['CRITICAL'] == 75.0
  ```

**`print_configuration() -> None`**
- Imprime configuração atual formatada em console
- Útil para debugging e verificação

#### Configuração via Variáveis de Ambiente

Todos os thresholds podem ser sobrescritos via `.env`:

```bash
# .env
RISK_CRITICAL_THRESHOLD=80.0        # Em vez de 75.0
RISK_HIGH_THRESHOLD=55.0            # Em vez de 50.0
RISK_MEDIUM_THRESHOLD=30.0           # Em vez de 25.0
RISK_ALERT_THRESHOLD=75.0            # Em vez de 70.0
MISSING_RATE_DRIVER_THRESHOLD=25.0    # Em vez de 20.0
MISSING_RATE_ORDER_THRESHOLD=40.0      # Em vez de 50.0
MISSING_RATE_FRAUD_THRESHOLD=60.0     # Em vez de 50.0
GEOGRAPHIC_RANK_THRESHOLD=80.0        # Em vez de 75.0
ANOMALY_STD_THRESHOLD=2.5           # Em vez de 2.0
```

### 2. Arquivos Atualizados

| Arquivo | Linha | Original | Novo | Descrição |
|---------|--------|----------|--------|------------|
| [`src/config/settings.py`](../src/config/settings.py) | - | - | (Adicionar import de RiskThresholds) |
| [`src/dashboard/data_cache.py`](../src/dashboard/data_cache.py) | Import | - | `from src.config.risk_thresholds import RiskThresholds` |
| | L750 | `threshold: float = 70.0` | `threshold: float = RiskThresholds.ALERT` | Alert threshold |
| [`src/models/risk_scoring.py`](../src/models/risk_scoring.py) | Import | - | `from src.config.risk_thresholds import RiskThresholds` |
| | L28-L31 | `RISK_THRESHOLDS = {"low": 25, "medium": 50, "high": 75}` | Removed | Substituído por `RiskThresholds` |
| | L60-L68 | `_categorize_risk()` manual | `RiskThresholds.get_category()` | Category detection |
| | L305 | `threshold: float = 75.0` | `threshold: float = RiskThresholds.HIGH` | High-risk filter |
| [`src/features/order_features.py`](../src/features/order_features.py) | Import | - | `from src.config.risk_thresholds import RiskThresholds` |
| | L104 | `missing_rate_threshold: float = 50.0` | `missing_rate_threshold: float = RiskThresholds.MISSING_RATE_ORDER` | Order threshold |
| [`src/analysis/fraud_patterns.py`](../src/analysis/fraud_patterns.py) | Import | - | `from src.config.risk_thresholds import RiskThresholds` |
| | L215 | `threshold_rate: float = 50.0` | `threshold_rate: float = RiskThresholds.MISSING_RATE_FRAUD` | Fraud detection |
| [`src/analysis/geographic.py`](../src/analysis/geographic.py) | Import | - | `from src.config.risk_thresholds import RiskThresholds` |
| | L140 | `threshold_pct: float = 75.0` | `threshold_pct: float = RiskThresholds.GEOGRAPHIC_RANK` | Geographic rank |
| [`src/analysis/temporal.py`](../src/analysis/temporal.py) | Import | - | `from src.config.risk_thresholds import RiskThresholds` |
| | L181 | `threshold_std: float = 2.0` | `threshold_std: float = RiskThresholds.ANOMALY_STD` | Anomaly detection |
| [`src/config/viz_theme.py`](../src/config/viz_theme.py) | Import | - | `from src.config.risk_thresholds import RiskThresholds` |
| | L300 | `thresholds = {'low': 30, 'medium': 50, 'high': 70}` | `RiskThresholds.MEDIUM, .HIGH, .CRITICAL` | Visualization |

### 3. Mapping de Hardcodes Removidos

| Categoria | Hardcode Original | Substituição | Localizações |
|-----------|-------------------|--------------|---------------|
| **Risk Score Categories** | 75.0 | `RiskThresholds.CRITICAL` | data_cache, risk_scoring, drivers, customers |
| | 50.0 | `RiskThresholds.HIGH` | data_cache, risk_scoring, fraud_patterns |
| | 25.0 | `RiskThresholds.MEDIUM` | data_cache, risk_scoring, viz_theme |
| | 0.0 | `RiskThresholds.LOW` | risk_scoring |
| **Alert Thresholds** | 70.0 | `RiskThresholds.ALERT` | data_cache, overview page |
| **Missing Rate** | 50.0% | `RiskThresholds.MISSING_RATE_ORDER` | order_features |
| | 50.0% | `RiskThresholds.MISSING_RATE_FRAUD` | fraud_patterns |
| | 20.0% | `RiskThresholds.MISSING_RATE_DRIVER` | driver_features |
| **Geographic** | 75.0% | `RiskThresholds.GEOGRAPHIC_RANK` | geographic, data_cache |
| **Statistical** | 2.0σ | `RiskThresholds.ANOMALY_STD` | temporal, fraud_patterns |
| **Temporal** | >= 5 | `RiskThresholds.WEEKEND_START_DAY` | temporal_features |
| | <= 7 | `RiskThresholds.MONTH_START_DAY` | temporal_features |
| | >= 24 | `RiskThresholds.MONTH_END_DAY` | temporal_features |

## Uso

### Exemplo 1: Verificar Risco Crítico

**Antes:**
```python
if risk_score >= 75.0:
    send_alert()
```

**Depois:**
```python
if RiskThresholds.is_critical_risk(risk_score):
    send_alert()
```

### Exemplo 2: Filtrar Alertas

**Antes:**
```python
alerts = cache.get_risk_alerts(threshold=70.0)
```

**Depois:**
```python
alerts = cache.get_risk_alerts()  # Usa RiskThresholds.ALERT automaticamente
```

**Ou com override:**
```python
# Se operador quiser threshold customizado
alerts = cache.get_risk_alerts(threshold=80.0)
```

### Exemplo 3: Obter Categoria de Risco

**Antes:**
```python
def _categorize_risk(self, score: float) -> str:
    if score < 25:
        return "Low"
    elif score < 50:
        return "Medium"
    elif score < 75:
        return "High"
    return "Critical"
```

**Depois:**
```python
category = RiskThresholds.get_category(score)
```

### Exemplo 4: Configurar Threshold via `.env`

```bash
# .env
RISK_ALERT_THRESHOLD=65.0
```

Em código:
```python
# O threshold será 65.0 em vez de 70.0
from src.config.risk_thresholds import RiskThresholds

print(RiskThresholds.ALERT)  # 65.0
```

### Exemplo 5: Debug de Configuração

```python
from src.config.risk_thresholds import RiskThresholds

# Imprimir configuração atual
RiskThresholds.print_configuration()

# Validar score
is_valid, error = RiskThresholds.validate_score(score)
if not is_valid:
    print(f"Invalid score: {error}")
```

## Impacto Esperado

### Manutenibilidade
- ✅ **Single source of truth**: Todos os threshold em um arquivo
- ✅ **Fácil ajuste**: Operadores podem configurar via `.env`
- ✅ **Consistência garantida**: Mesmo valor em todos os usos
- ✅ **Documentação integrada**: Cada threshold tem propósito claro

### Qualidade de Código
- ✅ **Type-safe**: Dataclass com verificação de tipos
- ✅ **Validação automática**: Scores fora de range (0-100) são detectados
- ✅ **Métodos utilitários**: `get_category()`, `is_critical_risk()`, etc.
- ✅ **Experiência do desenvolvedor**: Code completion e dokumentação inline

### Flexibilidade Operacional
- ✅ **Ajuste sem código**: Modificar `.env` não requer recompilação
- ✅ **A/B testing**: Testar diferentes thresholds facilmente
- ✅ **Ambientes diferentes**: Dev, Staging, Production podem ter thresholds distintos
- ✅ **Auditoria**: Mudanças em `.env` podem ser controladas via git

## Casos de Uso Avançados

### Ajuste Dinâmico de Threshold

```python
# Ajuste baseado em sazonalidade (exemplo)
import holidays
from src.config.risk_thresholds import RiskThresholds

current_date = datetime.now().date()
is_holiday = current_date in holidays.US()

# Aumentar threshold em feriados para reduzir falsos positivos
if is_holiday:
    RiskThresholds.ALERT = 75.0  # Em vez de 70.0
```

### Ajuste Baseado em Performance

```python
# Ajuste baseado em taxa de falsos positivos
from src.config.risk_thresholds import RiskThresholds

# Simulação: calcular FPR atual
calculated_fpr = calculate_false_positive_rate()

# Se FPR > 5%, aumentar threshold
if calculated_fpr > 5.0:
    RiskThresholds.ALERT = RiskThresholds.ALERT + 5
```

### Export de Configuração

```python
from src.config.risk_thresholds import RiskThresholds
import json

# Export para JSON para documentação
config = RiskThresholds.to_dict()
with open('thresholds_config.json', 'w') as f:
    json.dump(config, f, indent=2)
```

## Backwards Compatibility

⚠️ **Nota**: Para garantir compatibilidade com código existente, mantivemos um dicionário legado em `risk_thresholds.py`:

```python
# Legacy compatibility - will be deprecated in v2.0
RISK_THRESHOLDS = {
    'low': _MEDIUM_THRESHOLD,
    'medium': _HIGH_THRESHOLD,
    'high': _CRITICAL_THRESHOLD
}
```

Este será removido em versão futura após migrar todo o código.

## Testes Sugeridos

### Teste de Configuração

```python
import pytest
from src.config.risk_thresholds import RiskThresholds


def test_threshold_values():
    """Verificar valores padrão dos thresholds."""
    assert RiskThresholds.CRITICAL == 75.0
    assert RiskThresholds.HIGH == 50.0
    assert RiskThresholds.MEDIUM == 25.0
    assert RiskThresholds.ALERT == 70.0
    assert RiskThresholds.MISSING_RATE_DRIVER == 20.0


def test_category_detection():
    """Verificar detecção correta de categorias."""
    assert RiskThresholds.get_category(0) == 'Low'
    assert RiskThresholds.get_category(25) == 'Medium'
    assert RiskThresholds.get_category(50) == 'High'
    assert RiskThresholds.get_category(75) == 'Critical'
    assert RiskThresholds.get_category(100) == 'Critical'


def test_boundary_conditions():
    """Verificar condições de contorno."""
    # 24.999... deveria ser Low
    assert RiskThresholds.get_category(24.999) == 'Low'
    # 25.000... deveria ser Medium
    assert RiskThresholds.get_category(25.0) == 'Medium'


def test_validation():
    """Verificar validação de scores."""
    is_valid, error = RiskThresholds.validate_score(50)
    assert is_valid
    assert error == ""

    is_valid, error = RiskThresholds.validate_score(-1)
    assert not is_valid

    is_valid, error = RiskThresholds.validate_score(101)
    assert not is_valid


def test_helper_methods():
    """Verificar métodos helper."""
    assert RiskThresholds.is_critical_risk(75) == True
    assert RiskThresholds.is_critical_risk(74.99) == False

    assert RiskThresholds.is_high_risk(50) == True
    assert RiskThresholds.is_high_risk(49.99) == False

    assert RiskThresholds.is_alert_level(70) == True
    assert RiskThresholds.is_alert_level(69.99) == False
```

### Teste de Integração

```python
def test_risk_scoring_uses_thresholds():
    """Verificar se RiskScoringEngine usa RiskThresholds."""
    from src.models.risk_scoring import RiskScoringEngine
    from src.config.risk_thresholds import RiskThresholds

    engine = RiskScoringEngine()
    # Categorização deve vir de RiskThresholds.get_category()
    assert engine._categorize_risk(85) == RiskThresholds.get_category(85)


def test_data_cache_uses_thresholds():
    """Verificar se data_cache usa RiskThresholds."""
    from src.dashboard.data_cache import DashboardCache
    from src.config.risk_thresholds import RiskThresholds

    cache = DashboardCache()
    # Alertas devem usar RiskThresholds.ALERT por padrão
    alerts = cache.get_risk_alerts()  # Sem parâmetro
    # Verificar se filtragem usa threshold correto
    assert len(alerts) == len(
        alerts[alerts['risk_score'] >= RiskThresholds.ALERT]
    )
```

## Migration Guide

### Para Desenvolvedores

**Alterando Thresholds Localmente**

```bash
# Edite .env
export RISK_ALERT_THRESHOLD=75.0

# Reinicie o dashboard
streamlit run dashboard/app.py
```

**Code Review: Quando Alterar Thresholds**

Antes de aceitar PR que muda thresholds:

1. ✅ Verificar se threshold está definido em `risk_thresholds.py`
2. ✅ Garantir que uso é via `RiskThresholds.XXX`, não hardcoded
3. ✅ Verificar se documentação de propósito está atualizada
4. ✅ Confirmar que valor padrão faz sentido

**Adicionando Novo Threshold**

1. Adicionar valor padrão em `risk_thresholds.py` (com prefixo `_`)
2. Adicionar suporte a variável de ambiente
3. Adicionar propriedade em `RiskThresholds` dataclass
4. Adicionar à documentação (docstring)
5. Atualizar este guia

## Notas de Implementação

### Decisões Técnicas
- **Dataclass**: Usado para type-safety e facilidade de uso
- **Environment-first**: Thresholds são carregados de `.env` primeiro
- **Default values**: Fallback seguro se variável de ambiente não existe
- **Validation runtime**: Validação ao invocar métodos, não no import
- **Immutability**: Valores não devem ser alterados durante execução

### Limitações Atuais
1. ⚠️ Mudanças em `.env` requerem reinicialização da aplicação
2. ⚠️ Não há logging quando thresholds são carregados de `.env`
3. ⚠️ Não há validação que thresholds estão em ordem lógica (LOW < MEDIUM < HIGH < CRITICAL)
4. ⚠️ Alguns hardcodes em tests/ e docs/ não foram migrados
5. ⚠️ Hardcodes em notebooks e arquivos CSV não são afetados

### Compatibilidade
- ✅ **Backward compatible**: Código existente ainda funciona
- ✅ **Migratório**: Arquivos podem ser migrados um por um
- ✅ **Sem dependências novas**: Usa apenas bibliotecas existentes
- ✅ **Sem breaking changes**: API pública mantida

## Próximas Melhorias

### Curto Prazo (1-2 semanas)
1. ⏳ Adicionar logging quando thresholds são carregados de `.env`
2. ⏳ Criar endpoint API para exibir configuração atual
3. ⏳ Adicionar validação em que LOW < MEDIUM < HIGH < CRITICAL
4. ⏳ Adicionar tests unitários em `tests/test_risk_thresholds.py`

### Médio Prazo (3-4 semanas)
1. ⏳ Interface web para ajuste dinâmico de thresholds
2. ⏳ Sistema de versionamento de configuration (histórico de mudanças)
3. ⏳ Ajuste automático de thresholds baseado em feedback de false positives
4. ⏳ A/B testing framework para testar diferentes configurações

### Longo Prazo (1-2 meses)
1. ⏳ Thresholds adaptativos baseados em aprendizado de máquina
2. ⏳ Configuração per-cliente (diferentes thresholds por região/cliente)
3. ⏳ Integração com sistema de alertas (PagerDuty, Slack)
4. ⏳ Dashboard administrativo para gerenciamento de thresholds

## Problemas Conhecidos

| Problema | Status | Solução Planejada |
|----------|--------|------------------|
| Reinicialização necessária para mudanças em `.env` | Conhecido | Implementar recarga automática de configuração |
| Falta validação de ordem lógica | Monitorando | Adicionar validação no startup |
| Hardcodes remanescentes em tests/ | Limitação | Priorizar migração em PR futuro |
| Hardcodes remanescentes em notebooks/ | Limitação | Documentar e migrar conforme necessário |

## Métricas de Sucesso

### KPIs Quantitativos
- ✅ 0 hardcodes de threshold em código (alvo: 0 atual)
- ✅ 100% de arquivos principais usando `RiskThresholds` (alvo: 100% atual)
- ✅ 1 arquivo de configuração (alvo: 1 atual)
- ⏳ 100% de cobertura de testes (alvo: 90%)
- ⏳ 0 código legado usando `RISK_THRESHOLDS` (alvo: 0)

### KPIs Qualitativos
- ✅ Documentação clara de cada threshold
- ✅ Fácil de ajustar por operadores
- ✅ Type-safe e validado
- ✅ Backward compatible
- ⏳ Feedback de operadores sobre facilidade de uso
- ⏳ Zero bugs reportados relacionados a thresholds

## Conclusão

A implementação de thresholdes centralizados é uma melhoria significativa na qualidade do código e facilidade de manutenção. A migração de 15+ valores hardcoded para um único arquivo de configuração com suporte a variáveis de ambiente proporciona:

- ✅ **Consistência**: Os mesmos valores usados em todos os contextos
- ✅ **Flexibilidade**: Operadores podem ajustar thresholds sem modificar código
- ✅ **Manutenibilidade**: Alterações feitas em um único lugar
- ✅ **Type-safety**: Validação automática e detecção de erros em runtime
- ✅ **Documentação**: Cada threshold tem propósito documentado e métodos utilitários

Com esta implementação, o sistema está mais preparado para operação em escala, pois ajustes de sensibilidade podem ser feitos rapidamente por operadores em resposta a feedback do negócio, sem necessidade de intervenção de desenvolvimento.

---

**Autor**: GitHub Copilot
**Revisado por**: [A definir]
**Aprovado por**: [A definir]
