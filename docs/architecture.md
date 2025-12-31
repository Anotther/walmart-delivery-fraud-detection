# Arquitetura do Sistema

## Visão Geral

O sistema de detecção de fraudes do Walmart é uma aplicação de Data Science/ML que analisa dados de entregas e-commerce para identificar padrões de fraude.

## Stack Tecnológica

- **Python 3.11+**: Linguagem principal
- **PostgreSQL**: Banco de dados relacional
- **Streamlit**: Dashboard interativo
- **Scikit-learn**: Machine Learning
- **MLflow**: Tracking de experimentos
- **Pandas/SQLAlchemy**: Manipulação de dados

## Estrutura de Camadas

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│                   (Streamlit Dashboard)                     │
├─────────────────────────────────────────────────────────────┤
│                     ANALYSIS LAYER                          │
│     (src/analysis/ - Fraud Patterns, Geographic, etc.)     │
├─────────────────────────────────────────────────────────────┤
│                       ML LAYER                              │
│  (src/models/ - Isolation Forest, K-Means, Risk Scoring)  │
├─────────────────────────────────────────────────────────────┤
│                    FEATURE LAYER                            │
│      (src/features/ - Order, Driver, Customer Features)    │
├─────────────────────────────────────────────────────────────┤
│                       ETL LAYER                             │
│      (src/etl/ - Extractors, Transformers, Loaders)       │
├─────────────────────────────────────────────────────────────┤
│                      DATA LAYER                             │
│              (PostgreSQL + CSV Files)                       │
└─────────────────────────────────────────────────────────────┘
```

## Módulos Principais

### 1. Config (`src/config/`)
- `settings.py`: Configurações globais, paths, variáveis de ambiente
- `database.py`: Conexão PostgreSQL, session management

### 2. ETL (`src/etl/`)
- `extractors.py`: Leitura de CSVs
- `transformers.py`: Limpeza e transformação de dados
- `loaders.py`: Carga no PostgreSQL

### 3. Features (`src/features/`)
- `order_features.py`: Features de pedidos
- `driver_features.py`: Features de motoristas
- `customer_features.py`: Features de clientes
- `temporal_features.py`: Features temporais
- `aggregations.py`: Agregações combinadas

### 4. Analysis (`src/analysis/`)
- `descriptive.py`: Estatísticas descritivas
- `fraud_patterns.py`: Detecção de padrões de fraude
- `geographic.py`: Análise regional
- `temporal.py`: Análise temporal

### 5. Models (`src/models/`)
- `base.py`: Classe base para modelos
- `outlier_detection.py`: Isolation Forest, LOF
- `clustering.py`: K-Means, DBSCAN
- `risk_scoring.py`: Sistema de scoring de risco
- `train.py`: Pipeline de treinamento
- `predict.py`: Pipeline de predição

### 6. Dashboard (`dashboard/`)
- `app.py`: Aplicação principal
- `pages/`: Páginas do dashboard
- `components/`: Componentes reutilizáveis

## Fluxo de Dados

```
CSV Files
    │
    ▼
[Extractors] ──► Raw DataFrames
    │
    ▼
[Transformers] ──► Clean DataFrames
    │
    ├───────────────┬──────────────────┐
    ▼               ▼                  ▼
[PostgreSQL]   [Features]         [Analysis]
    │               │                  │
    └───────────────┼──────────────────┘
                    ▼
              [ML Models]
                    │
                    ▼
              [Risk Scores]
                    │
                    ▼
             [Dashboard]
```

## Modelos de Machine Learning

### Isolation Forest
- Detecção de anomalias não-supervisionada
- Identifica ordens/entidades outliers

### K-Means Clustering
- Segmentação de entidades
- Identificação de clusters de risco

### DBSCAN
- Detecção de ruído/anomalias
- Não requer número de clusters pré-definido

### Ensemble Outlier Detector
- Combina Isolation Forest + LOF
- Voting para maior confiança

## Banco de Dados

### Tabelas Principais
- `customers`: Dados de clientes
- `drivers`: Dados de motoristas
- `products`: Catálogo de produtos
- `orders`: Pedidos (fact table)
- `missing_items`: Produtos não entregues

### Views Analíticas
- `vw_driver_fraud_stats`: Estatísticas por motorista
- `vw_customer_fraud_stats`: Estatísticas por cliente
- `vw_regional_stats`: Estatísticas por região
- `vw_monthly_trends`: Tendências mensais
- `vw_hourly_patterns`: Padrões por hora
