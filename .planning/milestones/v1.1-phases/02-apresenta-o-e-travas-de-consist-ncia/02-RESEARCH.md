# Phase 2: Apresentação e Travas de Consistência - Research

**Researched:** 2026-06-05
**Domain:** Camada de apresentação Streamlit + testes de consistência cross-modo (Python/pytest)
**Confidence:** HIGH

## Summary

A Fase 1 já unificou a engine: os três modos (`Analisar`, `Garimpar BSD`, `Ranking`) consomem
funções canônicas (`payout_valuation()`, `roe()`, `dy_atual()`) e a engine já expõe todos os
campos que a Fase 2 precisa mostrar — `ultimo_ano()`, `ano_dpa`, `payout(ano)` cru, `payout_valuation()`
projetado, `n_fatores_faltantes`/`fatores_faltantes`, `PrecoAlvo.payout_fora_faixa` e `AnaliseAcao.vmin/vmax`.
**Não há cálculo novo a fazer na Fase 2** — é puramente wiring de apresentação (`app.py`) + testes.

Os cinco requisitos se resolvem em pontos cirúrgicos de `app.py`: ANO-01 adiciona uma coluna
"Ano-base" no Garimpo (linha ~213) e no Ranking (linha ~282), lendo `c.ultimo_ano()`/`c.ano_dpa`;
RANK-01 troca o `"—"` ambíguo (linhas 286-288) por `"indisponível"` quando o preço-alvo retorna
`None` por ROE/payout faltante; PAYOUT-02 expõe os dois payouts no Analisar (último ano vs.
projetado média 3a) — exige um campo novo `payout_valuation` no `AnaliseAcao` ou ler `c.payout_valuation()`
direto na UI. TEST-01 e TEST-02 entram no harness pytest existente (fixtures `CompanyData` construídas
à mão, sem rede), espelhando o estilo de `tests/test_screening.py::_empresa_solida`.

**Recomendação primária:** Tratar a Fase 2 como apresentação pura — ler campos já expostos pela engine,
nunca recomputar método em `app.py`; padronizar o rótulo `"indisponível"` (distinto de `"—"`); e escrever
TEST-01 montando UMA `CompanyData` fixture e afirmando que os três caminhos de engine produzem o mesmo
payout/ROE/veredito. **Streamlit 1.58.0 suporta `column_config`** — usar para rótulos de coluna e tooltips
de coluna onde fizer sentido, mantendo o padrão `help=h("chave")` já consolidado.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Cálculo de payout/ROE/veredito | Engine (`core`/`report`) | — | Fase 1 já unificou; Fase 2 NÃO recalcula |
| Exposição de ano-base/payout projetado | Engine (`fundamentals`/`report`) | App | engine já expõe `ultimo_ano`/`ano_dpa`/`payout_valuation`; falta só campo de payout projetado no `AnaliseAcao` |
| Renderização de ano-base, dual-payout, "indisponível" | App (`app.py`) | — | É apresentação: formatação de campos já calculados |
| Tooltips/rótulos das novas colunas | App (`app.py`) + `glossario.py` | — | padrão `help=h(...)` já estabelecido |
| Trava de consistência cross-modo | Tests (`tests/`) | — | pytest sobre fixtures `CompanyData`, sem rede |

## Standard Stack

### Core (já no projeto — nada a instalar)
| Library | Version (verificada) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | 1.58.0 | UI dos 3 modos | já em uso; `column_config` e `help=` suportados |
| pandas | 3.0.3 | DataFrames das tabelas | já alimenta todos os `st.dataframe` |
| pytest | 9.0.3 | harness de teste | golden + consistência já rodam nele |
| numpy | (instalado) | regressão (`comparables`) | dependência da engine, não tocada na Fase 2 |

`[VERIFIED: .venv/bin/python -c "import streamlit; print(streamlit.__version__)"]` → 1.58.0
`[VERIFIED: .venv/bin/python -c "import pandas; print(pandas.__version__)"]` → 3.0.3
`[VERIFIED: .venv/bin/pytest tests/ -q]` → 44 passed in 0.08s (estado atual, antes da Fase 2)

