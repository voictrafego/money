# Phase 1: Classificador de Arquétipo + Roteamento - Pattern Map

**Mapped:** 2026-07-11
**Files analyzed:** 4 (2 new, 2 modified/config)
**Analogs found:** 4 / 4 (todos com match forte no próprio repo)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/core/arquetipo.py` (NEW) | core / engine pura (classifier) | transform (CompanyData → ResultadoArquetipo) | `src/analista/core/lifecycle.py` + `src/analista/core/normalizacao.py` | exact (mesmo papel: função pura sobre sinais) |
| `ARQUETIPO_MOTOR` (dict no mesmo módulo, NEW) | registry / config module-level | lookup (chave → motor) | `lifecycle.ESTAGIOS`, `selo._MATRIZ`, `report._MATRIZ_LEITURA` | exact (dict módulo-nível curado) |
| `src/analista/report/report.py` (MODIFIED) | report / funil de valuation | request-response (orquestração + veredito) | ele mesmo (`analisar_acao`, padrão já estabelecido `:53-313`) | in-place (editar o próprio) |
| `config.yaml` → bloco `arquetipo:` (NEW) | config | — | bloco `selo:` (`:160-169`), bloco `padroes:` (`:120-137`) | exact (padrão "bloco irmão, anti-rebaseline") |
| `tests/test_arquetipo.py` (NEW) | test / golden offline | — | `tests/test_guardrails_fix06.py`, `tests/test_consistencia_modos.py` | exact (ROOT + `_cfg()` + fixtures sintéticas) |

Helper novo `_cv_lucro` mora dentro de `core/arquetipo.py` (não há primitiva de "oscilação" pronta) — segue o estilo das primitivas puras de `normalizacao.py`.

## Pattern Assignments

### `src/analista/core/arquetipo.py` (core, transform) — NEW

**Analog primário:** `src/analista/core/lifecycle.py` (módulo inteiro, 49 linhas) — função pura de classificação por heurística de thresholds, com dict de rótulos módulo-nível e None-handling explícito. **Analog secundário:** `src/analista/core/normalizacao.py` (primitivas puras, helper `_limpar`, uso de `statistics`).

**Docstring de cabeçalho + `from __future__`** (padrão de `lifecycle.py:1-10` e `normalizacao.py:1-30`): docstring explica o "porquê" ligando ao livro/brief, seguido de `from __future__ import annotations`. Ex. de `lifecycle.py`:
```python
"""Estágio do ciclo de vida da empresa — Cap. 8 (Damodaran, 2017).
...
"""
from __future__ import annotations
from typing import Optional
```

**Constantes/registry módulo-nível** (padrão `lifecycle.ESTAGIOS:12-19`): dict módulo-nível com comentário. Aplicar às 5 chaves + registry:
```python
# lifecycle.py:12-19 (analog do registry)
ESTAGIOS = {
    1: "Startup",
    2: "Crescimento jovem",
    ...
}
```

**Função pura de classificação com None-guarding** (padrão `lifecycle.classificar_estagio:22-49`): assinatura tipada, docstring com as regras em bullets, cada sinal `None` normalizado ou guardado ANTES de comparar. Note o padrão exato `g = g_lucro if g_lucro is not None else 0.0`:
```python
# lifecycle.py:22-49
def classificar_estagio(
    g_lucro: Optional[float],
    payout: Optional[float],
    lucro_positivo: bool,
    lucro_decrescente: bool = False,
) -> str:
    """Heurística de classificação do estágio de ciclo de vida.
    - prejuízo persistente → Startup/Declínio;
    ...
    """
    if not lucro_positivo:
        return ESTAGIOS[1] if not lucro_decrescente else ESTAGIOS[6]
    g = g_lucro if g_lucro is not None else 0.0
    p = payout if payout is not None else 0.0
    if lucro_decrescente and p > 0.9:
        return ESTAGIOS[6]
    if g >= 0.20 and p < 0.30:
        return ESTAGIOS[2]
    ...
    return ESTAGIOS[5]
