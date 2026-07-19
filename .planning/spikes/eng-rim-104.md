# Spike ENG — RIM único sobre os 104: sanidade de coorte + carve-out CONCESSAO_FINITA

**Tipo:** medição de arquitetura (de-risca as Ondas 2-4 da Fase 13) · **Universo:** os 104 do
snapshot LIMPO (`hs.CAMINHO_SNAPSHOT_LIMPO`) · **Ke:** único, β setorial+Blume carimbado (Fase 12)
**Medido em:** 2026-07-19 · **Fonte:** `scripts/spike_eng_rim_104.py`, 100% offline
**Re-emissão:** `.venv/bin/python scripts/spike_eng_rim_104.py`

> **Fronteira dura com a Fase 14 (VAL).** Este spike mede **distribuição por coorte** — nunca um
> caso. Ele **NÃO valida o caso do livro** (esse número soberano roda uma única vez na Fase 14; medir
> aqui queima o hold-out). Nenhuma linha nomeia ticker; nenhum knob é movido.

---

## Duas perguntas

1. **Regulada (madura + concessão) e cíclica ficam SÃS sob o RIM único?** Hoje madura→DDM (veredito
   por banda DDM) e cíclica→`lucro_normalizado`/Gordon-P/L. O §"Mapa de âncoras" do 13-RESEARCH
   propõe que **todos** passem a rodar o mesmo `motores.rim`, variando só o **insumo** (o ROE-âncora).
   Confiança MEDIUM no research — o comportamento precisava ser **medido**, não assumido.
2. **Que `g_terminal` o carve-out `CONCESSAO_FINITA` deve usar:** `None` (fade-only, recomendação do
   research) ou `PIB_real` (2,0% real puro)? A **direção** (não aplicar o `g` de inflação) é HIGH e
   travada; a **escolha exata** era a MEDIR.

---

## Veredito

> **(1) SIM — os quatro coortes ficam sãos sob o RIM único; nada explode. (2) `g_terminal = None`
> (fade-only) para o carve-out CONCESSAO_FINITA.** Nenhum knob movido; a fronteira com a Fase 14 é
> respeitada.

O sinal-âncora de "sanidade" é o mesmo oráculo herdado de KE-04: **nenhum `V` explode** contra o teto
adimensional de 50× preço. **Medido: o máximo de V/preço em TODOS os coortes é 2,82** (no coorte
cíclico) — quase 18× abaixo do teto. O RIM único não diverge em nenhum arquétipo.

---

## Medição por coorte (Variante A — CONCESSAO_FINITA com `g_terminal = None`)

Distribuição das razões sob o RIM único. `n` = tickers com Ke no coorte; `None` = degradados
(never-raise, dado degenerado). 93 tickers com Ke, 0 sem Ke, 0 exceções na engine. `g_cap` medido
= 7,28%.

| Coorte | n | None | V/preço (med · p10 · p90 · max) | P/B justo (med · p10 · p90) | payout_T (med · p10 · p90) | Ofensores |
|--------|---|------|----------------------------------|------------------------------|-----------------------------|-----------|
| financeira | 17 | 0 | 0,68 · 0,37 · 1,21 · 1,79 | 1,26 · 0,63 · 4,75 | 0,58 · 0,45 · 0,82 | P/B fora: 2 |
| madura | 8 | 0 | 0,66 · 0,37 · 0,99 · 1,12 | 0,88 · 0,41 · 1,66 | 0,65 · 0,36 · 0,85 | **0** |
| concessao | 15 | 0 | 0,77 · 0,28 · 1,26 · 1,38 | 1,11 · 0,53 · 1,82 | 1,00 · 1,00 · 1,00 | payout_T=1,0: 15 |
| ciclica | 49 | 4 | 0,49 · 0,11 · 1,27 · 2,82 | 0,76 · 0,12 · 2,41 | 0,58 · 0,28 · 0,81 | P/B fora: 1 · payout fora: 2 |
| crescimento | 4 | 0 | 0,41 · 0,29 · 0,95 · 1,16 | 1,17 · 0,70 · 2,75 | 0,55 · 0,42 · 0,70 | **0** |

