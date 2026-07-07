# Phase 15: Montagem do Setup (SetupSwing) + Score - Research

**Researched:** 2026-06-29
**Domain:** Agregação read-only / scoring ponderado explicável sobre o contrato `SinaisTecnicos` (sem novas deps, sem novo método)
**Confidence:** HIGH (todo o material foi verificado lendo o código real do contrato; os *valores* numéricos do score são ASSUMED/calibráveis por design)

## Summary

A Fase 15 não introduz matemática de mercado nova: ela **lê** o dataclass `SinaisTecnicos` que `indicators.calcular()` já produz (Fases 12–14, golden-testado) e o destila num **score ponderado explicável** com **grade qualitativa PT-BR**, **R:R como gate duro** e **conflito multi-TF como penalização modulante**. O padrão arquitetural exato já existe no próprio repo: `_checklist` (em `indicators.py`) e `presentation.py` são agregadores read-only que só consomem rótulos/campos já computados, sem recalcular indicador algum. `SetupSwing` é o mesmo padrão, um nível acima: consome o contrato inteiro e devolve score + decomposição peso-a-peso + grade.

A descoberta mais importante do research resolve a ambiguidade do ROADMAP sobre `setups.*`: **`core/setups.py` NÃO existe** — as Fases 13/14 colocaram tudo em `indicators.py` (pivôs, Dow, níveis, padrões, checklist). Portanto a Fase 15 cria **apenas `report/setup.py`** (dataclass `SetupSwing` + funções de scoring). Criar um `core/setups.py` é opcional e só se justifica se o planner quiser golden-testar a matemática pura de scoring isolada do dataclass — recomendo manter tudo em `report/setup.py` no MVP (mesma decisão que pôs `_checklist` dentro de `indicators.py`, não num módulo à parte).

O firewall é trivialmente satisfeito: `report/report.py` **importa** `indicators` (não o contrário). `report/setup.py` importará `indicators` diretamente e **nunca** `report.py` — não há nada em `report.py` que o score precise. A degradação graciosa é obrigatória porque todos os sub-objetos de `SinaisTecnicos` (`contexto`, `niveis`, `padroes`, `volume`...) têm default `None` (aditivos): cada acesso precisa de guard → retorno neutro "Sem setup", nunca exceção para a UI.

**Primary recommendation:** Criar `report/setup.py` com o dataclass `SetupSwing` (read-only, com decomposição peso-a-peso em sub-objetos) e funções puras de scoring que consomem `SinaisTecnicos`; pesos/limiares num bloco novo `score:` no `config.yaml` (irmão de `padroes:`/`indicadores:`); R:R **recomputado** dos campos numéricos brutos de `Niveis` sob `np.errstate` (não do string localizado) atuando como gate duro; goldens construídos com stubs duck-typed de `SinaisTecnicos` (idioma `_familias_stub`) para cravar cada grade + gate + penalização sem flutuar os 271 testes existentes.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Cálculo de indicadores/níveis/padrões | `core/indicators.py` (engine) | — | Já entregue Fases 12–14; Fase 15 NÃO toca |
| Scoring ponderado + grade + gate R:R | `report/setup.py` (engine de apresentação) | (opcional `core/setups.py` se extrair math pura) | Read-only sobre o contrato; mesmo nível de `presentation.py`/`_checklist` |
| Parametrização (pesos, R:R mín, cortes) | `config.yaml` (bloco `score:`) | — | Config-driven, sem hardcode (D-01/D-03 SC-3) |
| Renderização do score/decomposição | `app.py` (UI read-only) | — | **Fase 16** — fora de escopo aqui |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | já instalado (.venv) | `np.errstate`/`np.divide`/`np.isfinite` no gate de R:R | Idioma já estabelecido na Fase 13 (`_niveis_stop_rr`) [VERIFIED: .venv import OK] |
| dataclasses (stdlib) | Python 3.14 | `SetupSwing` + sub-objetos de decomposição | Mesmo padrão de `SinaisTecnicos`/`AnaliseAcao` [VERIFIED: indicators.py, report.py] |
| pyyaml | já instalado | Carregar bloco `score:` do `config.yaml` | Já é como `cfg` chega à engine [VERIFIED: cli.py:32] |

**Zero novas dependências de runtime** — constraint inegociável do marco (ROADMAP). Nada a instalar. [VERIFIED: pyproject.toml, .venv]

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tudo em `report/setup.py` | `core/setups.py` (math pura) + `report/setup.py` (dataclass) | Separação testável vs. mais um módulo; o repo já optou por NÃO separar (`_checklist` mora em `indicators.py`). Discrição do planner. |
| Recomputar R:R dos campos brutos de `Niveis` | Parsear o string `niveis.risco_retorno` "1 : 2,5" | Parsear é frágil (locale vírgula BR, "indisponivel"); recomputar de `entrada_zona`/`stop`/`alvo` sob `np.errstate` é robusto e reusa o idioma da Fase 13. **Recomendo recomputar.** |

