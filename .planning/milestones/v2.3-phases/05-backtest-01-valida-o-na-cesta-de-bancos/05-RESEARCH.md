# Phase 5: BACKTEST-01 — Validação na cesta de bancos - Research

**Researched:** 2026-07-12
**Domain:** Harness de validação determinístico (pytest golden + script standalone) sobre o motor RIM calibrado (Fase 4), cesta de bancos B3
**Confidence:** HIGH (todas as APIs abaixo lidas direto do código-fonte, file:line citado)

## Summary

Esta fase NÃO toca o motor. Ela **consome** o RIM calibrado através de `report.analisar_acao(c, cfg)`
sobre 4 `CompanyData` congelados (snapshot) e compara `a.intrinseco_motor` com 4 âncoras. Toda a
infraestrutura necessária já existe e é testada: o padrão exato de golden offline (`build CompanyData
em memória → analisar_acao(c, cfg) → assert numérico`) está vivo em `tests/test_vulc3_regressao.py`
(bancos sintéticos ITUB4/TAEE11/VALE3/WEGE3) e é o molde 1:1 do novo `tests/test_backtest_bancos.py`.
As âncoras Graham/Bazin (`core/lentes.py`), P/VP e P/L (`core/lentes.py::metricas_par` + `core/multiples.py`)
e o preço de mercado (`CompanyData.preco_atual`) são todas funções puras que operam sobre o mesmo
`CompanyData` — **zero fonte externa** para a âncora de múltiplos de pares (D-11).

O número sob validação é **`AnaliseAcao.intrinseco_motor`** (populado quando `a.motor == "rim"`).
A rota `financeira → rim` é confirmada por hard-route de setor em `core/arquetipo.py`. A única
incerteza real é **BBSE3 (BB Seguridade)**: o roteamento depende da string de setor da CVM casar o
token `seguradora` (word-boundary, plural tolerado) — se a CVM classificar como "Seguros"/"Previdência",
BBSE3 **não roteia para RIM** e vira a exceção documentada natural do D-08. O harness DEVE ler
`a.arquetipo`/`a.motor` por ticker e registrar, nunca assumir.

**Primary recommendation:** Congelar por ticker o subconjunto de campos de `CompanyData` que
`analisar_acao` consome (raw fundamentals + preço + beta) num YAML versionado + um `rf_local` global
carimbado; o teste reconstrói o `CompanyData`, roda `analisar_acao(c, cfg)` com `config.yaml` shipado,
lê `a.intrinseco_motor`, e crava o gate quórum-3/4-±15% contra a tabela de fair values YAML. Espelhar
`test_vulc3_regressao.py` verbatim no estilo.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VAL-01 | Harness reproduzível (script + teste) roda o RIM calibrado na cesta ITUB4/BBAS3/BBSE3/BBDC4 e reporta intrínseco vs âncoras; prova que generaliza | `analisar_acao` (report.py:312) devolve `a.intrinseco_motor` por ticker; snapshot congelado (padrão `test_vulc3_regressao.py`) garante reprodutibilidade; script standalone imita `cli.cmd_analyze` (cli.py:66) → `out/backtest_bancos.md` |
| VAL-02 | Triangula 4 âncoras: (a) Graham+Bazin, (b) preço, (c) tabela manual FV, (d) múltiplos de pares; aceite = RIM não cronicamente ~40-50% abaixo | (a) `lentes.preco_justo_graham`/`preco_teto_bazin` (lentes.py:37/75); (b) `c.preco_atual`; (c) YAML `tests/fixtures/fair_values_bancos.yaml` (novo); (d) medianas de `lentes.metricas_par(c).pvp/.pl` sobre a cesta (lentes.py:151) |
</phase_requirements>

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Fair values = pesquisa de consenso (target prices públicos), proposta ao usuário para aprovar ANTES de versionar. Não é o usuário que digita; não deriva de Graham/Bazin.
- **D-02:** Cada fair value é uma **faixa (mín–máx)**, não um ponto.
- **D-03:** Tabela versionada em YAML dedicado — `tests/fixtures/fair_values_bancos.yaml` (NÃO no `config.yaml`). Por ticker: `min`, `max`, `data`, `fonte/comentário`.
- **D-04:** Harness roda sobre **snapshots congelados**, não ao vivo. Congelar inputs do RIM (VPA, ROE, preço) num fixture versionado, data carimbada. Teste determinístico (golden reproduzível).
- **D-05:** Data-base = hoje (~2026-07-12), captura única ao vivo via `build.montar_empresa` para os 4 bancos; alinhar o consenso de FV à mesma janela.
- **D-06:** A âncora-verdade do gate automatizado = tabela manual de FV (D-01). As outras 3 âncoras = contexto no relatório, não no gate.
- **D-07:** Banda de PASS = **±15%** da faixa FV (PASS se RIM dentro da faixa ou até 15% fora de qualquer borda). Calibrável.
- **D-08:** Quórum = **3 de 4** dentro da banda. O 4º pode ficar fora SE E SOMENTE SE documentado. Desvio não-explicado = FAIL. O teste trava o quórum numérico 3/4 ±15%; a "explicação" é uma nota humana no YAML — o teste exige que a 4ª esteja anotada, não julga o texto.
- **D-09:** Entrega = pytest determinístico (`tests/test_backtest_bancos.py`) + script standalone (roda a cesta, imprime tabela).
- **D-10:** Script gera `out/backtest_bancos.md`, consistente com o padrão `out/TICKER.md`. Colunas: RIM, Graham+Bazin, preço, faixa FV, múltiplos de pares, desvio, PASS/FAIL, nota de exceção.
- **D-11:** Múltiplos de pares (P/VP, P/L) calculados **da própria cesta** — medianas dos 4 bancos do snapshot. Reusa `comparables.py`/`multiples.py`; zero fonte externa.
- **D-12:** Se a validação reprova além da exceção permitida, o achado é registrado (relatório + finding) e volta para ajustar a Fase 4 (loop). Não silencia desvios.

