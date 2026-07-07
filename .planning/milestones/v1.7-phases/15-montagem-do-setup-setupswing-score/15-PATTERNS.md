# Phase 15: Montagem do Setup (SetupSwing) + Score - Pattern Map

**Mapped:** 2026-06-29
**Files analyzed:** 3 (1 novo módulo, 1 config estendido, 1 novo teste)
**Analogs found:** 3 / 3 (todos com análogo forte no próprio repo)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/report/setup.py` (NOVO) | service/presentation engine (read-only aggregator) | transform (lê `SinaisTecnicos` → score) | `src/analista/core/indicators.py` `_checklist` (L1064-1119) + `src/analista/report/presentation.py` | exact (idioma agregador read-only) |
| `config.yaml` (bloco `score:` novo, appended) | config | — | bloco `padroes:` (config.yaml L120-138) | exact (bloco irmão, mesmo padrão config-driven) |
| `tests/test_setup_report.py` (NOVO) | test | request-response (golden) | `tests/test_indicators.py` (`_cfg_ind` L17, `_familias_stub` L1463, `test_checklist_sem_copy_natural` L1567) | exact (harness golden + stubs duck-typed + anti-copy) |

**Confirmado por inspeção:** `src/analista/report/setup.py` e `tests/test_setup_report.py` NÃO existem ainda (greenfield). `config.yaml` termina no bloco `padroes:` (L138) — o novo bloco `score:` se anexa limpo ao final, sem tocar `indicadores:`/`padroes:`. `core/setups.py` NÃO existe (research confirmado) — manter tudo em `report/setup.py`.

---

## Pattern Assignments

### `src/analista/report/setup.py` (read-only aggregator, transform)

**Analog primário:** `src/analista/core/indicators.py` `_checklist` (L1064-1119) — o molde exato do "lê rótulos já computados, deriva resultado, zero recálculo".
**Analog de apresentação:** `src/analista/report/presentation.py` (helpers puros que só FORMATAM campos já calculados, com convenção de degradação por sentinela).
**Idioma R:R:** `src/analista/core/indicators.py` `_niveis_stop_rr` (L859-867).
**Firewall:** `src/analista/report/report.py` — NUNCA importar. A direção do firewall é confirmada por `report.py` L16 (`from ..core import ... indicators`): report.py importa indicators, então setup.py importa indicators e nunca report.py.

**Imports pattern** (espelhar o topo de `indicators.py` L18-27 + `presentation.py` L14-16):
```python
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from ..core import indicators   # só p/ tipos; consome SinaisTecnicos JÁ calculado
# NUNCA: from . import report  /  from .report import ...  (quebra o firewall — Critério 1)
```

**Dataclass pattern** — copiar o estilo de contrato de `indicators.py` (L33-198) e `report.py` `AnaliseAcao` (L21-30): dataclasses com defaults aditivos (`= None`, `field(default_factory=list)`) p/ degradação graciosa. Ver `Niveis` (L96-115) e `Checklist` (L165-169) como molde dos sub-objetos com default.

**Agregador read-only core pattern** — copiar de `_checklist` (`indicators.py` L1083-1119):
```python
# Guard de None no topo, depois compõe lendo SÓ rótulos estáveis já validados:
lista_padroes = padroes.lista if padroes is not None else []   # guard None (L1083)
# ... deriva booleanos/sub-scores das strings, sem recalcular indicador algum.
return Checklist(sinais=[
    Sinal("rsi", mom.nivel_rsi in ("sobrecomprado", "sobrevendido"), mom.nivel_rsi),
    ...
])
```
Aplicar o MESMO contrato no `montar_setup`: ler `contexto.dow_diario`, `forca.forca_adx`, `tendencia.posicao_mm200`, `padroes.lista[].tipo/.estado`, `momentum.nivel_rsi/.cruzamento_macd`, `volume.rompimento_com_volume` — todos rótulos discretos já golden-testados (Fases 13-14). Qualquer `rolling`/`ewm`/`diff` é sinal de recálculo errado.

**Gate de R:R sob `np.errstate`** — copiar EXATAMENTE o idioma de `_niveis_stop_rr` (`indicators.py` L846-867), mas recomputando do bruto (NÃO parsear o string `niveis.risco_retorno` "1 : 2,5"):
```python
low, high = niveis.entrada_zona          # L846
entrada_ref = (low + high) / 2.0          # ponto médio da zona (L847)
risco = abs(entrada_ref - stop)           # stop = niveis.stop (L859)
retorno = abs(niveis.alvo - entrada_ref)  # L860
with np.errstate(divide="ignore", invalid="ignore"):
    razao = np.divide(retorno, risco)     # risco==0 → inf, não exceção (L862-863)
if risco <= 0 or not np.isfinite(razao):  # L864
    rr_valor = None                       # → GATE DURO falha → "Sem setup"
