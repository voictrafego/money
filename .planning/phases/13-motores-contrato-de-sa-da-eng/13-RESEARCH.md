# Phase 13: Motores + contrato de saída (ENG) - Research

**Researched:** 2026-07-19
**Domain:** Refactor interno (colapso de 4 motores → RIM único), contrato de saída do livro, corte contado de knobs
**Confidence:** HIGH (o alvo é 100% código deste repositório — verificado por leitura direta dos arquivos-fonte)

> **Natureza da fase:** esta é uma fase de **refatoração/colapso**, não greenfield. Não há
> biblioteca nova, dependência externa ou API para pesquisar — o "estado da arte" relevante é o
> **próprio código** e o **método do livro**. Toda a pesquisa abaixo é grounding no código real
> (assinaturas, sites de edição, contratos) e nas decisões travadas do 13-CONTEXT.md.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (13-CONTEXT.md §Decisions — copiadas verbatim em substância)

**Âncora de ROE por arquétipo (ENG-01/ENG-03)**
- **D-01:** `arquetipo.ARQUETIPO_MOTOR` (`arquetipo.py:48-54`) deixa de mapear arquétipo→*motor* e
  passa a mapear arquétipo→**política de derivação do ROE-âncora/base** do RIM único. A **fórmula
  RIM é idêntica** para todos; o que varia por arquétipo é o **insumo** (ROE-âncora e base de book).
- **D-02:** `lucro_normalizado`, `dcf_crescimento`, `nav_contabil` **não são mais motores primários**
  — sobrevivem (se sobreviverem) apenas como **derivadores de insumo** do RIM. `_intrinseco_por_motor`
  (`report.py:201-327`) colapsa num caminho único que sempre chama o RIM.
- **D-03:** financeira/madura → ROE **through-cycle mediana**; cíclica → ROE **implícito do lucro
  normalizado 7-10a**; crescimento → ROE **atual + retenção** com fade (`n_fade`). Formato é
  arquétipo→âncora, não arquétipo→motor. Granularidade exata → discricionário do researcher.

**Ensemble e guardas (ENG-02)**
- **D-04:** `_guarda_san01` (`report.py:108-182`), `_guarda_faixa_ddm` (`report.py:77-105`), a banda
  do ensemble (`banda_do_motor`, `divergencia_ativa`, VER-01/ENS-01 em `AnaliseAcao`) e a 2ª lente
  ensemble×DDM + divergência do ranque (`cli.py:203-243`) são **deletados** — não portados.

**CONCESSAO_FINITA + novo default (ENG-04)**
- **D-05:** hard-route `c.eh_concessionaria` (`arquetipo.py:159-160`) passa a rotular
  **`CONCESSAO_FINITA`** (mantém guarda anti-Petróleo). O default-por-eliminação (`:180`, hoje
  `PAGADORA_REGULADA`) passa a ser **`PAGADORA_MADURA`** (RIM normal, ROE through-cycle).
- **D-06:** `CONCESSAO_FINITA` usa **modelo de ativo financeiro** — o book **já é** o VP da RAP →
  **não conserta o `g`** (evita double-count de inflação sob ICPC 01). Mecânica exata → discricionário.

**Contrato de saída (ENG-05/06/07/08)**
- **D-07:** a engine entrega o contrato completo NESTA fase. Tríade **SUBAVALIADA / NO INTERVALO /
  SOBREAVALIADA** de `V` vs região `[V×(1−MS), V×(1+MS)]`. MS = parâmetro de config, **simétrica
  5-10%, nunca calibrada**. Ponte auditável `P/B justo = 1 + (ROE_T − Ke)/(Ke − g) × VPA = V` com
  `payout_T = 1 − g/ROE_T` **exibida**. Matriz Ke×g **vive** (sobre `a.ke`/`g` das Fases 11-12).
- **D-08:** UI Streamlit = **mudança mínima** — widget/param de MS, a tríade, a matriz Ke×g, e a
  **remoção de "Evitar" e "Qualidade Baixa"** (`selo.py:_MATRIZ[("Baixa","Caro")]`, eixo "Baixa").
- **D-09:** a tríade migra do prefixo do veredito do **DDM** para o **V do RIM** vs a região da MS.

**Guarda-corpo P/B justo (ENG-08/ENG-09)**
- **D-10 (dois níveis):** (a) **TESTE de correção**: `payout_T` negativo/>100% ou `P/B justo` fora de
  `(0, 6)` **FALHA o teste** (bug, não resultado). (b) **RUNTIME never-raise**: fora da faixa
  **degrada** (suprime veredito / VERIFICAR), **não levanta** (contrato SAN-06). O guard **não**
  conserta o `VPA = PL/num_acoes` inflado — ele **sinaliza**.

**Rebaixamento do Ranking (ENG-11)**
- **D-11:** colunas **preço-alvo / upside / veredito** saem do Ranking (regressão de pares é
  matematicamente cega ao nível de preço); ficam **múltiplos crus** (P/L, P/VP, DY, BSD).

**Corte de knobs (ENG-10)**
- **D-12:** bloco `motores:` de **~20/11 → ≤5 chaves, contadas**. Sub-blocos `motores.ciclica` e
  `motores.crescimento` colapsam. Qualquer folha que saia do config sai da partição do
  `calibracao.lock.yaml` **no mesmo commit**. **Orçamento intacto em 3 graus** (`ERP`, `n_fade`,
  `PIB_real`) — nenhum grau novo.

### Claude's Discretion (o trabalho real do researcher/planner)
1. O **mapa exato** arquétipo → política de ROE-âncora (D-03), calibrado ao código e à distribuição.
2. A **mecânica precisa** do carve-out `CONCESSAO_FINITA` no RIM único (D-06).
3. **Quais ≤5 chaves** sobrevivem em `motores:` e o destino de `ciclica.anos_media` /
   `crescimento.n_anos_explicito` como políticas de input (D-12).
4. O **formato exato** da ponte P/B exibida e dos rótulos do contrato (D-07/D-08).
5. A **divisão em waves** e a ordem dos commits atômicos (o diff de knob sancionado precisa ser coeso).
6. O **conjunto exato de colunas** do screener rebaixado (D-11).

### Deferred Ideas (OUT OF SCOPE)
- **Validação honesta / hold-out / caso do livro (ITUB4 = R$ 37,22)** — **Fase 14** (VAL). Validar
  aqui **queima o hold-out**. Ver §"Fronteira dura com a Fase 14" abaixo.
- **Motor `nav`/SOTP real para holdings** (ITSA4, B3SA3) — Future Requirement. Nesta fase o NAV é, no
  máximo, piso patrimonial/insumo do RIM.
- **Score BSD por arquétipo** — Future Requirement. O selo permanece (menos "Evitar"/"Qualidade Baixa").
- **Reforma visual pesada da tela** — só o mínimo de exibição do contrato (D-08).
- **Deflator no `dpa_recorrente`** — Future Requirement.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Descrição | Research Support (o que habilita a implementação) |
|----|-----------|---------------------------------------------------|
| ENG-01 | Um único motor de valor (RIM) | `motores.rim` (`motores.py:66`) já é o RIM híbrido multiestágio que sobrevive; `_intrinseco_por_motor` (`report.py:201`) é o dispatch a colapsar. Ver §"Mapa de âncoras" e §"Colapso do dispatch". |
| ENG-02 | Ensemble morre + `_guarda_san01`/`_guarda_faixa_ddm` removidos | Sites exatos: `report.py:77-105`, `108-182`, campos de ensemble em `AnaliseAcao:65-74`, `cli.py:203-243`, `app.py` bloco de divergência. Ver §"Remoção do ensemble". |
| ENG-03 | Classificador escolhe ÂNCORA (erro limitado), não motor | `arquetipo.classificar` (`arquetipo.py:124`) intocado; `ARQUETIPO_MOTOR` (`:48`) → `ARQUETIPO_ANCORA_ROE`. Ver §"Mapa de âncoras". |
| ENG-04 | `PAGADORA_REGULADA` → `PAGADORA_MADURA` + `CONCESSAO_FINITA` | Split em `arquetipo.py:159-160` (hard-route) e `:180` (default). Ver §"Split do arquétipo" e §"Carve-out CONCESSAO_FINITA". |
| ENG-05 | Contrato de saída do livro (tríade + região de valor) | `selo.faixa_do_veredito` (`selo.py:88`) + o veredito de `report.py:639-663`. Ver §"Contrato de saída". |
| ENG-06 | MS = controle do usuário, simétrica, nunca calibrada | `veredito.margem_seguranca` já existe (`config.yaml:118`), declarada em `user_control` do lock (`calibracao.lock.yaml:104-119`). Ver §"Margem de segurança". |
| ENG-07 | Matriz Ke×g vive, sobre Ke/g corretos | `ddm.matriz_sensibilidade` (`report.py:551`), grade em `config.yaml:108-110`. Herdada da Fase 12; reusar. |
| ENG-08 | Ponte auditável exibida + teste de correção | Identidade fechada JÁ existe como função pura no teste BLIND-02a (`test_invariantes_v24.py:96`). Ver §"Ponte P/B auditável". |
| ENG-09 | Guarda-corpo sobre a razão `0 < P/B < 6` | Dois níveis (D-10). Ver §"Guarda-corpo em dois níveis". |
| ENG-10 | `motores:` ~20/11 → ≤5 chaves, contadas | 7 folhas hoje (medido). Ver §"Corte contado de knobs". |
| ENG-11 | Ranking rebaixado a screener por múltiplos | `comparables.preco_alvo_por_regressao` (`:181`), `freio.py`, `cli.py:218-243`, `app.py:1638-1652`. Ver §"Rebaixamento do Ranking". |
</phase_requirements>

