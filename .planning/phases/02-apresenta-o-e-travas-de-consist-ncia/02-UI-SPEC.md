---
phase: 2
slug: apresenta-o-e-travas-de-consist-ncia
status: draft
shadcn_initialized: false
preset: none
created: 2026-06-05
---

# Fase 2 — Contrato de UI (Apresentação e Travas de Consistência)

> Contrato visual e de interação. Gerado por gsd-ui-researcher, verificado por gsd-ui-checker.

**Escopo crítico:** Esta fase faz TRÊS mudanças de exibição pequenas e aditivas num app
Streamlit já existente (`app.py`). NÃO é design system novo, nem redesign, nem nova página.
Os defaults do Streamlit e as convenções já consolidadas do app são a linha de base. Não há
paleta de cores, escala tipográfica nem sistema de espaçamento a inventar — eles são herdados
do tema padrão do Streamlit. Tudo aqui é leitura de campos que a engine (Fase 1) já calcula e
formatação seguindo os padrões existentes (`st.dataframe` + dict `rows`, `help=h("chave")`,
helpers `fmt_*`, `st.success/error/warning/info`).

---

## Mudanças de UI desta fase (as únicas 3)

| ID | Modo | Local em `app.py` | O que muda |
|----|------|-------------------|-----------|
| **ANO-01** | Garimpo + Ranking | `app.py:213` (dict rows Garimpo) e `app.py:282` (dict rows Ranking) | Adicionar coluna **"Ano-base"** = `c.ultimo_ano()`, deixando visível quando há mistura de anos na comparação |
| **PAYOUT-02** | Analisar | `app.py:121-132` (aba "📈 Múltiplos & Crescimento") | Quando o payout do último ano (`c.payout(ult)`, já em `a.multiplos["DP (payout)"]`) difere do payout usado no DDM (`c.payout_valuation()`, média 3a + clamp), exibir **AMBOS rotulados** |
| **RANK-01** | Ranking | `app.py:286-288` (Preço-alvo/Upside/Veredito) | Quando a empresa é descartada da regressão (`pa is None` por ROE/payout faltante), exibir **"indisponível"** em vez do **"—"** ambíguo (lido como "cara/sem upside") |

**Restrição LOCKED (STATE.md / RESEARCH.md):** exibir o ano-base, NÃO uniformizar; ler campos
da engine, NUNCA recalcular método em `app.py`; nunca reusar `"—"` para dado faltante no Ranking.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Streamlit nativo — não é React/Next/Vite; shadcn gate N/A) |
| Preset | not applicable |
| Component library | Streamlit 1.58.0 widgets nativos (`st.dataframe`, `st.metric`, `st.tabs`, `st.success/error/warning/info`) |
| Icon library | Emoji inline (convenção existente do app: 🔎 ⛏️ 📊 ✅ 🔺 ➖ ⚠️) — não introduzir lib de ícones |
| Font | Tema padrão do Streamlit (não customizado pelo app) |

**Nota:** O app é deliberadamente minimalista. Não introduzir CSS custom, `column_config`
completo que altere larguras/ordem, nem novos padrões de layout. `st.column_config.Column(..., help=...)`
é permitido APENAS para rótulo/tooltip de coluna, se agregar clareza — caso contrário, manter
`st.dataframe(df, hide_index=True, use_container_width=True)` simples.

---

## Spacing Scale

Herdado do tema padrão do Streamlit. **Esta fase não declara nem altera espaçamento** — não
há container, card ou layout novo. As mudanças são colunas adicionais em tabelas já existentes
e linhas adicionais numa tabela de múltiplos já existente.

| Token | Value | Usage |
|-------|-------|-------|
| (Streamlit default) | — | Espaçamento de widgets, colunas e tabelas gerido pelo tema do Streamlit |

Exceptions: nenhuma. Nenhum valor de espaçamento custom é introduzido nesta fase.

---

## Typography

Herdada do tema padrão do Streamlit. **Esta fase não declara nem altera tipografia.** Rótulos
de coluna, labels de métrica e texto de tooltip usam a tipografia padrão do Streamlit para
cada elemento (`st.dataframe` header, `st.metric` label, markdown do tooltip).

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| (Streamlit default — não customizado) | — | — | — |

Convenção a seguir: rótulos de coluna curtos e diretos (ex.: "Ano-base"); texto explicativo
sempre via `help=h("chave")` com markdown do `glossario.G`, nunca prosa inline nova na tabela.

---

## Color

