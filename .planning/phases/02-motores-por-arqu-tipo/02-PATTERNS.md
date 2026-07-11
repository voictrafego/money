# Phase 2: Motores por Arquétipo - Pattern Map

**Mapped:** 2026-07-11
**Files analyzed:** 9 (2 new, 7 modified)
**Analogs found:** 9 / 9 (all have a strong in-repo analog)

> Este projeto é uma engine Python single-tier. "Role" abaixo é a camada do projeto
> (`core/` puro = fonte única de método; `report/` amarra e exibe; `config.yaml`; `tests/`)
> e "Data Flow" é o padrão de computação (transform puro, funil de valuation, predicado, golden).
> Todos os analógos abaixo foram lidos linha a linha nesta sessão e trazem âncoras `arquivo:linha`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/core/motores.py` **(NOVO)** | core (motores puros) | transform (config-driven, never-raise) | `src/analista/core/ddm.py` | exact |
| `src/analista/core/motores.py` → `nav_contabil()` **(NOVO)** | core | transform | `src/analista/core/lentes.py` `vpa()` (`:51`) | exact |
| `src/analista/core/motores.py` → `dcf_crescimento()` **(NOVO)** | core | transform | reuso de `ddm.ddm_dois_estagios()` (`:78`) | exact |
| `src/analista/core/motores.py` → `ke_rim()` **(NOVO)** | core | transform | `src/analista/core/capm.py` `ke_local()` (`:69`) | exact |
| `src/analista/core/arquetipo.py` (registry) **(EDIT)** | core (registry) | lookup | `ARQUETIPO_MOTOR` dict próprio (`:45`) | in-place |
| `src/analista/report/report.py` (funil + dataclass + suspensão + render) **(EDIT)** | report (amarração) | funil de valuation | roteamento próprio (`:180-186`) + bloco DDM (`:188-204`) | in-place |
| `src/analista/cli.py` `_motor_pendente()` **(EDIT)** | entry point (paridade Ranking) | predicado | `_motor_pendente()` próprio (`:45-54`) | in-place |
| `config.yaml` bloco `motores:` **(EDIT, aditivo)** | config | knobs | bloco `arquetipo:` (`:171-203`) | sibling |
| `tests/test_motores.py` **(NOVO)** | test (golden) | golden puro + e2e | `tests/test_ddm.py` + `tests/test_arquetipo_roteamento.py` | exact |
| `tests/test_arquetipo_roteamento.py` **(EDIT asserts)** | test | golden e2e | asserts próprios (`:116-135`) | in-place |
| `tests/test_ranking_freio.py` **(EDIT asserts)** | test | golden predicado | asserts próprios (`:122-131`) | in-place |

---

## Pattern Assignments

### `src/analista/core/motores.py` (NOVO — core, transform puro config-driven)

**Analog primário:** `src/analista/core/ddm.py` (motor puro com dataclass de resultado + never-raise).
Espelhar 1:1 o esqueleto: docstring citando o capítulo/método, `Number = Optional[float]`,
uma `@dataclass` de resultado por motor, funções que recebem números prontos e devolvem
`Optional[Resultado]` (nunca levantam).

**Imports pattern** (copiar de `ddm.py:13-18`):
```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

Number = Optional[float]
```
Para reusos internos, seguir o padrão de `lentes.py:21` (`from . import multiples as mult`)
e importar `from . import ddm, lentes` quando o motor compõe outra primitiva do `core/`.

**Dataclass de resultado + never-raise** (espelha `ddm.py:21-46`, `valor_gordon`):
```python
# ddm.py:21-34 — dataclass de resultado com campo derivado em __post_init__
@dataclass
class ResultadoDDM:
    valor_intrinseco: float
    vp_dividendos: float
    vp_residual: float
    valor_residual_futuro: float
    dividendos_projetados: List[float]
    vp_por_ano: List[float]
    peso_residual: float = field(init=False)

    def __post_init__(self) -> None:
        self.peso_residual = (
            self.vp_residual / self.valor_intrinseco if self.valor_intrinseco else 0.0
        )