```
> **Contrato de None (Pitfall 2 do RESEARCH):** `roe_valuation()`/`margem_valuation()`/`payout_valuation()` retornam `None` (falta PL ano-1, série vazia). Guardar cada um com `is not None` antes de qualquer `>=`, exatamente como `lifecycle` normaliza `g`/`p`. Degradação graciosa → default `pagadora_regulada` ou `fronteirico=True`, nunca `TypeError`.

**Dataclass de resultado** (padrão `report.selo.Selo:26-43` e `fundamentals.CompanyData:19-24`): `@dataclass` com defaults degradáveis e docstring por campo. `field(default_factory=list/dict)` para mutáveis:
```python
# selo.py:26-43 (analog do ResultadoArquetipo)
@dataclass
class Selo:
    """Selo derivado (aditivo, defaults degradáveis)."""
    bsd: Optional[float] = None
    cor: Optional[str] = None
    ...
    verificar: bool = False
```
Para listas/dicts mutáveis usar `field(default_factory=...)` como em `CompanyData` (`fundamentals.py:24,27`): `anos: List[int] = field(default_factory=list)`.

**Helper puro de oscilação `_cv_lucro`** (padrão `normalizacao._limpar:34-36` + uso de `statistics`): helper privado prefixado `_`, filtra `None`, guarda tamanho mínimo e denominador zero, retorna `Optional[float]`:
```python
# normalizacao.py:34-36 (analog do _cv_lucro) + normalizacao.py:39-55 (guardas de N/vazio)
def _limpar(valores: Sequence[Number]) -> List[float]:
    """Descarta os None (não contam como 0) e converte para float."""
    return [float(v) for v in valores if v is not None]
# ... na media_winsorizada: guardas de len antes de operar
    if not limpos:
        return None
    if len(limpos) == 1:
        return limpos[0]
    if len(limpos) < 5:
        return float(median(limpos))
```
`_cv_lucro` reusa `statistics` (o RESEARCH sugere `mean`/`pstdev`); `normalizacao.py` já usa `from statistics import median` — mesma convenção de import.

**Consumo dos sinais canônicos (consistência cross-modo, Core Value):** o classificador chama métodos de `CompanyData` sem recalcular — `c.roe_valuation()`, `c.payout_valuation()`, `c.serie("lucro_liquido")`, `c.serie_lucro_normalizada()`, `c.margem_valuation()`, `c.eh_concessionaria`, `c.setor`. Ver assinaturas e contrato-None em `fundamentals.py:78-90` (payout), `:137-150` (roe_valuation, `None` sem PL ano-1), `:63-67` (serie).

---

### `ARQUETIPO_MOTOR` registry (dict módulo-nível em `core/arquetipo.py`) — NEW

**Analog:** três dicts curados módulo-nível já no repo:
- `lifecycle.ESTAGIOS` (`lifecycle.py:12-19`) — dict simples chave→rótulo.
- `selo._MATRIZ` (`selo.py:48-55`) — dict de tupla→string, com comentário "copy estável, NÃO tunável (fica no código de propósito)".
- `report._MATRIZ_LEITURA` (`report.py:322-352`) — dict de tupla→frase curada.

**Padrão a copiar** (`selo.py:46-55`): dict módulo-nível com comentário explicando por que fica no código (vs. config). O registry ENG-01 segue isto — a **taxonomia mora no código**, só os **thresholds** vão pro `config.yaml`:
```python
# selo.py:48-55
_MATRIZ = {
    ("Alta", "Barato"): "JOIA",
    ("Alta", "Justo"): "Boa, no preço",
    ...
}
```
Registry alvo (do RESEARCH Pattern 2): chaves = constantes das 5 chaves; valor `"ddm"` só para `pagadora_regulada`, `None` para o resto (motor pendente Fase 2). Lookup no report via `.get(chave)` (padrão de `.get` já usado em `selo.cor_do_bsd:66` e `report.py` em toda parte).

---

### `src/analista/report/report.py` (report, request-response) — MODIFIED

**Analog:** o próprio funil `analisar_acao` (`:53-313`) — padrão já estabelecido; as edições seguem o estilo local.

**Novos campos em `AnaliseAcao`** (padrão `:22-51`): campos aditivos, tipados `Optional`, com comentário de fase, mutáveis via `field(default_factory=...)`. Ver o bloco de campos aditivos das fases anteriores (`:43-50`, com cabeçalho `# --- Fase X: ... (aditivo, read-only) ---`):
```python
# report.py:43-50 (padrão para os campos arquétipo/motor/fronteirico/candidatos/motor_pendente)
    # --- Phase 6: read técnico consultivo (aditivo, read-only sobre o fundamento) ---
    sinais: Optional["indicators.SinaisTecnicos"] = None
    timing_estado: str = ""
    ...
    # --- Fase 20: Selo de Sustentabilidade × veredito de preço (aditivo, read-only) ---
    selo: Optional["selo_mod.Selo"] = None
```
Novos campos sugeridos (do RESEARCH): `arquetipo: str = ""`, `motor: str = ""`, `arquetipo_fronteirico: bool = False`, `arquetipo_candidatos: List[str] = field(default_factory=list)`, `motor_pendente: bool = False`.

