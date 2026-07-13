# Research Summary — Marco v2.4 Fidelidade do Valuation

**Project:** Analista de Dividendos (Lazari Capital)
**Domain:** Engine de valuation fundamentalista (RIM/DDM/DCF/NAV) sobre dados públicos B3 — correção de viés sistemático e dispersão de dados
**Researched:** 2026-07-13
**Confidence:** MEDIUM-HIGH (teoria e código-fonte verificados; materialidade de alguns efeitos contábeis brasileiros ainda não medida)

---

## Executive Summary

O app subvaloriza quase toda a B3 (mediana intrínseco/preço 0,68; DDM sozinho 0,48) porque carrega **duas doenças independentes**: um **viés de unidade** (o `Ke` é nominal — embute ~5,2pp de inflação via Selic-ciclo — enquanto o `g` terminal é 2,5% real; o modelo trata inflação como destruição de valor e fica matematicamente incapaz de justificar o P/L mediano de mercado) e uma **dispersão de dados** (escala de `num_acoes` quebrada em 41 de 104 tickers, JCP descartado em 13 empresas, split ajustado duas vezes). A pesquisa das 4 frentes (Stack/Features/Arquitetura/Pitfalls) convergiu de forma incomum: **nenhuma delas propôs inventar algo novo** — a stack já tem tudo (só falta uma função `ipca_ciclo` irmã de `selic_ciclo_para_capm`), o contrato de saída já está no livro (valor intrínseco + região de valor + tríade de veredito + MS simétrica do usuário — não um preço-teto de Bazin), e os 4 motores provaram ser, sob clean surplus, **um único modelo (RIM) com políticas de input diferentes por arquétipo**, não 4 opiniões independentes.

A abordagem recomendada é a que o próprio `PROJECT.md` já fixou: uma ordem de 8 fases (0–7) estritamente sequencial — quarentena de testes primeiro, depois reconciliação de dados, depois ingestão, depois primitivas, **depois `g` isolado, depois `Ke` isolado** (nunca fundidos), depois colapso dos 4 motores num RIM único com contrato de saída (preço-teto derivado do `V`, nunca de Bazin), e só então revalidação com hold-out pré-registrado. Cada passo depende do anterior porque a interação `g`×`Ke` é o próprio objeto de diagnóstico do marco.

O risco central, unânime nas 4 pesquisas, é **repetir o post-mortem do v2.3**: calibrar um parâmetro novo (a margem de segurança, ou qualquer um dos ~20 knobs do bloco `motores:`) até os resultados "ficarem bonitos", criando um segundo erro que mascara o primeiro. A mitigação é estrutural, não de disciplina: deletar (não atualizar) os goldens de nível, travar o orçamento de graus de liberdade em 3 (contando escolhas estruturais, não só floats), proibir commits que tocam `config.yaml` e um golden no mesmo commit, e escrever como **critério de saída explícito** que o golden `ITUB4: 32.88` DEVE quebrar.

---

## Key Findings

### Recommended Stack

Nenhuma dependência nova. O marco se resolve com `requests`/`yfinance`/`pandas`/`numpy` já instalados. O único componente novo é `macro.ipca_ciclo(anos=10)` (SGS 13522, mesma janela do `rf_ciclo`) — é essa simetria de janela que torna o valuation invariante à inflação. `pandera`/`great-expectations` são explicitamente rejeitados (peso/indireção para 4 asserts aritméticos); PIB real de longo prazo é **constante estrutural de 2,0%**, não série (evita volatilidade cíclica num parâmetro que deve ser de regime). `impliedSharesOutstanding` do Yahoo substitui `sharesOutstanding` (que só conta uma classe de ação). Beta setorial + Blume é só aritmética sobre dado já coletado.

**Core technologies (sem mudança):**
- Python 3 + pandas/numpy/yfinance/requests — engine já suficiente
- SGS 13522 (IPCA acumulado 12m, BCB) — nova série, mesmo padrão do `selic_ciclo_para_capm`
- `impliedSharesOutstanding` (Yahoo) — corrige a base de `num_acoes` para ações ON+PN

**Graus de liberdade do modelo-alvo: 3** — `ERP=4,5%`, `n_fade=5`, `PIB_real=2,0%`. Todo o resto é derivado de dado ou fonte externa.

### Expected Features (o contrato de saída)