### Claude's Discretion
- Local exato do fixture de FV e do snapshot (fixtures/ vs data/) — desde que versionado e citável.
- Estrutura interna do snapshot (raw fundamentals no boundary do RIM vs CompanyData serializado) — mínimo que reproduz o intrínseco de forma estável.
- Como o script standalone é invocado (`python -m`, `scripts/`, ou função) — desde que reproduza o mesmo resultado do teste.

### Deferred Ideas (OUT OF SCOPE)
- Redeploy do v2.3 na VPS (Fase 6 / OPS-01).
- Expandir o backtest para não-bancos / outros arquétipos.
- Backtest histórico multi-período (aqui é snapshot único).
</user_constraints>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Captura de fundamentos ao vivo (D-05) | Ingest (`ingest/build.py`) | — | `montar_empresa` já combina CVM+Yahoo+BCB; rodar UMA vez |
| Cálculo do intrínseco RIM (número validado) | Core/Report (`report.analisar_acao` → `motores.rim`) | — | O harness consome, não reimplementa (Integration Point CONTEXT) |
| Âncoras Graham/Bazin | Core (`core/lentes.py`) | — | Funções puras sobre CompanyData |
| Âncora múltiplos de pares P/VP,P/L (D-11) | Core (`core/lentes.py::metricas_par`, `core/multiples.py`) | Harness (mediana) | Métricas por par vêm do core; a agregação (mediana da cesta) é lógica nova do harness |
| Snapshot congelado (D-04) | Test fixture (YAML novo) | — | Determinismo; fora do motor |
| Gate quórum 3/4 ±15% (D-06/07/08) | Test (`tests/test_backtest_bancos.py`) | — | Lógica de validação nova, config-driven |
| Relatório legível (D-10) | Script standalone → `out/` | — | Espelha `cli.cmd_analyze` markdown |

## Q1 — Extração do intrínseco RIM (o número validado)

**Superfície a chamar:** `report.analisar_acao(c: CompanyData, cfg: dict) -> AnaliseAcao`
(`src/analista/report/report.py:312`). Never-raise no uso normal; retorna um dataclass `AnaliseAcao`
(report.py:23-73).

**Campo que carrega o intrínseco RIM:** **`a.intrinseco_motor: Optional[float]`** (report.py:59).
Populado em report.py:420 via `a.intrinseco_motor = _intrinseco_por_motor(a.motor, c, a, cfg)`.
Para banco roteado a RIM, `_intrinseco_por_motor` (report.py:183-240) executa o ramo `motor == "rim"`
(report.py:202-214) e devolve `res_rim.valor_intrinseco`.

Campos de roteamento a ler junto (para confirmar/registrar a rota — crítico p/ D-08):
- `a.arquetipo: str` — esperado `"financeira"` para banco (report.py:401).
- `a.motor: str` — esperado `"rim"` (report.py:404-405).
- `a.motor_rotulo` — `"RIM — VPA + VP do excesso de ROE sobre Ke (banco/seguradora)"` (motores.py:33).

**Roteamento arquétipo→motor:** `arquetipo.classificar(c, cfg)` (arquetipo.py:124) → hard-route de
setor por token (arquetipo.py:150-154): setor que casa `financeiro_tokens` (config.yaml:199 — inclui
`banco`, `seguradora`) → `FINANCEIRA`. Registry `ARQUETIPO_MOTOR[FINANCEIRA] = "rim"` (arquetipo.py:48-54).
`_setor_casa_token` casa por **limite de palavra com plural tolerado** (arquetipo.py:107-121): `Bancos`
casa `banco`; `Seguradoras` casa `seguradora`.

**Fórmula do RIM (para conferência, NÃO reimplementar):** `motores.rim(vpa0, roe0, ke, retencao, n,
excesso_sustentavel, g_terminal, ke_g_spread_min)` (motores.py:64). Inputs montados no dispatch
(report.py:204-213):
- `vpa0 = lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))`
- `roe0 = c.roe_valuation()`
- `ke = motores.ke_rim(c.beta, cfg)`  (clampa a `[ke_piso, ke_teto]`, teto 0.13; nunca excede ke_live)
- `retencao = 1.0 - (c.payout_valuation() or 0.0)`
- `n = rim_cfg["n_fade"]` (10), `excesso_sustentavel`, `g_terminal`, `ke_g_spread_min` de config.

