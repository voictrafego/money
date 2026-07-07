# Phase 20 — CONTEXT

**Phase:** 20 — Selo de Sustentabilidade do Dividendo cruzado com veredito de preço (DDM)
**Captured:** 2026-07-02

## Domain

Exibir um **selo visual de qualidade do dividendo (4 cores)** e **cruzá-lo com o veredito de preço do DDM** num quadrante, para dar ao usuário um resumo de 1 olhada: *qualidade do provento × preço*. Diferencial explícito vs. AUVP (que mostra só a cor de fundamento e **ignora o preço**). É camada de **exibição/derivação** sobre números que a engine já calcula — não é novo método.

## Decisions (locked)

### D1 — Fonte da cor do selo = score BSD existente
- A cor sai do **score BSD (0–100)** que a engine já calcula e testa (`core/screening.py`, `bsd_ranking`). Sem novo score, sem risco aos golden.
- **Cortes de cor:** 🟢 Verde **≥ 70** · 🔵 Azul **55–70** · 🟡 Amarelo **40–55** · 🔴 Vermelho **< 40**.
- Limiares são um **parâmetro tunável** (colocar em `config.yaml`, não hardcode espalhado), mas estes são os valores iniciais.

### D2 — Quadrante Qualidade × Preço com rótulos (o diferencial)
- Eixo **Qualidade** = cor do selo → **Alta** (verde/azul) vs **Baixa** (amarelo/vermelho).
- Eixo **Preço** = veredito do DDM em 3 faixas: **Barato** (SUBAVALIADA) · **Justo** (NO INTERVALO) · **Caro** (SOBREAVALIADA).
- **Matriz de rótulos:**

  | Qualidade ↓ / Preço → | Barato (SUBAVAL.) | Justo (NO INT.) | Caro (SOBREAVAL.) |
  |---|---|---|---|
  | **Alta** (verde/azul) | **JOIA** | Boa, no preço | Boa, mas cara |
  | **Baixa** (amar./verm.) | **VALUE TRAP** | Fraca | Evitar |

- **VERIFICAR** (salvaguarda DDM-FIX-05: payout>100% / DY>15% / dividendo em prejuízo) **não** entra na matriz de preço — vira um **alerta separado** ("Verificar dados") que se sobrepõe ao rótulo de preço.
- Copy sempre **descritiva, nunca recomendação** (gate regulatório): "JOIA/VALUE TRAP" descrevem a combinação qualidade×preço, não dizem "compre/venda".

### D3 — Onde exibir
- **Aba Analisar**: selo em destaque (perto do veredito atual) + o quadrante/rótulo.
- **Garimpo (BSD)** e **Ranking**: uma **coluna de selo** por linha (ambos já têm BSD/tickers na mão).
- Selo visualmente **idêntico** nos três lugares (mesma função de render).

## Canonical refs (ler antes de planejar)

- `.planning/ROADMAP.md` → "### Phase 20" (goal, requisitos SELO-01/02/03, gates).
- `docs/estudo-mercado-interno.md` → Fase 5 (#1) e Teardown 1.1-A (inspiração AUVP "Selo de Viabilidade"; o diferencial é cruzar com preço).
- Engine já existente:
  - `src/analista/core/screening.py` — `bsd_ranking(...)` retorna dicts com `bsd` (0–100), `acima_de_80`, `n_fatores_faltantes`; `REFERENCIA_BSD` (bandas), pesos (`payout` 30).
  - `src/analista/report/report.py` — monta o veredito de preço: strings `SUBAVALIADA` / `NO INTERVALO` / `SOBREAVALIADA` / `VERIFICAR` (~linhas 195–204) + a banda `vmin/vmax`.
  - `src/analista/report/presentation.py` — formatação de saída (padrão de exibição).
  - `src/analista/core/multiples.py` — CDC, payout; `core/fundamentals.py` — payout_valuation (sustentável).

## Code context (reuso e pontos de atenção)

- **Reusar**, não recriar: o número do selo é o `bsd` já calculado; o eixo de preço é o veredito do DDM já calculado. A fase é **derivação + UI**.
- **⚠ A investigar no research/plan:** hoje o **BSD é calculado no fluxo de Garimpo** (`screening.bsd_ranking` sobre uma lista). Na **aba Analisar** (fluxo `report.py` de 1 ticker) o BSD **pode não estar sendo computado** — o planner precisa decidir se chama `bsd_ranking([company])` no report ou expõe o cálculo do BSD como função reutilizável para 1 empresa. Não decidir aqui; é trabalho de plano.
- **Gate `app.py` read-only:** a lógica (score→cor, veredito→faixa, matriz→rótulo) vive na **engine/report** (ex.: campos novos num dataclass tipo `Selo`/`analise`), e `app.py` só **lê e desenha**. Seguir o mesmo firewall do `SetupSwing`.
- **Sem novas dependências**; custo-zero; **os testes golden seguem verdes** (o selo é aditivo — não altera múltiplos/DDM/BSD existentes).

## Deferred ideas (não nesta fase)

- **Sub-score de sustentabilidade dedicado** (payout sustentável + cobertura por FCO + consistência do DPA + dívida), substituindo o BSD como fonte da cor — considerado e adiado em favor de reusar o BSD. Candidato a fase futura se o BSD se mostrar grosseiro para dividendos.
- **Alertas** (corte/aumento de payout, data-com) — Onda 2, depende da camada SaaS (contas + jobs).
- **Parecer por IA** do quadrante (Gemini) — Fase 5 #2, parcado.

## Constraints (gates do marco)

`app.py` read-only · testes golden verdes · zero novas deps de runtime · custo-zero · **EXIBE, NUNCA recomenda**.
