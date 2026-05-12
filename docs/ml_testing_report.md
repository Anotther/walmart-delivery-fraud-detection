# Relatório de Testes de Machine Learning

**Walmart Delivery Fraud Detection — Central Florida 2023**

> **Data de geração:** 2026-05-10
> **Branch:** `claude/ml-testing-report-edka8`
> **Ambiente:** Python 3.11.15 · pytest 9.0.3 · scikit-learn 1.8.0 · pandas 3.0.2

---

## 1. Resumo Executivo

| Indicador | Valor |
|-----------|-------|
| Total de testes coletados | 29 |
| Testes aprovados (PASSED) | 25 (86%) |
| Testes reprovados (FAILED) | 4 (14%) |
| Erros de coleta (ERROR) | 0 |
| Cobertura de `src/models/` | **0%** |
| Cobertura de `src/features/` | **0%** |
| Cobertura de `src/analysis/` | **~5%** (1 teste) |
| Cobertura de `src/config/` | **0%** |

A suíte atual cobre apenas **componentes de dashboard e infraestrutura**. Nenhum dos seis modelos de Machine Learning implementados possui teste automatizado. Isso representa um risco crítico, pois erros no pipeline de detecção de fraude podem passar despercebidos por releases completos.

**Ação imediata recomendada:** implementar testes unitários para `src/models/` e `src/features/` antes do próximo ciclo de retreinamento.

---

## 2. Arquitetura dos Modelos de ML

### 2.1 Visão Geral dos Componentes

```
                  ┌─────────────────────────────────┐
                  │         Pipeline de Treino       │
                  │       src/models/train.py        │
                  └──────────────┬──────────────────┘
                                 │ prepare_training_data()
                                 ▼
               ┌─────────────────────────────────────────┐
               │          Feature Engineering            │
               │  src/features/aggregations.py           │
               │  create_fraud_detection_dataset()       │
               └────┬──────────┬───────────┬────────┬───┘
                    │          │           │        │
              Drivers    Customers     Orders  Temporal
                    │          │           │        │
                    └──────────┴───────────┴────────┘
                                 │  14 features numéricas
                    ┌────────────┼────────────────────────┐
                    ▼            ▼                        ▼
        ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐
        │ IsolationForest│  │  K-Means     │  │  EnsembleDetector  │
        │  (anomalia)   │  │ (clustering) │  │  (IF + LOF)        │
        └──────┬────────┘  └──────┬───────┘  └──────────┬─────────┘
               │                  │                      │
               └──────────────────┴──────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    RiskScoringEngine     │
                    │  src/models/risk_scoring │
                    │  Score final 0-100       │
                    └─────────────────────────┘
```

### 2.2 Modelos Implementados

#### Detecção de Anomalias (`src/models/outlier_detection.py`)

| Modelo | Classe | Parâmetros-chave | Saída |
|--------|--------|-----------------|-------|
| Isolation Forest | `IsolationForestModel` | `contamination=0.1`, `n_estimators=100` | Score 0-100 (maior = mais risco) |
| Local Outlier Factor | `LOFModel` | `n_neighbors=20`, `contamination=0.1`, `novelty=True` | Score normalizado |
| Ensemble | `EnsembleOutlierDetector` | Votação majoritária: IF + LOF | Predição binária + score médio |

#### Clustering (`src/models/clustering.py`)

| Modelo | Classe | Parâmetros-chave | Saída |
|--------|--------|-----------------|-------|
| K-Means | `KMeansModel` | `n_clusters=5` (auto via silhouette, `max_k=10`) | Cluster 0–k, distância ao centroide |
| DBSCAN | `DBSCANModel` | `eps=0.5`, `min_samples=10` | Cluster label (`-1` = anomalia) |
| Analisador Combinado | `FraudClusterAnalyzer` | Usa K-Means + DBSCAN | Análise de clusters de alto risco |

#### Pontuação de Risco (`src/models/risk_scoring.py`)