**BBSE3 flag (D-08):** se a string de setor CVM da BB Seguridade for "Seguradoras"/"Seguros e
Previdência" contendo `seguradora`, roteia RIM. Se for só "Seguros"/"Previdência" (sem `seguradora`),
NÃO casa o token → cai no refino quantitativo (arquetipo.py:162-186) → provável `pagadora_regulada`
(default) ou `crescimento` → motor ≠ rim → `a.intrinseco_motor` vem de OUTRO motor. **O harness deve
capturar o setor real na captura ao vivo e assertar/registrar `a.motor` por ticker.** Se ≠ "rim",
BBSE3 é a exceção documentada natural.

## Q2 — Snapshot congelado para determinismo (D-04/D-05)

**Shape do CompanyData** (`src/analista/core/fundamentals.py:19-53`): dataclass mutável. Séries anuais
são `Dict[int, float]` (`{ano: valor}`) — toleram buracos. Campos de mercado escalares. Não é pydantic;
construção trivial via kwargs + preenchimento de dicts (padrão em todos os testes offline).

**Como `montar_empresa` produz o snapshot ao vivo (D-05):**
`build.montar_empresa(ticker, ano_base, n_anos=10)` (`src/analista/ingest/build.py:40`) →
`Optional[CompanyData]`. Chamar UMA vez por banco com `ano_base = cfg["universo"]["ano_base"]` (2025)
e `n = cfg["universo"]["anos_historico"]` (10) — exatamente como `cli._montar` (cli.py:52-63).

**Campos mínimos que `analisar_acao` consome para um banco→RIM** (freeze só estes; o resto degrada
gracioso a None):

| Campo CompanyData | Tipo | Usado por | Obrigatório p/ RIM |
|-------------------|------|-----------|--------------------|
| `ticker`, `nome`, `setor` | str | roteamento (setor) + display | SIM (setor decide a rota) |
| `anos` | List[int] | `ultimo_ano`, séries | SIM |
| `lucro_liquido` | Dict[int,float] | `roe_valuation`, `lpa_valuation`, `cv_lucro`, payout | SIM |
| `patrimonio_liquido` | Dict[int,float] | `vpa` (RIM), `roe_valuation` (PL médio) | SIM |
| `num_acoes` | Dict[int,float] | `vpa`, `lpa`, `dpa` | SIM |
| `dividendos` | Dict[int,float] | `payout_valuation` → retenção | SIM (retenção do RIM) |
| `preco_atual` | float | âncora (b) + veredito | SIM (âncora) |
| `beta` | float | `ke_rim` | SIM (ke) |
| `vendas_liquidas` | Dict[int,float] | ML/margem (display) | opcional (None → "-") |
| `fco` | Dict[int,float] | CDC (display) | opcional |
| `dpa_trailing_12m` | float | `dy_atual` | opcional |
| `ohlc_ajustado` | DataFrame | read técnico | NÃO (None → degrada, report.py:644-655) |

**Boundary de freeze recomendado (Discretion):** **serializar o subconjunto acima de `CompanyData`
por ticker em YAML** e reconstruir no teste — NÃO congelar `vpa0/roe0/ke` já-derivados. Justificativa:
(1) VAL-01 quer validar a engine **como shipada, incluindo o roteamento** (financeira→RIM) e a
exceção BBSE3 (D-08) — só `analisar_acao` exercita isso; (2) é o padrão já vivo e testado
(`test_vulc3_regressao.py::_itub4_live_like`, linhas 160-175, congela exatamente esses campos e roda
`analisar_acao`); (3) reconstruir raw fundamentals mantém o teste imune a mudança de assinatura interna
do `motores.rim` (o loop D-12 re-roda o snapshot, não reescreve o teste).

**LANDMINE de determinismo — `rf_local` (Selic ao vivo):** `ke_rim` lê `cfg["capm"]["rf_local"]`
(motores.py:143-145). No fluxo ao vivo, `cli.cmd_analyze` **sobrescreve** `cfg["capm"]["rf_local"]`
com a Selic-ciclo do BCB ANTES de chamar `analisar_acao` (cli.py:77-79). `config.yaml` shipa
`rf_local: 0.105` (config.yaml:76) como default offline determinístico. **Para reprodutibilidade, o
teste NÃO deve chamar a rede: rodar `analisar_acao(c, cfg)` com `config.yaml` as-is (rf_local=0.105).**
Congelar no fixture o `rf_local` (escalar) usado na captura ao vivo (D-05) e, no teste, injetá-lo em
`cfg["capm"]["rf_local"]` antes de `analisar_acao` — assim o número congelado casa a captura. Para
ITUB4 (beta 1,29) o clamp a `ke_teto=0.13` domina e o rf_local exato é irrelevante; para bancos de
beta menor pode importar → congelar o `rf_local` remove a ambiguidade. **`analisar_acao` NÃO muta
`cfg`** (a mutação de rf_local é feita pelo caller cli.py, não pela engine) — confirmado lendo
report.py:312-708; sem efeitos colaterais sobre cfg.