**Instalação:** Nenhuma. Custo zero respeitado; nenhuma dependência nova é necessária para apresentação + testes.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| coluna nova no `st.dataframe` | `st.column_config.Column(help=...)` | column_config dá tooltip por coluna (1.23+); útil para "Ano-base" e dual-payout, mas o padrão atual do app é `st.dataframe(...)` simples + `help=` no `st.markdown`/`st.metric`. Manter consistência: usar column_config só se agregar clareza, senão seguir o padrão atual. `[VERIFIED: streamlit 1.58.0 >> 1.23]` |
| campo novo `payout_valuation` em `AnaliseAcao` | ler `c.payout_valuation()` direto na UI | ler direto na UI é mais simples e NÃO viola "não recalcular método" (é a função canônica da engine, não um recálculo). Recomendado: ler direto, sem inflar o dataclass — a menos que o planner prefira simetria com `vmin/vmax`. |

## Architecture Patterns

### System Architecture Diagram (fluxo de dados — Fase 2 destacada)

```
                  config.yaml ──► CFG (ANO_BASE, N_ANOS)
                       │
  ticker(s) ──► montar() [cache] ──► CompanyData (engine, Fase 1) ────────────┐
                                       campos JÁ expostos:                      │
                                       • ultimo_ano()                           │
                                       • ano_dpa / dpa_trailing_12m             │
                                       • payout(ano)  [último ano, cru]         │
                                       • payout_valuation() [proj. média 3a]    │
                                       • roe(ano)                               │
                                       │                                        │
        ┌──────────────────┬──────────┴───────────────┐                        │
        ▼                  ▼                           ▼                        │
   analisar_acao()    bsd_ranking()            ranking_por_multiplos()          │
   → AnaliseAcao      → [{bsd, fatores_        + ajustar_regressao_pl()         │
     • vmin/vmax        faltantes,             + preco_alvo_por_regressao()     │
     • multiplos        n_fatores_              → PrecoAlvo                      │
       ["DP(payout)"]    faltantes,...}]          • payout_fora_faixa           │
       = payout(ult)                              • (None se ROE/payout falta)  │
        │                  │                           │                        │
        ▼                  ▼                           ▼                        │
  ┌─────────────────────────────────────────────────────────────────────┐     │
  │  app.py — CAMADA DE APRESENTAÇÃO (alvo da Fase 2)                     │◄────┘
  │  PAYOUT-02: Analisar mostra payout(ult) E payout_valuation() rotulados│
  │  ANO-01:   Garimpo+Ranking mostram coluna "Ano-base" (ultimo_ano)     │
  │  RANK-01:  Ranking troca "—" por "indisponível" quando alvo=None      │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ▼
  tests/ — TRAVAS (Fase 2): TEST-01 cross-modo / TEST-02 golden verde
```

### Render sites exatos em `app.py` (o planner deve mirar estas linhas)

| Requisito | Modo | Local em `app.py` | O que existe hoje | O que muda |
|-----------|------|-------------------|-------------------|------------|
| ANO-01 | Garimpo | `app.py:213-221` (dict `rows`) | colunas Ticker/BSD/Passa filtros/Fatores/Setor | adicionar `"Ano-base": c.ultimo_ano()` (e/ou `c.ano_dpa`) |
| ANO-01 | Ranking | `app.py:282-289` (dict `rows`) | Ticker/Nota/Preço/Preço-alvo/Upside/Veredito | adicionar `"Ano-base": <empresa>.ultimo_ano()` |
| RANK-01 | Ranking | `app.py:286-288` (`"—"` em Preço-alvo/Upside/Veredito) | `fmt_rs(pa.preco_alvo) if pa else "—"` | quando `pa is None` por dado faltante → `"indisponível"` (distinguir de "cara") |
| PAYOUT-02 | Analisar | `app.py:107-113` (métricas) + `app.py:121-132` (aba Múltiplos) | só `payout(ult)` em `a.multiplos["DP (payout)"]` (linha 127-128) | mostrar AMBOS rotulados: "Payout (último ano)" = `payout(ult)` e "Payout p/ valuation (média 3a)" = `c.payout_valuation()` |

### Pattern 1: UI lê campo da engine, nunca recalcula (LOCKED na Fase 1)
**What:** A camada de apresentação só formata campos já expostos pela engine canônica.
**When to use:** Sempre nesta fase. ANO-01/PAYOUT-02/RANK-01 são todos "ler campo + formatar".
**Example:**
```python
# Source: app.py:107 (padrão já estabelecido na Fase 1 — VAL-01/WR-07)
intervalo = f"{fmt_rs(a.vmin)} – {fmt_rs(a.vmax)}" if a.vmin is not None and a.vmax is not None else "—"
# Fase 2 segue o mesmo molde para payout projetado:
payout_proj = c.payout_valuation()  # função canônica, NÃO é recálculo de método
```

