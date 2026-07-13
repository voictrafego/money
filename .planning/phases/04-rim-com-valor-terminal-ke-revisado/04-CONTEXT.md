# Phase 4: RIM com Valor Terminal + Ke Revisado — Context (Iteração 2 / Loop D-12)

**Gathered:** 2026-07-13
**Status:** Ready for planning

> **Reabertura via loop D-12.** A Fase 4 (iteração 1) já foi executada e verificada
> (`04-01-SUMMARY.md`): o RIM ganhou valor terminal e o ITUB4 saiu de R$23→R$32,9. Mas o
> BACKTEST-01 da Fase 5 provou que a calibração **não generaliza** no cesto de bancos — só 1/4
> na banda ±15% do consenso. Este CONTEXT.md guia a **segunda iteração** (recalibração), não uma
> reescrita. Evidência: `.planning/phases/05-backtest-01-valida-o-na-cesta-de-bancos/05-04-SUMMARY.md`,
> `out/backtest_bancos.md`, e o blocker em `.planning/STATE.md`.

<domain>
## Phase Boundary

**Entrega:** recalibrar o motor RIM (config-driven, mudanças cirúrgicas) para que a **cesta de
bancos** (ITUB4/BBAS3/BBSE3/BBDC4) passe no gate do BACKTEST-01 — alvo **3/4 dentro da banda ±15%
do consenso + 1 exceção de arquétipo documentada** —, fechando o loop D-12 e destravando a Fase 6.

**Diagnóstico de partida** (RIM congelado × faixas de consenso ao vivo, banda ±15%):

| Ticker | RIM | Faixa consenso | Erro | Causa estrutural |
|--------|-----|----------------|------|------------------|
| ITUB4 | 32,88 | 30,50–50,00 | dentro | ✅ (não regredir) |
| BBAS3 | 45,60 | 20,00–39,00 | +54,6% | ROE atual alto vs mercado precificando queda (agro 2025) — **ou bug de dado `num_acoes`** |
| BBSE3 | 25,38 | 33,00–46,00 | −35,7% | seguradora capital-light (ROE ~50%, book pequeno) que o RIM ancorado-em-book não valua |
| BBDC4 | 10,47 | 15,00–24,00 | −46,3% | guarda anti-bad-bank usa ROE no vale; mercado precifica recuperação |

**In scope:** normalização through-cycle do ROE no valor terminal; tratamento/rota próprio para
seguradora (minimalista); calibração dos knobs de banco existentes (`config.yaml::motores.rim`);
manter os invariantes golden verdes.

**Out of scope:** reescrever o motor RIM; motor de valuation novo do zero; afrouxar a banda ±15% ou
o quórum do gate (D-07/D-08 são intocáveis — o gate cobra a calibração, não o contrário); mexer no
DDM/selo/lentes exceto onde o roteamento de seguradora exigir.

</domain>

<decisions>
## Implementation Decisions

### ROE forward vs. atual (BBAS3 + BBDC4)
- **D-01:** Normalizar o ROE **através do ciclo apenas no valor terminal** (a perpetuidade de
  Gordon sobre o RI terminal). Preservar o ROE atual (`roe0`) na janela explícita e **não** tocar
  no intrínseco de curto prazo — o ITUB4 (já dentro da banda) não pode regredir. A normalização é a
  alavanca única que cobre BBAS3 (ROE caindo) e BBDC4 (ROE recuperando), que são o **mesmo problema
  em direções opostas**.
- **D-02:** O turnaround do BBDC4 é resolvido pela normalização do D-01, **não** por um cap/knob
  próprio de "banco em turnaround". Sem proliferar tratamento por sub-tipo de banco.

### BBSE3 — arquétipo seguradora
- **D-03:** Seguradora capital-light recebe **tratamento/rota própria**, fora do bank-RIM ancorado
  em book. Preferência por **mudança minimalista**: um cap de excesso específico para seguradoras
  **ou** roteamento para um motor existente adequado a franquia/dividendo (ex.: DDM), o que for
  menor e mais reusável — **não** um motor de valuation novo do zero.
