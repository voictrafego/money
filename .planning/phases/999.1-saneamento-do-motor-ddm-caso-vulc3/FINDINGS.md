# Saneamento do motor DDM — Achados (caso VULC3)

**Capturado:** 2026-06-26
**Status:** Backlog (não sequenciado)
**Origem:** Diagnóstico externo sobre o relatório VULC3 (money.voictech.com.br, 26/06/2026) + verificação linha a linha no código por Claude Code.

> Este documento é a **semente** do item de backlog 999.1. Preserva o diagnóstico e a
> verificação contra o código para quando o item for promovido a milestone via
> `/gsd-review-backlog`. É diagnóstico, **não** especificação de correção.

---

## Sintoma

VULC3 (Vulcabras), relatório de 26/06/2026:
- Preço: R$ 14,40 · Intrínseco (DDM): R$ 167,70–334,20 (11x–23x o preço) · Veredito: **SUBAVALIADA** (selo verde) · DY: 37,0%
- Múltiplos: ROE 51,4% · Ke 9,4% · Beta 0,88 · P/L 3,37 · Payout último ano 124,7% · Payout p/ valuation 100,0%
- Crescimento: g histórico (CAGR) 47,3% · g por fundamentos −12,7% · g alto adotado 25,0% · g estável 2,5%
- Estágio: "Crescimento maduro" · Setor: "Têxtil e Vestuário" (errado — é calçados)

Um intrínseco de 11x–23x o preço, sustentado por 5 anos sem nunca tocar a cotação, é **modelo divergindo**, não tese de subavaliação.

## Verificação contra o código (confirmações)

| Item | Veredito | Evidência |
|---|---|---|
| **A** — `g_alto > Ke` infla a fase explícita | ✅ Raiz formal | `core/ddm.py:92` (`ddm_dois_estagios`) só valida `ke - g_estavel <= 0`. **Sem trava `g_alto < ke`.** `projetar_dividendos` capitaliza a `g_alto` sem relação com Ke. |
| **B** — g adotado ignora g por fundamentos | ✅ (mecanismo descrito errado) | `report/report.py:70` → `g_alto = g_historico` (g_fundamentos só fallback). Linha 72: `g_alto = max(g_estavel, min(g_alto, 0.25))` — **teto fixo 25%**, não "CAGR pela metade". `g_fundamentos=−12,7%` é exibido e descartado. |
| **C** — payout 100% perpétuo | ✅ | `core/fundamentals.py:76` `payout_valuation` = média 3a **com clamp 1.0**, sem expurgo de extraordinário. |
| **D** — lucro não normalizado contamina tudo | ✅ Raiz a montante | `lucro_liquido` é CVM cru. ROE, CAGR, payout, DY derivam dele. Sem camada de normalização. |
| **E** — veredito ignora flags | ✅ | `report/report.py:114-124` veredito = só preço vs `vmin/vmax`. Alertas (126-141) nunca realimentam o rótulo. |
| **F** — Ke baixo demais | ✅ (pior que pensaram) | `config.yaml` CAPM hardcoded de fim de 2019: `rf_us 1,92%`, `embi 2,14%`, `erp_us 6,20%`. Reproduzido: `0,0192 + 0,88*(0,062+0,0214)` ×inflação = **9,43%**. Nenhum input vem de dado vivo. |
| **G** — estágio "maduro" mas DDM high-growth | ✅ | `core/lifecycle.py:47` "Crescimento maduro" é fallthrough `g>=0.05`. Estágio **nunca** seleciona a variante do DDM — é cosmético (só display). |
| **H** — amplitude 2x = toggle binário | ⚠️ conclusão certa, hipótese errada | `vmin/vmax` = min/max de 2 cenários discretos (`ddm_constante` g-const × `ddm_h` modelo-H), **não** banda de sensibilidade. Mas `n_anos_explicito` é **fixo em 10** (não toggle 5-vs-10). O ~2x é coincidência deste caso. A matriz de sensibilidade real existe (`ddm.py:118`) mas só vira tabela. |
| **I** — banda nunca cruza o preço | ✅ sintoma | Banda = `vmin/vmax` atual projetado liso, não recalculado mês a mês. Bom caso de regressão. |
| **J** — DY 37% trailing / sem recorrente | ✅ em parte | Múltiplos usam DPA último ano-calendário / preço (trailing). Existe `dy_atual()` com `dpa_trailing_12m` mas é outro caminho. Sem noção recorrente vs trailing. Gap de 5pp vs fontes = janela de dados (checar). |
| **K** — setor errado | ✅ baixo impacto | Vem do mapeamento da ingestão. Afetaria se beta setorial/comparáveis usarem setor. |

## O que o diagnóstico não pegou

1. **A fase explícita é de 10 anos** (`config.yaml: n_anos_explicito: 10`) — a explosão é sobre 10 anos de `g>Ke`, pior que o item H sugere.
2. **A semente já vem inflada:** `dpa_inicial = lpa * (1+g_alto) * payout_proj` (`report.py:101`) — dividendo do ano 1 já leva +25%.
3. **A trava certa existe no lugar errado:** `valor_gordon` (`ddm.py:44`) tem o guard `ke - g <= 0 → None`. O DDM de dois estágios — o que roda — não tem.

## Cascata de dependência (causa → sintoma)

1. Lucro não normalizado (D) — raiz mais a montante; contamina ROE/CAGR/payout/DY.
2. g adotado desligado dos fundamentos (B) — consome os números contaminados e ignora `g_fundamentos`.
3. `g > Ke` (A) + Ke baixo demais (F) — transformam o g inflado num valuation explosivo.
4. Payout 100% perpétuo (C) + estágio maduro com high-growth (G) — reforçam a explosão.
5. Veredito ignora flags (E) — apresenta o output absurdo como recomendação positiva.
6. H, I, J, K — sintomas/tells e casos de regressão.

## Fixes priorizados (por alavancagem)

- **DDM-FIX-01** — trava `g_alto < Ke` (ou clamp `g_alto = min(g_alto, Ke − margem)`) em `ddm_dois_estagios`/`analisar_acao`. ~3 linhas, mata a explosão sozinha. **Maior ROI.**
- **DDM-FIX-02** — reconciliar `g_alto` com `g_fundamentos`/payout; payout 100% ⇒ g sustentável 0 por construção.
- **DDM-FIX-03** — refrescar inputs do CAPM (rf/EMBI do BCB ao vivo, ou abordagem `local` com Selic). Hoje são valores de 2019.
- **DDM-FIX-04** — normalização de lucro (expurgo de não-recorrentes) antes de ROE/CAGR/payout/DY. Maior esforço, raiz a montante.
- **DDM-FIX-05** — veredito consome as flags: rebaixar "SUBAVALIADA" para "divergência de modelo / verificar" quando payout>100% ou DY>15%.
- **DDM-FIX-06** — guardrails/regressão: DY recorrente vs trailing; banda = sensibilidade real (não 2 cenários); setor correto; caso VULC3 como teste de regressão.

## Conexão com o trabalho em andamento (v1.2)

A Phase 6 (TIMING-02, matriz fundamento×técnico) **lê `a.veredito` como token líder e decisório**. Veredito furado ⇒ a matriz propaga fielmente um veredito errado com a técnica subordinada. Não bloqueia v1.2, mas é pré-requisito de qualidade para o valor da Phase 6/7. Restrição de invariante: qualquer correção aqui precisa manter os 64 golden tests de valuation coerentes (provavelmente exige rebaselining deliberado, não "manter verde a qualquer custo").
