# Carrossel LinkedIn — Avaliação das versões e versão final

Processo: a partir da base (com `github.com/Anotther` removido do rodapé),
foram derivadas 3 versões de design. Cada uma foi renderizada em 1080×1350
(Playwright + Chromium headless) e avaliada com screenshots dos slides
representativos (capa e KPIs).

## Versões derivadas

| Arquivo | Direção | Características |
|---|---|---|
| `carousel-v1.html` | **Editorial Hairline** | Fundo plano, sem caixas (réguas/hairlines), tipografia display grande, muito respiro |
| `carousel-v2.html` | **Soft Elevated** | Cards brancos arredondados (18px), sombras profundas, fundo radial mais frio |
| `carousel-v3.html` | **Analyst Grid** | Textura de papel-milimetrado, numerais tabulares, cantos retos (6px), barra superior tracejada |

## Notas (0–10)

| Critério | Base | V1 | V2 | **V3** |
|---|---|---|---|---|
| Legibilidade mobile | 9 | 9 | 9 | 9 |
| Hierarquia / scan | 8 | 9 | 8 | 9 |
| Alinhamento de marca | 9 | 8 | 9 | 9 |
| Originalidade | 6 | 8 | 6 | 9 |
| Espaço-negativo | 6 | 5 | 6 | 6 |
| Fidelidade em PDF | 9 | 9 | 8 | 9 |
| **Média** | **7.8** | **8.0** | **7.7** | **8.5** |

**Ranking:** 🥇 V3 · 🥈 V1 · 🥉 Base · V2

## Por que V3 vence

- É a única versão que **parece uma ferramenta de analytics de fraude** —
  coerência temática — mantendo as cores da marca Walmart.
- Textura sutil de grade + barra tracejada = ar técnico sem prejudicar leitura.
- Numerais tabulares alinham todas as métricas verticalmente.

## Achados que alimentaram a versão final

1. **Falha transversal (todas as versões):** no slide de KPIs os cards eram
   altos demais e o conteúdo flutuava, criando espaço morto. O V1 (hairline)
   piorava isso. → Final usa `align-content:center` na grade, deixando os
   cards no tamanho do conteúdo e centralizando o bloco.
2. **Tipografia:** o display maior do V1 dá mais presença. → H1 66px no final.
3. **Identidade:** V3 vira a base visual do final.

## Versão final (produção)

`docs/linkedin-post/carousel.html` = **V3 (Analyst Grid)** + tipografia do V1
+ correção do espaço-negativo dos KPIs. Exportada em
`docs/linkedin-post/walmart-fraud-detection-carousel.pdf` (1080×1350, 8 páginas).

> Os arquivos `carousel-v*.html`, o `build.py` e os screenshots em `shots/`
> ficam versionados como registro do processo de design e podem ser
> regenerados com `python3 build.py`.
