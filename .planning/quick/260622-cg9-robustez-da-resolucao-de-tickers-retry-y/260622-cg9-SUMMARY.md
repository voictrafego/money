---
phase: quick-260622-cg9
plan: 01
subsystem: ingest
tags: [tickers, yahoo, cvm, resolucao, retry, robustez]
requires: []
provides:
  - coletar_mercado com retry interno de fetch (FIX 1)
  - _norm cirurgico (fronteira de palavra) + fallback token-set em resolver (FIX 2)
  - ticker_map.json com 8 overrides deterministicos verificados (FIX 3)
affects:
  - src/analista/ingest/prices.py
  - src/analista/ingest/universe.py
  - data/ticker_map.json
tech-stack:
  added: []
  patterns:
    - "retry com backoff curto p/ rate-limit intermitente do Yahoo"
    - "remocao de tokens juridicos por fronteira de palavra (\\b) em vez de str.replace"
    - "casamento por sobreposicao de tokens (Jaccard/subset) com prefixo-abreviacao como fallback aditivo"
key-files:
  created:
    - tests/test_ingest_resolucao.py
  modified:
    - src/analista/ingest/prices.py
    - src/analista/ingest/universe.py
    - data/ticker_map.json
decisions:
  - "Retry trata exceção OU info sem nome E sem preço como tentativa falha; 3 tentativas, backoff 0.5s/1.0s; desiste sem propagar exceção (comportamento de desistência inalterado)."
  - "_norm remove sufixo jurídico (s.a./s/a/sa/s a/ltda) e conectivos só em fronteira de palavra (\\b), preservando Saneamento/Sao/SABESP/Energisa."
  - "Token-set é estritamente ADITIVO: roda só após exato E contém falharem; limiar Jaccard>=0.5 OU todos os tokens da CVM cobertos pelo alvo, com >=2 tokens em comum; empate -> nome CVM mais curto."
  - "Match de token aceita prefixo/abreviação (>=3 chars) para casar abreviações da CVM (bras~brasileira, prop~propriedades) sem afrouxar o limiar global."
  - "ELET3/ELET6 omitidos do override: sem CD_CVM ATIVO verificável no cad_cia_aberta em cache."
metrics:
  duration: 12
  completed: 2026-06-22
---

# Quick Task 260622-cg9: Robustez da resolução de tickers (retry Yahoo + token-set + override) Summary

Resolução de tickers robustecida atacando as 3 causas reais de "Não encontrei dados suficientes": Yahoo flaky (retry), nome legal divergente do longName (token-set + `_norm` corrigido) e override pequeno (8 entradas verificadas). Mudanças cirúrgicas e majoritariamente aditivas; precedência override→exato→contém preservada; 62 testes passam offline (49 golden + 13 novos).

## What Was Built

### FIX 1 — Retry de fetch no `coletar_mercado` (`prices.py`)
- `_fetch_info(tk)` extraído (mantém `tk.info or {}` com `try/except -> {}`), mockável.
- Laço de retry com `_MAX_TENTATIVAS = 3` e backoff curto (`0.5s`, `1.0s` via `time.sleep`).
- Tentativa "falha" = `_fetch_info` lança OU dict sem nome (longName/shortName) E sem preço (currentPrice/regularMarketPrice). Ao esgotar, segue com `info={}` sem propagar exceção (desistência idêntica à anterior).
- `history`/`dividends` e a montagem do `DadosMercado` intocados; assinatura e dataclass inalterados.

### FIX 2 — `_norm` cirúrgico + fallback token-set (`universe.py`)
- `_norm` agora remove sufixos jurídicos e conectivos como **tokens em fronteira de palavra** (`re.sub(r"\b...\b", ...)`), corrigindo o bug do `str.replace(" sa", " ")` que gerava "neamento"/"o". Pontuação `.`/`/` é separada antes para casar `s.a.`/`s/a`.
- `resolver`: caminhos override → guard cad/nome → exato → contém **inalterados** (retornam direto). Só após exato E contém falharem entra `_resolver_token_set`.
- Token-set: une tokens significativos (len>2) do nome completo e dos segmentos separados por ` - ` (marca à parte, ex. `... - SABESP`); escolhe a empresa CVM com mais tokens em comum sob limiar de segurança (Jaccard>=0.5 OU todos os tokens da CVM cobertos, >=2 em comum); empate → nome CVM mais curto. Match de token aceita prefixo/abreviação (>=3 chars).

### FIX 3 — Override ampliado (`ticker_map.json`)
- +8 entradas verificadas no cadastro (SIT==ATIVO), agrupadas por bloco: BBSE3=23159, CXSE3=23795 (seguradoras); SBSP3=14443, CSMG3=19445 (saneamento); VIVT3=17671, TIMS3=24929 (telecom); JBSS3=20575, AGRO3=20036 (agro). 41 chaves no total, JSON válido.