## Q3 — Padrão de golden determinístico existente (D-09)

**Molde canônico: `tests/test_vulc3_regressao.py`** — é o gêmeo exato do novo teste.
- Config: `_cfg()` abre `config.yaml` shipado via `yaml.safe_load` (test_vulc3_regressao.py:34-37;
  idêntico em test_motores.py:22-24). `ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`.
- Fixture offline: função `_itub4_live_like() -> CompanyData` (linhas 160-175) constrói o CompanyData
  em memória preenchendo os dicts por ano — **exatamente os campos da tabela Q2**.
- Execução: `a = report.analisar_acao(c, cfg)` (linha 183).
- Gate numérico duro: `assert a.arquetipo == "financeira"`, `assert a.motor == "rim"`,
  `assert a.intrinseco_motor is not None`, `assert a.intrinseco_motor > 30.0` (linhas 184-188).
- Tolerância: convenção do repo é **faixa absoluta** (`32.0 <= v <= 40.0` em test_motores.py:61) ou
  limiar duro (`> 30.0`). Não há `pytest.approx` no estilo do repo para valuation — usa bounds.

**Config de teste:** `pyproject.toml:14-16` — `pythonpath=["src"]`, `testpaths=["tests"]`. Sem
`conftest.py`, sem `tests/fixtures/` ainda (ambos a criar). Rodar: `pytest tests/test_backtest_bancos.py -x`.
Suíte cheia (gate de fase): `pytest` (440 testes hoje verdes — CONTEXT/SUMMARY).

**Estrutura recomendada de `tests/test_backtest_bancos.py`:**
1. `_cfg()` (copiar de test_vulc3_regressao.py:34-37).
2. `_carregar_snapshot()` → lê `tests/fixtures/snapshot_bancos_2026-07-12.yaml`, reconstrói 4
   `CompanyData` + `rf_local`.
3. `_carregar_fair_values()` → lê `tests/fixtures/fair_values_bancos.yaml`.
4. Um teste que itera os 4, roda `analisar_acao`, calcula PASS/FAIL ±15% e crava o quórum 3/4 + a
   regra de anotação (Q7). Constantes nomeadas `BANDA_PASS = 0.15`, `QUORUM_MIN = 3` (não números
   soltos — Established Pattern CONTEXT).

## Q4 — Âncoras (a) Graham+Bazin e (d) múltiplos de pares

**Graham (anchor a)** — `core/lentes.py:37` `preco_justo_graham(lpa, vpa) -> Optional[float]` =
`√(22,5 × LPA × VPA)`; None se LPA≤0 ou VPA≤0. Receita canônica exata (app.py:1053-1055):
```python
_ult = c.ultimo_ano()
_vpa = lentes.vpa(c.patrimonio_liquido.get(_ult), c.num_acoes.get(_ult))
graham = lentes.preco_justo_graham(c.lpa_valuation(), _vpa)
```

**Bazin (anchor a)** — `core/lentes.py:75` `preco_teto_bazin(dpa_med, dy_minimo=0.06)`. Receita
canônica (app.py:1067-1069):
```python
_dpas = [c.dpa(ano) for ano in c.anos_ordenados()]
_dpa_med = lentes.dpa_medio(_dpas, n=5)   # média dos últimos 5 anos-calendário (lentes.py:59)
bazin = lentes.preco_teto_bazin(_dpa_med)
```

**Múltiplos de pares P/VP e P/L (anchor d, D-11)** — `core/lentes.py:151`
`metricas_par(c) -> ParComparavel` devolve `.pl`, `.pvp`, `.roe`, `.dy`, `.valor_mercado` (never-raise,
campos None quando insumo falta):
- `pl = mult.preco_lucro(c.preco_atual, c.lpa_valuation())` (multiples.py:52; P/L com LPA canônico)
- `pvp = c.preco_atual / lentes.vpa(PL[ult], num_acoes[ult])` (lentes.py:159-162)

**Mediana da cesta (lógica NOVA do harness, D-11):** coletar `metricas_par(c).pvp` e `.pl` dos 4
bancos do snapshot e tomar a mediana (`statistics.median` sobre os não-None). Referência setorial
interna, **zero fonte externa**, mesma data-base. `lentes.tabela_pares(companies, ticker_alvo)`
(lentes.py:181) já monta a lista de `ParComparavel` marcando o alvo — pode ser reusado para gerar as 4
linhas; a agregação (mediana) é do harness.

## Q5 — Preço de mercado (anchor b)

`CompanyData.preco_atual: Optional[float]` (fundamentals.py:40), populado por `montar_empresa` de
`dm.preco_atual` (build.py:58). Já é frozen no snapshot (campo obrigatório da tabela Q2). Nenhuma
chamada extra. `a.preco_atual` também é espelhado em `AnaliseAcao` (report.py:315).

## Q6 — Formato de saída (D-10)