### Pattern 2: Tooltip via `help=h("chave")` (padrão do app)
**What:** Texto de ajuda vem de `glossario.G` via `h(chave)`; markdown renderiza no tooltip.
**When to use:** Ao adicionar rótulos novos (dual-payout, "Ano-base", "indisponível") que precisem de explicação.
**Example:**
```python
# Source: app.py:71,109-113 + glossario.py:102-104
st.sidebar.metric("Selic (corte do DY)", fmt_pct(selic_atual()), help=h("selic"))
m4.metric("ROE", fmt_pct(a.multiplos.get("ROE")), help=h("roe"))
# Fase 2: adicionar chaves novas a glossario.G (ex.: "ano_base", "payout_dual", "indisponivel")
```

### Pattern 3: Formatação tolerante a None (helpers do app)
**What:** `fmt_pct`, `fmt_num`, `fmt_rs` retornam `"—"` para None. RANK-01 precisa de um rótulo DIFERENTE.
**When to use:** RANK-01 deve distinguir "indisponível" (dado faltante) de "—" (genérico). Não reusar `fmt_rs` cru.
**Example:**
```python
# Source: app.py:48-57 (helpers atuais — todos devolvem "—" para None)
def fmt_pct(x, casas=1): return "—" if x is None else f"{x*100:.{casas}f}%"
# Fase 2: para RANK-01, o veredito/alvo deve dizer "indisponível" quando pa is None
#         por ROE/payout faltante — NÃO o "—" ambíguo lido como "cara".
```

### Anti-Patterns to Avoid
- **Recomputar payout/ROE/min-max em `app.py`:** quebra a unificação da Fase 1. Sempre ler `c.payout_valuation()`, `c.payout(ult)`, `a.vmin/vmax`.
- **Reescrever fórmulas de valuation:** explicitamente OUT OF SCOPE (REQUIREMENTS.md). As fórmulas estão corretas (IN-01..05).
- **Forçar o mesmo ano-base entre empresas:** a decisão LOCKED é EXIBIR o ano-base (ANO-01), não uniformizar (ver STATE.md blocker CR-02 parte 2).
- **Usar `"—"` para dado faltante no Ranking:** é exatamente o bug do RANK-01 (lido como "cara").

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Payout projetado p/ valuation | recalcular média 3a + clamp na UI | `c.payout_valuation()` | função canônica única (Fase 1) — recalcular reintroduz CR-02/WR-03 |
| Ano-base de uma empresa | derivar de `c.anos` na UI | `c.ultimo_ano()` (e `c.ano_dpa` p/ DPA) | já é o método único usado pelos 3 modos |
| Intervalo intrínseco | `min/max([ddm_h, ddm_constante])` na UI | `a.vmin`/`a.vmax` | Fase 1 já removeu essa duplicação (WR-07) |
| Detectar empresa descartada da regressão | re-checar None/<=0 na UI | `pa is None` (retorno de `preco_alvo_por_regressao`) | a engine já retorna None quando `None in (dp,roe,lpa,preco)` ou `lpa<=0` (comparables.py:129) |
| Tooltips | strings inline espalhadas | `glossario.G` + `h(chave)` | padrão único de tooltips do app |

**Key insight:** Toda a "inteligência" de método já está na engine após a Fase 1. A Fase 2 não tem
direito de recomputar nada — qualquer cálculo em `app.py` é um bug de regressão de consistência.

## Campos exatos que a engine expõe (resposta à pergunta-chave #1)

> Fonte: leitura direta de `src/` nesta sessão `[VERIFIED: grep/read do código]`.

### `CompanyData` (`src/analista/core/fundamentals.py`)
| Campo/método | Assinatura | Linha | Semântica | Uso na Fase 2 |
|--------------|-----------|-------|-----------|---------------|
| `ultimo_ano()` | `-> Optional[int]` | fundamentals.py:54-56 | maior ano com lucro coletado | **ANO-01** (Garimpo + Ranking) |
| `ano_dpa` | `Optional[int]` (campo) | fundamentals.py:48 | ano-base do DPA usado no DY | ANO-01 (sinalizar ano do dividendo, se desejado) |
| `dpa_trailing_12m` | `Optional[float]` | fundamentals.py:47 | DPA 12m reais | contexto do DY (não obrigatório exibir) |
| `payout(ano)` | `(int) -> Optional[float]` | fundamentals.py:70-71 | payout CRU do ano (sem clamp) | **PAYOUT-02** (lado "último ano") |
| `payout_valuation(janela=3)` | `-> Optional[float]` | fundamentals.py:73-86 | média 3a + clamp 1.0 (canônico) | **PAYOUT-02** (lado "projetado/DDM") |
| `roe(ano)` | `(int) -> Optional[float]` | fundamentals.py:88-99 | PL médio; None no 1º ano | TEST-01 (coerência cross-modo) |
| `lpa(ano)` / `dpa(ano)` | `(int) -> Optional[float]` | fundamentals.py:64-68 | por ação | TEST-01 |