O livro **não** prescreve preço-teto de Bazin — prescreve **valor intrínseco (DDM/RIM) + região de valor**, com uma tríade de decisão (Cap. 17, caso ITUB4): comprar abaixo de R$35, vender acima de R$39, "valor justo" no intervalo. Isso é exatamente o `SUBAVALIADA / NO INTERVALO / SOBREAVALIADA` que o app já tem — **não trocar por preço-teto + binário Bazin**. O teto que o marco constrói tem que ser **derivado do V** (`P_teto = V × (1 − MS)`), nunca de `DPA/6%`.

**Must have (contrato de saída, na ordem em que travam umas nas outras):**
- Preço-teto = `V × (1 − MS)`, nunca Bazin
- MS **escalonada pela incerteza do dado por ticker** (tabela fixa estilo Morningstar, escrita ANTES de ver resultados — nunca calibrada contra dispersão/preço/taxa de "Comprar")
- Viés binário mecânico (`preço < teto`), nunca uma regra própria que possa discordar do teto
- "Aguardar"/"Acima do preço-teto" no lugar de "Evitar"/"Qualidade Baixa" (fidelidade ao método **e** redução de risco CVM Res. 19/20)
- Nunca suprimir o número sob baixa confiança — alargar a MS + bandeira explícita (Morningstar/SWS alargam; nunca escondem)
- Ponte auditável com **payout terminal implícito** (`payout_T = 1 − g/ROE_T`) — é simultaneamente feature de transparência, teste de correção e guarda-corpo dimensional

**Should have (segunda onda):** reverse DDM ("o que o preço de hoje assume"), DY no teto, confiança visível por ticker.

**Anti-features / deletar:** SAN-01 e `_guarda_faixa_ddm` (cicatrizes do viés — consertadas as doenças, viram um segundo erro cancelando o primeiro); ensemble com bandeira de divergência ENS-01 (mede os próprios bugs de dados, não divergência de método); regressão P/L do Ranking como "preço-alvo" — rebaixar a "posição relativa aos pares", nunca deletar (é Cap. 11-12 do livro).

### Architecture Approach

Sob clean surplus, RIM ≡ DDM ≡ DCF-equity (Ohlson 1995) — logo os 4 motores atuais **não são 4 modelos, são 4 implementações do mesmo modelo com inputs inconsistentes**, e a dispersão medida (0,81/0,63/0,63/0,48) é assinatura de bugs, não de método. A arquitetura-alvo colapsa os 4 motores num **RIM único**, onde o classificador de arquétipo deixa de escolher um *modelo* (erro ilimitado) e passa a escolher uma *política de input/âncora de ROE* (erro limitado) — melhoria arquitetural gratuita. Carve-outs reais: `PAGADORA_REGULADA` (hoje default por eliminação, bug latente) separa em `PAGADORA_MADURA` (RIM) e `CONCESSAO_FINITA` (anuidade truncada — transmissoras sob ICPC 01 usam modelo de ativo financeiro; o book já é o VP da RAP; corrigir o `g` sem tratar isso causaria double-count de inflação).

**Major components:**
1. `core/veredito.py` (novo) — decisão pura: `decidir(preco, preco_teto, cfg) → Veredito{vies, margem, confiança}`; aqui mora o assert `0 < pb_justo < 6` que substitui SAN-01
2. `core/ponte.py` (novo) — decomposição VPA + VP(excesso ROE) + VP(terminal) = preço-teto, invariante testável
3. `core/motores.py` (encolhe) — `rim()` sobrevive; `dcf_crescimento`/`lucro_normalizado`/`nav_contabil` deletados e viram políticas de input do RIM
4. `core/capm.py` — Blume real, β setorial, ERP único; `ke_teto`/`ke_piso` deletados só na Fase 5
5. `ingest/` — módulo novo de reconciliação (4+1 asserts, never-raise, marca confiança baixa)
6. `report/report.py` e `selo.py` — encolhem; decisão vira campo/enum, não parsing de string humana

### Critical Pitfalls

