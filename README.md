# Walmart Delivery Fraud Detection

Sistema de detecção de fraudes em entregas e-commerce do Walmart para a região Central da Flórida.

## Objetivo

Identificar padrões de fraude em entregas onde clientes reportam itens não recebidos, determinando se a responsabilidade é de motoristas, consumidores ou problemas sistêmicos.

## Stack Tecnológica

- **Python 3.11+**
- **PostgreSQL** - Banco de dados
- **Streamlit** - Dashboard interativo
- **Scikit-learn** - Machine Learning
- **MLflow** - Tracking de experimentos
- **Pandas/SQLAlchemy** - Manipulação de dados

## Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd walmart-delivery-fraud-detection

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure o banco de dados
cp .env.example .env
# Edite .env com suas credenciais PostgreSQL

# Execute o setup
python scripts/setup_database.py
```

## Uso

### Dashboard

```bash
streamlit run dashboard/app.py
```

Acesse http://localhost:8501

### Notebooks

```bash
jupyter notebook notebooks/
```

### Treinamento de Modelos

```bash
python scripts/train_models.py
```

## Estrutura do Projeto

```
├── data/                   # Dados CSV
├── src/
│   ├── config/            # Configurações
│   ├── database/          # Modelos ORM e SQL
│   ├── etl/               # Pipeline ETL
│   ├── features/          # Feature Engineering
│   ├── models/            # Modelos ML
│   ├── analysis/          # Análises estatísticas
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
- **Overview**: Métricas gerais e tendências
- **Orders**: Análise de pedidos
- **Drivers**: Performance de motoristas
- **Customers**: Comportamento de clientes
- **Fraud Detection**: Scores de risco
- **Geographic**: Análise regional

### Modelos ML
- **Isolation Forest**: Detecção de anomalias
- **K-Means**: Segmentação de entidades
- **DBSCAN**: Detecção de outliers
- **Risk Scoring**: Sistema de pontuação de risco

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

## Configuração do Banco de Dados

O projeto requer PostgreSQL. Configure as credenciais no arquivo `.env`:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=walmart_fraud
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha
```

## Licença

Projeto acadêmico para fins educacionais.