---

## Summary

Esta fase é uma **cirurgia de simplificação**: os 4 caminhos de `_intrinseco_por_motor`
(`report.py:201-327`) — `rim`, `normalizado`, `dcf`, `nav`, mais a rota `seguradora` e o passthrough
`ddm` — colapsam num **único caminho RIM**. Sob clean surplus (Ohlson 1995), RIM ≡ DDM ≡ DCF-equity;
os 4 "motores" eram a **mesma** equação com inputs inconsistentes, e a dispersão medida
(0,81/0,63/0,63/0,48) era a assinatura dos bugs já curados nas Fases 9-12 — não divergência de método.
O que sobrevive e melhora é o **classificador de arquétipo** (`arquetipo.classificar`): ele para de
escolher um *modelo* (erro ilimitado) e passa a escolher uma *âncora de ROE* (erro limitado). Os 3
ex-motores viram **derivadores de insumo**: `lucro_normalizado` → o ROE-âncora da cíclica;
`nav_contabil` → o piso patrimonial da holding; `dcf_crescimento` → **deletado** (Armadilha 2:
consertá-lo com FCFE o torna DDM por teorema).

O **contrato de saída já está quase certo no app** e **não deve ser trocado**. O que muda: (1) a
tríade passa a computar de `V vs [V×(1−MS), V×(1+MS)]` em vez de ler o prefixo do veredito do DDM
(D-09); (2) a MS vira **parâmetro exposto ao usuário** (ela já existe como `veredito.margem_seguranca`,
congelada no `user_control` do lock aguardando exatamente o ENG-06); (3) a **ponte auditável P/B** é
exibida e vira teste de correção — e a **identidade fechada já existe como função pura testada**
(`test_invariantes_v24.py:96`, o BLIND-02a). O ensemble inteiro (`_guarda_san01`, `_guarda_faixa_ddm`,
banda motor×contraponto, divergência, `_veredito_fronteirico`) **morre** — eram cicatrizes que mediam
os próprios bugs do projeto.

Finalmente: o bloco `motores:` do `config.yaml` (hoje **7 folhas**, medido) cai para **≤5 contadas**,
com o `calibracao.lock.yaml` reescrito **no mesmo commit** e o **orçamento intacto em 3 graus**; e o
Ranking é **rebaixado** (saem preço-alvo/upside/veredito, ficam múltiplos crus) — não deletado.

**Primary recommendation:** Um único `motores.rim(...)` alimentado por uma tabela
`ARQUETIPO_ANCORA_ROE` que decide **de onde vem o `roe0`/`roe_terminal`/base de book**; o RIM,
`a.ke` (Fase 12) e `g_cap`/`g_T` (Fase 11) já são os insumos prontos. Provar por **execução da
regressão dos 104 tickers** (o oráculo herdado de GROW-04/05 e KE-04), **nunca** pelo caso do livro
(Fase 14). Todo diff de knob = `config.yaml` + `calibracao.lock.yaml` juntos, **separado** de qualquer
edição em `tests/` (o hook BLIND-05 casa `tests/classificacao.yaml`).

---

## Architectural Responsibility Map

Este projeto é um **monólito Python de camada única** (engine pura + Streamlit + CLI). Não há tiers
browser/API/DB. O "tier" relevante é a **camada arquitetural interna**, e o mapa abaixo é o que o
plan-checker deve usar para verificar que nada foi posto no lugar errado.

| Capability | Camada primária | Camada secundária | Rationale |
|------------|-----------------|-------------------|-----------|
| Classificação de arquétipo | `core/arquetipo.py` (pura) | — | Lê só sinais de `CompanyData`; nunca recalcula método. Sobrevive intocado no corpo; só o registry muda. |
| Fórmula de valor (RIM único) | `core/motores.py::rim` (pura) | — | Recebe números-síntese prontos; never-raise. A ÚNICA fórmula de valor pós-fase. |
| Derivação do ROE-âncora por arquétipo | `report/report.py` (orquestração) | `core/normalizacao.py`, `core/lentes.py` | A política arquétipo→insumo mora no orquestrador (`_intrinseco_por_motor`), consumindo primitivas puras. |
| Custo de capital `a.ke` | `core/capm.py` (pura) + entry points (carimbo) | — | **JÁ PRONTO** (Fase 12). Esta fase NÃO recomputa; só consome `a.ke`. |
| Crescimento `g_cap`/`g_T` | `report.py` (deriva de cfg) | — | **JÁ PRONTO** (Fase 11). `g_cap` derivado na engine; `g_T` fechado por empresa. NÃO recalibrar. |
| Contrato de saída (tríade, região, ponte P/B) | `report/report.py` (veredito) | `report/selo.py` (camada derivada) | O veredito computa V vs região; o selo deriva quadrante. Firewall selo↛report preservado. |
| Margem de segurança (MS) | `config.yaml` (param) → `report.py` (consumo) → UI (widget) | — | Controle do usuário, nunca calibrado. Já existe como `veredito.margem_seguranca`. |
| Matriz Ke×g | `core/ddm.py::matriz_sensibilidade` (pura) | `report.py` (monta em torno de `a.ke`) | Herdada da Fase 12; reusar, não reinventar. |
| Screener por múltiplos (Ranking) | `core/comparables.py` (pura) + `cli.py`/`app.py` (view) | `core/freio.py` | Múltiplos crus permanecem; a imputação de preço-alvo/upside sai da view. |
| Orçamento de knobs | `config.yaml` ↔ `calibracao.lock.yaml` ↔ `tests/test_blindagem_orcamento.py` | — | Partição das folhas do escopo; contagem é critério de verificação. |

---

## Runtime State Inventory

> Fase de refatoração de código/config. Nenhum estado de runtime externo armazena os nomes de motor.

| Categoria | Itens encontrados | Ação necessária |
|-----------|-------------------|-----------------|
| **Stored data** | **Nenhum** — os snapshots de teste (`tests/fixtures/snapshot_*.yaml`, `hs.CAMINHO_SNAPSHOT_LIMPO`) congelam **dados crus de entrada** (fundamentos CVM, preços), **não** valores computados por motor nem nomes de arquétipo. Verificado: os snapshots são regenerados a partir do ingest; a engine roda sobre eles. | Nenhuma migração de dados. O snapshot limpo (DATA-06) é lido cru; o intrínseco é recomputado a cada run. |
| **Live service config** | O app Streamlit deployado na VPS (`31.97.130.40` via Docker) roda o mesmo código. Não há workflow n8n / dashboard / config em UI externa que embuta nome de motor. | Redeploy do app após a fase (fora do escopo de código — é operação de release). |
| **OS-registered state** | **Nenhum** — sem Task Scheduler / cron / systemd embutindo nomes de motor. Verificado: o projeto é engine + Streamlit, sem jobs registrados. | Nenhuma. |
| **Secrets/env vars** | **Nenhum** — nenhum secret/env var referencia motor/arquétipo por nome. | Nenhuma. |
| **Build artifacts** | **Nenhum** — projeto Python rodado do source (`.venv`); sem egg-info/binário que carregue nome de motor. O `pytest tests/arquivo.py` direto quebra a coleta (CLASSIFICACAO ORFA) — usar `-k`. | Nenhuma. |

**A pergunta canônica:** *depois que todo arquivo do repo é atualizado, que sistema de runtime ainda
tem o nome antigo cacheado?* Resposta medida: **nenhum**. O único "estado" a atualizar fora do código
é o **deploy** do app na VPS (operação de release, não tarefa de código).

---

## Architecture Patterns

### Diagrama do fluxo pós-fase (a forma-alvo)

