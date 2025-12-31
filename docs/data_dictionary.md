# Dicionário de Dados

## Tabelas de Origem (CSV)

### orders.csv
Tabela principal de pedidos.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| date | DATE | Data do pedido |
| order_id | VARCHAR(50) | ID único do pedido |
| order_amount | VARCHAR | Valor do pedido (formato: "$1,234.56") |
| region | VARCHAR(50) | Região de entrega |
| items_delivered | INTEGER | Quantidade de itens entregues |
| items_missing | INTEGER | Quantidade de itens não entregues |
| delivery_hour | TIME | Hora da entrega |
| driver_id | VARCHAR(20) | ID do motorista |
| customer_id | VARCHAR(20) | ID do cliente |

### customers_data.csv
Dados dos clientes.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| customer_id | VARCHAR(20) | ID único (formato: WCID####) |
| customer_name | VARCHAR(100) | Nome do cliente |
| customer_age | INTEGER | Idade do cliente |

### drivers_data.csv
Dados dos motoristas.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| driver_id | VARCHAR(20) | ID único (formato: WDID#####) |
| driver_name | VARCHAR(100) | Nome do motorista |
| age | INTEGER | Idade do motorista |
| Trips | INTEGER | Total de entregas em 2023 |

### products_data.csv
Catálogo de produtos.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| produc_id* | VARCHAR(30) | ID do produto (nota: typo no nome) |
| product_name | VARCHAR(200) | Nome do produto |
| category | VARCHAR(100) | Categoria |
| price | VARCHAR | Preço (formato: "$12.34") |

### missing_items_data.csv
Produtos reportados como não entregues.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| order_id | VARCHAR(50) | ID do pedido |
| product_id_1 | VARCHAR(30) | 1º produto não entregue |
| product_id_2 | VARCHAR(30) | 2º produto não entregue (nullable) |
| product_id_3 | VARCHAR(30) | 3º produto não entregue (nullable) |

## Features Calculadas

### Order Features
| Feature | Tipo | Descrição |
|---------|------|-----------|
| total_items | INTEGER | items_delivered + items_missing |
| missing_rate | FLOAT | (items_missing / total_items) * 100 |
| is_high_value | BOOLEAN | order_amount > 75th percentile |
| delivery_period | CATEGORY | Night/Morning/Afternoon/Evening |
| day_of_week | STRING | Nome do dia |
| is_weekend | BOOLEAN | Sábado ou Domingo |
| order_size | CATEGORY | Small/Medium/Large |
| has_missing | BOOLEAN | items_missing > 0 |

### Driver Features
| Feature | Tipo | Descrição |
|---------|------|-----------|
| total_orders | INTEGER | Total de pedidos entregues |
| total_items_delivered | INTEGER | Total de itens entregues |
| total_items_missing | INTEGER | Total de itens não entregues |
| missing_rate | FLOAT | Taxa de itens não entregues |
| orders_with_missing | INTEGER | Pedidos com problemas |
| pct_orders_with_missing | FLOAT | % de pedidos com problemas |
| age_group | CATEGORY | 18-25/26-35/36-45/46-55/55+ |
| experience_level | CATEGORY | Novice/Intermediate/Experienced/Expert |
| risk_score | FLOAT | Score de risco 0-100 |
| risk_category | CATEGORY | Low/Medium/High/Critical |

### Customer Features
| Feature | Tipo | Descrição |
|---------|------|-----------|
| total_orders | INTEGER | Total de pedidos realizados |
| total_spent | FLOAT | Valor total gasto |
| avg_order_value | FLOAT | Valor médio por pedido |
| total_items_ordered | INTEGER | Total de itens pedidos |
| total_items_missing | INTEGER | Total de itens não recebidos |
| missing_rate | FLOAT | Taxa de itens não recebidos |
| orders_with_missing | INTEGER | Pedidos com problemas |
| age_group | CATEGORY | 18-25/26-35/36-45/46-55/56-65/65+ |
| customer_segment | CATEGORY | Low Value/Medium Value/High Value/VIP |
| risk_score | FLOAT | Score de risco 0-100 |
| risk_category | CATEGORY | Low/Medium/High/Critical |

## Regiões

Central Florida (dados de 2023):
- Altamonte Springs
- Apopka
- Casselberry
- Clermont
- Kissimmee
- Lake Mary
- Orlando
- Oviedo
- Sanford
- Winter Park