# ddm.py:37-46 — guard de borda: qualquer input None / divisor ≤ 0 → None (never-raise)
def valor_gordon(dpa1: float, ke: float, g: float) -> Number:
    if dpa1 is None or ke is None or g is None:
        return None
    if ke - g <= 0:
        return None
    return dpa1 / (ke - g)
```

**Core pattern — loop de PV com fade** (espelha o projetar+descontar de `ddm.py:97-115`):
```python
# ddm.py:101-106 — a mecânica de desconto e valor terminal a replicar no RIM:
vp_por_ano = [d / (1 + ke) ** (t + 1) for t, d in enumerate(divs)]
vp_dividendos = sum(vp_por_ano)
div_n = divs[-1]
vr_futuro = div_n * (1 + g_estavel) / (ke - g_estavel)
vp_residual = vr_futuro / (1 + ke) ** n
```
Para o RIM (D-01/D-02), o RESEARCH.md já traz o esqueleto pronto (RESEARCH `Pattern 1`,
linhas 146-172): fade linear do ROE até Ke, `B_t = B_{t-1}·(1 + ROE_t·retencao)`, excesso→0
em `n` ⇒ RI terminal ≈ 0, valor ancorado no VPA. Mesma assinatura-guard de `valor_gordon`
(`if None in (...) or n <= 0 or ke <= 0 or vpa0 <= 0: return None`).

---

### `src/analista/core/motores.py` → `nav_contabil()` (holding, ENG-05, D-03)

**Analog:** `src/analista/core/lentes.py` `vpa()` (`:51`) — reuso DIRETO, sem recalcular.

```python
# lentes.py:51-53 — VPA = PL / nº ações, via _safe_div (trata None/zero)
def vpa(patrimonio_liquido: float, num_acoes: float) -> Number:
    """Valor patrimonial por ação = PL / nº de ações (do ano-base)."""
    return mult._safe_div(patrimonio_liquido, num_acoes)
```

**Ano-base canônico** (padrão já usado em `lentes.metricas_par`, `lentes.py:157-162` — copiar):
```python
# lentes.py:157-162 — resolve o ano-base pelo c.ultimo_ano() e passa PL/ações desse ano
ult = c.ultimo_ano()
pvp = mult._safe_div(
    c.preco_atual,
    vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult)),
)
```
NAV = `lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))`. Rótulo obrigatório
(D-03): `"NAV contábil (piso patrimonial), não SOTP por segmento"`.

---

### `src/analista/core/motores.py` → `dcf_crescimento()` (crescimento, ENG-04, D-05)

**Analog:** reuso PURO de `src/analista/core/ddm.py` `ddm_dois_estagios()` (`:78`) — **sem tocar
o módulo** (aceite #5, golden `test_ddm`). Alimenta LUCRO/LPA no lugar de dividendo.

```python
# ddm.py:78-91 — assinatura reusável tal-qual; dpa_inicial recebe LPA projetado, não DPA
def ddm_dois_estagios(
    dpa_inicial: float, g_alto: float, n: int, g_estavel: float, ke: float,
    decrescente: bool = False, tributacao: float = 0.0,
) -> Optional[ResultadoDDM]:
    if ke is None or g_estavel is None or ke - g_estavel <= 0:
        return None
    if dpa_inicial is None or n <= 0:
        return None
    ...
