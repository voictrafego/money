# Phase 4: RIM com Valor Terminal + Ke Revisado — Research

**Researched:** 2026-07-12
**Domain:** Residual Income Valuation (Ohlson/CFA), custo de capital de bancos (Damodaran), engine Python pura
**Confidence:** HIGH (teoria + números medidos no próprio código)

## Summary

O motor RIM atual (`motores.rim`) ancora bancos de qualidade perto do VPA porque a estrutura
**fade-para-zero-sem-terminal (D-02)** joga fora o valor econômico que o banco cria DEPOIS do
horizonte explícito de 10 anos. Confirmado numericamente: com os inputs live do ITUB4
(VPA≈19, ROE≈19,3%, retenção≈0,533, n=10), o RIM atual entrega **R$23–26** varrendo Ke de
10,5%→14% — o Ke move só ~R$3, **não é a alavanca**. A alavanca é o **valor terminal**
(perpetuidade do residual income), exatamente o que o modelo hoje não tem. `[VERIFIED: cálculo local]`

A formulação teoricamente fundada é o **Modelo de Renda Residual multiestágio** (CFA Level 2 /
Ohlson): janela explícita de residual income + **continuing value** no fim do horizonte. Há duas
variantes canônicas do continuing value — (i) **perpetuidade de Gordon** sobre o RI terminal
crescendo a `g`, e (ii) **fator de persistência ω** (Ohlson) que decai o RI. `[CITED: CFA L2 /
analystnotes / breakingdownfinance]` Testei ambas mais o P/B justo puro e um múltiplo de saída, e
recomendo um **híbrido**: manter a janela de fade, mas fazê-la convergir para um **excesso
sustentável limitado** (não a zero, não ao excesso cheio eterno) e capitalizar o RI terminal como
**perpetuidade de Gordon** via reuso de `ddm.valor_gordon`.

**Primary recommendation:** RIM híbrido — a janela de fade converge para `Ke + excesso_sustentavel`
(cap ~4,5pp) e adiciona um valor terminal = `valor_gordon(RI_{n+1}, Ke, g_terminal)` descontado.
Com `excesso_sustentavel=0.045`, `g_terminal=0.025` e Ke revisto para 0,13 (CAL-02), **ITUB4 ≈
R$32,9** (terminal ≈17% do valor) — dentro do alvo R$32–40, mesma ordem de Graham (R$39,88) e do
preço (R$44,30), e materialmente acima dos R$23 atuais. `[VERIFIED: cálculo local]`

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Valor terminal do RIM (perpetuidade de RI) | `core/motores.py::rim` (função pura) | `core/ddm.py::valor_gordon` (reuso) | O motor COMPÕE a primitiva testada de Gordon; não reimplementa perpetuidade |
| Ke estrutural do banco (revisão CAL-02) | `core/motores.py::ke_rim` + `config.yaml` | `core/capm.py` (intocado, só leitura via ke_live) | Ke do RIM é knob de config, clampado; capm.py permanece a referência ao vivo |
| Dispatch dos novos knobs → motor | `report/report.py::_intrinseco_motor` (linhas 202-210) | `config.yaml::motores.rim` | report lê cfg e passa parâmetros; app.py só lê o resultado |
| Âncoras de validação (Fase 5) | `core/lentes.py` (Graham/Bazin, intocado) | — | Fornecem os números-verdade contra os quais o RIM é cobrado |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAL-01 | RIM ganha valor terminal parametrizado, fundamento teórico, ITUB4 ~R$32-40 | Formulação híbrida recomendada (§Architecture Patterns); números concretos por Ke em §Formulação do Valor Terminal; knobs em §Standard Stack/config |
| CAL-02 | Ke do RIM revisado como ajuste secundário (rever teto 14% / erp_banco) | §Reconciliação de Ke — Damodaran mature ERP 4,23% + Selic já embute risco-país; recomendação `ke_teto` 0.14→0.13 (move ~R$2) |
</phase_requirements>

> **Nota:** Não existe CONTEXT.md para esta fase (a pasta `04-*` estava vazia). Não há decisões
> travadas de discussão a copiar; as restrições vêm de REQUIREMENTS.md, PROJECT.md (D-01/D-02) e
> CLAUDE.md. A seção Assumptions Log lista o que precisa de confirmação do usuário.