else:
    rr_valor = float(razao)
# GATE DURO (D-03/D-04): rr_valor is None or rr_valor < cfg["score"]["rr_minimo"] → "Sem setup"
```

**Guard de borda / degradação graciosa** — copiar o estilo de early-return de `_niveis_stop_rr` L834-838 e `_padroes` L902-903 (`return Padroes(lista=[])`): se `sinais is None` ou `sinais.niveis`/`sinais.contexto` são `None` → `return SetupSwing(score=0.0, grade="Sem setup")`, NUNCA levanta exceção. Todos os sub-objetos de `SinaisTecnicos` têm default `None` (L180-198) — cada acesso precisa de guard.

**Config-driven** — receber `cfg: dict` por parâmetro (idioma de `calcular(ohlc, cfg)` e `_niveis_stop_rr(..., cfg)` L814): `sc = cfg["score"]`; ler `sc["pesos"]`, `sc["rr_minimo"]`, `sc["penalidade_conflito_mtf"]`, `sc["cortes_grade"]`. Zero hardcode de pesos/cortes na montagem (Critério 3).

**Copy neutra** — `grade`/`detalhe` são chaves estáveis ("Forte"/"Moderado"/"Fraco"/"Sem setup", "alta+forte", "duplo_fundo:confirmado"), NUNCA imperativo. Espelhar a convenção de `Sinal.detalhe` (L160) e o comentário de firewall de copy em `_checklist` (L1078-1079).

---

### `config.yaml` — bloco `score:` (NOVO, append ao final)

**Analog:** bloco `padroes:` (config.yaml L120-138), que a Fase 14 anexou como irmão de `indicadores:` sem tocar nenhuma linha existente.

**Pattern a copiar** (estrutura + comentário-cabeçalho + valores comentados inline):
```yaml
# --- v1.4 Fase 14: padrões gráficos sobre pivôs (Murphy) — ... ---  (L120-124: cabeçalho que explica anti-rebaseline)
padroes:
  lookback_pivos: 8           # comentário inline explicando o porquê do valor
  price_tolerance_pct: 0.03   # ...
```

**Novo bloco a criar** (valores travados em CONTEXT D-01; cortes/rr/penalidade ASSUMED-calibráveis do RESEARCH):
```yaml
# --- v1.5 Fase 15: score de confluência técnica (SCORE-01) ---
# Bloco NOVO, irmão de `indicadores:`/`padroes:`. Nenhuma linha existente é tocada (anti-rebaseline).
score:
  pesos:                    # somam 100 (D-01: tendência domina)
    tendencia: 35
    risco_retorno: 20
    padroes: 20
    momentum: 15
    volume: 10
  rr_minimo: 1.5            # GATE DURO (D-04): rr < isto → "Sem setup". Calibrável.
  penalidade_conflito_mtf: 0.20   # alinhamento_mtf=="conflito" → score ×(1−0.20) (D-07)
  cortes_grade:            # sobre o score 0-100 (D-05). Calibráveis.
    forte: 70
    moderado: 50
    fraco: 25              # abaixo de `fraco` (com gate ok) → ainda "Sem setup" (floor)
