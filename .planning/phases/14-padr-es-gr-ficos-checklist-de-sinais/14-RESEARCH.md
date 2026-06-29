# Phase 14: Padrões Gráficos + Checklist de Sinais - Research

**Researched:** 2026-06-29
**Domain:** Detecção geométrica determinística de padrões gráficos (Murphy) sobre pivôs no-repaint + agregação de checklist de sinais
**Confidence:** MEDIUM (contratos/harness do código = HIGH; limiares geométricos dos detectores = LOW-MEDIUM, é o ponto central a calibrar)

## Summary

A Fase 14 é **100% código novo aditivo sobre `core/indicators.py`**, sem novas dependências e sem
tocar a engine fundamentalista. Os insumos já existem e são no-repaint: a Fase 13 entregou
`_pivos()` (fractal de Williams causal), `Pivos.pivot_high/pivot_low` (Series com preço nas barras
de pivô confirmado, NaN nas demais), `Volume.rompimento_com_volume` (flag de rompimento+volume na
barra fechada `iloc[-2]`), zonas S/R, contexto de Dow e os campos discretos de momentum/canais. O
detector de padrões **consome pivôs já confirmados** e aplica regras geométricas; o checklist
apenas **lê rótulos já computados** e os expõe como liga/desliga. Nenhum dos dois recalcula
indicadores.

O risco real não é técnico-de-implementação — é **falso positivo por limiar frouxo** (Pitfall 11
da pesquisa do marco) e **repaint na borda** (Pitfall 1/2). A mitigação é dupla: (1) limiares
geométricos explícitos no `config.yaml` validados multi-ticker, e (2) reuso estrito da disciplina
no-repaint já travada na Fase 13 — só barras fechadas (`iloc[-2]`), pivôs já confirmados, e um
**gate de truncação** (`detect(df[:k]) == detect(df)` nas barras fechadas) obrigatório como teste.

**Primary recommendation:** Implementar detectores como funções puras em `core/indicators.py`
(ou um novo `core/padroes.py` importado por `calcular`), populando campos **aditivos** `padroes` e
`checklist` em `SinaisTecnicos` (default `None`, espelhando como `pivos`/`niveis`/`volume` foram
adicionados). Detecção sobre o **frame nominal** (família de PREÇO, D-02). Confirmação = close da
barra fechada além da neckline + flag de volume. Limiares em novo bloco `padroes:` no `config.yaml`.
Estado `"em_formacao"`/`"confirmado"`/`None`. Fixtures golden reusam os helpers `_pivos_manual`/
`_pivos_ts`/`_frame_ohlc`/`_frame_ohlcv` já existentes em `tests/test_indicators.py`.

## User Constraints (derivadas de STATE.md §Decisions, CLAUDE.md e gates do marco v1.4)

> Não existe `14-CONTEXT.md` ainda (esta pesquisa precede o discuss/plan). Estas são as decisões
> JÁ TRAVADAS do marco que constrangem a fase — o planner deve honrá-las como locked.

### Locked Decisions
- **Produto separado / read-only:** Fase 14 é só **engine**. `app.py` permanece read-only; nenhuma
  renderização/copy nesta fase (a UI é a Fase 16). Os rótulos são strings estáveis/neutras, NUNCA
  linguagem natural (mesma regra D-01 da Fase 13).
- **Zero novas dependências de runtime:** tudo sobre `numpy`/`pandas`/`scipy` já instalados.
  `requirements.txt` inalterado. NÃO usar `scipy.signal.find_peaks`/`argrelextrema` para pivôs
  (prominence repinta na borda — proibido); os pivôs já vêm prontos da Fase 13.
- **Aditividade de contrato:** todo campo novo em `SinaisTecnicos`/dataclasses entra como opcional
  com default (`None`), NUNCA reordena/remove campo existente — é o que mantém os goldens verdes.
- **No-repaint causal obrigatório:** rótulo de um padrão em `t` é imutável em `t+1` para barras
  fechadas; confirmação avaliada na barra FECHADA (`iloc[-2]`), nunca na barra viva. **Teste de
  estabilidade no-repaint (truncação) é gate da fase.**
- **Firewall:** nada nesta fase pode importar/alterar `report/report.py` nem a aba Analisar.
- **MVP honesto:** SÓ duplo topo, duplo fundo, OCO e OCO invertido. Triângulos/bandeiras/retângulos
  ficam **explicitamente FORA** do v1.4 (Future Requirements).
