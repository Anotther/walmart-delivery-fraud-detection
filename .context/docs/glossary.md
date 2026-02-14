# Glossary

## Domain Terms
- Fraud exposure: estimated financial impact from missing-item patterns.
- Missing rate: percentage of missing items relative to ordered items.
- Orders with issues: percentage of orders with at least one missing item.
- Risk score: composite score (0-100) used to prioritize investigation.
- Risk category: qualitative bucket such as Low, Medium, High, Critical.
- Suspicious pair: repeated high-risk interaction between a driver and customer.
- Hotspot: region with elevated fraud indicators.

## Data Entities
- Order: delivery transaction with amount, region, timestamp, customer, driver.
- Customer: purchasing entity associated with order history and missing claims.
- Driver: fulfillment entity with delivery history and incident profile.
- Product: catalog item referenced by order and missing-items datasets.
- Missing item record: product references reported as not delivered for an order.

## Technical Terms
- ETL: extract, transform, and load pipeline for source CSV datasets.
- Dashboard cache: cached and shaped datasets exposed to Streamlit pages.
- Outlier model: anomaly detector (Isolation Forest, LOF, DBSCAN variants).
- Clustering: unsupervised segmentation used to identify risk archetypes.
- Feature engineering: derivation of model-ready and analysis-ready metrics.

## Process Terms
- Source of truth board: `docs/TASK_BACKLOG.md`.
- Manual dashboard checklist: `docs/PLAN-dashboard-streamlit.md`.
- Theme audit: checks to ensure design token consistency and accessibility.

## Related Resources
- `../../docs/data_dictionary.md`
- `../../docs/kpis_metrics.md`
- `./project-overview.md`
