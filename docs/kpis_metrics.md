# KPIs e Metricas - Walmart Fraud Detection

Este documento define os KPIs e metricas principais para o dashboard e relatorios executivos.

## 1. KPIs Principais (Executive Summary)

### 1.1 Metricas de Volume
| KPI | Descricao | Formula | Fonte |
|-----|-----------|---------|-------|
| Total Orders | Numero total de pedidos | COUNT(order_id) | orders |
| Total Revenue | Receita total | SUM(order_amount) | orders |
| Total Items | Total de itens pedidos | SUM(items_delivered + items_missing) | orders |
| Active Drivers | Motoristas ativos | COUNT(DISTINCT driver_id) | orders |
| Active Customers | Clientes ativos | COUNT(DISTINCT customer_id) | orders |

### 1.2 Metricas de Fraude
| KPI | Descricao | Formula | Threshold |
|-----|-----------|---------|-----------|
| Missing Rate | Taxa de itens faltantes | items_missing / total_items * 100 | <5% = Bom, 5-10% = Atencao, >10% = Critico |
| Orders with Issues | % pedidos com problemas | orders_with_missing / total_orders * 100 | <10% = Bom |
| Estimated Loss | Perda estimada | items_missing * avg_item_value | - |
| Fraud Exposure | Exposicao a fraude | total_orders * missing_rate * avg_order_value | - |

### 1.3 Metricas de Risco
| KPI | Descricao | Formula | Threshold |
|-----|-----------|---------|-----------|
| High Risk Drivers | Motoristas de alto risco | COUNT(risk_category IN ('High', 'Critical')) | <5% do total |
| High Risk Customers | Clientes de alto risco | COUNT(risk_category IN ('High', 'Critical')) | <3% do total |
| Suspicious Pairs | Pares suspeitos driver-customer | COUNT(suspicious_pairs) | Monitorar |
| Critical Alerts | Alertas criticos | COUNT(risk_score > 75) | Acao imediata |

---

## 2. KPIs por Dimensao

### 2.1 Driver Performance
| Metrica | Descricao | Uso |
|---------|-----------|-----|
| driver_missing_rate | Taxa de falta por motorista | Identificar motoristas problematicos |
| driver_order_count | Pedidos por motorista | Volume de trabalho |
| driver_risk_score | Score de risco (0-100) | Priorizacao de auditoria |
| pct_orders_with_missing | % pedidos com problemas | Performance individual |

### 2.2 Customer Behavior
| Metrica | Descricao | Uso |
|---------|-----------|-----|
| customer_missing_rate | Taxa de falta por cliente | Identificar repeat offenders |
| customer_total_spent | Gasto total | Segmentacao VIP |
| customer_risk_score | Score de risco (0-100) | Monitoramento |
| orders_with_missing | Pedidos com problemas | Historico de reclamacoes |

### 2.3 Regional Analysis
| Metrica | Descricao | Uso |
|---------|-----------|-----|
| region_missing_rate | Taxa de falta por regiao | Identificar hotspots |
| region_order_volume | Volume por regiao | Distribuicao geografica |
| region_revenue | Receita por regiao | Importancia economica |
| region_risk_index | Indice de risco regional | Priorizacao de acoes |

### 2.4 Temporal Patterns
| Metrica | Descricao | Uso |
|---------|-----------|-----|
| monthly_missing_rate | Taxa mensal | Sazonalidade |
| hourly_pattern | Padrao por hora | Horarios de risco |
| weekday_pattern | Padrao por dia da semana | Planejamento |
| trend_direction | Tendencia (up/down/stable) | Monitoramento |

---

## 3. KPIs de Machine Learning

### 3.1 Model Performance
| Metrica | Descricao | Target |
|---------|-----------|--------|
| anomaly_detection_rate | Taxa de deteccao de anomalias | >80% |
| false_positive_rate | Taxa de falsos positivos | <20% |
| model_confidence | Confianca media do modelo | >0.7 |
| coverage | % dados cobertos pelo modelo | >95% |

### 3.2 Risk Scoring
| Metrica | Descricao | Uso |
|---------|-----------|-----|
| risk_score_distribution | Distribuicao de scores | Calibracao |
| high_risk_conversion | Taxa de confirmacao de fraude | Validacao |
| score_stability | Estabilidade temporal | Monitoramento |

---

## 4. Metricas para Dashboard

### 4.1 Overview Page
```
- total_orders, total_revenue, missing_rate
- orders_with_issues, estimated_loss
- active_drivers, active_customers
- alerts_count, critical_alerts
```

### 4.2 Drivers Page
```
- driver_count, avg_missing_rate
- risk_distribution (pie chart)
- top_10_risky_drivers (table)
- missing_rate_by_experience (bar chart)
```

### 4.3 Customers Page
```
- customer_count, avg_missing_rate
- segment_distribution (pie chart)
- top_suspicious_customers (table)
- spending_vs_missing (scatter plot)
```

### 4.4 Fraud Detection Page
```
- risk_score_histogram
- anomaly_count, model_metrics
- collusion_pairs (table)
- investigation_priority_list (table)
```

### 4.5 Geographic Page
```
- region_map (heatmap)
- regional_comparison (bar chart)
- hotspots_list (table)
- regional_trends (line chart)
```

---

## 5. Metricas para Relatorio Executivo

### 5.1 Sumario Executivo
1. **Exposicao Total a Fraude**: $X (baseado em items missing * valor medio)
2. **Taxa de Problemas**: X% dos pedidos com itens faltantes
3. **Tendencia**: Aumento/Reducao de X% vs periodo anterior
4. **Acoes Recomendadas**: Lista priorizada

### 5.2 Analise de Causa Raiz
1. **Por Responsavel**:
   - Drivers: X% dos casos atribuiveis
   - Customers: X% dos casos atribuiveis
   - Sistemico: X% dos casos

2. **Por Categoria**:
   - Produtos de alto valor: X% das perdas
   - Categorias especificas: Lista

### 5.3 Recomendacoes Quantificadas
| Medida | Reducao Esperada | Custo | ROI |
|--------|------------------|-------|-----|
| Verificacao por foto | 30-40% | $X | X:1 |
| Assinatura digital | 20-30% | $X | X:1 |
| Auditoria de drivers | 15-25% | $X | X:1 |
| Monitoramento ML | 40-50% | $X | X:1 |

---

## 6. Frequencia de Atualizacao

| Metrica | Frequencia | Responsavel |
|---------|------------|-------------|
| KPIs principais | Diaria | Automatico |
| Risk scores | Tempo real | ML Pipeline |
| Alertas | Tempo real | Sistema |
| Relatorios | Semanal/Mensal | BI Team |

---

## 7. Data Sources Mapping

```
Notebook 01 (EDA Orders) -> Overview metrics, temporal trends
Notebook 02 (Drivers/Customers) -> Risk scores, suspicious entities
Notebook 03 (Fraud Analysis) -> Pattern detection, recommendations
Notebook 04 (ML Models) -> Anomaly scores, model metrics
Notebook 05 (Products) -> Product risk, category analysis
Notebook 06 (Dashboard Prep) -> Aggregated views, cached data
```