## Formulação do Valor Terminal — 4 abordagens comparadas

Todos os números abaixo são **ITUB4 live** (VPA=19, ROE0=0,193, retenção=0,533, n=10, g=0,025),
computados localmente. `[VERIFIED: cálculo local]` Baseline atual (fade→Ke, D-02): **R$23–26**.

| # | Abordagem | Ke=0.11 | Ke=0.125 | Ke=0.14 | Fundamento | Risco |
|---|-----------|---------|----------|---------|------------|-------|
| (a) | **P/B justo puro** `VPA·(ROE−g)/(Ke−g)`, sem janela | 37,6 | 31,9 | 27,8 | Single-stage RIM / Gordon (CFA) | Abandona a janela de fade; assume ROE e g constantes p/ sempre desde o ano 0; no Ke=0.14 atual fica ABAIXO do alvo |
| (b) | **Híbrido excesso cheio** (sem fade) + perpetuidade RI g=0.025 | 49,0 | 39,4 | 32,5 | RIM multiestágio, ω→persistência total | **Explosivo** com Ke baixo (49); assume moat cheio eterno; **over-valua banco medíocre** |
| (b') | **Persistência ω (Ohlson)**, excesso flat na janela + `RI_n·ω/(1+Ke−ω)` | 33,6–36,3 | 30,0–31,9 | 27,0–28,2 | **Canônico CFA L2** (ω≈0,62 empírico) | Conservador — exige Ke≈0,11 p/ bater o alvo, o que joga o peso no Ke (contraria CAL-02) |
| (c) | **Fade parcial a excesso sustentável (capped) + perpetuidade Gordon** ← RECOMENDADO | 37,6 | 33,9 | 31,0 | RIM multiestágio c/ período de vantagem competitiva | Requer 2 knobs; número depende do cap; guarda anti-bad-bank obrigatória |
| (d) | **Múltiplo de saída** (P/B terminal sobre book_n) | 33–40 | 31–38 | 29–35 | Exit-multiple (prática de M&A) | O book_n compõe p/ ~R$42; o terminal domina; P/B_exit vira **fator de fudge** ancorado em pares |

### Por que (c) — o híbrido — e não (a)/(b')/(d)

- **(a)** é o mais limpo (livro-texto), mas no Ke=0,14 atual entrega R$27,8 (< alvo) e **descarta
  toda a máquina de fade** — mudança grande, e assume vantagem competitiva constante para sempre
  desde hoje (irreal para 10 anos à frente).
- **(b') persistência ω** é o mais canônico do CFA, porém é o mais conservador: só bate o alvo com
  Ke≈0,11, empurrando o trabalho pesado para o Ke — o que **contraria CAL-02** (Ke deve ser a
  alavanca fina ~R$3, não o conserto principal). Mistura clean-surplus (book cresce) com decaimento
  ω do RI é teoricamente desconfortável.
- **(d)** faz o valor depender do `book_n` composto a 10,3%/ano por 10 anos (→ ~R$42) × um P/B
  escolhido a dedo — na prática um fudge factor. Rejeitado por CAL-01 exigir "fundamento teórico,
  não fator de fudge".
- **(c)** hitta o alvo **principalmente pelo valor terminal** (Ke fica secundário, como CAL-02
  pede): terminal ≈16–22% do valor. Reusa `ddm.valor_gordon`. Com a guarda de cap correta, **não
  é explosivo** e **não over-valua bancos ruins** (ver Pitfalls).

### Sensibilidade ao cap de excesso sustentável (recipe (c), g=0.025)

| excesso_sustentavel | Ke=0.11 | Ke=0.125 | Ke=0.13 | Ke=0.14 |
|---------------------|---------|----------|---------|---------|
| 0.030 | 33,5 | 30,6 | 29,7 | 28,2 |
| 0.040 | 36,2 | 32,8 | 31,8 | 30,0 |
| **0.045** | **37,6** | **33,9** | **32,9** | 31,0 |
| 0.050 | 39,0 | 35,1 | 33,9 | 31,9 |

**Recipe recomendada:** `excesso_sustentavel=0.045`, `g_terminal=0.025`, `ke_teto=0.13` →
**ITUB4 ≈ R$32,9**. `[VERIFIED: cálculo local]`

## O g de perpetuidade e a estabilidade numérica

- **Qual g:** reutilizar o `g_estavel=0.025` que já existe em `config.yaml::ddm.g_estavel`
  (crescimento ≤ PIB, Focus/BCB). `[VERIFIED: config.yaml linha 90]` Recomendo declarar um
  `motores.rim.g_terminal: 0.025` explícito (localidade/independência do motor, espelha o valor do
  DDM mas não acopla os blocos — coerente com o padrão anti-rebaseline do projeto).
- **Explosão (Ke−g)→0:** `ddm.valor_gordon` já retorna `None` quando `ke−g<=0`
  `[VERIFIED: ddm.py:44]`, mas valores **próximos** de zero inflam o terminal. Medido: com g
  destravado a 0,08–0,10 o modelo estoura/degrada. `[VERIFIED: cálculo local]`
- **Guarda recomendada:** exigir `Ke − g_terminal ≥ spread_min` (sugiro `0.03`) antes de calcular o
  terminal; se violar, degrada para o fade-only (never-raise). Como `g_terminal` é fixo em 0,025 e
  `ke_piso=0.11`, o spread mínimo real é 0,085 — folgado; a guarda protege configs futuros.
- **NÃO crescer o book na perpetuidade acima de g_terminal:** o RI terminal cresce a `g_terminal`,
  não à taxa de crescimento do book na janela (10,3%). Usar 10,3% no terminal seria assumir
  reinvestimento a ROE-excesso eterno — a fonte clássica de RIM explosivo.

## Standard Stack

Nenhuma biblioteca nova. O trabalho é aritmético em funções puras já existentes.

### Reuso (não reinventar)
| Primitiva | Onde | Uso no terminal |
|-----------|------|-----------------|
| `ddm.valor_gordon(dpa1, ke, g)` | `core/ddm.py:37` | `= RI_{n+1}/(Ke−g)` — a perpetuidade do RI terminal. `[VERIFIED: ddm.py:37-46]` |
| `lentes.vpa(pl, n_acoes)` | `core/lentes.py:51` | VPA0 (já usado no dispatch). `[VERIFIED: report.py:204]` |
| `motores.ke_rim(beta, cfg)` | `core/motores.py:98` | Ke estrutural clampado (CAL-02 mexe nos knobs, não na função) |

### Novos knobs em `config.yaml` (bloco `motores.rim`)
```yaml
motores:
  rim:
    erp_banco: 0.045          # (existente) mantido — Damodaran mature ERP ~4,23%
    ke_piso: 0.11             # (existente)
    ke_teto: 0.13             # CAL-02: revisar de 0.14 → 0.13 (documentar; move ~R$2)
    n_fade: 10                # (existente)
    excesso_sustentavel: 0.045  # NOVO — cap do excesso de ROE sobre Ke que persiste (moat durável ~4,5pp)
    g_terminal: 0.025           # NOVO — g do RI na perpetuidade (espelha ddm.g_estavel; guarda Ke−g)
    ke_g_spread_min: 0.03       # NOVO (opcional) — piso de (Ke−g_terminal) p/ liberar o terminal; senão fade-only
```
**Verificação de knobs existentes:** `erp_banco/ke_piso/ke_teto/n_fade` confirmados em
`config.yaml:230-239`. `[VERIFIED: config.yaml]`

## Architecture Patterns

### Fluxo do cálculo (RIM híbrido recomendado)

```
report.analisar_acao
  └─ _intrinseco_motor(motor="rim")            report.py:202-210
       ├─ vpa0   = lentes.vpa(PL, n_acoes)
       ├─ roe0   = c.roe_valuation()
       ├─ ke     = motores.ke_rim(beta, cfg)    # clampado [ke_piso, ke_teto], ≤ ke_live
       ├─ ret    = 1 - payout_valuation()
       └─ motores.rim(vpa0, roe0, ke, ret, n, excesso_sustentavel, g_terminal, ...)
            │
            ├─ JANELA (t=1..n):   fade_para = ke + min(roe0−ke, excesso_sustentavel)
            │     RI_t = (ROE_t − Ke)·B_{t-1};  VP += RI_t/(1+Ke)^t
            │     B_t = B_{t-1}·(1 + ROE_t·ret)          # clean surplus (inalterado)
            │
            ├─ TERMINAL (se Ke−g ≥ spread_min):
            │     RI_{n+1} = RI_n·(1+g_terminal)
            │     TV = ddm.valor_gordon(RI_{n+1}, Ke, g_terminal)   # reuso
            │     VP_terminal = TV/(1+Ke)^n
            │
            └─ V0 = VPA0 + VP_janela + VP_terminal
```

### Pattern 1: fade parcial a excesso sustentável (substitui o fade-para-Ke de D-02)
**What:** `fade_para = ke + min(roe0 − ke, excesso_sustentavel)`, com `max(0, ...)` no cap.
**When:** sempre no motor RIM.
**Por que o `min(roe0−ke, cap)`:** é a guarda anti-bad-bank. Se `roe0 < ke` (banco que destrói
valor), `roe0−ke` é negativo → `fade_para < ke` → RI terminal negativo → **valor ABAIXO do book**
(correto). Se `roe0 ≫ ke` (super-banco), o cap trava o excesso perpétuo em 4,5pp (não assume moat
cheio eterno). `[VERIFIED: cálculo local — bad bank ROE=0.10<Ke=0.125 → P/B=0.73]`

### Assinatura de rim() — mudança mínima, backward-safe
```python
def rim(vpa0, roe0, ke, retencao, n,
        excesso_sustentavel: float = 0.0,   # NOVO — default 0.0 reproduz o fade-a-Ke antigo
        g_terminal: Optional[float] = None,  # NOVO — None => sem terminal (comportamento D-02)
        fade_para: Optional[float] = None,   # mantido p/ compat
        ) -> Optional[ResultadoRIM]:
```
Defaults escolhidos para que **chamadas antigas sem os novos args reproduzam o comportamento D-02**
(never-raise, testes que não passam os args continuam válidos). `ResultadoRIM` ganha um campo
`vp_terminal: float` (paridade com `ResultadoDDM.vp_residual`).

### Anti-Patterns a evitar
- **Crescer o RI terminal à taxa do book (10,3%)** em vez de g_terminal → RIM explosivo.
- **Fade para um FLOOR fixo `ke+cap` sem o `min(roe0−ke, ...)`** → lifta banco ruim acima do book
  (medido: ROE=0,10<Ke → P/B=1,22, ERRADO). Sempre usar o `min`.
- **Tocar `ddm.py`/`selo.py`/`lentes.py`** → proibido (CAL-01 + firewall). Só `motores.py`,
  `config.yaml`, `report.py` (dispatch) e o golden `test_motores.py`.
- **Duplicar `g_estavel`** sem documentar que espelha `ddm.g_estavel`.

## Don't Hand-Roll

| Problema | Não construir | Usar | Por quê |
|----------|---------------|------|---------|
| Perpetuidade do RI terminal | `RI/(ke-g)` inline no motor | `ddm.valor_gordon(RI_{n+1}, ke, g)` | Já testada, já trata `ke−g<=0`→None (`ddm.py:44`); consistência cross-modo (FIX-04) |
| VPA0 | `PL/n_acoes` inline | `lentes.vpa` | Já é a fonte no dispatch (report.py:204) |
| Guarda `ke−g` | novo `if` custom | a guarda de `valor_gordon` + `ke_g_spread_min` na borda | Never-raise já é o padrão do módulo |

## Reconciliação de Ke (CAL-02)

**Fato:** o golden assumiu Ke≈12,5% (caso Itaú do livro, Cap. 17), mas o `ke_rim` **live** bate no
teto 0,14: com beta=1,29, rf(Selic-ciclo)≈9,6% e erp_banco=0,045 → 9,6% + 1,29×4,5% ≈ **15,4%**,
clampado a 14%. `[VERIFIED: motores.py:113-122 + inputs medidos]`

**Damodaran para banco brasileiro:** mature-market ERP = **4,23%** (jan/2026); o Brasil adiciona
~3,24pp de country risk premium. `[CITED: aswathdamodaran.substack.com Country Risk 2025 /
pages.stern.nyu.edu ctryprem]` **Ponto-chave:** no framework LOCAL do projeto, a Selic-through-cycle
(rf≈9,6%) **já embute risco-país + inflação**, então o `erp_banco=0.045 ≈ mature ERP` está correto e
**não deve** somar o country risk de novo (senão double-count). Isso valida manter `erp_banco=0.045`.

**Recomendação CAL-02 (ajuste fino, ~R$2):**
1. **Revisar `ke_teto` 0.14 → 0.13**, documentando: um banco large-cap/líquido com beta ajustado
   (Blume/Bloomberg puxa betas altos em direção a 1,0) tem Ke estrutural ~13%, não 14%. Move ITUB4
   de ~R$31,0 para ~R$32,9. `[VERIFIED: cálculo local]`
2. Manter `erp_banco=0.045`, `ke_piso=0.11`. Não mexer em `capm.erp_local` (0.06) nem no
   `ke_live` (o RIM segue nunca excedendo o CAPM ao vivo — D-01 intacto).
3. Alternativa se o usuário preferir não mexer no teto: manter 0,14 e subir `excesso_sustentavel`
   para 0,05 → ITUB4 ≈ R$31,9 (borda inferior do alvo). Menos elegante; o Ke seria a alavanca
   escondida. **Preferir revisar o teto.**

**Não pode explodir:** os clamps `[ke_piso, ke_teto]` e `≤ ke_live` permanecem; o teto só desce.

## Common Pitfalls

### Pitfall 1: Double-counting janela × terminal
**O que dá errado:** somar uma perpetuidade de excesso CHEIO por cima de uma janela que também
mantém o excesso cheio → conta o mesmo moat duas vezes (abordagem (b), R$49).
**Como evitar:** a janela é a **transição** (fade do excesso corrente até o sustentável); o
terminal é só o **estado estacionário** (excesso sustentável). Sem sobreposição.
**Sinal:** terminal > 30% do valor, ou ITUB4 > R$42.

### Pitfall 2: Over-valuation de banco de baixa qualidade
**O que dá errado:** um floor fixo `ke+cap` levanta um banco com ROE<Ke acima do book.
**Root cause:** ignorar o sinal de `roe0−ke`. **Medido:** floor fixo → ROE=0,10<Ke → P/B=1,22.
**Como evitar:** `fade_para = ke + min(roe0−ke, cap)` (permite excesso negativo).
**Sinal:** um banco com ROE < Ke retornando V > VPA.

### Pitfall 3: ROE de 1 ano vs normalizado
**O que dá errado:** `roe0 = roe_valuation()` de um ano atípico (provisão/reversão) vira excesso
perpétuo capitalizado → o terminal amplifica o ruído de um exercício.
**Como evitar:** `roe_valuation()` já usa a base normalizada (FIX-04, janela + winsor)
`[VERIFIED: config.yaml:56-58]`. Verificar na Fase 5 que a cesta usa ROE normalizado; se um ticker
tiver ROE0 destoante da média 3–10a, sinalizar. O `excesso_sustentavel` cap também amortece.
**Sinal:** ITUB4 do RIM oscilando >20% entre anos-base adjacentes.

### Pitfall 4: g_terminal acoplado ao crescimento do book
**O que dá errado:** usar 10,3% (book growth) no terminal → Ke−g pequeno → explosão.
**Como evitar:** g_terminal ≤ g_estavel (0,025), com guarda `Ke−g ≥ spread_min`.

### Pitfall 5: Regressão de TAEE11 / DDM / firewall
**O que dá errado:** mudar `rim()` sem cuidado quebra pagadora regulada ou o golden do DDM.
**Como evitar:** TAEE11 roteia para o motor **DDM**, não RIM → intocada por construção. `ddm.py`
não é tocado → `test_ddm` verde. O golden `test_rim_roe_igual_ke_ancora_no_vpa` (ROE=Ke → V=VPA)
**continua válido** (RI=0 em toda a janela → terminal=0). **Sinal:** rodar a suíte; só
`test_rim_itub4_honesto_maior_que_ddm` deve exigir atualização (é o golden que ENCODA D-02).

## Impacto no Golden (obrigatório atualizar — é parte da fase, não regressão)

`tests/test_motores.py::test_rim_itub4_honesto_maior_que_ddm` **encoda o D-02** que estamos
substituindo. `[VERIFIED: test_motores.py:29-42]` O plano DEVE atualizar:
- A banda `26.0 <= V <= 34.0` → nova banda alvo (~R$30–40 conforme recipe; ex. com VPA=22 do golden
  a recipe dá **R$39,2**, com VPA=19 live dá **R$32,9**).
- A assertiva `abs(res.ri_por_ano[-1]) < 0.05` (RI terminal ≈0) → **deixa de valer** (o RI terminal
  agora é positivo e alimenta a perpetuidade). Trocar por assertiva sobre `vp_terminal > 0`.
- **Mantém válidos sem mudança:** `test_rim_roe_igual_ke_ancora_no_vpa`, `test_rim_never_raise`,
  todos os `ke_rim`, e os goldens de normalizado/dcf/nav.

## Validação / Âncoras (prepara a Fase 5)

Números-verdade para "coerente com a realidade" — o RIM não pode ficar cronicamente ~40–50% abaixo:

| Âncora | ITUB4 | Fonte | Já no código? |
|--------|-------|-------|---------------|
| Graham `√(22,5·LPA·VPA)` | R$39,88 | `lentes.preco_justo_graham` | ✓ `lentes.py:37` |
| Bazin `DPA_médio/0,06` | (calcular na cesta) | `lentes.preco_teto_bazin` | ✓ `lentes.py:75` |
| Preço de mercado | R$44,30 | Yahoo (live) | ✓ |
| P/VP de pares | (BBAS3/BBDC4/BBSE3) | `lentes.metricas_par` | ✓ `lentes.py:151` |
| Fair values manuais | (a definir Fase 5, VAL-02) | tabela do usuário | ✗ — criar na Fase 5 |

**RIM recomendado (R$32,9) vs âncoras:** entre Bazin/DDM (piso conservador) e Graham/preço
(R$40–44) — ordem de grandeza correta, folga de segurança preservada. A cesta (VAL-01: ITUB4,
BBAS3, BBSE3, BBDC4) é a prova de generalização; deixar `excesso_sustentavel`/`ke_teto` em config
para calibrar contra a cesta sem redeploy.

## State of the Art

| Old (D-02) | Novo (recomendado) | Impacto |
|------------|--------------------|---------|
| Fade linear do excesso → Ke, RI terminal ≈0, sem perpetuidade | Fade → excesso sustentável (capped) + perpetuidade de Gordon sobre RI terminal | ITUB4 R$23 → ~R$33; terminal ≈17% do valor |
| Ke clampado a [0.11, 0.14], teto batido ao vivo | Teto 0.14 → 0.13 (CAL-02, documentado) | +~R$2, secundário |

## Security Domain

Mudança em função numérica pura, sem nova superfície de ataque (sem rede, sem input de usuário
não-confiável; os inputs vêm de CVM/Yahoo já ingeridos). ASVS aplicável: apenas **V5 Input
Validation** — satisfeita pelo padrão **never-raise** do módulo (guardas de `None`/`n<=0`/`ke<=0`/
`vpa0<=0` na borda do motor, e `ke−g<=0`→None em `valor_gordon`). V2/V3/V4/V6: não se aplicam.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `excesso_sustentavel=0.045` (moat durável ~4,5pp sobre Ke) é um valor defensável para bancos brasileiros de qualidade | Formulação / config | Calibração fina; se alto over-valua, se baixo subvaloriza. Mitigado: knob de config, calibrado na cesta (Fase 5) |
| A2 | Revisar `ke_teto` de 0.14→0.13 é defensável (beta ajustado de banco large-cap ~13%) | CAL-02 | Se o usuário preferir 14%, subir excesso_sustentavel p/ 0.05 (alternativa documentada) |
| A3 | `g_terminal=0.025` (= g_estavel do DDM) é o crescimento de LP adequado do RI | g de perpetuidade | Já é o default do DDM (≤PIB); baixo risco |
| A4 | VPA0 live ≈ R$19 e ROE0 ≈ 19,3% (medidos 2026-07-12) refletem o ITUB4 no momento do plano | Todos os números | Se os fundamentos mudarem materialmente, os números-alvo deslocam; a faixa R$32–40 é o critério, não um ponto |
| A5 | O fator de persistência ω (alternativa b') não é adotado | Formulação | Se o revisor preferir o canônico CFA puro, (b') exige Ke≈0.11 e reabre CAL-02 |

## Open Questions

1. **`ke_teto` 0.13 vs 0.14** — Recomendação: 0.13 (move ~R$2, mantém CAL-02 secundário). Decisão do
   usuário na discuss/plan; ambos entregam alvo com o cap certo.
2. **Fair values manuais da cesta (VAL-02)** — fora do escopo da Fase 4; a Fase 5 precisa da tabela
   do usuário. Não bloqueia CAL-01/02.
3. **Aplicar o mesmo terminal aos OUTROS motores (DCF/normalizado)?** — Explicitamente **fora de
   escopo** (REQUIREMENTS Future/Out of Scope). Só RIM nesta fase.

## Sources

### Primary (HIGH)
- Código local verificado: `motores.py` (rim/ke_rim), `ddm.py` (valor_gordon), `lentes.py`,
  `config.yaml`, `report.py:202-210`, `test_motores.py` — todas as citações `[VERIFIED]`
- Cálculos numéricos locais (Python) de todas as 4+ formulações e testes de robustez `[VERIFIED]`

### Secondary (MEDIUM)
- CFA Level 2 — Multistage Residual Income / continuing residual income & persistence factor ω
  (ω≈0,62 empírico): analystnotes.com, breakingdownfinance.com/continuing-residual-income,
  ift.world concept 58 `[CITED]`
- Damodaran — mature-market ERP 4,23% (jan/2026), country risk premium Brasil ~3,24pp:
  aswathdamodaran.substack.com "Country Risk 2025", pages.stern.nyu.edu ctryprem `[CITED]`

## Metadata

**Confidence breakdown:**
- Formulação recomendada + números: **HIGH** — computados no próprio código com os inputs medidos
- Fundamento teórico (RIM multiestágio): **HIGH** — CFA L2 curriculum + Ohlson, cross-verificado
- Knobs exatos (0.045 / ke_teto 0.13): **MEDIUM** — defensáveis, calibráveis na cesta (Fase 5)
- Ke de banco (Damodaran): **MEDIUM-HIGH** — mature ERP citado; a escolha de teto é judgment

**Research date:** 2026-07-12
**Valid until:** ~2026-08-12 (estável; os inputs live do ITUB4 podem deslocar os números-ponto,
mas a formulação e a faixa-alvo permanecem)

## RESEARCH COMPLETE

**Phase:** 4 - RIM com Valor Terminal + Ke Revisado
**Confidence:** HIGH

### Key Findings
- O Ke NÃO é a alavanca (move ~R$3); o **valor terminal** é (medido no código).
- Recomendo o **RIM híbrido (c)**: fade parcial a um excesso sustentável capped + perpetuidade de
  Gordon sobre o RI terminal, reusando `ddm.valor_gordon` — teoricamente fundado (RIM multiestágio
  CFA/Ohlson), não-explosivo, robusto a bancos ruins.
- Recipe: `excesso_sustentavel=0.045`, `g_terminal=0.025`, `ke_teto` 0.14→0.13 → **ITUB4 ≈ R$32,9**
  (alvo R$32–40 atingido, terminal ≈17% do valor).
- Guarda anti-bad-bank obrigatória: `fade_para = ke + min(roe0−ke, cap)` (não um floor fixo).
- O golden `test_rim_itub4_honesto_maior_que_ddm` DEVE ser atualizado (encoda D-02); `test_ddm`,
  TAEE11 e o firewall permanecem intactos por construção.

### File Created
`.planning/phases/04-rim-com-valor-terminal-ke-revisado/04-RESEARCH.md`