### `AnaliseAcao` (`src/analista/report/report.py`)
| Campo | Tipo | Linha | Semântica | Uso |
|-------|------|-------|-----------|-----|
| `multiplos["DP (payout)"]` | `Optional[float]` | report.py:56 | = `c.payout(ult)` (último ano, cru) | **PAYOUT-02** lado exibido |
| `vmin` / `vmax` | `Optional[float]` | report.py:37-38 | intervalo intrínseco único | já wired (VAL-01) |
| `veredito` | `str` | report.py:39 | texto SUBAVALIADA/SOBREAVALIADA/NO INTERVALO | TEST-01 |
| `alertas` | `List[str]` | report.py:40 | inclui "Payout > 100%" etc. | contexto |

> **PAYOUT-02 — fato central** `[VERIFIED: report.py:56 vs report.py:97]`: `a.multiplos["DP (payout)"]`
> é `c.payout(ult)` (último ano, cru), mas o DDM usa `payout_proj = c.payout_valuation()` (média 3a + clamp).
> Esses dois números **podem divergir** e hoje só o primeiro aparece na UI (app.py:127-128). O payout
> projetado NÃO está exposto em `AnaliseAcao` — a Fase 2 precisa expô-lo (campo novo OU ler `c.payout_valuation()`
> direto na UI, que é o caminho mais simples e não viola a regra de não-recalcular).

### `bsd_ranking()` retorno (`src/analista/core/screening.py:362-371`)
Cada item é dict com: `ticker`, `nome`, `setor`, `bsd`, `acima_de_80`, `indicadores`,
`fatores_faltantes` (List[str]), `n_fatores_faltantes` (int). `[VERIFIED: screening.py:362-371]`
— `n_fatores_faltantes` já é exibido (app.py:219); ANO-01 só precisa adicionar `ultimo_ano` ao lado.

### `PrecoAlvo` retorno (`src/analista/core/comparables.py:106-148`)
Campos: `pl_corrente`, `pl_esperado`, `lpa`, `preco_corrente`, `preco_alvo`, `upside`,
`subavaliada`, `payout_fora_faixa`. **Retorna `None`** quando `None in (dp, roe, lpa, preco_corrente)`
ou `lpa <= 0` (comparables.py:129). `[VERIFIED: comparables.py:118-148]`
— **Esse `None` é exatamente o gatilho do RANK-01:** hoje vira `"—"` (app.py:286-288), deve virar `"indisponível"`.

## Streamlit: padrões em uso no app (resposta à pergunta-chave #3)

`[VERIFIED: read app.py]`
- **Tabelas:** sempre `st.dataframe(pd.DataFrame(...), hide_index=True, use_container_width=True)`.
  Nunca `st.table`. (app.py:131, 147, 177, 226, 290)
- **Métricas:** `st.metric(label, valor, help=h("chave"))` em colunas (`st.columns(5)`). (app.py:108-113)
- **Tooltips:** `help=h("chave")` em `st.metric`, `st.markdown`, `st.subheader`, `st.radio`. (app.py:69,71,109-113,124,...)
- **Avisos/estados:** `st.success`/`st.error`/`st.warning`/`st.info` para veredito e mensagens. (app.py:99-104,227,295)
- **Abas:** `st.tabs([...])` no Analisar. (app.py:119)
- **`column_config`:** NÃO usado hoje, mas suportado (Streamlit 1.58.0). Opcional para tooltip por coluna
  nas tabelas do Garimpo/Ranking. `[VERIFIED: streamlit 1.58.0 — column_config GA desde 1.23]`
- **Cache:** `@st.cache_data` em `montar`/`selic_atual`/`carregar_config`. Não tocar.

**Recomendação:** seguir o padrão `st.dataframe` + coluna nova no dict `rows`; usar `help=h(...)` no
cabeçalho do bloco (markdown) ou `st.column_config.Column("Ano-base", help=h("ano_base"))` se quiser
tooltip por coluna. Não introduzir um padrão de UI novo (o app é deliberadamente minimalista).

