# Phase 1: Classificador de Arquétipo + Roteamento - Research

**Researched:** 2026-07-11
**Domain:** Roteamento de motor de valuation por arquétipo de negócio (classificação + registry) dentro do funil `report.analisar_acao`
**Confidence:** HIGH (código lido linha a linha; 338 testes verdes na baseline; setores e âncoras verificados contra os dados CVM cacheados)

## Summary

A Fase 1 é **puramente interna** ao pacote `analista`: nenhum dado novo, nenhuma dependência externa nova, nenhum motor novo. O trabalho é (1) um **classificador** que lê sinais que `CompanyData` já expõe, (2) um **registry arquétipo→motor** (dict módulo-nível), e (3) inserir o roteamento no funil `report.analisar_acao` **entre o CAPM (`report.py:113-134`) e a montagem do DDM (`report.py:136-152`)**, mais campos aditivos em `AnaliseAcao` e a mudança de comportamento D-04 ("suspende veredito / rebaixa DDM quando o motor do arquétipo não existe"). `core/ddm.py` e `report/selo.py` **não são tocados** nesta fase. [VERIFIED: leitura de report.py, selo.py, fundamentals.py, cvm.py, build.py]

O achado mais importante e não-óbvio: **o `setor` (string do `SETOR_ATIV` da CVM) É confiável para os arquétipos fortes** — `ITUB4`/`BBAS3`/`SANB11` = `'Bancos'`, `BBSE3`/`CXSE3` = `'... Seguradoras e Corretoras'`, `ITSA4` = `'... Intermediação Financeira'` — porque são categorias de **registro legal**, não rótulos de negócio. O que é não-confiável é o rótulo de setores **industriais/cíclicos** (VULC3 caiu em 'Têxtil'). Logo o híbrido D-02 se justifica exatamente assim: **hard-route por string de setor para financeira/regulada; quantitativo para todo o resto.** [VERIFIED: pandas sobre `data/cvm/cad_cia_aberta.csv`]

O segundo achado crítico: **`eh_concessionaria` (build.py:68) tem um falso-positivo real** — `'Petróleo e Gás'` casa a substring `'Gás'` → `PETR4` seria roteado como pagadora regulada e **rodaria o DDM como primário** (aberração silenciosa exatamente do tipo que o milestone combate). Precisa de guarda no hard-route. [VERIFIED: reproduzido em Python]

**Primary recommendation:** Criar `core/arquetipo.py` (classificador puro `classificar(c) -> ResultadoArquetipo` + registry `ARQUETIPO_MOTOR`), dirigir o hard-route por `c.setor` string-match + `eh_concessionaria` **com guarda anti-Petróleo**, refinar o resto por ROE/retenção/oscilação de lucro reusando `roe_valuation`/`payout_valuation`/`serie_lucro_normalizada`/`lifecycle`, e no `report.py` inserir o roteamento após `:134`, adicionando campos aditivos a `AnaliseAcao` e a suspensão D-04 no bloco do veredito (`:184-207`) — tudo do lado do report, sem tocar o firewall selo↛report.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 (calibração do fallback):** Fronteiriço dispara **só em conflito real de sinais** — quando setor e refino quantitativo discordam, ou quando as métricas se contradizem entre si. Quando setor + quantitativo concordam, **crava**. Meta: ~85% cravados / ~15% fronteiriços.
- **D-02 (setor vs quantitativo):** Roteamento **híbrido**. Setores de **alta confiança** roteiam direto (hard-route): **banco** (detecção CVM por códigos de conta), **seguradora**, e **regulada** (via `eh_concessionaria`). Todo o resto passa pelo **refino quantitativo** (ROE/retenção/oscilação de margem/lucro). O rótulo genérico da CVM **não** é confiável (VULC3→'Têxtil'), então fora dos setores fortes o quantitativo decide.
- **D-03 (taxonomia — 5 chaves 1:1 com motores):** `financeira`→RIM (banco+seguradora juntos), `pagadora_regulada`→DDM (plugado nesta fase), `ciclica`→lucro normalizado (F2), `crescimento`→DCF (F2), `holding`→NAV/SOTP (F2). Sem separar banco↔seguradora; sem "compounder" distinto de crescimento. Nomes exatos das chaves a critério do planner, desde que 1:1 com os 5 motores.
- **D-04 (motor ausente na F1):** **Suspende o veredito primário e rebaixa o DDM.** Quando o arquétipo aponta para motor inexistente (RIM/normalizado/DCF/SOTP), a ferramenta **NÃO roda o DDM como se fosse o motor certo**: exibe "arquétipo X → motor Y (chega na Fase 2)", mostra Graham/Bazin como referência, e **não estampa selo 'evitar'**. A pagadora regulada (TAEE11), cujo DDM **existe**, roteia normalmente e mantém números/veredito **idênticos** aos de hoje.

### Claude's Discretion
- Nomes exatos das chaves do registry e assinatura da função classificadora.
- Thresholds numéricos do refino quantitativo (ROE "alto e estável", oscilação de margem/lucro para cíclica, retenção para compounder) — o researcher deriva a partir dos sinais disponíveis.
- Forma exata da exposição do resultado (campos novos em `AnaliseAcao`: arquétipo, motor, confiança/`fronteiriço`, candidatos) e a renderização mínima no report/CLI. UX rica fica para a Fase 3.
- Como estruturar o registry (dict módulo-nível, dataclass, etc.).