**Import do novo módulo** (padrão `:16-19`): adicionar ao bloco de imports `from ..core import ...`:
```python
# report.py:16-19
from ..core import capm, ddm, growth, indicators, lifecycle, screening
from ..core import multiples as mult
from ..core.fundamentals import CompanyData
from . import selo as selo_mod
```
Acrescentar `arquetipo` à lista `from ..core import ...` (mesma linha que `capm, ddm, ...`).

**Ponto de inserção do roteamento — ENTRE `:134` e `:136`** (após a trava `g_alto ≤ Ke`, antes do comentário `# --- DDM de dois estágios ---`). Contexto exato:
```python
# report.py:130-136 (inserir DEPOIS de :134, ANTES de :136)
    if a.g_alto is not None and a.ke is not None:
        a.g_alto = min(a.g_alto, a.ke)          # :133-134 (fim do CAPM)

    # *** NOVO: classificar arquétipo + resolver motor via registry (ENG-01) ***
    #   arq = arquetipo.classificar(c)
    #   a.arquetipo/a.arquetipo_fronteirico/a.arquetipo_candidatos = ...
    #   motor = arquetipo.ARQUETIPO_MOTOR.get(arq.chave)
    #   a.motor = motor or "pendente_fase_2"; a.motor_pendente = (motor is None)

    # --- DDM de dois estágios (Cap. 15/17) ---   # :136 (bloco DDM roda como HOJE)
```
> **Crítico (RESEARCH Pattern 2 / Pitfall 5):** o bloco DDM `:136-152` **continua rodando sempre** (popula `ddm_constante`/`ddm_h`/`sensibilidade` que a UI exibe como lente e que `test_guardrails_fix06` exige). A mudança D-04 é **só no veredito**.

**Suspensão D-04 reusando o prefixo "VERIFICAR"** — o veredito já usa "VERIFICAR" para a salvaguarda DDM-FIX-05 (`:197-201`). Copiar exatamente esse padrão de frase e guardá-lo ANTES do ramo de preço (`:184`):
```python
# report.py:184-207 (bloco veredito — analog do texto "VERIFICAR" a copiar de :197-201)
    if a.vmin is not None and a.vmax is not None and a.preco_atual:
        if a.preco_atual < a.vmin:
            if flag_payout or flag_dy or flag_div_prejuizo:
                ...
                a.veredito = (
                    f"VERIFICAR — preço R$ {_br(a.preco_atual)} abaixo do intervalo intrínseco "
                    f"R$ {_br(a.vmin)}–{_br(a.vmax)}, mas sinais de risco ({', '.join(motivos)}) "
                    f"contradizem a tese de desconto: possível divergência de modelo."
                )
            else:
                a.veredito = f"SUBAVALIADA — preço R$ {_br(a.preco_atual)} abaixo ..."
```
D-04 acrescenta um guard `if a.motor_pendente:` no topo desse bloco que estampa um veredito com prefixo **"VERIFICAR — arquétipo X usa motor Y (Fase 2) ..."** e um `a.alertas.append(...)` (padrão de append em `:210-238`). Reusar "VERIFICAR" faz `selo.montar_selo` marcar `verificar=True` sem atribuir faixa/rótulo (`selo.py:119-122`) → **não estampa 'evitar'** sem tocar o firewall.