## Estrutura de testes (resposta à pergunta-chave #4)

`[VERIFIED: read tests/, pyproject.toml, pytest run]`

### Harness
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config | `pyproject.toml` → `[tool.pytest.ini_options]` `pythonpath=["src"]`, `testpaths=["tests"]` |
| conftest | **nenhum** (não há `tests/conftest.py`) |
| Run command | `.venv/bin/pytest tests/ -q` |
| Estado atual | **44 passed in 0.08s** |

### Estilo de fixture (modelo para TEST-01)
Os testes constroem `CompanyData` **à mão**, sem rede — exatamente o que TEST-01 precisa:
```python
# Source: tests/test_screening.py:7-26 (_empresa_solida) e test_fundamentals_consistencia.py:15-21
c = CompanyData(ticker="X", anos=[2022, 2023, 2024])
c.lucro_liquido = {2022: 100, 2023: 100, 2024: 100}
c.dividendos = {2022: 150, ...}
c.num_acoes = {2022: 1, ...}
c.patrimonio_liquido = {...}
c.preco_atual = 30.0
```
- `test_screening.py::_empresa_solida` é a fixture mais completa (10 anos, todos os campos). TEST-01 pode reusar/inspirar-se nela.
- Testes existentes por módulo: `test_ddm.py` (8), `test_multiples.py` (10), `test_comparables.py` (7), `test_screening.py` (8), `test_fundamentals_consistencia.py` (9). **TEST-02 = manter todos os 44 verdes.**

### Como TEST-01 (coerência cross-modo) deve plugar
A mesma `CompanyData` deve passar pelos TRÊS caminhos de engine e produzir payout/ROE/veredito coerentes:
1. **Analisar:** `report.analisar_acao(c, CFG)` → `a.multiplos["ROE"]`, `a.multiplos["DP (payout)"]`, `a.veredito`, `a.vmin/vmax`.
2. **Ranking:** `c.roe(c.ultimo_ano())`, `c.payout_valuation()` (vetor DP), `cmp.preco_alvo_por_regressao(...)`.
3. **Garimpo:** `sc.indicadores_bsd(c)` / `c.dy_atual()` / `c.roe(...)`.

Asserções de coerência (exemplos):
- `c.roe(c.ultimo_ano())` usado pelo Ranking == ROE que o Analisar coloca em `a.multiplos["ROE"]` (ambos `c.roe(ult)`). `[VERIFIED: report.py:53 e app.py:261 chamam o mesmo c.roe(ult)]`
- `c.payout_valuation()` usado pelo DDM do Analisar (report.py:97) == o usado pelo vetor DP do Ranking (app.py:264). `[VERIFIED]`
- Veredito do Analisar coerente com `subavaliada` do preço-alvo do Ranking para a mesma empresa (mesma direção barato/caro), respeitando que são métodos diferentes (DDM vs regressão) — afirmar **direção/sinal**, não igualdade numérica.

> **Cuidado para o planner:** TEST-01 precisa de `CFG`. O app lê `config.yaml` via `carregar_config()`,
> mas o teste roda fora do Streamlit. Opções: (a) carregar `config.yaml` no teste com `yaml.safe_load`,
> (b) montar um `cfg` mínimo dict inline. O CLI (`cli.py`) já carrega cfg fora do Streamlit — espelhar essa carga. `[VERIFIED: cli.py:65 usa report.analisar_acao(c, cfg)]`
> A regressão (`ajustar_regressao_pl`) exige **≥4 empresas** (comparables.py:94) — TEST-01 do modo Ranking
> precisa de ≥4 fixtures OU testar só payout/ROE (que não exigem regressão).

## Common Pitfalls

### Pitfall 1: Confundir "—" (genérico) com "indisponível" (RANK-01)
**What goes wrong:** Reusar `fmt_rs(...) or "—"` para o caso de dado faltante mantém o bug do RANK-01.
**Why:** `"—"` é lido pelo usuário como "cara"/sem upside; "indisponível" comunica dado ausente.
**How to avoid:** Quando `pa is None` (empresa descartada da regressão), exibir literal `"indisponível"` em Preço-alvo/Upside/Veredito. Diferenciar de quando a regressão inteira não roda (n<4 → já tratado em app.py:295).
**Warning signs:** Empresa com ROE/payout None aparecendo com "—" no veredito do Ranking.

