# Phase 10: Crescimento robusto + de-poison do screening - Pattern Map

**Mapped:** 2026-06-27
**Files analyzed:** 5 (1 new function + 4 modified) + 2 reused primitives
**Analogs found:** 5 / 5 (todos com analog exato no próprio módulo)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/core/growth.py` — NOVA função log-linear (GROW-01) | core / pure-fn | transform (série → escalar) | `growth.cagr` (L16) + `growth.crescimento_aritmetico` (L32) — mesmo módulo | exact |
| `src/analista/report/report.py` §`analisar_acao` L79 | report / orchestration | transform | já chama `growth.cagr(lucros[0], lucros[-1], …)` L79 + consome `serie_lucro_normalizada()` L77 | exact (in-place swap) |
| `src/analista/core/screening.py` §`indicadores_bsd` L261-276 | core / aggregation | transform (CRUD-like dict de indicadores) | `cagr_serie` closure L261-264 + `serie_winsorizada` (normalizacao L94) | exact |
| `src/analista/core/comparables.py` §`preco_alvo_por_regressao` L133 | core / pure-fn | transform (regressão) | clamp já existente L148 (`dp_clamp`) | partial (clamp parcial pré-existe) |
| call sites `cli.py:158-159` + `app.py:472` | cli / app surface | request-response | espelham-se (FIX-04 fonte única) | exact (par espelhado) |

**Reused primitives (read-only, sem edição):**
- `src/analista/core/normalizacao.py` §`serie_winsorizada` (L94-105) — winsoriza séries de div/FCO no screening (D-05).
- `src/analista/core/fundamentals.py` §`serie_lucro_normalizada` (L126-129) — série winsorizada que o g_historico log-linear consome (já usada em report.py L77).

---

## Pattern Assignments

### `src/analista/core/growth.py` — NOVA função log-linear (GROW-01, core, transform)

**Analog (template a espelhar):** `growth.cagr` (L16-29) e `growth.crescimento_aritmetico` (L32-46) no MESMO arquivo.

**Padrão de função pura a copiar — assinatura + fronteira de None + alias `Number`** (growth.py L9-46):
```python
from __future__ import annotations

from typing import Optional, Sequence

Number = Optional[float]


def cagr(valor_inicial: float, valor_final: float, n_periodos: int) -> Number:
    """Crescimento geométrico (CAGR) = (V_n / V_0)^(1/n) - 1.

    Exige base e ponta positivas (não faz sentido com valores <= 0).
    """
    if (
        valor_inicial is None
        or valor_final is None
        or n_periodos <= 0
        or valor_inicial <= 0
        or valor_final <= 0
    ):
        return None
    return (valor_final / valor_inicial) ** (1.0 / n_periodos) - 1.0


def crescimento_aritmetico(serie: Sequence[float]) -> Number:
    """Média aritmética das variações período a período."""
    if serie is None or len(serie) < 2:
        return None
    ...
```

**O que a nova função deve replicar do template:**
1. **Assinatura:** recebe `serie: Sequence[float]` (igual a `crescimento_aritmetico`), devolve `Number` (`Optional[float]`).
2. **Fronteira de None idêntica ao CAGR (D-03):** retornar `None` se `serie is None`, `len(serie) < 2`, OU **qualquer ponto ≤ 0** (em `cagr`: `valor_inicial <= 0 or valor_final <= 0` — para log-linear isso vira "qualquer ano ≤ 0", pois `ln` é indefinido em prejuízo). NÃO introduzir fallback aritmético que mudaria a fronteira de None (D-03, risco de regressão golden).
3. **Import discipline (D-01 / Claude's Discretion):** SÓ `numpy`/`statistics`. growth.py hoje **não importa numpy** — adicionar `import numpy as np` no topo. NÃO importar nada de `fundamentals`/`report`/`screening` (evitar ciclo — screening importa growth em L18, report em L16).
4. **Núcleo (D-01):** OLS de `ln(serie)` contra o tempo via `numpy.polyfit(x, np.log(y), 1)`; `slope = coef[0]`; `g = exp(slope) - 1`. Anualizado por construção (x em passo de 1 ano).
5. **Docstring no estilo do módulo:** referência ao Cap. 14 + "tendência de crescimento" (explicabilidade, D-01).

---

### `src/analista/report/report.py` §`analisar_acao` L79 (report, transform)

**Analog:** o próprio site de chamada — swap in-place. A série normalizada já está disponível em escopo (L77).

**Before-state EXATO a substituir** (report.py L76-79):
```python
lucros_raw = c.serie("lucro_liquido")
lucros = c.serie_lucro_normalizada()         # série winsorizada (já existe, L126 fundamentals)
if len(lucros) >= 2:
    a.g_historico = growth.cagr(lucros[0], lucros[-1], len(lucros) - 1)   # ← L79: CAGR endpoint a substituir