- **"Exibe, nunca recomenda":** o checklist mostra estado liga/desliga e o *porquê* do setup —
  jamais "compre/venda". (Gate de copy é da Fase 16, mas os rótulos desta fase já devem ser neutros.)

### Claude's Discretion
- Nomes exatos dos dataclasses/campos novos e organização interna (espelhar `Pivos`/`Niveis`).
- Módulo de hospedagem dos detectores: dentro de `indicators.py` ou novo `core/padroes.py`
  importado por `calcular` (ver Open Question 1).
- Valores iniciais dos limiares geométricos no `config.yaml` (faixas sugeridas abaixo; calibração
  multi-ticker é parte do aceite — Success Criterion 3).

### Deferred Ideas (OUT OF SCOPE)
- Triângulos, bandeiras, retângulos, cunhas (continuação) — Future Requirements.
- Neckline desenhada/trendlines automáticas na UI — Fase 16/backlog.
- Score ponderado que consome o padrão (SCORE-01) — Fase 15.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PAT-01 | Engine detecta duplo topo/fundo + OCO sobre pivôs, com rótulo "em formação" vs "confirmado" (exige rompimento + volume) e alvo measured-move; triângulos/bandeiras fora | Algoritmos geométricos abaixo (§Architecture Patterns 1–3); insumo = `Pivos` da Fase 13; confirmação = `Volume.rompimento_com_volume` + close `iloc[-2]` além da neckline; measured-move = altura projetada da neckline |
| SIG-01 | Engine expõe checklist de sinais (rompimento, cruzamento MM, RSI/MACD, padrão, volume) liga/desliga, tornando explícito *por que* o setup existe | §Architecture Pattern 4 — agregação read-only de rótulos JÁ computados em `tendencia`/`canais`/`momentum`/`volume`/`padroes`; zero recálculo |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Detecção geométrica de padrões (duplo topo/fundo, OCO) | Core engine (`core/indicators.py` ou `core/padroes.py`) | — | Matemática pura determinística sobre pivôs; precedente direto: pivôs/níveis/volume da Fase 13 vivem em `indicators.py` |
| Rótulo "em formação" vs "confirmado" + measured-move | Core engine | — | Derivação determinística de pivôs + neckline + close fechado; nada de UI |
| Confirmação por volume | Core engine (reuso `Volume`) | — | Flag `rompimento_com_volume` já existe; o detector a consome, não a recalcula |
| Checklist de sinais (agregação liga/desliga) | Core engine (campo aditivo em `SinaisTecnicos`) | `report/setup.py` (Fase 15, só LÊ) | Agrega rótulos já computados; é leitura/composição, não cálculo novo |
| Renderização do checklist/padrões anotados | UI read-only (`app.py`/`grafico.py`) | — | **Fase 16**, fora desta fase |
| Score que pondera o padrão | `report/setup.py` | — | **Fase 15**, fora desta fase |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | (já instalado) | aritmética vetorizada dos limiares geométricos | já é a base de `indicators.py` [VERIFIED: requirements.txt / código] |
| pandas | (já instalado) | Series/DataFrame de pivôs e OHLC, `.dropna()`, índice temporal | contrato `Pivos`/`SinaisTecnicos` é pandas [VERIFIED] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyyaml | (já instalado) | carregar `config.yaml` (bloco `padroes:`) | leitura de limiares — idioma `_cfg_ind()` já existe nos testes [VERIFIED] |
| pytest | (já instalado) | goldens novos | harness existente em `tests/test_indicators.py` [VERIFIED] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pivôs próprios (Fase 13) | `scipy.signal.find_peaks`/`argrelextrema` | **PROIBIDO** — prominence/janela centrada repintam na borda (Pitfall 2). Os pivôs no-repaint já existem |
| Regras geométricas | ML / template matching | Fora de escopo: custo, opacidade, contradiz "educacional/explicável" [CITED: research/FEATURES.md §6] |

**Installation:** Nenhuma. `requirements.txt` permanece inalterado (gate do marco). [VERIFIED: STATE.md §Decisions]

## Architecture Patterns

### System Architecture Diagram

