# Phase 13: Pivôs, Contexto de Tendência e Níveis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-29
**Phase:** 13-piv-s-contexto-de-tend-ncia-e-n-veis
**Areas discussed:** Detecção de pivôs + calibração, Semanal + regra de Dow, Âncora dos níveis + stop default, Zonas de S/R clustering

---

## Detecção de pivôs + calibração

| Option | Description | Selected |
|--------|-------------|----------|
| Fractal N-barras + defaults agora | Fractal de Williams (N barras esq+dir); no-repaint trivial/determinístico; N em config (default 2); calibração deferida | ✓ |
| Fractal N-barras + research antes | Mesmo fractal, mas roda /gsd-research-phase para calibrar N em B3 antes de planejar | |
| scipy find_peaks (prominence) | find_peaks com prominence/distance; risco de repaint na borda | |

**User's choice:** Fractal N-barras + defaults agora
**Notes:** Garantia de no-repaint pesou; calibração empírica fica em config para depois, sem detour de research.

---

## Semanal + regra de Dow

| Option | Description | Selected |
|--------|-------------|----------|
| Resample W-FRI + Dow com desempate MM/ADX | Semanal por resample do diário; HH/HL com desempate MM/ADX; lateral no ambíguo; conflito penaliza score | ✓ |
| Resample W-FRI + Dow puro | Mesmo resample, rótulo só por sequência de pivôs | |
| Buscar timeframe '1wk' do Yahoo | Adiciona 1wk à engine da Fase 12 (mais rede, amplia contrato) | |

**User's choice:** Resample W-FRI + Dow com desempate MM/ADX
**Notes:** Sem nova rede e sem ampliar o contrato da Fase 12; reusa ADX/MMs existentes.

---

## Âncora dos níveis + stop default

| Option | Description | Selected |
|--------|-------------|----------|
| Último impulso + stop mais conservador | Âncora no último impulso confirmado; stop = mais distante entre swing e ATR×m; m=1,5 config | ✓ |
| Último impulso + stop só no swing | ATR×m só como fallback | |
| Último impulso + stop só ATR×m | Ignora swing estrutural | |

**User's choice:** Último impulso + stop mais conservador
**Notes:** Respeitar estrutura sem aperto excessivo; ATR derivado do TR já calculado no ADX.

---

## Zonas de S/R: clustering

| Option | Description | Selected |
|--------|-------------|----------|
| Cluster por ATR + Donchian | Agrupa pivôs com distância < k×ATR; largura adaptativa; + Donchian | ✓ |
| Cluster por % fixo + Donchian | Tolerância percentual fixa; não adapta à volatilidade | |
| Só Donchian | Sem clustering de pivôs | |

**User's choice:** Cluster por ATR + Donchian
**Notes:** Largura adaptativa é mais robusta entre papéis B3 distintos; Donchian já existe em SinaisTecnicos.

---

## Claude's Discretion

- Nomes de campos/dataclasses e organização interna dos módulos (desde que aditivos a `SinaisTecnicos`).
- Defaults finos dos params em `config.yaml` (k do cluster, janela de volume, janela Donchian para S/R).

## Deferred Ideas

- Calibração empírica de N (pivôs) / k (cluster) em ações B3 via `/gsd-research-phase`.
- Buscar timeframe `1wk` direto do Yahoo (preterido em favor do resample W-FRI).
- Trendlines automáticas desenhadas, OBV / volume relativo avançado.
