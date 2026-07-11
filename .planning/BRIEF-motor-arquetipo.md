# Brief de Milestone: Motor de Valuation por Arquétipo de Negócio

> **Como usar este arquivo:** este é o documento-fonte para abrir o próximo milestone do engine.
> Com a sessão do Claude Code **enraizada neste repo** (`analista_dividendos`), rode:
> 1. `/gsd-new-milestone` — apontando para este brief (sugestão de código: **v2.2 — Motor por Arquétipo**).
> 2. `/gsd-plan-phase` — para detalhar a(s) fase(s) que o roadmap gerar.
>
> Preserva o texto original da fase (seção "Documento original") e adiciona o enquadramento
> GSD (requisitos, critérios de aceite) + o mapa de código já levantado (âncoras `arquivo:linha`).

**Proposto:** 2026-07-10
**Milestone sugerido:** v2.2 — Motor de Valuation por Arquétipo (número final decidido no `/gsd-new-milestone`)
**Natureza:** trabalho de **engine** (não de comercialização). Milestone v2.0 (Lazari Capital) está fechado; v2.1 é o backlog de polish de UX. Este é um milestone major de arquitetura do valuation.

---

## Core Value

Cada tipo de negócio é roteado para o motor de valuation certo antes de valuar, e **nenhum veredito final é puxado por um modelo que não serve para aquele perfil**. Um compounder de qualidade (banco) nunca mais é carimbado "evitar" porque o DDM de estágio único não cabe nele.

## Milestone Goal

Corrigir o erro de **arquitetura** (não de fórmula) em que a ferramenta aplica um único motor primário (DDM de estágio único) para todas as ações. Construir: (1) um classificador de arquétipo que roteia cada ação, (2) um registro de motores por arquétipo, (3) ensemble com bandeira de divergência, (4) guarda-corpos de sanidade anti-aberração, (5) uma agregação de veredito que consome o motor **do arquétipo** e assume a dúvida em casos-fronteira. Meta: acertar os ~85% de casos claros e assumir honestamente a dúvida nos ~15% fronteiriços.

## Contexto: o caso ITUB4 que expôs o problema

- Preço de mercado: R$ 43,59 · DDM (ao vivo): R$ 12,93–19,32 · Graham: R$ 39,88 · Bazin: R$ 28,97
- Veredito estampado: **SOBREAVALIADA / Qualidade Baixa / Evitar**
- Divergência de ~3x entre DDM e Graham/mercado não é ruído — é sinal de motor primário errado para o negócio.
- Raiz (todas consequência de DDM de estágio único num banco): (1) Ke ~17,3% ao vivo (Selic alta via CAPM) comprime o denominador `V = D1/(Ke−g)`; (2) normalização de payout 105%→46,7% correta, mas derruba o DY de 7,9%→4,0% na entrada do modelo; (3) DDM ignora lucro retido reinvestido (ROE 19,3%, retenção ~53%), subestimando o compounder.

> Nota técnica (levantada no repo): o teste golden trava o DDM do Itaú em **R$ 37,22** (`tests/test_ddm.py`), usando Ke fixo de livro (12,48%). A run ao vivo injeta Rf via Selic (`macro.selic_ciclo_para_capm`) → Ke ~17,3% → comprime para ~R$ 16. Portanto esta refatoração **não deve quebrar** o golden do livro (input fixo), mas confirma a hipersensibilidade do DDM ao vivo ao Ke.

---

## Requisitos

### Classificador de arquétipo (ARQ) — o coração, ~60% do esforço

- **ARQ-01**: Classificador que decide o arquétipo do negócio **antes de valuar**, a partir dos dados já puxados (CVM + Yahoo + BCB): filtro grosso por setor CVM + refino quantitativo por métricas que a própria ação entrega (financeira → RIM; pagadora estável com payout comportado → DDM elegível; ROE alto e estável com retenção alta → compounder; margem/lucro oscilando violento → cíclica).
- **ARQ-02**: **Fallback honesto** — quando a confiança do classificador for baixa (caso-fronteira, híbrido, mudança de estágio), NÃO chutar: marcar como fronteiriço e rodar 2–3 lentes candidatas.

### Registro de motores (ENG)

- **ENG-01**: Registry arquétipo→motor primário, consumido pela agregação do veredito.
- **ENG-02**: **RIM (Residual Income Model)** — VPA + VP do excesso de ROE sobre Ke — para banco/seguradora (ITUB4, BBAS3, BBSE3).
- **ENG-03**: **Lucro normalizado** (média 7–10a ou mid-cycle) → EV/EBITDA ou FCF para cíclica de commodity (VALE3, GGBR4, SUZB3).
- **ENG-04**: **DCF de FCF multi-estágio** (ou múltiplo relativo) para crescimento/capital-light (WEGE3, tech, varejo em expansão).
- **ENG-05** (stretch/holding): **NAV / SOTP** para holding/imobiliária. Avaliar se entra neste milestone ou fica deferido.
- **DDM** permanece como motor primário para pagadora madura/regulada (TAEE11, SAPR11, EGIE3) — já existe, não quebrar.

