---
phase: 01-classificador-de-arqu-tipo-roteamento
verified: 2026-07-11T17:36:12Z
status: gaps_found
score: 3/4 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  gaps_closed:
    - "UI Streamlit (app.py) exibe 'Arquétipo → motor' incondicionalmente, inclusive para o caso não-suspenso (pagadora_regulada/TAEE11) — confirmado app.py:882, fora de qualquer guard de a.motor_pendente."
  gaps_remaining:
    - "WEGE3 (ticker nomeado explicitamente na SC#1 e na SC#3 da Fase 2 como 'crescimento') ainda NÃO classifica como crescimento limpo quando alimentado com dados CVM REAIS (cd_cvm 5410) — o fix do 01-03 corrigiu o golden sintético (progressão geométrica perfeitamente suave, 1.18**i) mas não o defeito real: os retornos ano-a-ano de WEGE3 de verdade têm variância de TAXA de crescimento (de -3% a +52%/ano), produzindo CV detrended ≈0.62-0.84 (a depender da janela de anos) — acima do novo corte ciclica_cv_min=0.50. Resultado real: chave='ciclica', fronteirico=True, candidatos=['ciclica','crescimento'], confianca='baixa' (não mais 'ciclica'/alta como antes, mas também não 'crescimento' limpo)."
  regressions: []
