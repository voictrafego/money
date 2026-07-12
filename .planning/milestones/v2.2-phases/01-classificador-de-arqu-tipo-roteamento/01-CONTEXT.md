# Phase 1: Classificador de Arquétipo + Roteamento - Context

**Gathered:** 2026-07-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Erguer a etapa de **classificação/roteamento que hoje não existe** no funil de valuation. A ferramenta passa a decidir o **arquétipo do negócio** (financeira, pagadora regulada, cíclica, crescimento, holding) **antes de valuar**, a partir dos dados que já se puxa (CVM + Yahoo + BCB), e a **escolha do motor deixa de ser fixa (DDM hard-coded)** e passa por um **registry arquétipo→motor**. Nesta fase só o DDM já está plugado (para pagadora regulada); os demais motores (RIM/normalizado/DCF/SOTP) chegam na Fase 2.

**Requisitos cobertos:** ARQ-01 (classificar antes de valuar), ARQ-02 (fallback honesto), ENG-01 (registry arquétipo→motor), ENG-06 (DDM permanece p/ pagadora regulada).

**Dentro do escopo:** classificador (setor + refino quantitativo), fallback fronteiriço, registry, DDM plugado como motor da regulada, exposição do arquétipo/motor/confiança em `AnaliseAcao`, e a mudança de comportamento "suspende veredito primário quando o motor do arquétipo ainda não existe".
**Fora do escopo (outras fases):** implementar RIM/normalizado/DCF/SOTP (Fase 2); ensemble + bandeira de divergência + guarda-corpos + refatoração do selo (Fase 3); qualquer UI além da exposição mínima do arquétipo.
</domain>

<decisions>
## Implementation Decisions

### Calibração do fallback honesto (ARQ-02)
- **D-01:** Fronteiriço dispara **só em conflito real de sinais** — quando setor e refino quantitativo discordam (ex.: setor diz banco, métricas dizem outra coisa) ou quando as métricas se contradizem entre si. Quando setor + quantitativo concordam, **crava**. Meta explícita: ~85% cravados / ~15% fronteiriços (não ser conservador a ponto de marcar tudo como dúvida, nem agressivo a ponto de nunca duvidar).

### Setor CVM vs. refino quantitativo (ARQ-01)
- **D-02:** Roteamento **híbrido**. Setores de **alta confiança** roteiam direto (hard-route): **banco** (detecção CVM por códigos de conta), **seguradora**, e **regulada** (via `eh_concessionaria`, que já deriva Energia/Saneamento/Água/Gás). Todo o resto passa pelo **refino quantitativo** (ROE/retenção/oscilação de margem/lucro). Racional: `eh_concessionaria` e a detecção de banco na CVM já são confiáveis; o rótulo genérico da CVM **não** é (VULC3 caiu em 'Têxtil'), então fora dos setores fortes o quantitativo decide.

### Taxonomia dos arquétipos (chaves do registry — ENG-01)
- **D-03:** **5 chaves, mapeamento 1:1 com os motores** da Fase 2:
  - `financeira` → **RIM** (banco + seguradora juntos na mesma chave/motor)
  - `pagadora_regulada` (madura) → **DDM** (já plugado nesta fase)
  - `ciclica` → **lucro normalizado** (Fase 2)
  - `crescimento` → **DCF** (Fase 2)
  - `holding` → **NAV/SOTP** (Fase 2)
  - Sem separar banco↔seguradora e sem chave "compounder" distinta de crescimento — mantém o mapa arquétipo↔motor limpo. (Nomes exatos das chaves ficam a critério do planner, desde que 1:1 com os 5 motores.)

### Comportamento na Fase 1 quando o motor do arquétipo ainda não existe
- **D-04:** **Suspende o veredito primário e rebaixa o DDM.** Quando o arquétipo classificado aponta para um motor que ainda não existe (RIM/normalizado/DCF/SOTP na Fase 1), a ferramenta **NÃO roda o DDM como se fosse o motor certo**: exibe "arquétipo X → motor Y (chega na Fase 2)", mostra Graham/Bazin como referência, e **não estampa selo 'evitar'**. Isso já mata metade do bug do ITUB4 na própria Fase 1 (zero aberração silenciosa desde já). A pagadora regulada (TAEE11), cujo motor DDM **existe**, roteia normalmente e mantém números/veredito **idênticos** aos de hoje.