### Ensemble & divergência (ENS)

- **ENS-01**: Nunca cravar número único quando os modelos discordam muito. Rodar motor primário + ≥1 contraponto; se a divergência passar do limiar (ex: maior > 2× menor), levantar **bandeira de divergência** com hipótese ("compounder subvalorizado pelo DDM", "cíclica no topo do ciclo", etc). Divergência é informação exibida, não defeito escondido.

### Guarda-corpo de sanidade (SAN)

- **SAN-01**: Regras anti-aberração que capturam o absurdo antes de virar selo. Ex.: SE `intrínseco < 0,5 × mediana dos pares` E `ROE > 15%` E `normalização de payout cortou o dividendo > 40%` ENTÃO não estampar "qualidade baixa / evitar" — estampar "DDM conservador demais para o perfil, ver motor primário do arquétipo".

### Veredito honesto (VER)

- **VER-01**: Refatorar a agregação do selo final para consumir o motor **do arquétipo**, não o DDM fixo.
- **VER-02**: Em caso-fronteira, o veredito assume a dúvida em voz alta (range + bandeira) em vez de fingir certeza.

---

## Critérios de Aceite (Success Criteria)

1. **ITUB4** não é mais estampado "evitar" via DDM sozinho. Motor primário = RIM; DDM rebaixado a "lente conservadora".
2. **Pagadora regulada** (TAEE11) continua usando DDM como primário (não quebrou o que funcionava).
3. **Cíclica** (VALE3) usa lucro normalizado, não o lucro de um ano só.
4. **Crescimento** (WEGE3) não recebe mais DDM cuspindo zero/lixo.
5. **Caso híbrido/fronteiriço** exibe range + bandeira de divergência em vez de veredito falso cravado.
6. **Zero aberração silenciosa:** todo veredito "evitar" passa pelos guarda-corpos antes de exibir. Aberração reconhecida e comentada é aceitável; número errado com cara de certo, não.

---

## Fora de Escopo

- Acertar 100% dos tickers automaticamente (meta: ~85% claros + assumir dúvida nos ~15%).
- Novas fontes de dados além de CVM, Yahoo e BCB.
- Redesenho de UI além da lógica de veredito e da exibição da bandeira de divergência.
- Backtesting dos modelos contra retorno futuro (fase posterior).

## Nota de Implementação

O gargalo é o **classificador**, não os motores (RIM/DDM/lucro normalizado/DCF/SOTP são fórmulas de livro-texto, ~20% do esforço). Priorizar a **árvore de decisão do classificador** primeiro, depois plugar os motores nela.

**Ordem sugerida de fases:** (1) Classificador de arquétipo + fallback honesto → (2) Engine registry + motores (RIM primeiro, é o que destrava ITUB4) → (3) Ensemble + bandeira de divergência → (4) Guarda-corpos de sanidade → (5) Refatoração do veredito/selo para consumir o arquétipo.

---

## Mapa de código (levantado em 2026-07-10 — âncoras para o planejamento)

Ponto único de valuation e onde o roteamento entra:

- **`src/analista/report/report.py`**
  - `analisar_acao(c, cfg)` (`report.py:53`) — **o funil**. Ordem interna: múltiplos (`:64`) → crescimento (`:80-102`) → lifecycle (`:109`) → CAPM `a.ke` (`:113-128`) → DDM (`:140-152`) → flags de risco (`:158-168`) → **veredito** (`:170-207`) → read técnico (`:240-290`) → selo (`:307-311`). **Roteamento de arquétipo entra entre o CAPM (`:113`) e a montagem do DDM (`:136`).**
  - Precedente de bandeira já existe: veredito `"VERIFICAR — possível divergência de modelo"` (`report.py:197-201`), hoje disparado por flags de risco. É o ponto natural de extensão para a bandeira de divergência.
  - `relatorio_markdown(c, a, cfg)` (`report.py:410`) — render; seção Veredito em `:489`. `AnaliseAcao` dataclass em `:22`. `_veredito_token` (`:355`) parseia o prefixo do veredito (manter em sincronia com o selo).