Herdada do tema padrão do Streamlit. **Esta fase não declara paleta 60/30/10** — seria
over-spec para 3 mudanças de exibição. O uso de cor segue a semântica de estado já estabelecida
no app, via componentes nativos do Streamlit:

| Role | Componente | Usage |
|------|-----------|-------|
| Sucesso/positivo | `st.success` + ✅ | Veredito SUBAVALIADA / "Passa filtros" / "Subavaliada ✅" |
| Alerta/atenção | `st.warning` + ⚠️ | Alertas (payout > 100%, BSD sem filtros, payout ajustado) |
| Erro/negativo | `st.error` + 🔺 | Veredito SOBREAVALIADA / falha de coleta |
| Neutro/informativo | `st.info` / `st.caption` + ➖ | Regressão indisponível (n<4), notas de rodapé |

Accent reserved for: nenhum accent novo introduzido. A cor é função da semântica de estado do
Streamlit (success/warning/error/info), reusada exatamente como já está no app.

**RANK-01 — regra de cor/semântica importante:** "indisponível" é estado NEUTRO de dado ausente,
NÃO um estado negativo. Não pintar de vermelho/erro. Renderizar como texto simples na célula da
tabela (igual ao "—" hoje), apenas com a palavra "indisponível" em vez de "—". A distinção é
textual (palavra), não cromática.

---

## Copywriting Contract

Os literais abaixo são o contrato de texto desta fase. Português pt-BR, fiel ao tom enxuto do app.

### ANO-01 — coluna Ano-base (Garimpo e Ranking)

| Element | Copy |
|---------|------|
| Rótulo da coluna | `Ano-base` |
| Valor da célula | inteiro de `c.ultimo_ano()` (ex.: `2024`); se `None`, usar `"—"` (helper padrão, dado genuinamente ausente) |
| Tooltip (chave nova `ano_base` em `glossario.G`) | "**Ano-base** — último exercício (ano) com lucro coletado para esta empresa, vindo das demonstrações da CVM. Empresas diferentes podem ter ano-base diferente conforme o que já foi divulgado; quando os anos divergem, a comparação mistura períodos — fique atento a isso." |

### PAYOUT-02 — dois payouts rotulados (Analisar, aba Múltiplos)

| Element | Copy |
|---------|------|
| Linha 1 (último ano) | `Payout (último ano)` → `fmt_pct(c.payout(ult))` |
| Linha 2 (valuation/DDM) | `Payout p/ valuation (média 3a)` → `fmt_pct(c.payout_valuation())` |
| Tooltip (chave nova `payout_dual` em `glossario.G`) | "**Por que dois payouts?** O *Payout (último ano)* é a fatia do lucro distribuída no exercício mais recente. O *Payout p/ valuation (média 3a)* é a média projetada dos últimos 3 anos (com teto de 100%), e é esse que o modelo de valuation (DDM) usa para estimar o valor justo. Quando os dois divergem, o app mostra ambos para você entender de onde vem o preço-alvo." |
| Substitui | a linha única `"DP (payout)"` da tabela de múltiplos (que hoje só mostra o último ano) — desdobrar em duas linhas rotuladas |

### RANK-01 — "indisponível" no Ranking

| Element | Copy |
|---------|------|
| Preço-alvo (quando `pa is None`) | `indisponível` |
| Upside (quando `pa is None`) | `indisponível` |
| Veredito (quando `pa is None`) | `indisponível (ROE/payout ausente)` |
| Tooltip (opcional, chave nova `indisponivel`) | "**indisponível** — esta empresa foi deixada de fora da regressão de preço-alvo porque faltou ROE ou payout para estimá-la. Não é 'cara' nem 'barata': simplesmente não há dado suficiente para o cálculo." |

### Estados gerais (já existentes — não alterar, só confirmar)

| Element | Copy (existente, manter) |
|---------|--------------------------|
| Empty state (Garimpo/Ranking sem dados) | `Nenhuma empresa com dados suficientes.` (`st.error`) |
| Empty state (Analisar sem dados) | `Não encontrei dados suficientes para {ticker}. Confira o ticker ou adicione o mapeamento em data/ticker_map.json.` (`st.error`) |
| Regressão impossível (n<4) | `Poucas empresas para a regressão (precisa de ≥4). Os preços-alvo ficam indisponíveis.` (`st.info`) |
| CTA primário (Garimpo) | `Garimpar` (existente, não alterar) |
| CTA primário (Ranking) | `Rankear` (existente, não alterar) |
| CTA primário (Analisar) | `Analisar` (existente, não alterar) |

**Ações destrutivas:** nenhuma nesta fase. É leitura/exibição apenas; sem delete, sem
mutação de dado, sem confirmação necessária.