```
                       frame OHLCV (nominal, D-02)
                                  │
                                  ▼
              ┌──────────  indicators.calcular(ohlc, cfg, ohlc_nominal)  ──────────┐
              │                                                                     │
   _pivos(nominal) ──► Pivos(pivot_high, pivot_low)   _volume(ohlc) ──► Volume(rompimento_com_volume)
              │                    │                                      │
              │                    ▼                                      │
              │        ┌── _padroes(pivos, nominal, volume, cfg) ──┐      │
              │        │  1. janela: últimos K pivôs confirmados    │      │
              │        │  2. casa geometria (simetria/altura/cabeça)│◄─────┘ (flag volume p/ confirmar)
              │        │  3. neckline = vale/pico intermediário     │
              │        │  4. estado: em_formacao | confirmado       │
              │        │     confirmado ⇔ close[iloc-2] além da     │
              │        │     neckline E flag volume                 │
              │        │  5. measured-move = altura ± da neckline   │
              │        └──────────────┬─────────────────────────────┘
              │                       ▼
              │                  Padroes(lista de PadraoGrafico)
              │                       │
  tendencia/canais/momentum ──────────┤
              │                       ▼
              │        _checklist(tendencia, canais, momentum, volume, padroes)
              │                       │
              │                       ▼
              │                  Checklist(sinais liga/desliga)
              └───────────────────────┬─────────────────────────────┐
                                       ▼
                       SinaisTecnicos(..., padroes=…, checklist=…)   (campos aditivos, default None)
```

### Recommended Project Structure
```
src/analista/core/
├── indicators.py    # MODIFY: novos dataclasses Padroes/PadraoGrafico/Checklist/Sinal;
│                    #         _padroes() + _checklist(); chamada em calcular(); campos aditivos
│                    #         em SinaisTecnicos  (OU extrair _padroes p/ core/padroes.py — Open Q1)
config.yaml          # MODIFY: novo bloco `padroes:` (limiares geométricos)
tests/test_indicators.py  # ADD: goldens de detecção + measured-move + no-repaint + checklist
```

### Pattern 1: Duplo Topo / Duplo Fundo sobre pivôs
**What:** Dois pivôs-topo de altura similar separados por um pivô-fundo (a neckline). Rompimento da
neckline para baixo confirma. Duplo fundo é o espelho (dois fundos + pico intermediário, rompe p/ cima).
**When to use:** ≥2 pivôs-topo confirmados (duplo topo) ou ≥2 pivôs-fundo (duplo fundo) na janela.
**Algoritmo (determinístico):**
```python
# Fonte: regras geométricas Murphy [CITED: research/FEATURES.md §6]; harness = código Fase 13.
# Insumo: pivos.pivot_high / pivos.pivot_low (já no-repaint), frame NOMINAL.
# 1. Pega os últimos `lookback_pivos` pivôs-topo confirmados (timestamp, preço).
topos = pivos.pivot_high.dropna()        # já só barras confirmadas
if len(topos) >= 2:
    t1, t2 = topos.iloc[-2], topos.iloc[-1]              # dois topos mais recentes
    ts1, ts2 = topos.index[-2], topos.index[-1]
    # 2. simetria de preço entre os dois topos
    simetria = abs(t1 - t2) / ((t1 + t2) / 2)
    # 3. vale intermediário = pivô-fundo confirmado ENTRE ts1 e ts2 → neckline (horizontal p/ duplo)
    vale = pivos.pivot_low[(pivos.pivot_low.index > ts1) & (pivos.pivot_low.index < ts2)].dropna()
    if simetria <= cfg_pad["price_tolerance_pct"] and len(vale):
        neckline = float(vale.min())                    # fundo entre os topos
        altura = (t1 + t2) / 2 - neckline               # measured-move height
        altura_pct = altura / neckline
        if altura_pct >= cfg_pad["min_pattern_height_pct"]:
            # 4. estado na barra FECHADA (iloc[-2]); confirmação = close < neckline + volume
            close_f = nominal["Close"].iloc[-2]
            rompeu = close_f < neckline
            confirmado = rompeu and volume.rompimento_com_volume  # ou flag de quebra-baixa+vol
            estado = "confirmado" if confirmado else "em_formacao"
            alvo = neckline - altura                     # projeção measured-move p/ baixo
            # PadraoGrafico("duplo_topo", estado, neckline, alvo, pivos_envolvidos=[ts1,ts2,vale.idxmin()])
```
> **Duplo fundo:** trocar `pivot_high↔pivot_low`, `min↔max`, `close > neckline`, `alvo = neckline + altura`.
> **Confirmação de volume:** `Volume.rompimento_com_volume` hoje é específico de rompimento da Donchian
> superior (alta). Para o lado de BAIXA (duplo topo / OCO), o planner precisa de uma flag análoga de
> "rompimento com volume" na quebra da neckline — ou generalizar `_volume` para expor volume>MM na barra
> fechada independente da direção (ver Open Question 2). **Não hand-roll uma segunda MM de volume.**