```
Chamada recomendada (RESEARCH `Pattern 2`, linhas 174-184): `dpa_inicial = lpa_valuation()·(1+g_alto)`,
`decrescente=True` (modelo-H conservador). Rótulo honesto: "DCF sobre lucro, aproximação
capital-light" (Pitfall 4). `g_alto ≤ ke` já garantido em `report.py:172-173`.

**Cíclica (ENG-03, D-04)** reusa `ddm.valor_gordon` (`:37`) como P/L justo sobre o lucro
normalizado + `norm.base_normalizada` (`normalizacao.py:58`) para o lucro médio 7–10a
(RESEARCH `Pattern 3`, linhas 186-194).

---

### `src/analista/core/motores.py` → `ke_rim()` (Ke estrutural do RIM, D-01)

**Analog:** `src/analista/core/capm.py` `ke_local()` (`:69-71`) — mesma forma `rf + beta×ERP`,
mas com ERP de banco (sem o prêmio small-cap embutido em `erp_local`) e clamp piso/teto.

```python
# capm.py:69-71 — a fórmula base a espelhar (com ERP próprio + teto ≤ ke_live)
def ke_local(beta_acao: float, rf_local: float, erp_local: float) -> float:
    """Ke pela abordagem com dados locais (caso Engie, 17.2): Ke = Rf + Beta * ERP."""
    return rf_local + beta_acao * erp_local
```
D-01: `ke_rim = clamp(rf_ciclo + beta×erp_banco, piso, min(ke_live, teto))`, tudo config-driven
no novo bloco `motores.rim` (ver `config.yaml` abaixo). O `rf_local` já vem resolvido
through-the-cycle pelos entry points (`cli.py:113`) — o RIM NÃO troca a fonte de rf, só usa
um ERP menor + teto (RESEARCH linhas 229-246; golden ITUB4 ~R$40 calibra os números).

---

### `src/analista/core/arquetipo.py` — registry `ARQUETIPO_MOTOR` (EDIT)

**Analog:** o próprio dict (`:45-51`). Trocar os 4 `None` pelos ids dos motores novos.

```python
# arquetipo.py:45-51 — HOJE (4 chaves None):
ARQUETIPO_MOTOR = {
    FINANCEIRA: None,
    PAGADORA_REGULADA: "ddm",
    CICLICA: None,
    CRESCIMENTO: None,
    HOLDING: None,
}
# DEPOIS (Fase 2): FINANCEIRA: "rim", CICLICA: "normalizado",
#                  CRESCIMENTO: "dcf", HOLDING: "nav" (pagadora_regulada intocada)
```
Os ids têm de bater 1:1 com o dispatch do funil (`report.py`) e com o predicado de suspensão
(`motor != "ddm"`). Nenhuma outra linha de `arquetipo.py` muda (classificador intocado).

---

### `src/analista/report/report.py` — funil + dataclass + suspensão + render (EDIT)

**Analog:** o próprio arquivo. Quatro pontos de edição, todos com padrão local a copiar.

**(1) Novos campos em `AnaliseAcao`** (espelha o bloco aditivo Fase 1, `report.py:51-56`):
```python
# report.py:51-56 — padrão de campo aditivo read-only com comentário de fase:
    # --- Fase 1 v2.2: roteamento por arquétipo (aditivo, read-only) ---
    arquetipo: str = ""
    motor: str = ""
    arquetipo_fronteirico: bool = False
    arquetipo_candidatos: List[str] = field(default_factory=list)
    motor_pendente: bool = False