gaps:
  - truth: "Rodar a engine (CLI/UI) em WEGE3 classifica e exibe o arquétipo 'crescimento' antes do bloco de valuation (SC#1, ticker nomeado explicitamente; reforçado pela SC#3 da Fase 2: 'WEGE3 (crescimento) usa DCF multi-estágio')"
    status: failed
    reason: >
      Reproduzido de forma independente com dados REAIS da CVM (cache local, cd_cvm 5410,
      WEGE3, três janelas de anos testadas: 2015-2023, 2016-2023, 2015-2024 — todas
      convergem), chamando diretamente `arquetipo.classificar()` do código atual (pós
      01-03/01-04): `chave='ciclica'`, `fronteirico=True`, `candidatos=['ciclica',
      'crescimento']`, `confianca='baixa'`. Isso é uma MELHORA sobre o estado anterior
      (antes: 'ciclica'/confianca='alta', sem nem cair no fallback honesto) mas NÃO é o
      'crescimento' que a Success Criteria nomeia explicitamente para WEGE3, nem o que a
      Fase 2 SC#3 pressupõe ('WEGE3 (crescimento) usa DCF'). Como `motor =
      ARQUETIPO_MOTOR.get('ciclica') = None`, o veredito de WEGE3 continua suspenso
      (motor_pendente=True, mesma suspensão D-04 de antes), só que agora citando
      "arquétipo ciclica" em vez de silenciar o problema.

      Causa raiz: o golden `test_compounder_realista_wege_vira_crescimento` (01-03) usa uma
      progressão geométrica PERFEITAMENTE suave (`lucros = [round(1000 * (1.18 ** i)) for i
      in range(10)]`), que produz retornos ano-a-ano praticamente constantes (CV≈0.0013) —
      um cenário idealizado que NÃO existe em nenhuma empresa real. Os números reais de
      WEGE3 (extraídos do DFP CVM cacheado, mesma fonte que a produção usa):
      LL 2015→2023 = [1.166B, 1.128B, 1.141B, 1.344B, 1.632B, 2.396B, 3.657B, 4.273B,
      5.868B] — crescimento real, mas NÃO suave: retornos ano-a-ano variam de -3,3% a
      +52,6%. O CV desses retornos reais (≈0.62-0.84, dependendo da janela) fica ACIMA do
      novo corte `ciclica_cv_min=0.50`, disparando o candidato `ciclica` de novo — e como o
      candidato `crescimento` também dispara (ROE real≈0.258 ≥ 0.15, retenção real≈0.554 ≥
      0.50), o resultado cai em conflito (`fronteirico=True`), com `chave=distintos[0]`
      favorecendo `ciclica` por ordem de append no código — o MESMO desempate que o plano
      01-03 reconheceu explicitamente como fora de escopo ("o fix é no sinal, não no
      desempate distintos[0]"), mas que volta a importar porque o sinal, na prática real,
      não ficou consertado o suficiente. Este é o mesmo padrão de defeito da verificação
      anterior: um golden sintético idealizado mascara um defeito que só aparece com dados
      de produção reais.
    artifacts:
      - path: "src/analista/core/arquetipo.py"
        issue: "_cv_lucro (retornos ano-a-ano) mede variância da TAXA de crescimento, não apenas oscilação de sinal/reversão — penaliza compounders reais com crescimento desigual (alguns anos 50%+, outros quase 0%) da mesma forma que penalizaria uma cíclica genuína. ciclica_cv_min=0.50 (config.yaml) foi calibrado só contra o golden sintético suave e os goldens de cíclica/fronteiriço sintéticos, não contra a série real de WEGE3."
      - path: "config.yaml"
        issue: "ciclica_cv_min: 0.50 — não recalibrado contra dados reais de WEGE3 (CV real ≈0.62-0.84); o comentário inline cita só os regimes sintéticos ('compounder monotônico ~0.00-0.01; cíclico que alterna sinal >1.3')."
    missing:
      - "Recalibrar/validar o sinal e/ou o corte contra a série REAL de WEGE3 (cd_cvm 5410, dados já cacheados offline em data/cvm/), não só contra o golden sintético. Evidência levantada nesta verificação: o corte precisaria subir para algo entre ~0.85 e ~1.35 para acomodar o CV real de WEGE3 (0.62-0.84) sem quebrar os goldens sintéticos de cíclica (1.386) e fronteiriço (1.669) — MAS isso é só um ajuste de threshold; testar contra 2-3 outros compounders reais (ex.: LREN3, EGIE3 não-regulada, ou outro nome do universo B3) antes de fixar o número, para não recalibrar em cima de um único ponto."
      - "Alternativa mais robusta ao CV-de-retornos (sugerida no code review original, CR-01, e nunca testada): dispersão dos RESÍDUOS de um ajuste log-linear sobre a série de lucro. Reproduzido nesta verificação com os mesmos dados reais de WEGE3: pstdev dos resíduos do ajuste log-linear ≈0.174 — uma escala muito mais discriminante (não conflita com os thresholds já usados em roe_alto_min/retencao_alta_min, ~0.15-0.50) e que não penaliza variância de TAXA de crescimento, só desvio da tendência — provável candidato a resolver o problema sem re-varrer o threshold às cegas."
      - "Golden de compounder realista deveria replicar os RETORNOS ANO-A-ANO reais de uma empresa (não uma progressão geométrica perfeita) — ex.: usar os próprios números de WEGE3 levantados nesta verificação como fixture, em vez de 1.18**i — para não mascarar o mesmo tipo de defeito outra vez."
---

# Phase 1: Classificador de Arquétipo + Roteamento Verification Report

**Phase Goal:** Erguer a etapa de classificação/roteamento de arquétipo. A ferramenta decide o
arquétipo (financeira, pagadora regulada, compounder/crescimento, cíclica, holding) ANTES de
valuar, com fallback honesto em casos-fronteira, e um registry arquétipo→motor (DDM plugado
como primário da pagadora regulada), sem tocar nos motores.

**Verified:** 2026-07-11T17:36:12Z
**Status:** gaps_found
**Re-verification:** Yes — after gap closure (plans 01-03, 01-04)

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Rodar a engine (CLI/UI) em ITUB4, TAEE11, VALE3 e WEGE3 classifica e exibe o arquétipo antes do bloco de valuation | ✗ FAILED (persiste, forma diferente) | ITUB4→financeira ✓, TAEE11→pagadora_regulada ✓, VALE3→ciclica ✓ (confirmados de novo com dados CVM reais offline pós-fix). **WEGE3 com dados reais → chave='ciclica', fronteirico=True, confianca='baixa'** — melhor que antes (não mais confiança 'alta' falsa), mas ainda NÃO 'crescimento' como a própria SC#1 nomeia e como a SC#3 da Fase 2 pressupõe. O golden `test_compounder_realista_wege_vira_crescimento` (01-03) passa porque usa uma fixture sintética perfeitamente suave que não reflete a variância de taxa de crescimento real de WEGE3. Ver evidência completa abaixo. |
| 2 | Escolha do motor vem do registry arquétipo→motor; motor ausente cai em fallback explícito, não crash | ✓ VERIFIED | Inalterado desde a verificação anterior. `ARQUETIPO_MOTOR` (arquetipo.py:36-42), `report.py:151-153`. Confirmado de novo: ITUB4/TAEE11/VALE3 resolvem motor sem exceção; WEGE3 (agora fronteiriço) cai em `motor_pendente=True` com mensagem explícita, sem crash. |
| 3 | TAEE11 (pagadora regulada) roteada para DDM primário, números/veredito idênticos — test_ddm, test_selo, test_consistencia_modos verdes | ✓ VERIFIED | Reconfirmado com dados CVM reais de TAEE11 (cd_cvm 20257, eh_concessionaria=True): `classificar()` retorna `pagadora_regulada`, motor='ddm'. `python -m pytest -q` → 355 passed (0 failed), incluindo test_ddm/test_selo/test_consistencia_modos. `git log` confirma `src/analista/core/ddm.py` e `src/analista/report/selo.py` intocados pelos commits desta fase (incl. 01-03/01-04). |
| 4 | Ticker de baixa confiança marcado como fronteiriço com 2-3 candidatos | ✓ VERIFIED | Mecanismo funciona (e, ironicamente, capturou WEGE3 nesta rodada): `test_conflito_de_sinais_marca_fronteirico` verde; reprodução real com WEGE3 mostra `fronteirico=True`, `candidatos=['ciclica','crescimento']`, `confianca='baixa'` — o MECANISMO de fallback honesto (ARQ-02) está correto. O problema não é o mecanismo, é o sinal de entrada que decide quando disparar o conflito. |

**Score:** 3/4 truths verified. Gap 1 (SC#1) permanece FAILED, agora por uma causa mais estreita
e melhor evidenciada do que a rodada anterior. Gap 2 (exposição na UI) foi FECHADO.

### Evidência: reprodução com dados reais (independente do SUMMARY)

Reprodução offline, chamando diretamente `arquetipo.classificar()` do código atual contra dados
CVM cacheados localmente (`data/cvm/dfp_cia_aberta_*.zip`, sem rede), via
`src.analista.ingest.cvm.fundamentos_do_ano`:

```
WEGE3 (cd_cvm 5410), janela 2015-2023:
  lucro_liquido = [1165810000, 1127832000, 1140942000, 1344148000, 1632455000,
                   2395957000, 3657480000, 4272872000, 5867615000]
  roe_valuation()    = 0.2582   (real WEGE3 ≈0.258 — bate com o número citado no 01-03)
  payout_valuation() = 0.4460   (retenção ≈0.554, dispara candidato crescimento)
  cv_lucro (NOVO, detrended) = 0.7955   (>= ciclica_cv_min=0.50 → dispara candidato ciclica)
  → ResultadoArquetipo(chave='ciclica', fronteirico=True,
                        candidatos=['ciclica', 'crescimento'], confianca='baixa')