**Installation:**
```bash
# Nada a instalar — tudo já está no .venv
```

## Architecture Patterns

### System Architecture Diagram

```
indicators.calcular(ohlc, cfg, ohlc_nominal)
        │  (já existe — Fases 12-14, NÃO tocar)
        ▼
   SinaisTecnicos ──────────────────────────────────────────────┐
   ├─ contexto: ContextoTendencia (dow_diario, alinhamento_mtf)  │
   ├─ forca:    Forca (forca_adx, adx, ...)                      │
   ├─ tendencia:Tendencia (posicao_mm200, cruzamento, ...)       │
   ├─ niveis:   Niveis (entrada_zona, stop, alvo, risco_retorno) │  INSUMOS
   ├─ padroes:  Padroes (lista[PadraoGrafico])                   │  (read-only)
   ├─ momentum: Momentum (nivel_rsi, cruzamento_macd, ...)       │
   └─ volume:   Volume (rompimento_com_volume, ...)              │
                                                                 ▼
   report/setup.py  montar_setup(sinais, cfg)  ◄── cfg["score"] (pesos/limiares)
        │
        ├─ 1. guard: sinais/sub-objetos None? → SetupSwing("Sem setup") neutro
        ├─ 2. R:R numérico (recompute de Niveis sob np.errstate)
        │       └─ GATE DURO: rr < rr_minimo OU indisponível → "Sem setup" (zera)
        ├─ 3. sub-score por família ∈ [0,1]:
        │       tendência ← contexto.dow_diario + forca.forca_adx + posicao_mm200
        │       r:r       ← razão normalizada
        │       padrões   ← padroes.lista (tipo+estado, coerência c/ dow)
        │       momentum  ← momentum.nivel_rsi + cruzamento_macd
        │       volume    ← volume.rompimento_com_volume
        ├─ 4. score = Σ(sub_score_i × peso_i) × 100   (pesos 35/20/20/15/10)
        ├─ 5. penalização multi-TF: alinhamento_mtf=="conflito" → score ×(1−penalidade)
        └─ 6. grade ← cortes(config): Forte/Moderado/Fraco; gate/floor → "Sem setup"
                                                                 │
                                                                 ▼
                                          SetupSwing (dataclass read-only)
                                          ├─ score: float (0-100)
                                          ├─ grade: str ("Forte"|"Moderado"|"Fraco"|"Sem setup")
                                          ├─ decomposicao: list[ContribFamilia]  ◄── peso-a-peso
                                          ├─ gate_rr_ok: bool / rr_valor: float|None
                                          ├─ conflito_mtf: bool (penalização aplicada)
                                          └─ niveis_estudo: (entrada/stop/alvo como referência)
                                                                 │
                                                                 ▼
                                          Fase 16: app.py (thin renderer, NÃO recalcula)
```

> O firewall: a seta NUNCA passa por `report/report.py`. `report/setup.py` importa `from ..core import indicators` (para os tipos/dataclasses) e consome o `SinaisTecnicos` que o caller (Fase 16) já obteve via `indicators.calcular()`. [VERIFIED: report.py:16 importa indicators — direção do firewall confirmada]

### Recommended Project Structure
```
src/analista/
├── core/
│   └── indicators.py     # contrato SinaisTecnicos (NÃO tocar nesta fase)
└── report/
    ├── report.py         # engine fundamentalista — FIREWALL, nunca importada por setup.py
    ├── presentation.py   # analog read-only existente
    └── setup.py          # NOVO: SetupSwing + scoring (consome indicators, nunca report.py)
config.yaml               # + bloco novo `score:` (irmão de `indicadores:`/`padroes:`)
tests/
└── test_setup_report.py  # NOVO: goldens do score/grade/gate/decomposição/anti-copy
```

### Pattern 1: Agregador read-only sobre rótulos já computados (o idioma `_checklist`)
**What:** Funções que LEEM strings/flags estáveis já validadas pelas famílias e as compõem; zero recálculo, zero número novo de mercado.
**When to use:** Toda a montagem do `SetupSwing`.
**Example:**
```python
# Source: src/analista/core/indicators.py L1064-1119 (_checklist — VERIFIED)
# O score segue EXATAMENTE este contrato: lê rótulos já computados, deriva o resultado.
def _checklist(tend, canais, mom, vol, padroes) -> Checklist:
    lista_padroes = padroes.lista if padroes is not None else []   # guard None
    return Checklist(sinais=[
        Sinal("rsi", mom.nivel_rsi in ("sobrecomprado", "sobrevendido"), mom.nivel_rsi),
        ...
    ])
```

