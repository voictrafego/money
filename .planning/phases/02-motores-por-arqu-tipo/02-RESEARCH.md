# Phase 2: Motores por Arquétipo - Research

**Researched:** 2026-07-11
**Domain:** Valuation engines (RIM, lucro normalizado, DCF multi-estágio, NAV) plugados num registry Python puro; wiring no funil de `report.analisar_acao`
**Confidence:** HIGH (código-fonte inspecionado linha a linha; fórmulas são livro-texto)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 — RIM usa Ke estrutural/mid-cycle (~12,5%), NÃO o Ke do CAPM ao vivo (~17%).** Com ITUB4 (ROE ~19,3%), Ke ~12,5% dá excesso ~6,8% e destrava ~R$40 (aceite #1). O DDM com Ke ao vivo (~17% → ~R$16) fica como **lente conservadora**. *(Nota factual confirmada abaixo — o app já injeta Selic through-the-cycle; a alavanca é o RIM usar um Ke MENOR que o CAPM, não trocar a fonte de rf.)* De onde sai o Ke estrutural fica a critério do planner.
- **D-02 — Excesso de ROE faz *fade* até o Ke** num horizonte explícito (~7–10a) + valor terminal ancorado no VPA. Nenhum banco rende acima do custo de capital para sempre.
- **D-03 — NAV contábil simplificado (não SOTP por segmento).** Motor holding = PL/ações (`lentes.vpa`), rotulado "NAV contábil (piso patrimonial), não SOTP por segmento". Nenhum ticker-âncora é holding; mantém registry 5/5 custo-zero.
- **D-04 — Cíclica = P/L justo sobre lucro normalizado** (7–10a, `serie_lucro_normalizada` já existe), não sobre 1 ano. Fonte do P/L justo a critério do planner. NÃO usa EV/EBITDA (evita dívida líquida + D&A da CVM).
- **D-05 — Crescimento = multi-estágio sobre lucro/FCF**, com `g_alto`→`g_estável` já calculados, descontado ao Ke normalizado. Reusa a mecânica de dois estágios (`ddm.ddm_dois_estagios` como função pura OU helper extraído), **sem tocar `core/ddm.py`** nem depender de capex.
- **D-06 — Motor calcula e EXIBE o intrínseco; selo/veredito continua SUSPENSO.** *(Armadilha crítica — ver Pitfall 1.)* A condição de suspensão migra de `motor_pendente` → "selo ainda não consome o motor do arquétipo" (todo arquétipo não-DDM permanece suspenso). `selo.py`, o firewall selo↛report e `report._veredito_token` NÃO mudam nesta fase.

### Claude's Discretion
- Fonte do "P/L justo" da cíclica (mediana histórica própria vs. setorial vs. regressão P/L~f(payout,ROE)).
- Thresholds/horizontes numéricos: anos do fade do RIM (~7–10a), anos da normalização da cíclica, horizonte/estágios do crescimento.
- Estrutura de código dos motores: assinaturas, reuso direto de `ddm_dois_estagios` vs. helper genérico, forma de rotular cada motor, rebaixamento do DDM a "lente conservadora".
- Como resolver o VPA/PL do NAV e do RIM (ano-base efetivo) — reusar `lentes.vpa` e métodos canônicos de `CompanyData`.

### Deferred Ideas (OUT OF SCOPE)
- SOTP real por segmento (recusado, D-03).
- EV/EBITDA para cíclica (D-04).
- DCF de FCF puro com capex projetado (D-05).
- Selo consumir o motor (VER-01), ensemble + bandeira (ENS-01), guarda-corpos completos (SAN-01), dúvida honesta fronteira (VER-02) → **Fase 3**.
- Validação empírica / backtesting (BACKTEST-01).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **ENG-02** | RIM (VPA + VP do excesso de ROE sobre Ke) para banco/seguradora | Fórmula RIM detalhada abaixo; insumos prontos: `lentes.vpa` (`lentes.py:51`), `roe_valuation()`/`payout_valuation()` (`fundamentals.py:137/:78`); Ke estrutural via nova alavanca (D-01, ver §"Ke do RIM") |
| **ENG-03** | Lucro normalizado (P/L justo × lucro médio 7–10a) para cíclica | `serie_lucro_normalizada()` (`fundamentals.py:127`) + `base_normalizada(anos_media=7..10)` (`normalizacao.py:58`); P/L justo via 1/Ke ou Gordon sobre lucro normalizado (reusa `ddm.valor_gordon`, `ddm.py:37`) |
| **ENG-04** | DCF multi-estágio sobre lucro/FCF para crescimento | Reuso puro de `ddm.ddm_dois_estagios` (`ddm.py:78`) alimentado por `lpa_valuation()` em vez de dividendo; `g_alto`/`g_estavel`/`ke` já calculados (`report.py:136-173`) |
| **ENG-05** | NAV/SOTP (NAV contábil simplificado) para holding | `lentes.vpa(PL_ult, num_acoes_ult)` — piso patrimonial direto (D-03) |
</phase_requirements>

## Summary

O gargalo desta fase **não** são as fórmulas (RIM/lucro normalizado/DCF/NAV são livro-texto e ~todos os insumos já existem canonicamente em `CompanyData`) — é o **wiring correto no funil de `report.analisar_acao` sem regredir o ITUB4**. O código está maduro: registry `ARQUETIPO_MOTOR` (`arquetipo.py:45`) com 4 chaves `None`, roteamento já plugado (`report.py:180-186`), funil único de valuation, funções puras espelhando `ddm.py`, e uma bateria de goldens offline que travam comportamento.

A **armadilha central (D-06)** é arquitetural e aparece em **três superfícies** que hoje derivam suspensão de `ARQUETIPO_MOTOR.get(chave) is None`: `report.py:240` (`if a.motor_pendente:`), `cli._motor_pendente` (`cli.py:45-54`, paridade no Ranking), e os goldens (`test_arquetipo_roteamento.py`, `test_ranking_freio.py`). No instante em que a Fase 2 troca os 4 `None` pelos ids dos motores, `motor is None` vira `False` **em todos os três lugares** — a suspensão cai, e como o selo ainda consome DDM até a Fase 3, o ITUB4 despenca do "VERIFICAR" (protegido) para "SOBREAVALIADA → Evitar" via DDM. A migração `motor_pendente → "selo não consome o motor do arquétipo"` (ou seja: suspende para todo arquétipo cujo motor ≠ `"ddm"`) tem de ser feita **junto** com o plug dos motores, senão o critério de aceite #1 regride.

A **nota factual do D-01 está CONFIRMADA no código**: `cli.py:113` injeta `macro.selic_ciclo_para_capm` (Selic média 10a through-the-cycle, `macro.py:87`) em `cfg["capm"]["rf_local"]`; `report.py:161` monta `a.ke = capm.ke_local(beta, rf_local, erp_local)`. Com `erp_local=0.06` (que embute ~1,5% de prêmio small-cap/iliquidez, comentário do `config.yaml:66-68`) e beta de banco, o Ke ao vivo fica ~15–17%. Trocar spot→ciclo **já foi feito e é insuficiente**; a alavanca do #1 é o RIM usar um Ke MENOR que esse CAPM ao vivo.

**Primary recommendation:** Implementar os 4 motores como funções puras em módulos `core/` (novo `core/motores.py` ou um por motor, espelhando `ddm.py`), reusando `lentes.vpa`, `ddm.ddm_dois_estagios`/`valor_gordon` e os `*_valuation()` canônicos — **sem recalcular método** (consistência cross-modo). Plugar no registry, calcular no funil após `report.py:186`, gravar em novos campos de `AnaliseAcao` (`report.py:23`), exibir no render, e **migrar a suspensão nas TRÊS superfícies simultaneamente** (report + cli + goldens). Ke do RIM: recomendação = **normalizar rf through-the-cycle + ERP de banco (sem prêmio small-cap), com teto ≤ Ke ao vivo**, config-driven, ancorado no golden de livro 12,48%.

## Architectural Responsibility Map

Projeto é uma engine Python single-tier (sem backend/rede na engine). O mapa é por **módulo/camada** — a fronteira que a Fase 1 já estabeleceu (FIX-04: `core/` puro é fonte única de método; `report/` amarra e exibe).

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fórmula de cada motor (RIM/normalizado/DCF/NAV) | `core/` (funções puras, sem I/O) | — | Espelha `ddm.py`/`lentes.py`; testável por golden; consistência cross-modo |
| Registry arquétipo→motor | `core/arquetipo.py` (`ARQUETIPO_MOTOR`) | — | Ponto único já estabelecido (Fase 1, ENG-01) |
| Insumos normalizados (ROE/LPA/payout/lucro) | `core/fundamentals.py` (`*_valuation()`) + `core/normalizacao.py` | — | Fonte única de sinais (FIX-04) — motores CONSOMEM, não recalculam |
| Ke estrutural do RIM | `core/capm.py` (nova função) + `config.yaml` | entry points (`cli.py`/`app.py`) resolvem rf | Ke é config-driven; engine lê cfg e permanece offline/determinística |
| Cálculo no funil + campos de resultado | `report/report.py` (`analisar_acao`, `AnaliseAcao`) | — | Funil único de valuation; roteamento já está aqui (`:180-186`) |
| Suspensão do veredito (D-06) | `report/report.py` (`:240`) **e** `cli.py` (`_motor_pendente`) | — | Duas superfícies em paridade (Analisar + Ranking); ambas migram juntas |
| Rebaixamento DDM → "lente conservadora" + render | `report/report.py` (`relatorio_markdown`) + `cli.py`/`app.py` | `report/presentation.py` | Só exibição (D-06); UX rica é Fase 3 |
| Selo (BSD × preço) | `report/selo.py` | — | **NÃO muda** (D-06); firewall selo↛report preservado |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`dataclasses`, `math`, `statistics`) | 3.14 | Estrutura dos motores puros, PV, médias | Já é o padrão de `ddm.py`/`lentes.py`/`normalizacao.py` |
| numpy | já instalado | OLS/percentis (winsor, log-linear) — só se um motor precisar | Já usado em `growth.py`/`normalizacao.py`/`comparables.py` |