## Tests
- `tests/test_ingest_resolucao.py` (novo, 13 casos, 100% offline):
  - retry: exceção→sucesso, info vazio→sucesso, todas falham→desiste sem exceção (fetch e `time.sleep` monkeypatched; `_yf` stubado com history/dividends vazios — sem rede).
  - `_norm`: preserva Saneamento/Sao/SABESP; remove S.A./S/A/SA/LTDA só em fronteira.
  - token-set: AGRO3→20036, SBSP3→14443 (sem casar CSMG 19445).
  - não-regressão: TOTVS→19992, Cosan→19836, Energisa→15253, TIM→24929 (via exato/contém, cadastro sintético via monkeypatch, override vazio).
- Suíte completa: `.venv/bin/python -m pytest tests/ -q` → **62 passed**. Golden tests (test_ddm, test_multiples, test_comparables, test_screening, test_consistencia_modos, test_fundamentals_consistencia) intactos.

## TDD Gate Compliance
- RED: `9a62c1e test(cg9-01): add failing offline tests...`
- GREEN: `9e1609c feat(cg9-01): retry...` (FIX 1), `70f5f71 feat(cg9-01): _norm + token-set` (FIX 2)
- FIX 3: `43869b2 feat(cg9-01): ampliar ticker_map.json` (dado, não-TDD)

## Omissão documentada: ELET3 / ELET6
Eletrobras (Centrais Elétricas Brasileiras) **não foi adicionada ao override**. O `cad_cia_aberta.csv` em cache não contém um CD_CVM com `SIT==ATIVO` correspondente — só consta `ELETROPAR` (CD 15784) com situação **cancelada**, que não corresponde a ELET3/ELET6. Inventar um CD_CVM violaria a regra de só registrar overrides verificados. Mitigação parcial: o retry (FIX 1) reduz falhas por rate-limit intermitente e o token-set (FIX 2) pode casar a Eletrobras por nome assim que o cadastro em cache for atualizado para uma versão que a contenha como ATIVO. Recomendação para o futuro: revalidar o cache da CVM e, se a Eletrobras aparecer como ATIVO, adicionar ELET3/ELET6 ao override de forma determinística.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug de teste] Assertion de substring trocada por assertion de token em `_norm`**
- **Found during:** Task 2 (verify de `_norm`)
- **Issue:** `assert "neamento" not in n` falhava porque "neamento" é substring legítima de "saneamento" (preservada corretamente). O intuito era detectar "neamento" como *token* solto (o bug do `str.replace`).
- **Fix:** asserts passam a operar sobre `.split()` (tokens), não substring.
- **Files modified:** tests/test_ingest_resolucao.py
- **Commit:** 70f5f71

**2. [Rule 1 - Bug de teste] Teardown da fixture chamava `cache_clear` no lambda monkeypatchado**
- **Found during:** Task 2 (token-set/regressão)
- **Issue:** `universe.carregar_cadastro.cache_clear()` no teardown rodava antes do monkeypatch restaurar o wrapper `lru_cache`, levantando AttributeError no `function` simples.
- **Fix:** `cache_clear()` só no setup; teardown delega a restauração ao monkeypatch.
- **Files modified:** tests/test_ingest_resolucao.py
- **Commit:** 70f5f71

**3. [Rule 2 - Robustez aditiva] Match de token com prefixo/abreviação no token-set**
- **Found during:** Task 2 (AGRO3 não casava)
- **Issue:** a CVM abrevia tokens ("BRAS"/"PROP") que o longName do Yahoo grafa por extenso ("Brasileira"/"Propriedades"); igualdade estrita deixava o Jaccard abaixo de 0.5 e impedia o match correto de AGRO3.
- **Fix:** `_token_casa` aceita prefixo de >=3 chars em qualquer direção; mantém o limiar global (sem afrouxar) e não gera falso-positivo (SBSP3 continua não casando CSMG).
- **Files modified:** src/analista/ingest/universe.py
- **Commit:** 70f5f71

## Self-Check: PASSED
- src/analista/ingest/prices.py — FOUND (retry + `_fetch_info` + `_MAX_TENTATIVAS`)
- src/analista/ingest/universe.py — FOUND (`_norm` com `\b`, `_resolver_token_set`, `_token_casa`)
- data/ticker_map.json — FOUND (41 chaves, JSON válido, sem ELET3/ELET6)
- tests/test_ingest_resolucao.py — FOUND (13 testes offline)
- Commits: 9a62c1e, 9e1609c, 70f5f71, 43869b2 — todos no git log
- Suíte completa: 62 passed (offline)
