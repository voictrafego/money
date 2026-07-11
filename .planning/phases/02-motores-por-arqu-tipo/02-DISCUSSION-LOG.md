# Phase 2: Motores por Arquétipo - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-11
**Phase:** 2-Motores por Arquétipo
**Areas discussed:** Ke dos motores (RIM), Escopo do NAV/SOTP, Método sob custo-zero, Fronteira Fase 2×3

---

## Ke dos motores (RIM)

| Option | Description | Selected |
|--------|-------------|----------|
| Ke through-the-cycle | Ke por Selic normalizada (~10a); destrava ITUB4 ~R$40; DDM ao vivo vira lente conservadora | ✓ |
| Mesmo Ke ao vivo do DDM | RIM usa Ke~17,3% igual DDM; excesso só ~2% → ITUB4 fica ~R$26 (falha #1) | |
| Ke ao vivo com teto | Ke ao vivo com teto/haircut (~13–14%); meio-termo, exige calibrar | |

**User's choice:** Ke through-the-cycle → decisão D-01.
**Notes:** Correção factual pós-scout: o app **já** injeta a Selic through-the-cycle (`selic_ciclo_para_capm`,
média 10a) no `rf_local` — o Ke do CAPM ao vivo fica ~17% para banco por causa da média 10a elevada +
beta×ERP, não da Selic spot. Logo a decisão real é o RIM usar um **Ke estrutural mais baixo (~12,5%, ancorado
no golden do livro 12,48%)** que o CAPM ao vivo. A fonte exata do Ke estrutural fica a critério do
researcher/planner (rf normalizado + ERP de banco, Ke ancorado no livro, ou teto sobre o CAPM). Registrado na
nota factual de D-01 no CONTEXT.md.

---

## Ke dos motores (RIM) — persistência do excesso

| Option | Description | Selected |
|--------|-------------|----------|
| Fade até Ke no horizonte | Excesso de ROE decai rumo ao Ke em ~7–10a + terminal ancorado no VPA; prática-padrão | ✓ |
| Excesso persistente + terminal | Excesso persiste + perpetuidade com g; mais agressivo, risco de inflar | |
| Você decide | Horizonte/terminal a critério do planner | |

**User's choice:** Fade até Ke no horizonte → decisão D-02.
**Notes:** Coerente com a filosofia de honestidade/conservadorismo do projeto; nenhum banco rende acima do
custo de capital para sempre.

---

## Escopo do NAV/SOTP (holding, ENG-05)

| Option | Description | Selected |
|--------|-------------|----------|
| NAV simplificado (book) | NAV = PL/ações (VPA), rotulado como piso patrimonial; registry 5/5, critério #4 honesto | ✓ |
| Deferir ENG-05 | Holding fica com motor pendente; ajusta ROADMAP; critério #4 sai da fase | |
| SOTP real por segmento | Somar partes por segmento; frágil sob custo-zero, contra a natureza da fase | |

**User's choice:** NAV simplificado (book) → decisão D-03.
**Notes:** Brief marca ENG-05 como stretch; nenhum ticker-âncora é holding. NAV contábil via `lentes.vpa`,
rotulado honestamente como piso (não SOTP por segmento).

---

## Método sob custo-zero — cíclica (VALE3)

| Option | Description | Selected |
|--------|-------------|----------|
| P/L sobre lucro normalizado | Lucro médio 7–10a (já existe) × P/L justo; sem dívida líquida; menor risco de dado | ✓ |
| EV/EBITDA normalizado | EBITDA norm × múltiplo − dívida líquida; teoricamente apto mas mais frágil (dívida+D&A) | |
| Você decide | Planner escolhe conforme confiabilidade do pipeline | |

**User's choice:** P/L sobre lucro normalizado → decisão D-04.
**Notes:** Núcleo do critério #2 é valuar sobre lucro normalizado. Fonte do "P/L justo" a critério do planner.

---

## Método sob custo-zero — crescimento (WEGE3)

| Option | Description | Selected |
|--------|-------------|----------|
| Multi-estágio sobre lucro/FCF | Lucro (≈FCF) projetado por g_alto→g_estável, desc. Ke; captura reinvestimento; reusa 2 estágios | ✓ |
| Múltiplo relativo (P/L justo) | P/L justo × lucro projetado (1 passo); simples mas comprime a tese multi-estágio | |
| DCF de FCF puro | FCF = FCO − capex projetado + perpetuidade; depende de capex frágil | |

**User's choice:** Multi-estágio sobre lucro/FCF → decisão D-05.
**Notes:** Reusa a mecânica de dois estágios (do `ddm.ddm_dois_estagios` como função pura, ou helper genérico
extraído) sem tocar `core/ddm.py`.

---

## Fronteira Fase 2 × Fase 3

| Option | Description | Selected |
|--------|-------------|----------|
| Exibe número, selo suspenso | Motor calcula+exibe o intrínseco; selo/veredito segue suspenso; VER-01 fica na Fase 3 | ✓ |
| Motor já vira primário | Levanta a suspensão; selo consome o motor já nesta fase (puxa VER-01); mexe no firewall | |

**User's choice:** Exibe número, selo suspenso → decisão D-06.
**Notes:** Armadilha crítica identificada: quando o RIM for plugado, `motor_pendente` vira False e, se a
suspensão simplesmente cair, o ITUB4 **regride para "evitar"** via DDM (selo ainda consome DDM até a Fase 3).
Por isso a condição de suspensão migra de `motor_pendente` → "selo ainda não consome o motor do arquétipo".

## Claude's Discretion

- Fonte do "P/L justo" da cíclica (mediana própria/setorial/regressão existente).
- Fonte exata do Ke estrutural do RIM (rf normalizado + ERP de banco / Ke ancorado no livro / teto sobre CAPM).
- Thresholds e horizontes numéricos (anos do fade, anos da normalização, estágios do crescimento).
- Estrutura de código dos motores (assinaturas, reuso de `ddm_dois_estagios` vs helper genérico, rótulos no
  report/CLI, rebaixamento do DDM a "lente conservadora").

## Deferred Ideas

- SOTP real por segmento (holding).
- EV/EBITDA para cíclica.
- DCF de FCF puro com capex projetado.
- VER-01 / ENS-01 / SAN-01 / VER-02 → Fase 3 por design.
- Validação empírica / backtesting (BACKTEST-01, fora do milestone).