1. **Reajustar o knob para o golden voltar a passar (o pitfall META, o mais importante)** — o repo já contém a instrução escrita de fazer isso (`config.yaml:237` "Move ITUB4 ~R$2"; `config.yaml:258` "NÃO mexer... mudariam o ITUB4"). Prevenção: deletar (não atualizar) o golden na Fase 0; testes de distribuição+jackknife no lugar de assert-de-ticker; testes de invariante que nenhum knob satisfaz; hook de commit que bloqueia `config.yaml` + golden no mesmo commit; `calibracao.lock.yaml` com orçamento de 3 knobs travado por teste.
2. **A "nota de exceção" é lavanderia de overfit** — o gate atual aprova qualquer reprovação com um parágrafo (BBSE3 ganhou uma rota nova depois de falhar). Contagem real do v2.3: ~8 graus de liberdade sobre 4 observações, não 4. Prevenção: carve-outs declarados ANTES de rodar; zero exceções permitidas no hold-out.
3. **Validação circular via consenso de sell-side** — target price é preço com um chapéu; validar V contra ele valida contra o que está sendo julgado. Âncora não-circular real: invariantes algébricos (grátis) + centro da seção transversal (mediana V/P ≈ 1, detector de viés, nunca alvo de calibração).
4. **Look-ahead bias na CVM** — DFP só é pública até 3 meses após o exercício (Res. CVM 80); ZIPs são regenerados com restatements; universo atual tem survivorship bias. Se não der para fazer point-in-time direito, **não fazer o backtest temporal** — um backtest ingênuo produz confiança falsa, pior que nenhum número.
5. **O executor "conserta" os ~150 testes em vez do código** (afrouxar tolerância, `xfail`, deletar assert). Prevenção: classificar os 448 testes em INVARIANTE/GOLDEN-DE-NÍVEL/CONTRATO antes de tocar código; golden-master + diff aprovado; CI que barra afrouxamento silencioso; meta-teste "canário" que prova que a suíte ainda reprova quando um knob piora.

---

## A ÂNCORA DE VERDADE (critério de aceite mais duro do marco)

Lido direto do PDF (Cap. 17, Tabelas 41/43) — o caso-exemplo do próprio livro:

```
LIVRO:    g = 10,24%  ·  Ke = 12,48%  →  V = R$ 37,22   (região R$ 35–39, MS ±5%)
APP HOJE: g =  6,94%  ·  Ke = 17,30%  →  DDM R$ 16,13
```

O `g` do livro (10,24%) é praticamente o `g` **por fundamentos** que o app calcula e **descarta** (10,29%) — o app adota o histórico de 6,94%. O app replica o caso-exemplo do próprio livro com menos da metade do valor. Isso não é calibração: é o Core Value ("fiel ao método do livro") violado no caso-teste do próprio método. **Qualquer fase de contrato de saída/calibração deve ser checada contra esse número antes de ser considerada concluída.**

## O CONTRATO DE SAÍDA — já definido pelo livro, não inventar outro

Verificado no PDF: "preço-teto" e "Bazin" têm **zero** ocorrências; "valor intrínseco" tem 39. O livro entrega:

- **Valor intrínseco (V)** — DDM/RIM, Cap. 13–17
- **Região de valor** — banda em torno de V
- **Tríade de decisão** — SUBAVALIADA (compra descontada) / NO INTERVALO (valor justo) / SOBREAVALIADA (venda) — o app já tem isso, **não trocar por binário**
- **Margem de segurança simétrica escolhida pelo USUÁRIO** (±5%, ±10% — "é você quem decide") — mata a Armadilha 4 por construção: uma MS que é controle explícito do usuário não pode ser calibrada para maquiar resultado
- **A matriz de sensibilidade Ke×g** — "a que mais gostamos" no livro; é a estratégia **preferida** para a região de valor; deve ser construída sobre `Ke`/`g` corretos, não sobre os errados de hoje

**Sai apenas:** "Evitar" e "Qualidade Baixa" — nunca vieram do livro (invenção do produto; risco de método e jurídico simultaneamente).

---

## As Duas Doenças e a Ordem Obrigatória (0→7)

**Doença 1 — VIÉS (erro de unidade).** `Ke` nominal (Selic-ciclo, embute ~5,2pp de inflação) vs `g` de 2,5% real. Teto de P/L = 7,8x contra P/L mediano de mercado de 9,9x. Único parâmetro compartilhado pelos 4 motores.

**Doença 2 — DISPERSÃO (dados).** `num_acoes = lucro/LPA` com bases cruzadas quebra a escala em 41/104 tickers; JCP descartado em 13 empresas; split ajustado duas vezes; zero reconciliação no pipeline.

**Ordem obrigatória (cada fase depende da anterior):**

