# Milestones

## v2.2 Motor de Valuation por Arquétipo (Shipped: 2026-07-12)

**Phases completed:** 3 phases (01–03), 14 plans. Fases arquivadas em `.planning/milestones/v2.2-phases/`.

**Key accomplishments:**

- **Classificador + roteamento (Fase 01):** a ferramenta passa a decidir o **arquétipo do negócio antes de valuar** (filtro grosso por setor CVM + refino quantitativo por ROE/retenção/ciclicidade em resíduos log-lineares), com **fallback honesto** que marca casos-fronteira e guarda 2–3 lentes candidatas em vez de chutar. Escolha do motor migra de DDM hard-coded para um **registry arquétipo→motor** consumido no funil de `report.py`. (ARQ-01/02, ENG-01/06)
- **Motores por arquétipo (Fase 02):** plugados no registry os motores que faltavam — **RIM** (banco/seguradora, destrava o ITUB4 de ~R$16 do DDM comprimido para ~R$23–40), **lucro normalizado** (cíclicas, média 7–10a), **DCF multi-estágio** (crescimento) e **NAV** (holding). O DDM puro não foi tocado; rebaixa a "lente conservadora" onde não é o primário. (ENG-02..05)
- **Veredito honesto (Fase 03):** o selo passa a **consumir o motor do arquétipo** (não o DDM fixo), preservando o firewall testado selo↛report; **ensemble motor×contraponto DDM** com **bandeira de divergência** + hipótese curada quando maior > 2× menor (ENS-01); **guarda-corpos anti-aberração** SAN-01 (`_guarda_san01`: reetiqueta "DDM conservador demais para o perfil", número visível) antes de estampar "evitar"; e **dúvida honesta no caso-fronteira** (range dos motores candidatos + bandeira "classificação incerta", VER-02). ITUB4 deixou de ser carimbado "Evitar". (VER-01/VER-02)
- **Consistência entre superfícies:** os 3 sinais do veredito honesto (bandeira, range, reetiqueta) e o rótulo do intrínseco por motor renderizados no CLI markdown E na aba Analisar do Streamlit, lendo o mesmo objeto `AnaliseAcao` sem recálculo — Core Value (mesma ação, mesmos números em cada menu).

**Auditoria de milestone:** PASSED. A auditoria cross-fase pegou um blocker que a verificação por-fase não via — a aba **"Ranking por múltiplos" do Streamlit** ainda cravava "Cara"/"Subavaliada" por regressão de lente única, sem o freio que o CLI já aplicava (ITUB4 aparecia "Cara" no Ranking e protegido no Analisar). **Fechado antes do arquivamento** pela quick task `260712-p6r`: freio extraído para `core/freio.py` (fonte única), aplicado na aba Ranking com paridade travada por teste `is`. Suíte final **437 verde**; firewall intacto.

**Known deferred items at close:** 4 quick-tasks obsoletas da era v1.x (ajuste do Ranking por múltiplos, robustez da resolução de tickers, Swing Trade MVP candlestick, auto-refresh do 4º menu) — reconhecidas e adiadas, não fazem parte do v2.2. Ver STATE.md Deferred Items.

---

## v2.0 Comercialização — Lazari Capital (Shipped: 2026-07-10)

**Phases completed:** 3 phases (01–03), 12 de 13 plans. Fases arquivadas em `.planning/milestones/v2.0-phases/`.

**Key accomplishments:**

- **Fundação (Fase 01):** camada Django própria (repo `lazari-capital`, espelhando o `crm-voic`) com cadastro self-serve email+senha, sessão, `status_assinatura` como fonte de verdade e trial de 7 dias sem cartão; gate via Traefik forward-auth (Django valida sessão+status, injeta `X-User-Email` no Streamlit).
- **Cobrança (Fase 02):** cobrança recorrente mensal via Asaas (checkout hospedado, produto nunca toca cartão), webhooks nativos Django idempotentes (sem n8n) atualizando o status, e página de conta (status/cancelar/link de cobrança).
- **Go-live (Fase 03):** deploy integrado na VPS — `www.lazaricapital.com.br` (Django landing/auth/billing, TLS) + `app.lazaricapital.com.br` (Streamlit atrás do gate, WS 101 sem loop); cutover do `money.voictech.com.br` (301/308) concluído com n8n/crm intactos; stack `lazari` 1/1 healthy + cron de backup diário. Marca comercial Lazari Capital no ar, posicionada como software educacional (sem recomendação).
- **v2.1 (polish de UX, entregue como quick-tasks):** Top-5 do review UX deployado 2026-07-10 (spinner de carregamento, abas sem flash, formatação numérica BR `R$ 41,57`, legendas de selo/triângulo + glossário de siglas, menus renomeados + contagem corrigida).

**E2E pago (03-05):** CONCLUÍDO — smoke real R$19,90 PIX confirmado ao vivo (suíte Phase 2 ao vivo + webhook idempotente + transições de status no navegador). NFS-e automática por assinatura implementada e validada. Único item aberto (não-técnico): operador decidir se estorna o R$19,90 do smoke no painel Asaas.

---

## v1.3 Saneamento residual do valuation (Shipped: 2026-06-28)

**Phases completed:** 3 phases (09–11), 9 plans

**Key accomplishments:**