**Padrão a espelhar:** `cli.cmd_analyze` (cli.py:66-87): `os.makedirs(OUT_DIR)`, monta markdown, grava
`out/{ticker}.md` com `open(destino,"w",encoding="utf-8").write(md)`. O gerador de markdown é
`report.relatorio_markdown(c, a, cfg)` (report.py:844+), que usa `L: List[str]` + `"\n".join(L)` e a
lib `tabulate` (report.py:14) para tabelas. `OUT_DIR` já existe como constante em cli.py.

**Recomendação:** o script standalone monta uma tabela única (uma linha por ticker) com as colunas do
D-10 usando `tabulate(linhas, headers=..., tablefmt="github")` (mesma dependência já no projeto) e grava
`out/backtest_bancos.md`. Colunas: `Ticker | Motor | RIM | Graham | Bazin | Preço | FV faixa | P/VP med
| P/L med | Desvio RIM×FV | PASS/FAIL | Nota exceção`. Não reusar `relatorio_markdown` (é por-ação); o
backtest é uma tabela-resumo da cesta.

## Q7 — Mecânica do gate PASS/FAIL (D-06/D-07/D-08)

**Fonte de verdade do gate (D-06):** só a tabela manual de FV (YAML). As outras 3 âncoras entram no
markdown como contexto, não no assert.

**PASS por ticker (D-07):** dado `fv_min`, `fv_max` e `rim = a.intrinseco_motor`:
```
PASS  se  fv_min*(1 - 0.15) <= rim <= fv_max*(1 + 0.15)
```
(banda ±15% em torno de qualquer borda da faixa). Constante nomeada `BANDA_PASS = 0.15`.

**Quórum + anotação (D-08 — como o teste distingue "3 passam + 1 anotada" de "3 passam + 1 silenciosa"):**
Cada ticker no YAML de FV tem um campo OPCIONAL `excecao_nota: <str>`. Regra do teste:
```
passes = [t for t in cesta if PASS(t)]
falhas = [t for t in cesta if not PASS(t)]
assert len(passes) >= 3                                  # quórum numérico (QUORUM_MIN)
for t in falhas:                                         # cada falha DEVE estar anotada
    assert fv[t].get("excecao_nota"),  f"{t} fora da banda sem nota de exceção → FAIL silencioso"
```
Assim: 4/4 PASS → verde trivial. 3 PASS + 1 fora COM `excecao_nota` não-vazia → verde (exceção
documentada). 3 PASS + 1 fora SEM nota → o `assert` da nota falha (FAIL silencioso barrado). ≤2 PASS →
o `assert len>=3` falha (calibração não generaliza → loop D-12). O teste **não julga o texto** da nota,
só exige presença (D-08).

**Dados que o teste lê do YAML de FV (D-03 + campo novo):** por ticker `min: float`, `max: float`,
`data: str`, `fonte: str`, e `excecao_nota: Optional[str]`.

## Q8 — Config knobs (D-04, calibração da Fase 4)

Confirmados em `config.yaml` §`motores.rim` (linhas 229-252) e consumidos por report.py:206-212 /
motores.py:143-149:

| Knob | Valor shipado | Papel |
|------|--------------|-------|
| `motores.rim.erp_banco` | 0.045 | ERP do ke_rim (sem prêmio small-cap) |
| `motores.rim.ke_piso` | 0.11 | clamp inferior do ke |
| `motores.rim.ke_teto` | 0.13 | CAL-02, clamp superior (ativo p/ ITUB4) |
| `motores.rim.n_fade` | 10 | horizonte explícito |
| `motores.rim.excesso_sustentavel` | 0.045 | cap do excesso de ROE na perpetuidade |
| `motores.rim.g_terminal` | 0.025 | g do RI terminal (≤ PIB) |
| `motores.rim.ke_g_spread_min` | 0.03 | piso (ke−g) p/ liberar o terminal |
| `capm.rf_local` | 0.105 | rf offline determinístico (ver LANDMINE Q2) |

Como carregar: `yaml.safe_load(open("config.yaml"))` via `_cfg()` (test_motores.py:22-24). O snapshot
reproduz o intrínseco da Fase 4 porque roda o MESMO config + os MESMOS raw inputs. Números-alvo de
referência (SUMMARY 04-01): ITUB4 live R$32,87, golden R$39,23, bad-bank R$15,54.

## Q9 — Landmines / gotchas

1. **`rf_local` ao vivo quebra o determinismo** — ver LANDMINE Q2. Congelar o rf_local usado na
   captura; no teste NUNCA chamar `macro.selic_ciclo_para_capm` (rede). Rodar `analisar_acao` offline.
2. **Roteamento BBSE3** — depende da string de setor da CVM casar `seguradora`. Capturar o setor real
   ao vivo e assertar/registrar `a.motor` por ticker. Se ≠ "rim", `a.intrinseco_motor` vem de outro
   motor (NAV/DDM/DCF) → é a exceção D-08. Não assumir RIM cegamente.
3. **`a.intrinseco_motor` pode ser None** — `_intrinseco_por_motor` é never-raise (report.py:238-239) e
   report.py:427-432 zera valores ≤0. O harness deve tratar None (registrar "motor não estimou" e
   contar como fora-da-banda exigindo nota).