```
CompanyData (dados já curados: Fases 9-12)
      │
      ▼
arquetipo.classificar(c, cfg)  ──►  ResultadoArquetipo(chave)   [SOBREVIVE INTOCADO no corpo]
      │
      ▼
ARQUETIPO_ANCORA_ROE[chave]    ──►  política de derivação do INSUMO   [NOVO nome; era ARQUETIPO_MOTOR]
      │
      ▼
_derivar_insumo_rim(politica, c, cfg)  ──►  (roe0, roe_terminal, base_book, retencao, g_terminal_policy)
      │                                       ├─ financeira/madura → roe_valuation (through-cycle)
      │                                       ├─ ciclica          → ROE = lucro_normalizado 7-10a ÷ book
      │                                       ├─ crescimento      → roe0 = roe_qualidade_atual, fade n_fade
      │                                       ├─ holding          → NAV piso (book floor)
      │                                       └─ concessao_finita → g_terminal PINADO (não IPCA) [carve-out]
      │
      ▼
motores.rim(vpa0, roe0, ke=a.ke, retencao, n=n_fade, g_terminal=g_T, roe_terminal, ...)  ──►  V
      │                                       [A ÚNICA fórmula de valor. a.ke e g_T já prontos.]
      ▼
V  ──►  região de valor [V×(1−MS), V×(1+MS)]   ──►  tríade SUB / NO INTERVALO / SOBRE
      │                                              (D-09: de V, não do prefixo do DDM)
      ├──► ponte auditável: P/B justo = 1 + (ROE_T−Ke)/(Ke−g) ; payout_T = 1 − g/ROE_T   [exibida + teste]
      ├──► guard: 0 < P/B < 6  →  teste FALHA se fora (bug) / runtime DEGRADA (never-raise)
      └──► matriz Ke×g em torno de a.ke   [herdada Fase 12]
      │
      ▼
selo.montar_selo(bsd, veredito, cfg)  ──►  quadrante  [SEM "Evitar"/"Baixa"×"Caro"]
      │
      ▼
UI Streamlit / CLI  (tríade + MS widget + matriz + ponte)     Ranking → screener por múltiplos crus
```

**O que MORRE neste diagrama** (comparar com o `report.py` atual): a rota `seguradora`, o passthrough
`ddm`, `_guarda_faixa_ddm`, `_guarda_san01`, o bloco ensemble (`contraponto_valor`, `banda_do_motor`,
`divergencia_*`), `_veredito_fronteirico`/VER-02, `_hipotese_divergencia`. Ver §"Remoção do ensemble".

### Pattern 1: Registry arquétipo → política (não arquétipo → motor)

**O quê:** `ARQUETIPO_MOTOR` (dict `str→str` de id de motor) vira `ARQUETIPO_ANCORA_ROE` (dict de
política de derivação de insumo). A **assinatura de `arquetipo.classificar` não muda**; o corpo do
classificador não muda (só as duas linhas de split do D-05).

**Quando usar:** sempre — é o coração do ENG-01/ENG-03.

**Exemplo (forma recomendada, o planner ajusta):**
```python
# core/arquetipo.py  — 5→6 chaves de arquétipo (split de PAGADORA_REGULADA)
FINANCEIRA = "financeira"
PAGADORA_MADURA = "pagadora_madura"          # NOVO nome do default-por-eliminação (ex-PAGADORA_REGULADA)
CONCESSAO_FINITA = "concessao_finita"        # NOVO: hard-route eh_concessionaria (carve-out ICPC 01)
CICLICA = "ciclica"
CRESCIMENTO = "crescimento"
HOLDING = "holding"

# arquétipo → POLÍTICA de ROE-âncora (não mais → motor). Um enum/str de política, consumido
# por _derivar_insumo_rim no report. Ex.: "through_cycle" | "normalizado" | "atual_fade" | "nav_piso".
ARQUETIPO_ANCORA_ROE = {
    FINANCEIRA:       "through_cycle",
    PAGADORA_MADURA:  "through_cycle",
    CONCESSAO_FINITA: "through_cycle_sem_g",   # carve-out: g terminal pinado (D-06)
    CICLICA:          "normalizado",
    CRESCIMENTO:      "atual_fade",
    HOLDING:          "nav_piso",
}
```

### Pattern 2: Um único caminho RIM (colapso do dispatch)

**O quê:** `_intrinseco_por_motor(motor, c, a, cfg)` deixa de ter 6 ramos (`rim`/`normalizado`/`dcf`/
`nav`/`ddm` + rota `seguradora`) e passa a: (1) derivar o insumo pela política do arquétipo; (2)
chamar **sempre** `motores.rim(...)`. Renomear a função ajuda (ex.: `_valor_rim`).

**Quando usar:** o dispatch principal em `report.py:519` e — se sobreviver algo do fronteiriço —
o ponto único. Como o ensemble/fronteiriço morre (D-04), o segundo consumidor de
`_intrinseco_por_motor` (o `_veredito_fronteirico`) desaparece junto.

**Nota crítica de insumo por arquétipo (a mecânica que o planner precisa acertar):**
- **through_cycle** (financeira, madura): `roe0 = c.roe_valuation()`, `roe_terminal =
  _roe_through_cycle(c, rim_cfg)` — **exatamente o que o ramo `rim` já faz hoje** (`report.py:255-268`).
  É o baseline; ITUB4/bancos não regridem.
- **normalizado** (cíclica): o RIM precisa de um `roe0` que reflita o **poder de lucro mid-cycle**,
  não o ROE do ano corrente. Derivar: `lpa_norm = mult.lpa(norm.media_ciclo(serie_deflacionada,
  anos_media), num_acoes)` (a série JÁ deflacionada por IPCA, PRIM-04, como o ramo `normalizado`
  faz em `report.py:285-309`), e então `roe0 ≈ lpa_norm / vpa0`. Isto substitui o
  `motores.lucro_normalizado(...)` (Gordon-P/L) por um RIM alimentado pelo ROE normalizado — evita a
  Armadilha 2 e mantém a fórmula única. `motores.lucro_normalizado` pode virar helper de derivação
  do `lpa_norm` OU ser inlinado.
- **atual_fade** (crescimento): `roe0 = c.roe_qualidade_atual()` (o endpoint, não a mediana — o mesmo
  sinal que `arquetipo.classificar` usa em `arquetipo.py:167`), com fade sobre `n_fade` até o excesso
  sustentável. É o comportamento nativo do `motores.rim` (a janela explícita já faz fade). O
  `dcf_crescimento` **morre** — **não** substituir por FCFE (Armadilha 2: `lpa × payout` = DDM por
  teorema; WEGE3 0,58 → 0,26).
- **nav_piso** (holding): o RIM já ancora no `vpa0` (1º termo); a holding = RIM com o NAV como piso
  patrimonial. `motores.nav_contabil` (= `lentes.vpa`) pode sobreviver como derivador do piso.
  SOTP real é Future Requirement (deferido).

**Anti-Patterns a evitar:**
- **Consertar o `dcf_crescimento` com FCFE** (`lpa × payout`): vira DDM por teorema. **Deletar, não consertar.**
- **Consertar o `g` das transmissoras** sob ICPC 01: double-count de inflação. É o carve-out.
- **Portar `_guarda_san01`/`_guarda_faixa_ddm`/ensemble** "por segurança": são cicatrizes do viés.
- **Recomputar `a.ke` ou recalibrar `g_cap`**: já prontos (Fases 11-12). Tocar apaga o diagnóstico.
- **Calibrar a MS** contra dispersão/preço/taxa de compra (Armadilha 4).

---

## Mapa de âncoras por arquétipo (D-01/D-03 — discricionário resolvido)

Grounding nas assinaturas reais (`report.py`, `arquetipo.py`, `motores.py`):

| Arquétipo | Política ROE-âncora | `roe0` (janela) | `roe_terminal` | `g_terminal` | Base de book | Ex-motor absorvido |
|-----------|--------------------|-----------------|----------------|--------------|--------------|--------------------|
| FINANCEIRA | through_cycle | `c.roe_valuation()` | `_roe_through_cycle` | `g_T = max(0, min(ROE_T×ret, g_cap))` | `vpa0` (PL/ações) | (o RIM já era este) |
| PAGADORA_MADURA | through_cycle | `c.roe_valuation()` | `_roe_through_cycle` | `g_T` (idem) | `vpa0` | (era default→DDM; agora RIM) |
| CONCESSAO_FINITA | through_cycle **sem g** | `c.roe_valuation()` | `_roe_through_cycle` | **pinado (ver carve-out)** | `vpa0` (= VP da RAP) | (era default→DDM) |
| CICLICA | normalizado | `lpa_norm_deflacionado / vpa0` | `_roe_through_cycle` | `g_T` | `vpa0` | `lucro_normalizado` → derivador |
| CRESCIMENTO | atual + fade | `c.roe_qualidade_atual()` | `_roe_through_cycle` | `g_T` | `vpa0` | `dcf_crescimento` → **deletado** |
| HOLDING | nav piso | `c.roe_valuation()` | `_roe_through_cycle` | `g_T` | `vpa0` (piso NAV) | `nav_contabil` → piso |

**Observação load-bearing:** hoje, `pagadora_regulada → "ddm"` (motor DDM, veredito por banda DDM). O
split D-05 muda isso: **madura e concessão passam a rodar o RIM** como todos os outros. Isto **altera
o número** de TAEE11/regulada (hoje o veredito vem do DDM). Isso é esperado (o RIM é a fórmula única),
mas é exatamente o tipo de mudança que a **regressão dos 104** deve medir antes do plano (não pode
explodir; ver §"Estratégia de prova por execução"). Confiança MEDIUM aqui — o comportamento exato de
TAEE11 sob RIM precisa ser **medido**, não assumido.

---

## Carve-out CONCESSAO_FINITA (D-06 — mecânica precisa recomendada)