### Deferred Ideas (OUT OF SCOPE)
- Thresholds finos e validação empírica / backtesting contra retorno futuro (BACKTEST-01, deferido).
- Exposição rica do "porquê" da classificação na UI (é da Fase 3; aqui só exposição mínima).
- Separar banco de seguradora e compounder de crescimento como chaves distintas (recusado em D-03).
- Implementar RIM/normalizado/DCF/SOTP (Fase 2); ensemble + bandeira de divergência + guarda-corpos + refatoração do selo (Fase 3).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ARQ-01 | Classificar o arquétipo do negócio **antes de valuar** (setor CVM como filtro grosso + refino quantitativo por ROE/retenção/oscilação de margem-lucro) | Sinais prontos em `CompanyData`: `setor`, `eh_concessionaria`, `roe_valuation()`, `payout_valuation()`, `serie_lucro_normalizada()`, `serie('lucro_liquido')`, `margem_valuation()`, `estagio` via `lifecycle.classificar_estagio`. Ponto de inserção `report.py:134→136`. Ver **Standard Stack** e **Sinais do Classificador**. |
| ARQ-02 | **Fallback honesto** — confiança baixa → marca fronteiriço + guarda 2–3 lentes candidatas | Modelar `ResultadoArquetipo` com `fronteirico: bool` e `candidatos: list`. Regra de conflito D-01 detalhada em **Pattern 3**. |
| ENG-01 | **Registry arquétipo→motor primário** consumido pela agregação | Dict módulo-nível `ARQUETIPO_MOTOR` em `core/arquetipo.py`; só `pagadora_regulada`→"ddm" implementado, resto → `None`/"pendente_fase_2". Ver **Pattern 2**. |
| ENG-06 | **DDM permanece** primário para pagadora madura/regulada (TAEE11) — não quebrar o que funciona | Hard-route `eh_concessionaria`→`pagadora_regulada`→DDM roda o bloco `report.py:136-152` **inalterado**; `test_ddm`, `test_consistencia_modos`, `test_guardrails_fix06` continuam verdes. **Guarda anti-Petróleo obrigatória** (ver Pitfall 1). |
</phase_requirements>

## Architectural Responsibility Map

Aplicação single-tier (engine Python + Streamlit); os "tiers" aqui são **camadas de módulo**, e a fronteira que importa é **engine pura ↔ apresentação**.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Classificar arquétipo (sinais → chave) | `core/arquetipo.py` (novo, engine pura) | — | Espelha `core/lifecycle.py`: função pura sobre `CompanyData`, sem rede, testável por golden. Consistência cross-modo por construção (mesma fonte que Analisar/Ranking). |
| Registry arquétipo→motor | `core/arquetipo.py` (dict módulo-nível) | — | ENG-01 pede um mapa único; mantê-lo junto do classificador evita import cruzado report↔core desnecessário. |
| Roteamento (escolher se DDM roda como primário) | `report/report.py` `analisar_acao` (`:134→136`) | — | O funil é o **ponto único** de valuation (padrão estabelecido). Roteamento entra aqui, não espalhado. |
| Suspensão de veredito / rebaixar DDM (D-04) | `report/report.py` bloco veredito (`:184-207`) | — | Do lado do report, preservando o firewall selo↛report (selo só recebe primitivos). |
| Exposição (arquétipo/motor/fronteiriço) | `AnaliseAcao` dataclass (`report.py:22`) + render `:410` + CLI/app | `report/presentation.py` | Campos aditivos read-only; render mínimo (D-04/discricionário). |
| Detecção "é financeira" (banco/seguradora) | `c.setor` string-match (já disponível) | `ingest/cvm.py` + `build.py` (opcional, novo flag) | Setor legal é confiável p/ financeiras (verificado). Account-code detector é reforço opcional com novo encanamento — ver **Open Question 1**. |

## Standard Stack

Fase 100% interna — **zero dependências novas**. O "stack" é o que já existe no repo. [VERIFIED: `requirements.txt`, imports lidos]

### Core (reaproveitado, não instalar nada)
| Módulo/API | Onde | Uso na Fase 1 | Por que é o padrão |
|------------|------|---------------|--------------------|
| `CompanyData` | `core/fundamentals.py:20` | Fonte única de todos os sinais | Já consumido por Analisar/Garimpo/Ranking → classificar sobre ele garante consistência cross-modo (Core Value) |
| `roe_valuation()` | `fundamentals.py:137` | ROE-síntese normalizado (sinal de qualidade) | Método canônico FIX-04; **None** quando falta PL do ano anterior |
| `payout_valuation()` | `fundamentals.py:78` | Retenção = `1 − payout` (sinal compounder) | Mediana s/ clamp; canônico; pode ser >1.0 (TAEE ≈2.16) |
| `serie_lucro_normalizada()` | `fundamentals.py:127` | Série winsorizada p/ CAGR / estabilidade | Já usado no `g_historico` |
| `serie("lucro_liquido")` | `fundamentals.py:63` | Série **crua** p/ medir oscilação (cíclica) | Crua de propósito: a oscilação é o sinal |
| `margem_valuation()` | `fundamentals.py:152` | ML normalizada (número único) | Espelha `roe_valuation`; **None** se faltar base |
| `eh_concessionaria` | campo em `CompanyData` (build.py:68) | Hard-route `pagadora_regulada` | Já deriva Energia/Saneamento/Água/Gás — **mas tem falso-positivo, ver Pitfall 1** |
| `setor` (string) | `CompanyData.setor` (build.py:56 ← `universe.resolver`) | Hard-route financeira/seguradora | `SETOR_ATIV` legal-confiável p/ financeiras (verificado) |
| `lifecycle.classificar_estagio()` | `lifecycle.py:22` | Sinal crescimento×maturidade | Heurística de 6 estágios já calculada em `report.py:109` |
| `beta`, `patrimonio_liquido` | campos `CompanyData` | Contexto/degradação | `beta: Optional[float]`; PL é `Dict[int,float]` |
| `normalizacao.serie_winsorizada` / `median` | `normalizacao.py:94` / stdlib | Medir dispersão sem hand-roll | Primitiva pura já existe |