4. **Sem efeitos colaterais em cfg** — `analisar_acao` lê cfg, não muta (verificado report.py:312-708).
   Seguro rodar os 4 bancos com o mesmo dict cfg. (A mutação de rf_local, se feita, é do harness/caller.)
5. **Firewall selo↛report / arquivos proibidos** — esta fase NÃO toca `core/ddm.py`, `report/selo.py`,
   `core/lentes.py`, `core/motores.py`, `config.yaml` (a menos que o loop D-12 dispare). O novo teste
   só ADICIONA à suíte; os 440 testes + invariantes (TAEE11 DDM, VULC3, firewall) devem seguir verdes.
6. **`num_acoes` base de unit** — nenhum dos 4 bancos é UNIT (ITUB4/BBDC4=4, BBAS3/BBSE3=3), então
   `_eh_unit` é False e não há fator de conversão (build.py:17-37). Sem gotcha aqui.
7. **`payout_valuation` sem clamp pode passar de 1.0** — bancos pagam JCP; se a mediana do payout
   passar de 100%, `retencao = 1 - payout` fica negativa e alimenta o RIM. É o comportamento shipado
   (não corrigir aqui); só registrar se algum banco sair estranho — candidato a nota de exceção, não a
   patch (escopo cirúrgico).

## Runtime State Inventory

Fase de criação de artefatos novos (teste + fixtures + script), NÃO rename/refactor. Ainda assim:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Nenhum — não há datastore; snapshot é YAML versionado em git | Nenhuma |
| Live service config | Nenhum — custo-zero, sem serviço externo persistente | Nenhuma |
| OS-registered state | Nenhum | Nenhuma |
| Secrets/env vars | Nenhum — dados gratuitos, sem chave | Nenhuma |
| Build artifacts | `tests/fixtures/` (novo dir) + `out/backtest_bancos.md` (gerado, provável gitignore como o resto de `out/`) | Criar dir; confirmar `.gitignore` de `out/` |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | tudo | ✓ (assumido) | ≥3.10 (pyproject) | — |
| pytest | teste | ✓ | testpaths configurado | — |
| PyYAML (`yaml`) | config + fixtures | ✓ | usado em todos os testes | — |
| tabulate | markdown do script | ✓ | import em report.py:14 | join manual de strings |
| Rede CVM/Yahoo/BCB | captura ao vivo D-05 (UMA vez) | ✓ ao vivo | — | Se cair, snapshot não pode ser gerado; o TESTE não precisa de rede |

**Missing dependencies with no fallback:** nenhuma. A captura ao vivo (D-05) exige rede uma única vez;
o teste determinístico roda 100% offline sobre o YAML congelado.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (`[tool.pytest.ini_options]`, pyproject.toml:14) |
| Config file | `pyproject.toml` — `pythonpath=["src"]`, `testpaths=["tests"]` |
| Quick run command | `pytest tests/test_backtest_bancos.py -x` |
| Full suite command | `pytest` (440 testes hoje) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VAL-01 | RIM calibrado roda na cesta, intrínseco por ticker reproduzível | golden | `pytest tests/test_backtest_bancos.py -x` | ❌ Wave 0 |
| VAL-02 | Gate quórum 3/4 ±15% vs FV; exceção exige nota | golden | `pytest tests/test_backtest_bancos.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_backtest_bancos.py -x`
- **Per wave merge:** `pytest` (suíte cheia — não regredir 440 + firewall)
- **Phase gate:** suíte verde antes de `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_backtest_bancos.py` — cobre VAL-01/VAL-02 (novo)
- [ ] `tests/fixtures/fair_values_bancos.yaml` — tabela manual FV (D-03) — precisa do consenso aprovado (D-01)
- [ ] `tests/fixtures/snapshot_bancos_2026-07-12.yaml` — snapshot congelado (D-04/D-05) — precisa da captura ao vivo
- [ ] Script standalone (`scripts/backtest_bancos.py` ou `python -m analista.backtest`) → `out/backtest_bancos.md`
- [ ] `tests/fixtures/` dir não existe ainda — criar

*Framework install: nenhum — pytest/PyYAML/tabulate já presentes.*

## Standard Stack

### Core (reuso, zero dependência nova)
| Library/Módulo | Purpose | Why Standard |
|---------|---------|--------------|
| `report.analisar_acao` (report.py:312) | Produz `a.intrinseco_motor` (RIM) | Superfície única do valuation; harness consome, não reimplementa |
| `ingest.build.montar_empresa` (build.py:40) | Captura ao vivo (D-05), UMA vez | Já combina CVM+Yahoo+BCB |
| `core.lentes` (lentes.py) | Graham, Bazin, VPA, `metricas_par` (P/VP,P/L) | Puros, testados (test_lentes.py) |
| `core.multiples` (multiples.py) | P/L, DY primitivos | Cap.10 canônico |
| `yaml` / `tabulate` | fixtures + markdown | Já no projeto |

**Installation:** nenhuma — `pip install -e .` já cobre tudo. Não adicionar dependências (custo-zero).