Janela 2016-2023: cv=0.6157 → mesmo resultado (ciclica/fronteiriço/baixa)
Janela 2015-2024: cv=0.8431 → mesmo resultado (ciclica/fronteiriço/baixa)

Controle — ITUB4 (cd_cvm 19348): chave='financeira' (hard-route, inalterado) ✓
Controle — TAEE11 (cd_cvm 20257, eh_concessionaria=True): chave='pagadora_regulada', motor='ddm' ✓
Controle — VALE3 (cd_cvm 4170): cv_lucro=1.900 → chave='ciclica', fronteirico=False, confianca='alta' ✓
           (cíclica genuína de commodity, corretamente NÃO afetada pelo fix)

Métrica alternativa testada (resíduos de ajuste log-linear sobre a mesma série real de WEGE3,
sugerida no code review original CR-01 mas não adotada pelo 01-03): pstdev(resíduos) ≈ 0.174 —
separa WEGE3 de cíclicas genuínas numa escala mais discriminante, sem penalizar variância de
TAXA de crescimento (só desvio de tendência).
```

Suíte completa: `python -m pytest -q` → **355 passed, 0 failed** (confirmado nesta verificação,
não apenas citado do SUMMARY).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/arquetipo.py::_cv_lucro` | CV detrended (retornos ano-a-ano), não nível bruto | ✓ VERIFIED (existe, substantivo, ligado) — ⚠️ mas sinal ainda produtor de resultado incorreto p/ WEGE3 real | Reescrito conforme 01-03 (linhas 58-81): `pstdev(retornos)/abs(mean(retornos))`, guards preservados. Puro, sem I/O. Corretamente invariante a tendências suaves, mas SENSÍVEL a variância de taxa de crescimento em séries reais — WEGE3 real dispara o candidato ciclica de novo. |
| `config.yaml` bloco `arquetipo.ciclica_cv_min` | recalibrado para a escala da nova métrica | ✓ VERIFIED (existe) — ⚠️ mas não validado contra dados reais | `0.50` (linhas 195), comentário inline correto para a escala nova; calibrado só contra os goldens sintéticos, não contra WEGE3 real (CV real 0.62-0.84, acima do corte). |
| `tests/test_arquetipo.py::test_compounder_realista_wege_vira_crescimento` | golden trava crescimento p/ compounder realista | ✓ VERIFIED (passa) — ⚠️ mas fixture não é representativa de dados reais | `lucros = [round(1000 * (1.18 ** i)) for i in range(10)]` é uma progressão geométrica PERFEITAMENTE suave (CV≈0.0013) — não replica a variância real de taxa de crescimento de WEGE3 (CV real 0.62-0.84). O golden passa, mas não protege contra o defeito que ainda existe nos dados reais. |
| `app.py` (Streamlit UI) | exibe `a.arquetipo`/`a.motor` incondicional, junto ao caption Setor/Estágio | ✓ VERIFIED (wired, incondicional) | `app.py:882`: `st.caption(f"Arquétipo: {esc_md(a.arquetipo or '—')} → motor {esc_md(a.motor or '—')}")` — dentro do ramo `else:` de dados OK, ANTES do bloco de veredito (:884+), SEM guard por `a.motor_pendente`. Confirmado visualmente lendo o arquivo (não só grep): a linha está sempre no fluxo, cobrindo o caso não-suspenso (pagadora_regulada). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `arquetipo.py::classificar` | `CompanyData.roe_valuation/payout_valuation/serie/eh_concessionaria/setor` | consumo de sinais canônicos | ✓ WIRED | Inalterado; reconfirmado. |
| `arquetipo.py::classificar` | `config.yaml arquetipo:` | `cfg.get("arquetipo", {})` | ✓ WIRED | `ciclica_cv_min` lido corretamente (0.50). |
| `report.py::analisar_acao` | `arquetipo.classificar + ARQUETIPO_MOTOR` | import + lookup após CAPM | ✓ WIRED | Inalterado. |
| `app.py` (render) | `a.arquetipo` / `a.motor` | `st.caption` incondicional linha 882 | ✓ WIRED (NOVO — fecha Gap 2) | Confirmado: `grep -c "a.arquetipo" app.py` = 1, dentro do fluxo principal, antes do veredito, sem guard de `motor_pendente`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `arquetipo.py::classificar` | `cv = _cv_lucro(c.serie("lucro_liquido"))` | Série real de lucro CVM (WEGE3, cd_cvm 5410, offline) | Sim, dado real flui — mas o SINAL continua estruturalmente incompatível com a variância de taxa de crescimento de compounders reais | ⚠️ FLOWING BUT STILL INCORRECT PARA WEGE3 — defeito residual do CR-01, agora restrito a compounders com crescimento desigual (não perfeitamente suave). |
| `app.py` render → `a.arquetipo`/`a.motor` | `st.caption` linha 882 | `AnaliseAcao` populado por `report.analisar_acao` | Sim | ✓ FLOWING (novo, confirma fechamento do Gap 2) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| ITUB4 (dados CVM reais) classifica financeira | script offline, cd_cvm 19348 | `chave='financeira'` | ✓ PASS |
| TAEE11 (dados CVM reais) classifica pagadora_regulada, motor ddm | script offline, cd_cvm 20257 | `chave='pagadora_regulada'`, `motor='ddm'` | ✓ PASS |
| VALE3 (dados CVM reais) classifica cíclica | script offline, cd_cvm 4170 | `chave='ciclica'`, cv=1.90 | ✓ PASS |
| WEGE3 (dados CVM reais) classifica crescimento | script offline, cd_cvm 5410, 3 janelas de anos | `chave='ciclica'`, `fronteirico=True`, `confianca='baixa'` — esperado `crescimento` limpo | ✗ FAIL |
| Golden sintético `test_compounder_realista_wege_vira_crescimento` | `pytest tests/test_arquetipo.py::test_compounder_realista_wege_vira_crescimento` | passa | ✓ PASS (mas não é evidência suficiente — ver gap) |
| Suíte completa | `python -m pytest -q` | `355 passed, 0 failed` | ✓ PASS |
| `app.py` referencia `a.arquetipo`/`a.motor` incondicionalmente | `grep -n "a.arquetipo" app.py` + leitura do fluxo | linha 882, fora de qualquer guard `motor_pendente` | ✓ PASS |
| `ddm.py`/`selo.py` intocados por 01-03/01-04 | `git log --oneline -- src/analista/core/ddm.py src/analista/report/selo.py` | últimos commits predatam a fase 1 | ✓ PASS |
| Nenhum marcador TODO/FIXME/TBD/XXX novo | `grep -n -E "TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER"` em arquetipo.py, app.py, config.yaml | sem matches | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|--------------|--------|----------|
| ARQ-01 | 01-01, 01-02, 01-03 | Classifica o arquétipo antes de valuar (setor CVM + refino quantitativo por ROE/retenção/oscilação) | ⚠️ PARTIAL (inalterado) | Hard-route por setor (financeira/regulada) correto e soberano. O refino quantitativo melhorou (WEGE3 não é mais confiantemente errado) mas continua não classificando WEGE3 como crescimento com dados reais — o requisito ("ROE alto e estável... → compounder; margem/lucro oscilando violento... → cíclica") ainda não está integralmente satisfeito para o caso nomeado explicitamente no roadmap. |
| ARQ-02 | 01-01, 01-02 | Fallback honesto: fronteiriço + 2-3 lentes candidatas em conflito real | ✓ SATISFIED | Mecanismo funciona corretamente, inclusive capturando o caso WEGE3 como conflito honesto em vez de silenciar — comportamento correto do MECANISMO em si. |
| ENG-01 | 01-01, 01-02 | Registry arquétipo→motor consumido na agregação do veredito | ✓ SATISFIED | Inalterado; reconfirmado. |
| ENG-06 | 01-02 | DDM permanece motor primário para pagadora madura/regulada, sem quebrar o que já funciona | ✓ SATISFIED | Reconfirmado com TAEE11 real; ddm.py/selo.py intocados pelos commits 01-03/01-04. |

