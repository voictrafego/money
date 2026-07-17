# Phase 12: Custo de capital / `Ke` (KE) — Research

**Researched:** 2026-07-17
**Domain:** Custo de capital (CAPM), unificação de fonte única do `Ke`, remoção de clamp, beta setorial+Blume, orçamento de knobs (lock)
**Confidence:** HIGH (tudo verificado no código real do repositório; 3 questões abertas isoladas ao fim)

Este é um documento de **verificação**, não de decisão. As 14 decisões D-01..D-14 do
`12-CONTEXT.md` estão **locked**. O que segue confirma cada ponteiro contra o código de hoje,
resolve os valores discricionários (limiar do fallback, formato do artefato) a partir de dados
reais, e **sinaliza 3 contradições** entre o CONTEXT.md e o estado real do repositório que o
planner precisa reconciliar antes de escrever o plano.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01..D-14 — copiadas verbatim do 12-CONTEXT.md)

**Beta setorial — agregação (KE-03):**
- **D-01:** agrupar pelo **setor CVM** (`c.setor`, string econômica). É a "industry beta" de
  Damodaran, disponível no ingest antes do Ke. **Não** usar `arquetipo` como chave (computado
  depois do Ke; exigiria reordenar).
- **D-02:** **mediana** dos betas crus dos pares do setor — robusta a outliers.
- **D-03:** aplicar Blume (`0,33 + 0,67×β`) **uma vez**, sobre o β setorial agregado (agregar-β-cru
  →Blume ≡ Blume→agregar para mediana/média; linear e monotônico).
- **D-04:** grupo com pares **< limiar estrutural** (ex.: 3) ou ticker **sem setor** → usar o
  **próprio `c.beta` com Blume** (β individual Blume-ajustado). Degradação graciosa, never-raise;
  limiar **estrutural, não calibrado contra ticker**.

**Onde o β é computado — pureza da engine:**
- **D-05:** fonte = **artefato pré-computado e versionado**; um passo offline gera `setor →
  mediana(β cru)`; os entry points **carimbam** o mapa em `cfg`; a engine lê `cfg[...][setor]` e
  aplica Blume. **Não** tabela digitada. **Não** dinâmico por run.
- **D-06:** invariante **analyze==rank** (DURO + teste): mesmo β setorial (logo mesmo Ke) para a
  mesma ação entre `analyze` e `rank`. Computar mediana dinâmica por run é o anti-padrão WR-03.
  Fonte única carimbada (espelha `_carimbar_macro`/`rf_local`) + teste. É o KE-05 na prática.
- **D-07:** β setorial é **DADO, FORA do lock** — não é knob, não entra no orçamento de 3 graus,
  não toca `calibracao.lock.yaml`.

**Unificação dos dois Ke:**
- **D-08:** **deletar `ke_rim`**; `report.py:261` alimenta o RIM com o **`a.ke` único**. Com
  ERP=0,045 e clamp fora, `ke_rim` colapsa exatamente em `ke_local`. **Não** manter passthrough.
- **D-09:** RIM recebe `a.ke` pronto — **não** recomputa. Ke único computado uma vez, carimbado em
  `a.ke`, lido por todos os consumidores (DDM, RIM, rota de segurança, matriz Ke×g).
- **D-10:** limpeza config + lock no **MESMO diff**: `erp_banco`, `ke_piso`, `ke_teto` saem do
  `config.yaml` (bloco `motores.rim`); as folhas congeladas correspondentes saem da partição do
  `calibracao.lock.yaml` no mesmo commit; `test_knobs_batem_com_o_lock` e a contagem refletem.

**Validação sem clamp + Ke exibido:**
- **D-11:** provar "nada explode" com **(a)** regressão contra o **mapa REAL de 104 tickers** +
  **(b)** teste do invariante estrutural `Ke_min(Blume) ≈ 11,07% > g_cap = 7,28%`. **SEM** novo
  guard (o guarda-corpo P/B é a Fase 13).
- **D-12:** `capm.erp_local` **0,06 → 0,045** (valor do grau ERP no lock, mesmo commit); o golden
  `ITUB4 = 32,88` **quebra e é DELETADO** (não atualizado). Tudo no mesmo diff sancionado.
- **D-13:** remover o marker `xfail(strict=True)` de `test_invariancia_inflacao_engine_itub4`; passa
  a asseverar a invariância de verdade e passa porque o sistema mudou. **NÃO afrouxar o limiar**.
  `xfail_estritos()` cai 2→1.
- **D-14:** report exibe **`a.ke`** como O Ke (nunca `ke_rim`); matriz `delta_ke × delta_g` em torno
  do `a.ke`; idêntica entre `analyze`/`rank`. Remover qualquer exibição de Ke ≠ `a.ke`.

### Claude's Discretion (resolvido neste RESEARCH)
- Valor exato do limiar de pares do fallback (D-04) → **§Distribuição setorial**: recomendo **3**.
- Nome/formato do artefato de betas e chave em `cfg` (D-05) → **§Artefato de betas**.
- Assinatura do gerador offline + helper de carimbo → **§Padrão de carimbo**.
- Ordem dos commits atômicos (diff de knob coeso) → **§Sequenciamento de commits**.
- Rótulos do report/matriz (D-14); reescrita da partição do lock (D-10) → **§Inventário do lock**.

### Deferred Ideas (OUT OF SCOPE — Fase 13/14)
- Guarda-corpo P/B justo `0 < P/B < 6` → **Fase 13**.
- Colapso dos 4 motores num RIM único + corte final de knobs `motores:` ~11→≤5 → **Fase 13**.
- Validação honesta / hold-out / caso do livro (ITUB4 = R$ 37,22) → **Fase 14**.
- Reforma de UI do contrato de saída → **Fase 13**.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Descrição | Suporte de pesquisa |
|----|-----------|---------------------|
| KE-01 | Um único `Ke` no sistema (hoje dois: DDM `a.ke` e RIM `ke_rim`) | `ke_rim` deletado (D-08); `report.py:261` passa a `a.ke`. Prova de colapso em §Colapso `ke_rim ≡ ke_local`. |
| KE-02 | ERP 4,5% (sem small-cap 1,5%) | `capm.erp_local` 0,06→0,045; grau ERP do lock atualizado no mesmo diff. §Inventário do lock. |
| KE-03 | Beta setorial + Blume | §Distribuição setorial (limiar 3 estrutural + artefato versionado). D-01..D-07. |
| KE-04 | `ke_piso`/`ke_teto` removidos; nada explode por aritmética | §Invariante `Ke_min > g_cap` (11,07% > 7,28%); §Validação D-11. |
| KE-05 | Ke exibido = Ke que produziu o número; matriz em torno dele; idêntico analyze/rank | `a.ke` já é o exibido (`report.py:982`); matriz em `report.py:539-543`. Invariante analyze==rank via carimbo único (D-06). |
</phase_requirements>