### Supporting
| Módulo | Onde | Quando usar |
|--------|------|-------------|
| `ddm.ddm_dois_estagios(dpa_inicial, g_alto, n, g_estavel, ke, decrescente=False, tributacao=0.0)` | `core/ddm.py:78` | Só para `pagadora_regulada`: bloco `report.py:136-152` roda inalterado (ENG-06) |
| `lentes.preco_justo_graham(lpa, vpa)` / `lentes.preco_teto_bazin(dpa_med)` | `core/lentes.py:37/75` | Referência p/ D-04 (app.py já as exibe em `:943-965`; CLI markdown **não** as mostra hoje) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `core/arquetipo.py` (novo módulo em `core/`) | classificador dentro de `report.py` | `core/` mantém a engine pura testável isolada (espelha `lifecycle.py`, `screening.py`); embutir no report acopla e dificulta golden direto. **Recomendado: `core/arquetipo.py`.** |
| Hard-route por `c.setor` string | novo flag `eh_financeira` em CVM (2.08 vs 2.03) | String já disponível e verificada confiável p/ financeiras; flag CVM é reforço com encanamento novo (cvm→build→CompanyData). **Recomendado: string agora; flag como Open Question.** |
| `dict` módulo-nível para o registry | `Enum` + `dataclass` | Dict é o mais simples e o que o CONTEXT permite; um `Enum` de arquétipos evita typos de string. **Recomendado: `Enum`/constantes p/ as 5 chaves + dict registry.** |

**Installation:** Nada a instalar.
```bash
# nenhuma dependência nova — Fase 100% interna
```

**Version verification:** N/A (sem pacotes novos). Stack existente confirmado em `requirements.txt` (pandas, numpy, pyyaml, yfinance, requests, tabulate, streamlit; pytest para testes). [VERIFIED: requirements.txt lido]

## Architecture Patterns

### System Architecture Diagram

```
                          report.analisar_acao(c, cfg)   [report.py:53]
                                        │
   múltiplos :64 → crescimento :80-102 → lifecycle a.estagio :109 → CAPM a.ke :113-134
                                        │
                    ┌───────────────────┴────────────────────┐
                    │   *** NOVO: ROTEAMENTO (após :134) ***  │
                    │   arq = arquetipo.classificar(c)        │
                    │   a.arquetipo, a.motor, a.fronteirico,  │
                    │   a.arquetipo_candidatos = ...          │
                    │   motor = ARQUETIPO_MOTOR[arq.chave]    │
                    └───────────────────┬────────────────────┘
                                        │
                       motor == "ddm" (pagadora_regulada)?
                          │ sim                       │ não  (RIM/normalizado/DCF/SOTP)
                          ▼                           ▼
         DDM roda como HOJE (:136-152)     DDM NÃO roda como primário (D-04)
         veredito de preço normal          → a.motor_pendente = True
         (TAEE11 idêntico)                  → veredito suspenso: "arquétipo X →
                          │                    motor Y chega na Fase 2"; Graham/
                          │                    Bazin como referência; sem selo 'evitar'
                          └───────────────┬───────────┘
                                          ▼
              veredito :170-207 (bloco condicionado ao motor)
                                          ▼
              read técnico :240-301 (inalterado) → selo :303-311 (inalterado,
              recebe o veredito já ajustado — firewall preservado)
                                          ▼
                                   return AnaliseAcao
```

O classificador **lê apenas** `CompanyData` (sinais já calculados); é engine pura, sem rede. O ponto de decisão único é o roteamento inserido após o Ke.

### Recommended Project Structure
```
src/analista/
├── core/
│   ├── arquetipo.py        # NOVO: classificar() + ResultadoArquetipo + ARQUETIPO_MOTOR (registry)
│   ├── fundamentals.py      # inalterado (fonte dos sinais)
│   ├── lifecycle.py         # inalterado (sinal reusado)
│   └── ddm.py               # NÃO TOCAR (ENG-06 / test_ddm golden)
├── report/
│   ├── report.py            # EDITAR: inserir roteamento :134→136; campos em AnaliseAcao :22;
│   │                        #         condicionar veredito :184-207 ao motor (D-04); render :410 mínimo
│   └── selo.py              # NÃO TOCAR (firewall selo↛report; refatoração é Fase 3)
└── ingest/
    ├── build.py             # (opcional) novo flag eh_financeira — ver Open Question 1
    └── cvm.py               # (opcional) expor template financeiro — ver Open Question 1
tests/
└── test_arquetipo.py        # NOVO: golden do classificador (âncoras ITUB4/TAEE11/VALE3/WEGE3/PETR4)
```

