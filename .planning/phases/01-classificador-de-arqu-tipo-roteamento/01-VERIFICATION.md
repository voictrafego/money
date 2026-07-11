---
phase: 01-classificador-de-arqu-tipo-roteamento
verified: 2026-07-11T21:15:54Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  gaps_closed:
    - "WEGE3 (ticker nomeado explicitamente na SC#1) agora classifica 'crescimento' (fronteirico=False) com dados CVM REAIS — confirmado tanto via reprodução offline (cache CVM local, 3 janelas de anos) quanto via execução end-to-end do CLI real (`python -m analista analyze WEGE3`, rede + Yahoo, sem mock): `*Arquétipo:* crescimento → motor pendente_fase_2`. Causa raiz (sinal `_cv_lucro` medindo variância de TAXA de crescimento em vez de desvio de TENDÊNCIA) corrigida pelo plano 01-05: substituição por dispersão de resíduos de ajuste log-linear + recalibração de `ciclica_cv_min` (0.50 → 0.35) validada contra >=3 compounders reais (WEGE3, RADL3, ABEV3/LREN3) e >=4 cíclicas reais (VALE3, GGBR4, SUZB3, PETR4) — não mais um único ponto de calibração."
    - "RADL3 (compounder citado no audit de coerência, Achado 1a) também corrigido: chave='crescimento', fronteirico=False, confirmado em reprodução real (offline e via rede)."
    - "MDIA3 (Achado 1b do audit de coerência: hard-route financeiro capturava fragmento 'rci' de 'Banco RCI Brasil' dentro de 'comeRCIo') corrigido pelo plano 01-06: override determinístico no ticker_map (MDIA3 → cd_cvm 20338, setor Alimentos) + defesa em profundidade por casamento de token com limite de palavra (\\b) no hard-route financeiro. Confirmado: MDIA3 != financeira; ITUB4/BBAS3 seguem financeira."
  gaps_remaining: []
  regressions: []
---

# Phase 1: Classificador de Arquétipo + Roteamento Verification Report

**Phase Goal:** Classificador/roteamento de arquétipo coerente e utilizável cross-setor — decide
o arquétipo ANTES de valuar, fallback honesto em fronteira, registry arquétipo→motor (DDM
primário da pagadora regulada), sem tocar nos motores.

**Verified:** 2026-07-11T21:15:54Z
**Status:** passed
**Re-verification:** Yes — after coherence gap-closure round (plans 01-05, 01-06, 01-07, 01-08),
following two prior verification rounds that returned `gaps_found`.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Rodar a engine em ITUB4, TAEE11, VALE3 e WEGE3 classifica e exibe o arquétipo ANTES do valuation | ✓ VERIFIED (gap fechado) | Executado o CLI real (`python -m analista analyze <ticker>`, dados reais via CVM+Yahoo, sem mock) para os 4 tickers nomeados na SC. Linha de cabeçalho do relatório, ANTES de qualquer tabela de valuation: `ITUB4 → *Arquétipo:* financeira → motor pendente_fase_2`; `TAEE11 → *Arquétipo:* pagadora_regulada → motor ddm`; `VALE3 → *Arquétipo:* ciclica → motor pendente_fase_2`; **`WEGE3 → *Arquétipo:* crescimento → motor pendente_fase_2`** (ticket previamente FAILED nas duas rodadas anteriores). Reprodução independente também confirmada offline contra cache CVM local (`arquetipo.classificar()` chamado diretamente, sem rede): WEGE3 roe=0.258/retencao=0.554/cv=0.174 → `crescimento`, `fronteirico=False` — números idênticos aos citados na verificação anterior (que então cravava FAILED pela métrica antiga). |
| 2 | Motor vem do registry; motor ausente → fallback explícito, não crash | ✓ VERIFIED | Inalterado desde as rodadas anteriores. `ARQUETIPO_MOTOR` (arquetipo.py:45-51). ITUB4/VALE3 (motor=None) exibem `motor pendente_fase_2` sem crash; TAEE11 resolve `motor ddm` sem exceção. Confirmado por execução real do CLI (não só teste). |
| 3 | TAEE11 → DDM primário, números idênticos; test_ddm/test_selo/test_consistencia_modos verdes | ✓ VERIFIED | `classificar()` real (via rede) para TAEE11 (`eh_concessionaria=True`) → `pagadora_regulada`, motor=`ddm`. Suíte alvo executada isoladamente: `pytest tests/test_ddm.py tests/test_selo.py tests/test_consistencia_modos.py` → 21 passed. `git diff --stat` (do commit anterior a 01-05 até HEAD) para `src/analista/core/ddm.py` e `src/analista/report/selo.py` → **vazio, nenhum commit os tocou** — firewall preservado por toda a rodada de gap-closure (01-05 a 01-08). |
| 4 | Ticker de baixa confiança → fronteiriço com 2-3 candidatos | ✓ VERIFIED | Mecanismo ARQ-02 preservado e ainda exercitado: `test_conflito_de_sinais_marca_fronteirico` verde; adicionalmente, com dados reais via rede, GGBR4/SUZB3 (retenção alta em anos de boom de commodity + prejuízo em outros anos) capturam corretamente `fronteirico=True`, `candidatos=['ciclica','crescimento']` — o mecanismo de fallback honesto dispara em conflito real de sinais, sem quebrar a chave primária (`ciclica`) exigida. |