---

## Summary

O sistema tem hoje **dois `Ke` simultâneos**, ambos verificados no código:
1. **`a.ke`** — `capm.ke_local(c.beta, rf_local, erp_local)` (`report.py:470`), com `erp_local=0,06`
   e **beta CRU** (`c.beta`, direto do Yahoo). É o Ke **exibido** (`report.py:982`) e o do DDM/matriz.
2. **`ke_rim`** — `motores.ke_rim(c.beta, cfg)` (`motores.py:148-172`), com `erp_banco=0,045`, **clamp
   `[ke_piso=0,11, ke_teto=0,13]`** e teto `ke_live`. Alimenta **só** o RIM (`report.py:261`); **nunca
   é exibido**. É a "manchete oculta" do KE-01.

A Fase 12 colapsa os dois num só. A prova aritmética do colapso é **limpa e sem resíduo** (§Colapso).
O clamp sai com segurança porque o **piso estrutural do Blume** (β→0 ⇒ Blume=0,33) garante
`Ke_min = rf + 0,33×0,045 ≈ 11,07%` (com o rf carimbado 9,58%) — **3,79pp acima** do `g_cap=7,28%`,
folgado inclusive sobre o `ke_g_spread_min=0,03`. Nenhuma perpetuidade pode divergir por aritmética.

**3 correções de fato ao 12-CONTEXT.md** que o planner precisa incorporar:
1. **O golden `ITUB4 = 32,88` JÁ FOI DELETADO na Fase 10 (PRIM-05).** Não existe assert vivo desse
   valor para deletar na Fase 12. Os goldens que a Fase 12 realmente mata são **de banda de Ke**
   (`test_ke_local_na_faixa_small_cap_br`, `test_ke_rim_na_banda_estrutural`), já em quarentena.
2. **O ponteiro `report/setup.py` (carimbo) está errado.** `report/setup.py` é o agregador de swing
   trade (`SetupSwing`), sem relação com macro. O carimbo real vive em **`cli.py:_carimbar_macro`
   (66-93)**, **`app.py:882-898`** e **`backtest.py`**. O stamp do β setorial precisa dos **três**.
3. **`test_ke_rim_menor_que_ke_live_de_banco` (invariante, marcado "SOBREVIVE a Fase 12") referencia
   `motores.ke_rim`, que D-08 DELETA.** Contradição a reconciliar: o teste não pode sobreviver
   chamando uma função apagada — reescrever para a relação unificada ou deletar junto.

**Primary recommendation:** Executar D-08→D-14 como planejado. Limiar do fallback = **3** (mínimo
estrutural para a mediana rejeitar 1 outlier — o propósito do D-02). Normalizar o prefixo "Emp. Adm.
Part. - " ao agrupar por `c.setor` (reduz o fallback de 42→24 tickers em 104, dentro do D-01, usando
a utilidade `arquetipo._setor_casa_token` já antecipada). Artefato de betas em `data/beta_setorial.yaml`,
carimbado em `cfg["capm"]["beta_setorial"]`, espelhando `ipca_deflatores`.

---

## Architectural Responsibility Map

Fase de engine pura (Python) — sem tiers web. O mapa aqui é por **camada do pipeline**.

| Capability | Camada primária | Camada secundária | Rationale |
|------------|-----------------|-------------------|-----------|
| Cálculo do `Ke` (rf + β_blume×ERP) | Engine pura (`capm.ke_local`) | — | Offline, determinística, lê só `cfg` (nunca rede) |
| β cru por ticker | Ingest (`build.py:160`, `dm.beta` Yahoo) | — | Dado de mercado, coletado na montagem da empresa |
| `setor → mediana(β)` (agregação) | **Passo offline / gerador** | Entry points (carimbo) | Precisa do universo inteiro; `analyze` tem 1 ticker (WR-03/D-06) |
| Carimbo do mapa em `cfg` | Entry points (`cli`, `app`, `backtest`) | — | A rede/artefato vive na borda; a engine lê `cfg` (pureza) |
| Aplicação do Blume + fallback | Engine pura (`capm`/helper) | — | Linear, determinístico, never-raise |
| Consumo do `a.ke` único | Engine (DDM, RIM, matriz, rota segurança) | — | Ponto único de verdade (D-09) |
| Orçamento de knobs (ERP) | `config.yaml` + `calibracao.lock.yaml` | Teste de partição | Mudança sancionada e visível no diff |

**Fronteira crítica (D-05/D-06):** o β setorial **NÃO pode** ser computado dentro de `analisar_acao`
— ela monta 1 ticker e não tem os pares. Isso é o anti-padrão WR-03 (a mesma ação mostraria Ke
diferente entre menus). O único lugar correto é **offline → artefato → carimbo**, idêntico ao já
provado com `rf_local`/`pi_ciclo`/`ipca_deflatores`.

---

## Corrected Pointer Table (o que o CONTEXT.md diz × o que o código É hoje)

| Referência CONTEXT.md | Real hoje | Status |
|-----------------------|-----------|--------|
| `capm.py` `ke_local`/`beta`/`CapmParams` | `ke_local` **L69**, `beta` L23-46, `CapmParams` L49-59 | ✓ OK |
| `motores.py:148-172` `ke_rim` | `ke_rim` **L148-172** exato | ✓ OK |
| `report.py:463-482` (cálculo `a.ke`) | `cap=cfg["capm"]` L462; `a.ke=ke_local(...)` **L470**; teto g_alto L481-482 | ✓ OK (faixa real 461-482) |
| `report.py:261` (`ke_rim(c.beta,cfg)`) | `ke=motores.ke_rim(c.beta, cfg)` **L261** exato | ✓ OK |
| `report.py:539-566` (matriz de sensibilidade) | matriz **L539-543**; banda vmin/vmax da matriz **L561-574** | ✓ OK (dois blocos) |
| `report.py:240-241` (rota segurança usa `a.ke`) | `v_seg = ddm.valor_gordon(dpa_sust*(1+g_cap), a.ke, g_cap)` **L241** | ✓ OK |
| `cli.py:66-91` `_carimbar_macro` | `_carimbar_macro` **L66-93** (rf_local, ipca_deflatores, pi_ciclo) | ✓ OK (faixa 66-93) |
| **`report/setup.py`** (ponto de carimbo) | **ERRADO** — é o agregador `SetupSwing` (swing trade). Carimbo real: `app.py:882-898` + `cli.py:66-93` + `backtest.py:117-130` | ✗ **CORRIGIR** |
| `ingest/build.py:139-168` (`c.setor`/`c.beta`) | `montar_empresa` L135+; `setor=setor or dm.setor` **L150**; `c.beta=dm.beta` **L160** | ✓ OK (setor L150 não L142) |
| `config.yaml:72-96` (capm/erp_local) | bloco `capm` L72; `erp_local:0.06` **L77**; `rf_local:0.105` L86 | ✓ OK |
| `config.yaml:244-268` (motores.rim) | `erp_banco:0.045` **L245**; `ke_piso:0.11` **L249**; `ke_teto:0.13` **L250** | ✓ OK |
| `calibracao.lock.yaml:58-72` (grau ERP) | grau `ERP`, `caminho: capm.erp_local`, `valor:0.06` **L60-71** | ✓ OK |
| `calibracao.lock.yaml:122-131` (congelados) | header congelados L121-127; `erp_banco` **L130**, `ke_piso` L132, `ke_teto` L134 | ✓ OK (ke_piso/teto em 132/134, não todos ≤131) |
| `test_blindagem_orcamento.py:238-239` | comentário sobre saturação (L238) + `test_a_suite_reage...` L222 | ✓ OK (é comentário, não assert-alvo) |
| `test_invariancia_inflacao_engine_itub4` (xfail strict) | decorator **L105-112**, função **L113**, assert L149-154 em `test_invariantes_v24.py` | ✓ OK |
| `test_blindagem_meta.py:60-68` (`xfail_estritos()`) | `tolerados = h.quarentenados() \| h.xfail_estritos()` **L68** | ✓ OK |
| golden `ITUB4 = 32,88` "a localizar em tests/" | **JÁ DELETADO na Fase 10** (PRIM-05, `test_backtest_cesta_rota_por_ticker`). Sem assert vivo. Ver §Golden | ✗ **JÁ FOI** |

