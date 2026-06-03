# Post LinkedIn — Walmart Fraud Detection

---

## Texto do post

$6,5 bilhões em perdas. 53% vieram de itens "sumidos" em entregas.

Construí um sistema end-to-end para mapear esse padrão nos dados — e os números que surgiram são mais claros do que eu esperava.

Analisei 10.000 pedidos reais de 2023 na Flórida Central. O que encontrei:

→ 15% dos pedidos com itens reportados como ausentes (1.502 casos)
→ $517K em valor de pedidos afetados no período
→ 1 motorista com taxa de missing 6x acima da média do sistema
→ Altamonte Springs: cidade com maior concentração — 16,2% vs. 15% de média regional
→ Variação mensal de até 3,6 p.p. (fev: 13,4% → mai: 17,0%)

O desafio central foi técnico: sem labels históricos de fraude confirmada, aprendizado supervisionado não funciona. A saída foi usar **Isolation Forest** para isolar anomalias + **K-Means/DBSCAN** para segmentar perfis de risco + um **Risk Score Engine** que combina 5 fatores em uma nota de 0 a 100.

O resultado é um dashboard com 9 módulos analíticos — de alertas em tempo real a análise de padrões de colisão entre motorista e cliente — rastreado com **MLflow** e deployado no **Streamlit Cloud**.

Stack: Python · scikit-learn · MLflow · Streamlit · PostgreSQL · Plotly

→ Dashboard live + repositório nos comentários.

Em detecção de fraude logística, você priorizaria Recall ou Precision? Me conta nos comentários.

#DataScience #MachineLearning #Python #FraudDetection #DataAnalytics

---

## Metadados do post

**Formato recomendado:** PDF carrossel (8 slides) + texto acima
**Dimensões dos slides:** 1080 × 1350px (proporção 4:5)
**Arquivo do carrossel:** `docs/linkedin-post/carousel.html` → exportar como PDF
**Hashtags:** #DataScience #MachineLearning #Python #FraudDetection #DataAnalytics

## Como exportar o carrossel como PDF

1. Abrir `docs/linkedin-post/carousel.html` no Chrome
2. `Ctrl+P` → Salvar como PDF
3. Configurações: **Margens: Nenhuma** e **Escala: 100%**. A regra `@page { size: 1080px 1350px }` já fixa as dimensões 4:5 — não é preciso ajustar orientação manualmente.
4. Conferir no preview que cada slide ocupa uma página inteira, sem cortes.

**Dica:** Para exportação automatizada e pixel-perfect, use Puppeteer/Playwright com `page.pdf({ width: '1080px', height: '1350px', printBackground: true })`.