- **`src/analista/report/selo.py`** — **a agregação do veredito final**. `montar_selo(bsd, veredito, cfg)` (`selo.py:105`) cruza eixo qualidade (BSD, `cor_do_bsd` `:58`) × eixo preço (`faixa_do_veredito` `:88`, por PREFIXO do veredito) via matriz 3×2 `_MATRIZ` (`:48`). "Evitar" = célula `(Baixa, Caro)` (`:54`). **Firewall testado: selo.py NÃO importa report.py** — só recebe primitivos. Se mudar strings de veredito, atualizar `faixa_do_veredito` (`:88`) e `report._veredito_token` (`:355`) juntos.
- **`src/analista/core/ddm.py`** — DDM puro. `ddm_dois_estagios` (`:78`), `valor_gordon` (`:37`), `matriz_sensibilidade` (`:118`). Recebe Ke/g/dpa prontos; não calcula nada de contexto.
- **`src/analista/core/lentes.py`** — Graham (`preco_justo_graham` `:37`), Bazin (`preco_teto_bazin` `:75`), VPA (`:51`), comparador de pares (`:140-221`). Hoje **secundárias** (só exibidas, não entram no veredito). Candidatas naturais a "lentes contraponto" do ensemble.
- **`src/analista/core/fundamentals.py`** — `CompanyData` (`:20`); métricas canônicas `roe_valuation` (`:137`), `lpa_valuation` (`:132`), `payout_valuation` (mediana s/ clamp, `:78`), `base_lucro_normalizada` (`:122`), `dy_atual`/`dy_recorrente`. **`setor` é string** (preenchida em `build.py:56`), hoje usada só para `eh_concessionaria` (`build.py:68`) e parsing CVM de bancos — **não roteia valuation**. Insumo-chave do classificador.
- **`src/analista/core/normalizacao.py`** + `serie_lucro_normalizada` — normalização estatística de lucro (winsor/mediana) já existe; base para o lucro normalizado das cíclicas.
- **`src/analista/core/comparables.py`** — regressão P/L=f(DP,ROE) e ranking por múltiplos; mediana/estatística de pares (relevante para o guarda-corpo "0,5× mediana dos pares" do SAN-01). Tabela de pares de contexto também em `lentes.py`.
- **`src/analista/core/lifecycle.py`** — `classificar_estagio` (rótulo de estágio; informativo, não roteia). Reaproveitável como sinal do classificador.
- **`src/analista/ingest/`** — `cvm.py` (bancos usam códigos de conta diferentes: PL 2.08 vs 2.03, receita de intermediação), `prices.py` (Yahoo), `macro.py` (Selic/Rf), `build.py` (`montar_empresa` `:40` orquestra ingest), `universe.py` (ticker→CD_CVM+setor).
- **Entrada:** CLI `python -m analista analyze ITUB4` (`cli.py:58`); Rf ao vivo injetado em `cli.py:69`. UI Streamlit em `app.py`.

### Testes que travam comportamento (NÃO quebrar sem intenção)

- `tests/test_ddm.py` — golden do livro: Ke Itaú 12,48%, DDM Itaú ≈ R$ 37,22 (input fixo).
- `tests/test_selo.py` — cortes de cor (70/55/40), rótulos da matriz (JOIA/VALUE TRAP/Evitar…), prefixos de veredito, **firewall** (selo não importa report). Se a refatoração mudar prefixos/rótulos, atualizar aqui.
- `tests/test_vulc3_regressao.py` — capstone end-to-end; invariante: veredito começa com "VERIFICAR". Mais frágil a mudanças no veredito/normalização.
- `tests/test_guardrails_fix06.py` — banda vmin/vmax = min/max da matriz; setor override VULC3.
- `tests/test_consistencia_modos.py` — mesmo número entre Analisar/Garimpo/Ranking (Core Value). Métodos canônicos `*_valuation()` em `fundamentals.py` são fonte única — mexer neles reverbera nos 3 modos.

---

## Documento original da fase (verbatim, como fornecido pelo operador)

### Objetivo da fase

Corrigir de vez o problema estrutural onde a ferramenta aplica **um único motor de valuation (DDM de estágio único)** como análise primária para todas as ações, gerando vereditos falsos ("qualidade baixa / evitar") em empresas de qualidade sempre que o motor não cabe no perfil do negócio.

Não é um bug pontual. É erro de arquitetura. O conserto é rotear cada tipo de negócio para o motor certo e nunca mais deixar um veredito final ser puxado por um modelo que não serve para aquele perfil.

### Onde exatamente o pipeline atual falha

1. **Não existe etapa de classificação/roteamento.** O campo "Setor: Bancos" é exibido na tela mas não é usado para escolher o modelo.
2. **Só existe um motor primário.** DDM de estágio único é a única análise principal. Graham e Bazin entram como "lentes de referência", secundárias. Não há RIM, não há lucro normalizado, não há FCF/DCF.
3. **A agregação do veredito é single-model.** O selo final (BSD × DDM) é puxado pelo DDM.
4. **Não há detecção de divergência nem guarda-corpo de sanidade.** Quando os modelos discordam em 3x, a ferramenta escolhe o pior em vez de sinalizar.
5. **Não há saída honesta para caso-fronteira.** A ferramenta sempre crava um veredito.

O problema não está nos modelos individuais (matematicamente corretos). Está na **ausência de roteamento** e na **função que agrega o veredito final**.

### Registro de motores

| Arquétipo | Exemplos | Motor primário |
|---|---|---|
| Banco / seguradora | ITUB4, BBAS3, BBSE3 | Residual Income Model (VPA + VP do excesso de ROE sobre Ke) |
| Pagadora madura / regulada | TAEE11, SAPR11, EGIE3 | DDM (o motor atual, que aqui funciona) |
| Cíclica de commodity | VALE3, GGBR4, SUZB3 | Lucro normalizado (média 7-10 anos ou mid-cycle) → EV/EBITDA ou FCF |
| Crescimento / capital-light | WEGE3, tech, varejo em expansão | DCF de FCF multi-estágio ou múltiplo relativo |
| Holding / imobiliária | patrimoniais | NAV / Soma das Partes (SOTP) |