```
RiskScoringEngine — Pesos por dimensão
├── missing_rate      → 25%
├── anomaly_score     → 25%
├── historical_pattern→ 20%
├── cluster_risk      → 15%
└── frequency         → 15%

Categorias (RiskThresholds):
├── Critical  : score ≥ 75
├── High      : score ≥ 50
├── Medium    : score ≥ 25
└── Low       : score ≥  0
```

#### Pontuação por Tipo de Entidade (`src/features/`)

| Entidade | Função | Pesos |
|---------|--------|-------|
| Motoristas | `get_driver_risk_scores()` | missing_rate 40% · pct_orders_with_missing 35% · volume 25% |
| Clientes | `get_customer_risk_scores()` | missing_rate 40% · pct_orders_with_missing 35% · frequência 25% |

#### Detecção de Padrões (`src/analysis/fraud_patterns.py`)

| Padrão | Função | Score |
|--------|--------|-------|
| Motorista com alta taxa | `detect_driver_fraud_patterns()` | 40 pts (taxa) + 35 pts (% pedidos) + 25 pts (volume) |
| Cliente suspeito | `detect_customer_fraud_patterns()` | 35 pts + 40 pts (100% pedidos) + 25 pts (alto valor) |
| Conluio motorista-cliente | `detect_collusion_patterns()` | missing_rate (capped 100), mín. 3 interações |
| Região anômala | `detect_regional_patterns()` | média + 2σ |

---

## 3. Resultados dos Testes Existentes

### 3.1 Execução Completa — `pytest tests/ -v`

```
============================= test session info ================================
Platform:  linux — Python 3.11.15
Pytest:    9.0.3
Rootdir:   /home/user/walmart-delivery-fraud-detection
Duration:  ~20 s
===============================================================================

tests/dashboard/test_component_sanitization.py::test_kpi_card_escapes_dynamic_fields_by_default         PASSED
tests/dashboard/test_component_sanitization.py::test_kpi_card_allows_html_value_when_enabled            PASSED
tests/dashboard/test_component_sanitization.py::test_insight_card_escapes_content_by_default            PASSED
tests/dashboard/test_component_sanitization.py::test_insight_card_keeps_html_when_explicitly_allowed    PASSED
tests/dashboard/test_theme_audit.py::test_scan_file_detects_white_plot_bg                               PASSED
tests/dashboard/test_theme_audit.py::test_repository_passes_theme_audit_strict                          PASSED
tests/dashboard/test_theme_tokens.py::test_theme_tokens_required_keys[light]                            PASSED
tests/dashboard/test_theme_tokens.py::test_theme_tokens_required_keys[dark]                             PASSED
tests/dashboard/test_theme_tokens.py::test_component_colors_contract_keys                               PASSED
tests/dashboard/test_theme_tokens.py::test_wcag_aa_contrast_for_core_text_pairs[light-text_primary-...]  PASSED
tests/dashboard/test_theme_tokens.py::test_wcag_aa_contrast_for_core_text_pairs[light-text_secondary-...] PASSED
tests/dashboard/test_theme_tokens.py::test_wcag_aa_contrast_for_core_text_pairs[dark-text_primary-...]   PASSED
tests/dashboard/test_theme_tokens.py::test_wcag_aa_contrast_for_core_text_pairs[dark-text_secondary-...] PASSED
tests/test_dashboard_pages_import.py::test_page_imports_without_error[1_Overview.py]                    PASSED
tests/test_dashboard_pages_import.py::test_page_imports_without_error[2_Monitor.py]                     PASSED
tests/test_dashboard_pages_import.py::test_page_imports_without_error[3_Drivers.py]                     PASSED
tests/test_dashboard_pages_import.py::test_page_imports_without_error[4_Customers.py]                   PASSED
tests/test_dashboard_pages_import.py::test_page_imports_without_error[5_Geographic.py]                  PASSED
tests/test_dashboard_pages_import.py::test_page_imports_without_error[6_Product_Analysis.py]            PASSED
tests/test_dashboard_pages_import.py::test_page_imports_without_error[7_Methodology.py]                 PASSED
tests/test_dashboard_pages_import.py::test_page_imports_without_error[8_Patterns.py]                    PASSED
tests/test_dashboard_pages_import.py::test_page_imports_without_error[9_Model_Performance.py]           PASSED
tests/test_database_manager.py::test_initialize_marks_database_available_on_success                     PASSED
tests/test_database_manager.py::test_initialize_enables_fallback_on_connection_error                    PASSED
tests/test_methodology_metadata.py::test_get_methodology_metadata_contract_nominal                      FAILED
tests/test_methodology_metadata.py::test_get_methodology_metadata_zero_orders                           FAILED
tests/test_methodology_metadata.py::test_get_methodology_metadata_missing_driver_customer_age           FAILED
tests/test_methodology_metadata.py::test_get_methodology_metadata_rebuilds_legacy_cached_payload        FAILED
tests/test_temporal_anomalies.py::test_detect_temporal_anomalies_default_threshold                      PASSED

==================== 4 failed, 25 passed in 20.49s ===========================
```