## Architecture Patterns

### Fluxo do harness (data flow)
```
captura ao vivo (1×, D-05)                 teste determinístico (offline, sempre)
──────────────────────────                 ──────────────────────────────────────
montar_empresa(ITUB4..BBSE3)               yaml.load(snapshot) ─┐
   │  (CVM+Yahoo+BCB)                       yaml.load(fair_values)│
   ▼                                                             ▼
CompanyData ×4 + rf_local ──► serializa ──► reconstrói CompanyData ×4
                              (YAML fixture)           │
                                                       ▼  cfg = config.yaml (rf_local congelado)
                                            analisar_acao(c, cfg) ×4
                                                       │
                                        ┌──────────────┼───────────────┐
                                        ▼              ▼               ▼
                              a.intrinseco_motor  a.arquetipo/motor  âncoras (Graham/Bazin/
                                  (RIM)            (rota, D-08)        preço / P/VP,P/L medianas)
                                        │                              │
                                        └──────► gate ±15% / 3-4 ◄─────┘  + FV YAML (D-06)
                                                       │
                                        ┌──────────────┴──────────────┐
                                        ▼                             ▼
                              assert quórum+anotação           script → out/backtest_bancos.md
                              (tests/test_backtest_bancos.py)   (tabela D-10)
```

### Recommended structure
```
tests/
├── test_backtest_bancos.py          # gate D-06/07/08 (novo)
└── fixtures/                        # novo dir (Discretion: fixtures/ escolhido)
    ├── snapshot_bancos_2026-07-12.yaml   # D-04/D-05 raw fundamentals+preço+beta+rf_local
    └── fair_values_bancos.yaml           # D-03 min/max/data/fonte/excecao_nota
scripts/
└── backtest_bancos.py               # standalone D-09/D-10 → out/backtest_bancos.md
```
*Discretion resolvido:* `tests/fixtures/` (não `data/`) porque o consumidor primário é o teste e o
CONTEXT D-03 já cita esse caminho; script em `scripts/` invocável por `python scripts/backtest_bancos.py`
(ou reuso de uma função `rodar_cesta()` que o teste E o script chamam — garante mesmo resultado).

### Anti-patterns to avoid
- **Reimplementar a fórmula RIM no harness** — consumir `analisar_acao`/`a.intrinseco_motor`. Se a
  Fase 4 mudar (loop D-12), re-roda o snapshot, não reescreve o teste.
- **Congelar `vpa0/roe0/ke` derivados** em vez de raw fundamentals — perde o teste de roteamento
  (BBSE3/D-08) e acopla ao internals do motor.
- **Números soltos** (`0.15`, `3`) no corpo do teste — usar constantes nomeadas (`BANDA_PASS`, `QUORUM_MIN`).
- **Chamar a rede no teste** — quebra determinismo; a rede vive só na captura ao vivo (1×).
- **Assumir BBSE3→RIM** — ler `a.motor` e tratar exceção.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Intrínseco RIM | fórmula custom | `analisar_acao` → `a.intrinseco_motor` | fonte única calibrada; loop D-12 |
| Graham/Bazin | √/DPA custom | `lentes.preco_justo_graham`/`preco_teto_bazin` | puros, testados, degradação tratada |
| P/VP, P/L por par | divisão manual | `lentes.metricas_par(c)` | usa LPA/VPA canônicos (Core Value: consistência entre menus) |
| Captura de dados | scraping | `build.montar_empresa` | já resolve CVM+Yahoo+BCB+unit |
| Config load | parse custom | `yaml.safe_load(config.yaml)` via `_cfg()` | padrão do repo |

## Common Pitfalls

### Pitfall 1: Snapshot não-determinístico por rf_local ao vivo
**O que dá errado:** o teste chama Selic ao vivo (ou usa rf_local default diferente do da captura) → o
ke muda → o intrínseco congelado não bate. **Como evitar:** congelar `rf_local` no fixture e injetá-lo
em `cfg` no teste; nunca chamar `macro.selic_ciclo_para_capm` no teste. **Sinal:** número do teste
diverge da captura só para bancos de beta < ~1,15 (onde o clamp 0.13 não domina).

### Pitfall 2: BBSE3 roteado para fora do RIM sem tratamento
**O que dá errado:** setor CVM não casa `seguradora` → motor ≠ rim → `a.intrinseco_motor` de outro
motor (ou None) comparado a um FV de banco. **Como evitar:** assertar/registrar `a.motor` por ticker;
se ≠ "rim", marcar exceção documentada (D-08) com nota. **Sinal:** `a.arquetipo != "financeira"` na BBSE3.