# ADICIONAR (Fase 2): intrinseco_motor: Optional[float] = None
#                     motor_rotulo: str = ""   (ou um dataclass ResultadoMotor por tipo)
```

**(2) Dispatch dos motores no funil** — inserir logo após a resolução do motor (`report.py:180-186`),
espelhando como o bloco DDM (`:188-204`) consome insumos canônicos:
```python
# report.py:180-186 — o motor já é resolvido aqui; o dispatch entra na sequência:
arq = arquetipo.classificar(c, cfg)
a.arquetipo = arq.chave
a.arquetipo_fronteirico = arq.fronteirico
a.arquetipo_candidatos = arq.candidatos
motor = arquetipo.ARQUETIPO_MOTOR.get(arq.chave)
a.motor = motor or "pendente_fase_2"
a.motor_pendente = motor is None
# NOVO: if a.motor == "rim": a.intrinseco_motor = motores.rim(...) ; elif "normalizado"/"dcf"/"nav" ...
#       (esqueleto em RESEARCH linhas 290-307)
```
Consumir SEMPRE os `*_valuation()` (Pitfall 2, anti-recalculo), como o funil já faz em
`report.py:101-108` e `:189`:
```python
# report.py:101, 189 — sinais-síntese canônicos que os motores devem consumir (não o cru):
lpa = c.lpa_valuation()              # base normalizada / nº ações
payout_proj = c.payout_valuation()  # média 3a + clamp 1.0
# + c.roe_valuation(), norm.base_normalizada(c.serie("lucro_liquido"), anos_media=N)
```

**(3) Migração da suspensão D-06** — o ponto mais delicado (Pitfall 1). Trocar o predicado em
`report.py:240` de `motor_pendente` → `motor != "ddm"`, reusando o MESMO prefixo "VERIFICAR":
```python
# report.py:240-256 — HOJE dispara por motor_pendente (vira False quando os motores entram):
    if a.motor_pendente:
        a.veredito = (
            f"VERIFICAR — arquétipo {a.arquetipo} usa o motor '{a.motor}', que chega na "
            f"Fase 2; o DDM abaixo é lente conservadora, não o motor deste perfil. "
            f"Referências: Graham/Bazin."
        )
        a.alertas.append(...)
# DEPOIS: `if a.motor != "ddm":` (o selo ainda consome DDM até a Fase 3, então TODO arquétipo
#         não-DDM segue suspenso). Texto atualiza: motor já EXISTE mas o selo não o consome ainda.
#         selo.py NÃO muda — o prefixo "VERIFICAR" já é tratado por selo.montar_selo (selo.py:119).
```
O ramo `elif a.vmin is not None and ...` (`report.py:257+`, veredito DDM) permanece — só é
alcançado quando `motor == "ddm"`.

**(4) Render — DDM rebaixado a "lente conservadora" + intrínseco do motor** (`report.py:483-568`):
```python
# report.py:489 — cabeçalho já exibe arquétipo→motor (só passa a mostrar id real, não pendente):
             f"|  *Arquétipo:* {a.arquetipo or '-'} → motor {a.motor or '-'}")
# report.py:532 — a seção "## Valuation por Desconto de Dividendos" ganha, onde motor != "ddm",
#   uma linha do intrínseco do motor (ex.: "RIM: R$ 40,xx") + sub-rótulo na tabela DDM
#   "(lente conservadora — não é o motor deste arquétipo)". Só exibição (D-06); sem tocar o cálculo.
```

---

### `src/analista/cli.py` — `_motor_pendente()` (EDIT, paridade Ranking D-06)

**Analog:** a própria função (`:45-54`). Migrar o predicado igual ao `report.py:240`.

```python
# cli.py:45-54 — HOJE: pendente = registry devolveu None
def _motor_pendente(c, cfg: dict) -> bool:
    arq = arquetipo.classificar(c, cfg)
    return arquetipo.ARQUETIPO_MOTOR.get(arq.chave) is None
# DEPOIS: return arquetipo.ARQUETIPO_MOTOR.get(arq.chave) != "ddm"
#         (senão o Ranking volta a estampar preço-alvo por regressão para bancos)
```
Consumidor a preservar: `alvo_regressao_confiavel(..., motor_pendente)` (`cli.py:57-85`) usa o
retorno como está — não muda de assinatura, só de semântica interna do predicado.

---

### `config.yaml` — bloco novo `motores:` (EDIT aditivo, anti-rebaseline)

**Analog:** o bloco `arquetipo:` (`:171-203`) — irmão novo, comentado, config-driven, NENHUMA
linha pré-existente tocada (Pitfall 5).

```yaml
# config.yaml:171-177 — padrão do bloco irmão a espelhar (cabeçalho + anti-rebaseline):
# --- Fase 1 (v2.2): Classificador de Arquétipo (ARQ-01/ARQ-02) ---
# Bloco NOVO, irmão de `selo:`. Thresholds INICIAIS ... São config-driven ...
# Anti-rebaseline (Pitfall 4): nenhum bloco pré-existente é tocado.
arquetipo:
  roe_alto_min: 0.15
  ...