---

## Distribuição setorial real (104 tickers) + limiar do fallback (D-04)

Fonte: `tests/fixtures/snapshot_sanidade_limpo_2026-07-15.yaml`, 104 tickers reais, campos `setor`
+ `beta`. [VERIFIED: parse Python do snapshot]

### Descoberta central: o `c.setor` cru fragmenta setores economicamente idênticos

A string CVM crua separa **holdings** ("Emp. Adm. Part. - X") das **operadoras** ("X") e ainda varia
a abreviação ("Construção Civil, Mat. Constr. e Decoração" × "Const. Civil, Mat. Const. e Decoração").
Exemplos medidos:

| Grupo econômico | `c.setor` cru (grupos separados) | Tickers |
|-----------------|----------------------------------|---------|
| Energia Elétrica | `Energia Elétrica` (9) **+** `Emp. Adm. Part. - Energia Elétrica` (6) | AURE3,CMIG3,CMIG4,CPLE3,CPLE6,EGIE3,ENEV3,EQTL3,TRPL4 / ALUP11,CPFE3,ELET3,ELET6,ENGI11,TAEE11 |
| Seguradoras | `Seguradoras e Corretoras` (2) **+** `Emp. Adm. Part. - Seguradoras e Corretoras` (2) | PSSA3,WIZC3 / BBSE3,CXSE3 |
| Metalurgia | `Metalurgia e Siderurgia` (4) **+** `Emp. Adm. Part. - Metalurgia e Siderurgia` (2) | CSNA3,FESA4,GGBR4,USIM5 / GOAU4,KEPL3 |
| Extração Mineral | `Extração Mineral` (2) **+** `Emp. Adm. Part. - Extração Mineral` (1) | CMIN3,VALE3 / BRAP4 |

> **BB × Bradesco (exemplo canônico do KE-03) funciona de qualquer jeito:** ambos caem em `Bancos`
> (10 tickers) na string crua. O problema de fragmentação atinge os OUTROS setores.

### Distribuição por número de betas disponíveis (não por tickers — β `null` não entra na mediana)

12 tickers têm `beta: null` no snapshot (não contribuem para a mediana do setor).

| Agrupamento | Setores distintos | Fallback @ limiar 2 | Fallback @ **limiar 3** | Fallback @ limiar 4 |
|-------------|-------------------|---------------------|-------------------------|---------------------|
| **`c.setor` cru** | 36 | 12 tickers (10 setores) | **42 tickers (24 setores)** | 55 tickers |
| **normalizado** (strip "Emp. Adm. Part. - ") | 28 | 7 tickers | **24 tickers (14 setores)** | 42 tickers |

Tabela normalizada, limiar 3, os setores que **agrupam** (n_betas ≥ 3) e sua mediana → Ke_Blume base
(β_blume = 0,33+0,67×mediana; contribuição ao Ke = β_blume×0,045):

| n_beta | Setor (normalizado) | mediana β | β_blume | contribuição ERP (×0,045) |
|-------:|---------------------|----------:|--------:|--------------------------:|
| 11 | Energia Elétrica | 0,615 | 0,742 | 3,34pp |
| 10 | Bancos | 1,216 | 1,145 | 5,15pp |
| 9 | Comércio (Atacado e Varejo) | 1,154 | 1,103 | 4,96pp |
| 6 | Metalurgia e Siderurgia | 0,740 | 0,826 | 3,72pp |
| 5 | Petróleo e Gás | 0,744 | 0,828 | 3,73pp |
| 4 | Agricultura | 0,599 | 0,731 | 3,29pp |
| 4 | Máquinas/Equip./Veículos | 0,677 | 0,784 | 3,53pp |
| 4 | Saneamento/Água/Gás | 0,798 | 0,865 | 3,89pp |
| 4 | Seguradoras e Corretoras | 0,777 | 0,851 | 3,83pp |
| 3 | Construção Civil | 1,620 | 1,415 | 6,37pp |
| 3 | Extração Mineral | 0,892 | 0,928 | 4,18pp |
| 3 | Papel e Celulose | 0,510 | 0,672 | 3,02pp |
| 3 | Serviços Médicos | 1,355 | 1,238 | 5,57pp |
| 3 | Serviços Transporte e Logística | 0,945 | 0,963 | 4,33pp |

[VERIFIED: cálculo Python sobre o snapshot]

### Recomendação de limiar: **3** — justificativa **estrutural** (nunca menciona ticker)

O D-02 escolheu a **mediana** com uma razão explícita: *"robusta a outliers — um beta distorcido não
contamina o grupo"*. Essa propriedade **só existe a partir de n=3**:

- **n=2:** a mediana = média dos dois valores. **Zero rejeição de outlier.** O propósito do D-02
  não é atingido — um único beta distorcido move o "setorial" em cheio.
- **n=3:** a mediana ignora o maior e o menor; **rejeita 1 outlier**. É o menor `n` em que a
  estatística escolhida no D-02 cumpre o papel para o qual foi escolhida.

Logo o limiar estrutural é `n_betas_disponíveis ≥ 3`. Abaixo disso, cai no fallback do D-04 (β
individual Blume). **A justificativa é uma propriedade da mediana, não um alvo de ticker** — passa no
teste `-k justificativa` e no `.githooks/commit-msg`. [CITED: propriedade da mediana amostral]

### Recomendação de normalização (dentro do D-01, não uma re-decisão)