> **Pitfall 3 (NÃO criar prefixo novo):** `selo.faixa_do_veredito` (`selo.py:88-102`) e `report._veredito_token` (`report.py:355-360`) são dois parsers de prefixo independentes que casam só `SUBAVALIADA`/`NO INTERVALO`/`SOBREAVALIADA`/`VERIFICAR`. Um prefixo inédito ("AGUARDANDO MOTOR") os quebra. Ver `_veredito_token`:
```python
# report.py:355-360
def _veredito_token(veredito: str) -> str:
    for t in ("SUBAVALIADA", "SOBREAVALIADA", "NO INTERVALO"):
        if veredito.startswith(t):
            return t
    return ""
```

**Render mínimo** (padrão `relatorio_markdown:410-518`): linha no cabeçalho `:414` (junto de Setor/Preço/Estágio) tipo "Arquétipo: X → motor Y"; quando `motor_pendente`, nota no bloco Veredito (`:488-496`). Padrão de append em lista `L`:
```python
# report.py:414-415 (analog do header a estender)
    L.append(f"*Setor:* {a.setor or '-'}  |  *Preço atual:* R$ {_num(a.preco_atual)}  "
             f"|  *Estágio (ciclo de vida):* {a.estagio}")
```

---

### `config.yaml` → bloco `arquetipo:` (NEW)

**Analog:** bloco `selo:` (`config.yaml:160-169`) e bloco `padroes:` (`:120-137`) — ambos "bloco NOVO, irmão de X, anti-rebaseline; nenhuma linha existente tocada".

**Padrão a copiar** (`config.yaml:160-169`): cabeçalho de comentário explicando o que o bloco parametriza + de onde vem + que é o único ponto de ajuste; valores com comentário inline por linha:
```yaml
# config.yaml:160-169 (analog do bloco arquetipo:)
# --- Fase 20: Selo de Sustentabilidade do Dividendo (SELO-01) ---
# Bloco NOVO, irmão de `screening:`/`score:`. ...
selo:
  cor:
    verde_min: 70                 # BSD >= 70 → verde (qualidade Alta)
    azul_min: 55
    amarelo_min: 40
```
Bloco alvo (do RESEARCH Thresholds): `arquetipo:` irmão de `selo:`, com `financeiro_tokens`, `regulada_excluir_tokens: [petróleo]` (guarda anti-Petróleo/Gás, Pitfall 1), `roe_alto_min: 0.15`, `retencao_alta_min: 0.50`, `ciclica_cv_min: 0.40`. **Não tocar nenhum bloco existente** (Pitfall 4 — 338 goldens não podem flutuar).

---

### `tests/test_arquetipo.py` (test, golden offline) — NEW

**Analog:** `tests/test_guardrails_fix06.py` e `tests/test_consistencia_modos.py` — goldens offline, sem rede, `CompanyData` sintético.

**Boilerplate ROOT + `_cfg()`** (idêntico em ambos os analogs, `test_guardrails_fix06.py:16-29` / `test_consistencia_modos.py`):
```python
# test_guardrails_fix06.py:16-29
import os
import yaml
from analista.core.fundamentals import CompanyData
from analista.report import report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _cfg() -> dict:
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)
```

**Fixture-modelo `CompanyData` sintético** (padrão `test_guardrails_fix06._empresa_crescente_solida:32-53` e `test_consistencia_modos._empresa_solida`): construtor com 10 anos preenchendo TODOS os campos. Reusar `setor="Energia Elétrica"` para o caso `pagadora_regulada` (Pitfall 5: TAEE11 idêntica):
```python
# test_guardrails_fix06.py:32-53 (analog das fixtures ITUB4/TAEE11/VALE3/WEGE3/PETR4)
def _empresa_crescente_solida(ticker="SOLID3"):
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Sólida Crescente", setor="Energia Elétrica", anos=anos)
    for i, a in enumerate(anos):
        c.lucro_liquido[a] = round(1000 * (1 + 0.08) ** i)
        c.patrimonio_liquido[a] = 4000 + i * 100
        c.dividendos[a] = round(0.5 * lucro)
        c.num_acoes[a] = 1000
        ...
    c.preco_atual = 25.0
    c.beta = 0.8
    return c
```
> Para o hard-route financeira, criar fixture com `setor="Bancos"` (ITUB4) e `setor="... Seguradoras ..."`; para regulada `setor="Energia Elétrica"` + `c.eh_concessionaria=True`; para o falso-positivo `setor="Petróleo e Gás"` + `eh_concessionaria=True` (guarda deve rejeitar). Note que `eh_concessionaria` é campo do `CompanyData` (`fundamentals.py:45`) settável direto no teste.