```
Novo bloco `motores:` com `rim: { erp_banco, ke_piso, ke_teto, n_fade }`, anos de normalização
da cíclica e horizonte/estágios do crescimento. Não editar `ddm:`/`capm:`/`arquetipo:`
(os goldens pinam esses valores).

---

### `tests/test_motores.py` (NOVO — golden por motor)

**Analog:** `tests/test_ddm.py` (golden puro do livro) + `tests/test_arquetipo_roteamento.py`
(fixtures sintéticas + assert e2e via `analisar_acao`).

**Golden puro por motor** (espelha `test_ddm.py:34-48` — inputs fixos, tolerância absoluta):
```python
# test_ddm.py:38-48 — padrão: chama a função pura com inputs de livro e checa faixa + composição
res = ddm.ddm_dois_estagios(
    dpa_inicial=2.362, g_alto=0.1024, n=10, g_estavel=0.025, ke=0.1248,
)
assert res is not None
assert abs(res.valor_intrinseco - 37.22) < 0.20
assert abs(res.peso_residual - 0.483) < 0.02
```
RIM tipo-ITUB4: VPA/ROE~19,3%/Ke~12,5%/retenção~0,53 → intrínseco ~R$40 e materialmente >
DDM ao vivo (~R$16); excesso fade → RI terminal ≈ 0 (RESEARCH linhas 338-345).

**Fixture sintética + assert e2e** (copiar o estilo de `_financeira`/`_petroleo_compounder`,
`test_arquetipo_roteamento.py:50-82`):
```python
# test_arquetipo_roteamento.py:50-63 — fixture de banco (hard-route financeira):
def _financeira(ticker="BANK3") -> CompanyData:
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Banco", setor="Bancos", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = 1000
        c.patrimonio_liquido[a] = 5000
        c.dividendos[a] = 300
        c.num_acoes[a] = 1000
        ...
    c.preco_atual = 70.0
    c.beta = 0.9
    return c
```
E2e por motor: `a.motor == "rim"/"normalizado"/"dcf"/"nav"`, `a.intrinseco_motor` populado,
`a.veredito.startswith("VERIFICAR")` MESMO com motor plugado (D-06),
`selo.montar_selo(bsd_baixo, a.veredito, cfg).rotulo is None` (não estampa 'evitar').

---

### `tests/test_arquetipo_roteamento.py` + `tests/test_ranking_freio.py` (EDIT asserts — IN-SCOPE)

**Analog:** os asserts atuais que codificam a semântica "pendente" da Fase 1, que a Fase 2
deliberadamente substitui (Pitfall 1 / RESEARCH linhas 347-356).

```python
# test_arquetipo_roteamento.py:116-121 — HOJE assevera motor_pendente is True para financeira:
def test_financeira_suspende_veredito_e_nao_estampa_evitar():
    a = report.analisar_acao(_financeira(), cfg)
    assert a.arquetipo == "financeira"
    assert a.motor_pendente is True          # ← MUDA: agora a.motor == "rim"
    assert a.veredito.startswith("VERIFICAR")  # ← PRESERVA (veredito segue suspenso por motor != "ddm")

# test_ranking_freio.py:122-131 — HOJE _motor_pendente(banco) is True:
def test_motor_pendente_financeira_suspende():
    banco = _empresa("ITUB4", "Bancos")
    assert _motor_pendente(banco, _cfg()) is True   # ← MUDA de semântica: motor existe, mas != "ddm"