D-01 trava a **chave** como `c.setor`. Recomendo que o agrupamento **normalize** a string antes de
agrupar — remover o prefixo `"Emp. Adm. Part. - "` (holding e operadora têm o **mesmo risco de
negócio**, que é exatamente a premissa do KE-03). Isso:
- Reduz o fallback de **42→24 tickers** no limiar 3 (de 40% para 23% do universo).
- Usa a utilidade **`arquetipo._setor_casa_token`** (`arquetipo.py:107`), explicitamente antecipada
  pelo CONTEXT D-01 code_context como *"útil se o agrupamento precisar normalizar strings CVM"*.
- **Não** muda a chave (continua derivada de `c.setor`), só higieniza a representação.

⚠️ Mesmo normalizado, "Construção Civil" e "Const. Civil" (abreviações diferentes) permanecem
separados — normalização por prefixo não resolve variação de abreviação. Ver **Questão Aberta #1**.

---

## Colapso `ke_rim ≡ ke_local` (prova para D-08 — sem resíduo/bloqueador)

Código atual (`motores.py:148-172`) [VERIFIED: leitura]:
```
ke_live = rf + beta × erp_local            # erp_local = 0,06
ke      = rf + beta × erp_banco            # erp_banco = 0,045
ke_clamp = max(ke_piso, min(ke, ke_teto))  # [0,11 , 0,13]
return   min(ke_clamp, ke_live)
```
`ke_local` (`capm.py:69`): `return rf_local + beta_acao × erp_local`.

**Depois da Fase 12** (erp_banco removido, clamp removido, ERP unificado em 0,045):
```
ke_rim(beta) = rf + beta × 0,045
ke_local(beta, rf, 0,045) = rf + beta × 0,045      ⟹  IDÊNTICOS
```
Termos residuais examinados, **nenhum bloqueia o colapso**:
- **rf:** `ke_rim` lê `cap.get("rf_local",0.105)`; `a.ke` lê `cap["rf_local"]`. **Mesmo rf_local.** ✓
- **teto `ke_live`:** `min(ke, ke_live)` — com `ke = rf+β×0,045 < rf+β×0,06 = ke_live` para β>0, o
  `min` já devolve `ke`. Some sozinho ao remover o clamp. Com o Blume piso β_blume≥0,33>0, β é sempre
  positivo → não-issue. ✓
- **beta de entrada:** aqui está a única diferença **de comportamento** (não de fórmula), e é
  **intencional**: hoje `ke_rim(c.beta)` usa **β CRU**; pós-Fase 12 o RIM recebe `a.ke`, que passa a
  usar **β setorial+Blume** (KE-03). Ou seja, o Ke do RIM **muda de nível** (β cru → β blume). Isso é
  a unificação, **não** um resíduo — `ke_rim` é deletado, não sobrevive com beta diferente.

**Conclusão:** colapso exato, sem bloqueador. `ke_rim` pode ser deletado com segurança; `report.py:261`
troca `ke=motores.ke_rim(c.beta, cfg)` por `ke=a.ke`. [VERIFIED: aritmética + leitura de código]

---

## Invariante estrutural `Ke_min > g_cap` (D-11 / KE-04)

Aritmética verificada [VERIFIED: cálculo Python]:

| rf | β floor | β_blume | Ke_min | Ke_min − g_cap (7,28%) |
|----|---------|---------|--------|------------------------|
| **9,58%** (Selic-ciclo carimbado ao vivo) | 0 (piso Blume absoluto) | 0,330 | **11,07%** | **+3,79pp** |
| 9,58% | 0,255 (PEAB3, mín. do universo) | 0,501 | 11,83% | +4,55pp |
| 10,5% (default offline `selic_fallback`) | 0 | 0,330 | 11,98% | +4,70pp |

