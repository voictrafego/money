# Phase 18: Home — Watchlist + Notícias - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning
**Source:** Conversa com o usuário (decisões travadas via perguntas) + análise da aba "Notícias" do TradersClub (mobile.tradersclub.com.br/mover) para referência de layout.

<domain>
## Phase Boundary

**Entrega:** uma **página inicial (landing default)** do app com duas partes:
1. **Watchlist** de até ~5 tickers escolhidos pelo usuário — preço + variação do dia colorida, atualizando sozinho (~30–60s), com aviso de atraso (~15min).
2. **Feed de notícias** do mercado financeiro — só **manchete + submanchete + fonte + horário**; clique abre o **site original** da fonte em nova aba; auto-atualiza (~5–15min).

**Fora de escopo (v1 desta Home):**
- Tempo-real tick-a-tick (feed pago) — fica no delayed ~15min do Yahoo.
- Camada de IA de sentimento (sentimento por notícia / "ativos mais citados" à la TradersClub) — deferido.
- Reproduzir texto completo das notícias — só manchete/trecho + link (copyright).
- Backend/login/persistência server-side da watchlist — usa `localStorage` (a conta paga vem no v2.0).
- Gráficos na watchlist (sparkline/candle) — só número + variação nesta versão (candidato a backlog).
- Qualquer mudança nas engines fundamentalista/técnica ou nos 283 goldens.

**Não-objetivo:** recomendar. A Home **exibe** preço e manchete, nunca "compre/venda".
</domain>

<decisions>
## Decisões travadas (com o usuário)

### D-01 — Onde a Home vive: **nova landing default**
- Ao abrir o app, a **Home é a primeira tela**. Os 4 menus atuais (Analisar/Garimpar/Ranking/Swing) continuam no radio lateral, sem mudança de comportamento.
- Implica reorganizar o roteamento do `app.py`: hoje o default do radio "O que você quer fazer?" é "Analisar uma ação"; a Home entra como nova opção **default/primeira**. Manter os menus existentes intactos (aditivo).

### D-02 — Watchlist: **lista default editável + persistência `localStorage`**
- Parte de ~5 tickers default de dividendos (sugestão: BBSE3, TAEE11, EGIE3, ITUB4, BBAS3 — confirmar no plano).
- Usuário edita (adiciona/remove, teto ~5) e a escolha **persiste entre sessões via `localStorage`** por navegador (sem backend). Ponte Python↔JS é unidirecional no Streamlit — reusar a lição da Fase 17 (persistência client-side via `localStorage`, best-effort com fallback).
- Tickers inválidos degradam sem quebrar (mostra "—"/erro no item, não derruba a página).

### D-03 — Fontes de notícia: **InfoMoney + Google News RSS + o que tiver RSS aberto**
- Foco no que funciona bem e de graça via **RSS**. InfoMoney tem RSS; **Google News RSS** (query de mercado BR) cobre vários veículos.
- **Valor e Folha** têm RSS fraco/paywall → validar feed a feed no plano; incluir só o que retornar manchete utilizável. Não travar a fase numa fonte específica.
- Parser: `feedparser` (possível **única dependência Python nova** — validar/pinnar; se preferir custo-zero de dep, avaliar parse de RSS com stdlib, mas `feedparser` é o pragmático).

### D-04 — Refresh das cotações: **auto ~30–60s + aviso de atraso ~15min**
- Auto-refresh via `st.fragment` (padrão das Fases 16/17) escopado só ao bloco da watchlist — não re-roda o app todo.
- Efeito visual verde/vermelho na variação do dia (e, se viável sem complicar, um flash na mudança de preço).
- **Aviso explícito de atraso (~15min)** visível (selo/legenda) — não passar sensação de tempo-real.
- Notícias auto-atualizam em cadência maior (~5–15min).

### D-05 — Custo & carga: **cache compartilhado no servidor (obrigatório)**
- `@st.cache_data(ttl=...)` no fetch de cotações e de RSS → **1 chamada por ticker/feed por intervalo**, independente do nº de usuários. Sem isso, N usuários × polling = risco de bloqueio do Yahoo (não-oficial). Este é o item de arquitetura mais importante da fase.
- TTL alinhado à cadência: cotações ~30–60s; RSS ~5–15min.

### D-06 — Arquitetura: **UI fina + módulo novo read-only**
- Lógica de agregação num módulo novo e leve (ex.: `core/home_feed.py` / `core/watchlist.py`): busca cotações (reusa o fetch Yahoo já usado no swing) e parseia RSS. `app.py` ganha a página Home como camada fina.
- **Custo-zero**: sem API paga. **283 goldens intactos**; engines fundamentalista/técnica **não são tocadas**.
</decisions>

<insights_tradersclub>
## Referência de layout — aba "Notícias" do TradersClub (mobile.tradersclub.com.br/mover)

- **Item de notícia** = manchete (1 linha) + **chip da fonte** (ex.: InfoMoney, agência) + **horário** + ícone de compartilhar. Lista vertical densa e escaneável. → é o layout-alvo (headline + fonte + hora; submanchete quando disponível).
- **Notícia ligada a ativo**: alguns itens têm chip do ticker + variação do dia. → ideia futura de casar notícia↔watchlist (deferir se complicar).
- **Delayed 15min no plano free**, tempo-real só via cadastro em corretora → confirma que delayed é o padrão gratuito e tempo-real é pago (fora de escopo).
- **Camada "Analyst" (IA)**: sentimento por notícia/setor + "ativos mais citados" → é o diferencial deles e o que encareceria; **explicitamente fora do v1**, candidato a milestone futuro.
</insights_tradersclub>

<open_questions>
## A resolver no plano (não bloqueantes)
- Lista default exata de tickers da watchlist e teto (5 fixo?).
- Confirmar `feedparser` como dependência nova (pinnar versão) vs. parse por stdlib.
- Validar quais feeds RSS retornam manchete+resumo utilizáveis (InfoMoney, Google News RSS BR, Valor/Folha se der).
- Formato do aviso de atraso e do "estado vazio" (watchlist vazia / feed indisponível).
- Se a Home vira default, o que acontece com quem tinha o comportamento antigo (só reorganização do radio — sem migração de dados).
</open_questions>