### Pattern 1: Classificador puro sobre CompanyData (espelha lifecycle.py)
**What:** Função pura `classificar(c: CompanyData) -> ResultadoArquetipo`, sem rede, sem cfg obrigatório (ou cfg só para thresholds tunáveis).
**When to use:** Sempre — é o coração ARQ-01.
**Example:**
```python
# core/arquetipo.py  — Source: padrão de core/lifecycle.py e core/screening.py (repo)
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from .fundamentals import CompanyData

# 5 chaves 1:1 com os motores (D-03). Constantes evitam typo de string.
FINANCEIRA = "financeira"                 # -> RIM (Fase 2)
PAGADORA_REGULADA = "pagadora_regulada"   # -> DDM (plugado nesta fase)
CICLICA = "ciclica"                       # -> lucro normalizado (Fase 2)
CRESCIMENTO = "crescimento"               # -> DCF (Fase 2)
HOLDING = "holding"                       # -> NAV/SOTP (Fase 2)

ARQUETIPO_MOTOR = {                        # registry ENG-01
    FINANCEIRA: None,                      # motor pendente (Fase 2)
    PAGADORA_REGULADA: "ddm",              # ÚNICO implementado na Fase 1 (ENG-06)
    CICLICA: None,
    CRESCIMENTO: None,
    HOLDING: None,
}

@dataclass
class ResultadoArquetipo:
    chave: str                             # uma das 5 constantes
    fronteirico: bool = False              # ARQ-02
    candidatos: List[str] = field(default_factory=list)  # 2-3 chaves quando fronteiriço
    confianca: str = "alta"                # "alta" (cravado) | "baixa" (fronteiriço)
    sinais: dict = field(default_factory=dict)  # {roe, retencao, cv_lucro, estagio, ...} p/ debug/Fase 3
```

### Pattern 2: Registry consumido no funil (ENG-01)
**What:** `report.py` lê `ARQUETIPO_MOTOR[arq.chave]` e ramifica.
**When to use:** No ponto de inserção `report.py:134→136`.
**Example:**
```python
# report.py, logo após a trava g_alto ≤ Ke (:133-134), ANTES do bloco DDM (:136)
# Source: ponto de inserção definido em CONTEXT canonical_refs
from ..core import arquetipo as arq_mod

arq = arq_mod.classificar(c)
a.arquetipo = arq.chave
a.arquetipo_fronteirico = arq.fronteirico
a.arquetipo_candidatos = arq.candidatos
motor = arq_mod.ARQUETIPO_MOTOR.get(arq.chave)
a.motor = motor or "pendente_fase_2"
a.motor_pendente = motor is None          # dirige a suspensão D-04 no veredito
```
> **Importante:** o bloco DDM (`:136-152`) **continua rodando sempre** — ele popula `a.ddm_constante`/`a.ddm_h`/`a.sensibilidade` que a UI já exibe como "lente". A mudança D-04 é **só no veredito** (`:184-207`): quando `a.motor_pendente`, não estampar SUBAVALIADA/SOBREAVALIADA como veredito primário. Isso mantém `test_guardrails_fix06.test_banda_vem_da_matriz_de_sensibilidade` verde (a banda/matriz seguem existindo) sem contradizer D-04.

### Pattern 3: Árvore de decisão híbrida (D-01/D-02)
**What:** Hard-route de alta confiança → senão refino quantitativo → detecção de conflito → fronteiriço.
**When to use:** Dentro de `classificar()`.
**Example (pseudocódigo prescritivo):**
```python
def classificar(c: CompanyData) -> ResultadoArquetipo:
    setor = (c.setor or "").lower()

    # (1) HARD-ROUTE de alta confiança (D-02) — setor legal é confiável p/ financeiras
    FINANCEIRO_TOKENS = ("banco", "intermediação financeira", "intermediacao financeira",
                         "seguradora", "arrendamento mercantil", "crédito imobiliário",
                         "credito imobiliario", "factoring", "securitização",
                         "securitizacao", "bolsas de valores")
    if any(tok in setor for tok in FINANCEIRO_TOKENS):
        return ResultadoArquetipo(FINANCEIRA, confianca="alta")

    # (2) HARD-ROUTE regulada — eh_concessionaria COM guarda anti-Petróleo (Pitfall 1)
    if c.eh_concessionaria and "petróleo" not in setor and "petroleo" not in setor:
        # opcional D-01: veto quantitativo se a margem/lucro oscilar como cíclica
        return ResultadoArquetipo(PAGADORA_REGULADA, confianca="alta")

    # (3) REFINO QUANTITATIVO (todo o resto) — ROE / retenção / oscilação
    roe = c.roe_valuation()                     # pode ser None
    payout = c.payout_valuation()               # pode ser None / >1.0
    retencao = (1 - payout) if payout is not None else None
    cv = _cv_lucro(c.serie("lucro_liquido"))    # coef. de variação da série CRUA
    estagio = c.estagio  # ou recomputar via lifecycle (report.py já calcula em a.estagio)

    candidatos = []
    if cv is not None and cv >= 0.40:           # oscilação violenta → cíclica
        candidatos.append(CICLICA)
    if roe is not None and roe >= 0.15 and retencao is not None and retencao >= 0.50:
        candidatos.append(CRESCIMENTO)          # ROE alto + retenção alta = compounder
    if not candidatos:
        candidatos.append(PAGADORA_REGULADA)    # madura estável default → DDM elegível

    # (4) CONFLITO REAL (D-01) → fronteiriço; senão crava o único candidato
    if len(set(candidatos)) >= 2:
        return ResultadoArquetipo(candidatos[0], fronteirico=True,
                                  candidatos=list(dict.fromkeys(candidatos)),
                                  confianca="baixa")
    return ResultadoArquetipo(candidatos[0], confianca="alta")
```
> Os thresholds (0.40, 0.15, 0.50) são **iniciais e defensáveis, não calibrados** — ver seção **Thresholds** e **Assumptions Log**. Devem morar no `config.yaml` (bloco novo `arquetipo:`, irmão de `selo:`/`score:`), seguindo o padrão config-driven do repo (Pitfall 4).