### Pattern 2: Gate de R:R sob np.errstate (reusar o idioma da Fase 13)
**What:** Razão protegida contra divisão por zero/infinito; risco≤0 ou não-finito → "indisponível" → gate falha.
**When to use:** O passo 2 do `montar_setup` (gate duro D-03/D-04).
**Example:**
```python
# Source: src/analista/core/indicators.py L859-867 (_niveis_stop_rr — VERIFIED)
risco = abs(entrada_ref - stop)
retorno = abs(niveis.alvo - entrada_ref)
with np.errstate(divide="ignore", invalid="ignore"):
    razao = np.divide(retorno, risco)          # risco==0 → inf (não exceção)
if risco <= 0 or not np.isfinite(razao):
    rr_valor = None                            # → gate falha → "Sem setup"
else:
    rr_valor = float(razao)
# GATE DURO (D-03): rr_valor is None or rr_valor < cfg["score"]["rr_minimo"] → "Sem setup"
```
> `entrada_ref` = ponto médio de `niveis.entrada_zona`; `stop` = `niveis.stop`; `alvo` = `niveis.alvo`. Todos podem ser `None` (lateral/indisponível) → gate falha graciosamente.

### Pattern 3: Config-driven com bloco irmão (anti-rebaseline)
**What:** Novo bloco `score:` no `config.yaml`, sem tocar uma linha de `indicadores:`/`padroes:` — exatamente como a Fase 14 adicionou `padroes:`.
**Example (sugestão de bloco — valores ASSUMED, calibráveis):**
```yaml
# --- v1.4 Fase 15: score de confluência técnica (SCORE-01) ---
# Bloco NOVO, irmão de `indicadores:`/`padroes:`. Nenhuma linha existente é tocada.
score:
  pesos:                    # somam 100 (D-01: tendência domina)
    tendencia: 35
    risco_retorno: 20
    padroes: 20
    momentum: 15
    volume: 10
  rr_minimo: 1.5            # GATE DURO (D-04): rr < isto → "Sem setup". Calibrável.
  penalidade_conflito_mtf: 0.20   # conflito semanal×diário multiplica o score por (1−0.20) (D-07)
  cortes_grade:            # sobre o score 0-100 (D-05). Calibráveis.
    forte: 70
    moderado: 50
    fraco: 25              # abaixo de `fraco` (e com gate ok) → ainda "Sem setup" (floor)
```

### Anti-Patterns to Avoid
- **Importar `report.py` em `setup.py`:** quebra o firewall (Critério 1). `setup.py` só importa `from ..core import indicators`.
- **Recalcular qualquer indicador/nível:** o score só LÊ `SinaisTecnicos`. Recalcular RSI/ADX/pivô é violação do contrato (e dessincroniza dos goldens).
- **Parsear `niveis.risco_retorno` (string BR "1 : 2,5") para o gate:** frágil (locale + "indisponivel"). Recomputar de `entrada_zona`/`stop`/`alvo`.
- **Levantar exceção quando um sub-objeto é `None`:** todos têm default `None` (aditivos). Acesso sem guard → `AttributeError` na UI. Degradar para "Sem setup".
- **Hardcode de pesos/cortes na montagem:** tudo no `config.yaml` (Critério 3).
- **Copy imperativa em `grade`/labels:** "Forte" descreve confluência, não ordem. Nada de "compre/entre/venda" (gate de copy, D-06).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detectar tendência/Dow | Reimplementar HH/HL | `contexto.dow_diario` | Já golden-testado (Fase 13) [VERIFIED: indicators.py:_dow] |
| Calcular R:R | Recalcular risco/retorno do zero | Campos `niveis.entrada_zona/stop/alvo` + idioma `np.errstate` da Fase 13 | Os níveis já estão ancorados em pivôs confirmados |
| Detectar padrões | Reimplementar duplo topo/OCO | `padroes.lista[PadraoGrafico]` (tipo+estado) | Já no-repaint, calibrado multi-ticker (Fase 14) |
| Carregar config | Novo loader | Receber `cfg: dict` já carregado (idioma `_cfg_ind`) | Toda a engine recebe `cfg` por parâmetro [VERIFIED: calcular(ohlc, cfg)] |
| Detectar conflito multi-TF | Recalcular semanal | `contexto.alinhamento_mtf == "conflito"` | Já derivado por resample W-FRI (Fase 13) |

