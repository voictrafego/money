# Milestones

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
