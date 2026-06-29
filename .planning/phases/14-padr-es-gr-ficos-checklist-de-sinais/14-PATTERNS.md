# Phase 14: Padrões Gráficos + Checklist de Sinais - Pattern Map

**Mapped:** 2026-06-29
**Files analyzed:** 3 (1 core module MODIFY, 1 config MODIFY, 1 test ADD) — com Open Question 1 abrindo a opção de extrair um 4º arquivo (`core/padroes.py`)
**Analogs found:** 3 / 3 (todos os arquivos têm analog direto no próprio repo — a Fase 13 é o molde)

> Não existe `14-CONTEXT.md`. A lista de arquivos foi extraída de `14-RESEARCH.md`
> (§Recommended Project Structure linhas 144–151, §Architecture Patterns, §Code Examples).
> A fase é **100% aditiva sobre `core/indicators.py`** — nenhum contrato existente muda.

## File Classification

| New/Modified File | Op | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|----|----|-----------|----------------|---------------|
| `src/analista/core/indicators.py` | MODIFY | service + model (engine pura + dataclasses) | transform (geometria determinística sobre séries) | `_niveis_sr`/`_niveis_fib`/`_dow`/`_volume` + dataclasses `Niveis`/`Pivos`/`Volume` no mesmo arquivo | exact |
| `src/analista/core/padroes.py` *(opcional, Open Q1)* | ADD | service | transform | mesmas funções `_niveis_*` extraídas; importado por `calcular` | role-match (se o planner optar por extrair) |
| `config.yaml` (bloco `padroes:`) | MODIFY | config | config-load | bloco `indicadores:` (linhas 96–118) | exact |
| `tests/test_indicators.py` | ADD | test | golden/fixture | harness existente (`_cfg_ind`/`_frame_*`/`_pivos_*` + gate de truncação) | exact |

**Sub-itens dentro de `indicators.py` (todos aditivos):**

| Adição | Role | Data Flow | Analog direto |
|--------|------|-----------|---------------|
| dataclasses `PadraoGrafico` / `Padroes` | model | — | `Niveis` (95–115) / `Pivos` (86–93) — campos aditivos com default |
| dataclasses `Sinal` / `Checklist` | model | — | `ContextoTendencia` (126–131) — strings estáveis/neutras |
| campo `volume_acima_mm: bool` em `Volume` | model | — | `Volume` (118–123) — campo aditivo direcional (Open Q2) |
| função `_padroes(pivos, nominal, volume, cfg)` | service | transform | `_niveis_sr` (634–688) / `_dow` (545–592) |
| função `_checklist(tend, canais, mom, vol, padroes)` | service | aggregate (read-only) | idioma de rótulos discretos de `Momentum`/`Canais` — pura leitura/composição |
| campos `padroes=None` / `checklist=None` em `SinaisTecnicos` | model | — | `pivos`/`niveis`/`volume` aditivos (143–154) |
| wiring em `calcular(...)` | service | transform | `calcular` (921–972) — bloco de famílias de PREÇO sobre `nominal` |

## Pattern Assignments

### `src/analista/core/indicators.py` — dataclasses aditivas (model)

**Analog:** `Niveis` (linhas 95–115), `Pivos` (86–93), `Volume` (118–123), `ContextoTendencia` (126–131)

**Padrão de dataclass aditivo com auditabilidade** (`Niveis`, 105–115) — espelhar `pivos_ancora` para os pivôs-âncora do padrão:
```python
@dataclass
class Niveis:
    suportes: list = field(default_factory=list)
    ...
    pivos_ancora: dict = None   # {fundo_ts,fundo_preco,topo_ts,topo_preco} p/ auditabilidade
    stop: Number = None
    risco_retorno: str = "indisponivel"
```
Para a Fase 14 (RESEARCH §Code Examples 334–349):
```python
@dataclass
class PadraoGrafico:
    tipo: str        # "duplo_topo"|"duplo_fundo"|"oco"|"oco_invertido"  (chave estável, D-01)
    estado: str      # "em_formacao"|"confirmado"
    neckline: float
    alvo: float
    altura: float
    pivos_envolvidos: dict   # {ts: preco} — espelha Niveis.pivos_ancora

@dataclass
class Padroes:
    lista: list = field(default_factory=list)   # [] = nenhum (degradação graciosa)
```