**Score:** 4/4 truths verified. O gap 1 (SC#1/WEGE3), que persistiu por duas rodadas de
verificação anteriores, está fechado — confirmado tanto por reprodução offline (cache CVM) quanto
por execução end-to-end real do CLI (rede + Yahoo), a evidência mais forte disponível.

### Evidência: reprodução independente (não apenas citação do SUMMARY)

**1) Execução real end-to-end do CLI (rede, sem mock) — os 4 tickers nomeados na SC#1:**

```
$ python -m analista analyze ITUB4
*Arquétipo:* financeira → motor pendente_fase_2

$ python -m analista analyze TAEE11
*Arquétipo:* pagadora_regulada → motor ddm

$ python -m analista analyze VALE3
*Arquétipo:* ciclica → motor pendente_fase_2

$ python -m analista analyze WEGE3
*Arquétipo:* crescimento → motor pendente_fase_2      <-- gap fechado (era 'ciclica'/fronteirico nas duas rodadas anteriores)
```

**2) Reprodução direta de `arquetipo.classificar()` com dados reais via `build.montar_empresa`
(rede + fallback Yahoo de nº de ações, o mesmo caminho que a produção usa):**

```
WEGE3    -> crescimento        motor=None   fronteirico=False cand=['crescimento'] roe=0.2582 retencao=0.5540 cv=0.1744
RADL3    -> crescimento        motor=None   fronteirico=False cand=['crescimento'] roe=0.1776 retencao=0.6591 cv=0.1561
VALE3    -> ciclica            motor=None   fronteirico=False cand=['ciclica']     roe=0.4900 retencao=0.4936 cv=10.0 (prejuízo)
GGBR4    -> ciclica            motor=None   fronteirico=True  cand=['ciclica','crescimento'] roe=0.2403 retencao=0.6504 cv=10.0
SUZB3    -> ciclica            motor=None   fronteirico=True  cand=['ciclica','crescimento'] roe=0.3618 retencao=0.8227 cv=10.0
PETR4    -> ciclica            motor=None   fronteirico=False cand=['ciclica']     roe=0.3352 retencao=0.3273 cv=10.0
MDIA3    -> pagadora_regulada  motor=ddm    fronteirico=False cand=['pagadora_regulada'] (!= financeira, achado 1b fechado)
ITUB4    -> financeira         motor=None   fronteirico=False
TAEE11   -> pagadora_regulada  motor=ddm    fronteirico=False
```

Nota: GGBR4/SUZB3 saem `fronteirico=True` com dados de payout REAIS via rede (diferente do payout
hardcoded 0.80 dos goldens sintéticos-de-série-real em `tests/test_arquetipo.py`, que fixam
apenas `chave == CICLICA`, sem asserir `fronteirico`) — a chave primária permanece `ciclica`
(exigida pela SC), e o disparo de `fronteirico` é o próprio mecanismo ARQ-02 funcionando
honestamente diante de sinais reais conflitantes (ROE/retenção alto em anos de boom de commodity
+ prejuízo em outros anos da mesma série). Não é regressão: nenhum golden assume
`fronteirico=False` para esses dois tickers.

**3) Guarda-corpo DDM (Achado 2), execução real via rede:**