**Orphaned requirements check:** Inalterado — REQUIREMENTS.md mapeia exatamente ARQ-01, ARQ-02,
ENG-01, ENG-06 à Fase 1; nenhum requisito órfão.

**Nota:** REQUIREMENTS.md continua marcando ARQ-01 como `[x]` completo. Dado o achado acima
(WEGE3 real ainda não classifica crescimento), esse checkbox continua prematuro — ARQ-01 NÃO
deveria ser fechado nesta rodada.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/analista/core/arquetipo.py` | 58-81 | CR-01 residual: `_cv_lucro` (CV dos retornos ano-a-ano) penaliza variância de TAXA de crescimento, não só reversão/oscilação de sinal — compounders reais com crescimento desigual (WEGE3 real) continuam disparando o candidato `ciclica` | 🛑 Blocker | WEGE3 (nomeado explicitamente na SC#1 e pressuposto pela SC#3 da Fase 2) não classifica como `crescimento` limpo com dados reais — cai em fronteiriço/ciclica-primary |
| `tests/test_arquetipo.py` | 112-124 | Golden `test_compounder_realista_wege_vira_crescimento` usa fixture sintética idealizada (progressão geométrica perfeitamente suave) que não reflete a variância real de taxa de crescimento de nenhuma empresa real — mascara o defeito residual acima | ⚠️ Warning | Suíte 100% verde não é evidência de que o defeito nomeado no roadmap (WEGE3 real) está corrigido — mesmo padrão da rodada de verificação anterior, agora numa fixture diferente |
| `config.yaml` | 195 | `ciclica_cv_min: 0.50` calibrado só contra goldens sintéticos, não contra a série real de WEGE3 (CV real 0.62-0.84) | ⚠️ Warning | Threshold plausível na superfície, mas não validado contra o caso nomeado no roadmap |

Anti-patterns carregados da verificação anterior (WR-01 a WR-04, não relacionados aos gaps desta
rodada) permanecem sem mudança — não re-auditados aqui pois não fazem parte do escopo dos planos
01-03/01-04.

Nenhum marcador TBD/FIXME/XXX novo encontrado nos arquivos desta fase (gate de marcador: limpo).

### Human Verification Required

None. Os achados desta rodada são verificáveis programaticamente contra dados CVM reais
cacheados offline (sem rede) — nenhum comportamento visual/UX/tempo-real precisou de
confirmação manual.

### Gaps Summary

O plano 01-04 fechou completamente o Gap 2: a UI Streamlit agora exibe "Arquétipo → motor"
incondicionalmente, inclusive para o caso não-suspenso (pagadora regulada/TAEE11), em paridade
com o CLI. Esta parte está sólida e confirmada por leitura direta do código (não só grep).

O plano 01-03 melhorou genuinamente o comportamento de WEGE3 — de "confiantemente errado"
(ciclica/alta, sem cair no fallback honesto) para "honestamente incerto" (ciclica/fronteiriço/
baixa, com ambos os candidatos expostos). Isso é um progresso real e mensurável em direção ao
ARQ-02. Porém, reproduzindo com os MESMOS dados reais de WEGE3 que a verificação anterior usou
(cd_cvm 5410, cache CVM local, três janelas de anos testadas), o resultado ainda NÃO é o
`crescimento` limpo que a Success Criteria #1 nomeia explicitamente para este ticker, nem o que
a Success Criteria #3 da Fase 2 pressupõe ("WEGE3 (crescimento) usa DCF multi-estágio"). A causa
raiz mudou de forma: antes era o CV do nível bruto do lucro (dominado pela tendência); agora é o
CV dos retornos ano-a-ano (dominado pela VARIÂNCIA da taxa de crescimento, que também é alta em
compounders reais com crescimento desigual ano a ano, não só em cíclicas). O golden que deveria
travar essa regressão usa uma fixture sintética idealizada (progressão geométrica perfeitamente
suave) que não existe em nenhuma empresa real e por isso não captura o defeito residual — o
mesmo padrão da rodada de verificação anterior, aplicado a uma fixture diferente.

Uma métrica alternativa (resíduos de ajuste log-linear, já sugerida no code review original
CR-01 mas não adotada) foi testada nesta verificação contra os mesmos dados reais de WEGE3 e
produziu uma separação mais limpa (pstdev≈0.174, numa escala compatível com os outros thresholds
do bloco `arquetipo:`), sugerindo um caminho de correção mais promissor do que apenas recalibrar
o corte do CV de retornos.

O gap estruturado acima é acionável para `/gsd-plan-phase --gaps`: a correção deveria validar o
sinal (e/ou trocar de métrica) contra pelo menos 2-3 séries reais de compounders da B3 — não só
contra uma fixture sintética — antes de fechar o Gap 1 definitivamente.

---

_Verified: 2026-07-11T17:36:12Z_
_Verifier: Claude (gsd-verifier)_
