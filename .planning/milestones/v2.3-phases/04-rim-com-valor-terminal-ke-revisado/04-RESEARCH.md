# Fase 4 (Iteração 2 / Loop D-12): RIM com Valor Terminal + Ke Revisado — Research da RECALIBRAÇÃO

**Researched:** 2026-07-13
**Domain:** Calibração de valuation (Residual Income Model) para generalizar numa cesta de bancos/seguradora da B3
**Confidence:** HIGH (números estimados foram COMPUTADOS sobre o snapshot congelado, não assumidos)

> Esta RESEARCH.md é da **iteração 2** (recalibração do loop D-12). A tese do valor terminal
> (iteração 1) está preservada em `04-RESEARCH-it1.md` e **não é re-pesquisada**. Aqui só o que a
> recalibração precisa: o veredito BBAS3 (dado × ROE), a fórmula da normalização through-cycle do
> ROE terminal, o mecanismo de roteamento da seguradora, os knobs, e os números pós-recalibração.

<user_constraints>
## User Constraints (from CONTEXT.md — iteração 2)

### Locked Decisions
- **D-01:** Normalizar o ROE **através do ciclo apenas no valor terminal** (perpetuidade de Gordon
  sobre o RI terminal). Preservar `roe0` na janela explícita; **não** tocar o intrínseco de curto
  prazo. ITUB4 (já dentro da banda) **não pode regredir**. A normalização é a alavanca única que
  cobre BBAS3 (ROE caindo) e BBDC4 (ROE recuperando) — mesmo problema em direções opostas.
- **D-02:** O turnaround do BBDC4 é resolvido pela normalização (D-01), **não** por cap/knob próprio
  de "banco em turnaround". Sem tratamento por sub-tipo de banco.
- **D-03:** Seguradora capital-light recebe **rota própria**, fora do bank-RIM ancorado em book.
  Preferência por mudança minimalista: cap de excesso específico **ou** roteamento a um motor
  existente (ex.: DDM) — **não** um motor de valuation novo do zero.