**Padrão de campos discretos neutros** (`Momentum` 82–83, `ContextoTendencia` 130–131) — para `Sinal`/`Checklist`, manter strings estáveis (NUNCA copy natural):
```python
nivel_rsi: str   # "sobrecomprado" | "sobrevendido" | "neutro" | "indisponivel"
```

**Campo aditivo em `Volume`** (118–123) — adicionar `volume_acima_mm: bool = False` SEM tocar os existentes (Open Q2 — flag bidirecional p/ confirmar rompimento de BAIXA):
```python
@dataclass
class Volume:
    volume_mm: pd.Series = None
    rompimento_com_volume: bool = False
    # NOVO (aditivo): volume_acima_mm: bool = False   # barra fechada > MM, agnóstico de direção
```

**Campos aditivos em `SinaisTecnicos`** (143–154) — copiar EXATAMENTE o idioma de `pivos`/`niveis`/`volume`:
```python
    pivos: "Pivos" = None
    contexto: "ContextoTendencia" = None
    niveis: "Niveis" = None
    volume: "Volume" = None
    # NOVO: padroes: "Padroes" = None ; checklist: "Checklist" = None
```

---

### `src/analista/core/indicators.py` — `_padroes(...)` (service, transform)

**Analog:** `_niveis_sr` (634–688), `_dow` (545–592), `_niveis_fib` (699–765)

**Consumir pivôs já confirmados via `.dropna()`** (idioma de `_dow` 559–560, `_niveis_fib` 726–727):
```python
topos = pivos.pivot_high.dropna()    # já só barras de pivô CONFIRMADO
fundos = pivos.pivot_low.dropna()
```

**Comparar os dois/últimos pivôs por posição** (`_dow` 564–568) — molde direto p/ duplo topo:
```python
if len(topos) >= 2 and len(fundos) >= 2:
    hh = topos.iloc[-1] > topos.iloc[-2]
    ...
```

**Ler limiar do config e degradar graciosamente** (`_niveis_sr` 655–688) — `cfg["padroes"][...]`, retornar `Padroes(lista=[])` quando nada casa, NUNCA levantar:
```python
ind = cfg["indicadores"]
k = ind["cluster_k"]
...
if pivos is not None and len(atr_validos) and len(close) >= 2:
    ...
return Niveis(suportes=suportes, resistencias=resistencias, ...)
```

**Barra FECHADA `iloc[-2]` para confirmar rompimento** (`_volume` 851–861, `_niveis_sr` 673) — a confirmação do padrão lê SEMPRE a barra fechada, NUNCA `iloc[-1]`:
```python
ref = float(close.iloc[-2])          # barra FECHADA (D-04)
...
dsup_f = donchian_sup.iloc[-2]       # canal causal na barra fechada
vol_f = vol.iloc[-2]
close_f = ohlc["Close"].iloc[-2]
if not (pd.isna(dsup_f) or pd.isna(vmm_f) or pd.isna(vol_f)):
    flag = bool(close_f > dsup_f and vol_f > vmm_f)
```
→ Para `_padroes`: `confirmado = (close_f além da neckline) and volume.<flag>`; senão `"em_formacao"`.

**Proteger razões com `np.errstate`** (`_niveis_stop_rr` 817–820, `_canais` 294–295) — simetria/altura/measured-move com neckline próxima de zero:
```python
with np.errstate(divide="ignore", invalid="ignore"):
    razao = np.divide(retorno, risco)
if risco <= 0 or not np.isfinite(razao):
    ...
```

**Mutação in-place de dataclass** (`_niveis_fib`/`_niveis_stop_rr` mutam `niveis`) — opção de padrão se o planner preferir popular um objeto recebido, OU retornar novo (como `_niveis_sr`). Recomendação: `_padroes` RETORNA `Padroes`, espelhando `_niveis_sr`/`_volume`.

> **Neckline inclinada da OCO (Pitfall 3):** usar **posição inteira da barra** (índice 0..n-1) como eixo-x da reta, NUNCA o timestamp em ns. Não há analog exato — é a parte genuinamente nova; guardar os 5 pivôs em `pivos_envolvidos` para auditabilidade (espelha `pivos_ancora`).