**O problema (memória `rim-terminal-value-root-cause` + REQUIREMENTS ENG-04):** transmissoras sob
ICPC 01 usam **modelo de ativo financeiro** — o `patrimonio_liquido` (book) **já é** o VP da RAP
(Receita Anual Permitida descontada). Em ano de IPCA alto o ROE dispara (a RAP é indexada). Se o RIM
aplicar o `g_cap` (que **embute inflação** — `g_cap = (1+π_ciclo)(1+PIB_real)−1`) ao terminal dessa
empresa, conta a inflação **duas vezes**: uma no book que já a incorpora, outra no crescimento terminal.

**Mecânica recomendada (a mais limpa, o planner decide):** para `CONCESSAO_FINITA`, **não liberar o
terminal de crescimento** — passar `g_terminal = None` (ou pinar em 0). O `motores.rim` **já suporta
isto nativamente**: `motores.py:128-129` só libera o terminal quando `g_terminal is not None E
ke − g_terminal ≥ ke_g_spread_min`; com `g_terminal=None`, `vp_terminal = 0.0` e o valor vem só da
janela explícita de RI + o book (que já é o VP da RAP). Isto **não conserta o `g`** — ele simplesmente
não entra. É "vida finita" por construção, coerente com "concessão finita".

- **Alternativa** (se medição mostrar que zerar o terminal subvaloriza demais): pinar
  `g_terminal = PIB_real` (2,0% real puro, **não** reexpresso a nominal) — cresce só o real, não a
  inflação já capturada. Mais frágil (introduz uma exceção de nível); prefira a opção `None`.

**Guarda que sobrevive:** o casador anti-Petróleo (`_setor_casa_token(setor, regulada_excluir)`,
`arquetipo.py:159`) **permanece** no hard-route de `CONCESSAO_FINITA` — Petróleo com
`eh_concessionaria` **não** cai no balde da concessão. O teste `test_petroleo_nao_vira_pagadora_regulada`
(contrato) precisa migrar de rótulo (`PAGADORA_REGULADA` → `CONCESSAO_FINITA`) mas o comportamento é
o mesmo.

**Confiança:** MEDIUM. A **direção** (não aplicar o g de inflação) é HIGH e travada no CONTEXT. A
escolha exata (`None` vs `PIB_real`) deve ser **medida** sobre TAEE11/EGIE3/regulada na regressão dos
104 — mas o carve-out é declarado **ANTES** do hold-out (Fase 14), como exige o roadmap (§"NÃO criar
carve-out novo depois de ver um ticker falhar"). [CITED: REQUIREMENTS ENG-04, memória
rim-terminal-value-root-cause]

---

## Contrato de saída (ENG-05/06/07/08/09 — o app "quase certo, não trocar")

### Tríade migra do DDM para o V do RIM (D-09)

Hoje (`selo.py:88` `faixa_do_veredito`): a faixa Barato/Justo/Caro lê o **prefixo do veredito**, e o
veredito é montado em `report.py:639-663` comparando `preco_atual` vs a banda `vmin/vmax` — que hoje é
a **matriz de sensibilidade do DDM** (`report.py:577-585`) e, para não-DDM, a **banda do ensemble**
(`report.py:600-611`).

**Pós-fase:** a banda `vmin/vmax` passa a ser a **região de valor do RIM**: `[V×(1−MS), V×(1+MS)]` onde
`V = intrinseco_motor` (o RIM único). A árvore de veredito (`report.py:639-663`) **já tem a forma
certa** (SUBAVALIADA / NO INTERVALO / SOBREAVALIADA por comparação preço×banda) — só muda **de onde
vem a banda**. `selo.faixa_do_veredito` **permanece intocado** (já casa os 3 prefixos). As flags de
risco (payout>100%, DY>15%, div em prejuízo → VERIFICAR) devem **sobreviver** (`report.py:645-657`) —
elas são do livro (Cap. 6), não do ensemble.

### Margem de segurança (ENG-06 — controle do usuário)