| Fase | Nome | Critério de saída / entrega |
|---|---|---|
| **0** | Blindagem processual | Quarentena dos ~150 goldens (`@pytest.mark.legado`, deletados quando a fase chega); invariantes escritos como `xfail(strict=True)` HOJE — o principal: `V` invariante a +300bps de inflação (rf e g_cap juntos), variação <2% |
| **1** | Reconciliação de sanidade | 4+1 asserts (LPA reconcilia, num_acoes estável, proventos DFC≈Yahoo, PL/lucro mesma base, **clean surplus** ΔB=LL−Div) — never-raise, marcam confiança baixa |
| **2** | Ingestão correta | JCP (regex correto), lucro/PL do controlador, duplo split, `impliedSharesOutstanding` |
| **3** | Primitivas sem viés | `normalizacao.py:73-75` (mediana-de-3 = ano do meio, haircut −9,1%) e `fundamentals.py:137-150` (ROE de bases cruzadas). **CRITÉRIO DE SAÍDA: o golden ITUB4 32.88 DEVE quebrar** |
| **4** | `g` fechado | `g_cap = (1+π_ciclo)(1+PIB_real)−1 = 7,28%`, mesma janela do `rf`. Teste de invariância à inflação vira verde AQUI |
| **5** | Ke (separado de propósito) | ERP único 4,5%, beta setorial+Blume, `ke_teto`/`ke_piso` deletados. Fundir com a Fase 4 dá 1 número e zero diagnóstico |
| **6** | Colapso dos motores no RIM | 4 motores → políticas de input; contrato de saída (preço-teto/MS/ponte); carve-out `PAGADORA_MADURA`/`CONCESSAO_FINITA`; ensemble aposentado. **`config.yaml` bloco `motores:` de ~20 chaves → ≤5** |
| **7** | Revalidação honesta | Cesta estratificada, fair values commitados ANTES, 3 graus de liberdade, distribuição+jackknife (nunca ticker+reais); PIT real ou não fazer backtest temporal |

---

## As Cinco Armadilhas (com os números que as provam)

1. **Remover `ke_teto: 0.13` antes de consertar o `g`** → ITUB4 0,75→0,64; BBDC4 0,71→**0,52**. O clamp é indefensável (justificativa "Blume" é aritmeticamente falsa — daria 15,9%, não 13%) mas compensa o viés do `g`. Ke sozinho é líquido zero (0,68→0,67).
2. **"Consertar" `dcf_crescimento` com FCFE (lpa×payout)** → vira DDM matematicamente (teorema, não bug). WEGE3 0,58→**0,26**.
3. **Reajustar knobs quando o golden `ITUB4: 32.88 ± 0.20` quebrar** — ele VAI quebrar e isso é o conserto funcionando. Deletar, não atualizar. Regra: "uma justificativa legítima de knob nunca menciona um ticker" (contraste `config.yaml:237` "Move ITUB4 ~R$2").
4. **A margem de segurança virar o novo `ke_teto`** — se calibrada até os resultados ficarem bonitos, é o post-mortem do v2.3 num endereço novo. Neutralizada pelo livro: MS é escolha do usuário, nunca calibrada contra dispersão/preço/taxa de "Comprar".
5. **O conserto do `g` cria a própria fragilidade** — com `g=7,28%`, o spread `Ke−g` cai de 10,5pp para ~5,5pp e o peso do valor terminal **quase dobra**. `excesso_sustentavel` e `ke_g_spread_min`, hoje decorativos, viram load-bearing na Fase 4/6. Prever, não descobrir depois.

---

## As Três Regras Duras para o Roadmapper

**(A) NÃO fundir a Fase do `g` (4) com a do `Ke` (5).** A simulação prova: Ke sozinho é líquido-zero (0,68→0,67), g sozinho exagera. A interação `g`×`Ke` **é o ponto inteiro do marco** — duas fases dão duas medições limpas contra o mapa de 104 tickers; uma fase dá um número e zero diagnóstico. A tentação de fundir "para economizar tempo" vai ser forte e está errada.

**(B) Escrever "o golden ITUB4: 32.88 DEVE quebrar" como CRITÉRIO DE SAÍDA explícito da Fase 3 (primitivas)**, não como regressão. O golden foi calibrado para cancelar o haircut de lucro da primitiva — dois erros se anulando. Isso inverte o incentivo: um golden quebrado vira evidência de sucesso. Precisa estar escrito porque vai parecer errado no momento em que acontecer.