- **D-04:** Classificação/roteamento parte do setor CVM (BBSE3 = "Emp. Adm. Part. - Seguradoras e
  Corretoras", casou o token `seguradora`). O researcher define o ponto de corte exato.
- **D-05:** Sucesso = **3/4 dentro da banda ±15% + 1 exceção de arquétipo documentada** (regra de
  anotação D-08 do gate). Slot esperado = BBSE3; se o tratamento a fizer passar, vira 4/4.
- **D-06:** Piso honesto = **3/4**. 2/4 não é aceitável.
- **D-07:** Gate **não afrouxa**: nem banda ±15% nem quórum. Quando cruzar 3/4 o `xfail(strict)`
  vira `XPASS→FAIL` — remove-se o marcador (fechamento explícito do loop).
- **D-08:** **Um knob global de banco**. Divergência de arquétipo resolvida por **roteamento**
  (seguradora) + **normalização do ROE terminal** (ciclo/turnaround), não por caps por sub-tipo.
  Não proliferar superfície de calibração (evita overfit por segmento).
- **D-09 (ordem obrigatória):** **PRIMEIRO descartar o bug de dado da BBAS3** (`num_acoes` dobrado).
  Só atribuir BBAS3 ao ROE depois de confirmar o dado limpo.

### Claude's Discretion
- Forma exata da normalização through-cycle (blend setorial, mean-reversion, teto de excesso) —
  respeitando D-01 (só terminal, não regride ITUB4).
- Mecanismo concreto do roteamento de seguradora (cap próprio vs. rota DDM) — menor mudança que
  entregue BBSE3 dentro/perto da banda.

### Deferred Ideas (OUT OF SCOPE)
- Motor de valuation dedicado a seguradoras (embedded value / P/EV) — fase própria se o minimalista
  não bastar.
- Normalização through-cycle na janela explícita inteira (não só terminal) — rejeitada (mexe no ITUB4).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAL-01 | Calibrar o RIM (valor terminal / excesso sustentável) para generalizar na cesta | Normalização through-cycle do ROE terminal (§Alavanca 2) — computada: BBAS3 45,60→43,89, BBDC4 10,47→13,37, ITUB4 inalterado |
| CAL-02 | Ke estrutural revisado (ke_teto 0,14→0,13) | Já entregue na iteração 1 (ke=13% ativo em toda a cesta); esta iteração NÃO mexe no Ke — a alavanca passou a ser o ROE terminal (§Por que o Ke não é a alavanca) |
</phase_requirements>

## Summary

O diagnóstico do BACKTEST-01 (1/4 na banda) tem **três causas distintas**, e a recalibração é
cirúrgica e config/data-driven — nada de reescrever o RIM. Computei a decomposição do RIM sobre o
snapshot congelado (`vpa0 + vp_residual + vp_terminal` por ticker) e testei as alavancas
numericamente. Conclusões:

1. **BBAS3 (+54,6%) NÃO é bug de dado** (veredito D-09 cravado). O `num_acoes[2025]=5,71 bi` bate com
   as ~5,73 bi de ações reais do BB [VERIFIED]; o desdobramento 2:1 de 2024 é real e **imaterial ao
   RIM** (o motor só consome `num_acoes[último ano]`). O `+54,6%` é comportamento genuíno do modelo:
   o **VPA sozinho já é R$33,91** (acima do mid de consenso 29,5) porque o mercado precifica BBAS3
   **abaixo do book** (P/VP ~0,87) antecipando a queda de ROE do agro (ROE 2025 caiu a 8,9%),
   enquanto o RIM usa o ROE normalizado 3a (15,44%) acima do Ke (13%). **Resolve pela D-01, não por dado.**

2. **BBDC4 (−46,3%)** e **BBAS3** são o mesmo problema em direções opostas — a normalização
   **through-cycle do ROE no terminal** (mean-reversion à média histórica DO PRÓPRIO ticker) cobre
   ambos e **deixa o ITUB4 bit-idêntico** (prova matemática no §Por que ITUB4 não regride).

3. **BBSE3 (−35,7%)** é a única não-banco: o RIM ancorado em book (VPA=5,35, minúsculo) subvaloriza
   uma franquia capital-light. A rota mínima é **Gordon sobre o dividendo sustentável** (reusa
   `ddm.valor_gordon` + `c.dpa_recorrente()`), que aterrissa em **R$39,87 — em cima do mid (39,5)**.

**Primary recommendation:** Duas alavancas independentes, ambas config/data-driven, zero reescrita:
(1) parâmetro opcional `roe_terminal` em `motores.rim` (backward-safe) alimentado pelo ROE
through-cycle que o `report` computa da série; (2) sub-rota de seguradora em
`report._intrinseco_por_motor` via `ddm.valor_gordon`. Resultado computado: **4/4 na banda** (ou
3/4+BBSE3-documentada se a rota seguradora for adiada). ITUB4 inalterado por construção.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Normalização through-cycle do ROE terminal | `core/motores.py::rim` (param novo) | `report._intrinseco_por_motor` (computa e injeta o anchor) | O motor é primitiva pura; o anchor (média histórica) sai da série via `report`/`CompanyData` (fronteira FIX-04) |
| Cômputo do ROE through-cycle | `report._intrinseco_por_motor` | `CompanyData.roe(ano)` (já existe) | Reusa `c.roe(a)` por ano; zero método novo de valuation |
| Roteamento de seguradora | `report._intrinseco_por_motor` (ramo novo) | `core/arquetipo._setor_casa_token` (detecção) | O ponto onde arquétipo→motor se separa; detecção por token de setor CVM |
| Valuation da seguradora (franquia) | `core/ddm.py::valor_gordon` (reuso PURO) | `CompanyData.dpa_recorrente()` (já existe) | ddm.py INTOCADO; só é CHAMADO de um ramo novo no report |
| Gate de aceite (quórum 3/4 ±15%) | `tests/test_backtest_bancos.py` | `backtest.rodar_cesta` | Não muda; só o `xfail` cai quando cruzar o quórum (D-07) |

## Diagnóstico Computado (decomposição do RIM sobre o snapshot congelado)

Rodado com os inputs congelados de `snapshot_bancos_2026-07-12.yaml` (determinístico, offline):

| Ticker | vpa0 | roe0 (norm 3a) | ke | payout | fade_para | RIM = VPA + janela + terminal | terminal% | FV mid | desvio |
|--------|------|----------------|-----|--------|-----------|-------------------------------|-----------|--------|--------|
| ITUB4 | 19,00 | 19,31% | 13,00% | 46,7% | 17,50% | **32,88** = 19,00 + 8,15 + 5,73 | 17,4% | 40,2 | −18,3% (PASS) |
| BBAS3 | 33,91 | 15,44% | 13,00% | 39,3% | 15,44% (sem fade) | **45,60** = 33,91 + 6,36 + 5,33 | 11,7% | 29,5 | +54,6% (FAIL) |
| BBSE3 | 5,35 | 86,69% | 11,89% | 85,4% | 16,39% | **25,38** = 5,35 + 18,31 + 1,71 | 6,8% | 39,5 | −35,7% (FAIL) |
| BBDC4 | 15,93 | 10,08% | 13,00% | 38,3% | 10,08% (sem fade) | **10,47** = 15,93 − 3,16 − 2,30 | −22,0% | 19,5 | −46,3% (FAIL) |

**Leituras estruturais que isso força:**
- **BBAS3:** VPA (33,91) > mid de consenso (29,5). A janela (6,36) é **intocável** (D-01) → o piso
  alcançável mexendo só no terminal é `45,60 − 5,33 = 40,27`. Como a banda vai até 44,85, **BBAS3
  passa zerando/reduzindo o terminal**, mas aterrissa alto na banda (limitação honesta, §Riscos).
- **BBDC4:** janela e terminal **negativos** (ROE 10,08% < Ke 13% o tempo todo). Guarda anti-bad-bank
  (correta em si) fade a um excesso negativo; o mercado precifica recuperação forward.
- **BBSE3:** book minúsculo (5,35) + fade agressivo do ROE (86,69%→16,39%). O valor está no fluxo de
  lucro/franquia, não no patrimônio — o RIM ancorado em book não captura.
- **ITUB4:** o único cujo excesso de ROE (roe0−ke = 6,31pp) satura o cap `excesso_sustentavel` (4,5pp).

## Alavanca 1 — BBAS3: veredito D-09 (é ROE-terminal, NÃO bug de dado)

**Veredito: NÃO é bug de `num_acoes`.** Caminho de verificação executado:

1. **Ações reais do BB** ≈ **5,730 bilhões** [VERIFIED: statusinvest/stockanalysis, jul/2026]. O
   snapshot tem `num_acoes[2025]=5.708.689.674` — bate dentro de 0,4%. Logo `vpa0 = 193,57 bi /
   5,71 bi = R$33,91` está **correto** (P/VP de mercado = 20,58/33,91 ≈ 0,61, coerente com o
   P/VP ~0,6 histórico do BB).
2. **O desdobramento é real** (BB fez split ~2:1 em 2024): `num_acoes` salta 3,16 bi (2023) → 6,31 bi
   (2024) → 5,71 bi (2025). O valor 2024=6,31 bi é um artefato (média ponderada intra-ano do split),
   mas **IMATERIAL** — `motores.rim` só consome `num_acoes[último ano]=2025`. Os anos anteriores
   nunca entram no RIM.
3. **ROE independe de ações:** `roe_valuation = lucro_norm / PL_médio` e `payout = dividendos/lucro`
   (ações cancelam). Nenhum input do RIM (roe0, retenção, ke) muda com o split; só o `vpa0`, que usa
   o ano correto.

**Conclusão para o planner:** o `+54,6%` é o modelo, não o dado. A causa é o ROE normalizado backward
(15,44%, mediana de 2023-25 que descarta o colapso de 2025) ficar acima do Ke enquanto o consenso
precifica o forward abaixo do book. **Resolve pela normalização terminal (Alavanca 2), sem tocar
fixture/dado.** (Opcional, custo-zero: 1 linha de nota no snapshot confirmando que `num_acoes[2024]`
é artefato de split e imaterial — não é bloqueante.)

## Alavanca 2 — Normalização through-cycle do ROE TERMINAL (BBAS3 + BBDC4)

### Fundamento
Em equilíbrio competitivo o excesso de retorno (ROE − Ke) **reverte** — só um moat durável sustenta
excesso na perpetuidade (o `excesso_sustentavel` já modela isso). O livro (*O Investidor em Ações de
Dividendos*) favorece **poder de lucro through-cycle**, não pontual — reforça normalizar o ROE do RI
terminal à média do ciclo, fiel ao método [CITED: CONTEXT §specifics; Damodaran, "Normalized ROE =
average ROE over a full cycle"].

### Fórmula recomendada (a que passou nos testes)
Âncora = **ROE médio through-cycle DO PRÓPRIO ticker** (mediana dos `c.roe(ano)` sobre os ~10 anos),
aplicada **só no RI terminal**, ainda **capada pelo `excesso_sustentavel`**:

```
roe_terminal = ke + min(roe_ciclo − ke, excesso_sustentavel)     # excesso capado; PODE ser negativo (anti-bad-bank)
RI_terminal  = (roe_terminal − ke) · B_{n-1}                      # mesma base de book que o terminal legado
VP_terminal  = valor_gordon(RI_terminal·(1+g), ke, g) / (1+ke)^n
```

A **janela explícita (roe0, fade) fica intocada** (D-01). Só o RI_{n+1} da perpetuidade troca
`fade_para` por `roe_terminal`. `roe_ciclo` sai da série histórica via `report` (fronteira FIX-04) —
zero constante mágica no corpo do motor (D-08).

### ROE through-cycle computado (mediana dos `c.roe(ano)`)
| Ticker | roe0 (norm 3a) | ROE ciclo (mediana ~10a) | Direção da reversão |
|--------|----------------|--------------------------|---------------------|
| ITUB4 | 19,31% | 17,98% | excesso 4,98pp → **satura o cap 4,5pp** → terminal idêntico |
| BBAS3 | 15,44% | **14,66%** | reverte **para baixo** (excesso 2,44→1,66pp) |
| BBDC4 | 10,08% | **13,75%** | reverte **para cima** (excesso −2,92→+0,75pp) |
| BBSE3 | 86,69% | 81,26% | (não usa esta rota — vai para a de seguradora) |

### Efeito computado nos 4 tickers (mediana do ciclo, reversão terminal cheia)
| Ticker | RIM atual | RIM pós-normalização | vpa+janela+terminal | Banda ±15% | Veredito |
|--------|-----------|----------------------|---------------------|------------|----------|
| ITUB4 | 32,88 | **32,88 (inalterado)** | 19,00 + 8,15 + 5,73 | 25,9–57,5 | PASS |
| BBAS3 | 45,60 | **43,89** | 33,91 + 6,36 + 3,63 | 17,0–44,85 | PASS (alto na banda) |
| BBDC4 | 10,47 | **13,37** | 15,93 − 3,16 + 0,59 | 12,75–27,6 | PASS |
| BBSE3 | 25,38 | 25,38 | (inalterado por esta alavanca) | 28,05–52,9 | FAIL → vai p/ Alavanca 3 |

→ **3/4 PASS só com a Alavanca 2** (BBSE3 é o slot de exceção D-05).

**Variante testada e REJEITADA:** blend 50/50 (roe0 + ciclo) dá **2/4** (BBDC4 volta a falhar em
11,92). A reversão terminal precisa ser **cheia** (peso 1,0 no ciclo). Mediana ≈ média (44,60 vs
43,89 em BBAS3; 13,00 vs 13,37 em BBDC4) — **prefira mediana** (mais robusta ao ROE-colapso de 2025).

### Por que o ITUB4 NÃO regride (prova por construção)
Sempre que `roe_ciclo − ke ≥ excesso_sustentavel`, o `min(...)` satura no cap — **idêntico ao fade
terminal legado** (que também satura no cap). ITUB4: ciclo 17,98% → excesso 4,98pp ≥ 4,5pp → cap
morde → `roe_terminal = ke + 4,5pp = 17,5% = fade_para legado` → **RIM bit-idêntico (32,88)**.
Qualquer banco de qualidade cujo excesso through-cycle exceda o cap está protegido automaticamente.
A alavanca só MOVE tickers com excesso terminal ABAIXO do cap (BBAS3 1,66pp; BBDC4 −2,92→+0,75pp).

### Por que o Ke não é a alavanca (nesta iteração)
CAL-02 (ke_teto 0,14→0,13) já foi entregue na iteração 1 e o Ke=13% já está ativo nos 3 bancos.
Comprimir mais o Ke moveria TODOS na mesma direção (uniforme) — mas a falha é em **dois sentidos
opostos** (BBAS3 acima, BBDC4/BBSE3 abaixo), que um knob global de Ke não separa (finding 05-04).
Por isso a alavanca migrou do Ke para o ROE terminal (D-01).

## Alavanca 3 — Roteamento de seguradora (BBSE3)

### Mecanismo mínimo recomendado: rota Gordon-franquia (reuso PURO de `ddm.valor_gordon`)
```
dpa_sust = c.dpa_recorrente()                       # = payout_valuation × lpa_valuation (JÁ EXISTE) = R$3,83
V_seguradora = ddm.valor_gordon(dpa_sust·(1+g_estavel), ke_live, g_estavel)
```
- `ke_live` = CAPM ao vivo (`a.ke`, beta 0,31 → 12,36%), **não** o `ke_rim` (a seguradora não é
  banco de balanço large-cap).
- `g_estavel` = `cfg["ddm"]["g_estavel"]` (2,5%) — **zero knob numérico novo**.

**Resultado computado: R$39,87 — em cima do mid de consenso (39,5)**, dentro da banda [28,05; 52,9].
Faz BBSE3 o **4º PASS**.

### Alternativas testadas
| Rota | Valor BBSE3 | Veredito |
|------|-------------|----------|
| **Gordon(dpa_recorrente, ke_live, g=2,5%)** | **39,87** | ✅ **recomendada** (em cima do mid, reuso puro, zero knob) |
| DDM 2-estágios modelo-H (g_alto 12,4%) | 60,32 | ❌ acima da banda (g_alto de fundamentos explode p/ franquia) |
| Gordon(dpa_trailing_12m=6,87) | 71,43 | ❌ trailing carrega extraordinário |
| RIM cap seguradora 20pp (book-anchored) | 35,50 | ⚠️ funciona, mas é knob por sub-tipo (fere D-08) e menos principiado |
| RIM cap seguradora 10pp | 28,82 | ⚠️ passa raspando o piso; frágil |

A rota Gordon vence: é a **menor mudança reusável** (D-03), não prolifera knob (D-08), e é
economicamente correta para franquia capital-light de alto payout.

### Ponto de corte EXATO no código (D-04)
- **Detecção:** reusar `arquetipo._setor_casa_token(c.setor, ["seguradora"])` (casa por limite de
  palavra; BBSE3 setor = "Emp. Adm. Part. - Seguradoras e Corretoras" → casa). NÃO reimplementar match.
- **Local:** `report._intrinseco_por_motor`, ramo novo **antes** do `if motor == "rim"` (ou dentro
  dele, curto-circuitando). Retorna `V_seguradora`. Setar `a.motor = "seguradora"` (rótulo honesto).
- **Consequência no gate:** `test_backtest_cesta_rota_por_ticker` exige `excecao_nota` para
  `motor != "rim"` → **adicionar `excecao_nota` ao BBSE3** em `fair_values_bancos.yaml` documentando
  a rota ("seguradora capital-light → DDM-franquia/Gordon, fora do bank-RIM ancorado em book"). Isto
  É a exceção de arquétipo documentada de D-05.

### Fallback honesto
Se a Alavanca 3 for adiada, a Alavanca 2 sozinha entrega **3/4 + BBSE3 como falha documentada**
(adicionar `excecao_nota` ao BBSE3 satisfaz o loop de anotação do quórum-test). **Ambos os caminhos
fecham o loop D-12** e passam o gate. A rota Gordon é preferida (4/4, D-03).

## Knobs de Config (novos/alterados)

| Knob | Local | Default | WHY |
|------|-------|---------|-----|
| **`roe_terminal_stat`** (NOVO) | `config.yaml::motores.rim` | `"mediana"` | Estatística do ROE through-cycle usado no terminal (`mediana`\|`media`). Mediana é robusta ao colapso de ROE de 1 ano (agro 2025 do BBAS3). Único knob novo da Alavanca 2 (o anchor em si sai da série, não é constante). |
| `excesso_sustentavel` | `motores.rim` (existente) | 0,045 (**manter**) | O cap que protege o ITUB4 por construção (§prova). Testado: não precisa mudar. Mudá-lo mexe no ITUB4 — evitar. |
| `g_terminal`, `ke_g_spread_min`, `ke_teto`, `n_fade`, `erp_banco`, `ke_piso` | `motores.rim` (existentes) | **manter** | Iteração 1; a recalibração não os toca. |

**Seguradora:** **nenhum knob numérico novo** — reusa `ddm.g_estavel` (2,5%) + `dpa_recorrente()` +
`valor_gordon`. (Se quiser explicitar a lista de tokens da rota, reusar `arquetipo.financeiro_tokens`
que já contém `seguradora`; não criar bloco novo.)

Princípio D-08 honrado: **um** knob novo (`roe_terminal_stat`), divergência de arquétipo resolvida
por roteamento + normalização, não por caps por sub-tipo.

## Assinatura de `motores.rim` (backward-safe)

Adicionar **um parâmetro opcional** no fim da assinatura:
```python
def rim(vpa0, roe0, ke, retencao, n, excesso_sustentavel=0.0, g_terminal=None,
        ke_g_spread_min=0.03, fade_para=None, roe_terminal=None):
    ...
    # no bloco do terminal, se roe_terminal is not None:
    #   excesso_t = min(roe_terminal - ke, excesso_sustentavel)
    #   ri_terminal_base = excesso_t * b_{n-1}     # b_{n-1} = base do último RI da janela
    # senão: comportamento legado (ris[-1])
```
`roe_terminal=None` ⇒ **comportamento idêntico ao atual** ⇒ todos os goldens de `test_motores.py`
(que chamam sem esse arg) reproduzem bit-a-bit. O `report._intrinseco_por_motor` passa
`roe_terminal=roe_ciclo` só no ramo RIM.

## Impacto nos Goldens (o que atualizar, o que permanece)

| Teste / invariante | Impacto | Ação |
|--------------------|---------|------|
| `test_motores.py::test_rim_itub4_*` (chamadas diretas sem `roe_terminal`) | **Nenhum** (param default None = legado) | Nada |
| `test_motores.py::test_rim_bad_bank / roe_igual_ke / never_raise` | **Nenhum** | Nada |
| `test_ddm.py` (DDM Itaú R$37,22) | **Nenhum** (ddm.py INTOCADO; só CHAMADO) | Nada |
| `test_vulc3_regressao.py` (capstone e2e, VULC3 não é banco) | **Nenhum** | Nada |
| `test_selo.py` (firewall selo↛report) | **Nenhum** | Nada |
| `test_consistencia_modos.py` | **Nenhum** (mesma `analisar_acao`) | Nada |
| `test_backtest_bancos.py::test_backtest_cesta_rota_por_ticker` | ITUB4 fica em [30,40] (32,88); BBSE3 vira `motor="seguradora"` | Adicionar `excecao_nota` ao BBSE3 no fixture |
| `test_backtest_bancos.py::test_backtest_gate_quorum_e_anotacao` (`xfail(strict)`) | Vira **XPASS→FAIL** ao cruzar quórum | **Remover o marcador `@pytest.mark.xfail`** (fecha o loop D-12, D-07) |

**Não regride o ITUB4:** garantido por construção (o cap `excesso_sustentavel` morde idêntico ao
legado). Verificação sugerida no plano: assert `RIM(ITUB4) == 32,88` antes/depois (igualdade exata).

## Números Estimados Finais (pós-recalibração completa, contra a banda ±15%)

| Ticker | RIM final | Alavanca | Banda ±15% | Consenso mid | Veredito |
|--------|-----------|----------|------------|--------------|----------|
| ITUB4 | **32,88** | — (inalterado) | 25,93–57,50 | 40,2 | ✅ PASS |
| BBAS3 | **43,89** | 2 (ROE terminal ciclo) | 17,00–44,85 | 29,5 | ✅ PASS (alto na banda) |
| BBDC4 | **13,37** | 2 (ROE terminal ciclo) | 12,75–27,60 | 19,5 | ✅ PASS |
| BBSE3 | **39,87** | 3 (Gordon-franquia) | 28,05–52,90 | 39,5 | ✅ PASS (rota documentada) |

→ **4/4 na banda** (com a rota seguradora) — supera o piso D-05 (3/4+1). Sem a Alavanca 3: **3/4 +
BBSE3 exceção documentada** — também fecha o loop.

## Common Pitfalls

### Pitfall 1: normalizar o ROE também na janela explícita
**O que dá errado:** ITUB4 regride (viola D-01). **Como evitar:** o `roe_terminal` entra SÓ no RI da
perpetuidade; a janela mantém `roe0`/`fade_para`. A prova de não-regressão depende disso.

### Pitfall 2: usar blend parcial (roe0 × ciclo) no terminal
**O que dá errado:** BBDC4 volta a falhar (11,92 < 12,75) — 2/4. **Como evitar:** reversão terminal
**cheia** ao ciclo (peso 1,0). Confirmado computacionalmente.

### Pitfall 3: rotear seguradora para DDM 2-estágios (modelo-H) em vez de Gordon
**O que dá errado:** g_alto de fundamentos (12,4%) explode → R$60,32 (acima da banda). **Como
evitar:** Gordon de estágio único sobre o dividendo **sustentável** (`dpa_recorrente`), g=2,5%.

### Pitfall 4: usar `dpa_trailing_12m` na rota seguradora
**O que dá errado:** trailing carrega provento extraordinário → R$71,43. **Como evitar:**
`dpa_recorrente()` (payout normalizado × LPA normalizado), consistente com o resto do app (FIX-06).

### Pitfall 5: mudar `a.motor` de BBSE3 sem `excecao_nota` no fixture
**O que dá errado:** `test_backtest_cesta_rota_por_ticker` acusa "rota silenciosa" (FAIL). **Como
evitar:** adicionar `excecao_nota` ao BBSE3 em `fair_values_bancos.yaml` (é a exceção D-05/D-08).

### Pitfall 6: esquecer de remover o `xfail(strict)` ao cruzar o quórum
**O que dá errado:** `strict=True` transforma XPASS em FAIL — a suíte quebra "sem motivo aparente".
**Como evitar:** remover o marcador `@pytest.mark.xfail` de `test_backtest_gate_quorum_e_anotacao`
É PARTE da entrega (fechamento explícito do loop, D-07).

## Runtime State Inventory

Fase de recalibração de código/config — sem estado runtime externo.

| Categoria | Itens | Ação |
|-----------|-------|------|
| Dados armazenados | Nenhum — o snapshot congelado é fixture de teste, não datastore vivo. Verificado. | — |
| Config de serviço vivo | Nenhum — engine offline; sem serviço externo. Verificado. | — |
| Estado registrado no SO | Nenhum. Verificado. | — |
| Secrets/env vars | Nenhum. Verificado. | — |
| Artefatos de build | Nenhum — Python puro, sem compilação. Verificado. | — |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (já instalado; 442 passed baseline) |
| Config file | pytest via `tests/`; sem pytest.ini dedicado |
| Quick run | `pytest tests/test_motores.py tests/test_backtest_bancos.py -q` |
| Full suite | `pytest -q` |

### Phase Requirements → Test Map
| Req | Behavior | Test Type | Command | Existe? |
|-----|----------|-----------|---------|---------|
| CAL-01 | Cesta 3/4+ na banda ±15% | integração | `pytest tests/test_backtest_bancos.py::test_backtest_gate_quorum_e_anotacao -x` | ✅ (remover xfail) |
| CAL-01 | ITUB4 não regride (32,88) | unit | `pytest tests/test_motores.py::test_rim_itub4_live_alvo_32_40 -x` | ✅ |
| CAL-01 | Roteamento BBSE3 documentado | integração | `pytest tests/test_backtest_bancos.py::test_backtest_cesta_rota_por_ticker -x` | ✅ (add excecao_nota) |
| D-01 | RIM legado bit-idêntico sem `roe_terminal` | unit | `pytest tests/test_motores.py -q` | ✅ |

### Sampling Rate
- **Por commit:** `pytest tests/test_motores.py tests/test_backtest_bancos.py -q`
- **Por merge de wave:** `pytest -q` (suíte cheia, 442+)
- **Phase gate:** suíte cheia verde + `test_backtest_gate_quorum_e_anotacao` PASS (sem xfail).

### Wave 0 Gaps
- [ ] Novo unit test: `test_rim_terminal_normalizado` — `roe_terminal` abaixo do cap muda o valor;
  `roe_terminal` acima do cap = idêntico ao legado (prova a proteção do ITUB4). Cobre CAL-01/D-01.
- [ ] Novo unit test da rota seguradora: `V_seguradora(BBSE3) ≈ 39,87` a partir dos inputs congelados.

## Environment Availability

Sem dependências externas novas (Python + pytest + pyyaml já presentes; engine offline). SKIP de
probes de serviço.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Consenso ao vivo (fair_values) segue válido em jul/2026 | Números finais | Se o consenso mover, BBAS3 (alto na banda) é o mais frágil; re-checar a fixture aprovada |
| A2 | O split do BB em 2024 é ~2:1 (num_acoes 3,16→~5,7 bi) | Alavanca 1 | Baixo — o dado de mercado (~5,73 bi ações) corrobora e o RIM só usa o último ano |
| A3 | `roe_ciclo` = mediana dos `c.roe(ano)` disponíveis (1º ano é None por falta de PL−1) | Alavanca 2 | Baixo — testado; mediana ≈ média. Planner deve confirmar a série tem ≥5 pontos válidos por ticker |

## Open Questions (RESOLVED)

1. **BBAS3 aterrissa alto na banda (43,89 vs teto 44,85).** — RESOLVED: aceitar (passa o gate ±15%),
   registrado como o pass mais frágil; próxima alavanca é a Deferred "normalização na janela inteira".
   - Sabemos: VPA (33,91) > mid (29,5) e a janela residual (6,36) é intocável (D-01) → piso 40,27.
   - Incerto: robustez se o consenso live apertar ou o book/ROE do BB mudar.
   - Recomendação: aceitar (passa o gate ±15%, que é largo de propósito); registrar como o pass mais
     frágil. Se quebrar no futuro, a Deferred "normalização na janela inteira" é a próxima alavanca.

2. **BBSE3: 4/4 (rota Gordon) vs 3/4+exceção (só Alavanca 2).**
   - Recomendação: implementar a rota Gordon (D-03, 4/4, aterrissa no mid). Ambos fecham o loop; o
     planner pode fasear (Alavanca 2 primeiro → 3/4 verde → Alavanca 3 → 4/4).

## Sources

### Primary (HIGH confidence)
- Decomposição computada sobre `tests/fixtures/snapshot_bancos_2026-07-12.yaml` via `analista.backtest`
  + `analista.core.motores` (determinístico, offline) — todos os números RIM/pós-recalibração.
- `src/analista/core/motores.py::rim`, `core/ddm.py::valor_gordon`, `report._intrinseco_por_motor`,
  `core/fundamentals.py` (roe_valuation/dpa_recorrente), `core/arquetipo._setor_casa_token` — lidos.
- `04-CONTEXT.md` (iteração 2), `05-04-SUMMARY.md`, `out/backtest_bancos.md`, `test_motores.py`,
  `test_backtest_bancos.py` — lidos.

### Secondary (MEDIUM confidence)
- Nº de ações do BB (~5,73 bi) e split 2024 — statusinvest.com.br/acoes/bbas3, stockanalysis.com
  (jul/2026); corrobora `num_acoes[2025]` do snapshot (veredito D-09).

## Metadata

**Confidence breakdown:**
- Veredito BBAS3 (não é bug de dado): HIGH — dado de mercado corrobora + prova de que o split é imaterial ao RIM.
- Normalização terminal (números): HIGH — computada sobre inputs congelados, não assumida.
- Rota seguradora (39,87): HIGH — computada; reuso de primitiva testada.
- Não-regressão ITUB4: HIGH — prova por construção (cap satura idêntico) + valor bit-idêntico.

**Research date:** 2026-07-13
**Valid until:** enquanto `fair_values_bancos.yaml` (consenso aprovado) e o snapshot congelado não mudarem.

**Fontes web:**
- [BBAS3 - statusinvest](https://statusinvest.com.br/acoes/bbas3)
- [BBAS3 - stockanalysis](https://stockanalysis.com/quote/bvmf/BBAS3/)