**Key insight:** A Fase 15 é 100% composição. Qualquer linha que faça aritmética de série temporal (rolling, ewm, diff) é sinal de que algo está sendo recalculado errado — o score só pondera rótulos discretos e ~4 floats de nível.

## Runtime State Inventory

> Greenfield em estado: a fase só CRIA `report/setup.py` + bloco de config + teste. Não renomeia nem migra nada. Seção incluída por completude.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — verificado: nenhum datastore guarda score; é calculado on-the-fly por request | Nenhuma |
| Live service config | None — sem serviço externo; é módulo Python puro | Nenhuma |
| OS-registered state | None | Nenhuma |
| Secrets/env vars | None — sem segredos; só lê `config.yaml` versionado | Nenhuma |
| Build artifacts | `report/setup.py` é módulo novo no pacote `analista.report`; `pyproject` usa `packages.find` em `src/` → auto-incluído, sem reinstalar | Nenhuma (sem novo subpacote) |

## Mapeamento insumo→score (campos CONCRETOS do contrato)

> Esta é a tradução exata de cada família para pontuação. Todos os campos abaixo foram VERIFICADOS lendo `src/analista/core/indicators.py`. Sub-score de cada família ∈ [0,1]; valores de mapeamento são ASSUMED/calibráveis.

### Tendência (peso 35%)
Campos: `contexto.dow_diario` ("alta"|"baixa"|"lateral"|"indisponivel"), `forca.forca_adx` ("forte"|"neutro"|"sem_tendencia"|"indisponivel"), `tendencia.posicao_mm200` ("acima"|"abaixo"|"indisponivel"), `tendencia.cruzamento` ("golden_cross"|"death_cross"|"nenhum").
Sugestão de mapa: tendência direcional (`alta`/`baixa`) define a "direção do setup"; sub-score = base por dow direcional + bônus se `forca_adx=="forte"` + bônus se `posicao_mm200` coerente com a direção. `lateral`/`indisponivel` → sub-score baixo (geralmente já cai no gate via R:R indisponível).

### R:R (peso 20%) — e GATE DURO
Campos brutos: `niveis.entrada_zona` (low,high), `niveis.stop`, `niveis.alvo` → recomputar `razao = retorno/risco` sob `np.errstate`. (Alternativa: `niveis.risco_retorno` string já formatado.)
- **Gate (D-03/D-04):** `razao is None` ou `razao < rr_minimo (≈1.5)` → **zera o setup inteiro → "Sem setup"**, independente das outras famílias.
- **Sub-score (quando passa o gate):** normalizar a razão acima do mínimo, ex. clamp `(razao − rr_minimo)/(rr_alvo − rr_minimo)` em [0,1] com `rr_alvo` ~3.0 (config). Ou degraus.

### Padrões (peso 20%)
Campo: `padroes.lista[PadraoGrafico]` — cada um com `.tipo` ("duplo_topo"|"duplo_fundo"|"oco"|"oco_invertido") e `.estado` ("em_formacao"|"confirmado").
Sugestão: padrão **confirmado** coerente com a direção do setup → sub-score alto; **em_formacao** → parcial; lista vazia → 0. Coerência de direção: duplo_fundo/oco_invertido são de alta; duplo_topo/oco de baixa (derivável de `.alvo` vs `.neckline`, ou de tabela fixa por `.tipo`).

### Momentum (peso 15%)
Campos: `momentum.nivel_rsi` ("sobrecomprado"|"sobrevendido"|"neutro"), `momentum.cruzamento_macd` ("cruz_alta"|"cruz_baixa"|"nenhum"). (Atalho: os `Sinal` "rsi"/"macd" do `checklist.sinais` já booleanizam isso.)
Sugestão: MACD `cruz_alta` (em setup de alta) + RSI não-esticado → sub-score alto. **Cuidado:** RSI "sobrecomprado" NÃO é necessariamente bom num setup de alta — modelar como confirmação/divergência conforme a direção, não só "ativo".

### Volume (peso 10%)
Campo: `volume.rompimento_com_volume` (bool — rompimento Donchian sup COM volume>MM na barra fechada). Há também `volume.volume_acima_mm` (bool, agnóstico de direção).
Sugestão: `rompimento_com_volume==True` → sub-score 1.0; senão usar `volume_acima_mm` como meio-termo; ambos False → 0.

## Common Pitfalls