`veredito.margem_seguranca` **já existe** (`config.yaml:118`, default 0.15) e está **declarada no
`user_control` do lock** (`calibracao.lock.yaml:104-119`) com a anotação literal *"ENG-06 (Fase 13) —
vira controle do usuário"*. Esta fase **realiza** essa promessa:
- Default de config **simétrico 5-10%** (o livro: *"se 5%, 10% ou qualquer outro valor, é você quem
  decide"*, Cap. 17). Recomendação: default `0.05` ou `0.10` (o livro usa ±5% no caso ITUB4). **Mudar
  o default de 0.15 → 0.05/0.10 é um co-change config+lock sancionado** (o valor mora no `user_control`).
- **Widget na UI** (D-08): `st.slider`/`st.number_input` de MS, alimentando a região de valor.
- **NUNCA calibrada** contra dispersão/preço/compra (Armadilha 4). O lock já tem o texto-guarda
  ("uma margem calibrada para produzir mais compras é alavanca de marketing").
- A região é **simétrica**: `[V×(1−MS), V×(1+MS)]`. Hoje o fallback do ensemble já usa
  `intrinseco_motor × (1 ± margem)` (`report.py:608-610`) — a forma simétrica já está no código, só
  precisa virar o caminho **primário e único** (não fallback).

### Ponte P/B auditável (ENG-08) — a identidade já existe como função pura testada

A identidade fechada **já vive no repo** como função pura, no teste algébrico do BLIND-02a
(`tests/test_invariantes_v24.py:96`):
```python
def pb_justo(roe: float, ke: float, g: float) -> float:
    return 1.0 + (roe - ke) / (ke - g)     # P/B justo steady-state (Gordon-RIM)
```
Esta é a representação **steady-state** (perpetuidade) do RIM. Os insumos da ponte são os
**terminais**: `ROE_T = _roe_through_cycle(c, rim_cfg)`, `Ke = a.ke`, `g = g_T` (o g terminal por
empresa). A ponte a **exibir**:
```
P/B justo = 1 + (ROE_T − Ke)/(Ke − g)
V (ponte) = P/B justo × VPA
payout_T  = 1 − g/ROE_T        # payout terminal implícito
```

**Nuance crítica que o planner DEVE acertar (senão o teste de correção fica errado):** o
`motores.rim` é **multiestágio** (janela explícita de RI + terminal de Gordon), então
`P/B justo × VPA` **NÃO é igual** ao `V` da engine (`intrinseco_motor`) — a ponte é a decomposição
**steady-state/terminal**, uma **lente auditável**, não uma re-derivação do V multiestágio. Portanto:
- **A ponte é EXIBIÇÃO + sanidade da RAZÃO**, não uma asserção `P/B×VPA == intrinseco_motor`.
- O **teste de correção (D-10a)** é sobre a **razão implícita**: `payout_T ∈ (0, 1)` (i.e. não
  negativo, não > 100%) **E** `P/B justo ∈ (0, 6)`. Fora disso = **bug** (o terminal g excede ROE_T,
  ou o spread é patológico) → o teste **FALHA**.

Confiança HIGH na álgebra (função já testada); MEDIUM na decisão de *qual* ROE/g exibir na ponte —
recomendo os **terminais** (ROE_T, g_T) por coerência com o valor terminal do RIM. Registre como
[ASSUMED] se o planner quiser confirmar com o usuário.

### Guarda-corpo em dois níveis (ENG-09 / D-10)

| Nível | Onde | Comportamento | Caso |
|-------|------|---------------|------|
| **Correção (teste)** | `tests/` (novo) | `payout_T` negativo/>100% OU `P/B justo` fora de `(0,6)` → **assert FALHA** (é bug do modelo, não resultado). | O modelo produzindo uma razão impossível. |
| **Runtime (never-raise)** | `report.py` (borda do veredito) | Fora da faixa → **degrada** (suprime veredito / prefixo VERIFICAR), **NÃO levanta**. Preserva SAN-06. | CGRA4 a 921× é **sinalizado**, não quebra a UI. |

**Ponto sutil sobre o CGRA4 (não confundir):** o CGRA4 a 921× é um **bug de DADO** (`VPA =
PL/num_acoes` inflado — a escala de num_acoes), **não** um bug de razão. O P/B justo implícito do
CGRA4 é ~1,4× (perfeitamente sano) — o guard `0<P/B<6` **não o pega**, e não deveria: o modelo está
internamente consistente; o `V = 1,4 × VPA_inflado` é que é absurdo. Quem sinaliza o CGRA4 é: (1) o
SAN-01 (Fase 8) já rebaixando a confiança do ticker (`num_acoes×preço ≠ market_cap`); (2) o runtime
never-raise degradando o veredito quando `V` é absurdo vs preço (a sanidade `V < ~50× preço` já
provada na KE-04, `test_regressao_104_sem_explosao`). **O guard P/B (D-10) é ortogonal ao CGRA4** — ele
pega **patologias de MODELO** (P/B>6, payout_T fora de faixa), não bugs de escala de dado. Documente
isso no plano para o executor não tentar "fazer o P/B guard pegar o CGRA4" (não é o trabalho dele).

---

## Remoção do ensemble (ENG-02 / D-04) — inventário dos sites

**Deletar (não portar):**

| Alvo | Site | Nota |
|------|------|------|
| `_guarda_faixa_ddm` | `report.py:77-105` + chamada `:589` | Guarda de faixa DDM negativa/degenerada. |
| `_guarda_san01` | `report.py:108-182` + chamada `:706` | Reetiqueta "evitar" anti-aberração; config `veredito.san01` (`config.yaml:126-129`) sai junto. |
| Campos de ensemble em `AnaliseAcao` | `report.py:65-74` | `contraponto_valor`, `banda_do_motor`, `divergencia_ativa/razao/hipotese`, `arquetipo_incerto`, `candidatos_intrinsecos`, `veredito_range`, `motor_pendente`. |
| Bloco ensemble motor×contraponto | `report.py:591-629` | A banda vira a região da MS (D-07), não min/max motor×DDM. |
| `_veredito_fronteirico` (VER-02) | `report.py:329-395` + chamada `:697` | Roda um motor por candidato — morre com o dispatch único. |
| `_hipotese_divergencia` + `_HIPOTESE_DIVERGENCIA` | `report.py:855-890` | Copy de divergência. |
| 2ª lente ensemble×DDM + divergência (CLI) | `cli.py:203-243` | `ensemble_mid`, `divergencia_entre_lentes`, avisos de divergência. |
| Bloco de divergência (app) | `app.py:~945-980` (expander divergência/incerto) | Ver grep: `divergencia`, `candidatos_intrinsecos`. |
| Render de divergência/incerto (markdown) | `report.py:1071-1103` | Blocos "Classificação incerta" e "Bandeira de divergência". |

**`comparables.divergencia_entre_lentes`** (`comparables.py:87-107`): usado só pelo ensemble/CLI —
morre com eles (mas confirmar que nada mais o importa antes de deletar a função).

**Testes que morrem/mudam** (precisam de tratamento na `classificacao.yaml` no MESMO diff — ver
§"Classificação de testes + hook"):
- `test_ranking_freio.py::test_divergencia_*` (5 testes de `divergencia_entre_lentes`) — deletar se a
  função morre.
- `test_arquetipo_roteamento.py::test_fronteirico_*`, `test_render_fronteirico_*` (VER-02) — deletar.
- `test_guardrails_ddm.py::*` (5 testes de `_guarda_faixa_ddm`) — deletar.
- `test_guardrails_ddm.py::test_san01_reetiqueta_aberracao_itub4_like` (**golden_nivel** quarentenado,
  "-> Fase 10/13") — **DELETAR** (não atualizar).
- `test_arquetipo_roteamento.py::test_financeira_rim_destrava_vs_ddm_e_alimenta_veredito`
  (**golden_nivel**, "razao RIM/DDM > 1,3 via engine -> Fase 10/13") — **DELETAR** (o ensemble RIM/DDM
  morre; é o golden de nível que esta fase apaga).

---

## Corte contado de knobs (ENG-10 / D-12) — o número exato

**Medido no `config.yaml:245-277`** — o bloco `motores:` tem **7 folhas** (não ~20; o roadmap diz
"~20", o lock mede 7 hoje):
```
motores.rim.n_fade                    ← GRAU DE LIBERDADE (n_fade) — NÃO pode sair
motores.rim.excesso_sustentavel       ← congelado
motores.rim.ke_g_spread_min           ← congelado
motores.rim.roe_terminal_stat         ← congelado
motores.ciclica.anos_media            ← congelado
motores.ciclica.winsor                ← congelado
motores.crescimento.n_anos_explicito  ← congelado
```
(Contagem confirmada pela regra do `folhas_do_escopo`: lista = 1 folha; `motores` = 7. O lock
`calibracao.lock.yaml:34` documenta "motores 7".)

**Alvo ≤5 recomendado** (o planner confirma; a **contagem é o critério de verificação**):
- **MANTER (4 do RIM):** `rim.n_fade` (grau — obrigatório), `rim.excesso_sustentavel`,
  `rim.ke_g_spread_min`, `rim.roe_terminal_stat` — o RIM único depende dos 4.
- **MANTER (1 política de input):** `ciclica.anos_media` — vira a janela de normalização do
  **ROE-âncora da cíclica** (D-02/D-03). Recomendo **movê-la para `motores.rim.anos_ciclica`** (ou
  `motores.anos_media_ciclica`) para que o bloco `motores.ciclica` desapareça inteiro. Fica 5 folhas.
- **DELETAR (2):** `ciclica.winsor` (inerte desde PRIM-02 — a winsorização temporal saiu; a
  `media_ciclo` usa winsor mas o valor 0.10 é decorativo/pode virar constante de módulo se realmente
  necessário) e `crescimento.n_anos_explicito` (o `dcf_crescimento` **morre**; o RIM usa `n_fade`).

**Resultado:** `motores:` **7 → 5** folhas. Se o planner preferir mais agressivo (só os 4 do RIM +
inlinar `anos_ciclica` como constante), 7 → 4 também satisfaz ≤5.

**Reescrita coesa do lock (mesmo commit):**
- `escopo`: comentário de contagem `26 folhas (motores 7 ...)` → `24 folhas (motores 5 ...)` nos 3
  lugares (`calibracao.lock.yaml:34`, header, partição).
- `congelados`: remover `motores.ciclica.winsor` e `motores.crescimento.n_anos_explicito`; renomear
  `motores.ciclica.anos_media` → o novo caminho, se movido.
- `graus_de_liberdade`: **INTOCADO** — ERP, n_fade, PIB_real permanecem. **Orçamento em 3 graus.**
- `test_orcamento_de_knobs_e_exatamente_3` (partição `folhas == graus | congelados`) e
  `test_knobs_batem_com_o_lock` **refletem no mesmo diff** (é uma verificação de partição, não só de
  contagem — nenhuma folha órfã dos dois lados).

**Confiança:** HIGH na contagem (medida). MEDIUM em *quais* 5 exatas (recomendação fundamentada; a
única obrigação dura é `n_fade` sobreviver e a contagem ficar ≤5).

---

## Rebaixamento do Ranking (ENG-11 / D-11) — colunas exatas

**Por que (memória `ranking-e-cego-ao-preco`):** a regressão de pares (`comparables.preco_alvo_por_
regressao`) é **matematicamente cega ao nível de preço** — multiplicar o preço de todas as elétricas
por 1,5 dá upsides bit-a-bit idênticos. Ela não pode dizer que o setor está caro/barato em nível
absoluto; serve como **comparativo relativo** (Cap. 11-12), não como preço-alvo.

**SAI do Ranking** (imputam nível de preço):
- Coluna **Preço-alvo** (`app.py:1638` / `cli.py:228`) ← `preco_alvo_por_regressao(...).preco_alvo`
- Coluna **Upside** (`app.py:1639` / `cli.py:229`) ← `.upside`
- Coluna **Veredito** ("Subavaliada"/"Cara") (`app.py:1640,1627`)
- O `freio.alvo_regressao_confiavel` (`freio.py:32-60`) — governa só a coluna de alvo/upside; **morre
  junto** com as colunas que ele governa. `freio.motor_pendente` (`freio.py:18-29`) também morre (era
  a suspensão do preço-alvo por arquétipo).

**FICA no Ranking** (múltiplos crus comparáveis e ordenáveis):
- **Nota (0-100)** — `comparables.ranking_por_multiplos` (permanece; é a padronização do Cap. 11).
- **P/L, P/VP, DY, BSD** — múltiplos crus. Nota: o app hoje **já** monta P/L/P/VP/DY no comparador de
  pares (`app.py:1166-1178`); reusar essa apresentação. O **Selo** (cor BSD) já está no Ranking
  (`app.py:1635`) — permanece.
- A **regressão** em si (`ajustar_regressao_pl`) pode permanecer computada como **contexto informativo**
  (o caption "R²/n" — `app.py:1664-1668`, `cli.py:246-250`) OU sair. Recomendo: **manter a linha de
  contexto da regressão** (educativa, Cap. 12) mas **sem** derivar preço-alvo/upside/veredito dela. O
  planner decide; o essencial é que **nenhuma coluna imputa nível de preço**.

**`comparables.preco_alvo_por_regressao` + `PrecoAlvo`** (`comparables.py:169-216`): saem do **caminho
do Ranking**, mas a função pode permanecer no módulo (é testada por `test_comparables.py::
test_preco_alvo_cteep` como **invariante** — a conferência CTEEP do livro Cap. 12). **Não deletar a
função** (quebraria a conferência do livro); só **desconectá-la da view do Ranking**. Confirmar se
algum outro consumidor sobrevive.

**Testes afetados:** `test_ranking_freio.py::test_freio_*` (freio) e `::test_motor_pendente_*` — se
`freio.py` morre, deletar; `test_ranking_freio.py::test_divergencia_*` já listados acima.

---

## UI mínima Streamlit (D-08) — escopo estritamente mínimo

`app.py` (2090 linhas) — as **únicas** mudanças de exibição desta fase (reforma pesada é deferida):

1. **Widget de MS** (aba Analisar, perto do veredito ~`app.py:918-1041`): `st.slider("Margem de
   segurança", 0.0, 0.20, default, step=0.01)` alimentando a região de valor. A região `vmin/vmax`
   já é exibida na manchete (`app.py:1009,1054`).
2. **Tríade** já exibida (`app.py:918-927`: SUBAVALIADA/verde etc.) — só passa a vir da região do RIM
   (mudança de engine, não de UI).
3. **Matriz Ke×g** já exibida (`app.py:1430-1436`, "Sensibilidade do valor (linhas=Ke, colunas=g)") —
   já está sobre `a.ke`/`g` (Fase 12). **Reusar, não reinventar** (ENG-07). Confirmar que o header usa
   `a.ke` correto.
4. **Ponte P/B auditável** (NOVO): um bloco pequeno exibindo `P/B justo`, `V = P/B×VPA`, `payout_T`.
   Mínimo — 3 linhas de `st.metric`/`st.caption`.
5. **Remover "Evitar"** (`selo.py:_MATRIZ[("Baixa","Caro")] = "Evitar"` — `selo.py:54`) e o **eixo
   "Qualidade Baixa"** (`selo._qualidade`, `selo.py:79-85`: amarelo/vermelho → "Baixa"). Ambos nunca
   vieram do livro. Isto afeta `selo.py` + os testes de badge (`test_presentation_multiticker.py`,
   `test_comparador.py`). Cuidado: `_MATRIZ` tem 3 células "Baixa" (`VALUE TRAP`, `Fraca`, `Evitar`) —
   o CONTEXT pede remover **"Evitar" e o eixo "Baixa"**; o planner precisa decidir se remove o eixo
   inteiro (colapsa 6 células → 3) ou só a célula "Evitar". Recomendo: remover a linha "Evitar"
   explicitamente e re-rotular o eixo (D-08 diz "remoção de 'Evitar' e 'Qualidade Baixa'"). **Este é
   um ponto que merece confirmação** — ver Open Questions.

**NÃO tocar nesta fase:** as lentes "Preço-Justo (Graham)" e "Preço-Teto (Bazin)" (`app.py:1089-1116`)
são **lentes de contexto clássicas**, NÃO o contrato de saída. O requisito "não inventar contrato novo
à la Bazin" é sobre **não fazer o veredito virar Bazin**, não sobre remover a lente informativa
existente. **Deixar como está** (fora de escopo). Ver Open Questions.

---

## Fronteira dura com a Fase 14 (NÃO validar o caso do livro aqui)

**Isto é uma restrição de escopo, não uma sugestão.** Esta fase entrega o **motor**. O número
soberano do marco — **ITUB4 = R$ 37,22** (Cap. 17, `g=10,24%`, `Ke=12,48%`) — só se prova na **Fase
14** (VAL-01/VAL-04), e o hold-out **roda uma única vez**. Qualquer teste/asserção que verifique o
caso do livro **NESTA fase queima o hold-out** e transforma o marco no v2.3 de novo. Regras concretas
para o planner:
- **NÃO** escrever teste que assevere `ITUB4 ≈ 37,22` (nem 35-39, nem MS ±5% sobre ITUB4).
- **NÃO** calibrar knob/MS/carve-out "até o ITUB4 sair certo" — o hook BLIND-05 + `test_
  nenhuma_justificativa_de_knob_menciona_ticker` já barram justificativa com ticker, mas a disciplina
  é anterior ao hook.
- O que **é** permitido: a **regressão dos 104** como oráculo de "nada explode / razões sãs" (por
  distribuição, sem nomear ticker) — é o padrão herdado (GROW-04/05, KE-04), ver abaixo.

---

## Validation Architecture (prova por EXECUÇÃO da regressão dos 104 — não o caso do livro)

> `nyquist_validation: false` no config — a seção de test-map nyquist é omitida. Esta seção é o
> **oráculo de correção herdado** (GROW-04/05, KE-04/D-11), pedido explicitamente no objetivo: provar
> o guard P/B e o corte de knobs **por execução**, não por "suíte verde" (memória
> `guardrails-devem-ser-provados-por-execucao`).

**O oráculo:** `report.analisar_acao` sobre os **104 REAIS** (`hs.CAMINHO_SNAPSHOT_LIMPO`), com o β
setorial carimbado (`macro.carimbar_beta_setorial`, Ke offline idêntico ao app). É exatamente o
padrão de `tests/test_ke_validacao.py::test_regressao_104_sem_explosao` (KE-04), que já roda hoje.

**O que a regressão pós-colapso deve assegurar (invariante, BLIND-04a-safe — SEM nomear ticker):**
1. Todo ticker com dado suficiente resolve `intrinseco_motor` **finito e > 0** (ou `None`
   never-raise); nenhum NaN/inf/exceção.
2. **Nenhuma explosão:** `V < ~50× preço` (o teto de sanidade medido na KE-04, max real 4,7×) — sem
   nomear ticker, por distribuição.
3. **Razão P/B sã por construção:** para cada ticker, `payout_T ∈ (0,1)` e `P/B justo ∈ (0,6)` — este
   é o **guard D-10a provado por execução** sobre a cesta real, não sobre um caso.
4. **Um só caminho:** nenhum ticker roteia para `ddm`/`seguradora`/`normalizado`/`dcf`/`nav` como
   **motor primário** — todos passam pelo RIM único (o rótulo `a.motor` deve ser sempre o RIM, ou uma
   política de âncora, nunca um dos ex-motores).
5. **Cross-menu (WR-03):** `analyze` e `rank` produzem o mesmo `intrinseco_motor`/`a.ke`/matriz para a
   mesma ação (`test_cli_rank_consistencia.py` deve continuar verde; adaptar ao novo caminho).

**Framework:** pytest (config em `pyproject.toml`; `addopts = -m 'not golden_nivel' --strict-markers`,
`xfail_strict = true`).
- **Suíte default:** `.venv/bin/python -m pytest` (goldens de nível em quarentena; `-m ""` roda tudo;
  `-m golden_nivel` roda os quarentenados).
- **`pytest tests/arquivo.py` NÃO funciona** (dispara CLASSIFICACAO ORFA) — usar `-k`.
- **Suíte-alvo pós-fase:** `0 failed`, goldens de nível relevantes **DELETADOS** (não atualizados),
  o skip do jackknife permanece (Fase 14), `xfail_estritos() == 0` (as duas doenças já curadas nas
  Fases 10/12).

**Classificação dos testes novos:** todo teste novo (ponte P/B, guard, contrato de saída, âncora)
precisa de entrada em `tests/classificacao.yaml` **na coleta** — teste sem entrada **quebra a
coleta**. Classificar corretamente: identidade P/B / razão-sã = **invariante**; formato do contrato /
tríade / never-raise = **contrato**; **nunca** criar `golden_nivel` novo (é o reflexo do overfit).

---

## Classificação de testes + hook BLIND-05 (sequenciamento de commits — CRÍTICO)

**Descoberta que muda o plano de waves** (medido no `.githooks/commit-msg`): o hook BLIND-05 bloqueia
`config.yaml` **+** qualquer um de `tests/(fixtures/|test_|classificacao.yaml|conftest.py|
helpers_blindagem.py)` no **mesmo commit** — **`tests/classificacao.yaml` ESTÁ na lista casada**.
Como `calibracao.lock.yaml` vive na **raiz** (não em `tests/`), `config.yaml` + `lock` juntos **não**
disparam o hook (é o caminho sancionado).

**Consequência para a ordem dos commits:**
- **Commit de knob-cut (ENG-10):** `config.yaml` (motores trimado) + `calibracao.lock.yaml` (partição
  + contagem) — **e NADA de `tests/`**. Passa o hook sem trailer (config+lock não casa a 2ª regex).
  Convenção do projeto (12-03): carregar um trailer `Knob-Change-Justification:` de razão econômica
  **sem ticker** mesmo assim, para a disciplina do diff revisável.
- **Commits de teste** (deletar goldens, adicionar contrato/invariante + linhas na
  `classificacao.yaml`): **separados** do commit que toca `config.yaml`. Se, por necessidade, um
  commit precisar tocar `config.yaml` + `classificacao.yaml` juntos, **exige** o trailer
  `Knob-Change-Justification:` (sem ticker) — mas prefira separar.
- **Golden deletado = função + linha da `classificacao.yaml` no MESMO diff** (Pitfall 5, zero órfão) —
  isso **não** toca `config.yaml`, então não dispara o hook.

**`core.hooksPath` é estado local por clone** — o executor precisa de `git config core.hooksPath
.githooks` (o `test_hook_do_blind05_esta_instalado` deixa vermelho se ausente).

---

## Don't Hand-Roll

| Problema | Não construir | Usar/reusar | Por quê |
|----------|---------------|-------------|---------|
| Fórmula de valor | Um "novo RIM" | `motores.rim` (`motores.py:66`) | Já é RIM híbrido multiestágio, never-raise, com terminal normalizado e anti-bad-bank. A ponte P/B é derivável dele. |
| Custo de capital | Recomputar Ke | `a.ke` (Fase 12) | Ke único setorial+Blume já carimbado; recomputar reintroduz drift. |
| Crescimento terminal | Redigitar g | `g_cap`/`g_T` derivados (Fase 11) | `g_cap` derivado na engine, `g_T` fechado por empresa. Tocar apaga o diagnóstico. |
| Identidade P/B | Reimplementar | `pb_justo` de `test_invariantes_v24.py:96` | Já é função pura testada (BLIND-02a). Extrair para `core/` se precisar reuso. |
| Matriz Ke×g | Nova matriz | `ddm.matriz_sensibilidade` (`report.py:551`) | Herdada da Fase 12, em torno de `a.ke`. ENG-07 reusa. |
| Comparativo por múltiplos | Novo screener | `comparables.ranking_por_multiplos` | Cap. 11 já implementado; só remover as colunas de nível de preço. |
| Classificação de arquétipo | Novo classificador | `arquetipo.classificar` (`:124`) | Sobrevive intocado no corpo; só o registry e 2 linhas de split mudam. |
| Contrato de saída | Novo veredito | Árvore `report.py:639-663` + `selo.faixa_do_veredito` | Já tem a forma SUB/NO INTERVALO/SOBRE certa; só muda a fonte da banda. |

**Key insight:** esta fase é **subtração**, não adição. Quase tudo que ENG-01..09 precisam **já
existe** — o trabalho é **remover** os 3 caminhos redundantes, o ensemble e as guardas-cicatriz, e
**religar** a banda do veredito à região da MS sobre o RIM único.

---

## Common Pitfalls

### Pitfall 1: "Consertar" o dcf_crescimento com FCFE
**O que dá errado:** trocar `lpa` por `lpa × payout` no DCF o torna DDM por teorema (WEGE3 0,58→0,26).
**Como evitar:** o `dcf_crescimento` **morre**. Crescimento vira `roe0 = atual + fade` no RIM único.

### Pitfall 2: Aplicar o g de inflação às transmissoras
**O que dá errado:** double-count de IPCA (o book já é o VP da RAP). ROE dispara em ano de IPCA alto.
**Como evitar:** carve-out `CONCESSAO_FINITA` com `g_terminal = None` (fade-only, nativo no `motores.rim`).

### Pitfall 3: Calibrar a MS até os resultados ficarem bonitos
**O que dá errado:** Armadilha 4 (post-mortem v2.3 num endereço novo). A MS multiplica o V.
**Como evitar:** MS = controle do usuário, default simétrico de config; declarada no `user_control`.

### Pitfall 4: Editar `config.yaml` + `tests/classificacao.yaml` no mesmo commit sem trailer
**O que dá errado:** o hook BLIND-05 bloqueia o commit (assinatura de "calibrei o knob até passar").
**Como evitar:** separar o commit de knob (config+lock) dos commits de teste. Ou trailer sem ticker.

### Pitfall 5: Atualizar um golden de nível em vez de deletar
**O que dá errado:** mantém vivo o reflexo do overfit (Regra dura B; CLAUDE.md).
**Como evitar:** golden de nível que quebra (ex.: `test_financeira_rim_destrava`, `test_san01_
reetiqueta_aberracao_itub4_like`) é **DELETADO** — função + linha da `classificacao.yaml` no mesmo diff.

### Pitfall 6: Fazer o guard P/B (0<P/B<6) "pegar" o CGRA4 a 921×
**O que dá errado:** o CGRA4 é bug de DADO (VPA inflado), P/B implícito é ~1,4 (sano). Tentar pegá-lo
com o guard de razão corrompe o guard.
**Como evitar:** o guard P/B pega **patologias de modelo**; o CGRA4 é sinalizado por SAN-01 (confiança)
+ runtime never-raise (V vs preço). Ortogonais.

### Pitfall 7: Validar o caso do livro (ITUB4=37,22) nesta fase
**O que dá errado:** queima o hold-out da Fase 14; o marco vira o v2.3.
**Como evitar:** prova só por **distribuição** dos 104 (sem nomear ticker). O número final é a Fase 14.

### Pitfall 8: Deixar a MS como fallback em vez de caminho primário
**O que dá errado:** hoje `intrinseco_motor × (1±margem)` é só o *fallback* do ensemble
(`report.py:608`). Se ficar como fallback, a região de valor não é a do livro.
**Como evitar:** a região `[V×(1−MS), V×(1+MS)]` vira o **caminho primário e único** do veredito.

---

## Code Examples (padrões verificados no próprio repo)

### RIM único alimentado pela política do arquétipo (forma-alvo do dispatch)
```python
# report.py — _intrinseco_por_motor colapsado (esboço; o planner detalha)
# Fonte: motores.py:66 (rim), report.py:255-268 (ramo rim atual), arquetipo.py:167 (roe endpoint)
def _valor_rim(c, a, cfg):
    ult = c.ultimo_ano()
    rim_cfg = cfg["motores"]["rim"]
    g_cap = (1 + cfg["macro"]["pi_ciclo"]) * (1 + cfg["ddm"]["pib_real"]) - 1
    vpa0 = lentes.vpa(c.patrimonio_liquido.get(ult), c.num_acoes.get(ult))
    politica = arquetipo.ARQUETIPO_ANCORA_ROE[a.arquetipo]
    roe0, roe_term, g_term = _derivar_insumo(politica, c, cfg, g_cap, rim_cfg)  # ver mapa de âncoras
    res = motores.rim(
        vpa0=vpa0, roe0=roe0, ke=a.ke,                     # a.ke pronto (Fase 12)
        retencao=(1.0 - (c.payout_valuation() or 0.0)),
        n=rim_cfg["n_fade"],
        excesso_sustentavel=rim_cfg["excesso_sustentavel"],
        g_terminal=g_term,                                 # None p/ CONCESSAO_FINITA (carve-out)
        ke_g_spread_min=rim_cfg["ke_g_spread_min"],
        roe_terminal=roe_term,
    )
    return res.valor_intrinseco if res else None
```

### Ponte P/B auditável + teste de correção (razão, não nível)
```python
# core/valuation.py (novo helper puro) — Fonte: test_invariantes_v24.py:96
def pb_justo(roe_t, ke, g):
    return 1.0 + (roe_t - ke) / (ke - g)      # None-guard: ke - g > 0 (já garantido por Ke_min>g_cap)

def payout_terminal(roe_t, g):
    return 1.0 - g / roe_t                     # payout_T implícito

# teste (invariante): payout_T ∈ (0,1) e pb ∈ (0,6) — fora = BUG do modelo
assert 0.0 < payout_terminal(roe_t, g) < 1.0
assert 0.0 < pb_justo(roe_t, ke, g) < 6.0
```

### Região de valor simétrica (caminho primário)
```python
# report.py — a banda vira a região da MS sobre o RIM único (D-07/D-09)
# Fonte: report.py:608-610 (hoje fallback; vira primário)
ms = cfg["veredito"]["margem_seguranca"]        # controle do usuário, simétrico
a.vmin = a.intrinseco_motor * (1.0 - ms)
a.vmax = a.intrinseco_motor * (1.0 + ms)
# tríade: report.py:639-663 (forma já certa) — só a fonte da banda mudou
```

---

## State of the Art

| Antigo (v2.2/v2.3) | Novo (v2.4 Fase 13) | Impacto |
|--------------------|---------------------|---------|
| 4 motores + ensemble + divergência | 1 RIM + política de âncora | Erro ilimitado (escolha de modelo) → erro limitado (escolha de âncora) |
| Tríade do prefixo do veredito DDM | Tríade de V vs `[V×(1−MS), V×(1+MS)]` | Contrato do livro literal (Cap. 17) |
| MS embutida (0.15) como fallback | MS = controle do usuário, simétrica | Armadilha 4 morre por construção |
| Ranking com preço-alvo/upside/veredito | Screener por múltiplos crus | Regressão de pares deixa de fingir nível de preço |
| `pagadora_regulada` → DDM; default idem | `PAGADORA_MADURA` (RIM) + `CONCESSAO_FINITA` (carve-out) | Empresa sem sinal deixa de cair no balde da transmissora |
| `motores:` 7 folhas | ≤5 folhas contadas | Superfície de knob menor; orçamento em 3 graus |

**Deprecado/removido nesta fase:** `_guarda_san01`, `_guarda_faixa_ddm`, ensemble motor×contraponto,
`_veredito_fronteirico` (VER-02), `_hipotese_divergencia`, `dcf_crescimento` (motor), rota
`seguradora` como motor primário, colunas de preço-alvo/upside/veredito do Ranking, `freio.py`
(`motor_pendente`/`alvo_regressao_confiavel`), rótulo "Evitar", eixo "Qualidade Baixa".

---

## Security Domain

Projeto de **computação numérica pura** (engine offline + Streamlit local/VPS). Sem auth, sem PII,
sem SQL, sem rede na engine. As categorias ASVS são majoritariamente **N/A** para esta fase de
refatoração interna.

| ASVS | Aplica | Controle |
|------|--------|----------|
| V5 Input Validation | parcial | Tickers de entrada já validados nas bordas (`lentes.normalizar_tickers`); never-raise (SAN-06) degrada em vez de levantar. Esta fase não adiciona entrada nova não confiável. |
| V6 Cryptography | não | N/A |
| V2/V3/V4 Auth/Session/Access | não | N/A (o app tem login por email fora do escopo desta fase) |

Nota honesta: o único vetor relevante do projeto é **integridade de dado financeiro** (não segurança
de aplicação) — coberto pelos asserts SAN (Fase 8) e pela disciplina de knob (BLIND). Nada novo aqui.

---

## Assumptions Log

| # | Claim | Seção | Risco se errado |
|---|-------|-------|-----------------|
| A1 | A ponte P/B exibida usa os TERMINAIS (`ROE_T = _roe_through_cycle`, `g = g_T`), não `roe0`/`g_alto` | Ponte P/B | Baixo — coerente com o valor terminal do RIM; mas se o usuário quiser a razão da fase explícita, muda a exibição. Confirmar. |
| A2 | Carve-out CONCESSAO_FINITA = `g_terminal=None` (fade-only) é preferível a pinar em PIB_real | Carve-out | Médio — a escolha exata deve ser MEDIDA na regressão dos 104 (TAEE11/EGIE3); a direção (não IPCA) é travada |
| A3 | ≤5 knobs = `rim.{n_fade, excesso_sustentavel, ke_g_spread_min, roe_terminal_stat}` + `anos_ciclica` | Corte de knobs | Baixo — a única obrigação dura é `n_fade` sobreviver + contagem ≤5; o set exato é do planner |
| A4 | Remover "Qualidade Baixa" = re-rotular o eixo, mantendo VALUE TRAP/Fraca (só "Evitar" some) OU colapsar o eixo | UI mínima | Médio — o CONTEXT diz "remoção de Evitar E Qualidade Baixa"; ambiguidade real, precisa confirmação (ver OQ) |
| A5 | As lentes Graham/Bazin (`app.py:1089-1116`) ficam intocadas (contexto, não contrato) | UI mínima | Baixo — o requisito é sobre não INVENTAR contrato Bazin, não remover a lente informativa; mas confirmar |
| A6 | TAEE11/regulada sob RIM único (em vez de DDM) não explode nem subvaloriza grosseiramente | Mapa de âncoras | Médio — hoje regulada roteia p/ DDM; sob RIM o número muda. DEVE ser medido antes do plano final |
| A7 | Clean surplus (Ohlson 1995) ⇒ RIM ≡ DDM ≡ DCF-equity | Summary | Baixo — teoria estabelecida; SAN-05 já mede clean surplus como pré-condição do RIM |

---

## Open Questions

1. **Rótulo do eixo "Qualidade" após remover "Baixa" (A4)**
   - Sabemos: "Evitar" (`selo.py:54`) e "Qualidade Baixa" saem (D-08); nunca vieram do livro.
   - Não está claro: remover só a célula `("Baixa","Caro")="Evitar"` e re-rotular o eixo, OU colapsar
     o eixo Baixa inteiro (as 6 células do `_MATRIZ` viram 3)? Afeta `VALUE TRAP` e `Fraca`.
   - Recomendação: **remover "Evitar" e renomear o rótulo "Baixa" → algo descritivo neutro** (ex.:
     "Atenção") mantendo VALUE TRAP/Fraca — mudança mínima. Confirmar com o usuário no discuss/plan.

2. **Lentes Graham/Bazin no Analisar (A5)**
   - Sabemos: "Bazin"/"preço-teto" têm 0 ocorrências no livro; o requisito veta INVENTAR contrato Bazin.
   - Não está claro: a lente informativa "Preço-Teto (Bazin)" existente (`app.py:1104-1116`) deve
     sair? Ela é **contexto**, não o veredito.
   - Recomendação: **deixar** (fora de escopo desta fase; reforma de UI é deferida). Se o usuário
     quiser removê-la por fidelidade, é um item separado.

3. **Regressão dos 104 sob RIM único — comportamento de regulada/cíclica (A6)**
   - Sabemos: hoje regulada→DDM, cíclica→lucro_normalizado (Gordon-P/L). Sob RIM único, ambos mudam.
   - Não está claro: TAEE11/EGIE3/CSNA3 ficam sãos sob RIM? (Hoje TAEE11 é validada pela banda DDM.)
   - Recomendação: **rodar a regressão dos 104 como Wave 0 de medição** antes de fechar o mapa de
     âncoras — é o oráculo herdado (KE-04). Sem nomear ticker nos asserts (por distribuição).

---

## Environment Availability

Fase de código/config puro sobre o repositório — sem dependência externa nova.

| Dependência | Requerida por | Disponível | Versão | Fallback |
|-------------|---------------|------------|--------|----------|
| Python 3 + pytest | Toda a fase | ✓ (repo já roda) | `.venv` do projeto | — |
| numpy/scipy/pandas/tabulate | motores/comparables/report | ✓ (já em uso) | já instaladas | — |
| Snapshot limpo dos 104 (`hs.CAMINHO_SNAPSHOT_LIMPO`) | Regressão-oráculo | ✓ (DATA-06) | fixture versionada | — |
| Rede (BCB/Yahoo) | **NÃO** requerida | — | engine offline | a engine lê cfg carimbado; testes são offline |

Nenhuma dependência faltante. Nenhum bloqueio de ambiente.

---

## Sources

### Primary (HIGH confidence — leitura direta do código do repo, 2026-07-19)
- `src/analista/core/motores.py` — `rim` (:66), `lucro_normalizado` (:149), `dcf_crescimento` (:161), `nav_contabil` (:195)
- `src/analista/core/arquetipo.py` — `ARQUETIPO_MOTOR` (:48), `classificar` (:124), split sites (:159, :180)
- `src/analista/report/report.py` — `_guarda_faixa_ddm` (:77), `_guarda_san01` (:108), `_roe_through_cycle` (:184), `_intrinseco_por_motor` (:201), `_veredito_fronteirico` (:329), veredito (:639), matriz (:551)
- `src/analista/report/selo.py` — `_MATRIZ` (:48), `_qualidade` (:79), `faixa_do_veredito` (:88)
- `src/analista/core/comparables.py` — `preco_alvo_por_regressao` (:181), `PrecoAlvo` (:169), `divergencia_entre_lentes` (:87)
- `src/analista/core/freio.py` — `motor_pendente` (:18), `alvo_regressao_confiavel` (:32)
- `src/analista/cli.py` — `cmd_rank` (:168), 2ª lente ensemble×DDM (:203-243)
- `app.py` — Analisar (:900-1116), matriz (:1430), Ranking (:1554-1668)
- `config.yaml` — bloco `motores:` (:245-277), `veredito.margem_seguranca` (:118)
- `calibracao.lock.yaml` — escopo/graus/congelados/user_control (contagem "motores 7")
- `.githooks/commit-msg` — regex de co-change (casa `tests/classificacao.yaml`)
- `tests/test_invariantes_v24.py` — `pb_justo` (:96), BLIND-02a/b
- `tests/test_blindagem_orcamento.py` — `test_orcamento_de_knobs_e_exatamente_3` (:44), `test_knobs_batem_com_o_lock` (:119)
- `tests/classificacao.yaml` — inventário dos golden_nivel quarentenados
- `pyproject.toml` — addopts/markers/xfail_strict
- `.planning/config.json` — `nyquist_validation: false`, `ui_phase: true`

### Secondary (CITED — decisões e método)
- `.planning/phases/13-motores-contrato-de-sa-da-eng/13-CONTEXT.md` — D-01..D-12
- `.planning/REQUIREMENTS.md` — ENG-01..11, critério soberano, VAL (Fase 14)
- `.planning/ROADMAP.md` — regras duras A/B/C, §Phase 13/14
- `.planning/STATE.md` — estado da suíte pós-Fase 12, decisões acumuladas
- `.planning/phases/{11,12}-*/…-CONTEXT.md` — g_cap/g_T e a.ke prontos

### Tertiary (ASSUMED — conhecimento de método)
- Ohlson (1995) clean surplus ⇒ RIM ≡ DDM ≡ DCF-equity — teoria estabelecida (CFA L2); SAN-05 mede clean surplus como pré-condição no repo

---

## Metadata

**Confidence breakdown:**
- Sites de código a editar: **HIGH** — todos verificados por leitura direta com números de linha
- Mapa de âncoras por arquétipo: **MEDIUM-HIGH** — a direção é travada (CONTEXT D-03); a mecânica de
  derivação do `roe0` da cíclica é recomendação fundamentada no ramo `normalizado` existente
- Carve-out CONCESSAO_FINITA: **MEDIUM** — direção HIGH (não IPCA), escolha exata a MEDIR nos 104
- Ponte P/B / guard: **HIGH** na álgebra (função testada existe), MEDIUM em quais ROE/g exibir
- Corte de knobs (contagem 7→≤5): **HIGH** — medido no config
- Comportamento de regulada/cíclica sob RIM único: **MEDIUM** — precisa de medição (Wave 0 sugerida)

**Research date:** 2026-07-19
**Valid until:** estável (código do próprio repo; sem dependência externa que envelheça) — revalidar
só se as Fases 11/12 forem retocadas
</content>
</invoke>