```
**Crítico:** NÃO editar `indicadores:` (L97-118) nem `padroes:` (L125-138) — flutuaria os 271 goldens (Pitfall 4).

---

### `tests/test_setup_report.py` (test, golden)

**Analog:** `tests/test_indicators.py` — harness `_cfg_ind` (L17-21), stubs `_familias_stub` (L1463-1477), anti-copy `test_checklist_sem_copy_natural` (L1567-1590).

**Carregar config (copiar `_cfg_ind` L17-21):**
```python
def _cfg_ind() -> dict:
    raiz = Path(__file__).resolve().parents[1]
    with open(raiz / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
```

**Stubs duck-typed (copiar o idioma `_familias_stub` L1463-1477)** — construir `SimpleNamespace`/dataclasses reais só com os rótulos que `montar_setup` lê, sem rodar `calcular()`:
```python
from types import SimpleNamespace
def _sinais_stub(dow="alta", forca_adx="forte", posicao_mm200="acima",
                 alinhamento_mtf="alinhado_alta", entrada_zona=(95.0, 100.0),
                 stop=90.0, alvo=120.0, nivel_rsi="neutro", cruzamento_macd="cruz_alta",
                 rompimento_com_volume=True, padroes=None):
    contexto = SimpleNamespace(dow_diario=dow, alinhamento_mtf=alinhamento_mtf)
    forca = SimpleNamespace(forca_adx=forca_adx, adx=None)
    tendencia = SimpleNamespace(posicao_mm200=posicao_mm200, cruzamento="nenhum")
    niveis = SimpleNamespace(entrada_zona=entrada_zona, stop=stop, alvo=alvo,
                             risco_retorno="indisponivel")
    momentum = SimpleNamespace(nivel_rsi=nivel_rsi, cruzamento_macd=cruzamento_macd)
    volume = SimpleNamespace(rompimento_com_volume=rompimento_com_volume, volume_acima_mm=False)
    padroes = padroes if padroes is not None else indicators.Padroes(lista=[])
    return SimpleNamespace(contexto=contexto, forca=forca, tendencia=tendencia,
                           niveis=niveis, momentum=momentum, volume=volume, padroes=padroes)
```
> Para `padroes`, reusar o dataclass REAL `indicators.Padroes`/`PadraoGrafico` (como em `test_checklist_padrao_confirmado_ativa` L1519-1522), não SimpleNamespace, para casar a leitura `.tipo`/`.estado`.

**Anti-copy (copiar `test_checklist_sem_copy_natural` L1583-1590):**
```python
proibidos = ("compre", "venda", "comprar", "vender", "entre", "recomend", "sugiro", "indico")
# varrer setup.grade + cada decomposicao[].detalhe + qualquer string do dataclass:
for termo in proibidos:
    assert re.search(rf"\b{termo}", texto.lower()) is None, f"copy imperativo '{termo}' em '{texto}'"
```

**End-to-end (copiar `test_calcular_integra_padroes_checklist` L1543-1554):** rodar `indicators.calcular(_frame_ohlc_longo(), cfg)` → `montar_setup(s, cfg)`, asserir tipo + `grade in {"Forte","Moderado","Fraco","Sem setup"}` sem cravar floats frágeis.

**Cobertura de testes alvo (RESEARCH §Estratégia de Goldens):** 1 por grade (forte/moderado/fraco/sem-setup-floor); gate R:R zera (`rr=1.1` com famílias excelentes); R:R indisponível (níveis None); decomposição soma o score (Σ `contribuicao` == score pré-penalização); penalização multi-TF (`alinhamento_mtf="conflito"` → score×0.80, `conflito_mtf=True`, grade não vira "Sem setup" só por isso); degradação (`montar_setup(None, cfg)` não levanta); config-driven (mudar um peso muda o score).

---

## Shared Patterns

### Degradação graciosa (guard de None → retorno neutro, nunca exceção)
**Source:** `indicators.py` `_niveis_stop_rr` L834-838, `_padroes` L902-903, `_checklist` L1083
**Apply to:** topo de `montar_setup` e cada sub-score por família.
```python
if niveis.entrada_zona is None or niveis.alvo is None or niveis.pivos_ancora is None:
    return                       # early-return neutro, sem exceção (estilo L834-835)
```
Todos os sub-objetos de `SinaisTecnicos` têm default `None` (`indicators.py` L180-198) — sempre guardar antes de acessar `.dow_diario`/`.entrada_zona`/etc.

### Razão protegida sob `np.errstate`
**Source:** `indicators.py` L862-864 (R:R) e L918-919/L927-928 (simetria/altura de padrões)
**Apply to:** o gate de R:R em `setup.py`.
```python
with np.errstate(divide="ignore", invalid="ignore"):
    razao = np.divide(retorno, risco)
if risco <= 0 or not np.isfinite(razao): ...   # → "indisponível"/gate falha
```

### Config-driven por parâmetro `cfg: dict`
**Source:** `calcular(ohlc, cfg)`, `_niveis_stop_rr(..., cfg)` L814, `_padroes(...) cfg["padroes"]` L901, teste `_cfg_ind` L17
**Apply to:** assinatura de `montar_setup(sinais, cfg)` e ao carregamento nos testes.

### Firewall de copy (chaves estáveis neutras, nunca imperativo)
**Source:** `indicators.py` `Sinal`/`PadraoGrafico`/`ContextoTendencia` docstrings (L132, L140, L160, L1078-1079); teste `test_checklist_sem_copy_natural` L1567-1590
**Apply to:** todos os campos string de `SetupSwing`/`ContribFamilia` + o teste anti-copy.

### Direção do firewall de import (setup.py → indicators, NUNCA → report.py)
**Source:** `report.py` L16 importa `indicators` (direção confirmada)
**Apply to:** `setup.py` importa `from ..core import indicators` e nada de `report.py`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | Todos os 3 arquivos têm análogo forte no repo. A *matemática de scoring ponderado* (Σ sub_score×peso, normalização 0-100, cortes de grade) não tem análogo direto, mas é aritmética trivial sem padrão a copiar — segue os valores ASSUMED do RESEARCH §Mapeamento insumo→score (L195-218) e do bloco `score:` do config. |

## Metadata

**Analog search scope:** `src/analista/core/indicators.py`, `src/analista/report/{presentation,report}.py`, `config.yaml`, `tests/test_indicators.py`
**Files scanned:** 5 (todos lidos com excerpts extraídos)
**Pattern extraction date:** 2026-06-29
```