---

## Distinção crítica: "—" vs "indisponível" vs "N/A"

O app usa `"—"` (via `fmt_pct`/`fmt_num`/`fmt_rs`) para qualquer `None`. Esta fase introduz UMA
exceção semântica deliberada (RANK-01), sem alterar os helpers genéricos:

| Símbolo | Significado | Onde usar |
|---------|-------------|-----------|
| `—` | Dado genérico ausente / não aplicável | Mantido em todas as células onde já aparece (incl. Ano-base quando `ultimo_ano()` é `None`) |
| `indisponível` | Empresa **descartada da regressão** por ROE/payout faltante (RANK-01) | APENAS Preço-alvo/Upside/Veredito do Ranking quando `pa is None` |

**Não** alterar `fmt_rs`/`fmt_pct` para devolver "indisponível" — a substituição é local, no
ramo `if pa is None:` do Ranking (ver Code Examples do RESEARCH.md `app.py:282-289`).

---

## Tooltips a adicionar em `glossario.py`

Seguir o padrão `help=h("chave")` já consolidado. Adicionar a `glossario.G`:

| Chave nova | Usada em | Conteúdo |
|-----------|----------|----------|
| `ano_base` | coluna Ano-base (Garimpo + Ranking) | ver Copywriting ANO-01 |
| `payout_dual` | aba Múltiplos (Analisar) | ver Copywriting PAYOUT-02 |
| `indisponivel` | Ranking (opcional) | ver Copywriting RANK-01 |

Texto em markdown (o tooltip do Streamlit renderiza markdown), fiel ao tom do glossário existente.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| (nenhum) | — | not applicable |

Não há registry de componentes (não é shadcn/React). Zero dependências novas — custo zero
respeitado (CLAUDE.md). Não aplicável.

---

## Open Questions (não-bloqueantes — decidir no plan/execução)

Defaults sensíveis já foram fixados acima; estas são micro-escolhas de UX que o planner pode
ajustar sem reabrir o contrato:

1. **PAYOUT-02 — local exato dos dois payouts.** Default deste contrato: duas linhas rotuladas
   na tabela de múltiplos da aba "📈 Múltiplos & Crescimento" (RESEARCH.md Open Question #1,
   recomendação primária). Alternativa aceitável: `st.metric` dedicada acima das abas. Manter
   o desdobramento da linha `"DP (payout)"` de qualquer forma.
2. **PAYOUT-02 — mostrar sempre ou só quando divergem.** Default: mostrar SEMPRE as duas linhas
   rotuladas (mais previsível e didático). Mostrar só quando `payout(ult) != payout_valuation()`
   é aceitável, mas exige tolerância numérica — preferir sempre-visível.
3. **ANO-01 — tooltip vs coluna para `ano_dpa`.** Default: exibir só `ultimo_ano()` na coluna
   (o requisito pede isso explicitamente). `ano_dpa` (ano do dividendo) é nice-to-have e, se
   incluído, vai no tooltip `ano_base`, não em coluna separada (RESEARCH.md Open Question #3).
4. **ANO-01 — tooltip da coluna via `column_config` vs markdown.** Default: usar
   `st.column_config.Column("Ano-base", help=h("ano_base"))` para tooltip por coluna, OU manter
   `st.dataframe` simples e documentar o ano-base num `st.caption`/tooltip do bloco. Ambos
   aceitáveis; não alterar larguras/ordem das demais colunas (Pitfall 5 do RESEARCH.md).

---

## Checker Sign-Off

> Nota ao checker: esta é uma fase de exibição aditiva num app Streamlit existente. As dimensões
> Color/Typography/Spacing são herdadas do tema padrão do Streamlit por design — "herdado, não
> declarado" é a resposta correta e intencional, não uma lacuna. Avaliar Copywriting e
> consistência com os padrões existentes do app como dimensões primárias.

- [ ] Dimension 1 Copywriting: PASS — rótulos e estados definidos (Ano-base, dual-payout, indisponível)
- [ ] Dimension 2 Visuals: PASS — reusa widgets nativos do Streamlit, sem padrão novo
- [ ] Dimension 3 Color: PASS — herdada (semântica success/warning/error/info do Streamlit)
- [ ] Dimension 4 Typography: PASS — herdada (tema padrão do Streamlit)
- [ ] Dimension 5 Spacing: PASS — herdado (tema padrão do Streamlit)
- [ ] Dimension 6 Registry Safety: PASS — não aplicável (sem registry, zero deps novas)

**Approval:** pending