### Pitfall 2: Recalcular payout na UI para PAYOUT-02
**What goes wrong:** Implementar média 3a + clamp em `app.py` para mostrar o "projetado".
**Why:** Reintroduz a divergência que a Fase 1 eliminou.
**How to avoid:** Ler `c.payout_valuation()` (função canônica) e `c.payout(c.ultimo_ano())`. Rotular claramente: "último ano" vs "média 3a (usado no DDM)".
**Warning signs:** Aritmética de payout aparecendo em `app.py`.

### Pitfall 3: Mistura de anos invisível (ANO-01)
**What goes wrong:** Comparar empresas no Ranking/Garimpo onde cada uma tem `ultimo_ano` diferente sem avisar.
**Why:** `ultimo_ano()` depende de quais DFPs a CVM tinha na coleta (CR-02 parte 2). Empresas podem cair em anos diferentes.
**How to avoid:** Exibir a coluna "Ano-base" = `c.ultimo_ano()`. **Decisão LOCKED:** exibir, não uniformizar.
**Warning signs:** Coluna ausente; usuário assumindo todos no mesmo ano por causa da legenda "até ANO_BASE" (app.py:72).

### Pitfall 4: Quebrar um golden ao mexer no `AnaliseAcao`
**What goes wrong:** Adicionar campo/alterar `analisar_acao` e quebrar TEST-02.
**Why:** Os golden afirmam comportamento exato (ddm/multiples/comparables/screening).
**How to avoid:** Se expor payout projetado via campo novo no dataclass, dar `default None` (como `vmin/vmax`) — aditivo, não-quebrante. Rodar `pytest tests/ -q` após cada mudança. Preferir ler `c.payout_valuation()` na UI (zero risco de golden).

### Pitfall 5: `column_config` mudando o layout das tabelas
**What goes wrong:** Trocar `st.dataframe(df,...)` por column_config completo e alterar larguras/ordem.
**Why:** O app é minimalista e foi human-verified na Fase 1.
**How to avoid:** Mudança mínima — só adicionar coluna no dict `rows`. column_config apenas para tooltip/rótulo, se necessário.

## Code Examples

### ANO-01 no Garimpo (adicionar coluna)
```python
# Source: app.py:213-221 (dict rows do Garimpo) — adicionar campo
rows.append({
    "Ticker": c.ticker,
    "Ano-base": c.ultimo_ano(),          # ANO-01: ano-base efetivo
    "BSD": round(b.get("bsd") or 0, 1),
    "BSD > 80": "✅" if b.get("acima_de_80") else "",
    "Passa filtros": "✅" if rc.passou else "",
    "Fatores faltando": b.get("n_fatores_faltantes") or 0,
    "Setor": c.setor,
})
```

### RANK-01 no Ranking (indisponível vs —)
```python
# Source: app.py:282-289 — distinguir dado faltante de "cara"
pa = alvos.get(r["empresa"])
if pa is None:
    preco_alvo_txt, upside_txt, veredito = "indisponível", "indisponível", "indisponível (ROE/payout ausente)"
else:
    preco_alvo_txt = fmt_rs(pa.preco_alvo)
    upside_txt = fmt_pct(pa.upside) if pa.upside is not None else "—"
    veredito = ("Subavaliada ✅" if pa.subavaliada else "Cara 🔺")
    if pa.payout_fora_faixa:
        veredito += " ⚠️ payout ajustado"
```

### PAYOUT-02 no Analisar (dois payouts rotulados)
```python
# Source: app.py:107-128 — expor payout do último ano E o projetado (DDM)
payout_ult = a.multiplos.get("DP (payout)")   # = c.payout(ult), último ano cru
payout_proj = c.payout_valuation()            # média 3a + clamp 1.0 (usado no DDM)
# Mostrar ambos quando diferirem (rótulos sem ambiguidade); ex.: na aba Múltiplos ou métrica dedicada
# "Payout (último ano)" vs "Payout p/ valuation (média 3a)"
```

## State of the Art

| Old Approach (pré-Fase 1) | Current (pós-Fase 1) | When | Impact na Fase 2 |
|---------------------------|----------------------|------|------------------|
| payout 1a no Ranking, 3a no Analisar | `payout_valuation()` canônico nos dois | Fase 1 | PAYOUT-02 só precisa EXIBIR os dois números, não unificá-los |
| min/max recomputado na UI | `a.vmin/vmax` | Fase 1 (VAL-01) | molde para expor payout projetado |
| BSD min-max do lote | BSD absoluto + `fatores_faltantes` | Fase 1 | ANO-01 do Garimpo entra ao lado de `n_fatores_faltantes` (já exibido) |
| `"—"` ambíguo no Ranking | (ainda `"—"`) | — | **RANK-01 é justamente trocar isso por "indisponível"** |