```

**After (D-01):** trocar `growth.cagr(lucros[0], lucros[-1], len(lucros) - 1)` pela nova função log-linear recebendo a **série inteira** `lucros` (usa todos os pontos). `lucros` já é `serie_lucro_normalizada()` — nenhuma mudança de fonte de dados.

**Downstream que NÃO muda (preservar):**
- `g_alto` (L93-98): já lê `a.g_historico`; o piso `g_alto = max(0.0, min(g_alto, 0.25))` (L97) trata o downstream — D-03 confia nele.
- `g_fundamentos` (L82): intacto.
- `lucros_raw` (L76) e os fatos per-ano `lucro_positivo`/`lucro_decrescente` (L103-104) leem a série **CRUA** — D-07, não tocar.

---

### `src/analista/core/screening.py` §`indicadores_bsd` L261-276 (core, aggregation)

**Analog:** o closure `cagr_serie` (L261-264) é o exato before-state; a primitiva de normalização é `normalizacao.serie_winsorizada` (L94).

**Before-state EXATO a substituir** (screening.py L260-277):
```python
# 8/9/10. crescimento de FCO, dividendos e lucro em 3 anos (CAGR)
def cagr_serie(d: Dict[int, float]):
    if len(anos) < 2:
        return None
    return growth.cagr(d.get(anos[0]), d.get(anos[-1]), len(anos) - 1)   # ← endpoint a substituir

return {
    ...
    "crescimento_fc_3a": cagr_serie(c.fco),
    "crescimento_dividendos_3a": cagr_serie(c.dividendos),
    "crescimento_lucro_3a": cagr_serie(c.lucro_liquido),
}
```

**After (D-04 + D-05):**
1. Substituir `cagr_serie` pelo MESMO estimador log-linear de GROW-01 (consistência Analisar↔Screening por construção, D-04).
2. Aplicar `normalizacao.serie_winsorizada(...)` às **três** séries antes do estimador (D-05): lucro, dividendos E FCO. Hoje screening.py importa só `from . import growth` (L18) — adicionar `from . import normalizacao` (ou `from .normalizacao import serie_winsorizada`).
3. Atenção à montagem da série: o estimador recebe **valores ordenados por ano**. Hoje `cagr_serie` lê `d.get(anos[0])` / `d.get(anos[-1])` sobre `anos = c.anos_ordenados()[-anos_media:]` (L211). Para a série completa winsorizada, montar `[d.get(a) for a in anos]` (ou usar `c.serie(attr)`) e passar por `serie_winsorizada` — note que `serie_winsorizada` faz `_limpar` (descarta None) internamente.

**Primitiva a reusar — `normalizacao.serie_winsorizada`** (normalizacao.py L94-105):
```python
def serie_winsorizada(valores: Sequence[Number], winsor: float = 0.10) -> List[float]:
    """Série (mesmo comprimento dos pontos válidos) com os extremos winsorizados.
    Com < 5 pontos válidos a winsorização não morde — devolve os limpos."""
    limpos = _limpar(valores)
    if len(limpos) < 5:
        return limpos
    lo = float(np.percentile(limpos, winsor * 100))
    hi = float(np.percentile(limpos, (1.0 - winsor) * 100))
    return [min(max(v, lo), hi) for v in limpos]
```

**Fronteira a PRESERVAR (D-07, NÃO tocar):**
- Banda absoluta `REFERENCIA_BSD` (L191-202) — em especial `"payout": (0.0, 0.80)` (L192) e os pares `crescimento_*_3a` (L199-201). Só a BASE do fator muda; a banda de padronização fica.
- Proxy per-ano `cresc_lucro_lp` via `crescimento_por_fundamentos(roe_medio, payout_medio)` (L255-258) com `roe(a)`/`payout(a)` **CRUS** — intacto.
- `var_tangivel` via `growth.cagr` (L247) — fora de escopo, fica CAGR.
- `payout` médio cru (L218) — D-07, intacto.

---

### `src/analista/core/comparables.py` §`preco_alvo_por_regressao` L133 + call sites (D-06)

**Analog:** clamp já existente DENTRO da função (L148) — o padrão de clamp `min(max(x, 0.0), 1.0)`.

**BEFORE-STATE NUANCE (crítico p/ o planner — clamp parcial já existe):**
A função **já clampa** o `dp` recebido por empresa na PREVISÃO (comparables.py L146-150):
```python
# Mesmo clamp do Analisar antes do DDM (report.py: payout_proj = min(media_3a, 1.0)):
dp_clamp = min(max(dp, 0.0), 1.0)
payout_fora_faixa = dp_clamp != dp
pl_esperado = reg.prever(dp_clamp, roe)
```
PORÉM o **AJUSTE da regressão** (`cmp.ajustar_regressao_pl(PL, DP, ROE)`) consome o vetor `DP` **NÃO clampado** — montado em `cli.py:149` (`DP.append(c.payout_valuation())`) e `app.py:466`. É aí que TAEE11 ≈ 2.16 (payout sem clamp, D-03 Fase 9) **envenena os coeficientes** `b1` da regressão. O clamp de L148 só corrige a previsão por-empresa, não o fit. O handoff `09-CROSS-EFFECT-FASE10.md` (L16-17) confirma: "A regressão foi calibrada com payout ∈ [0,1]. Alimentá-la com payout ≈ 2.16 pode envenenar o ajuste".

**D-06 — onde clampar (na ENTRADA das chamadas, sem mexer no canônico):**
- `cli.py:158-159` — `cmp.preco_alvo_por_regressao(reg, c.payout_valuation(), c.roe_valuation(), c.lpa_valuation(), c.preco_atual)`
- `app.py:472` — chamada espelhada idêntica.
- E (consequência da nuance acima) o vetor `DP` que alimenta `ajustar_regressao_pl` em `cli.py:154` / `app.py:468` também precisa do `min(payout, 1.0)` para o fit não ficar envenenado. **Confirmar com o planner** se D-06 cobre só a previsão (já clampada em L148) ou também o fit (origem real do poison segundo o handoff).

**NÃO fazer (D-06 explícito):** NÃO reintroduzir clamp em `payout_valuation()` (fundamentals.py L77-86) nem em `normalizacao.mediana_payout` (normalizacao.py L78-91) — D-03 da Fase 9 preservado, a mediana pode ser legitimamente >100%.

**Call sites espelhados — par a manter em sincronia** (cli.py L157-161):
```python
if reg:
    for c in empresas:
        pa = cmp.preco_alvo_por_regressao(
            reg, c.payout_valuation(), c.roe_valuation(), c.lpa_valuation(), c.preco_atual)
        if pa:
            alvos[c.ticker] = pa