```
HAPV3    vmin=None vmax=None ddm_inaplicavel=True   (faixa negativa suprimida)
PCAR3    vmin=None vmax=None ddm_inaplicavel=True   (faixa negativa suprimida)
TAEE11   vmin=26.66 vmax=42.29 ddm_inaplicavel=False (faixa válida preservada)
```
(PRIO3 não reproduziu o 0-0 exato do audit com preços/dividendos atuais — dado de mercado mudou
desde a data do audit; o guarda-corpo em si está travado por golden frozen determinístico em
`tests/test_guardrails_ddm.py::test_faixa_degenerada_zero_prio3_suprimida`, verde.)

**4) Freio do Ranking + sinalização de divergência (Achados 3 e 4), execução real via rede:**

```
$ python -m analista rank --tickers ROMI3,ITUB4,BBAS3,WEGE3,TAEE11,VALE3
⚠ BBAS3: lentes divergem ~2.2× (DDM R$ 24.13 × regressão R$ 52.04) — ver Analisar; reconciliação na Fase 3.
⚠ ROMI3: lentes divergem ~8.2× (DDM R$ 5.62 × regressão R$ 0.68) — ver Analisar; reconciliação na Fase 3.
⚠ WEGE3: lentes divergem ~3.5× (DDM R$ 11.54 × regressão R$ 40.39) — ver Analisar; reconciliação na Fase 3.
⚠ ITUB4: lentes divergem ~3.5× (DDM R$ 15.03 × regressão R$ 52.33) — ver Analisar; reconciliação na Fase 3.

 # TICKER       NOTA    ALVO R$   UPSIDE
 1 BBAS3        69.0          —  (amostra pequena)
 ...
```
Todos os alvos de regressão crus foram freados (amostra pequena, n=6<10) — o freio funciona; a
sinalização de divergência dispara honestamente. Reconciliação/ensemble real permanece
DEFERIDA à Fase 3, conforme escopo declarado no 01-08.

**5) Suíte completa e suítes-alvo:**

```
python -m pytest -q                                                    -> 389 passed, 0 failed
python -m pytest tests/test_arquetipo.py tests/test_guardrails_ddm.py
       tests/test_ranking_freio.py tests/test_ddm.py tests/test_selo.py
       tests/test_consistencia_modos.py -v                             -> 69 passed
```

**6) Firewall ddm.py/selo.py:**