**(C) A deleção de knobs na Fase 6 tem que ser CONTADA, não descrita.** `config.yaml` bloco `motores:` de ~20 chaves → **≤5** é o requisito verificável. `excesso_sustentavel`, `g_terminal`, `ke_teto`, `ke_piso`, `roe_terminal_stat` foram todos calibrados contra o `g` enviesado — re-derivar, não re-tunar. Sem um número contável, essa deleção não acontece.

---

## Watch Out For — pitfalls que mais podem matar o marco

| Pitfall | Risco se ignorado | Fase que endereça |
|---|---|---|
| **Pitfall 1 — reajustar knob para o golden voltar** | O overfit sobrevive ao conserto que existia para matá-lo; v2.4 produz números novos com o mesmo viés antigo | 0 (deleção do golden + lock + hook) e 6 (calibração) |
| **Pitfall 5 — "consertar" os 448 testes em vez do código** | Suíte fica verde e decorativa; não constrange mais o modelo (estado de hoje) | 0 (classificação + baseline + CI), contínua até 6 |
| **Pitfall 2 — nota de exceção como lavanderia de overfit** | Carve-outs criados *depois* de ver o ticker falhar viram DoF invisível (BBSE3); v2.3 gastou ~8 DoF sobre 4 observações | 6 (carve-outs declarados na Fase 5, zero exceção no hold-out) |
| **Pitfall 3 — validação circular contra consenso de sell-side** | Valida o modelo contra o que ele deveria corrigir; target price é preço com um chapéu | 6 (métrica primária = invariantes + centro da seção transversal, nunca consenso como gate) |
| **Pitfall 12 — clean surplus não vale em banco BR (IFRS 9 FVOCI)** | `B0` deprimido → RIM subvaloriza banco de qualidade — pode ser o 3º bug de dados que os knobs do v2.3 mascaravam | 1 (assert clean surplus como pré-condição) + 2 (ingerir DRA — resultado abrangente) |
| **Pitfall 4 — look-ahead bias na CVM (DFP não é PIT)** | Backtest temporal ingênuo produz confiança falsa; pior que nenhum número | 6, com decisão explícita de escopo (PIT ou não fazer) tomada na Fase 5 |
| **Pitfall 15 — "NAV = 1º termo do RIM" é falso em holdings** | Colapsar NAV no RIM importa o book contábil para o único arquétipo onde ele é a informação errada, jogando fora o desconto de holding | 5 (carve-out declarado antes da Fase 6: rota a mercado ou recusa explícita) |
| **Pitfall 16 — instrumentos híbridos (IHCD/AT1) dentro do PL de bancos** | `B0` inflado → banco de qualidade sai barato demais — mesmo sintoma que o v2.3 combateu com knobs | 2 (ingestão), spike de investigação na Fase 1 |
| **Suspeita aberta do PROJECT.md — clean surplus violado em bancos** | Se confirmado, os knobs do v2.3 mascaravam um terceiro bug de dados, não só viés de `g`/`Ke` | Spike na Fase 1, ANTES de calibrar |

---

## Implications for Roadmap

### Fase 0: Blindagem processual
**Rationale:** sem isso, os consertos das fases seguintes são revertidos por um knob e ninguém nota; redefine o que "suíte verde" significa antes de tocar código.
**Delivers:** goldens legados quarentenados/deletáveis; invariantes escritos como `xfail(strict=True)`; classificação dos 448 testes; `calibracao.lock.yaml`; hook de commit anti-knob-com-golden.
**Avoids:** Pitfall 1 (meta-pitfall) e Pitfall 5.

### Fase 1: Reconciliação de sanidade
**Rationale:** os asserts SÃO o teste de regressão da Fase 2 — precisam existir antes do conserto para provar que ele funcionou.
**Delivers:** 4+1 asserts never-raise (incl. clean surplus); relatório dos 41 tickers quebrados; spike de investigação IHCD/AT1.
**Addresses:** T3 (score de confiança) do FEATURES.md nasce daqui.
**Avoids:** Pitfalls 6, 8, 10, 11, 12, 16.

### Fase 2: Ingestão correta
**Rationale:** os asserts da Fase 1 viram verde ticker a ticker — progresso mensurável.
**Delivers:** JCP correto, lucro/PL do controlador, `impliedSharesOutstanding`, DRA (resultado abrangente) ingerida.
**Uses:** stack — SGS 13522, `impliedSharesOutstanding`.
**Avoids:** Pitfalls 6, 7, 8, 9, 10, 12, 16.