### Claude's Discretion
- Nomes exatos das chaves do registry e assinatura da função classificadora.
- Thresholds numéricos do refino quantitativo (ex.: o que conta como ROE "alto e estável", quanto de oscilação de margem/lucro caracteriza cíclica, quanto de retenção caracteriza compounder) — o planner/researcher deriva a partir dos sinais disponíveis; o brief dá a direção (financeira→RIM, ROE alto+retenção→compounder, margem/lucro oscilando violento→cíclica).
- Forma exata da exposição do resultado (campos novos em `AnaliseAcao`: arquétipo, motor escolhido, confiança/`fronteiriço`, lista de candidatos quando fronteiriço) e a renderização mínima no report/CLI. UX rica fica para a Fase 3.
- Como estruturar o registry (dict módulo-nível, dataclass, etc.).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Brief e requisitos do milestone
- `.planning/BRIEF-motor-arquetipo.md` — brief-fonte: diagnóstico do ITUB4, mapa de código com âncoras `arquivo:linha`, ordem sugerida de fases, critérios de aceite. **Leitura obrigatória.**
- `.planning/REQUIREMENTS.md` — requisitos ARQ-01/ARQ-02/ENG-01/ENG-06 (e o restante do milestone para contexto de sequência).
- `.planning/ROADMAP.md` §"Phase 1" — goal + success criteria da fase.

### Código do funil de valuation (onde o roteamento entra)
- `src/analista/report/report.py` — `analisar_acao()` (funil, `:53`). Ponto de inserção do roteamento: entre o CAPM (`:113`) e a montagem do DDM (`:136`). Estágio de ciclo de vida já calculado em `:109`. Veredito em `:170-207`; `AnaliseAcao` dataclass em `:22`.
- `src/analista/report/selo.py` — agregação do selo (não muda nesta fase, mas o comportamento D-04 de "não estampar evitar" precisa não quebrar o firewall selo↛report; a refatoração real do selo é Fase 3).
- `src/analista/core/fundamentals.py` — `CompanyData` (`:20`): fonte dos sinais do classificador (`setor`, `roe_valuation()`, série `roe(ano)`, `payout_valuation()` + série, `serie_lucro_normalizada()`, `patrimonio_liquido`, `margem_valuation()`, `eh_concessionaria`, `beta`).
- `src/analista/core/lifecycle.py` — `classificar_estagio()`: heurística de 6 estágios (hoje informativa); reaproveitável como sinal do classificador.
- `src/analista/ingest/build.py` — `montar_empresa()` (`:40`); `eh_concessionaria` derivado em `:68` de `setores_concessionaria=(Energia, Saneamento, Água, Gás)`.
- `src/analista/ingest/universe.py` — `resolver()`: (CD_CVM, setor) com override display-only por ticker (`data/ticker_map.json`) sobre o `SETOR_ATIV` da CVM.
- `src/analista/ingest/cvm.py` — detecção de banco (códigos de conta diferentes: PL 2.08 vs 2.03, receita de intermediação) — sinal de alta confiança p/ o hard-route financeiro.