### Anti-Patterns to Avoid
- **Recalcular sinais no classificador** (ex.: ROE cru por ano) em vez de consumir `roe_valuation()`/`payout_valuation()` — quebra a consistência cross-modo (Core Value / `test_consistencia_modos`).
- **Fazer o hard-route regulada confiar cegamente em `eh_concessionaria`** — deixa PETR4 rodar DDM como primário (aberração). Guarda obrigatória.
- **Tocar `core/ddm.py` ou `report/selo.py`** — quebra `test_ddm` (golden R$37,22) e o firewall `test_selo`.
- **Mudar prefixos de veredito existentes** (SUBAVALIADA/SOBREAVALIADA/NO INTERVALO/VERIFICAR) sem atualizar `selo.faixa_do_veredito` (`selo.py:88`) E `report._veredito_token` (`report.py:355`) juntos — ver Pitfall 3.
- **Marcar tudo como fronteiriço** (conservadorismo) ou nunca duvidar (agressividade) — viola a meta ~85/15 de D-01.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Base de qualidade (ROE/LPA/margem) | ROE cru do último ano | `c.roe_valuation()`, `c.margem_valuation()` | Normalização winsor/mediana já resolvida (FIX-04); consistência cross-modo |
| Retenção / payout sustentável | Média manual de payout | `c.payout_valuation()` (`1 − payout`) | Mediana s/ clamp canônica (PAY-01); mesma que o DDM usa |
| Suavizar série p/ estabilidade | Loop de winsorização | `normalizacao.serie_winsorizada()` / `base_normalizada()` | Primitiva pura testada (`test_normalizacao`) |
| Estágio crescimento×maturidade | Nova heurística de ciclo | `lifecycle.classificar_estagio()` (já em `a.estagio`) | 6 estágios já calibrados e exibidos |
| Detecção de setor regulado | Nova lista de setores | `c.eh_concessionaria` (+ guarda) | Já derivado em build.py:68 |
| Dispersão (cíclica) | Fórmula ad-hoc de variância | `statistics.stdev/mean` (CV) ou comparar cru vs `serie_lucro_normalizada` | stdlib; um helper pequeno `_cv_lucro` é aceitável (não há primitiva "oscilação" pronta) |

**Key insight:** Quase todo sinal de que o classificador precisa **já existe como método canônico**. O único helper genuinamente novo é uma medida de **oscilação** da série de lucro/margem (não há primitiva pronta) — mantê-lo pequeno e puro em `core/arquetipo.py`, reusando `statistics`/`normalizacao`.

## Runtime State Inventory

> Fase greenfield (feature nova dentro do código; sem rename/migração de dados). Preenchido por completude.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — não há datastore de estado; CVM/Yahoo/BCB são cache de arquivos read-only (`data/cvm/*.zip`, `data/cache/`). Classificação é computada em memória a cada análise. | Nenhuma |
| Live service config | None — sem serviço externo com estado. `data/ticker_map.json` é override display-only versionado em git. | Nenhuma |
| OS-registered state | None — sem tasks/daemons. | Nenhuma |
| Secrets/env vars | None — Fase não lê secrets; engine é offline/determinística. | Nenhuma |
| Build artifacts | `pyproject.toml` define o pacote `analista`; novo módulo `core/arquetipo.py` é importado normalmente (namespace package, sem reinstalar). | Nenhuma |

**Nada encontrado que exija migração** — verificado por leitura do repo (sem banco, sem serviço com estado, sem registro de OS).

## Common Pitfalls

### Pitfall 1: `eh_concessionaria` casa 'Gás' dentro de 'Petróleo e Gás' → PETR4 vira pagadora regulada
**What goes wrong:** O hard-route `pagadora_regulada` roda o **DDM como primário** para Petrobras (cíclica de commodity), produzindo exatamente a aberração silenciosa que o milestone combate.
**Why it happens:** `build.py:68` faz `any(t.lower() in setor.lower() for t in ("Energia","Saneamento","Água","Gás"))`; `"gás"` é substring de `"petróleo e gás"`. [VERIFIED: reproduzido — `eh_concessionaria('Petróleo e Gás') == True`]
**How to avoid:** No hard-route, exigir `c.eh_concessionaria and "petróleo" not in setor` (guarda barata). Alternativa mais limpa: corrigir a tupla em build.py para casar `"Gás"` só como token isolado (regex `\bgás\b` já é o padrão em `universe._norm`), mas isso mexe em `build.py` e pode reverberar — a guarda no classificador é mais cirúrgica para a Fase 1.
**Warning signs:** PETR4/PETR3 roteando `pagadora_regulada` num teste de fumaça; qualquer ticker "Petróleo e Gás" com veredito de preço primário.

### Pitfall 2: `roe_valuation()`/`margem_valuation()`/`payout_valuation()` retornam **None**
**What goes wrong:** Comparações `roe >= 0.15` levantam `TypeError` ou classificam errado quando o sinal é None (falta PL do ano anterior, série vazia, etc.).
**Why it happens:** `roe_valuation` retorna None sem PL do ano-1 (`fundamentals.py:148-150`); `payout_valuation` None em série vazia; `beta` é `Optional[float]`. [VERIFIED: código lido]
**How to avoid:** Guardar cada sinal com `is not None` antes de comparar (como no pseudocódigo). Definir o comportamento de degradação: sem sinais suficientes → `pagadora_regulada` default OU `fronteirico=True` com candidatos vazios/`[PAGADORA_REGULADA]`. Nunca deixar None cair silenciosamente num ramo errado.
**Warning signs:** Empresa com 1 ano de dados (`VAZIA3` em `test_guardrails_fix06`) — o classificador tem de degradar sem exceção, espelhando o DDM que não roda.