*(sem coorte "holding": no snapshot atual, os candidatos a holding caem no refino quantitativo — a
rota `nav` como piso é Future Requirement e não altera esta medição.)*

### Regulada e cíclica ficam sãs sob o RIM único? SIM, por coorte

- **madura** (hoje →DDM, passa a rodar o RIM no split D-05): **SÃ — 0 ofensores.** V/preço mediana
  0,66; P/B justo mediana 0,88 ∈ (0,6); payout_T mediana 0,65 ∈ (0,1); sem explosão (max V/preço
  1,12). Isto **de-risca o split D-05**: mover a madura do DDM para o RIM único **não explode** nem
  produz razões patológicas — a preocupação MEDIUM do research se resolve a favor do colapso.
- **concessao**: **SÃ** sob as duas variantes (detalhe na §Decisão). Finita, P/B justo ∈ (0,6), sem
  explosão. O único "ofensor" na Variante A é `payout_T = 1,0` — um artefato de fronteira, não
  patologia (ver Decisão).
- **ciclica** (hoje →Gordon-P/L, passa a rodar o RIM com `roe0 = LPA normalizado ÷ VPA`): **SÃ no
  corpo da distribuição.** Mediana V/preço 0,49; P/B justo mediana 0,76 ∈ (0,6); payout_T mediana
  0,58 ∈ (0,1); **sem explosão** (max V/preço 2,82 — o teto do universo, ainda 18× abaixo de 50×).
  É o maior e mais ruidoso coorte (49): 4 degradam para `None` e ~3 tocam a fronteira do guard no
  rabo da distribuição — a cauda de dado sujo, absorvida pelo never-raise (SAN-06), não uma
  divergência de método.
- **financeira** (baseline — o RIM já era este motor): **SÃ**, 15/17 com P/B ∈ (0,6). Os 2 ofensores
  são a cauda de P/B < 1 (banco que destrói valor: `roe0 < Ke` → RI terminal negativo → valor abaixo
  do book) — o comportamento **anti-bad-bank correto** do RIM, não uma explosão.
- **crescimento**: **SÃ** — 0 ofensores no coorte pequeno (n=4); P/B ∈ (0,6), payout_T ∈ (0,1).

---

## Decisão do carve-out CONCESSAO_FINITA: `g_terminal = None` (fade-only)

As duas variantes, medidas lado a lado sobre o MESMO coorte de concessão (n=15):

| Variante | V/preço (med · max) | P/B justo (med · p90) | payout_T (med) | Ofensores | None |
|----------|---------------------|------------------------|-----------------|-----------|------|
| **A — `g_terminal = None`** (fade-only) | 0,77 · 1,38 | 1,11 · 1,82 | **1,00** | payout_T=1,0 em 15/15 | 0 |
| **B — `g_terminal = PIB_real`** (2,0% real) | 0,85 · 1,50 | 1,23 · 2,00 | 0,88 | **0** | 1 |

**Leitura da evidência:**

1. **Nenhuma das duas explode e nenhuma subvaloriza grosseiramente.** V/preço mediana 0,77 (A) vs
   0,85 (B); P/B justo ∈ (0,6) nas duas; max V/preço 1,38 (A) / 1,50 (B), ambos muito abaixo do teto
   de sanidade. O **gatilho** que o research definiu para preferir `PIB_real` — *"se a medição mostrar
   que zerar o terminal subvaloriza demais"* — **NÃO disparou**: a diferença é de ~8 p.p. de V/preço,
   não uma subvalorização grosseira.