### Pitfall 1: R:R só existe como string localizado
**What goes wrong:** Tentar usar `niveis.risco_retorno` ("1 : 2,5" / "indisponivel") direto no gate numérico.
**Why it happens:** O contrato formata o R:R para exibição (vírgula BR) — não expõe o float. [VERIFIED: indicators.py:867]
**How to avoid:** Recomputar a razão de `entrada_zona`/`stop`/`alvo` sob `np.errstate` (Pattern 2). Reaproveita o cálculo bruto, evita parsing locale-frágil.
**Warning signs:** `float("2,5")` quebra; `"indisponivel"` não parseia.

### Pitfall 2: Sub-objetos None viram AttributeError
**What goes wrong:** `sinais.contexto.dow_diario` quando `contexto is None` → crash na UI.
**Why it happens:** Todos os sub-objetos de `SinaisTecnicos` têm default `None` (aditivos, retrocompat). [VERIFIED: indicators.py:180-198]
**How to avoid:** Guard no topo de `montar_setup`: se `sinais is None` ou qualquer insumo essencial é `None`/incompleto → `SetupSwing` neutro "Sem setup". Degradação graciosa é Critério 1.
**Warning signs:** Frame curto/lateral/sem volume produz Nones em cascata.

### Pitfall 3: "Sem setup" tem DUAS origens — não confundir
**What goes wrong:** Tratar score baixo e gate-de-R:R como a mesma coisa, ou deixar score alto "passar" com R:R ruim.
**Why it happens:** D-05 diz que "Sem setup é TAMBÉM o resultado do gate". São dois caminhos: (a) gate de R:R falha → "Sem setup" mesmo com score bruto alto; (b) score abaixo do floor `fraco` → "Sem setup".
**How to avoid:** Aplicar o gate ANTES de classificar a grade. Expor `gate_rr_ok` e `rr_valor` no dataclass para a UI mostrar o *porquê* ("Sem setup" por R:R vs por baixa confluência).
**Warning signs:** Um setup com 3 sinais lindos mas R:R 1.1 aparecendo como "Forte".

### Pitfall 4: Rebaseline acidental dos 271 goldens
**What goes wrong:** Editar `indicators.py`/`config.yaml` blocos existentes e flutuar os goldens de Fases 12–14.
**Why it happens:** Tentar "ajustar" um rótulo na fonte em vez de mapeá-lo no score.
**How to avoid:** `setup.py` é 100% novo; `config.yaml` ganha só o bloco `score:`. Não tocar `indicadores:`/`padroes:`. Rodar `.venv/bin/python -m pytest -q` antes/depois.
**Warning signs:** Diff em `indicators.py` ou em chaves antigas do config.

### Pitfall 5: RSI/MACD tratados como "quanto mais ativo melhor"
**What goes wrong:** Somar "RSI sobrecomprado" como pontos positivos num setup de alta — é potencialmente exaustão, não confirmação.
**Why it happens:** O checklist é direção-agnóstico (liga/desliga); o score precisa de semântica direcional.
**How to avoid:** No mapa de momentum, condicionar o sinal à direção do setup (dow). Documentar a escolha; é decisão de método (Murphy: momentum confirma a favor da tendência).

## Code Examples

### Esqueleto sugerido de `report/setup.py` (assinatura + dataclass)
```python
# report/setup.py  (NOVO) — read-only, NUNCA importa report.py
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from ..core import indicators  # só para tipos; consome SinaisTecnicos já calculado

@dataclass
class ContribFamilia:
    familia: str          # "tendencia"|"risco_retorno"|"padroes"|"momentum"|"volume"
    sub_score: float      # ∈ [0,1] — a leitura crua da família
    peso: int             # do config (35/20/20/15/10)
    contribuicao: float   # sub_score * peso  → pontos no total (decomposição peso-a-peso, D-02)
    detalhe: str          # rótulo neutro de origem ("alta+forte", "duplo_fundo:confirmado", ...)

@dataclass
class SetupSwing:
    score: float                              # 0-100, já com penalização multi-TF
    grade: str                                # "Forte"|"Moderado"|"Fraco"|"Sem setup"
    decomposicao: list = field(default_factory=list)   # [ContribFamilia, ...]
    gate_rr_ok: bool = False
    rr_valor: float | None = None
    conflito_mtf: bool = False                # penalização aplicada (D-07)
    # Níveis de ESTUDO (referência, jamais ordem) — só repassa o que Niveis já tem
    entrada_zona: tuple | None = None
    stop: float | None = None
    alvo: float | None = None

def montar_setup(sinais: "indicators.SinaisTecnicos", cfg: dict) -> SetupSwing:
    """Read-only: lê SinaisTecnicos, devolve SetupSwing. Degrada para 'Sem setup', nunca levanta."""
    sc = cfg["score"]
    # 1. guard de borda → "Sem setup" neutro
    if sinais is None or sinais.niveis is None or sinais.contexto is None:
        return SetupSwing(score=0.0, grade="Sem setup")
    # 2. R:R recomputado + gate duro (Pattern 2) ...
    # 3-5. sub-scores, soma ponderada, penalização multi-TF ...
    # 6. grade por cortes do config ...
    return SetupSwing(...)
```

