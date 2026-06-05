---
phase: 02-apresenta-o-e-travas-de-consist-ncia
plan: 02
subsystem: tests
tags: [pytest, consistencia, cross-modo, regressao, ddm, payout, golden]

# Dependency graph
requires:
  - phase: 01-engine-de-consistencia
    provides: "Funções canônicas únicas (c.roe, c.payout, c.payout_valuation, report.analisar_acao, comparables.preco_alvo_por_regressao) consumidas igualmente pelos 3 modos"
  - phase: 02-apresenta-o-e-travas-de-consist-ncia
    plan: 01
    provides: "UI já lê os campos canônicos; este plano trava por pytest a consistência que a UI promete"
provides:
  - "Trava automatizada cross-modo (TEST-01): mesma CompanyData (à mão, sem rede) produz ROE/payout/veredito coerentes entre Analisar e Ranking"
  - "Asserção obrigatória e não-skipável da DIREÇÃO do veredito (DDM vs regressão) com ≥4 fixtures determinísticas"
  - "Confirmação explícita de que a suíte golden continua verde (TEST-02): 44 golden + 3 novos = 47 passed"
affects: [regressao-de-consistencia-futura, ci]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Teste de consistência cross-modo: montar CompanyData à mão e exercer as MESMAS funções que cada modo do app usa (sem rede, sem montar())"
    - "Carregar config.yaml no teste espelhando cli.py (yaml.safe_load), nunca o loader do app.py (@st.cache_data)"
    - "Para travar direção barato/caro do veredito, calibrar fixtures até o sinal estabilizar; afirmar SINAL, não igualdade numérica (DDM ≠ regressão)"

key-files:
  created:
    - tests/test_consistencia_modos.py
  modified: []

key-decisions:
  - "Empresa-alvo calibrada com preço (R$ 6,00) abaixo TANTO do intrínseco do DDM (~8,20 com LPA 1,0) QUANTO do preço-alvo da regressão, garantindo SUBAVALIADA pelos dois métodos de forma determinística"
  - "Comparáveis (BBB3/CCC3/DDD3) com P/L corrente alto puxam o P/L 'justo' da regressão para cima, fazendo o preço-alvo da alvo barata ficar acima do seu preço corrente"
  - "Asserção de payout distingue explicitamente o último ano cru (multiplos['DP (payout)'] == c.payout(ult)) do payout_valuation (média 3a + clamp), os dois números do PAYOUT-02"
  - "Nenhum golden editado: a única mudança é o arquivo de teste novo (TEST-02 confirma 47 passed)"

patterns-established:
  - "Rede de segurança contra regressão dos bugs CR-02/CR-03/WR-03: qualquer divergência futura entre modos quebra a suíte"

requirements-completed: [TEST-01, TEST-02]

metrics:
  duration_min: 12
  completed: "2026-06-05"
  tasks: 2
  files: 1
---

# Phase 2 Plan 2: Travas de Consistência Cross-Modo Summary

Trava por pytest a consistência cross-modo prometida pela Fase 1 (TEST-01) e confirma a
suíte golden verde (TEST-02), usando fixtures `CompanyData` montadas à mão sem rede.

## What Was Built

`tests/test_consistencia_modos.py` (novo, 173 linhas) com 3 funções de teste:

1. **`test_roe_coerente_analisar_vs_ranking`** — afirma igualdade exata
   `report.analisar_acao(c, cfg).multiplos["ROE"] == c.roe(ult)` (ambos `c.roe(ult)`: o
   caminho Analisar e o caminho Ranking consomem a mesma função canônica).

2. **`test_payout_coerente_ultimo_ano_vs_valuation`** — distingue os dois números do
   PAYOUT-02: `multiplos["DP (payout)"] == c.payout(ult)` (último ano cru, report.py:56)
   vs `c.payout_valuation()` (média 3a + clamp, canônico do DDM/Ranking).

3. **`test_veredito_direcao_coerente`** — monta 4 `CompanyData` determinísticas (AAA3/BBB3/
   CCC3/DDD3) para a regressão `ajustar_regressao_pl` ajustar (n=4, não-None). Afirma a
   DIREÇÃO do veredito: `a.veredito.startswith("SUBAVALIADA") == pa.subavaliada`, ancorada
   num sinal SUBAVALIADA determinístico. Obrigatória e não-skipável.

O loader de config espelha `cli.py` (`yaml.safe_load` de `config.yaml` na raiz; sem
`@st.cache_data` do streamlit).

## Calibração da fixture de direção (não-trivial)

O risco do plano era estabilizar o sinal entre dois métodos diferentes (DDM vs regressão).
Calibração final:
- **Alvo (AAA3):** lucro 1000 / 1000 ações → LPA 1,0; ROE 25%; payout_valuation 0,5; preço
  **R$ 6,00**. O DDM produz intrínseco ~R$ 8,20 → preço abaixo → `SUBAVALIADA`.
- **Comparáveis (BBB3/CCC3/DDD3):** mesmos ROE/payout, mas preços altos (R$ 40–45) → P/L
  corrente alto. A regressão eleva o P/L "justo"; o preço-alvo da AAA3 sai ~R$ 25 (>6) →
  `subavaliada=True`. Os dois métodos concordam na DIREÇÃO.

Tentativa inicial (preço R$ 10) falhou: regressão dizia SUBAVALIADA mas DDM dizia
SOBREAVALIADA (10 > 8,20). Recalibrado o preço da alvo para R$ 6,00 — fixture, não
asserção — até o sinal estabilizar.

## Verification Results

- `.venv/bin/pytest tests/test_consistencia_modos.py -q` → **3 passed** (exit 0)
- `.venv/bin/pytest tests/ -q` → **47 passed** (44 golden + 3 novos), zero failed (TEST-02)
- `grep -c "montar(" tests/test_consistencia_modos.py` → **0** (sem rede)
- Contém `yaml.safe_load` + `config.yaml`; NÃO contém `import streamlit` nem `@st.cache_data`
- Sem `pytest.skip` / `pytest.mark.skip` no arquivo
- Nenhum golden editado (`git status` mostra apenas o arquivo novo)

## Deviations from Plan

None - plano executado exatamente como escrito. A recalibração do preço da fixture
(R$ 10 → R$ 6) é a estabilização do sinal prevista no próprio plano (nunca relaxar a
asserção; recalibrar números das fixtures), não um desvio.

## Self-Check: PASSED