```
git diff --stat 3642a2a~1..HEAD -- src/analista/core/ddm.py src/analista/report/selo.py
-> (vazio — nenhuma alteração em todo o intervalo 01-05..01-08)
```

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/analista/core/arquetipo.py::_cv_lucro` | sinal de ciclicidade robusto a crescimento desigual real | ✓ VERIFIED | Reescrito (01-05): dispersão dos resíduos de ajuste OLS log-linear de `ln(lucro)~tempo`; override de prejuízo (`_SINAL_PREJUIZO_CICLICO=10.0`) precede o guard de <3 pontos. Puro, sem I/O. Validado contra dados reais via rede nesta verificação (não só fixtures congeladas). |
| `src/analista/core/arquetipo.py::_setor_casa_token` | hard-route financeiro por limite de palavra, não substring solta | ✓ VERIFIED | Regex `\btoken(?:s\|es)?\b` (01-06). Confirmado: MDIA3 (setor real "Alimentos" após fix de resolução) não casa `banco`; ITUB4/BBAS3 (setor "Bancos") seguem casando. |
| `config.yaml::arquetipo.ciclica_cv_min` | recalibrado (0.35) com margem contra >=3 compounders + >=4 cíclicas reais | ✓ VERIFIED | `0.35` (linha 195-197 do bloco `arquetipo:`). Compounders reais medidos: 0.156-0.220 (WEGE3/RADL3/ABEV3/LREN3); cíclicas reais (com prejuízo): sinal-sentinela 10.0. Margem ampla, não fixado na borda de um único ponto. |
| `data/ticker_map.json::MDIA3` | override determinístico {cd_cvm, setor} com precedência sobre resolução por nome | ✓ VERIFIED | `MDIA3 -> {cd_cvm: 20338, setor: "Alimentos"}` (mesma forma do VULC3 pré-existente). Confirmado end-to-end: `universe.resolver("MDIA3", ...)` devolve cd 20338/Alimentos, não mais 21466/Bancos. |
| `src/analista/report/report.py::_guarda_faixa_ddm` | suprime faixa DDM negativa (`vmax<=0`) ou degenerada (`0-0`) na borda de emissão | ✓ VERIFIED | Confirmado contra HAPV3/PCAR3 reais via rede (`ddm_inaplicavel=True`, vmin/vmax=None) e golden frozen PRIO3 (0-0). Guard inverso (TAEE11 positivo, faixa-cruza-zero) preservado. `core/ddm.py` intocado (guard vive só na borda de `report.py`). |
| `src/analista/cli.py::alvo_regressao_confiavel` + `_motor_pendente` | freio do modo Ranking (R²/n/degenerado/motor_pendente) | ✓ VERIFIED | Confirmado por execução real: `cmd_rank` suprime todos os alvos crus (amostra pequena, n=6) mantendo a NOTA do ranque intacta; suspensão por arquétipo replicada via `ARQUETIPO_MOTOR.get(chave) is None`, paridade com a D-04 do Analisar. |
| `src/analista/core/comparables.py::divergencia_entre_lentes` + `LIMIAR_DIVERGENCIA` | sinalização honesta de divergência entre lentes (SEM reconciliação) | ✓ VERIFIED | Confirmado por execução real: WEGE3 (~3.5×), ITUB4 (~3.5×), BBAS3 (~2.2×), ROMI3 (~8.2×) disparam aviso `⚠`. Reconciliação/ensemble real explicitamente FORA de escopo (comentário no código + SUMMARY), corretamente deferida à Fase 3 — não é uma pendência silenciosa. |
| `app.py` (Streamlit UI) | exibe `a.arquetipo`/`a.motor` incondicional + nota de `ddm_inaplicavel` | ✓ VERIFIED (herdado, sem regressão) | `app.py:882` (arquétipo→motor, incondicional) e `app.py:926` (nota de inaplicabilidade DDM). Nenhuma mudança nesta rodada além da adição de `ddm_inaplicavel` pelo 01-07. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `arquetipo.py::classificar` | `CompanyData.roe_valuation/payout_valuation/serie/eh_concessionaria/setor` | consumo de sinais canônicos | ✓ WIRED | Inalterado; reconfirmado com dados reais via rede. |
| `arquetipo.py::classificar` | `config.yaml arquetipo:` | `cfg.get("arquetipo", {})` | ✓ WIRED | `ciclica_cv_min=0.35` lido corretamente. |
| `report.py::analisar_acao` | `arquetipo.classificar + ARQUETIPO_MOTOR` | import + lookup após CAPM | ✓ WIRED | Inalterado; reconfirmado end-to-end (CLI real). |
| `report.py::analisar_acao` | `_guarda_faixa_ddm` | chamada após vmin/vmax, antes do veredito | ✓ WIRED (NOVO — Achado 2) | Confirmado por execução real (HAPV3/PCAR3 suprimidos); `report.py:239`. |
| `cli.py::cmd_rank` | `arquetipo.classificar + ARQUETIPO_MOTOR` (via `_motor_pendente`) | paridade com suspensão D-04 do Analisar | ✓ WIRED (NOVO — Achado 3) | Confirmado por execução real (`cmd_rank` suprime alvo de tickers com motor pendente). |
| `cli.py::cmd_rank` | `comparables.divergencia_entre_lentes` | 2ª lente DDM (read-only via `analisar_acao`) × alvo de regressão | ✓ WIRED (NOVO — Achado 4) | Confirmado por execução real (avisos `⚠` emitidos para 4 tickers no rank de teste). |
| `data/ticker_map.json` | `universe.resolver` | override determinístico, precedência sobre match por nome | ✓ WIRED (NOVO — Achado 1b) | Confirmado: MDIA3 resolve para cd 20338/Alimentos, não mais o cadastro envenenado. |
| `app.py` (render) | `a.arquetipo` / `a.motor` / `a.ddm_inaplicavel` | `st.caption` | ✓ WIRED | Herdado do 01-04, sem regressão; `ddm_inaplicavel` adicionado pelo 01-07 (`app.py:926`). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `arquetipo.py::classificar` | `cv = _cv_lucro(c.serie("lucro_liquido"))` | série real de lucro (CVM, via rede) | Sim — WEGE3 real produz `crescimento` corretamente | ✓ FLOWING (gap fechado) |
| `report.py::_guarda_faixa_ddm` | `a.vmin`/`a.vmax` (matriz de sensibilidade) | HAPV3/PCAR3 reais via rede | Sim — faixa negativa real suprimida | ✓ FLOWING |
| `cli.py::cmd_rank` | `reg.r2_baixo`/`amostra_pequena`, `pendentes[tk]` | regressão real (n=6) + `arquetipo.classificar` real | Sim — freio disparado com dados reais | ✓ FLOWING |
| `comparables.py::divergencia_entre_lentes` | `ddm_mid[tk]` × `pa.preco_alvo` | `report.analisar_acao` real (read-only) × regressão real | Sim — divergências reais calculadas e exibidas (~2.2×-8.2×) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| WEGE3 (dados reais, rede) classifica crescimento | `python -m analista analyze WEGE3` | `*Arquétipo:* crescimento → motor pendente_fase_2` | ✓ PASS (gap fechado) |
| ITUB4 (dados reais, rede) classifica financeira | `python -m analista analyze ITUB4` | `*Arquétipo:* financeira → motor pendente_fase_2` | ✓ PASS |
| TAEE11 (dados reais, rede) classifica pagadora_regulada, motor ddm | `python -m analista analyze TAEE11` | `*Arquétipo:* pagadora_regulada → motor ddm` | ✓ PASS |
| VALE3 (dados reais, rede) classifica ciclica | `python -m analista analyze VALE3` | `*Arquétipo:* ciclica → motor pendente_fase_2` | ✓ PASS |
| MDIA3 não classifica financeira | `arquetipo.classificar` via `build.montar_empresa("MDIA3",...)` real | `pagadora_regulada` (≠ financeira) | ✓ PASS |
| DDM degenerado suprimido (HAPV3/PCAR3) | `report.analisar_acao` real | `ddm_inaplicavel=True`, vmin/vmax=None | ✓ PASS |
| Ranking freia alvo cru + sinaliza divergência | `python -m analista rank --tickers ROMI3,ITUB4,BBAS3,WEGE3,TAEE11,VALE3` | todos os alvos "—" (amostra pequena); 4 avisos de divergência emitidos | ✓ PASS |
| Suíte completa | `python -m pytest -q` | `389 passed, 0 failed` | ✓ PASS |
| Suítes-alvo SC#3 | `pytest tests/test_ddm.py tests/test_selo.py tests/test_consistencia_modos.py` | `21 passed` | ✓ PASS |
| `ddm.py`/`selo.py` intocados por 01-05..01-08 | `git diff --stat 3642a2a~1..HEAD -- ddm.py selo.py` | vazio | ✓ PASS |
| Nenhum marcador TODO/FIXME/TBD/XXX novo (real, não falso-positivo) | grep nos 9 arquivos tocados pela rodada | 2 hits, ambos falso-positivo ("atípico", "\\uXXXX") | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|--------------|--------|----------|
| ARQ-01 | 01-01, 01-02, 01-03, 01-05, 01-06 | Classifica o arquétipo antes de valuar (setor CVM + refino quantitativo por ROE/retenção/oscilação) | ✓ SATISFIED (gap fechado) | Hard-route por setor correto (financeira/regulada, incl. defesa MDIA3). Refino quantitativo agora classifica corretamente o caso nomeado explicitamente no roadmap (WEGE3 real → crescimento) e os cíclicos genuínos (VALE3/GGBR4/SUZB3/PETR4 → ciclica). REQUIREMENTS.md `[x]` não é mais prematuro. |
| ARQ-02 | 01-01, 01-02 | Fallback honesto: fronteiriço + 2-3 lentes candidatas em conflito real | ✓ SATISFIED | Mecanismo inalterado e reconfirmado; captura corretamente conflitos reais de sinal (GGBR4/SUZB3 com payout real via rede). |
| ENG-01 | 01-01, 01-02 | Registry arquétipo→motor consumido na agregação do veredito | ✓ SATISFIED | Inalterado; reconfirmado end-to-end via CLI real, incl. replicado no modo Ranking (01-08). |
| ENG-06 | 01-02 | DDM permanece motor primário para pagadora madura/regulada, sem quebrar o que já funciona | ✓ SATISFIED | TAEE11 real via rede → `pagadora_regulada`/`ddm`; `ddm.py`/`selo.py` comprovadamente intocados por toda a rodada 01-05..01-08; testes-alvo verdes. |

**Orphaned requirements check:** REQUIREMENTS.md mapeia exatamente ARQ-01, ARQ-02, ENG-01, ENG-06
à Fase 1; nenhum requisito órfão.

**Nota informativa (fora do escopo desta fase):** REQUIREMENTS.md também marca `SAN-01` e
`ENS-01` como `[x] Complete` sob "Phase 3", atribuídos aos planos 01-07/01-08 desta rodada de
gap-closure (pull-forward de capacidade de Fase 3 para fechar os Achados 2/3/4 do audit). Isso é
consistente com o escopo explicitamente autorizado pelo prompt desta verificação ("Achado 2/3/4
fixes são Phase-3 capability pulled forward") e não afeta o veredito da Fase 1 — os 4
requisitos-contrato da Fase 1 (ARQ-01/02, ENG-01/06) são os únicos avaliados aqui. A reconciliação
completa (ensemble DDM × motor do arquétipo) permanece corretamente deferida à Fase 3, conforme
declarado no 01-08-SUMMARY.md.

### Anti-Patterns Found

Nenhum anti-pattern bloqueador ou de aviso encontrado nos 9 arquivos tocados pela rodada de
gap-closure (01-05 a 01-08): `src/analista/core/arquetipo.py`, `src/analista/core/comparables.py`,
`src/analista/report/report.py`, `src/analista/cli.py`, `config.yaml`, `data/ticker_map.json`,
`tests/test_arquetipo.py`, `tests/test_guardrails_ddm.py`, `tests/test_ranking_freio.py`, `app.py`.

Os 2 hits de grep para `TODO|FIXME|TBD|XXX|HACK|PLACEHOLDER` são falso-positivo (fragmentos de
palavras em português — "atípico" — e um literal de regex `\\uXXXX` em `app.py` sobre escape
JS/JSON, não um marcador de débito técnico).

Anti-patterns WR-01 a WR-04 carregados de rodadas de verificação anteriores (não relacionados aos
gaps desta rodada, fora do escopo dos planos 01-05..01-08) não foram re-auditados aqui.

Nenhum marcador de débito não referenciado encontrado nos arquivos desta rodada — gate de
marcador limpo.

### Human Verification Required

None. Todos os achados desta rodada são verificáveis programaticamente contra dados CVM/Yahoo
reais (via rede, sem mock) e contra o cache CVM offline — nenhum comportamento
visual/UX/tempo-real precisou de confirmação manual. A UI Streamlit (`app.py`) já havia sido
verificada por leitura direta do código nas rodadas anteriores e não foi alterada por esta rodada
além da adição do caption de `ddm_inaplicavel` (01-07), textualmente idêntico em padrão ao caption
de arquétipo/motor já confirmado.

### Gaps Summary

Nenhum gap remanescente. As duas rodadas de verificação anteriores mantiveram aberto o Gap 1
(SC#1/WEGE3): o sinal de ciclicidade antigo (CV dos retornos ano-a-ano) media a variância da TAXA
de crescimento, indistinguível de uma cíclica genuína para compounders reais de crescimento
desigual. O plano 01-05 substituiu o sinal por dispersão de resíduos de ajuste log-linear
(medindo desvio da TENDÊNCIA, não da taxa), recalibrou o corte com margem contra >=3 compounders
reais e >=4 cíclicas reais, e travou a correção com goldens de séries CVM REAIS (não mais
progressões geométricas sintéticas). Esta verificação reproduziu o resultado de forma
independente — tanto offline (cache CVM) quanto via execução end-to-end real do CLI com rede —
confirmando `WEGE3 → crescimento` sem fronteira, a evidência mais forte disponível.

O audit de coerência (01-AUDIT-COERENCIA.md), rodado no meio do processo de gap-closure, revelou 3
achados adicionais fora do escopo original da Fase 1 mas relacionados: over-match do hard-route
financeiro (MDIA3, Achado 1b — corrigido pelo 01-06), faixas DDM degeneradas/negativas emitidas
como intrínseco (Achado 2 — corrigido pelo 01-07, guarda-corpo puro na borda de `report.py`, sem
tocar `ddm.py`), e ausência de freio de arquétipo + sinalização de divergência no modo Ranking
(Achados 3 e 4 — corrigidos pelo 01-08, com a reconciliação/ensemble completa corretamente
deferida à Fase 3, sem "stub silencioso"). Todos os 4 achados foram fechados e verificados nesta
rodada com evidência de execução real (não apenas citação de SUMMARY), sem regressão na suíte
(389 passed) nem no firewall `ddm.py`/`selo.py` (intocado em todo o intervalo).

---

_Verified: 2026-07-11T21:15:54Z_
_Verifier: Claude (gsd-verifier)_