### Carregar o bloco `score:` (idioma já usado nos testes/CLI)
```python
# Source: tests/test_indicators.py L17-21 + cli.py:32 (VERIFIED) — o cfg é dict de yaml.safe_load
import yaml
with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
pesos = cfg["score"]["pesos"]   # {"tendencia": 35, ...}
```

## Estratégia de Goldens (`test_setup_report.py`)

O repo já tem o idioma exato para isso: **stubs duck-typed** que constroem só os rótulos que o consumidor lê, sem rodar `calcular()`. Ver `_familias_stub` (test_indicators.py L1465-1477) e `test_checklist_sem_copy_natural` (L1567).

**Plano recomendado:**
1. **Helper `_sinais_stub(...)`** com `SimpleNamespace`/dataclasses reais montando `contexto`, `niveis`, `forca`, `padroes`, `momentum`, `volume` controlados. Cada teste fixa exatamente as famílias para produzir a grade alvo.
2. **Um teste por grade:** `test_setup_forte`, `test_setup_moderado`, `test_setup_fraco`, `test_setup_sem_setup_por_score_baixo`.
3. **Gate de R:R:** `test_gate_rr_zera_setup` — famílias todas excelentes MAS `rr=1.1` → grade "Sem setup", `gate_rr_ok=False`. E `test_rr_indisponivel_sem_setup` (níveis None/lateral).
4. **Decomposição peso-a-peso:** `test_decomposicao_soma_score` — Σ `contribuicao` == `score` (antes da penalização) e cada `ContribFamilia.peso` bate o config.
5. **Penalização multi-TF:** `test_conflito_mtf_penaliza_sem_bloquear` — mesmo cenário com `alinhamento_mtf="conflito"` produz score == base×(1−penalidade) e `conflito_mtf=True`, grade não vira "Sem setup" só por isso (D-07).
6. **Degradação graciosa:** `test_setup_degrada_sem_excecao` — `montar_setup(None, cfg)` e sinais com sub-objetos None → "Sem setup", sem levantar.
7. **Anti-copy (replicar D-06):** `test_setup_sem_copy_imperativa` — copiar o padrão de `test_checklist_sem_copy_natural`: varrer `grade` + `decomposicao[].detalhe` + qualquer string do dataclass contra `("compre","venda","comprar","vender","entre","recomend","sugiro","indico")` com `re.search(rf"\b{termo}")`.
8. **Config-driven:** carregar via `_cfg_ind()` (mesmo helper) para pinar pesos/cortes; um teste que muda um peso e vê o score mudar prova que não há hardcode.
9. **End-to-end (1-2 testes):** rodar `indicators.calcular(_frame_ohlc_longo(), cfg)` → `montar_setup(...)` para provar a integração real do contrato (sem cravar números frágeis — asserir tipo/grade ∈ conjunto válido).

**Por que não flutua os 271:** `setup.py` e `test_setup_report.py` são novos; nenhuma fonte ou config existente é tocada. Comando de regressão: `.venv/bin/python -m pytest -q` (271 verdes antes e depois). [VERIFIED: 271 test functions coletados; test_indicators.py coleta 86]

## State of the Art

Não aplicável — sem bibliotecas externas/versões em jogo. O "estado da arte" relevante é o **contrato interno** das Fases 13–14, que está atual e golden-testado (concluídas 2026-06-29).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Escala do score = **0–100** (sub-scores ∈ [0,1] × peso × 100) | Score normalization | Baixo — discrição declarada (CONTEXT D-02); só muda apresentação |
| A2 | Cortes de grade Forte≥70 / Moderado≥50 / Fraco≥25 | Bloco `score:` | Médio — calibração; afeta distribuição das grades. Calibrável no config |
| A3 | `rr_minimo` = 1.5 (gate) e `rr_alvo` ~3.0 (normalização) | Gate R:R | Médio — gate mais/menos rígido; CONTEXT D-04 já diz "≈1.5 calibrável" |
| A4 | `penalidade_conflito_mtf` = 0.20 (multiplica score por 0.80) | Multi-TF | Médio — magnitude da penalização; CONTEXT D-07 deixa ao research |
| A5 | "Sem setup" tem floor de score (`<fraco`) ALÉM do gate de R:R | Grade | Médio — interpretação de D-05 ("também"). Confirmar com usuário se floor existe |
| A6 | Recomputar R:R dos campos brutos > parsear o string `risco_retorno` | Stack/Pitfall 1 | Baixo — ambos corretos; recompute é mais robusto |
| A7 | Manter scoring em `report/setup.py` (sem criar `core/setups.py`) | Architecture | Baixo — discrição; firewall e testabilidade preservados de qualquer forma |
| A8 | Coerência direcional de momentum (RSI sobrecomprado ≠ bônus automático em setup de alta) | Pitfall 5 / Momentum | Médio — decisão de método; documentar e validar no copy review |
| A9 | Direção de cada padrão derivável de `.tipo` (duplo_fundo/oco_invertido=alta) | Padrões mapping | Baixo — geometria fixa do detector da Fase 14 |