### Pitfall 3: mexer no veredito quebra o par `faixa_do_veredito` ↔ `_veredito_token`
**What goes wrong:** Se D-04 introduzir um **novo prefixo** de veredito (ex.: "AGUARDANDO MOTOR — …"), o selo (`faixa_do_veredito`, `selo.py:88`) devolve None e a matriz fundamento×técnico (`report._veredito_token`, `:355`) não casa → `test_selo`/`test_report` podem falhar e a UI perde o rótulo.
**Why it happens:** Dois parsers de prefixo independentes (firewall selo↛report) precisam ser mantidos em sincronia manualmente. [VERIFIED: `test_selo.test_faixa_do_veredito_prefixos`]
**How to avoid:** Preferir **suprimir/rebaixar** o veredito de preço (deixar `a.veredito` sem prefixo de preço, ou reusar o padrão **"VERIFICAR — …"** que o selo já trata como overlay `verificar=True` sem faixa/rótulo, `selo.py:119`). Reusar "VERIFICAR" é o caminho de menor risco: `montar_selo` já sabe suprimir o rótulo de preço nesse caso, e é semanticamente correto ("motor certo ainda não existe"). Se um prefixo novo for mesmo necessário, atualizar `faixa_do_veredito` + `_veredito_token` **juntos** e cobrir em teste.
**Warning signs:** `test_selo` falhando em `test_faixa_do_veredito_prefixos` ou `test_overlay_verificar`; rótulo de quadrante sumindo no app para tickers roteados.

### Pitfall 4: hardcode de thresholds espalhado → rebaseline dos goldens
**What goes wrong:** Cravar 0.15/0.40/0.50 no código dificulta ajuste e pode fazer goldens flutuarem quando recalibrados.
**Why it happens:** O repo tem forte convenção config-driven (`selo:`, `score:`, `padroes:` todos em `config.yaml`).
**How to avoid:** Bloco novo `arquetipo:` em `config.yaml` (irmão de `selo:`), lido pelo classificador; goldens pinam via `_cfg()`. Não tocar nenhum bloco existente do config (anti-rebaseline).
**Warning signs:** Números mágicos no `core/arquetipo.py`; testes de outras fases mudando de valor.

### Pitfall 5: TAEE11 (pagadora regulada) precisa ficar **idêntica** — regressão silenciosa
**What goes wrong:** Qualquer alteração no caminho DDM (mesmo aditiva) que mude `a.veredito`/`a.vmin`/`a.vmax`/`a.multiplos` da regulada viola ENG-06 e o critério de aceite #2.
**Why it happens:** O roteamento é inserido no meio do funil; é fácil condicionar algo que também afeta o ramo DDM.
**How to avoid:** Ramo `motor == "ddm"` deve executar o bloco `:136-207` **exatamente como hoje**. Adicionar um golden `test_arquetipo` com a fixture `_empresa_solida` (setor "Energia Elétrica", já usada em `test_consistencia_modos`/`test_selo`) afirmando: `arquetipo == pagadora_regulada`, `motor == "ddm"`, `fronteirico == False`, e `veredito` idêntico ao de `analisar_acao` pré-roteamento.
**Warning signs:** `test_consistencia_modos`, `test_selo.test_analisar_acao_popula_selo_coerente` ou `test_guardrails_fix06` mudando.

## Code Examples

### Classificar e rotear no funil (ponto de inserção exato)
```python
# report.py — inserir ENTRE :134 (trava g_alto ≤ Ke) e :136 (comentário "--- DDM ---")
# Source: report.py:113-152 (lido) + CONTEXT D-02/D-04
arq = arquetipo.classificar(c)
a.arquetipo = arq.chave
a.arquetipo_fronteirico = arq.fronteirico
a.arquetipo_candidatos = arq.candidatos
motor = arquetipo.ARQUETIPO_MOTOR.get(arq.chave)
a.motor = motor or "pendente_fase_2"
a.motor_pendente = (motor is None)
# ... bloco DDM :136-152 roda como hoje (popula ddm/sensibilidade p/ a UI-lente) ...
```

### Suspensão D-04 no bloco do veredito (reusando "VERIFICAR")
```python
# report.py — dentro do bloco veredito, guardando ANTES de estampar preço (:184)
# Source: report.py:184-207 (lido) + selo.py:119 (overlay VERIFICAR)
if a.motor_pendente:
    a.veredito = (
        f"VERIFICAR — arquétipo {a.arquetipo} usa o motor '{a.motor}', que chega na Fase 2; "
        f"o DDM abaixo é lente conservadora, não o motor deste perfil. "
        f"Referências: Graham/Bazin."
    )
    a.alertas.append(
        f"Roteamento: {a.arquetipo} → motor pendente (Fase 2). Veredito de preço suspenso "
        f"para não estampar selo por um modelo que não serve a este perfil (D-04)."
    )
elif a.vmin is not None and a.vmax is not None and a.preco_atual:
    ...  # lógica DDM ATUAL intacta (pagadora_regulada) — TAEE11 idêntica (ENG-06)
```
> Reusar o prefixo **"VERIFICAR"** faz `selo.montar_selo` marcar `verificar=True` e **não atribuir faixa/rótulo de preço** (`selo.py:119-122`) — ou seja, **não estampa 'evitar'** (D-04) **sem tocar o selo nem os prefixos existentes** (Pitfall 3 evitado). O firewall selo↛report continua intacto.

