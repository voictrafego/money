---
tipo: audit-empirico
escopo: coerência dos preços-alvo entre modos/lentes, 2 ações por setor da B3
data: 2026-07-11
engine: pós v2.2 Fase 01 (01-01..01-04 executados; re-verificação = gaps_found)
fonte_dados: 01-AUDIT-COERENCIA-DATA.json (22 ações, dados reais CVM cache + yfinance)
mapeia_para:
  fase_1_gap: "classificador over-routing a ciclica + hard-route financeira errado (MDIA3)"
  fase_2: "20/22 ações suspensas por motor_pendente — resolvido pelos motores da Fase 2"
  fase_3: "guarda-corpos DDM (valores ≤0/degenerados) + suspensão/freio no modo Ranking + divergência entre lentes"
---

# Auditoria de Coerência Setorial — Analista de Dividendos

**Pergunta:** o motor e suas constantes produzem preços-alvo coerentes com a realidade,
independentemente do setor? Uma ação de R$50 não pode aparecer como alvo R$16 numa lente e
R$40 em outra sem explicação.

**Resposta:** Ainda não. A correção arquitetural de v2.2 (suspensão `VERIFICAR` por
arquétipo) impede o app de *estampar* alvos absurdos de DDM como verdade — mas o audit
empírico em 22 ações (2/setor) revela 3 problemas que quebram a coerência, mapeados abaixo
para as fases do roadmap.

## Método

`report.analisar_acao` (lente DDM absoluta: `vmin/vmax` + veredito + arquétipo/motor) +
`comparables.preco_alvo_por_regressao` (lente regressão P/L~f(DP,ROE), relativa aos pares do
setor) rodados em 2 ações-foco por setor, com pares extras só para dar pontos à regressão.
Dados de fundamentos: DFP CVM cacheada (mesma fonte da produção). Preços: yfinance.

## Achado 1 — Over-routing a `ciclica` (FASE 1, gap aberto, generalizado)

O refino quantitativo joga a maioria do mercado em `ciclica` → `motor_pendente` → `VERIFICAR`.
**Só 4 de 22 ações produziram veredito real** (todas `pagadora_regulada`). Arquétipos
claramente errados encontrados (calibrar o classificador contra estes casos reais, não só WEGE3):

| Ação | Setor | Arquétipo obtido | Esperado | Nota |
|------|-------|------------------|----------|------|
| MDIA3 | Alimentos | **financeira** | crescimento/consumo | hard-route `financeira` casou token errado — é alimentos, não banco |
| WEGE3 | Bens de capital | ciclica (fronteiriço) | **crescimento** | compounder; gap já aberto (CV real 0.62–0.84 > corte 0.50) |
| RADL3 | Saúde/varejo farma | ciclica (fronteiriço) | **crescimento** | compounder de qualidade |
| ABEV3 | Bebidas | ciclica | crescimento/pagadora estável | consumo defensivo, não cíclico |
| VIVT3 | Telecom | ciclica | pagadora_regulada/estável | telecom regulada, pagadora |
| TIMS3 | Telecom | ciclica | pagadora_regulada/estável | idem |

Corretos (hard-routes funcionam): ITUB4/BBAS3 → financeira ✓; TAEE11/EGIE3/SBSP3/SAPR11 →
pagadora_regulada ✓; PETR4/PRIO3, VALE3/GGBR4, SUZB3/KLBN11, ROMI3 → ciclica ✓.

**Causa:** `_cv_lucro` (CV dos retornos ano-a-ano) mede variância da TAXA de crescimento,
penalizando compounders reais de crescimento desigual; `ciclica_cv_min=0.50` calibrado só
contra goldens sintéticos. Ver gap detalhado + lead (resíduos log-lineares, pstdev≈0.174 na
WEGE real) na `01-VERIFICATION.md`. **Recalibrar/validar contra ≥3 compounders reais**
(WEGE3, RADL3, e um terceiro) além dos cíclicos genuínos, para não calibrar num único ponto.
Investigar separadamente o hard-route `financeira` que capturou MDIA3.