- Payout sustentável geral (mediana sobre a série completa, sem clamp em 100%) + DY recorrente earnings-based (lucro normalizado × payout sustentável), robustos a anos extraordinários para qualquer ticker (Fase 9 — DYR-01/PAY-01).
- g histórico robusto via regressão log-linear (não endpoint-a-endpoint) e Garimpo/Ranking calculando crescimento sobre a série normalizada, não o lucro/dividendo CRU (Fase 10 — GROW-01/GROW-02).
- Apresentação: DY recorrente em destaque no header, payout cru do último ano exibido à parte, % na tabela de Múltiplos, e trava de validação multi-ticker (VULC3 + ITUB4/EGIE3/TAEE11/BBAS3) com rebaseline deliberado dos golden (Fase 11 — DYR-02/PAY-02/HIER-01/TEST-08). 8/8 requisitos.
- **Auditoria online + correção de dados (mesma sessão, deployado):** 4 bugs que faziam 4/4 ações saírem "sobreavaliada" — unit XXXX11 (P/L 3×/5×), proventos sem JCP (payout-mediana pela metade nos bancos → DFC da CVM), Ke=Selic spot → through-the-cycle (média 10a), empresas single-entity invisíveis (seleção consolidado/individual por empresa) + ticker_map +60 via FCA. Mais disclaimer legal. 191 testes verdes; deployado na VPS.

**Known deferred items at close:** 4 (2 quick-tasks obsoletos, 1 UAT parcial sem cenários abertos, 1 verificação humana da Fase 10) — ver STATE.md Deferred Items. Trabalho validado por 191 testes + checagens ao vivo.

---

## v1.2 Indicadores de tendência (timing) na aba Analisar (Shipped: 2026-06-27)

**Phases completed:** 5 phases (4–8), 16 plans

**Key accomplishments:**

- `core/indicators.py` puro calcula 4 famílias (Tendência SMA/EMA+cross, Canais Donchian/Bollinger/squeeze, Força ADX/inclinação, Momentum RSI/MACD) do OHLC, com matemática travada por golden (Wilder, no-repaint, split ITSA4, ADX×TradingView).
- Sinais técnicos vivem em `AnaliseAcao` via `analisar_acao`, com composite de timing (árvore MM200×ADX), matriz fundamento×técnico (fundamento sempre líder) e alerta de reverificação (voz "reverifique os fundamentos", nunca venda); base temporal semanal (W-FRI).
- Saneamento do motor DDM (caso VULC3): camada de normalização de lucro (FIX-04), reconciliação g_alto×g_fundamentos, CAPM 'local' com Selic do BCB, banda = sensibilidade real + DY recorrente (Fase 8).
- UI: overlays/subpainéis/controles do gráfico de indicadores + glossário (tooltips), encanamento OHLC/split-adjusted preservado da ingestão até a engine (Fases 4/7). 150 testes verdes.

---

## v1.1 Gráfico de preço na aba Analisar (Shipped: 2026-06-23)

**Phases completed:** 3 phases, 9 plans, 20 tasks

**Key accomplishments:**

- Unificou na origem três cálculos divergentes entre modos — payout-para-valuation (CR-02/WR-03), base de PL do ROE (WR-01) e DY corrente trailing-12m (WR-04) — numa engine única consumida por Analisar, Garimpo e Ranking.
- BSD do Garimpo reproduzível e absoluto (bandas fixas calibráveis em REFERENCIA_BSD), fatores ausentes neutros e contados, e proxy de crescimento na janela anos_media — fechando WR-06, WR-05 e WR-02.
- Expôs `vmin`/`vmax` em `AnaliseAcao` a partir do cálculo único do veredito (eliminando a duplicação UI×report — WR-07/VAL-01); a parte de payout canônico do DDM (PAYOUT-01/CR-02/WR-03) já havia sido entregue por 01-01 e foi verificada como satisfeita.
- Conectou os três modos do `app.py` à engine corrigida nos Planos 01–04: Garimpo ordena por "Passa filtros" (corte Selic) antes do BSD, Ranking monta o payout via `payout_valuation()` com sinalização de payout fora de faixa, e Analisar exibe o intervalo intrínseco lendo `a.vmin`/`a.vmax` — fechando GARIMPO-01/PAYOUT-01/RANK-02/VAL-01 na borda da UI. Verificação humana dos três modos no navegador APROVADA.
- Coluna Ano-base (Garimpo+Ranking), dois payouts rotulados na aba Múltiplos do Analisar e 'indisponível' neutro no Ranking, ligando à UI campos que a engine canônica da Fase 1 já expunha — sem recálculo de método em app.py — mais 3 tooltips no glossário; checkpoint human-verify APROVADO pelo usuário.
- A série diária de close de 5 anos que `prices.py` já baixava e descartava agora é preservada em `DadosMercado.serie_precos` e conduzida até `CompanyData` sem nova chamada de rede; plotly>=6.0 pinado e instalado.
- A aba "Analisar" agora renderiza, no topo (antes dos sub-tabs), um gráfico Plotly da evolução do preço de close de 5 anos (`c.serie_precos`) com a banda horizontal do valor intrínseco do DDM (`a.vmin`–`a.vmax`) sobreposta via `add_hrect`, com zoom/hover nativos e dois fallbacks graciosos (série indisponível → aviso sem quebrar; DDM None → só a linha).

---