### Medida de oscilação (helper novo, puro)
```python
# core/arquetipo.py  — Source: statistics stdlib; padrão de normalizacao.py
from statistics import mean, pstdev
def _cv_lucro(serie: list[float]) -> float | None:
    vals = [v for v in serie if v is not None]
    if len(vals) < 3:
        return None
    m = mean(vals)
    if m == 0:
        return None
    return pstdev(vals) / abs(m)   # coef. de variação; alto = oscilação violenta (cíclica)
```

## State of the Art

Domínio interno de finanças/heurística — sem "estado da arte" de biblioteca externa a rastrear. O relevante é o **estado do próprio código**:

| Old Approach (hoje) | Current Approach (Fase 1) | Impact |
|---------------------|---------------------------|--------|
| Motor primário fixo (DDM) para toda ação | Registry arquétipo→motor; DDM só p/ `pagadora_regulada` | Fim da aberração silenciosa; ITUB4 deixa de estampar "evitar" já na F1 (via D-04) |
| `setor` só usado p/ `eh_concessionaria` e display | `setor` string vira sinal de hard-route financeira/regulada | ARQ-01/D-02 |
| Veredito sempre cravado | Suspensão honesta quando motor não existe | ARQ-02/D-04 |

**Deprecated/outdated:** nada removido nesta fase (aditivo). RIM/normalizado/DCF/SOTP continuam ausentes até a Fase 2 — por isso a suspensão D-04 é necessária.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Threshold cíclica `CV(lucro cru) ≥ 0.40` separa commodity oscilante | Pattern 3 / Thresholds | Baixo — é calibrável em config; erra p/ mais fronteiriços (honesto). Backtest é fora de escopo (BACKTEST-01). |
| A2 | `ROE_valuation ≥ 0.15` + `retenção ≥ 0.50` caracteriza compounder/crescimento | Pattern 3 | Baixo — alinhado ao guardrail SAN-01 (ROE>15%) do brief; calibrável. |
| A3 | Setor legal (`SETOR_ATIV`) é confiável p/ financeiras (banco/seguradora/interm. financeira) | Summary / Pattern 3 | Baixo — VERIFICADO nos dados p/ ITUB4/BBAS3/SANB11/BBSE3/CXSE3/ITSA4. Risco residual: fintechs mal-cadastradas. |
| A4 | Reusar prefixo "VERIFICAR" para a suspensão D-04 é aceitável de UX | Pitfall 3 / Code Examples | Médio — é a via de menor risco técnico, mas o operador pode querer um rótulo próprio ("AGUARDANDO MOTOR"). **Confirmar na discussão/planejamento.** |
| A5 | Bloco DDM deve continuar rodando sempre (só o veredito é suspenso) | Pattern 2 | Baixo — necessário p/ manter `test_guardrails_fix06` (banda/matriz existem) e a UI-lente; consistente com D-04 ("DDM rebaixado a lente"). |
| A6 | `holding` não precisa de detector confiável na F1 (motor ausente de qualquer forma) | Open Questions | Baixo — o prefixo "Emp. Adm. Part." é ambíguo (TAEE11/WEGE3/ITSA4 todos o têm); classificação fina de holding fica p/ F2. |

**Nenhuma dessas é bloqueante.** A única que merece decisão explícita do operador antes de codar é **A4** (rótulo do veredito suspenso).

## Open Questions

1. **Detectar banco por código de conta CVM (2.08 vs 2.03) vale o encanamento novo?**
   - What we know: `cvm.fundamentos_do_ano` já usa `nome_primeiro=True` com códigos `["2.03","2.08"]` para o PL (`cvm.py:224-228`) e "Receitas da Intermediação Financeira" para receita (`:221`), **mas não retorna qual template casou** — não há flag de "é banco" hoje.
   - What's unclear: o setor string já resolve financeiras com confiança (A3). O detector por conta seria **reforço** (robustez contra cadastro errado), ao custo de propagar um flag `cvm → build.py → CompanyData.eh_financeira`.
   - Recommendation: **Fase 1 usa o hard-route por `c.setor` string** (já disponível, verificado). Tratar o detector por conta como melhoria opcional/Fase-2 se algum banco escapar. Registrar como decisão no plano.

2. **Regra de conflito D-01 quando o hard-route de setor bate mas o quantitativo discorda.**
   - What we know: D-02 diz que setores fortes hard-route DIRETO (sem quantitativo). D-01 diz que fronteiriço dispara em conflito setor×quantitativo.
   - What's unclear: para `pagadora_regulada` (onde o DDM existe e roda), vale rodar um **veto quantitativo** (ex.: margem oscilando como cíclica) antes de cravar, ou o hard-route é soberano? Ex.: uma "geradora" muito exposta a preço de energia.
   - Recommendation: hard-route **financeira** soberano (sem quantitativo). Hard-route **regulada** soberano **exceto** a guarda anti-Petróleo (Pitfall 1); adiar veto quantitativo fino da regulada para calibração futura. Confirmar na discussão.

3. **Onde exibir o arquétipo/motor no CLI markdown?** O `relatorio_markdown` (`report.py:410`) hoje **não** mostra Graham/Bazin (só o app.py mostra, `:943-965`). D-04 pede "mostra Graham/Bazin como referência".
   - Recommendation: exposição mínima — uma linha no cabeçalho do relatório (`:414`) tipo "Arquétipo: X → motor Y" e, quando `motor_pendente`, uma nota no bloco Veredito apontando as lentes clássicas. UX rica é Fase 3 (discricionário).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | tudo | ✓ | 3.x (`.venv`) | — |