**Deprecated/outdated:** `_media_payout_3a` local do report (removido na Fase 1 — não reintroduzir na UI).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Expor payout projetado lendo `c.payout_valuation()` direto na UI é preferível a inflar `AnaliseAcao` | Stack/PAYOUT-02 | baixo — ambos válidos; planner/usuário escolhe. Ler na UI é mais simples e não toca golden |
| A2 | TEST-01 deve afirmar DIREÇÃO (barato/caro) entre DDM e regressão, não igualdade numérica | Testes | médio — se o usuário quiser igualdade numérica, o teste precisaria de fixtures muito controladas; direção é o que "coerência" significa aqui |
| A3 | column_config é opcional; padrão atual (`st.dataframe` + dict rows) é suficiente | Streamlit | baixo — escolha estética, não funcional |

**Nada na categoria de versões/segurança é assumido:** versões verificadas via `.venv`.

## Open Questions (RESOLVED)

> Todas as três são micro-escolhas de UX não-bloqueantes, com defaults travados em 02-UI-SPEC.md.

1. **PAYOUT-02: onde mostrar o segundo payout?**
   - What we know: hoje só `payout(ult)` aparece (métrica + aba Múltiplos). `payout_valuation()` existe e é usado no DDM.
   - What's unclear: métrica dedicada (`st.metric`) vs. linha extra na tabela de múltiplos vs. caption na aba Valuation.
   - Recommendation: mostrar ambos rotulados na aba Múltiplos (linha "Payout — último ano" e "Payout — média 3a (DDM)"), exibindo a média 3a com destaque/aviso quando diferir do último ano. Decisão de layout fica para discuss/plan.
   - **RESOLVED:** default travado em 02-UI-SPEC.md → duas linhas rotuladas SEMPRE visíveis na aba Múltiplos ("Payout (último ano)" e "Payout p/ valuation (média 3a)"), não uma métrica condicional.

2. **TEST-01: cobrir o modo Ranking exige ≥4 empresas para a regressão.**
   - What we know: `ajustar_regressao_pl` retorna None com <4 (comparables.py:94).
   - What's unclear: se TEST-01 cobre veredito do Ranking (precisa regressão) ou só payout/ROE (não precisa).
   - Recommendation: TEST-01 mínimo = afirmar payout_valuation/roe iguais entre os caminhos (sem regressão). TEST-01 estendido (opcional) = montar ≥4 fixtures para checar direção do veredito Ranking vs Analisar.
   - **RESOLVED:** o critério de sucesso #4 do ROADMAP torna a direção do veredito OBRIGATÓRIA — o plano 02-02 monta ≥4 fixtures determinísticas para a regressão rodar e afirma a direção (subavaliada/cara) sem `pytest.skip`. Não é mais "opcional".

3. **ANO-01: exibir também `ano_dpa` (ano do dividendo) além de `ultimo_ano`?**
   - What we know: `ano_dpa` existe e é o ano-base do DPA do DY; pode diferir do `ultimo_ano` (fundamentos).
   - What's unclear: se o requisito quer só o ano dos fundamentos ou também o ano do dividendo.
   - Recommendation: ANO-01 pede `ultimo_ano` explicitamente — exibir esse. `ano_dpa` é nice-to-have (pode ir num tooltip).
   - **RESOLVED:** default travado em 02-UI-SPEC.md → coluna `ultimo_ano` na tabela; `ano_dpa` vai no tooltip (column_config ou caption — ambos aceitáveis).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| streamlit | UI (apresentação) | ✓ | 1.58.0 | — |
| pandas | tabelas | ✓ | 3.0.3 | — |
| pytest | TEST-01/02 | ✓ | 9.0.3 | — |
| Python | tudo | ✓ | 3.14 (.venv) / req ≥3.10 | — |

**Nota:** Os testes NÃO precisam de rede (CVM/Yahoo/BCB) — fixtures `CompanyData` são montadas à mão.
A UI em runtime usa rede via `montar()`, mas isso é pré-existente e fora do escopo da Fase 2.

## Validation Architecture