---

### `src/analista/core/indicators.py` — `_checklist(...)` (service, aggregate read-only)

**Analog:** sem função-analog exata (é agregação nova), mas o idioma é **ler rótulos discretos JÁ computados** das famílias (`Tendencia.cruzamento`, `Canais.rompimento_donchian`, `Momentum.nivel_rsi`/`cruzamento_macd`, `Volume.rompimento_com_volume`). Zero recálculo.

**Forma (RESEARCH §Pattern 4, 235–249):**
```python
@dataclass
class Sinal:
    nome: str        # "rompimento"|"cruzamento_mm"|"rsi"|"macd"|"padrao"|"volume"
    ativo: bool
    detalhe: str     # rótulo neutro já existente (ex.: "nova_maxima", "duplo_topo:confirmado")

def _checklist(tend, canais, mom, vol, padroes) -> "Checklist":
    return Checklist(sinais=[
        Sinal("rompimento",    canais.rompimento_donchian not in ("nenhum","indisponivel"), canais.rompimento_donchian),
        Sinal("cruzamento_mm", tend.cruzamento in ("golden_cross","death_cross"),           tend.cruzamento),
        Sinal("rsi",           mom.nivel_rsi in ("sobrecomprado","sobrevendido"),            mom.nivel_rsi),
        Sinal("macd",          mom.cruzamento_macd in ("cruz_alta","cruz_baixa"),            mom.cruzamento_macd),
        Sinal("padrao",        any(p.estado == "confirmado" for p in padroes.lista),         _resumo(padroes)),
        Sinal("volume",        bool(vol.rompimento_com_volume),                              "rompimento_com_volume"),
    ])
```
> Os booleanos derivam de **strings já validadas pelos goldens** — não introduz números novos. "ativo" = sinal disparado/relevante, NUNCA "compre/venda" (firewall de copy é da Fase 16).

---

### `src/analista/core/indicators.py` — wiring em `calcular(...)` (service)

**Analog:** `calcular` (921–972), em especial o bloco de famílias de PREÇO sobre `nominal` (940–961).

**Frame NOMINAL para a família de PREÇO** (940–959) — `_padroes` detecta sobre `nominal`, igual a `_pivos`/`_niveis_*` (D-02):
```python
pivos = _pivos(nominal, cfg)             # família de PREÇO → frame nominal
contexto = _contexto(ohlc, cfg)
niveis = _niveis_sr(pivos, nominal, forca.atr, ...)
_niveis_fib(niveis, pivos, contexto, nominal, cfg)
_niveis_stop_rr(niveis, contexto, forca.atr, nominal, cfg)
# NOVO (aditivo, mesmo padrão):
# padroes = _padroes(pivos, nominal, volume_obj, cfg)
# checklist = _checklist(tendencia, canais, momentum, volume_obj, padroes)
```
**Adicionar aos kwargs do return** (962–972) sem reordenar os existentes:
```python
return SinaisTecnicos(
    tendencia=_tendencia(close, cfg), canais=canais, forca=forca,
    momentum=_momentum(close, cfg), close=close,
    pivos=pivos, contexto=contexto, niveis=niveis, volume=_volume(ohlc, cfg),
    # NOVO: padroes=padroes, checklist=checklist,
)
```
> Nota: `_volume(ohlc, cfg)` hoje roda inline no return. Se `_padroes` precisar do objeto `Volume` (flag de confirmação), extrair `volume = _volume(ohlc, cfg)` para uma variável ANTES e reusá-la nos dois lugares — mudança puramente local, não-quebrante.

---

### `config.yaml` — bloco `padroes:` (config)

**Analog:** bloco `indicadores:` (linhas 96–118) — idioma config-driven com comentários densos explicando o "porquê" de cada limiar.

**Padrão (chave de topo nova, irmã de `indicadores:`):**
```yaml
indicadores:
  ...
  pivo_n: 2
  volume_janela: 20
```
Adicionar (RESEARCH §Code Examples 322–332, valores ASSUMED — calibração multi-ticker é parte do aceite):
```yaml
padroes:
  lookback_pivos: 8
  price_tolerance_pct: 0.03
  shoulder_symmetry_pct: 0.05
  head_min_prominence_pct: 0.02
  min_pattern_height_pct: 0.03
  exigir_volume_confirma: true
```
> **Regra anti-rebaseline (Pitfall 5):** SÓ adicionar bloco novo; NÃO tocar nenhuma linha de `indicadores:`. Os testes pinam o config via `_cfg_ind()` (carrega o `config.yaml` shipado) — qualquer mudança em default existente quebra os 252 testes.