### Testes que travam comportamento (não quebrar sem intenção)
- `tests/test_ddm.py` — golden do livro: DDM Itaú ≈ R$ 37,22 (input FIXO de livro, Ke 12,48%). A Fase 1 não toca `core/ddm.py` → deve continuar verde.
- `tests/test_selo.py` — cortes de cor + rótulos da matriz + **firewall selo↛report**. Preservar.
- `tests/test_consistencia_modos.py` — mesmo número entre Analisar/Garimpo/Ranking (Core Value). O roteamento não pode divergir os 3 modos.
- `tests/test_vulc3_regressao.py` — capstone e2e (veredito começa com "VERIFICAR"); `tests/test_guardrails_fix06.py`.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`eh_concessionaria`** (`build.py:68`, campo em `CompanyData`): já classifica "pagadora regulada" a partir do setor — é praticamente a chave `pagadora_regulada` pronta para o hard-route (D-02).
- **Detecção de banco na CVM** (`cvm.py`): bancos usam códigos de conta diferentes (PL 2.08 vs 2.03) — sinal de alta confiança para a chave `financeira` sem depender do rótulo textual.
- **`lifecycle.classificar_estagio`**: 6 estágios (Startup→Declínio) a partir de g_lucro + payout + lucro positivo/decrescente. Insumo pronto para o refino quantitativo (crescimento vs. maturidade).
- **Métodos canônicos de `CompanyData`**: `roe_valuation()`, `payout_valuation()`, `serie_lucro_normalizada()`, `margem_valuation()` — sinais normalizados já disponíveis; o classificador consome sem recalcular nada (mantém consistência cross-modo).
- **`normalizacao.py`** — base para caracterizar oscilação (cíclica) e, na Fase 2, o lucro normalizado.

### Established Patterns
- **Funil único de valuation** em `analisar_acao()` — o roteamento entra num único ponto (`report.py` entre `:113` e `:136`), não espalhado.
- **Firewall selo↛report** (testado): `selo.py` recebe só primitivos, não importa `report.py`. Preservar; a mudança de "não estampar evitar" (D-04) deve ser feita do lado do `report`/veredito, sem acoplar o selo.
- **Fronteira CRU × valuation (FIX-04)**: métodos `*_valuation()` são o número-síntese; `*(ano)` crus alimentam tabela/screening. O classificador deve usar os `*_valuation()` para os sinais de síntese.
- **Setor override display-only** (`ticker_map.json`): já existe precedente de corrigir rótulo de setor por ticker — reaproveitável se algum ticker forte for mal rotulado.

### Integration Points
- **Entrada do roteamento:** `report.py` logo após o cálculo do Ke (`:113-128`), antes de montar o DDM (`:136`). O arquétipo escolhe se o bloco DDM roda como primário ou é rebaixado (D-04).
- **Saída:** novos campos em `AnaliseAcao` (`report.py:22`) — arquétipo, motor escolhido, flag fronteiriço, candidatos — consumidos minimamente pelo render (`relatorio_markdown` `:410`) e pela CLI.
- **Registry:** novo módulo (provável `core/` ou `report/`) mapeando chave→motor; nesta fase só `pagadora_regulada`→DDM está implementado, o resto aponta para "motor pendente (Fase 2)".
</code_context>

<specifics>
## Specific Ideas

- O caso-âncora é o **ITUB4**: na Fase 1 ele já deve deixar de ser estampado "evitar" (via D-04: arquétipo financeiro → motor RIM pendente → suspende veredito primário, mostra Graham/Bazin). O fix completo (RIM produzindo ~R$40 + selo consumindo o arquétipo) fecha nas Fases 2 e 3.
- Tickers-âncora para os success criteria: **ITUB4** (financeira), **TAEE11** (regulada, deve ficar idêntica), **VALE3** (cíclica), **WEGE3** (crescimento).
- **VULC3** é o lembrete vivo de que o rótulo de setor da CVM erra — daí o híbrido (D-02) não confiar no rótulo genérico.
</specifics>

<deferred>
## Deferred Ideas

- **Thresholds finos e validação empírica** de qual sinal separa cada arquétipo com precisão → refino contínuo; backtesting contra retorno futuro é explicitamente fora de escopo do milestone (BACKTEST-01, deferido).
- **Exposição rica do "porquê" da classificação na UI** (mostrar os sinais que levaram ao arquétipo) → a UI da bandeira/veredito é da Fase 3; aqui só a exposição mínima.
- **Separar banco de seguradora** e **compounder de crescimento** como chaves distintas → considerado e recusado (D-03, 5 chaves 1:1); pode ser revisitado se a Fase 2 mostrar que RIM não serve igual para seguradora.

None dos itens acima altera o escopo da Fase 1 — discussão permaneceu dentro do domínio.
</deferred>

---

*Phase: 1-Classificador de Arquétipo + Roteamento*
*Context gathered: 2026-07-11*