```
Atualizar para `a.motor in {"rim","dcf","normalizado","nav"}` + manter
`a.veredito.startswith("VERIFICAR")`. O assert de `test_regulada_...` (`:104-112`,
`motor == "ddm"`, NÃO suspenso) permanece verde sem mudança.

---

## Shared Patterns

### Never-raise / degradação graciosa (borda de todo motor)
**Source:** `src/analista/core/ddm.py:42-46`, `src/analista/core/lentes.py:46-48`
**Apply to:** todas as 4 funções de `motores.py`
```python
# ddm.py:42-46 — guard de None + divisor inválido no topo; retorna None em vez de levantar
if dpa1 is None or ke is None or g is None:
    return None
if ke - g <= 0:
    return None
```

### Fronteira CRU × valuation (FIX-04 / Pitfall 2)
**Source:** `src/analista/core/fundamentals.py:122-150` (`base_lucro_normalizada`,
`lpa_valuation`, `roe_valuation`) + `report.py:98-101` (comentário FIX-04)
**Apply to:** todo insumo consumido pelos motores — SEMPRE `*_valuation()`, nunca `c.lucro_liquido.get(ult)` cru
```python
# fundamentals.py:132-135, 137-150 — número-síntese único de valuation (base normalizada):
def lpa_valuation(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
    base = self.base_lucro_normalizada(anos_media, winsor)
    return mult.lpa(base, self.num_acoes.get(self.ultimo_ano()))
def roe_valuation(self, anos_media: int = 3, winsor: float = 0.10) -> Optional[float]:
    base = self.base_lucro_normalizada(anos_media, winsor)
    ...
```

### Ano-base canônico (RIM e NAV / Pitfall 3)
**Source:** `src/analista/core/lentes.py:157-162`
**Apply to:** `rim()` e `nav_contabil()` — resolver `ult = c.ultimo_ano()` e passar `PL/ações` desse ano
```python
ult = c.ultimo_ano()
vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))
```

### Não recalcular método já resolvido (Don't-Hand-Roll)
**Source:** RESEARCH.md tabela "Don't Hand-Roll" (linhas 204-211)
**Apply to:** todos os motores — reusar `lentes.vpa`, `ddm.ddm_dois_estagios`, `ddm.valor_gordon`,
`norm.base_normalizada`; nunca inline `pl/acoes`, loop de desconto novo ou `lucro/(ke-g)`.

### Config-driven sem hardcode + anti-rebaseline
**Source:** `src/analista/core/arquetipo.py:138-143` (lê tudo de `cfg["arquetipo"]` com defaults) +
`config.yaml:171-177` (bloco irmão comentado)
**Apply to:** `ke_rim()` e horizontes/thresholds dos motores — ler de `cfg["motores"]`, bloco novo.

---

## No Analog Found

Nenhum arquivo desta fase fica sem analógo forte no repositório. Todos os 4 motores compõem
primitivas existentes (`ddm.py`, `lentes.py`, `normalizacao.py`, `capm.py`) e todos os pontos
de integração (registry, funil, suspensão, render, predicado do Ranking, goldens) já têm o
padrão estabelecido pela Fase 1. O único elemento genuinamente novo — a **calibração numérica
do Ke estrutural do RIM** (D-01, RESEARCH `Assumptions Log` A1) — não é um arquivo mas um
número a calibrar contra o golden ITUB4 ~R$40; o *código* que o hospeda (`ke_rim` espelhando
`capm.ke_local`) tem analógo exato.

## Metadata

**Analog search scope:** `src/analista/core/` (ddm, lentes, arquetipo, capm, fundamentals,
normalizacao), `src/analista/report/report.py`, `src/analista/cli.py`, `config.yaml`,
`tests/` (test_ddm, test_arquetipo_roteamento, test_ranking_freio)
**Files scanned (read):** 11
**Pattern extraction date:** 2026-07-11
