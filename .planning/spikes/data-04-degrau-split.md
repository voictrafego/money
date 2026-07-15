# Spike DATA-04 — onde está (hoje) o degrau artificial de ~13% no ITUB4

**Data:** 2026-07-15
**Estado medido:** pós-planos 09-01 (DATA-01/02) e 09-02 (DATA-03), com `num_acoes` já vindo da
contagem oficial da CVM (`composicao_capital`) por ano.
**Método:** medição offline (cache CVM) + leitura estática dos consumidores de séries ajustadas por
split. Script: `scripts/spike_data04_degrau_split.py` (reprodutível: `.venv/bin/python scripts/spike_data04_degrau_split.py`).

---

## Veredito

**O degrau artificial de ~13% NÃO EXISTE MAIS na série por-ação de VALUATION do ITUB4.** Ele foi
eliminado pela combinação de dois consertos anteriores, não por um bug que ainda vive numa linha:

1. **Fases 3–4** — `serie_precos` (o preço que o valuation e o gráfico consomem) passou a ser o
   **Close NOMINAL** (`auto_adjust=False`, `prices.py:174/183`), e o ajuste por split foi
   **isolado** em `dm.ohlc_ajustado` (`prices._ajustar_por_split`, `prices.py:93-133`), consumido
   **só** por indicadores técnicos e pelo candle do report — **nunca** cruzado com `num_acoes`.
2. **Plano 09-02 (DATA-03)** — `num_acoes` passou a ser a contagem oficial da CVM **por ano**
   (`build.py:136-154`), que carrega a bonificação real **exatamente uma vez**, no ano do evento.

Como a ref do requisito (`prices.py:71-111`) é **OBSOLETA** (hoje é o dataclass `DadosMercado` +
`_retornos_mensais`), a task de conserto seria escrita sobre a linha errada (Pitfall 6). A medição
substitui a suposição: o site real do split hoje é `prices._ajustar_por_split` (`prices.py:93-133`),
e ele **não alimenta nenhuma série por-ação de valuation**.

---

## Os dois ingredientes do degrau (ambos existem — mas nunca se multiplicam)

O degrau de ~13% seria o **double-count** da bonificação ITUB4 2024→2025. Os dois ingredientes:

- **Ingrediente A — `num_acoes` carrega o degrau REAL (medido, CVM oficial):**

  | ano | num_acoes_cru (composicao_capital) | razão ano/ano |
  |----:|-----------------------------------:|--------------:|
  | 2023 | 9.803.699 | 1,0003 |
  | 2024 | 9.748.073 | 0,9943 |
  | 2025 | 11.026.524 | **1,1311** |

  O salto 2024→2025 = **1,1311×** ≈ a bonificação real (≈1,1286×). É um degrau **legítimo** na
  contagem de ações — e aparece **uma única vez**, no ano do evento.

- **Ingrediente B — o Yahoo registra a MESMA bonificação como split (snapshot congelado):**
  `.splits` do ITUB4 traz `'2025-03-18': 1.1` e `'2025-12-26': 1.03` → produto **1,1 × 1,03 = 1,133**
  (≈ os "~13%" do requisito). `prices._ajustar_por_split` remove esse degrau do `ohlc_ajustado`.

**O double-count aconteceria SE** uma série por-ação de valuation multiplicasse `num_acoes` (com o
degrau real, ×1,133) por um preço **ajustado por split** (com o mesmo 1,133 removido) — a bonificação
contada duas vezes. **Isso não acontece**, porque os dois ingredientes estão em trilhos separados.

---

## O firewall (leitura estática dos consumidores — `grep src/`)

| Série | Ajustada por split? | Quem consome | Cruza `num_acoes`? |
|-------|---------------------|--------------|--------------------|
| `serie_precos` | **NÃO** (Close nominal) | valuation, gráfico, banda DDM | (preço × implied só em detectores) |
| `serie_precos_ajustada` | sim (Adj Close, total return) | **só RET-01** (retorno) | não |
| `ohlc_ajustado` | sim (split-only) | `report.py:682` (candle) + `intraday.py`/indicadores | **não** |
| `num_acoes` | n/a (contagem oficial/ano) | motores (LPA/PL) | — |

`num_acoes` só é cruzado com preço em `core/sanidade.py` (detectores SAN-01/SAN-03 — que existem
justamente para **reportar** esse tipo de divergência, não para alimentar valuation) e em
`motores.nav_contabil` (`PL / num_acoes`, sem preço e sem split). **Nenhuma série de valuation
multiplica `num_acoes` por um preço ajustado por split.**

---

## Consequência para a Task 2

O conserto é um **teste-guarda de regressão**, **sem edição de código de produção** (o próprio plano
prevê esse desfecho). O teste tem de ficar **vermelho se o degrau reaparecer** — isto é, se alguém:

- regredir `serie_precos` para o preço ajustado por split (desfazendo a Fase 3), **ou**
- cruzar `num_acoes` (com o degrau real) por um preço ajustado por split numa série de valuation.

Forma do assert (BLIND-04a): **razão adimensional ≈ 1**, ticker **sintético**, sem literal de R$ de
ticker real. A prova ancora no mecanismo REAL: com a bonificação `F`, `num_acoes` sobe `×F` e o preço
**nominal** cai `×(1/F)` → o produto (proxy de market cap) atravessa a fronteira **sem salto** (razão
≈ 1). Se o preço fosse ajustado por split, o produto saltaria `×F` ≈ 1,13 — o degrau, que o teste
reprova.