### Pattern 2: OCO / OCO invertido sobre pivôs (5 pivôs)
**What:** Ombro-Cabeça-Ombro = topo(LS) – fundo – TOPO maior(cabeça) – fundo – topo(RS), com cabeça
acima dos dois ombros e ombros ~simétricos. Neckline = reta pelos dois fundos (pode ser inclinada).
OCO invertido = espelho com fundos (cabeça mais baixa).
**When to use:** ≥3 pivôs-topo e ≥2 pivôs-fundo intercalados na janela (OCO); espelho p/ invertido.
**Algoritmo:**
```python
# Sequência exigida (OCO): LS(topo) < cabeça(topo) > RS(topo); dois fundos entre eles = neckline.
# 1. últimos 3 topos confirmados + 2 fundos entre eles, em ordem temporal alternada.
# 2. cabeça é o do MEIO e deve exceder ambos os ombros por >= head_min_prominence_pct.
prom_e = (cabeca - ls) / cabeca
prom_d = (cabeca - rs) / cabeca
# 3. simetria dos ombros
sim_ombros = abs(ls - rs) / ((ls + rs) / 2)
# 4. neckline por interpolação linear dos 2 fundos (f1 em ts_f1, f2 em ts_f2):
m = (f2 - f1) / (ts_f2_ord - ts_f1_ord)         # use índice posicional, NÃO timestamp cru
neckline_no_rompimento = f1 + m * (pos_barra_fechada - ts_f1_ord)   # extrapola até a barra fechada
# 5. altura = cabeça - neckline(na posição da cabeça); alvo = neckline_rompimento - altura (p/ baixo)
# 6. confirmado = close[iloc-2] < neckline_no_rompimento E volume; senão em_formacao
if prom_e >= P and prom_d >= P and sim_ombros <= S:
    ...
```
> **Neckline inclinada:** use **posição inteira da barra** (índice 0..n-1) como eixo-x, não o timestamp
> bruto (datas em ns explodem a regressão). Guarde os 5 pivôs (timestamps+preços) no dataclass para
> auditabilidade — espelha `Niveis.pivos_ancora` da Fase 13.
> **OCO invertido:** cabeça é o fundo mais BAIXO entre dois ombros-fundo; neckline pelos dois topos;
> rompe p/ CIMA; `alvo = neckline + altura`.

### Pattern 3: Estado "em formação" vs "confirmado" + measured-move
**What:** Máquina de estado de 2 estágios por padrão.
**When to use:** sempre que a geometria casar.
```
geometria casa, close ainda do lado da neckline   → "em_formacao"  (alvo já projetável, mas tentativo)
geometria casa + close[iloc-2] ALÉM da neckline + volume → "confirmado"
geometria não casa                                 → padrão ausente (não entra na lista)
```
**No-repaint:** todos os pivôs usados já são confirmados (imutáveis); a quebra é lida na barra fechada
(`iloc[-2]`), nunca na viva (`iloc[-1]`). Logo o rótulo emitido para uma barra ≤ t não muda quando chega
t+1. A transição em_formacao→confirmado ao avançar uma barra **não é repaint** (é nova informação numa
barra nova, não reescrita de uma barra passada). [CITED: research/PITFALLS.md Pitfall 1/2]

### Pattern 4: Checklist de sinais (SIG-01)
**What:** Lista read-only de sinais liga/desliga agregando rótulos JÁ computados. Zero cálculo novo.
**When to use:** sempre — popula um campo aditivo `checklist` em `SinaisTecnicos`.
```python
# Fonte: rótulos existentes de SinaisTecnicos (Fase 4–13). Apenas LÊ e compõe.
@dataclass
class Sinal:
    nome: str            # chave estável: "rompimento" | "cruzamento_mm" | "rsi" | "macd" | "padrao" | "volume"
    ativo: bool          # liga/desliga
    detalhe: str         # rótulo neutro já existente, p.ex. "nova_maxima", "cruz_alta", "duplo_topo:confirmado"

def _checklist(tend, canais, mom, vol, padroes) -> "Checklist":
    return Checklist(sinais=[
        Sinal("rompimento",   canais.rompimento_donchian not in ("nenhum","indisponivel"), canais.rompimento_donchian),
        Sinal("cruzamento_mm",tend.cruzamento in ("golden_cross","death_cross"),           tend.cruzamento),
        Sinal("rsi",          mom.nivel_rsi in ("sobrecomprado","sobrevendido"),            mom.nivel_rsi),
        Sinal("macd",         mom.cruzamento_macd in ("cruz_alta","cruz_baixa"),            mom.cruzamento_macd),
        Sinal("padrao",       any(p.estado == "confirmado" for p in padroes.lista),         _resumo(padroes)),
        Sinal("volume",       bool(vol.rompimento_com_volume),                              "rompimento_com_volume"),
    ])
```
> Estados booleanos derivam de **strings já validadas pelos goldens** — não introduz números novos.
> "ativo" significa "sinal disparado/relevante", não "compre". A semântica de *por que o setup existe*
> é a própria lista de flags ligadas.