## Achado 2 — DDM gera valores degenerados mesmo onde roda (FASE 3, guarda-corpos)

Mesmo na `pagadora_regulada` (que tem motor `ddm`), o DDM puro por dividendos produz faixas
incoerentes ou matematicamente inválidas:

| Ação | Preço | DDM vmin–vmax | mid/preço | Veredito | Problema |
|------|------:|--------------|----------:|----------|----------|
| SBSP3 | 31,11 | 6,16–9,75 | 0,26 | SOBREAVALIADA | Sabesp "valendo" R$6 — baixo payout/alto capex não cabe em DDM |
| EGIE3 | 33,58 | 18,42–29,84 | 0,72 | SOBREAVALIADA | subvalua sistematicamente |
| HAPV3 | 10,60 | −2,20 a −1,66 | −0,18 | (suspenso) | **faixa NEGATIVA** — inválida |
| PCAR3 | 2,73 | −7,67 a −5,95 | −2,49 | (suspenso) | **faixa NEGATIVA** |
| PRIO3 | 55,45 | 0,00–0,00 | — | (suspenso) | **faixa ZERO** — degenerada |
| PETR4 | 39,65 | 56,85–91,63 | 1,87 | (suspenso) | lucro cíclico no pico extrapolado → upside falso |

**Guarda-corpo necessário (Fase 3):** não emitir/exibir faixa quando `vmax ≤ 0` ou
degenerada; sinalizar quando o DDM é estruturalmente inaplicável (payout baixo, lucro no pico
do ciclo). Hoje esses números aparecem na seção DDM do relatório mesmo com o veredito suspenso.

## Achado 3 — Modo Ranking (regressão) sem freio de arquétipo (FASE 3)

O modo Ranking NÃO herda a suspensão por arquétipo — emite alvos crus, às vezes absurdos,
inclusive com R² nulo:

| Ação | Preço | Regressão alvo | R² (n) | Problema |
|------|------:|---------------:|-------:|----------|
| ROMI3 | 6,21 | **0,10** | 0,60 (4) | alvo R$0,10 (−98%) — degenerado |
| ITUB4 | 44,30 | 33,44 | **0,00** (4) | R²=0 → alvo é ruído |
| BBAS3 | 20,58 | 45,80 (+123%) | **0,00** (4) | R²=0 → alvo é ruído |

**Freio necessário (Fase 3):** suprimir/marcar alvo de regressão quando R²≈0 ou n insuficiente;
aplicar a mesma suspensão por arquétipo do modo Analisar.

## Achado 4 — Divergência entre lentes na MESMA ação (o sintoma que o usuário relatou)

| Ação | Preço | Lente DDM | Lente Regressão | Divergência |
|------|------:|-----------|-----------------|-------------|
| ITUB4 | 44,30 | ~R$15 | R$33 | ~2,2× |
| BBAS3 | 20,58 | R$19–30 | R$46 | ~1,8× |
| WEGE3 | 46,51 | R$9–14 | R$35 | ~3× |

As lentes medem coisas diferentes (intrínseco absoluto por dividendos vs. P/L justo relativo
a pares) — divergência pode ser legítima, mas o app precisa **reconciliar/explicar** (Fase 3:
ensemble + divergência), não apresentar as duas como "o preço-alvo".

## Encaminhamento

- **Fase 1 (corrigir agora, gap aberto):** recalibrar o classificador (sinal de ciclicidade +
  cortes + hard-route financeira) validando contra os casos reais deste audit.
- **Fase 2 (já roadmapeada):** motores por arquétipo — resolve a raiz dos 20/22 suspensos.
- **Fase 3 (já roadmapeada):** guarda-corpos DDM (Achado 2), freio do Ranking (Achado 3),
  reconciliação de divergência entre lentes (Achado 4). Capturados no backlog.