| pandas / numpy | leitura CVM / winsor | ✓ | instalados | — |
| pytest | goldens | ✓ | roda 338 testes em ~4s | — |
| Dados CVM cacheados | fixtures/âncoras offline | ✓ | `data/cvm/dfp_*_2015..2025.zip` + `cad_cia_aberta.csv` | testes usam `CompanyData` sintético (sem rede) |

**Missing dependencies with no fallback:** nenhuma.
**Missing dependencies with fallback:** nenhuma — Fase é código puro sobre o stack existente. [VERIFIED: `pytest -q` → 338 passed]

## Security Domain

Não aplicável de forma material: a Fase é um **refactor interno da engine de valuation**, sem nova superfície de entrada externa. Nenhum input de usuário novo, nenhuma chamada de rede nova, nenhum secret. A validação de borda já existe onde importa (ingestão CVM/Yahoo/BCB, fora do escopo desta fase). V5 (Input Validation) reduz-se a **degradação graciosa** de sinais `None` (Pitfall 2) — que é robustez, não segurança. Sem V2/V3/V4/V6 relevantes. `security_enforcement` não está setado no `.planning/config.json`; dado o caráter code-only sem I/O externo novo, não há controles ASVS a adicionar nesta fase.

## Thresholds (proposta inicial, config-driven)

Bloco novo sugerido em `config.yaml` (irmão de `selo:`), lido pelo classificador — **iniciais e defensáveis, calibração empírica é BACKTEST-01/deferida**:
```yaml
arquetipo:
  financeiro_tokens: [banco, "intermediação financeira", seguradora,
                      "arrendamento mercantil", "crédito imobiliário",
                      factoring, securitização, "bolsas de valores"]
  regulada_excluir_tokens: [petróleo]        # guarda anti-falso-positivo 'Gás' (Pitfall 1)
  roe_alto_min: 0.15                          # ROE de valuation "alto" (alinhado a SAN-01)
  retencao_alta_min: 0.50                     # 1 − payout_valuation ≥ 0.50 = compounder
  ciclica_cv_min: 0.40                        # coef. de variação da série de lucro CRUA
```
Racional por linha: `roe_alto_min=0.15` espelha o guardrail SAN-01 do brief (ROE>15%) e fica acima do `roe_min=0.10` do screening (Cap. 8) — separa "bom" de "excepcional". `retencao_alta_min=0.50` é o ponto onde `g_fund = ROE×(1−payout)` fica materialmente positivo (compounder reinveste ≥ metade). `ciclica_cv_min=0.40` marca lucro cuja dispersão é ~40%+ da média — swing "violento" no sentido do brief, folgado o bastante para não pegar maturidade estável. Todos calibráveis sem deploy; os goldens os pinam via `_cfg()`.

## Sources

### Primary (HIGH confidence)
- Código do repo lido integralmente: `report/report.py` (funil, AnaliseAcao :22, veredito :170-207, render :410, `_veredito_token` :355), `report/selo.py` (firewall, `faixa_do_veredito` :88, overlay VERIFICAR :119), `core/fundamentals.py` (CompanyData + métodos canônicos), `core/lifecycle.py`, `core/normalizacao.py`, `ingest/build.py` (`eh_concessionaria` :68), `ingest/cvm.py` (2.03/2.08, interm. financeira, distribuições), `ingest/universe.py` (resolver + override), `cli.py`, `config.yaml`, testes (`test_ddm`, `test_selo`, `test_consistencia_modos`, `test_vulc3_regressao`, `test_guardrails_fix06`).
- `pandas` sobre `data/cvm/cad_cia_aberta.csv` — SETOR_ATIV das âncoras (ITUB4='Bancos', BBSE3/CXSE3='...Seguradoras', TAEE11/ELET3='Emp. Adm. Part. - Energia Elétrica', SAPR11='Saneamento...', EGIE3='Energia Elétrica', VALE3='Extração Mineral', WEGE3='...Máqs...', ITSA4='...Intermediação Financeira', PETR4='Petróleo e Gás').
- Reprodução do falso-positivo `eh_concessionaria('Petróleo e Gás') == True`.
- `pytest -q` → 338 passed (baseline verde).

### Secondary (MEDIUM confidence)
- `.planning/BRIEF-motor-arquetipo.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `01-CONTEXT.md` — decisões e âncoras de código (cross-verificadas contra o código real).

### Tertiary (LOW confidence)
- Thresholds numéricos (A1/A2) — baseados no espírito do livro/brief, não em backtest (explicitamente fora de escopo).

## Metadata

**Confidence breakdown:**
- Standard stack / sinais disponíveis: **HIGH** — assinaturas e retornos (incl. casos None) lidos direto na fonte.
- Ponto de inserção / âncoras: **HIGH** — confirmadas linha a linha (`:53/:109/:113-134/:136-152/:170-207/:22/:355/:410`).
- Hard-route por setor: **HIGH** — SETOR_ATIV das âncoras verificado nos dados CVM.
- Pitfall Petróleo/Gás: **HIGH** — reproduzido.
- Thresholds do refino quantitativo: **MEDIUM-LOW** — defensáveis e config-driven, mas não calibrados (backtest deferido).
- Superfície de teste: **HIGH** — os 5 testes-trava lidos; invariantes explícitos.

**Research date:** 2026-07-11
**Valid until:** ~30 dias (código estável; sem dependências fast-moving). Revalidar `pytest` baseline se o repo mudar antes do planejamento.