- **D-04:** A classificação/roteamento parte do setor CVM (BBSE3 = "Emp. Adm. Part. - Seguradoras e
  Corretoras", casou o token `seguradora`). O researcher define o ponto de corte exato do roteamento.

### Alvo de aceite (fecha o loop D-12)
- **D-05:** Sucesso = **3/4 dentro da banda ±15% + 1 exceção de arquétipo documentada** (usa a regra
  de anotação D-08 que o gate `test_backtest_bancos.py` já implementa). O slot de exceção esperado é
  a **BBSE3**; se o tratamento de seguradora (D-03) a fizer passar, vira 4/4 — o piso honesto é 3/4+1.
- **D-06:** Piso é **3/4** — 2/4 não honra o "a calibração generaliza" do milestone e não é aceitável.
- **D-07:** Gate **não afrouxa**: nem a banda ±15% (D-07 da Fase 5) nem o quórum. Quando a cesta
  cruzar 3/4, o `xfail(strict=True, raises=AssertionError)` de `test_backtest_bancos.py` acende
  `XPASS→FAIL` automaticamente — sinal de que o loop fechou; aí remove-se o marcador.

### Calibração global vs. por arquétipo
- **D-08:** Manter **um knob global de banco** (`excesso_sustentavel` etc. em `config.yaml`) — motor
  simples. A divergência de arquétipo é resolvida por **roteamento** (seguradora, D-03) e por
  **normalização do ROE terminal** (turnaround/ciclo, D-01), não por caps por sub-tipo. Não
  proliferar superfície de calibração (evita overfit por segmento).

### Ordem de ataque (obrigatória p/ o researcher)
- **D-09:** **PRIMEIRO descartar o bug de dado da BBAS3** (`num_acoes` dobrado inflando VPA/lucro por
  ação → +54%). Se o desvio for de dado, a BBAS3 se resolve **sem** tocar em calibração, e a tese de
  ROE-terminal (D-01) fica só para o BBDC4. Só atribuir BBAS3 ao ROE depois de confirmar o dado limpo.

### Claude's Discretion
- Forma exata da normalização through-cycle (blend com média setorial, mean-reversion, teto de
  excesso terminal, etc.) — researcher/planner decidem, respeitando D-01 (só terminal, não regride ITUB4).
- Mecanismo concreto do roteamento de seguradora (cap próprio vs. rota p/ DDM) — menor mudança que
  entregue BBSE3 dentro/perto da banda de consenso.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Evidência do loop D-12 (o que a recalibração precisa consertar)
- `.planning/phases/05-backtest-01-valida-o-na-cesta-de-bancos/05-04-SUMMARY.md` — o achado 1/4, os desvios por ticker e as hipóteses de causa
- `out/backtest_bancos.md` — tabela D-10 com as 4 âncoras por ticker (regenerável via `scripts/backtest_bancos.py`)
- `tests/fixtures/snapshot_bancos_2026-07-12.yaml` — RIM congelado por ticker (base offline determinística)
- `tests/fixtures/fair_values_bancos.yaml` — faixas de consenso ao vivo aprovadas (âncora-verdade)
- `tests/test_backtest_bancos.py` — o gate quórum-3/4-±15% + regra de anotação (o `xfail` a derrubar quando fechar)

### Iteração 1 da Fase 4 (o que já existe — não reescrever)
- `.planning/phases/04-rim-com-valor-terminal-ke-revisado/04-01-SUMMARY.md` — o RIM híbrido multiestágio, knobs e gate ITUB4 R$32-40
- `.planning/phases/04-rim-com-valor-terminal-ke-revisado/04-RESEARCH.md` — a tese do valor terminal (Ohlson/RI, P/B justo)
- `src/analista/core/motores.py::rim` — motor a recalibrar (valor terminal via `ddm.valor_gordon`)
- `config.yaml::motores.rim` — knobs `excesso_sustentavel`, `g_terminal`, `ke_g_spread_min`, `ke_teto`
- `src/analista/report/report.py::_intrinseco_por_motor` — dispatch (ramo `motor=='rim'` + roteamento de arquétipo)

### Invariantes que não podem quebrar
- `tests/test_ddm.py` (DDM Itaú R$37,22), `tests/test_vulc3_regressao.py` (capstone e2e), `tests/test_motores.py` (gate ITUB4 R$32-40 + bad-bank), firewall selo↛report — ver blocker em `.planning/STATE.md`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/ddm.py::valor_gordon` — primitiva de perpetuidade já reusada pelo RIM terminal; candidata natural para o tratamento de seguradora capital-light (D-03) se a rota for dividendo/franquia.
- `config.yaml::motores.rim` — todos os knobs de banco já são config-driven; a recalibração mexe em valores, não em código do corpo do motor (D-08).

### Established Patterns
- Knobs config-driven, zero magic constant no corpo do motor (Fase 4 it.1) — manter.
- Roteamento por arquétipo em `report._intrinseco_por_motor` (o ponto onde seguradora se separa de banco, D-03).
- TDD com gate duro que cobra o NÚMERO-ALVO (não só a direção) — a lição do v2.2; o gate do BACKTEST-01 já é esse mecanismo.

### Integration Points
- O harness `src/analista/backtest.py::rodar_cesta` consome `report.analisar_acao(...).intrinseco_motor` — qualquer mudança de calibração/roteamento se reflete automaticamente no backtest e no gate (mesma função no teste e no script).

</code_context>

<specifics>
## Specific Ideas

- Método do livro (*O Investidor em Ações de Dividendos*): favorece poder de lucro **sustentável /
  through-cycle**, não lucro pontual — reforça D-01 (normalizar o ROE terminal) como fiel ao método,
  não um hack para passar no gate.
- A BBSE3 é a **única não-banco** do cesto — daí ser o slot natural da exceção de arquétipo (D-05).

</specifics>

<deferred>
## Deferred Ideas

- **Motor de valuation dedicado para seguradoras** (embedded value / P/EV) — se o tratamento
  minimalista (D-03) não bastar, um motor próprio de seguradora é uma capacidade nova, de fase
  própria, não desta recalibração.
- **Normalização through-cycle na janela explícita inteira** (não só no terminal) — rejeitada agora
  (D-01) por mexer no ITUB4 que já funciona; reconsiderar só se a normalização terminal não bastar.

### Reviewed Todos (not folded)
None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-rim-com-valor-terminal-ke-revisado*
*Context gathered: 2026-07-13 (iteração 2 / loop D-12)*
