# Walmart Delivery Fraud Detection

Sistema de detecção de fraudes em entregas e-commerce do Walmart para a região Central da Flórida.

## Objetivo

Identificar padrões de fraude em entregas onde clientes reportam itens não recebidos, determinando se a responsabilidade é de motoristas, consumidores ou problemas sistêmicos.

## Stack Tecnológica

- **Python 3.11+**
- **PostgreSQL 14+** - Banco de dados transacional/analítico
- **Streamlit** - Dashboard interativo
- **Scikit-learn** - Machine Learning
- **MLflow** - Tracking de experimentos
- **Pandas / SQLAlchemy** - ETL e acesso a dados
- **Plotly** - Visualizações

## Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd walmart-delivery-fraud-detection

# Crie um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure o banco de dados
cp .env.example .env
# Edite .env com suas credenciais PostgreSQL

# Execute o setup completo (schema + views + ETL inicial)
python scripts/setup_database.py
```

## Comandos Principais

### ETL (somente carga/recarga)

```bash
python scripts/run_etl.py
```

### Treinamento de Modelos

```bash
python scripts/train_models.py
```

### Dashboard

```bash
streamlit run dashboard/app.py
```

Acesse http://localhost:8501

### Notebooks

```bash
jupyter notebook notebooks/
```

## Qualidade e Segurança

```bash
# Testes
pytest tests/

# Segurança + qualidade (Bandit + pip-audit + pytest)
scripts/security_checks.sh
```

## Estrutura do Projeto

```
├── data/                   # Dados CSV
├── src/
│   ├── config/            # Configurações
│   ├── database/          # Conexão, manager e SQL versionado
│   ├── etl/               # Pipeline ETL
│   ├── features/          # Feature Engineering
│   ├── models/            # Modelos ML
│   ├── analysis/          # Análises estatísticas
│   ├── dashboard/         # Camada de cache/dados para páginas
│   └── utils/             # Utilitários
├── dashboard/             # Streamlit App
├── notebooks/             # Jupyter Notebooks
├── scripts/               # Scripts CLI
├── docs/                  # Documentação
└── tests/                 # Testes
```

## Dados

O projeto analisa 5 datasets de entregas em 2023:

- **orders.csv** - Pedidos (fact table)
- **customers_data.csv** - Clientes
- **drivers_data.csv** - Motoristas
- **products_data.csv** - Produtos
- **missing_items_data.csv** - Itens não entregues

## Funcionalidades

### Dashboard
- **Overview**: visão executiva, KPIs e tendências
- **Monitor**: monitoramento operacional e drift/sinais
- **Drivers**: análise de risco por motorista
- **Customers**: análise de risco por cliente
- **Geographic**: hotspots e distribuição regional
- **Product Analysis**: itens/produtos com maior incidência
- **Methodology**: documentação metodológica e qualidade
- **Patterns**: padrões suspeitos e hipóteses analíticas
- **Model Performance**: métricas e saúde dos modelos

### Modelos ML
- **Isolation Forest**: Detecção de anomalias
- **K-Means / DBSCAN**: Segmentação e outliers
- **Ensemble Outlier Detector**: combinação de detectores
- **Risk Scoring Engine**: sistema de pontuação de risco

### Análises
- Padrões de fraude por motorista/cliente
- Tendências temporais (mensal, semanal, horária)
- Hotspots geográficos
- Detecção de potencial conluio

## Notebooks

1. `01_eda_orders.ipynb` - Análise exploratória de pedidos
2. `02_eda_drivers_customers.ipynb` - Análise de motoristas e clientes
3. `03_fraud_analysis.ipynb` - Análise detalhada de fraude
4. `04_model_experiments.ipynb` - Experimentos de ML
5. `05_products_missing_items.ipynb` - Produtos e itens faltantes
6. `06_dashboard_data_preparation.ipynb` - Preparação de dados para dashboard
7. `07_model_monitoring_retraining.ipynb` - Monitoramento e retreino

## Configuração do Banco de Dados

O projeto requer PostgreSQL. Configure as credenciais no arquivo `.env`:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=walmart_fraud
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha
APP_ENV=development
DEBUG=False
```

## Licença

Projeto acadêmico para fins educacionais.