> Todos os valores numéricos (A1–A5) são **config-driven e calibráveis** — entram no `config.yaml`, não no código. A discuss-phase já travou as decisões estruturais (D-01..D-07); estes são os *valores iniciais sensatos* que o research ancora.

## Open Questions (RESOLVED)

> Resolvidas no planejamento da Fase 15 (plano 15-01). Cada recomendação abaixo foi adotada com valor concreto no PLAN.

1. **RESOLVED — floor configurável `cortes_grade.fraco`.** "Sem setup" tem floor de score além do gate de R:R? (A5)
   - What we know: D-05 diz "'Sem setup' é TAMBÉM o resultado do gate de R:R" — "também" sugere uma 2ª origem (score muito baixo).
   - What's unclear: se um setup com R:R válido mas confluência mínima deve ser "Fraco" ou "Sem setup".
   - Recommendation: implementar floor configurável (`cortes_grade.fraco`); abaixo dele → "Sem setup". Expor `gate_rr_ok`+`rr_valor` para a UI distinguir as duas origens. Confirmar no plan/discuss.

2. **RESOLVED — NÃO no MVP (volume já pesa 10%).** Gate de liquidez (volume mínimo) entra no MVP? (CONTEXT discrição)
   - What we know: a família Volume já tem peso 10%; o screening fundamentalista usa `volume_min_diario` R$15M, mas é outro contexto.
   - What's unclear: se vale um gate duro de liquidez no swing.
   - Recommendation: **NÃO no MVP** — o peso de volume já penaliza; um gate duro de liquidez sobre intraday best-effort arrisca over-bloquear. Deixar como deferido/backlog.

3. **RESOLVED — padrão incoerente pontua ~0 (não negativo); refinamento pós-MVP.** Direção do setup quando dow="alta" mas padrão confirmado é de baixa (duplo_topo)?
   - What we know: famílias podem discordar (tendência alta + padrão de reversão de baixa).
   - What's unclear: o score deve somar a "força" do padrão (que aponta contra) ou tratar como conflito interno.
   - Recommendation: o padrão coerente com a direção do dow pontua; o incoerente pontua ~0 (não negativo, para não criar score negativo). Documentar; é refinamento, não bloqueio do MVP.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | engine | ✓ | 3.14.5 (.venv) | — |
| numpy/pandas/scipy/pyyaml | scoring + testes | ✓ | instalados no `.venv` | — |
| pytest | goldens | ✓ | coleta 271 testes OK | — |

**Missing dependencies:** Nenhuma. Constraint "zero novas deps" satisfeita por construção. [VERIFIED: .venv/bin/python import OK; pytest collect OK]

## Security Domain

> Módulo Python read-only local (Streamlit single-user). Superfície de ataque mínima nesta fase.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | parcial | Único "input" é o `cfg` (config versionado) e o `SinaisTecnicos` interno; validação só na borda de ingest (já feita Fases 12–13). `setup.py` valida None/forma e degrada |
| V6 Cryptography | não | Sem cripto |
| V2/V3/V4 Auth/Sessão/Acesso | não | Sem auth nesta fase (v2.0) |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Divisão por zero / inf propagado à UI | Denial of Service (crash) | `np.errstate` + `np.isfinite` (idioma Fase 13) → "indisponível" |
| Exceção não-tratada quebra a aba Streamlit | DoS | Guards de None + retorno neutro "Sem setup" (Critério 1) |
| Copy que vira recomendação financeira | (risco regulatório, não STRIDE) | Firewall de copy + teste anti-imperativo (D-06) |

## Sources