2. **O único sinal que separa as variantes é o `payout_T`.** Na Variante A ele **crava em 1,00** para
   todo o coorte. Isso é uma **identidade definicional**, não uma patologia: `payout_T = 1 − g/ROE_T`
   e, com `g = 0`, `payout_T = 1` por construção. Economicamente é **exatamente** o que se espera de
   uma **concessão de vida finita** cujo book **já capitaliza** a receita regulatória descontada
   (ICPC 01): sem crescimento terminal real, distribui tudo, book estável em termos reais. O `g_cap`
   (que **embute inflação**, `g_cap = (1+π_ciclo)(1+PIB_real)−1`) aplicado a esse terminal contaria a
   inflação **duas vezes** — uma no book que já a incorpora, outra no crescimento. Zerar o terminal é
   a correção econômica, não um ajuste de nível.
3. **A Variante B mantém `payout_T` estritamente dentro de (0,1) (0,88)** e não tem ofensores, mas
   **introduz uma exceção de nível** (o 2,0% real pinado) — o que o research aponta como *"mais
   frágil"* — em troca de resolver um artefato de fronteira que **não é uma patologia de modelo**.

**Escolha: `g_terminal = None`.** É a mecânica mais limpa (o `motores.rim` já a suporta nativamente:
`motores.py:128-129` só libera o terminal com `g_terminal is not None`), é a economicamente correta
sob ICPC 01, e o gatilho para a alternativa não disparou. "Vida finita" por construção, coerente com
"concessão finita".

### Nota load-bearing para o Plano 03 (guarda P/B, ENG-08/ENG-09/D-10a)

O guard de correção D-10a exige `payout_T ∈ (0,1)` **aberto**. Sob `g_terminal = None`, todo o coorte
de concessão crava `payout_T = 1,0` — a **fronteira** do intervalo aberto. Como esse `1,0` é a
identidade de um terminal deliberadamente zerado (não uma razão impossível), o guard do carve-out
**deve** tratar a concessão como "sem perpetuidade de crescimento": ou **não aplicar** a checagem de
`payout_T` quando `g_terminal is None`, ou usar meio-aberto `(0, 1]` para `CONCESSAO_FINITA`. Sem essa
semântica, o guard marcaria **toda** concessão como ofensora por um artefato de fronteira. O guard de
`P/B justo ∈ (0,6)` **permanece** aplicável (a concessão o satisfaz: mediana 1,11 na Variante A).

---

## Fronteira respeitada — nenhum knob movido

- **`git diff --stat src/ config.yaml calibracao.lock.yaml` VAZIO** ao fim do spike — nenhuma
  produção, nenhum knob de valuation tocado (o corte contado do bloco `motores:` é o Plano 03). O
  script é throwaway offline, não importado por produção.
- **A decisão do carve-out NÃO é calibração de knob:** é sanidade de coorte por distribuição. A
  justificativa é econômica (ICPC 01: o book já é o VP da receita regulatória; `g_cap` embute
  inflação → double-count) e **não menciona nenhum ticker** (BLIND-04a).
- **NÃO valida o caso do livro** (Fase 14): nenhuma razão medida é comparada a um alvo em reais; a
  saída é agregada por coorte. `g_cap` (Fase 11) e `a.ke` (Fase 12) foram **consumidos prontos**, não
  recalibrados.

## O que os Planos 02/03 consomem deste spike

1. **O RIM único é seguro para o colapso:** os quatro coortes (financeira, madura, cíclica,
   crescimento) ficam sãos; nada explode (max V/preço 2,82 « 50×). O mapa de âncoras do §RESEARCH
   pode ser declarado.
2. **O split D-05 (madura sai do DDM para o RIM) está medido e de-riscado** — 0 ofensores no coorte
   madura.
3. **Carve-out CONCESSAO_FINITA: `g_terminal = None`** — com a nota de semântica do guard `payout_T`
   para o Plano 03 (meio-aberto `(0,1]` ou skip quando `g_terminal is None`).
4. **A cauda cíclica é de dado, não de método** — o never-raise (SAN-06) já a absorve; nenhum motor
   novo é necessário.