### Anti-Patterns to Avoid
- **`find_peaks`/`argrelextrema`/`center=True` para achar topos:** lookahead/repaint — proibido. Use
  `Pivos` da Fase 13. [CITED: research/PITFALLS.md Pitfall 2]
- **Confirmar na barra viva (`iloc[-1]`):** repaint clássico — a barra reabre e o padrão "pisca".
  Sempre `iloc[-2]`.
- **Neckline via timestamp cru em ns:** overflow/escala absurda na reta. Use posição inteira da barra.
- **Calibrar o detector contra UM gráfico-exemplo:** explode em falso positivo no resto. Validar
  multi-ticker. [CITED: research/PITFALLS.md Pitfall 11]
- **Recalcular volume/MM/RSI dentro do detector:** quebra o single-source; consuma os campos prontos.
- **Copy em linguagem natural / qualquer "compre/venda":** rótulos são chaves estáveis nesta fase.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Achar topos/fundos | Detector de extremos próprio | `_pivos()` / `Pivos.pivot_high/low` (Fase 13) | Já é no-repaint, golden-testado, causal |
| Confirmação por volume | Nova MM de volume | `Volume.rompimento_com_volume` / `volume_mm` | Já calculado na barra fechada (VOL-01) |
| Barra fechada vs viva | Lógica de "última barra" ad-hoc | Invariante `iloc[-2]` já difundida em `_volume`/`_dow`/`_niveis` | Consistência + no-repaint |
| Carregar limiares | Constantes hardcoded | bloco `padroes:` no `config.yaml` via `cfg["padroes"]` | Ajuste sem deploy; goldens pinam o config (`_cfg_ind`) |
| Frame nominal vs ajustado | Reescalar preços à mão | passar o `nominal` (D-02, já roteado em `calcular`) | Pivôs/níveis/padrões são família de PREÇO |
| Degradação graciosa | try/except solto | retornar `Padroes(lista=[])` / `"indisponivel"` sem exceção | Padrão onipresente em `indicators.py` |

**Key insight:** A Fase 13 já resolveu as duas partes difíceis e perigosas (achar pivôs sem lookahead +
confirmar rompimento com volume na barra fechada). A Fase 14 é **composição geométrica** desses
primitivos — o trabalho é definir limiares conservadores e provar no-repaint, não reinventar detecção.

## Common Pitfalls