### Pitfall 3: FAIL silencioso escapando o gate
**O que dá errado:** 1 banco fora da banda sem nota passa despercebido. **Como evitar:** o loop
`for t in falhas: assert fv[t]["excecao_nota"]` (Q7). **Sinal:** teste verde com um desvio grande não
anotado — precisamente o que D-08 barra.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| RIM fade-sem-terminal ancorado no VPA (D-02) | RIM híbrido + valor terminal (Gordon sobre RI) | Fase 4 (04-01-SUMMARY) | ITUB4 R$23→R$32,9; é o que esta fase valida |
| "Calibração empírica deferida" nos comentários do config | BACKTEST-01 = Fase 5 (esta) | 2026-07-12 | config.yaml:242 já aponta a cesta ITUB4/BBAS3/BBSE3/BBDC4 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Setor CVM da BBSE3 pode não casar `seguradora` → rota ≠ RIM | Q1/Q9/Pitfall 2 | Baixo — o harness LÊ `a.motor` e trata; a suposição só antecipa a exceção D-08. Verificar na captura ao vivo |
| A2 | `out/` está no `.gitignore` (como saída gerada) | Runtime Inventory | Baixo — confirmar; se não estiver, adicionar `out/backtest_bancos.md` ou versioná-lo intencionalmente |
| A3 | Congelar `rf_local` como escalar reproduz o ke de todos os 4 bancos | Q2/Pitfall 1 | Médio — para ITUB4 o clamp 0.13 domina; validar na captura que o ke congelado bate o live por ticker |
| A4 | Os 4 bancos têm setor/beta/fundamentos que fazem `analisar_acao` produzir `a.intrinseco_motor` não-None | Q1/Q9 | Médio — se um degradar a None, é exceção D-08 (nota), não bug; confirmar na captura |

## Open Questions (RESOLVED)

1. **Setor CVM exato da BBSE3 e roteamento resultante**
   - Sabemos: hard-route financeira casa `banco`/`seguradora` por word-boundary (arquetipo.py:150-154).
   - Incerto: a string real da CVM para BB Seguridade.
   - Recomendação: resolver na captura ao vivo (D-05); registrar `a.arquetipo`/`a.motor` no snapshot.
   - **RESOLVED:** delegado ao Plan 05-01 Task 1/2 — a captura ao vivo grava `setor`, `motor_observado`/`arquetipo_observado` por ticker; se ≠ rim, vira exceção documentada (D-08) via `excecao_nota`.

2. **Valores de consenso da tabela de FV (D-01)**
   - Sabemos: faixa min/max por ticker, aprovada pelo usuário antes de versionar.
   - Incerto: os números (dependem de pesquisa de consenso na data-base).
   - Recomendação: task dedicada de pesquisa + aprovação do usuário ANTES da task do fixture YAML.
   - **RESOLVED:** Plan 05-02 Task 1 (pesquisa de consenso) → Task 2 (checkpoint de aprovação do usuário, bloqueante) → Task 3 (grava o fixture) — a ordem D-01 está travada.

3. **Invocação do script standalone (Discretion)**
   - Recomendação: função pura `rodar_cesta(snapshot, fair_values, cfg) -> resultados` reusada pelo
     teste E por um wrapper `scripts/backtest_bancos.py` — garante que script e teste dão o mesmo número.
   - **RESOLVED:** PATTERNS.md fixou `src/analista/backtest.py::rodar_cesta` (compartilhada) + wrapper `scripts/backtest_bancos.py` (Plan 05-03); o teste (Plan 05-04) importa a MESMA `rodar_cesta`.

## Sources

### Primary (HIGH confidence) — código lido nesta sessão
- `src/analista/report/report.py:23-73,183-240,312-420,844+` — AnaliseAcao, dispatch, intrinseco_motor
- `src/analista/core/motores.py:64-150` — rim(), ke_rim(), ResultadoRIM
- `src/analista/core/fundamentals.py:19-201` — CompanyData shape + métodos *_valuation
- `src/analista/ingest/build.py:40-117` — montar_empresa
- `src/analista/core/arquetipo.py:48-186` — roteamento financeira→rim, tokens
- `src/analista/core/lentes.py:37-196` — Graham, Bazin, metricas_par (P/VP,P/L)
- `src/analista/core/multiples.py:52-99` — preco_lucro, dividend_yield
- `src/analista/core/comparables.py` — ranking/regressão (contexto D-11)
- `src/analista/cli.py:52-87` — padrão cmd_analyze → out/TICKER.md
- `app.py:1053-1069` — receita canônica Graham/Bazin
- `config.yaml:196-258` — arquetipo tokens + motores.rim knobs
- `tests/test_vulc3_regressao.py` / `tests/test_motores.py` / `tests/test_lentes.py` — padrão golden
- `pyproject.toml:14-16` — config pytest
- `.planning/phases/04-.../04-01-SUMMARY.md` — números verificados do RIM calibrado

## Metadata

**Confidence breakdown:**
- Standard stack / APIs: HIGH — todas lidas file:line, assinaturas verificadas
- Padrão de teste: HIGH — molde vivo em test_vulc3_regressao.py
- Roteamento BBSE3: MEDIUM — depende da string de setor real (resolver na captura)
- Determinismo rf_local: HIGH no mecanismo, MEDIUM no impacto por-ticker (clamp)

**Research date:** 2026-07-12
**Valid until:** 30 dias (código estável; muda só se o loop D-12 recalibrar a Fase 4)

## RESEARCH COMPLETE