### 3.2 Análise dos Testes Reprovados

Todos os 4 falhos estão em `tests/test_methodology_metadata.py`. A causa raiz é única:

```
AttributeError: <module 'src.dashboard.data_cache'> has no attribute 'load_orders'
```

**Diagnóstico:** os testes tentam fazer `monkeypatch.setattr(data_cache_module, "load_orders", ...)`, mas a função `load_orders` foi removida ou renomeada em `src/dashboard/data_cache.py`. O módulo de testes não foi atualizado após essa refatoração.

**Testes afetados:**

| Teste | Linha de Falha |
|-------|----------------|
| `test_get_methodology_metadata_contract_nominal` | linha 89 |
| `test_get_methodology_metadata_zero_orders` | linha 142 |
| `test_get_methodology_metadata_missing_driver_customer_age` | linha 188 |
| `test_get_methodology_metadata_rebuilds_legacy_cached_payload` | linha 222 |

**Correção necessária:** atualizar `tests/test_methodology_metadata.py` para referenciar o atributo correto que substituiu `load_orders` em `src/dashboard/data_cache.py`.

---

## 4. Cobertura Atual de Testes por Módulo

| Módulo | Arquivo de Teste | Cobertura | Observação |
|--------|-----------------|-----------|-----------|
| `src/models/outlier_detection.py` | — | **0%** | Nenhum teste |
| `src/models/clustering.py` | — | **0%** | Nenhum teste |
| `src/models/risk_scoring.py` | — | **0%** | Nenhum teste |
| `src/models/train.py` | — | **0%** | Nenhum teste |
| `src/models/predict.py` | — | **0%** | Nenhum teste |
| `src/models/base.py` | — | **0%** | Nenhum teste |
| `src/features/driver_features.py` | — | **0%** | Nenhum teste |
| `src/features/customer_features.py` | — | **0%** | Nenhum teste |
| `src/features/order_features.py` | — | **0%** | Nenhum teste |
| `src/features/temporal_features.py` | — | **0%** | Nenhum teste |
| `src/features/aggregations.py` | — | **0%** | Nenhum teste |
| `src/analysis/temporal.py` | `test_temporal_anomalies.py` | **~5%** | 1 teste de contrato |
| `src/analysis/fraud_patterns.py` | — | **0%** | Nenhum teste |
| `src/analysis/geographic.py` | — | **0%** | Nenhum teste |
| `src/config/risk_thresholds.py` | — | **0%** | Nenhum teste |
| `src/dashboard/` | Vários arquivos | **~40%** | 24 testes (tema, sanitização, imports) |
| `src/database/` | `test_database_manager.py` | **~30%** | 2 testes de infra |

> **Cobertura estimada total do projeto:** ~12% (dominada pelo dashboard)
> **Cobertura do pipeline de ML:** ~1%

---

## 5. Lacunas Críticas de Testes

### 5.1 Modelos ML — Prioridade Alta

#### `IsolationForestModel` (`src/models/outlier_detection.py`)
- Treino com dados sintéticos e verificação de `fit()` sem exceção
- `predict()` retorna apenas valores em `{1, -1}`
- `get_risk_scores()` normaliza para intervalo `[0, 100]`
- Pontos de alta anomalia recebem score maior que pontos normais