### Primary (HIGH confidence)
- `src/analista/core/indicators.py` — contrato `SinaisTecnicos` completo (dataclasses L33-198; `_checklist` L1064; `_niveis_stop_rr` R:R L812-867; `_contexto`/alinhamento_mtf L1171-1219; `calcular` L1222) [VERIFIED: leitura integral]
- `src/analista/report/report.py` — confirma direção do firewall (importa `indicators`, L16) [VERIFIED]
- `src/analista/report/presentation.py` — analog read-only de apresentação [VERIFIED]
- `config.yaml` — blocos `indicadores:`/`padroes:` como molde [VERIFIED]
- `tests/test_indicators.py` — `_cfg_ind` (L17), `_familias_stub` (L1465), `test_checklist_sem_copy_natural` (L1567) [VERIFIED]
- `.planning/phases/13-*/13-02-SUMMARY.md` — conflito multi-TF é rótulo aditivo que modula, nunca bloqueia (D-06) [VERIFIED]
- `.planning/REQUIREMENTS.md` §SCORE-01; `.planning/ROADMAP.md` §Phase 15 [VERIFIED]
- `.planning/config.json` — `nyquist_validation: false` → seção Validation Architecture omitida [VERIFIED]

### Secondary / Tertiary
- N/A — pesquisa 100% interna ao repo; nenhuma fonte externa necessária (zero deps novas).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero deps novas, tudo verificado no `.venv`/`pyproject`
- Architecture (firewall, módulo único, contrato): HIGH — lido direto do código; ambiguidade `setups.*` resolvida (módulo não existe)
- Mapeamento insumo→score (campos concretos): HIGH para os campos existentes; MEDIUM para o *mapeamento* exato (decisão de método)
- Valores numéricos do score (pesos já travados; cortes/rr_min/penalidade): MEDIUM/ASSUMED — config-driven, calibração deferida (A1–A5)
- Estratégia de goldens: HIGH — idioma de fixtures já existe no repo

**Research date:** 2026-06-29
**Valid until:** ~30 dias (contrato interno estável; só muda se Fases 13/14 forem alteradas)

## RESEARCH COMPLETE

**Phase:** 15 - Montagem do Setup (SetupSwing) + Score
**Confidence:** HIGH (estrutura) / MEDIUM (valores numéricos calibráveis, config-driven)

### Key Findings
- **Ambiguidade `setups.*` resolvida:** `core/setups.py` NÃO existe — Fases 13/14 colocaram tudo em `indicators.py`. A Fase 15 cria **apenas `report/setup.py`** (dataclass + scoring). Criar `core/setups.py` é opcional (discrição); recomendo manter em `report/setup.py`, espelhando `_checklist`.
- **Firewall trivial:** `report.py` importa `indicators` (não o contrário). `setup.py` importará `indicators` direto e nunca `report.py`. Nada em `report.py` é necessário.
- **Mapeamento insumo→score documentado campo-a-campo:** tendência←`contexto.dow_diario`+`forca.forca_adx`; R:R←`niveis.entrada_zona/stop/alvo` (recomputar, não parsear o string); padrões←`padroes.lista[].tipo/estado`; momentum←`momentum.nivel_rsi/cruzamento_macd`; volume←`volume.rompimento_com_volume`.
- **Gate vs penalização:** R:R recomputado sob `np.errstate` → gate duro (zera→"Sem setup"); `alinhamento_mtf=="conflito"` → multiplica score por (1−penalidade), nunca bloqueia. "Sem setup" tem 2 origens (gate de R:R e floor de score) — expor `gate_rr_ok`/`rr_valor`.
- **Goldens sem flutuar os 271:** módulo+teste novos, só bloco `score:` no config; idioma de stubs duck-typed (`_familias_stub`) e anti-copy (`test_checklist_sem_copy_natural`) já existem para replicar.

### File Created
`.planning/phases/15-montagem-do-setup-setupswing-score/15-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | Zero deps novas; verificado no .venv |
| Architecture | HIGH | Lido do código; firewall e módulo resolvidos |
| Mapeamento de campos | HIGH | Campos concretos verificados em indicators.py |
| Valores do score | MEDIUM | Pesos travados (D-01); cortes/rr_min/penalidade ASSUMED, config-driven |
| Estratégia de goldens | HIGH | Idioma de fixtures já existe no repo |

### Open Questions
1. "Sem setup" tem floor de score além do gate de R:R? (interpretação de D-05 "também") — recomendo floor configurável.
2. Gate de liquidez no MVP? — recomendo NÃO (volume já tem peso 10%).
3. Padrão confirmado incoerente com o dow — pontua ~0 (não negativo); refinamento pós-MVP.

### Ready for Planning
Research completo. O planner pode criar os PLAN.md (sugestão: 1 plano de contrato+config+scoring core, 1 plano de goldens+anti-copy, possivelmente fundidos dado o tamanho).