### Pitfall 1: Falso positivo por limiar frouxo (pareidolia)
**What goes wrong:** Detector dispara em quase qualquer zigue-zague; usuário vê 5 padrões e perde confiança.
**Why it happens:** Padrões gráficos são subjetivos; sem `price_tolerance_pct`/`min_pattern_height_pct`/
`shoulder_symmetry_pct` rígidos, vira gerador de pareidolia.
**How to avoid:** Limiares conservadores no `config.yaml`; exigir confirmação (rompimento+volume) p/
"confirmado"; **preferir poucos padrões de alta confiança**; validar contra ≥3 tickers variados.
**Warning signs:** Múltiplos padrões sobrepostos; detector calibrado contra 1 exemplo. [CITED: PITFALLS.md #11]

### Pitfall 2: Repaint na detecção (padrão que se reescreve)
**What goes wrong:** Padrão aparece "centrado" no último topo sem barras de confirmação à direita; o
alvo muda quando chega uma barra nova.
**Why it happens:** usar pivô não-confirmado ou ler a barra viva.
**How to avoid:** só `Pivos` confirmados; quebra na barra fechada (`iloc[-2]`); **teste de truncação
obrigatório** `detect(df[:k]).barra(t) == detect(df).barra(t)` p/ barras fechadas. [CITED: PITFALLS.md #2]
**Warning signs:** teste de no-repaint ausente; alvo que flutua ao append de barra.

### Pitfall 3: Neckline inclinada mal-formada (OCO)
**What goes wrong:** reta da neckline com coeficiente absurdo → confirmação nunca/sempre dispara.
**Why it happens:** usar timestamp em nanossegundos como eixo-x da reta.
**How to avoid:** eixo-x = posição inteira da barra; extrapolar até a barra de rompimento; guardar os
pivôs-âncora no dataclass.
**Warning signs:** alvos negativos/explosivos; OCO confirmando em série lateral.

### Pitfall 4: Confirmação de volume só p/ alta
**What goes wrong:** duplo topo/OCO (rompem p/ BAIXO) nunca confirmam porque a flag de volume só olha
rompimento da Donchian SUPERIOR.
**Why it happens:** `Volume.rompimento_com_volume` foi feito p/ VOL-01 (alta).
**How to avoid:** generalizar `_volume` p/ expor "volume da barra fechada > MM" direcional, ou um helper
de confirmação que o detector usa nos dois lados (Open Question 2). Não criar segunda MM.
**Warning signs:** padrões de topo eternamente "em_formacao".

### Pitfall 5: Rebaseline acidental dos goldens existentes
**What goes wrong:** mexer num default de `config.yaml`/campo de dataclass quebra os 252 testes atuais.
**Why it happens:** mudança não-aditiva.
**How to avoid:** SÓ adicionar bloco `padroes:` e campos `=None`; rodar a suíte inteira a cada plano.
**Warning signs:** diff que toca linhas existentes de `SinaisTecnicos`/`config.yaml indicadores:`.

## Code Examples

### Bloco `padroes:` no config.yaml (sugestão de limiares — ASSUMED, calibrar)
```yaml
# --- v1.4 Fase 14: padrões gráficos sobre pivôs (Murphy) — MVP duplo topo/fundo + OCO ---
padroes:
  lookback_pivos: 8           # nº de pivôs confirmados mais recentes varridos (janela de busca)
  price_tolerance_pct: 0.03   # simetria de PREÇO entre os 2 topos/fundos do duplo (<=3%)
  shoulder_symmetry_pct: 0.05 # simetria dos 2 ombros da OCO (<=5%)
  head_min_prominence_pct: 0.02  # cabeça deve exceder cada ombro em >=2%
  min_pattern_height_pct: 0.03   # altura mínima (measured-move) como % da neckline (>=3%) — anti-ruído
  exigir_volume_confirma: true   # confirmação requer rompimento da neckline COM volume>MM
```

### Dataclass aditivo (espelha Pivos/Niveis)
```python
# Fonte: padrão aditivo de indicators.py (Pivos linhas 86-93, Niveis 95-115).
@dataclass
class PadraoGrafico:
    tipo: str                 # "duplo_topo" | "duplo_fundo" | "oco" | "oco_invertido"
    estado: str               # "em_formacao" | "confirmado"
    neckline: float
    alvo: float               # measured-move
    altura: float
    pivos_envolvidos: dict    # {ts: preco} dos pivôs âncora — auditabilidade (como Niveis.pivos_ancora)

@dataclass
class Padroes:
    lista: list = field(default_factory=list)   # [] = nenhum padrão (degradação graciosa)
```

### Gate de no-repaint (obrigatório — espelha test_pivos_no_repaint_truncacao)
```python
# Fonte: tests/test_indicators.py linhas 433-455 (gate de truncação dos pivôs).
def test_padroes_no_repaint_truncacao():
    cfg = _cfg_ind()
    df = _frame_duplo_topo()                 # fixture sintética determinística (ver abaixo)
    full = indicators._padroes(indicators._pivos(df, cfg), df, ..., cfg)
    for k in (..., ...):                      # barras fechadas
        pk = indicators._padroes(indicators._pivos(df.iloc[:k], cfg), df.iloc[:k], ..., cfg)
        # o rótulo/estado de cada padrão âncora em barras já fechadas é idêntico
        assert _estado_em(pk, barra_fechada) == _estado_em(full, barra_fechada)
```

### Fixture sintética de duplo topo (reusa _frame_ohlc/_frame_ohlcv)
```python
# Fonte: helpers tests/test_indicators.py linhas 136-142 (_frame_ohlc), 861-871 (_frame_ohlcv c/ Volume).
def _frame_duplo_topo():
    sobe1  = np.linspace(50, 70, 12)
    desce  = np.linspace(70, 60, 8)[1:]      # vale (neckline ~60)
    sobe2  = np.linspace(60, 70, 8)[1:]      # 2º topo ~igual ao 1º (simetria)
    rompe  = np.linspace(70, 55, 8)[1:]      # quebra a neckline p/ baixo (55 < 60)
    close  = np.concatenate([sobe1, desce, sobe2, rompe])
    vol    = np.r_[np.full(len(close)-3, 1.0), np.full(3, 5.0)]  # volume alto no rompimento
    return _frame_ohlcv(close, volume=vol)    # já produz Open/High/Low/Close/Volume
```
> Para testar a GEOMETRIA isolada (sem depender de `_pivos`), reusar `_pivos_manual` (linhas 760-776) e
> `_pivos_ts` (linhas 949-961) — injetam pivôs determinísticos com preços/timestamps conhecidos.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `argrelextrema`/`find_peaks` p/ pivôs e padrões | Fractal de Williams confirmado por barras fechadas | Fase 13 | No-repaint trivial; base obrigatória da Fase 14 |
| Detecção "a olho"/template ML | Regras geométricas determinísticas config-driven | decisão do marco | Explicável, custo-zero, reproduzível |

**Deprecated/outdated:** Qualquer detector com janela centrada (`center=True`) — repinta na borda.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `price_tolerance_pct` = 3% entre topos do duplo | config.yaml sugerido | Frouxo → falso positivo; rígido → não detecta. Calibrar multi-ticker (Success Criterion 3) |
| A2 | `shoulder_symmetry_pct` = 5% e `head_min_prominence_pct` = 2% (OCO) | config.yaml | Idem A1 — OCO é o mais sensível a simetria |
| A3 | `min_pattern_height_pct` = 3% da neckline | config.yaml | Filtro anti-ruído; valor real depende da volatilidade típica B3 |
| A4 | `lookback_pivos` = 8 pivôs | config.yaml | Curto demais perde padrões longos; longo demais casa pivôs sem relação |
| A5 | Measured-move = altura projetada da neckline (sem desconto) | Patterns 1–2 | É a regra clássica de Murphy; alguns usam alvo parcial — mas projeção cheia é o padrão didático |
| A6 | Neckline do duplo topo é horizontal (min do vale) | Pattern 1 | Aceitável p/ duplo; OCO precisa de neckline inclinada (Pattern 2) |
| A7 | Confirmação exige `iloc[-2]` além da neckline + volume>MM na barra fechada | Pattern 3 | Coerente com VOL-01/D-04; precisa flag de volume bidirecional (Open Q2) |

> Todos os limiares (A1–A4) são **LOW-MEDIUM confidence** e são o ponto central a discutir/calibrar
> antes de cravar. A validação multi-ticker faz parte do aceite (Success Criterion 3).

## Open Questions

1. **Onde hospedar os detectores: `indicators.py` ou novo `core/padroes.py`?**
   - O que sabemos: Fase 13 pôs pivôs/níveis/volume DENTRO de `indicators.py`; o marco fala de
     `core/setups.py` (mas isso era a montagem do `SetupSwing`, que é da Fase 15 / `report/setup.py`).
   - O que é incerto: `indicators.py` já tem 972 linhas; um `core/padroes.py` importado por `calcular`
     pode ser mais limpo.
   - Recomendação: manter em `indicators.py` por consistência e single-assembly-point (`calcular`), OU
     extrair p/ `core/padroes.py` SE o planner preferir — ambos são aditivos. Decidir no discuss/plan.

2. **Flag de volume bidirecional para confirmar rompimentos de BAIXA (duplo topo/OCO).**
   - O que sabemos: `Volume.rompimento_com_volume` só cobre rompimento da Donchian SUPERIOR (alta).
   - O que é incerto: generalizar `_volume` (aditivo, novo campo direcional) vs. helper local de
     confirmação no detector que lê `volume_mm` + `volume` da barra fechada.
   - Recomendação: expor `volume_acima_mm: bool` (barra fechada, agnóstico de direção) aditivamente em
     `Volume`, e o detector decide direção pela neckline. Não criar segunda MM.

3. **Múltiplos padrões simultâneos: lista ou "o mais recente/relevante"?**
   - Recomendação: retornar **lista** (`Padroes.lista`), deixando o ranqueamento/seleção p/ a Fase 15
     (score) e a renderização p/ a Fase 16. Mantém a engine descritiva, não prescritiva.

4. **Tolerância temporal entre os pivôs do padrão (largura mín/máx do padrão em barras).**
   - Não há param sugerido ainda; talvez necessário p/ evitar casar topos longe demais. Avaliar se
     `lookback_pivos` já basta ou se cabe um `max_largura_barras`. Decidir na calibração multi-ticker.

## Environment Availability

SKIPPED — fase puramente de código/engine (matemática sobre OHLC em memória). Sem dependências
externas, serviços, rede ou tooling além de `numpy`/`pandas`/`scipy`/`pytest` já instalados e usados
pela Fase 13. [VERIFIED: requirements.txt inalterado é gate do marco]

## Security Domain

> `security_enforcement` ausente do `config.json` (= habilitado por default), mas esta fase é
> matemática pura sobre séries OHLC já em memória, sem nova superfície de ataque.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | sem auth nesta fase (v2.0) |
| V3 Session Management | no | — |
| V4 Access Control | no | app read-only single-user local/Streamlit |
| V5 Input Validation | parcial | OHLC vem do pipeline da Fase 12 (yfinance) já validado/saneado; o detector apenas degrada graciosamente (frame curto/None → `Padroes(lista=[])`), nunca levanta |
| V6 Cryptography | no | nenhum dado sensível/cripto |

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Frame malformado/curto/NaN | DoS (exceção na aba) | Guard de degradação graciosa (idioma `calcular` linhas 937-938); nunca exceção na UI |
| Divisão por zero em simetria/altura (neckline=0) | Tampering/erro | Proteger razões com guard/`np.errstate` (idioma já onipresente em `indicators.py`) |

> A fronteira de segurança *de produto* aqui é **regulatória, não técnica**: "exibe, nunca recomenda".
> Rótulos neutros nesta fase; o gate de copy é da Fase 16.

## Sources

### Primary (HIGH confidence)
- `src/analista/core/indicators.py` (972 linhas) — contrato `SinaisTecnicos`/`Pivos`/`Niveis`/`Volume`,
  `_pivos` (485-533), `_volume` (829-861), `calcular` (921-972), idioma `iloc[-2]`/`.shift(1)`/`np.errstate`
- `tests/test_indicators.py` (1143 linhas) — harness de goldens: `_frame_pivos`, `_frame_ohlc`,
  `_frame_ohlcv`, `_pivos_manual`, `_pivos_ts`, gate de truncação no-repaint (433-455, 471-493)
- `config.yaml` — bloco `indicadores:` (96-118): idioma config-driven e densidade de comentários
- `.planning/phases/13-…/13-PATTERNS.md` — analogs, aditividade, gate no-repaint, fixtures
- `.planning/STATE.md` §Decisions + `.planning/ROADMAP.md` Phase 14 — gates travados do marco
- `.planning/REQUIREMENTS.md` — PAT-01, SIG-01

### Secondary (MEDIUM confidence)
- `.planning/research/FEATURES.md` §6 (detecção de padrões), §7 (checklist/score) — abordagem geométrica
- `.planning/research/PITFALLS.md` Pitfalls 1, 2, 11, 12 — repaint, falso positivo, ancoragem

### Tertiary (LOW confidence — validar)
- Regras geométricas de Murphy (measured-move, simetria de ombros, neckline) — conhecimento de domínio
  destilado na research do marco; **limiares numéricos (A1–A7) precisam de calibração multi-ticker**

## Metadata

**Confidence breakdown:**
- Standard stack / contratos / harness: HIGH — verificado direto no código (252 testes coletados)
- Algoritmos de detecção (estrutura): MEDIUM — regras geométricas claras, mas é código novo sem analog exato
- Limiares geométricos (valores): LOW-MEDIUM — sem valor canônico; calibração multi-ticker é parte do aceite
- Checklist (SIG-01): HIGH — pura agregação de rótulos já golden-testados
- Pitfalls / no-repaint: HIGH — verificados contra Fase 13 e research do marco

**Nota sobre "191 goldens":** o critério de sucesso cita "191 goldens verdes", mas a suíte atual já tem
**252 testes coletados** (a Fase 13 adicionou ~60). A invariante real é "**todos os testes existentes
seguem verdes**" (hoje 252) + novos goldens da fase. O 191 é o baseline fundamentalista v1.3.

**Research date:** 2026-06-29
**Valid until:** ~30 dias (código estável; sem libs externas voláteis). Reabrir se a Fase 13 sofrer
rebaseline de contrato.
```