**Asserts de golden** (padrão `test_guardrails_fix06.py:83-111`): rodar `report.analisar_acao(c, _cfg())` e afirmar campos + degradação sem exceção. Trava-chave Pitfall 5 (TAEE11 idêntica): afirmar `arquetipo == pagadora_regulada`, `motor == "ddm"`, `fronteirico == False`, e `veredito` inalterado:
```python
# test_guardrails_fix06.py:103-111 (analog do teste de degradação sem exceção)
def test_banda_degrada_quando_ddm_nao_roda():
    c = CompanyData(ticker="VAZIA3", anos=[2024])
    c.preco_atual = 10.0
    a = report.analisar_acao(c, _cfg())
    assert a.sensibilidade is None
    assert a.vmin is None and a.vmax is None
    assert a.veredito == ""
```

## Shared Patterns

### Contrato de None / degradação graciosa
**Source:** `core/lifecycle.py:38-39` (normaliza `None`→default), `core/normalizacao.py:34-36,47-51` (`_limpar` + guardas de len), `core/fundamentals.py:105-107,143-150` (retorna `None` sem PL ano-1).
**Apply to:** `core/arquetipo.py` (todo sinal guardado `is not None` antes de comparar), `report.py` (ramo `motor_pendente`/DDM-não-rodou). Nunca deixar `None` cair num `>=` → `TypeError`. Degradação → default `pagadora_regulada` ou `fronteirico=True`.

### Config-driven (thresholds fora do código)
**Source:** `report/selo.py:66-69` (lê `cfg["selo"]["cor"]` com `.get(...)` + default), `config.yaml:160-169` (bloco `selo:`).
**Apply to:** `core/arquetipo.py` lê `cfg["arquetipo"]` (tokens + thresholds); goldens pinam via `_cfg()`. Números mágicos (0.15/0.40/0.50) NÃO no código.

### Firewall selo↛report / reuso de "VERIFICAR"
**Source:** `report/selo.py:10-18` (docstring do firewall), `selo.py:119-122` (overlay VERIFICAR sem faixa), `report.py:197-201` (frase "VERIFICAR" existente).
**Apply to:** a suspensão D-04 é feita 100% do lado do `report` (veredito), reusando o prefixo "VERIFICAR". `selo.py` NÃO é tocado. Não criar prefixo novo (mantém sincronia `faixa_do_veredito`↔`_veredito_token`).

### Consumo de sinais canônicos (consistência cross-modo)
**Source:** `core/fundamentals.py:78-90` (`payout_valuation`), `:122-162` (`roe_valuation`/`margem_valuation`/`serie_lucro_normalizada`), `:63-67` (`serie`).
**Apply to:** `core/arquetipo.py` — consumir os `*_valuation()` e `serie("lucro_liquido")` diretamente; jamais recalcular ROE/payout cru (quebraria `test_consistencia_modos`).

## No Analog Found

Nenhum arquivo sem análogo. Todos os papéis desta fase têm precedente forte no próprio repo. O único componente genuinamente novo é o helper `_cv_lucro` (medida de oscilação) — mas ele segue o estilo de primitiva pura de `core/normalizacao.py`, então não é "sem análogo", apenas "sem primitiva idêntica pronta".

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (nenhum) | — | — | Cobertura total; helper `_cv_lucro` espelha `normalizacao.py` |

## Metadata

**Analog search scope:** `src/analista/core/` (lifecycle, normalizacao, fundamentals), `src/analista/report/` (report, selo), `src/analista/ingest/build.py`, `config.yaml`, `tests/`
**Files scanned:** 8 fontes lidas + `find` sobre `src/` (30 módulos) e `ls tests/` (30 testes)
**Pattern extraction date:** 2026-07-11
</content>
</invoke>