---

### `tests/test_indicators.py` — goldens (test, golden/fixture)

**Analog:** harness completo no próprio arquivo — `_cfg_ind` (15–19), helpers de frame, fixtures de pivô manual, e os gates de no-repaint.

**Carregar config pinado** (15–19):
```python
def _cfg_ind() -> dict:
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
```

**Fixture sintética de frame OHLCV** (`_frame_ohlcv` 861–870) — reuso direto p/ construir o duplo topo (RESEARCH 364–375):
```python
def _frame_ohlcv(close, high=None, low=None, volume=None, start="2021-01-01"):
    close = np.asarray(close, dtype=float)
    high = close + 0.5 if high is None else np.asarray(high, dtype=float)
    low = close - 0.5 if low is None else np.asarray(low, dtype=float)
    volume = np.full(len(close), 1000.0) if volume is None else np.asarray(volume, dtype=float)
    idx = pd.date_range(start, periods=len(close), freq="B")
    return pd.DataFrame({"Open": close, "High": high, "Low": low, "Close": close, "Volume": volume}, index=idx)
```

**Injetar pivôs determinísticos (geometria isolada, sem depender de `_pivos`)** — `_pivos_manual` (760–776) e `_pivos_ts` (949–964) constroem um `Pivos` com preços/timestamps conhecidos:
```python
def _pivos_ts(topos: dict, fundos: dict, n_barras: int = 10) -> "indicators.Pivos":
    idx = pd.date_range("2021-01-01", periods=n_barras, freq="B")
    ph = pd.Series(np.nan, index=idx); pl = pd.Series(np.nan, index=idx)
    for i, p in topos.items(): ph.iloc[i] = p
    for i, p in fundos.items(): pl.iloc[i] = p
    ...
    return indicators.Pivos(pivot_high=ph, pivot_low=pl, ultimo_topo=..., ultimo_fundo=..., n=2)
```
→ Usar `_pivos_ts({...topos OCO...}, {...fundos...})` para testar a geometria de OCO/duplo topo sem ruído.

**GATE OBRIGATÓRIO — no-repaint por truncação** (`test_pivos_no_repaint_truncacao` 433–455) — molde EXATO do gate da fase:
```python
def test_pivos_no_repaint_truncacao():
    cfg = _cfg_ind()
    df = _frame_pivos()
    N = cfg["indicadores"]["pivo_n"]
    full = indicators._pivos(df, cfg)
    for k in (40, 60):
        pk = indicators._pivos(df.iloc[:k], cfg)
        lim = k - N - 1            # exclui a barra viva do slice
        np.testing.assert_allclose(
            pk.pivot_high.iloc[:lim].to_numpy(float),
            full.pivot_high.iloc[:lim].to_numpy(float), equal_nan=True)
```
→ Para padrões (RESEARCH 351–362): `_padroes(_pivos(df[:k]), df[:k], ..., cfg)` deve dar o MESMO estado/rótulo de cada padrão âncora em barras já fechadas que `_padroes(... df ...)`.

**GATE complementar — barra viva não altera nada** (`test_pivos_no_repaint_barra_viva` 471–493): mutar High/Low da barra viva (`iloc[-1]`) para extremo absurdo NÃO pode mudar nenhum padrão já confirmado.

**Degradação graciosa via `calcular`** (test 932 / `test_volume_frame_curto` 910–917): frame curto/sem padrão → `Padroes(lista=[])` e checklist com todos `ativo=False`, sem exceção.

## Shared Patterns

### Disciplina no-repaint (barra fechada `iloc[-2]`)
**Source:** `_volume` (851–861), `_dow` (579–587), `_niveis_sr` (673), docstring `_pivos` (485–502)
**Apply to:** `_padroes` (confirmação de rompimento da neckline), todos os goldens de padrão
```python
ref = float(close.iloc[-2])     # barra FECHADA — NUNCA iloc[-1] (viva)
```
A transição `em_formacao → confirmado` ao avançar uma barra NÃO é repaint (é nova informação numa barra nova). Rótulo de uma barra ≤ t é imutável em t+1.

