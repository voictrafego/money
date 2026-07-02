# Phase 19: Lentes de valuation e contexto na aba Analisar - Context

**Gathered:** 2026-07-02
**Status:** Ready for planning
**Source:** Decisões tomadas com o usuário (sessão) + estudo do concorrente Investidor10

<domain>
## Phase Boundary

Adicionar à **aba Analisar** (menu "Analisar uma ação") quatro lentes de valuation/contexto,
todas **read-only** sobre dados que a engine já produz. NÃO cria novos menus, NÃO toca no método
fundamentalista (DDM/múltiplos/BSD), NÃO recalcula o veredito, NÃO adiciona dependência nem chamada
de rede nova. Custo-zero mantido (CVM + Yahoo + BCB). Os 296 testes golden continuam verdes e
`app.py` permanece thin renderer (regra locked desde a Phase 2).

Fora de escopo: agenda de dividendos futura (exige feed de comunicados CVM/RI que não temos),
radar de sazonalidade, índice de Basileia, e qualquer feature que emita "compre/venda".
</domain>

<decisions>
## Implementation Decisions

### Onde a lógica vive (arquitetura)
- As **fórmulas de referência** (Graham, Bazin, "quanto teria rendido") vivem na **engine** (`core/`,
  módulo puro testável por golden) — NÃO no `app.py`. A UI só LÊ o resultado. Espelha o padrão do
  método (ex.: `ddm.py`, `multiples.py`). `app.py` continua read-only.
- Reusar dados já presentes em `AnaliseAcao`/`montar_empresa()`: **LPA, VPA, DPA, dividendos por ano,
  preço atual, preço 5a (Adj Close já baixado no gráfico da aba)**. Reusar `comparables.py`/`multiples.py`
  para os pares. **Nenhuma chamada de rede nova.**

### VAL-01 — Preço-Justo de Graham
- Fórmula: **√(22,5 × LPA × VPA)** (LPA e VPA do ano-base já calculados).
- Exibir como **card ao lado do DDM** com upside vs. preço atual.
- Degradação (never-raise): LPA ≤ 0 ou VPA ≤ 0 → "indisponível" + disclaimer de que a fórmula
  não vale para empresa sem lucro/PL positivo (ex.: não serve p/ tech/prejuízo). Não quebra a aba.

### VAL-02 — Preço-Teto de Bazin
- Fórmula: **DPA médio dos últimos 5 anos ÷ DY-mínimo (6%)**. Usar os dividendos por ano já coletados;
  se <5 anos de listagem, usar o período disponível (espelha a nota do concorrente).
- Exibir como **card** com upside vs. preço atual.
- Degradação: sem histórico de dividendos → "indisponível" + aviso de que só vale p/ boas pagadoras.

### RET-01 — "Quanto teria rendido"
- **R$ 1.000 investidos há N anos, hoje valeriam R$ X**, COM reinvestimento de dividendos.
- Fonte: o **Adj Close** da série 5a que a aba já baixa (Adj Close já embute reinvestimento) →
  `1000 × preco_hoje/preco_ini`. **Sem nova chamada de rede.**
- Exibir ~1–3 janelas (sugerido 1a e 5a). Degradação: histórico insuficiente → oculta a janela
  sem quebrar. (Rentabilidade REAL descontando IPCA fica FORA deste escopo — precisaria de série
  histórica de IPCA; só temos IPCA 12m. Pode virar follow-up.)

### PEER-01 — Comparador de pares do setor
- Tabela com **P/L, P/VP, ROE, DY, Valor de Mercado** dos pares do mesmo setor, **destacando** a ação
  analisada. Reusar `comparables.py`/`multiples.py` (a lógica de pares já existe — o Ranking usa).
- Degradação: sem pares suficientes → mensagem neutra, sem quebrar. **Não emite recomendação** (só contexto).
- **Exceção à regra "zero rede nova":** buscar pares NÃO-cacheados dispara fetch (Yahoo/CVM), igual à aba Ranking hoje. É **intencional e aceito** só para PEER-01; as outras 3 lentes (Graham/Bazin/retorno) seguem 100% sem rede nova. A verificação (19-04) NÃO deve tratar isso como violação.

### Fronteira e testes
- Fórmulas novas ganham **testes golden** (valores conhecidos) — mantém o padrão de fidelidade do projeto.
- Os 296 goldens existentes continuam verdes; nenhum arquivo de engine do método é alterado em comportamento.

### Claude's Discretion
- Layout exato dos cards (colunas, ordem) e onde encaixar na aba Analisar (perto do bloco de valuation
  existente); nomes dos módulos/funções novos; quantas janelas de rentabilidade exibir; formatação.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engine (reuso — não alterar comportamento)
- `src/analista/core/fundamentals.py` — dataclass `AnaliseAcao`/empresa: LPA, VPA, DPA, dividendos por ano, preço atual, DY.
- `src/analista/core/multiples.py` — cálculo de múltiplos (P/L, P/VP, DY, etc.).
- `src/analista/core/comparables.py` — lógica de pares/setor (usada no Ranking).
- `src/analista/core/ddm.py` — padrão de módulo de valuation testável (analog p/ Graham/Bazin).
- `src/analista/ingest/build.py` / `prices.py` — como preço 5a (Adj Close) e dividendos chegam.

### UI (thin renderer — só leitura)
- `app.py` branch `if modo.startswith("Analisar")` (~linha 588+) — onde os cards/tabela entram.
- Bloco de valuation/gráfico existente da aba Analisar — encaixar as lentes perto dele.

### Contexto de produto
- `.claude/.../memory/investidor10-competitor-analysis.md` (memória) — por que estas 4 features.
</canonical_refs>

<specifics>
## Specific Ideas

- Graham e Bazin como **duas lentes de referência ao lado do DDM** — deixar explícito que são
  fórmulas clássicas simplificadas e o DDM é a análise principal do método.
- "Quanto teria rendido" é o gancho emocional; manter honesto (com aviso "rentabilidade passada não
  garante futura" já presente no disclaimer global).
- Comparador: destacar a linha do ticker analisado para leitura rápida.
</specifics>

<deferred>
## Deferred Ideas

- Rentabilidade **real** (descontando IPCA) multi-ano — precisa de série histórica de IPCA no `macro.py`.
- Radar de dividendos (sazonalidade dos meses de pagamento) — Tier 2, próximo ciclo.
- Agenda de dividendos futura (proventos anunciados) — precisa de feed CVM/RI (fora do custo-zero atual).
</deferred>

---

*Phase: 19-lentes-de-valuation-e-contexto-na-aba-analisar*
*Context gathered: 2026-07-02*