**O número "11,07%" do CONTEXT corresponde ao rf carimbado ao vivo = 9,58%**, NÃO ao default offline
0,105. Racional: `0,0958 + 0,33×0,045 = 0,11065`. [VERIFIED: REQUIREMENTS cita "rf = Selic-ciclo
9,58%"; snapshot_bancos usa `rf_local:0.105`].

**Por que substitui o clamp por aritmética:** o Blume **põe piso em β em 0,33** (mesmo um β negativo
vira β_blume=0,33). Logo `Ke_min = rf + 0,33×ERP` **independe de outlier de beta**. Como `g_T ≤
g_cap = 7,28%` (GROW-03) e `Ke ≥ 11,07%`, o spread `Ke−g_T ≥ 3,79pp > 0` — a perpetuidade Gordon
`TV = RI×(1+g)/(Ke−g)` **converge por construção**. Bônus: 3,79pp > `ke_g_spread_min=0,03` → o guard
de spread também nunca dispara no piso.

**Margem de segurança do invariante:** para o `Ke_min` tocar o `g_cap` seria preciso `rf < 7,28% −
0,33×0,045 = 5,79%`. Selic-ciclo (média 10a) abaixo de 5,8% é historicamente implausível no Brasil.

**Recomendação de teste (D-11b):** asseverar a **desigualdade estrutural** `rf_carimbado +
0,33×erp_local > g_cap` (robusta a drift do rf), e documentar 11,07% como o valor no Selic-ciclo
atual — **não** cravar o número 11,07% como golden (seria golden de nível).

---

## Inventário do lock (D-10) — antes/depois

`calibracao.lock.yaml` hoje: **escopo = 29 folhas** [VERIFIED: leitura + contagem].
Partição = 3 graus de liberdade + 26 congelados.

| Bloco | Folhas hoje | Folhas depois da Fase 12 |
|-------|------------:|-------------------------:|
| motores | 10 (7 em `motores.rim` + 3) | **7** (4 em `motores.rim` + 3) |
| capm | 12 | 12 (ERP muda de **valor**, não some) |
| ddm | 5 | 5 |
| normalizacao | 2 | 2 |
| **Total escopo** | **29** | **26** |

**Folhas que SAEM da partição (congelados → deletadas do config `motores.rim` e do lock, mesmo diff):**
- `motores.rim.erp_banco: 0.045` (lock L130) — o 2º ERP morre; sobra `capm.erp_local`.
- `motores.rim.ke_piso: 0.11` (lock L132).
- `motores.rim.ke_teto: 0.13` (lock L134).

**Grau de liberdade ERP:** `capm.erp_local` continua sendo o grau; muda o **valor** `0.06 → 0.045`
(lock L60-71, `valor:`), mesmo commit. Continua 3 graus (ERP, n_fade, PIB_real) — **orçamento intacto**.

**Testes do lock que precisam ficar verdes no mesmo diff** [VERIFIED: `test_blindagem_orcamento.py`]:
- `test_orcamento_de_knobs_e_exatamente_3` (L44): verifica **partição** `folhas(cfg,escopo) ==
  graus ∪ congelados`. É **dinâmico** — lê o config e o lock. Remover as 3 folhas de ambos os lados
  mantém a partição completa (26 == 3 ∪ 23). Fica verde **sse** config e lock mudarem juntos.
- `test_knobs_batem_com_o_lock` (L119): cada valor congelado == valor no config. Remover as 3 entradas
  dos dois lados mantém a igualdade. (⚠️ O comentário L127 diz "30 folhas / 27 congelados" — está
  **stale** desde a Fase 11; o teste é dinâmico e não hardcoda o número, mas o comentário e o header
  "29 folhas" do lock devem ser atualizados para 26 por honestidade documental.)

**Sequenciamento de commits (§discretion D-10) — restrição do hook BLIND-05:**
`.githooks/commit-msg` [VERIFIED: leitura] **BLOQUEIA** `config.yaml` + qualquer
`tests/(fixtures/|test_*|classificacao.yaml|conftest.py|helpers_blindagem.py)|pyproject.toml` no mesmo
commit. **MAS** `config.yaml` + `calibracao.lock.yaml` é o par **SANCIONADO** (lock mora na raiz, fora
de `tests/`). Consequência para o plano:
- **Commit de knob:** `config.yaml` (erp_local, remove erp_banco/ke_piso/ke_teto) + `calibracao.lock.yaml`
  **juntos**, com trailer `Knob-Change-Justification: <razão econômica, sem citar ticker>`.
- **Deleção/edição de testes** (goldens de Ke, teste de determinismo) precisa ir em **commit
  separado** do `config.yaml`, senão o hook bloqueia. Isso é uma restrição real de ordenação atômica.

---

## Golden(s) a deletar / testes afetados (correção ao D-12)

**O golden `ITUB4 = 32,88` JÁ NÃO EXISTE como assert vivo.** Foi deletado na Fase 10 (PRIM-05,
`test_backtest_cesta_rota_por_ticker`, banda `_ITUB4_RIM_MIN/MAX` 30-40) [VERIFIED:
`test_backtest_bancos.py:61-62` documenta a deleção; `classificacao.yaml`]. As ocorrências restantes de
"32,88" em `tests/` são **narrativa** (comentários), **corpus do próprio detector AST**
(`helpers_blindagem.py:157/215/…` — NÃO tocar, é o teste do detector) ou **metadado de fixture**
(`snapshot_bancos:296 intrinseco_motor_observado: 32.88`, lido só por `scripts/capturar_snapshot_bancos.py`,
**não asseverado**). D-12/ROADMAP rule B restatam um critério **herdado da Fase 10** — não há assert de
32,88 para deletar aqui.

### Goldens que a Fase 12 REALMENTE mata (deletar + remover entrada em `classificacao.yaml`)

| Teste | Arquivo:linha | Assert | Ação |
|-------|---------------|--------|------|
| `test_ke_local_na_faixa_small_cap_br` | `test_capm_local.py:55-66` | `assert 0.13 < ke < 0.22` | **DELETE** (banda vinda de erp_local=0,06; já `golden_nivel`, morte agendada p/ Fase 12 em `classificacao.yaml:66`) |
| `test_ke_rim_na_banda_estrutural` | `test_motores.py:107-116` | banda `0,11–0,14` (`ke_piso/ke_teto`) | **DELETE** (`ke_rim` deletado; `classificacao.yaml:351` agenda p/ Fase 12) |
| `test_vulc3_cascata...` sub-banda `ke≥0,15` | `test_vulc3_regressao.py` | banda de Ke da cascata | **DELETE só a sub-banda** de Ke (`classificacao.yaml:487` já anota "[Fase 12] DELETADA"; os invariantes estruturais sobrevivem) |

### Testes que precisam de UPDATE (não deletar — mudança de fórmula, não crava nível)

| Teste | Arquivo:linha | Problema | Ação |
|-------|---------------|----------|------|
| `test_engine_offline_ke_determinístico` | `test_capm_local.py:104-127` | `esperado = rf_local + 0.88×erp_local` (β **cru**) | **UPDATE** para a fórmula Blume+setorial (`rf + β_blume×0,045`). É `invariante` de pureza offline; atualizar a fórmula ao novo modelo é legítimo (não é crava-nível). Commit separado do `config.yaml`. |
| `test_ke_rim_menor_que_ke_live_de_banco` | `test_motores.py:91-104` | chama `motores.ke_rim(1.0, cfg)` — **função deletada** | **RECONCILIAR** (Questão Aberta #2): reescrever para a relação do Ke unificado, ou deletar. `classificacao.yaml:350` diz "SOBREVIVE" — inconsistente com D-08. |
| `test_ke_local_materialmente_acima_do_ke_de_2019` | `test_capm_local.py:42-52` | `assert ke > 0.094` com β 0,88 cru | Provável **UPDATE** do beta de entrada (usar β_blume) — mas o assert `>0,094` deve seguir valendo (Ke novo ~12% > 9,4%). Verificar na execução. |

---

## Padrão de carimbo (fonte única) + artefato de betas (D-05/D-06)

### O padrão exato a espelhar (verificado em 3 sítios)

**`cli.py:66-93` `_carimbar_macro(cfg)`** [VERIFIED]:
```python
cfg["capm"]["rf_local"] = macro.selic_ciclo_para_capm(cfg["capm"]["selic_fallback"], anos)
cfg["macro"] = {**cfg.get("macro", {}),
    "ipca_deflatores": macro.ipca_deflatores_anuais(anos),
    "pi_ciclo": macro.ipca_ciclo_para_g(cfg["macro"].get("pi_ciclo", ...), anos)}
```
Chamado por `cmd_analyze` (L103) **e** `cmd_rank` (L177) — **mesma** fonte (WR-03).

**`app.py:882-898`** [VERIFIED]: mesmo carimbo, via funções cacheadas `rf_capm`/`ipca_deflatores_capm`/
`pi_ciclo_capm` (L246-258), escrevendo em `CFG["capm"]["rf_local"]` e `CFG["macro"][...]` antes de
`report.analisar_acao(c, CFG)` (L898).

**`backtest.py:117-130`** [VERIFIED]: `rodar_cesta` injeta `rf_local`/`ipca_deflatores` numa **cópia**
do cfg a partir do snapshot (`_CHAVES_GLOBAIS = {"data_base","rf_local","ipca_deflatores"}` L33).

A engine (`analisar_acao`) **nunca** toca a rede — lê `cfg["capm"]["rf_local"]` / `cfg["macro"][...]`.

### Recomendação concreta do artefato de betas setoriais

- **Gerador offline** (novo, irmão de `macro.selic_ciclo_para_capm`): computa `setor → mediana(β cru)`
  do universo, aplicando o **limiar 3 na geração** (setores com <3 betas **não** entram no mapa → a
  engine cai no fallback). Assinatura sugerida:
  ```python
  # em ingest/macro.py (ou novo ingest/betas.py)
  def mapa_beta_setorial(empresas, limiar=3) -> dict[str, float]:
      # agrupa por setor NORMALIZADO, mediana dos β não-None, só setores com n>=limiar
  ```
  Escrito num script de build (irmão de `scripts/capturar_snapshot_bancos.py`) para um arquivo
  **versionado**.
- **Arquivo:** `data/beta_setorial.yaml` (junto de `data/ticker_map.json`). Formato: `{setor_normalizado:
  mediana_beta}`. Versionado = determinístico, "derivado, não digitado" (gerado de dados reais),
  auto-atualiza ao regenerar (como o snapshot).
- **Chave em `cfg`:** `cfg["capm"]["beta_setorial"]` (dict). Carimbado nos **três** entry points
  (`cli._carimbar_macro`, `app.py:882+`, e adicionar `"beta_setorial"` a `backtest._CHAVES_GLOBAIS`
  para os testes offline). Helper de carimbo: `def carimbar_beta_setorial(cfg): cfg["capm"]
  ["beta_setorial"] = carregar_beta_setorial()` — irmão de `_carimbar_macro`.
- **Consumo na engine** (novo helper em `capm.py`, mantém `ke_local` puro):
  ```python
  def beta_blume(beta_cru, setor, mapa_setorial):
      base = mapa_setorial.get(_normalizar_setor(setor)) if mapa_setorial else None
      base = base if base is not None else beta_cru      # fallback D-04
      return 0.33 + 0.67*base if base is not None else None   # never-raise
  ```
  Depois `a.ke = capm.ke_local(beta_blume(c.beta, c.setor, cfg["capm"].get("beta_setorial")),
  cap["rf_local"], cap["erp_local"])`.
- **Teste D-06 (invariante analyze==rank):** montar 1 ticker (analyze) e o mesmo ticker num conjunto
  (rank), com o **mesmo** mapa carimbado, e asseverar `a_analyze.ke == a_rank.ke` para o mesmo ticker.

---

## BLIND-02b — mecânica do destravamento (D-13)

Estado atual [VERIFIED: `test_invariantes_v24.py:105-154`]:
```python
@pytest.mark.invariante
@pytest.mark.xfail(strict=True, reason="Doenca 1 ... Vira VERDE sozinho na FASE 12 ...")
def test_invariancia_inflacao_engine_itub4():
    ...
    variacao = abs(v_chocado / v_base - 1)
    assert variacao < LIMIAR_INFLACAO   # 0.05  ← NÃO MEXER
```
Hoje **xfail** porque o `ke_teto=0,13` satura sob o choque de +300bps: o Ke não se move 1bp, só o `g`
sobe, o spread encolhe e o `V` sobe ~+18% (medido). Removido o clamp (KE-04), o Ke reage ao rf e a
variação cai abaixo de 5%.

**Edição exata (D-13):**
1. **Remover** o decorator `@pytest.mark.xfail(strict=True, reason=...)` (L105-112). Manter
   `@pytest.mark.invariante`. O `assert variacao < 0.05` **não muda** (proibido afrouxar; PROIBIDO
   trocar por skip).
2. O `xfail_strict=true` do `pyproject.toml` faria o teste, se destravado, dar **XPASS = FAILED**
   enquanto o xfail existir e o código já estiver curado — por isso remover o marker **junto** com a
   remoção do clamp, no mesmo estado.

**Transição de `xfail_estritos()` — CORREÇÃO MEDIDA ao D-13 (BLOQUEADOR):**
[VERIFIED por execução: `h.xfail_estritos()` = `['tests/test_invariantes_v24.py::test_invariancia_inflacao_engine_itub4']` — **exatamente 1**, não 2]

O CONTEXT.md D-13 diz *"xfail_estritos() cai de 2→1"*. **Está errado.** BLIND-03 já foi curado na Fase
10 e seu xfail foi removido (o próprio docstring `test_invariantes_v24.py:15-18` confirma). **Hoje há
UM único xfail estrito** (BLIND-02b). Removê-lo faz `xfail_estritos()` cair **1 → 0**.

⚠️ **E 0 quebra uma guarda.** `test_blindagem_selecao.py:100-104` [VERIFIED] faz:
```python
doencas = set(h.xfail_estritos())
assert doencas, "Nenhum `xfail(strict=True)` na suite: as duas doencas do v2.4 ..."
```
Com 0 xfail estritos, `assert doencas` **FALHA**. Logo D-13 **não é só "remover o marker"** — a
remoção do último xfail estrito derruba `test_blindagem_selecao::test_...` e a premissa de
`test_blindagem_meta`. O planner precisa **reconciliar essa guarda no mesmo diff**: sua premissa ("as
doenças estão escritas como código") deixa de valer porque **ambas as doenças foram curadas** (BLIND-03
na Fase 10, BLIND-02b aqui). Opções: (a) adaptar a guarda para "0 é válido pós-cura, desde que os
invariantes normais permaneçam no run default"; (b) converter o teste num invariante que verifica que
BLIND-02b agora **passa como teste normal**. É mudança de contrato **porque o sistema foi curado** —
legítima, não um afrouxamento.

⚠️ Restrição de commit: `test_invariantes_v24.py` é `tests/test_*` → **não** pode co-commitar com
`config.yaml` (hook BLIND-05). A remoção do xfail vai em commit separado do knob.

---

## Validação sem clamp — superfície D-11 (nyquist_validation = false)

`config.json` tem `workflow.nyquist_validation: false` → a seção formal "Validation Architecture" é
omitida. Mas a superfície de validação do D-11 é **o coração desta fase** e o planner precisa dela.

**Framework:** pytest (`pyproject.toml`: `testpaths=["tests"]`, `xfail_strict=true`,
`addopts="-m 'not golden_nivel' --strict-markers"`). "Suíte verde" = 0 failed com goldens em
quarentena. [VERIFIED]

**Harness de regressão dos 104 tickers (mirror GROW-04/05):** existe
`tests/helpers_sanidade.py` que carrega `snapshot_sanidade_limpo_2026-07-15.yaml` (104 tickers) OFFLINE.
[VERIFIED]. É o harness a reusar para o D-11a.

**Duas provas do D-11:**
- **(a) Regressão anti-explosão nos 104 tickers:** rodar `analisar_acao` sobre os 104 com o Ke novo
  (β setorial+Blume, ERP 0,045, sem clamp) e asseverar, para cada ticker com Ke e V computados: `V`
  finito e positivo; `Ke − g_T > 0` (spread convergente); `Ke ≥ Ke_min` estrutural. **Nenhum guard
  novo** (o guarda P/B é Fase 13) — a asserção é "nada explode / diverge", não "está na banda X".
  Precisa que o snapshot carregue o mapa `beta_setorial` carimbado (adicionar às chaves globais).
- **(b) Invariante estrutural:** `rf_carimbado + 0,33×erp_local > g_cap` (§Invariante acima).

**Amostragem prática (sem Nyquist formal):**
- Por task: `pytest -k "capm or ke or invariancia_inflacao or blindagem_orcamento" -x` (rápido).
- Por wave/merge: `pytest` (suíte default, goldens em quarentena) — deve ficar verde.
- Gate de fase: `pytest` verde **+** a regressão dos 104 tickers verde **+** BLIND-02b agora normal e
  passando **+** `xfail_estritos()` = 1.

---

## Don't Hand-Roll

| Problema | Não construir | Usar | Porquê |
|----------|---------------|------|--------|
| Resolver rf/π/betas na engine | fetch de rede em `analisar_acao` | carimbo nos entry points → `cfg` | Pureza da engine; WR-03 (drift entre menus) |
| Mediana setorial por run | computar dentro de `cmd_analyze` | artefato offline `data/beta_setorial.yaml` | `analyze` tem 1 ticker, sem pares (D-06) |
| Match de string de setor | `==` / substring ad-hoc | `arquetipo._setor_casa_token` (limite de palavra) | Já existe, antecipado no D-01 |
| Evitar Ke explosivo | reintroduzir clamp | piso aritmético do Blume (`Ke_min > g_cap`) | Escopo negativo explícito; clamp é a Doença 3 |
| Carregar snapshot 104 | novo loader | `helpers_sanidade.py` + `backtest.carregar_snapshot` | Já offline/determinístico |

**Key insight:** nesta fase a tentação perigosa é **um clamp com outro nome**. O escopo negativo é
categórico: se um V explodir sem `ke_teto`, o bug está em `ROE_T`/spread (Fase 13), **não** no Ke.

---

## Common Pitfalls

### Pitfall 1: Computar a mediana setorial dinamicamente por run
**O que dá errado:** `cmd_analyze` monta 1 ticker, não tem os pares → mediana != a do `rank` → a
mesma ação mostra Ke/V diferente entre menus (WR-03, quebra o Core Value cross-modo).
**Evitar:** artefato offline carimbado; teste analyze==rank (D-06).

### Pitfall 2: Co-commitar `config.yaml` com testes
**O que dá errado:** `.githooks/commit-msg` bloqueia `config.yaml`+`tests/*` no mesmo commit (BLIND-05).
**Evitar:** knob (`config.yaml`+`lock`) num commit sancionado com trailer; edições de teste em commit
separado.

### Pitfall 3: Cravar "11,07%" ou "12,48%" como golden
**O que dá errado:** vira golden de nível — o reflexo do overfit v2.3. E 11,07% depende do rf ao vivo
(9,58%), não do default offline (11,98%).
**Evitar:** asseverar a **desigualdade** `Ke_min > g_cap`, não o número.

### Pitfall 4: Atualizar (em vez de deletar) os goldens de banda de Ke
**O que dá errado:** mantém vivo o reflexo que produziu o overfit (regra CLAUDE.md).
**Evitar:** DELETE `test_ke_local_na_faixa_small_cap_br` e `test_ke_rim_na_banda_estrutural` + suas
entradas em `classificacao.yaml`.

### Pitfall 5: Esquecer que `test_ke_rim_*` chamam uma função deletada
**O que dá errado:** deletar `ke_rim` quebra a coleta de 2 testes que o importam.
**Evitar:** tratar `test_ke_rim_menor_que_ke_live_de_banco` (reescrever/deletar) e
`test_ke_rim_na_banda_estrutural` (deletar) no mesmo diff que remove `ke_rim`.

### Pitfall 6: remover o BLIND-02b zera os xfail estritos e quebra `test_blindagem_selecao`
**O que dá errado (MEDIDO):** só existe **1** xfail estrito hoje (BLIND-02b). Removê-lo leva a 0, e
`test_blindagem_selecao.py:100-104` faz `assert doencas` (exige ≥1) → **FALHA**.
**Evitar:** reconciliar a guarda no mesmo diff (a premissa "há doença escrita como código" morre com a
cura). Não deletar o assert por deletar — adaptá-lo à realidade pós-cura (ambas as doenças curadas).

---

## Runtime State Inventory

Fase de refactor/rename de knobs — inventário aplicável.

| Categoria | Itens encontrados | Ação |
|-----------|-------------------|------|
| Dados armazenados | Snapshots de teste (`snapshot_bancos_2026-07-12.yaml:296 intrinseco_motor_observado=32.88`; `snapshot_sanidade_limpo`) carregam Ke/V observados. **Não** são asseverados como golden de nível — metadados diagnósticos. O snapshot precisa carregar `beta_setorial` carimbado para a engine offline computar o Ke novo. | Adicionar `beta_setorial` às chaves globais do snapshot/loader (`backtest._CHAVES_GLOBAIS`) |
| Config de serviço vivo | Nenhum serviço externo. Streamlit lê `config.yaml` no boot. | Nenhuma migração de dado externo |
| Estado registrado no SO | Nenhum (sem cron/scheduler tocado por esta fase). | Nenhuma — verificado por ausência de refs |
| Secrets / env vars | Nenhum. Selic/IPCA via BCB público (sem chave); β via Yahoo (sem chave). | Nenhuma |
| Artefatos de build | **Novo** artefato `data/beta_setorial.yaml` a gerar; `data/ticker_map.json` já existe (usado pelo hook). Nenhum egg-info/binário afetado. | Gerar `data/beta_setorial.yaml` no commit da fase |

**Canônico:** depois que `config.yaml`+`capm.py`+`motores.py` mudarem, o único estado que carrega o
método antigo é **o mapa `beta_setorial` nos snapshots de teste** — precisa ser gerado/carimbado, senão
os testes offline computam Ke com fallback individual (não setorial) e divergem do app.

---

## Environment Availability

| Dependência | Requerida por | Disponível | Versão | Fallback |
|-------------|---------------|-----------|--------|----------|
| Python 3 + pytest | toda a suíte | ✓ | pyproject `[tool.pytest]` | — |
| PyYAML | snapshots/lock | ✓ | usado em todos os loaders | — |
| BCB SGS (rede) | rf/π ao vivo (entry points) | n/a offline | — | `selic_fallback`/`pi_ciclo` default (degradação graciosa já implementada) |
| Yahoo Finance (β cru) | gerador do artefato | n/a offline | — | β `null` → fallback individual/omitido da mediana |

Sem bloqueadores. A engine e os testes rodam offline (snapshots congelados); a rede só é tocada nos
entry points, com degradação graciosa já existente.

## Project Constraints (from CLAUDE.md)

- **"Suíte verde" v2.4:** 0 failed com `golden_nivel` em quarentena, xfail estritos vermelhos por
  contrato, jackknife skipped. Golden que quebra é **DELETADO, não atualizado**.
- **Orçamento de 3 knobs** (`ERP`, `n_fade`, `PIB_real`) em `calibracao.lock.yaml`; qualquer knob de
  valuation muda **com o lock no mesmo diff**. 4º grau deixa a suíte vermelha.
- **Justificativa de knob NUNCA menciona ticker** (teste `-k justificativa` + `.githooks/commit-msg`).
- **NUNCA** afrouxar tolerância, marcar `xfail` casual, trocar `xfail`→`skip`, ou deletar assert para
  ficar verde.
- Hook não versionado: `git config core.hooksPath .githooks` em todo clone.
- `pytest tests/arquivo.py` **não funciona** (dispara `CLASSIFICACAO ORFA`) — usar `-k`.
- **β setorial é DADO, FORA do lock (D-07)** — não conta como grau de liberdade.

## Project Skills

Nenhum `SKILL.md` de projeto (só dentro de `.venv/…/streamlit`, irrelevante). [VERIFIED: find]

---

## State of the Art

| Abordagem antiga | Abordagem nova (Fase 12) | Impacto |
|------------------|--------------------------|---------|
| Dois Ke: `a.ke` (β cru, ERP 0,06) + `ke_rim` (β cru, ERP 0,045, clamp) | Um Ke: `a.ke` (β setorial+Blume, ERP 0,045), sem clamp | KE-01/05; RIM lê `a.ke` |
| Clamp `[0,11 ; 0,13]` como guarda-corpo | Piso aritmético do Blume (`Ke_min≈11,07% > g_cap`) | KE-04; remove Doença 3 (BLIND-02b) |
| β individual bruto | mediana setorial + Blume `0,33+0,67β` | KE-03; BB≈Bradesco; some 2,7× de espalhamento |
| ERP 0,06 (com small-cap 1,5%) | ERP 0,045 (mercado maduro puro) | KE-02; universo já filtrado por liquidez |

**Deprecado/removido nesta fase:** `motores.ke_rim`, `motores.rim.erp_banco`, `motores.rim.ke_piso`,
`motores.rim.ke_teto` (código + config + lock).

---

## Assumptions Log

| # | Claim | Seção | Risco se errado |
|---|-------|-------|-----------------|
| A1 | ~~Após remover o xfail resta ≥1~~ **RESOLVIDO (medido): há só 1 xfail estrito hoje; remover BLIND-02b leva a 0, o que QUEBRA `test_blindagem_selecao` (`assert doencas`)** | BLIND-02b / Pitfall 6 | Não é assumption — é blocker medido. A guarda `assert doencas` precisa ser reconciliada no mesmo diff. |
| A2 | `test_engine_offline_ke_determinístico` e `test_ke_local_materialmente...` usam empresa com setor válido | Golden/testes | Se a empresa-fixture não tem setor no mapa, o Ke cai no fallback individual — o `esperado` do update precisa refletir isso |
| A3 | Normalizar "Emp. Adm. Part. - " está dentro do D-01 (não re-decisão da chave) | Distribuição setorial | Se o usuário quis `c.setor` **cru literal**, o fallback fica em 42/104 (Questão #1) |

Todos os demais claims são `[VERIFIED]` por leitura de código, parse de snapshot ou cálculo.

---

## Open Questions (para o planner)

1. **Normalização de `c.setor` (D-01):** o grau de normalização é discricionário? Recomendo strip do
   prefixo "Emp. Adm. Part. - " (fallback 42→24). Mas "Construção Civil" × "Const. Civil" (abreviação)
   permanece fragmentado — vale um mapa de normalização de abreviações, ou aceita-se o fallback nesses
   casos de baixa contagem? **Recomendação:** strip do prefixo (alto impacto, baixo risco); aceitar o
   resto no fallback individual (never-raise, degradação graciosa já é o contrato do D-04).

2. **`test_ke_rim_menor_que_ke_live_de_banco` (contradição D-08 × classificacao):** o teste é marcado
   "SOBREVIVE a Fase 12" (`classificacao.yaml:350`), mas chama `motores.ke_rim`, que D-08 deleta. Reescrever
   para a relação do Ke unificado (ex.: o Ke do RIM == `a.ke`) ou deletar? **Recomendação:** reescrever
   como invariante da unificação (`ke_do_rim ≡ a.ke`) — preserva o espírito "Ke do RIM não excede o Ke
   ao vivo" que agora é trivialmente verdadeiro (são o mesmo).

3. **RESOLVIDO (não é mais aberta):** há **1** xfail estrito hoje (BLIND-02b), não 2. Removê-lo
   → 0 → quebra `test_blindagem_selecao::test_...` (`assert doencas`). **Decisão para o planner:** como
   reconciliar essa guarda (cujo propósito — "a doença está escrita como código" — cumpre-se ao ser
   curada)? Ver §BLIND-02b e Pitfall 6. Recomendação: converter em invariante "BLIND-02b passa como
   teste normal" e ajustar `test_blindagem_selecao` para aceitar 0 doenças pendentes pós-cura.

---

## Sources

### Primary (HIGH confidence)
- Código do repositório (leitura direta): `src/analista/core/capm.py`, `core/motores.py:148-172`,
  `report/report.py`, `cli.py`, `app.py:882-898`, `ingest/build.py`, `ingest/macro.py` refs.
- `calibracao.lock.yaml` (partição de 29 folhas, grau ERP, congelados).
- `config.yaml` (blocos `capm`, `macro.pi_ciclo`, `motores.rim`).
- Testes: `test_invariantes_v24.py`, `test_blindagem_orcamento.py`, `test_blindagem_meta.py`,
  `test_blindagem_selecao.py`, `helpers_blindagem.py`, `test_capm_local.py`, `test_motores.py`,
  `test_backtest_bancos.py`, `classificacao.yaml`, `pyproject.toml`.
- `.githooks/commit-msg` (regra de co-change BLIND-05).
- Parse Python de `tests/fixtures/snapshot_sanidade_limpo_2026-07-15.yaml` (distribuição setorial dos
  104 tickers, medições de β/mediana/Blume/Ke_min).

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` (KE-01..05, rf=9,58%), `.planning/ROADMAP.md` (regras A/B/C, critério
  soberano), `.planning/phases/11-.../11-CONTEXT.md` (padrão de carimbo, g_cap=7,28%).

### Tertiary (LOW confidence)
- Nenhuma — não houve dependência de fontes externas não verificadas.

---

## Metadata

**Confidence breakdown:**
- Ponteiros / colapso `ke_rim` / lock / goldens: **HIGH** — lidos e conferidos no código.
- Distribuição setorial / limiar 3 / Ke_min 11,07%: **HIGH** — computados sobre o snapshot real.
- Artefato de betas (formato/nome/chave): **MEDIUM** — recomendação de design, espelha padrão provado.
- Contagem de xfail estritos: **HIGH** — medida por execução (1 hoje → 0 após remover; quebra `test_blindagem_selecao`).

**Research date:** 2026-07-17
**Valid until:** ~2026-08-16 (30 dias; código estável, projeto local sem deps voláteis)