### Degradação graciosa (sem exceção na UI)
**Source:** `calcular` guard (937–938), `_volume` (843–844), `_niveis_sr` (669/685–688)
**Apply to:** `_padroes` → `Padroes(lista=[])`; `_checklist` → todos `ativo=False`
```python
if "Volume" not in ohlc.columns or len(ohlc) == 0:
    return Volume()              # default seguro antes de qualquer cálculo
```

### Proteção de divisão (`np.errstate`)
**Source:** `_niveis_stop_rr` (817–823), `_canais` (294–295), `rsi_wilder` (235–240)
**Apply to:** simetria de preço, altura/measured-move, prominência da cabeça (denominadores que podem ser ~0)
```python
with np.errstate(divide="ignore", invalid="ignore"):
    razao = np.divide(retorno, risco)
if risco <= 0 or not np.isfinite(razao):
    ... = "indisponivel"
```

### Rótulos estáveis/neutros (D-01, firewall de copy)
**Source:** `Momentum` (82–83), `Canais` (54–56), `ContextoTendencia` (130–131)
**Apply to:** `PadraoGrafico.tipo`/`.estado`, `Sinal.nome`/`.detalhe`
Chaves estáveis ("duplo_topo", "confirmado", "em_formacao") — NUNCA linguagem natural, NUNCA "compre/venda". A renderização é da Fase 16.

### Config-driven + pinado nos testes
**Source:** bloco `indicadores:` (config.yaml 96–118) + `_cfg_ind()` (test 15–19)
**Apply to:** todos os limiares geométricos vão para `padroes:` no config; goldens leem via `_cfg_ind()["padroes"]`. Nada de constantes hardcoded no detector.

### Aditividade de contrato (anti-rebaseline)
**Source:** comentários de `Canais.donchian_sup_55=None` (57–60), `Niveis` (100), `Volume` (121), `SinaisTecnicos.pivos=None` (143–154)
**Apply to:** TODO campo novo entra como opcional com default; NUNCA reordena/remove campo existente. Rodar a suíte inteira (252 testes) a cada plano.

## No Analog Found

| Sub-item | Role | Data Flow | Reason / Mitigação |
|----------|------|-----------|--------------------|
| Geometria da OCO com neckline inclinada (regressão linear pelos 2 fundos) | service | transform | Não há detector multi-pivô de reta inclinada no repo (Fibonacci usa pivôs, mas neckline horizontal). É a parte genuinamente nova. **Usar posição inteira da barra como eixo-x** (Pitfall 3), guardar 5 pivôs em `pivos_envolvidos`. Sem analog → seguir RESEARCH §Pattern 2 (195–215). |
| `_checklist` (agregação read-only de rótulos) | service | aggregate | Não há função que apenas LÊ rótulos de múltiplas famílias e compõe booleanos. É composição trivial (RESEARCH §Pattern 4). Sem risco — só lê strings já golden-testadas. |

## Metadata

**Analog search scope:** `src/analista/core/indicators.py` (972 linhas, todo o contrato + detectores da Fase 13), `config.yaml` (bloco `indicadores:`), `tests/test_indicators.py` (1143 linhas, harness de goldens)
**Files scanned:** 3 (todos os analogs vivem no próprio repo — a Fase 13 é o molde 1:1)
**Pattern extraction date:** 2026-06-29
**Open Questions herdadas (RESEARCH 403–426) que o planner deve resolver no plan:**
1. Hospedar detectores em `indicators.py` (consistência/single-assembly) vs novo `core/padroes.py` (arquivo já tem 972 linhas). Ambos aditivos.
2. Flag de volume bidirecional: expor `volume_acima_mm: bool` aditivo em `Volume` (recomendado) — detector decide direção pela neckline. Não criar 2ª MM.
3. Múltiplos padrões → retornar **lista** (`Padroes.lista`); ranqueamento fica p/ Fase 15.
4. Tolerância temporal entre pivôs (`max_largura_barras`?) — avaliar na calibração; talvez `lookback_pivos` baste.