#### `EnsembleOutlierDetector` (`src/models/outlier_detection.py`)
- Votação majoritária com resultados conflitantes entre IF e LOF
- `score()` é a média normalizada dos dois sub-modelos
- `get_model_predictions()` retorna predições individuais

#### `KMeansModel` (`src/models/clustering.py`)
- Detecção automática de k ótimo via silhouette score
- `get_silhouette_score()` retorna valor em `[-1, 1]`
- Distâncias ao centroide são não-negativas
- `get_cluster_statistics()` inclui missing_rate por cluster

#### `DBSCANModel` (`src/models/clustering.py`)
- Pontos de ruído são retornados por `get_noise_points()`
- Label `-1` classifica anomalias
- `get_cluster_info()` retorna número correto de clusters e pontos de ruído

#### `RiskScoringEngine` (`src/models/risk_scoring.py`)
- `fit()` treina ensemble e clustering sem erro
- `score_orders()` retorna `RiskScore` com `score` em `[0, 100]`
- Categorização correta: Critical ≥ 75, High ≥ 50, Medium ≥ 25, Low ≥ 0
- Pesos somam 1.0: `0.25 + 0.25 + 0.20 + 0.15 + 0.15 = 1.00`

### 5.2 Feature Engineering — Prioridade Alta

#### `get_driver_risk_scores()` (`src/features/driver_features.py`)
- `missing_rate = 0%` → score ≈ 0 (Low)
- `missing_rate = 100%` com todas as ordens afetadas → score ≈ 100 (Critical)
- Motorista com poucas ordens não vicia o score por volume

#### `get_customer_risk_scores()` (`src/features/customer_features.py`)
- Mesma estrutura de pesos que motoristas (40/35/25)
- Clientes VIP com alta taxa → flag High/Critical independente do segmento

#### `create_driver_features()` (`src/features/driver_features.py`)
- `missing_rate = total_items_missing / total_items_delivered`
- `pct_orders_with_missing = orders_with_missing / total_orders * 100`
- `experience_level` derivado de `total_trips` com limites corretos

#### `create_fraud_detection_dataset()` (`src/features/aggregations.py`)
- Merge entre features de ordem, motorista e cliente sem perda de linhas
- Coluna `is_fraud_candidate` derivada de `has_missing`
- 14 colunas numéricas produzidas por `get_feature_columns()`

### 5.3 Configuração e Limiares — Prioridade Média

#### `RiskThresholds` (`src/config/risk_thresholds.py`)

| Caso de borda | Resultado esperado |
|--------------|-------------------|
| `get_category(75)` | `'Critical'` |
| `get_category(74.9)` | `'High'` |
| `get_category(50)` | `'High'` |
| `get_category(25)` | `'Medium'` |
| `get_category(0)` | `'Low'` |
| `validate_score(101)` | `(False, "Score cannot exceed 100")` |
| `validate_score(-1)` | `(False, "Score cannot be negative")` |
| `validate_score("x")` | `(False, "Score must be numeric")` |

#### Sobrescrita via variáveis de ambiente
- `RISK_CRITICAL_THRESHOLD=80` → `RiskThresholds.CRITICAL == 80.0`
- Thresholds carregados em tempo de importação, não em runtime

### 5.4 Detecção de Padrões — Prioridade Média

#### `detect_driver_fraud_patterns()` (`src/analysis/fraud_patterns.py`)
- Motorista com `missing_rate > mean + 2σ` recebe 40 pontos
- Motorista com `pct_orders_with_missing > mean + 2σ` recebe 35 pontos
- Motorista com volume de itens faltantes > P95 recebe 25 pontos
- Score máximo: 100; mínimo para qualquer flag: 25

#### `detect_collusion_patterns()`
- Requer `min_interactions=3` para flagging
- Par com `missing_rate >= 50%` recebe score = missing_rate
- Par abaixo do limiar não gera `FraudIndicator`

---

## 6. Recomendações de Testes

### 6.1 Estrutura de Diretórios Proposta