**Nenhuma dependência nova.** [VERIFIED: `pyproject.toml` não lista deps novas necessárias; numpy/pandas já presentes via `.venv`]. Custo-zero e o princípio "só CVM + Yahoo + BCB" já satisfeitos pelos insumos existentes.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Um `core/motores.py` único | Um módulo por motor (`core/rim.py`, `core/normalizado.py`…) | Módulo único agrupa 4 funções pequenas e simétricas; um-por-motor espelha `ddm.py` mas fragmenta. **Discrição do planner** (D-06 discretion). Recomendação: `core/motores.py` único (4 funções puras + dataclasses de resultado). |
| Reusar `ddm.ddm_dois_estagios` direto no crescimento | Extrair helper genérico `pv_fluxo_dois_estagios` | Reuso direto é zero-código-novo e não toca `ddm.py` (só passa lucro no lugar de dividendo). Extrair helper é mais "limpo semanticamente" mas mexe em `ddm.py` (risco ao golden). **Recomendação: reuso direto** — mantém `core/ddm.py` intocado (aceite #5). |

**Installation:** nenhuma. `python -m pytest` (testpaths=`tests`, `pyproject.toml:16`).

## Architecture Patterns

### System Architecture Diagram

```
CompanyData (CVM+Yahoo+BCB, já montado)         cfg (config.yaml, rf resolvido no entry point)
        │                                                │
        ▼                                                ▼
  report.analisar_acao(c, cfg)  ─────── FUNIL ÚNICO ──────────────────────────────►
        │
        ├─ múltiplos / crescimento (g_alto,g_estavel) / lifecycle        [report.py:97-150]
        ├─ CAPM ao vivo → a.ke  (ke_local, Selic ciclo)                  [report.py:152-173]
        ├─ ROTEAMENTO: arq = classificar(c,cfg); motor = REGISTRY[chave] [report.py:180-186]
        │        │
        │        ▼   ◄── NOVO: dispara o motor do arquétipo ───────────────────────┐
        │   ┌─────────────────────────────────────────────────────────────────┐   │
        │   │ financeira → RIM(vpa, roe_val, ke_estrutural, payout, fade)      │   │
        │   │ ciclica    → normalizado(lucro_norm_7-10a, P/L justo)           │  core/motores.py
        │   │ crescimento→ DCF(lpa_val, g_alto, g_est, ke) via ddm_dois_estag. │  (funções puras)
        │   │ holding    → NAV = lentes.vpa(PL_ult, acoes_ult)               │   │
        │   │ pagadora_regulada → ddm (JÁ EXISTE, não muda)                   │   │
        │   └─────────────────────────────────────────────────────────────────┘   │
        │        │ resultado → NOVOS campos em AnaliseAcao (intrínseco + rótulo) ◄──┘
        │        ▼
        ├─ DDM sempre roda (agora "lente conservadora" onde motor≠ddm)   [report.py:188-204]
        ├─ VEREDITO: SUSPENSO se selo_nao_consome_motor (motor≠"ddm")    [report.py:240 ◄ MIGRA]
        │        (mantém prefixo "VERIFICAR" → selo não estampa 'evitar')
        ▼
  relatorio_markdown / CLI / app.py: exibe intrínseco do motor + DDM lente   [report.py:483+]

  PARALELO (Ranking): cli._motor_pendente(c,cfg) ◄── MESMA migração D-06  [cli.py:45-54]
  selo.montar_selo(bsd, veredito, cfg): NÃO MUDA (firewall)               [selo.py — intocado]
```

### Recommended Project Structure
```
src/analista/core/
├── motores.py        # NOVO: rim(), lucro_normalizado(), dcf_crescimento(), nav_contabil()
│                     #       + dataclasses de resultado (ResultadoRIM etc.). Puro, sem I/O.
├── arquetipo.py      # EDIT: ARQUETIPO_MOTOR — 4 None → "rim"/"normalizado"/"dcf"/"nav"
├── ddm.py            # INTOCADO (aceite #5) — reusado por import no crescimento
├── lentes.py         # INTOCADO — vpa() reusado por RIM e NAV
├── capm.py           # EDIT (leve): função do Ke estrutural do RIM (ou derivar no motor)
└── fundamentals.py   # INTOCADO — *_valuation() consumidos pelos motores

src/analista/report/
├── report.py         # EDIT: dispara motores no funil; novos campos AnaliseAcao;
│                     #       MIGRA suspensão :240; render do intrínseco + DDM lente
└── selo.py           # INTOCADO (D-06, firewall)

src/analista/cli.py   # EDIT: _motor_pendente → predicado migrado (paridade D-06)
config.yaml           # EDIT: bloco `motores:` (Ke estrutural do RIM, anos de fade/normalização)
tests/                # NOVO: test_motores.py (golden por motor) + EDIT dos goldens de suspensão
```

### Pattern 1: Motor como função pura config-driven (espelha `ddm.py`)
**What:** cada motor recebe números prontos e devolve um dataclass de resultado (`Number`/`None` never-raise).
**When to use:** todos os 4 motores.
**Example:**
```python
# Source: espelha src/analista/core/ddm.py:78 (ddm_dois_estagios) e :21 (ResultadoDDM)
@dataclass
class ResultadoRIM:
    valor_intrinseco: float
    vpa_base: float
    vp_residual_income: float
    ri_por_ano: List[float]

def rim(vpa0: float, roe0: float, ke: float, retencao: float,
        n: int, fade_para: Optional[float] = None) -> Optional[ResultadoRIM]:
    """RIM com clean surplus e fade do excesso de ROE até Ke (D-02).
    V0 = VPA0 + Σ_{t=1..n} (ROE_t − Ke)·B_{t-1} / (1+Ke)^t
    ROE_t decai linearmente de roe0 até (fade_para or ke); B_t = B_{t-1}·(1 + ROE_t·retencao).
    Excesso → 0 em n ⇒ RI terminal ≈ 0, valor ancorado no VPA (sem perpetuidade de excesso)."""
    if None in (vpa0, roe0, ke, retencao) or n <= 0 or ke <= 0 or vpa0 <= 0:
        return None
    fade_para = ke if fade_para is None else fade_para
    b_prev, vp, ris = vpa0, 0.0, []
    for t in range(1, n + 1):
        frac = (t - 1) / (n - 1) if n > 1 else 1.0
        roe_t = roe0 + (fade_para - roe0) * frac
        ri = (roe_t - ke) * b_prev
        vp += ri / (1 + ke) ** t
        ris.append(ri)
        b_prev = b_prev * (1 + roe_t * retencao)
    return ResultadoRIM(vpa0 + vp, vpa0, vp, ris)
```

### Pattern 2: Reuso do DDM como mecânica de PV de fluxo crescente (crescimento, D-05)
```python
# Source: reuso de src/analista/core/ddm.py:78 SEM tocar o módulo (aceite #5)
# g_alto/g_estavel/ke já estão em report.py:136-173. Alimenta LUCRO no lugar de dividendo:
lucro_inicial = c.lpa_valuation() * (1 + a.g_alto)   # earnings do ano 1 (não × payout!)
res_dcf = ddm.ddm_dois_estagios(
    dpa_inicial=lucro_inicial, g_alto=a.g_alto, n=n, g_estavel=g_estavel, ke=a.ke,
    decrescente=True,   # modelo-H: g decai — conservador, coerente com o projeto
)   # res_dcf.valor_intrinseco = VP do lucro crescente + Gordon terminal sobre lucro
```
**Caveat teórico (Pitfall 4):** capitalizar 100% do lucro E crescer via retenção double-conta o reinvestimento. Rótulo honesto ("DCF sobre lucro, capital-light") mitiga; D-05 aceita lucro≈FCF só para capital-light (WEGE3).

### Pattern 3: Cíclica = lucro normalizado capitalizado (D-04)
```python
# Source: reuso de core/normalizacao.base_normalizada (normalizacao.py:58) + ddm.valor_gordon (ddm.py:37)
lucro_mid = norm.base_normalizada(c.serie("lucro_liquido"), anos_media=10, winsor=0.10)
lpa_mid = mult.lpa(lucro_mid, c.num_acoes.get(c.ultimo_ano()))
# P/L justo via Gordon sobre lucro normalizado (fair P/E = (1+g_est)/(Ke−g_est)); sempre disponível,
# custo-zero, usa o Ke já calculado. Alternativa: fair P/E = 1/Ke (sem crescimento perpétuo).
justo = ddm.valor_gordon(dpa1=lpa_mid, ke=a.ke, g=g_estavel)   # = lpa_mid × fair_PE
```

### Anti-Patterns to Avoid
- **Recalcular ROE/LPA/payout dentro do motor:** viola FIX-04/consistência cross-modo. SEMPRE consumir `roe_valuation()`/`lpa_valuation()`/`payout_valuation()`. [VERIFIED: `fundamentals.py:78-200`]
- **Tocar `core/ddm.py` para o crescimento:** quebra o golden `test_ddm` (aceite #5). Reusar por import, não editar.
- **Deixar a suspensão cair só em `report.py`:** o Ranking (`cli._motor_pendente`) e os goldens (`test_ranking_freio`, `test_arquetipo_roteamento`) usam o MESMO predicado — migrar os três juntos (Pitfall 1).
- **Ke do RIM herdando o CAPM ao vivo (~17%):** derrota o critério #1 (D-01).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| VPA (PL/ações) do RIM e do NAV | Cálculo inline `pl/acoes` | `lentes.vpa(pl, acoes)` (`lentes.py:51`) | Ponto único; `mult._safe_div` trata None/zero |
| PV de fluxo crescente 2 estágios (crescimento) | Loop de desconto novo | `ddm.ddm_dois_estagios` (`ddm.py:78`) | Já testado; Gordon terminal + modelo-H embutidos; NÃO tocar o módulo |
| Gordon simples (P/L justo da cíclica) | `lucro/(ke-g)` inline | `ddm.valor_gordon` (`ddm.py:37`) | Trava `ke>g`, never-raise |
| Lucro médio 7–10a (cíclica) | Média manual | `norm.base_normalizada(serie, anos_media=N)` (`normalizacao.py:58`) ou `serie_lucro_normalizada()` (`fundamentals.py:127`) | Winsor/mediana robusta a exercício atípico já resolvida (FIX-04) |
| ROE/LPA/payout de valuation | Cru do último ano | `c.roe_valuation()` / `c.lpa_valuation()` / `c.payout_valuation()` | Base normalizada, fonte única cross-modo |
| Selo/quadrante | Nova lógica de veredito | `selo.montar_selo` (**intocado**, D-06) | Firewall selo↛report; prefixo "VERIFICAR" já suprime 'evitar' |

**Key insight:** ~90% dos insumos dos 4 motores já existem canonicamente. O trabalho é **compor**, não **calcular** — e wirear sem regredir.

## Runtime State Inventory

Fase de **adição de feature + uma migração de comportamento em código** (predicado de suspensão). Não é rename/rebrand nem migração de dados. Auditoria explícita:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Nenhum — a engine não persiste estado; `CompanyData` é montado on-the-fly da CVM/Yahoo/BCB a cada run. Verificado em `cli.py:_montar` e ausência de DB. | Nenhuma |
| Live service config | Nenhum — sem serviços externos com estado (app é Streamlit stateless + engine pura). | Nenhuma |
| OS-registered state | Nenhum. | Nenhuma |
| Secrets/env vars | Nenhum — custo-zero, APIs públicas sem chave (BCB SGS, Yahoo, CVM). | Nenhuma |
| Build artifacts | `config.yaml` é lido em runtime (não compilado). Novo bloco `motores:` é aditivo. Testes offline carregam `config.yaml` shipado. | Adicionar bloco `motores:` sem tocar blocos existentes (anti-rebaseline) |

**"Migração" desta fase é puramente de código/comportamento**, não de estado: o predicado de suspensão em 3 superfícies (`report.py:240`, `cli.py:45-54`, 2 goldens) muda de "motor é None" para "motor ≠ ddm". Detalhado em Pitfall 1.

## Ke do RIM (D-01) — a alavanca do critério #1

**Nota factual do D-01: CONFIRMADA no código.** [VERIFIED: leitura de `cli.py:113`, `report.py:152-173`, `capm.py:69-71`, `macro.py:87-100`, `config.yaml:61-85`]

- `cli.py:110-115` (comentário FIX-03) resolve `cfg["capm"]["rf_local"] = macro.selic_ciclo_para_capm(selic_fallback, rf_ciclo_anos=10)` — Selic **média 10a through-the-cycle**, não spot. `app.py:245`/`:865` fazem o mesmo (referenciado no brief; a paridade é o padrão do projeto).
- `report.py:161`: `a.ke = capm.ke_local(c.beta, cap["rf_local"], cap["erp_local"])` = `rf + beta×ERP` (`capm.py:71`).
- `config.yaml:66`: `erp_local: 0.06` = ~4,5% mercado maduro (Damodaran) **+ ~1,5% prêmio small-cap/iliquidez**.
- Logo, para um banco (beta ~1,0–1,3, rf ciclo ~0,096) o Ke ao vivo ≈ 0,096 + 1,2×0,06 ≈ **16,8%**. O ~R$16 do DDM vem desse Ke estrutural alto para bancos, **não** de uma Selic do dia. Trocar spot→ciclo já está feito e é insuficiente.

**Opções para o Ke estrutural do RIM (planner escolhe; recomendação abaixo):**

| Opção | Como | Prós | Contras |
|-------|------|------|---------|
| (a) **rf ciclo + ERP de banco (sem small-cap)** — RECOMENDADA | ERP ~0,045 (tira o prêmio small-cap/iliquidez, impróprio para banco large-cap/líquido); `ke_rim = rf_ciclo + beta×erp_banco`, com teto `min(ke_rim, ke_live)` | Objetivo, config-driven, auto-atualiza com a Selic, economicamente justificável (banco não é small-cap) | Com beta 1,24 dá ~15,2% — pode ainda ficar acima de 12,5% se a Selic ciclo estiver alta; usar teto/piso |
| (b) **Ke ancorado no livro (~12,48%)** | Constante config `motores.rim.ke_estrutural: 0.1248` (referência do golden `test_ddm`) | Bate exatamente o ~R$40; simples | Não auto-atualiza; "número mágico" (mitigável com comentário citando o livro Cap. 16/17) |
| (c) **Teto (cap) sobre o Ke ao vivo** | `ke_rim = min(a.ke, teto_config)` (ex.: teto 0,13) | Reusa o Ke existente; nunca infla | Escolha do teto é arbitrária; ainda precisa de um número |

**Recomendação:** (a) como método primário (honesto/auto-atualizável) **combinado com um piso/teto ancorado no livro** — `ke_rim = clamp(rf_ciclo + beta×erp_banco, piso≈0.11, teto≈min(ke_live, 0.14))`. Config-driven em `config.yaml` bloco novo `motores.rim`. O golden do RIM (ITUB4 ~R$40) valida a calibração. **[ASSUMED]** os números exatos de ERP/piso/teto — são discrição do planner (D-01) e devem sair calibrados contra o alvo ~R$40, não cravados aqui.

## Common Pitfalls

### Pitfall 1: A suspensão D-06 cai em 3 superfícies e regride o ITUB4 (ARMADILHA CRÍTICA)
**What goes wrong:** ao trocar `ARQUETIPO_MOTOR[financeira]=None → "rim"`, o predicado `motor is None` vira `False`. Em `report.py:240` (`if a.motor_pendente:`) a suspensão cai → o ITUB4 atravessa para o `elif` do DDM (`report.py:257-278`) e recebe "SOBREAVALIADA" → selo estampa "Evitar" (célula `(Baixa, Caro)`, `selo.py`). O critério de aceite #1 REGRIDE — exatamente o bug que o milestone existe para corrigir.
**Why it happens:** o selo continua consumindo o DDM até a Fase 3 (VER-01); o motor calcula/exibe mas NÃO alimenta o selo (D-06). Se a suspensão sumir antes do selo consumir o motor, abre-se uma janela em que o DDM volta a mandar no veredito de arquétipo não-DDM.
**How to avoid:** migrar o predicado de `motor is None` para **`motor != "ddm"`** (= "o selo ainda não consome o motor deste arquétipo") em TRÊS lugares, no MESMO plano:
1. `report.py:240` — trocar `if a.motor_pendente:` por `if a.motor != "ddm":` (ou um campo novo `a.selo_consome_motor`/`a.veredito_suspenso`). O texto "VERIFICAR — arquétipo … motor …" continua reusando o prefixo que `selo.montar_selo` (`selo.py:119`) já trata (não toca `selo.py`).
2. `cli.py:45-54` (`_motor_pendente`) — mesmo predicado, para o Ranking manter paridade (senão o Ranking passa a estampar preço-alvo por regressão para bancos).
3. Goldens: `test_arquetipo_roteamento.py:120/:135` e `test_ranking_freio.py:122-126` asseveram `motor_pendente is True` para financeira/crescimento — isso muda de propósito (agora o motor EXISTE, mas o veredito segue suspenso). **Atualizar esses asserts é IN-SCOPE e esperado** — eles codificam a semântica "pendente" da Fase 1 que a Fase 2 deliberadamente substitui.
**Warning signs:** `test_arquetipo_roteamento::test_financeira_suspende…` verde por acaso via `motor_pendente` mas o assert real deveria ser `a.veredito.startswith("VERIFICAR")` COM `a.motor == "rim"`. Se o teste continua checando `motor_pendente is True`, a migração está incompleta.

**Semântica recomendada dos campos:** manter `a.motor_pendente` significando literalmente "registry devolveu None" (agora sempre False, já que 5/5 preenchido) OU renomear para `a.veredito_suspenso`/manter e derivar de `motor != "ddm"`. Recomendação: introduzir `a.motor` já resolvido (`report.py:185`) como fonte da verdade e suspender por `a.motor != "ddm"`; deixar `motor_pendente` como legado ou reaproveitar seu significado. Planner decide (D-06 discretion sobre estrutura de código).

### Pitfall 2: Recalcular método dentro do motor quebra consistência cross-modo
**What goes wrong:** um motor calcula ROE/lucro do último ano cru em vez do `*_valuation()` normalizado → Analisar e Ranking divergem para a mesma ação (viola Core Value, `test_consistencia_modos.py`).
**How to avoid:** motores recebem SÓ números já síntese (`roe_valuation()`, `lpa_valuation()`, `base_normalizada()`, `lentes.vpa`). Nunca `c.lucro_liquido.get(ult)` cru dentro de um motor de valuation.
**Warning signs:** `test_consistencia_modos.py` ou `test_vulc3_regressao.py:113-114` falham.

### Pitfall 3: VPA de ano-base errado (RIM e NAV)
**What goes wrong:** usar um `PL`/`num_acoes` de ano faltante → VPA None ou de base inconsistente.
**How to avoid:** resolver pelo `c.ultimo_ano()` como o resto do app: `lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))` — padrão já usado em `lentes.metricas_par` (`lentes.py:161`) e `app.py:957`. Never-raise (`_safe_div`).
**Warning signs:** NAV/RIM None para empresa com dados; verificar `ult`.

### Pitfall 4: DCF de crescimento double-conta reinvestimento
**What goes wrong:** capitalizar 100% do lucro (via `ddm_dois_estagios` alimentado por LPA) E fazê-lo crescer a `g_alto` (que vem de retenção) super-estima — o lucro que cresce é justamente o que NÃO é distribuído.
**How to avoid:** rótulo honesto ("DCF sobre lucro, aproximação capital-light"), preferir o modelo-H (`decrescente=True`, conservador), e travar `g_alto ≤ ke` (já garantido em `report.py:172-173`). Aceite #3 só exige "não cuspir zero/lixo" — não exige precisão de FCF. D-05 aceita a aproximação.
**Warning signs:** intrínseco de crescimento absurdamente acima do mercado (várias vezes o preço) — validar contra WEGE3.

### Pitfall 5: Anti-rebaseline do `config.yaml`
**What goes wrong:** editar blocos existentes (`ddm`, `capm`, `arquetipo`) ao adicionar knobs dos motores → goldens que pinam esses valores flutuam.
**How to avoid:** bloco NOVO `motores:` irmão de `arquetipo:` (padrão já seguido por `selo:`/`score:`/`padroes:`). Nenhuma linha pré-existente tocada.

## Code Examples

### NAV contábil (holding, ENG-05, D-03) — o mais simples
```python
# Source: reuso direto de lentes.vpa (lentes.py:51) — piso patrimonial
ult = c.ultimo_ano()
nav = lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))
# rótulo obrigatório (D-03): "NAV contábil (piso patrimonial), não SOTP por segmento"
```

### Disparo do motor no funil (após report.py:186)
```python
# Source: novo bloco em report.analisar_acao, após a resolução do motor (report.py:184-186)
if a.motor == "rim":
    a.intrinseco_motor = motores.rim(
        vpa0=lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult)),
        roe0=c.roe_valuation(), ke=motores.ke_rim(c.beta, cfg), 
        retencao=(1 - (c.payout_valuation() or 0)), n=cfg["motores"]["rim"]["n_fade"],
    )
elif a.motor == "normalizado":
    ...  # lucro normalizado 7-10a × P/L justo (Gordon sobre lucro / 1-Ke)
elif a.motor == "dcf":
    ...  # ddm.ddm_dois_estagios alimentado por lpa_valuation (Pattern 2)
elif a.motor == "nav":
    ...  # lentes.vpa (acima)
# a.motor == "ddm": nada a fazer — o bloco DDM (report.py:188+) já é o motor primário
a.motor_rotulo = {...}[a.motor]   # rótulo humano exibido no render
```

### Rebaixamento do DDM a "lente conservadora" (render, D-06)
```python
# Source: report.relatorio_markdown (report.py:531+). Onde motor != "ddm", a seção DDM
# ganha um sub-rótulo "(lente conservadora — não é o motor deste arquétipo)". Sem tocar o cálculo.
# O intrínseco do motor do arquétipo é exibido como referência primária (ex.: "RIM: R$ 40,xx").
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| DDM de estágio único como único motor primário | Registry arquétipo→motor (5 motores) | Fase 1 (ENG-01) plugou o registry; Fase 2 preenche os 4 `None` | ITUB4 deixa de ser carimbado por um modelo que não serve |
| Suspensão por `motor_pendente` (registry None) | Suspensão por "selo não consome o motor" (`motor != "ddm"`) | **Esta fase (D-06)** | Impede regressão do ITUB4 quando os motores entram |
| rf = Selic spot | rf = Selic through-the-cycle (média 10a) | FIX-03 (já feito) | Ke ao vivo menos volátil; ainda ~17% p/ banco → RIM precisa de Ke próprio |

**Deprecated/outdated:** nada removido — tudo aditivo. `ddm.py`/`lentes.py`/`selo.py`/`fundamentals.py` permanecem intocados.

## Validation Architecture

> `workflow.nyquist_validation: false` em `.planning/config.json` — a seção Nyquist formal é dispensada. Abaixo, a **estratégia de golden por motor** que a fase deve adicionar, no padrão pytest já dominante (34 arquivos de teste, todos offline/síncronos).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (testpaths=`tests`, `pyproject.toml:14-16`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run | `python -m pytest tests/test_motores.py -x` |
| Full suite | `python -m pytest` (todos offline, fixtures sintéticas — sem rede) |

### Per-engine golden/anchor tests (NOVO `tests/test_motores.py`)
| Motor | Golden puro (função) | Anchor e2e (via `analisar_acao`) |
|-------|----------------------|----------------------------------|
| **RIM (ENG-02)** | `rim(vpa0, roe0, ke, retencao, n)` com inputs tipo-ITUB4 (VPA, ROE ~19,3%, Ke ~12,5%, retenção ~0,53) → intrínseco na faixa ~R$40 e **materialmente > DDM ao vivo (~R$16)**; excesso fade → RI terminal ≈ 0 | Fixture banco (espelha `_financeira`, `test_arquetipo_roteamento.py:57`): `a.intrinseco_motor` populado, `a.motor=="rim"`, veredito ainda "VERIFICAR" (D-06) |
| **Lucro normalizado (ENG-03)** | `base_normalizada(serie_10a_oscilante, anos_media=10)` ignora pico/vale; intrínseco = lucro_mid × P/L justo; **usa média 7–10a, não 1 ano** (fixture com 1 ano 3× dispara a diferença, como `test_vulc3`) | Fixture cíclica (CV alto, ROE oscilante): `a.motor=="normalizado"`, intrínseco sobre lucro médio ≠ sobre lucro do último ano |
| **DCF crescimento (ENG-04)** | `ddm_dois_estagios` alimentado por LPA de compounder (payout baixo, ROE alto) → intrínseco **> 0 e finito** (não zero/lixo); modelo-H < constante | Fixture crescimento (espelha `_petroleo_compounder`): `a.motor=="dcf"`, intrínseco positivo, sem faixa degenerada |
| **NAV holding (ENG-05)** | `lentes.vpa(PL, acoes)` = piso patrimonial; None se PL/ações faltam | Fixture holding sintética: `a.motor=="nav"`, intrínseco == VPA do ano-base |
| **D-06 suspensão (todos)** | — | Para cada arquétipo não-DDM: `a.veredito.startswith("VERIFICAR")` **mesmo com motor plugado**; `selo.montar_selo(bsd_baixo, veredito, cfg).rotulo is None` (não estampa 'evitar') |

### Goldens EXISTENTES a preservar / atualizar
| Test | Ação |
|------|------|
| `tests/test_ddm.py` (R$37,22, Ke 12,48%) | **PRESERVAR verde** — aceite #5; não tocar `core/ddm.py` |
| `tests/test_selo.py` (firewall, cortes, VERIFICAR) | **PRESERVAR** — `selo.py` intocado (D-06) |
| `tests/test_consistencia_modos.py` | **PRESERVAR** — motores consomem `*_valuation()`, não divergem os 3 modos |
| `tests/test_vulc3_regressao.py` (veredito "VERIFICAR", banda) | **PRESERVAR** — VULC3 é têxtil→cíclica ou regulada? Verificar que o novo motor não muda o prefixo esperado ("VERIFICAR"). Se VULC3 rotear p/ cíclica, o veredito segue suspenso (motor≠ddm) → ainda "VERIFICAR" ✓ |
| `tests/test_guardrails_fix06.py` | **PRESERVAR** — banda DDM inalterada |
| `tests/test_arquetipo_roteamento.py:119-135` | **ATUALIZAR** (esperado): `motor_pendente is True` → `a.motor in {"rim","dcf",...}` + `a.veredito.startswith("VERIFICAR")` via novo predicado |
| `tests/test_ranking_freio.py:122-131` | **ATUALIZAR** (esperado): `_motor_pendente(banco) is True` → novo predicado de suspensão (`motor != "ddm"`) |

**Sampling:** rodar `python -m pytest` completo por plano (é rápido, offline). Gate de fase: suite verde antes de `/gsd-verify-work`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Números exatos de ERP-banco/piso/teto do Ke do RIM (para chegar a ~R$40 no ITUB4) | Ke do RIM | Médio — calibração; o golden do RIM valida. Discrição do planner (D-01) |
| A2 | `app.py:245/:865` injeta `selic_ciclo_para_capm` igual ao `cli.py:113` | Nota factual D-01 | Baixo — `cli.py:113` VERIFICADO; app.py é referência do brief/CONTEXT, padrão do projeto (não reli app.py:245 diretamente) |
| A3 | Fair P/E da cíclica via Gordon/(1÷Ke) é aceitável vs. mediana histórica/regressão | Pattern 3 / ENG-03 | Baixo — D-04 dá discrição; regressão P/L exige peer set (indisponível no Analisar single-ticker), então Gordon/1÷Ke é o custo-zero sempre-disponível |
| A4 | VULC3 (`Têxtil e Vestuário`) roteia p/ cíclica ou regulada e segue suspenso ("VERIFICAR") pós-migração | Validation | Médio — se VULC3 rotear p/ um motor≠ddm, o novo predicado mantém "VERIFICAR" ✓; confirmar em execução que `test_vulc3` não regride |
| A5 | Introduzir `core/motores.py` único (vs. um módulo por motor) | Structure | Baixo — discrição do planner (D-06); ambos funcionam |

## Open Questions (RESOLVED)

> **RESOLVED (2026-07-11, plan revision):** as três perguntas abaixo foram decididas e já estão refletidas nos planos 02-01/02-02 — (1) predicado explícito de suspensão migrado para `motor != "ddm"` nas 3 superfícies; (2) render mínimo (uma linha por motor + DDM "lente conservadora"); (3) fade LINEAR do ROE até Ke. Adicionalmente, o alvo "~R$40" do RIM (D-01) foi reconciliado para o número honesto ~R$28 que o modelo conservador (fade a zero, D-02) produz — decisão do usuário, o número honesto vence.

1. **Semântica final do campo de suspensão (`motor_pendente` vs. novo `veredito_suspenso`/`selo_consome_motor`).**
   - What we know: o predicado precisa virar `motor != "ddm"` nas 3 superfícies.
   - What's unclear: renomear o campo (mais claro) vs. reaproveitar `motor_pendente` (menos churn nos consumidores).
   - Recommendation: introduzir predicado explícito e legível; deixar `motor_pendente` refletir literalmente "registry None" (agora sempre False) ou removê-lo se nenhum consumidor restar. Planner decide.

2. **Rótulo/UX exato do intrínseco do motor no render (CLI + app.py:882).**
   - What we know: exibir "arquétipo → motor: R$ x,xx" + DDM como "lente conservadora".
   - What's unclear: quão rico é o render nesta fase (D-06 pede o mínimo; UX rica é Fase 3).
   - Recommendation: uma linha por motor no `relatorio_markdown` (seção Valuation) + o cabeçalho já existente (`report.py:489`, `app.py:882`). Sem bandeira de divergência (Fase 3).

3. **Fade do RIM: linear no ROE vs. no excesso (ROE−Ke).**
   - What we know: D-02 pede fade do excesso até zero em ~7–10a + terminal no VPA.
   - What's unclear: decair ROE_t linearmente (excesso decai não-linear pela composição de B) vs. decair o excesso diretamente.
   - Recommendation: decair ROE_t linearmente até Ke (excesso→0 naturalmente); mais simples e estável. Golden calibra.

## Environment Availability

Sem dependências externas novas. Tudo stdlib + numpy/pandas já instalados. Testes offline (fixtures sintéticas, sem rede).

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | engine | ✓ | 3.14 (`.venv`) | — |
| numpy | normalizacao/growth (já usados) | ✓ | instalado | — |
| pytest | goldens | ✓ | instalado | — |

## Sources

### Primary (HIGH confidence) — código-fonte inspecionado nesta sessão
- `src/analista/core/arquetipo.py` (`:45` registry, `:121` classificar) — [VERIFIED]
- `src/analista/core/ddm.py` (`:37` valor_gordon, `:78` ddm_dois_estagios, `:118` matriz) — [VERIFIED]
- `src/analista/core/lentes.py` (`:51` vpa, `:37` graham, `:75` bazin) — [VERIFIED]
- `src/analista/core/capm.py` (`:69` ke_local, `:62` ke_eua_ajustada) — [VERIFIED]
- `src/analista/core/fundamentals.py` (`:78` payout_valuation, `:122` base_lucro_normalizada, `:127` serie_lucro_normalizada, `:132` lpa_valuation, `:137` roe_valuation) — [VERIFIED]
- `src/analista/core/normalizacao.py` (`:58` base_normalizada, `:94` serie_winsorizada) — [VERIFIED]
- `src/analista/core/growth.py` (`:51` log-linear, `:78` por_fundamentos) — [VERIFIED]
- `src/analista/core/comparables.py` (regressão P/L=f(DP,ROE); precisa de peer set) — [VERIFIED]
- `src/analista/report/report.py` (`:23` AnaliseAcao, `:92` analisar_acao, `:180-186` roteamento, `:188-204` DDM, `:240-256` suspensão, `:483+` render) — [VERIFIED]
- `src/analista/report/selo.py` (firewall, `:119` montar_selo, VERIFICAR overlay) — [VERIFIED]
- `src/analista/cli.py` (`:45-54` _motor_pendente, `:57` alvo_regressao_confiavel, `:113` rf ciclo) — [VERIFIED]
- `src/analista/ingest/macro.py` (`:47` spot, `:87` selic_ciclo_para_capm) — [VERIFIED]
- `config.yaml` (`:60-94` capm/ddm, `:171-203` arquetipo) — [VERIFIED]
- `tests/test_ddm.py`, `test_arquetipo_roteamento.py`, `test_vulc3_regressao.py`, `test_ranking_freio.py`, grep de suspensão — [VERIFIED]
- `.planning/BRIEF-motor-arquetipo.md`, `REQUIREMENTS.md`, `02-CONTEXT.md` — [CITED]

### Secondary (MEDIUM confidence)
- `app.py:882/:957` (render do arquétipo + uso de `lentes.vpa` no ano-base) — grep VERIFIED; código completo não lido linha a linha.

### Tertiary (LOW confidence)
- Nenhuma — todas as afirmações materiais têm âncora no código.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — nenhuma dep nova; insumos existem e foram lidos.
- Architecture/wiring: HIGH — funil, registry, AnaliseAcao e pontos de suspensão inspecionados com âncoras.
- Fórmulas dos motores: HIGH (livro-texto) — RIM/normalizado/DCF/NAV são padrão; caveat do double-count do DCF explicitado.
- Ke do RIM (calibração numérica): MEDIUM — a nota factual do D-01 foi CONFIRMADA no código; os números exatos do Ke estrutural são calibráveis contra o golden (A1).
- Pitfall D-06 (3 superfícies): HIGH — os 3 pontos e os 2 goldens que quebram foram localizados por leitura direta.

**Research date:** 2026-07-11
**Valid until:** ~30 dias (código estável; sem dependências fast-moving)