```
app.py L470-474 é a mesma chamada inline — qualquer clamp aplicado num site DEVE ser aplicado no outro (FIX-04: consistência entre superfícies por construção).

---

## Shared Patterns

### Função pura (core estimadores)
**Source:** `src/analista/core/growth.py` (todo o módulo) + `src/analista/core/normalizacao.py` L1-36
**Apply to:** nova função log-linear
```python
from __future__ import annotations
from typing import Optional, Sequence
import numpy as np            # normalizacao.py L29 — padrão p/ numérico pesado

Number = Optional[float]      # alias de retorno em growth.py L13 e normalizacao.py L31
```
- Recebe `Sequence[Number]`, devolve `Number`. Guard-clauses no topo, retorno `None` na borda. Sem efeitos colaterais, sem I/O, sem imports da engine de fundamentos/report (evita ciclo). Docstring cita o capítulo do livro.

### Fonte única entre superfícies (FIX-04 / D-04)
**Source:** padrão `*_valuation()` chamado sem args em Analisar + cli + app
**Apply to:** o estimador de crescimento — Analisar (report.py) e Screening (screening.py) devem chamar a MESMA função log-linear sobre a MESMA base normalizada. Os call sites de `preco_alvo_por_regressao` (cli/app) devem receber o MESMO clamp.

### Clamp de payout `min(max(x,0.0),1.0)`
**Source:** `comparables.py` L148
**Apply to:** entrada da regressão de preço-alvo (D-06), espelhando o comentário que referencia o clamp do DDM no report.

### Fronteira CRU vs normalizado (D-07 / D-06 Fase 9)
**Source:** comentários em report.py L72-75/L101-104, screening.py, fundamentals.py L118-119
**Apply to:** TODAS as edições — só os **agregados de crescimento de série** mudam de base (normalizada). `roe(ano)`/`payout(ano)`/`lpa(ano)`/`lucro_liquido` CRUS continuam alimentando elegibilidade per-ano, tabela "Fundamentos por ano", detector de armadilha e banda `REFERENCIA_BSD`.

### Rebaseline deliberado de golden tests
**Source:** convenção do projeto (CLAUDE.md: golden em `tests/` devem passar) + D / `<specifics>`
**Apply to:** testes afetados pela troca CAGR→log-linear. Golden/golden-adjacentes identificados:
- `tests/test_growth_reconciliacao.py` — asserts diretos sobre `a.g_historico` (L65, L82, L100, L121) comparando com "CAGR cru". MUDAM com log-linear — rebaselinar deliberadamente, documentando o delta por ticker.
- `tests/test_screening.py` — `indicadores_bsd` (crescimento_*_3a).
- `tests/test_consistencia_modos.py`, `tests/test_comparables.py`, `tests/test_ddm.py` — verificar impacto indireto.
Validação multi-ticker é critério de aceite (`<specifics>`): VULC3 (ano extraordinário NÃO infla BSD/g) + TAEE11/EGIE3/ITUB4/BBAS3 (g e ranking NÃO regridem materialmente; TAEE11 payout≈2.16 NÃO distorce preço-alvo após clamp).

---

## No Analog Found

(nenhum — todos os pontos têm analog exato no próprio módulo; a fase é refator/swap de estimador, não criação de novo tipo de artefato)

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | — |

---

## Metadata

**Analog search scope:** `src/analista/core/` (growth, normalizacao, fundamentals, screening, comparables), `src/analista/report/`, `src/analista/cli.py`, `app.py`, `tests/`
**Files scanned:** 8 source + 5 test files grep'd
**Pattern extraction date:** 2026-06-27
**Key cross-cut:** import cycle — `screening` e `report` importam `growth`; o estimador novo NÃO pode importar de volta. Só `numpy`/`statistics`.