> `workflow.nyquist_validation` está **false** em `.planning/config.json` `[VERIFIED]`. Seção incluída em forma resumida porque TEST-01/TEST-02 são requisitos explícitos da fase.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run | `.venv/bin/pytest tests/ -q` |
| Full suite | `.venv/bin/pytest tests/ -q` (mesmo; suíte pequena, 0.08s) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Comando | Arquivo |
|--------|----------|-----------|---------|---------|
| TEST-01 | mesma empresa → payout/ROE/veredito coerentes entre 3 modos | unit/integração | `pytest tests/test_consistencia_modos.py -x` | ❌ criar (Wave 0) |
| TEST-02 | golden existentes verdes | regressão | `pytest tests/ -q` | ✅ existe (44 testes) |
| ANO-01/RANK-01/PAYOUT-02 | apresentação correta | manual (Streamlit) + lógica via TEST-01 | verificação humana no navegador | parcial |

### Wave 0 Gaps
- [ ] `tests/test_consistencia_modos.py` — TEST-01 (cross-modo). Pode reusar fixture estilo `_empresa_solida`.
- [ ] (opcional) helper para carregar `config.yaml` no teste OU `cfg` mínimo inline para `analisar_acao`.
- *Sem necessidade de novo conftest ou instalação — infra de teste já cobre o resto (TEST-02).*

## Security Domain

> `security_enforcement` não está definido em config.json. App é local, sem auth, sem entrada de
> rede além de tickers digitados (passados a yfinance/CVM). Fase 2 é apresentação + testes, sem nova
> superfície de ataque. **V5 (Input Validation):** tickers já são normalizados (`.strip().upper()`),
> e a validação só em borda (CLAUDE.md). Nenhuma categoria ASVS nova aplicável a esta fase.

## Project Constraints (from CLAUDE.md + STATE.md)

| Constraint | Fonte | Implicação na Fase 2 |
|-----------|-------|----------------------|
| Python 3 + Streamlit, sem backend próprio | CLAUDE.md | nada novo; só `app.py` + `tests/` |
| Custo zero (só dados grátis) | CLAUDE.md | zero dependências novas |
| Golden tests devem continuar passando | CLAUDE.md / STATE.md / TEST-02 | rodar `pytest` após cada mudança; mudanças no dataclass devem ser aditivas (`default None`) |
| Não reescrever fórmulas de valuation | REQUIREMENTS.md (Out of Scope) | Fase 2 NÃO toca core/ de valuation; só apresentação |
| Não adicionar features além do pedido | CLAUDE.md | só os 5 requisitos; sem novos menus |
| Comentários só quando o "porquê" não é óbvio | CLAUDE.md | seguir estilo enxuto do app |
| Exibir ano-base, NÃO uniformizar | STATE.md (CR-02 parte 2) | ANO-01 = coluna informativa, não força mesmo ano |
| GSD workflow (não editar fora de comando) | CLAUDE.md | execução via `/gsd-execute-phase` |

## Sources

### Primary (HIGH confidence)
- Código-fonte lido nesta sessão: `app.py`, `src/analista/core/{fundamentals,comparables,screening}.py`, `src/analista/report/report.py`, `src/analista/glossario.py`, `tests/*.py`, `pyproject.toml`, `config.yaml` (parcial via app.py)
- `.planning/phases/01-engine-de-consist-ncia/01-0{1,2,3,4,5}-SUMMARY.md` — o que a Fase 1 entregou
- `.planning/{REQUIREMENTS,ROADMAP,STATE}.md` — requisitos, critérios, decisões LOCKED
- `CONSISTENCY-REVIEW.md` — CR-02, CR-03, WR-03 (findings que a Fase 2 fecha)
- `.venv` — versões verificadas (streamlit 1.58.0, pandas 3.0.3, pytest 9.0.3)
- `pytest tests/ -q` → 44 passed (baseline TEST-02)

### Secondary (MEDIUM confidence)
- Streamlit `column_config` GA desde 1.23 (conhecimento de docs; versão local 1.58.0 >> 1.23, suporte garantido)

## Metadata

**Confidence breakdown:**
- Campos da engine: HIGH — lidos linha a linha no código-fonte
- Render sites em app.py: HIGH — localizados por linha
- Harness de teste: HIGH — testes lidos e executados (44 passed)
- Padrões Streamlit: HIGH — observados no app + versão verificada
- Layout exato de PAYOUT-02: MEDIUM — decisão de UX fica para plan/discuss

**Research date:** 2026-06-05
**Valid until:** 2026-07-05 (projeto estável, repo local; reavaliar se a engine mudar)