### Fase 3: Primitivas sem viés
**Rationale:** sem dado correto, primitiva correta não significa nada.
**Delivers:** `normalizacao.py` e `fundamentals.py` corrigidos; `ROE_CSR`. **Golden ITUB4 32.88 quebra (critério de saída).**
**Avoids:** Pitfall 14 (viés direcional da normalização), Pitfall 11.

### Fase 4: `g` fechado
**Rationale:** tem que preceder o Ke — sozinho vai exagerar em alguns nomes, aceitável por ser uma janela de 1 fase.
**Delivers:** `g_cap = 7,28%`; teste de invariância à inflação vira verde.
**Implements:** `ipca_ciclo` do STACK.md.

### Fase 5: `Ke` limpo
**Rationale:** tirar o clamp só é seguro depois do `g`; regra dura (A) — não fundir com a Fase 4.
**Delivers:** Blume real, β setorial, ERP único 4,5%, `ke_teto`/`ke_piso` deletados.
**Also:** carve-outs de arquétipo (`PAGADORA_MADURA`/`CONCESSAO_FINITA`, holding) declarados por escrito aqui, antes do hold-out.

### Fase 6: Colapso dos motores + contrato de saída
**Rationale:** precisa de `Ke`/`g` confiáveis, senão entrega uma ponte de aparência honesta sobre números desonestos.
**Delivers:** RIM único como política de input por arquétipo; `core/veredito.py`, `core/ponte.py`; preço-teto = V×(1−MS); MS escalonada; payout terminal implícito; "Aguardar" no lugar de "Evitar"; ensemble/regressão-como-alvo aposentados. **Requisito contado: config.yaml `motores:` ~20→≤5 chaves.**
**Avoids:** Pitfalls 2, 13, 15.

### Fase 7: Revalidação honesta (hold-out)
**Rationale:** por último — qualquer coisa antes queima o hold-out.
**Delivers:** cesta 40-60 tickers, fair values commitados ANTES, roda uma vez, testes de distribuição+jackknife.
**Avoids:** Pitfalls 3, 4.

### Phase Ordering Rationale

- A ordem 0→7 é imposta por dependência causal (cada fase precisa do dado/parâmetro corrigido na anterior), não por conveniência de sprint.
- A separação `g`(4)/`Ke`(5) é a única exceção que parece redundante e **não é** — é a regra dura (A).
- Fase 6 (contrato de saída) só pode calibrar `MS` **depois** de `V` estar sem viés — regra explícita do FEATURES.md §2.2.

### Research Flags

Precisam de `/gsd-research-phase` durante o planejamento fino:
- **Fase 5/6 — carve-out de concessão finita:** o prazo remanescente `T` da concessão **não está confirmado como disponível gratuitamente e estruturado** (ARCHITECTURE.md §3). Pode exigir tabela curada.
- **Fase 6 — payout terminal implícito e escolha de `ROE_T`:** decisão de método ainda em aberto (through-cycle? histórico? setorial?) — é a premissa que mais move o valor terminal.
- **Fase 2 — IHCD/AT1 em bancos BR:** confiança MEDIUM, precisa verificação nas notas explicativas antes de decidir tratamento.
- **Fase 7 — viabilidade de PIT real (point-in-time):** se o custo de fazer direito (universo FCA por ano, trava de disponibilidade) for alto demais, a decisão de **não fazer** o backtest temporal precisa ser tomada explicitamente na Fase 5, não descoberta na Fase 7.

Fases com padrões bem estabelecidos (podem pular pesquisa extra):
- **Fase 0, 1, 2:** os asserts e a correção de ingestão são aritmética de uma linha, já verificados no código; STACK.md e PITFALLS.md já entregam o código exato.
- **Fase 4:** derivação de `g_cap` já medida ao vivo (BCB), fórmula fechada.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Séries do BCB e chaves do Yahoo verificadas ao vivo, não de memória |
| Features (contrato de saída) | **HIGH** | **O PDF do livro FOI lido diretamente** (2026-07-13, `pdftotext`): "preço-teto" = **0 ocorrências**, "Bazin" = **0**, "valor intrínseco" = **39**. A regra de decisão de 3 estados e a MS simétrica escolhida pelo usuário são **citação literal** do Cap. 17. Comportamento de concorrentes sob baixa confiança permanece MEDIUM (mas é irrelevante — o livro tem precedência) |
| Architecture | MEDIUM-HIGH | Álgebra e ordem de build HIGH (Ohlson 1995, Penman); materialidade de dirty surplus no Brasil e disponibilidade do prazo de concessão NÃO medidas |
| Pitfalls | MEDIUM-HIGH | Bugs de código e bandas do gate HIGH (executados no repo); prazo DFP e IRRF HIGH (fonte oficial); IHCD/AT1 e DFC líquida de IRRF MEDIUM (não verificado nas notas) |