```
tests/
├── models/
│   ├── test_isolation_forest.py     # IsolationForestModel, LOFModel
│   ├── test_ensemble.py             # EnsembleOutlierDetector
│   ├── test_clustering.py           # KMeansModel, DBSCANModel
│   └── test_risk_scoring.py         # RiskScoringEngine, RiskScore
├── features/
│   ├── test_driver_features.py      # create_driver_features, get_driver_risk_scores
│   ├── test_customer_features.py    # create_customer_features, get_customer_risk_scores
│   ├── test_order_features.py       # create_order_features
│   └── test_aggregations.py         # create_fraud_detection_dataset
├── analysis/
│   ├── test_fraud_patterns.py       # detect_*_fraud_patterns
│   └── test_temporal_anomalies.py   # já existe — expandir
├── config/
│   └── test_risk_thresholds.py      # RiskThresholds, get_category, validate_score
├── dashboard/                       # já existe
└── integration/
    └── test_full_pipeline.py        # ETL → Features → Treino → Predição
```

### 6.2 Exemplos de Testes Unitários

#### Isolation Forest — normalização de score

```python
# tests/models/test_isolation_forest.py
import numpy as np
import pytest
from src.models.outlier_detection import IsolationForestModel

@pytest.fixture
def trained_model():
    X = np.random.randn(200, 5)
    model = IsolationForestModel(contamination=0.1)
    model.fit(X)
    return model, X

def test_predictions_are_binary(trained_model):
    model, X = trained_model
    preds = model.predict(X)
    assert set(preds).issubset({1, -1})

def test_risk_scores_in_range(trained_model):
    model, X = trained_model
    scores = model.get_risk_scores(X)
    assert scores.min() >= 0
    assert scores.max() <= 100

def test_anomalies_have_higher_scores(trained_model):
    model, X = trained_model
    preds = model.predict(X)
    scores = model.get_risk_scores(X)
    mean_normal = scores[preds == 1].mean()
    mean_anomaly = scores[preds == -1].mean()
    assert mean_anomaly > mean_normal
```

#### RiskThresholds — valores limítrofes

```python
# tests/config/test_risk_thresholds.py
import pytest
from src.config.risk_thresholds import RiskThresholds

@pytest.mark.parametrize("score,expected", [
    (75.0, "Critical"),
    (74.9, "High"),
    (50.0, "High"),
    (49.9, "Medium"),
    (25.0, "Medium"),
    (24.9, "Low"),
    (0.0,  "Low"),
])
def test_get_category_boundaries(score, expected):
    assert RiskThresholds.get_category(score) == expected

@pytest.mark.parametrize("score,valid", [
    (0,   True),
    (100, True),
    (-1,  False),
    (101, False),
])
def test_validate_score(score, valid):
    is_valid, _ = RiskThresholds.validate_score(score)
    assert is_valid == valid
```

#### Driver Features — cálculo de missing_rate

```python
# tests/features/test_driver_features.py
import pandas as pd
from src.features.driver_features import create_driver_features, get_driver_risk_scores

def make_data():
    drivers = pd.DataFrame({
        "driver_id": ["WDID00001", "WDID00002"],
        "name": ["Alice", "Bob"],
        "age": [30, 45],
        "total_trips": [100, 500],
    })
    orders = pd.DataFrame({
        "order_id": range(10),
        "driver_id": ["WDID00001"] * 5 + ["WDID00002"] * 5,
        "items_delivered": [10] * 10,
        "items_missing":   [0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
        "order_amount":    [100.0] * 10,
    })
    return drivers, orders

def test_missing_rate_calculation():
    drivers, orders = make_data()
    features = create_driver_features(drivers, orders)
    alice = features[features["driver_id"] == "WDID00001"].iloc[0]
    assert alice["missing_rate"] == pytest.approx(5 / 50 * 100)

def test_risk_scores_in_range():
    drivers, orders = make_data()
    features = create_driver_features(drivers, orders)
    scored = get_driver_risk_scores(features)
    assert scored["risk_score"].between(0, 100).all()
```

### 6.3 Métricas de Qualidade para Modelos Não Supervisionados

Como o sistema não possui labels de fraude confirmados, as métricas de avaliação devem focar em:

| Métrica | Alvo | Como medir |
|---------|------|-----------|
| Silhouette Score (K-Means) | > 0.30 | `KMeansModel.get_silhouette_score(X)` |
| Taxa de anomalias (Isolation Forest) | ≈ 10% ± 2% | `(preds == -1).mean()` |
| Estabilidade de scores | CV < 5% | Re-treinar 5x, medir desvio dos scores |
| Cobertura de Critical/High risk | 5–15% das entidades | `(scores ≥ 50).mean()` |
| Concordância IF × LOF (Ensemble) | > 70% | `(if_pred == lof_pred).mean()` |

---

## 7. Roadmap de Implementação

### Sprint 1 — Fundação (Prioridade Alta)

- [ ] Corrigir falhas em `tests/test_methodology_metadata.py` (atualizar referência de `load_orders`)
- [ ] `tests/config/test_risk_thresholds.py` — cobrir `get_category`, `validate_score`, `to_dict`
- [ ] `tests/models/test_isolation_forest.py` — treino, predição binária, normalização 0–100
- [ ] `tests/models/test_clustering.py` — silhouette score, noise points DBSCAN, optimal k

### Sprint 2 — Feature Engineering (Prioridade Alta)

- [ ] `tests/features/test_driver_features.py` — missing_rate, pct_orders, risk categories
- [ ] `tests/features/test_customer_features.py` — mesmos contratos que drivers
- [ ] `tests/features/test_order_features.py` — delivery_period, is_high_value, has_missing
- [ ] `tests/features/test_aggregations.py` — create_fraud_detection_dataset sem perda de linhas

### Sprint 3 — Modelos Avançados e Padrões (Prioridade Média)

- [ ] `tests/models/test_ensemble.py` — votação majoritária, concordância sub-modelos
- [ ] `tests/models/test_risk_scoring.py` — RiskScoringEngine end-to-end
- [ ] `tests/analysis/test_fraud_patterns.py` — scoring por pontos, collusão, padrões regionais

### Sprint 4 — Integração e CI/CD (Prioridade Média)

- [ ] `tests/integration/test_full_pipeline.py` — ETL → Features → Treino → Predição
- [ ] Adicionar `pytest-cov` e exigir cobertura mínima de **80%** em `src/models/` e `src/features/`
- [ ] Configurar GitHub Actions para rodar `pytest` em PRs para `main`

---

## 8. Nota sobre Ambiente de Execução

Durante a execução desta análise, identificou-se que o ambiente de testes requer instalação manual de dependências não presentes no interpretador padrão do pytest:

```bash
# Dependências ausentes no ambiente pytest padrão
pip install pandas scikit-learn numpy plotly sqlalchemy streamlit
```

**Recomendação:** garantir que o `requirements.txt` seja instalado no mesmo ambiente Python usado pelo pytest. Considerar uso de `tox` ou `Makefile` para padronizar o ambiente de testes:

```makefile
# Makefile (exemplo)
test:
    pip install -r requirements.txt
    python3 -m pytest tests/ -v --tb=short
```

---

## 9. Conclusão

O sistema de detecção de fraudes do Walmart possui uma arquitetura de ML robusta e bem estruturada, com seis modelos distintos e um pipeline completo de feature engineering. No entanto, **a cobertura de testes do pipeline de ML é efetivamente zero** — todos os testes existentes cobrem apenas o dashboard e a infraestrutura de banco de dados.

As 4 falhas identificadas têm causa raiz única e são corrigíveis com baixo esforço. O maior risco operacional é a ausência de testes nos modelos de Isolation Forest, K-Means, DBSCAN, Ensemble e no `RiskScoringEngine` — qualquer regressão nessas camadas passaria silenciosa para produção.

A implementação do roadmap proposto, começando pelo Sprint 1, elevaria a cobertura do pipeline de ML de ~0% para ~60% em duas semanas, reduzindo significativamente o risco de falhas não detectadas no processo de retreinamento e predição.

---

*Relatório gerado automaticamente pela análise estática do repositório + execução da suíte de testes existente.*
*Para dúvidas ou contribuições, abra uma issue ou comentário neste PR.*