**Overall confidence:** MEDIUM-HIGH — a arquitetura e a ordem de fases têm base teórica sólida e foram cruzadas com execução real do código; os gaps remanescentes são pontuais (T da concessão, ROE_T terminal, IHCD) e não bloqueiam o início do marco.

### Gaps to Address

- ~~**Não foi lido o PDF do livro diretamente**~~ — **FECHADO em 2026-07-13.** O PDF foi lido
  (`659422642-Orleans-Martins-O-Investidor-em-Acoes-de-Dividendos.pdf`, via `pdftotext -layout`).
  Resultado: **"preço-teto" e "Bazin" têm ZERO ocorrências**; "valor intrínseco", 39. O livro
  prescreve **valor intrínseco + região de valor**, com regra de decisão de **três** estados
  (compra descontada / valor justo / venda interessante — Cap. 17, citação literal), **margem de
  segurança simétrica escolhida pelo usuário** (*"se 5%, 10% ou qualquer outro valor, é você quem
  decide"*) e a **matriz de sensibilidade Ke×g** como a estratégia *preferida* (*"a que mais
  gostamos"*). O contrato de saída do marco está travado no PROJECT.md e **não depende mais de
  suposição**. A proposta original de "preço-teto + viés binário" foi **descartada por infidelidade
  ao método**.
- **Prazo remanescente `T` das concessões** — não confirmado como disponível gratuitamente; plano de fallback (tabela curada) precisa ser validado antes da Fase 5.
- **Materialidade do dirty surplus no universo brasileiro** — não medida; script de 20 linhas proposto para a Fase 3 resolve isso barato.
- **IHCD/AT1 dentro do PL de bancos BR** — hipótese plausível mas não verificada nas notas explicativas; spike necessário na Fase 1.
- **`ROE_T` terminal** (through-cycle vs. histórico vs. setorial) — decisão de método em aberto que mais move o valor terminal; precisa ser resolvida e exposta na ponte auditável (Fase 6).

## Sources

### Primary (HIGH confidence)
- Código-fonte do repositório: `src/analista/ingest/{build,cvm,prices,macro}.py`, `src/analista/core/{normalizacao,fundamentals,motores,capm,arquetipo,ddm,comparables}.py`, `config.yaml`, `tests/test_backtest_bancos.py` — lidos e executados
- BCB SGS 13522 (IPCA 12m) e 432 (Selic meta) — verificados ao vivo
- Yahoo Finance `sharesOutstanding`/`impliedSharesOutstanding` — verificado ao vivo (ITUB4, ITUB3, PETR4)
- Resolução CVM 80/2022 (prazo de entrega da DFP) — fonte oficial
- Lei 15.270/2025 + PLP 128/2025 (IRRF sobre JCP/dividendos 2026) — Receita Federal, PwC
- Ohlson (1995), Penman (*Financial Statement Analysis and Security Valuation*), Penman & Sougiannis — equivalência RIM≡DDM≡DCF e viés de truncamento
- Morningstar — metodologia oficial de Uncertainty Rating (escala de MS por bucket)
- Nota Técnica IFRS×Regulatório da TAESA; CVM Ofício-Circular SNC/SEP 04/2020 — tratamento contábil de transmissoras

### Secondary (MEDIUM confidence)
- Isidro, O'Hanlon & Young (2004) — dirty surplus é problema de variância, não viés sistemático
- Anotações de capítulo da própria engine (`ddm.py`, `comparables.py`, `lentes.py`) — reconstrução do que o livro prescreve, indireta mas com exemplos numéricos conferidos
- Investidor10 — vernáculo "preço-teto" no PF brasileiro
- Simply Wall St — comportamento sob baixa confiança (*Narratives*, 4 variantes de DCF)

### Tertiary (LOW confidence)
- Status Invest sob baixa confiança — não investigado, não bloqueia (padrão já estabelecido por Morningstar/SWS)

---
*Research completed: 2026-07-13*
*Ready for roadmap: yes*
