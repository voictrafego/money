# Fase 2: Apresentação e Travas de Consistência - Mapa de Padrões

**Mapeado:** 2026-06-05
**Arquivos analisados:** 3 (`app.py` modificado em 3 sítios, `glossario.py` modificado, `tests/test_consistencia_modos.py` novo)
**Analogias encontradas:** 3 / 3 (todas internas ao próprio repo — fase aditiva, sem greenfield)

> Esta fase é apresentação pura + 1 teste. Todos os analogons já existem no codebase.
> O planner deve **espelhar exatamente** as convenções abaixo, com `file:linha`.
> Regra LOCKED (Fase 1): a UI **lê** campos da engine, **nunca recalcula** método.

---

## Classificação de Arquivos

| Arquivo (novo/modificado) | Papel | Fluxo de Dados | Analogon mais próximo | Qualidade |
|---------------------------|-------|----------------|----------------------|-----------|
| `app.py` (Garimpo, dict `rows` ~213-221) | view/render | request-response (leitura→tabela) | o próprio bloco Garimpo `app.py:213-221` | exact (auto-analogon: adicionar 1 chave ao dict) |
| `app.py` (Ranking, dict `rows` ~282-289) | view/render | request-response | o próprio bloco Ranking `app.py:282-289` | exact |
| `app.py` (Analisar, aba Múltiplos ~121-132) | view/render | request-response | bloco de múltiplos `app.py:125-132` | exact |
| `src/analista/glossario.py` (`G` dict) | config/i18n | static-lookup | entradas existentes `glossario.py:11-99` | exact (mesma estrutura de dict) |
| `tests/test_consistencia_modos.py` (NOVO) | test | unit/integração (sem rede) | `tests/test_screening.py::_empresa_solida` | role-match + fixture-match |

**Caminho real do glossário confirmado:** `src/analista/glossario.py` — dict module-level `G: dict[str, str]` (linha 11), acessado via `h(chave)` (linha 102-104). Import no app: `from analista.glossario import h` (`app.py:17`).

---

## Pattern Assignments

### `app.py` — ANO-01 Garimpo (view, dict `rows`)

**Analogon:** `app.py:213-221` (o próprio dict `rows` do Garimpo).

**Padrão atual a espelhar** (`app.py:213-221`):
```python
rows.append({
    "Ticker": c.ticker,
    "_passou": bool(rc.passou),
    "BSD": round(b.get("bsd") or 0, 1),
    "BSD > 80": "✅" if b.get("acima_de_80") else "",
    "Passa filtros": "✅" if rc.passou else "",
    "Fatores faltando": b.get("n_fatores_faltantes") or 0,
    "Setor": c.setor,
})
```

**Mudança (aditiva):** inserir uma chave `"Ano-base": c.ultimo_ano()` no dict. `c` é o `CompanyData` já em escopo no loop (`app.py:209 for c in empresas:`). `c.ultimo_ano()` é `Optional[int]` (`fundamentals.py:54-56`) — `st.dataframe` renderiza `None` como vazio; se quiser literal, usar `c.ultimo_ano() or "—"` (helper-style; "—" = ausente genérico, conforme UI-SPEC).

**Renderização da tabela (não mudar):** `app.py:224-226` — `pd.DataFrame(rows).sort_values(...)` + `st.dataframe(df, hide_index=True, use_container_width=True)`. A nova coluna entra automaticamente na ordem de inserção do dict. **Não usar `column_config` que altere larguras** (Pitfall 5). Tooltip de coluna opcional via `st.column_config.Column("Ano-base", help=h("ano_base"))` é permitido só se não reordenar/redimensionar.

---

### `app.py` — ANO-01 Ranking (view, dict `rows`)

**Analogon:** `app.py:282-289` (o próprio dict `rows` do Ranking).

**Padrão atual a espelhar** (`app.py:282-289`):
```python
rows.append({
    "Ticker": r["empresa"],
    "Nota (0–100)": round(r["nota"], 1) if r["nota"] is not None else None,
    "Preço atual": fmt_rs(next(c.preco_atual for c in empresas if c.ticker == r["empresa"])),
    "Preço-alvo": fmt_rs(pa.preco_alvo) if pa else "—",
    "Upside": fmt_pct(pa.upside) if pa and pa.upside is not None else "—",
    "Veredito": veredito,
})
```

**Mudança (aditiva):** inserir `"Ano-base": <empresa>.ultimo_ano()`. Atenção: no Ranking o loop é `for r in ranking` (dicts de resultado), **não** sobre `CompanyData`. O `CompanyData` é obtido pelo mesmo idiom já usado na linha `"Preço atual"`:
```python
"Ano-base": next(c.ultimo_ano() for c in empresas if c.ticker == r["empresa"]),
```
(espelha exatamente o `next(c.preco_atual for c in empresas if c.ticker == r["empresa"])` da linha 285).

**Renderização (não mudar):** `app.py:290` — `st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)`.

---

### `app.py` — RANK-01 "indisponível" (view, branch `pa is None`)

**Analogon:** `app.py:275-289` (a montagem do `veredito` + dict `rows` do Ranking).

**Padrão atual** (`app.py:276-288`) — onde o `"—"` ambíguo vive:
```python
pa = alvos.get(r["empresa"])
veredito = "—"
if pa:
    veredito = "Subavaliada ✅" if pa.subavaliada else "Cara 🔺"
    if pa.payout_fora_faixa:
        veredito += " ⚠️ payout ajustado"
rows.append({
    ...
    "Preço-alvo": fmt_rs(pa.preco_alvo) if pa else "—",
    "Upside": fmt_pct(pa.upside) if pa and pa.upside is not None else "—",
    "Veredito": veredito,
})
```

**Mudança (RANK-01):** quando `pa is None` (empresa descartada da regressão por ROE/payout faltante — `comparables.py:129` retorna `None`), trocar os três `"—"` por `"indisponível"`. O molde recomendado (RESEARCH Code Example app.py:282-289):
```python
pa = alvos.get(r["empresa"])
if pa is None:
    preco_alvo_txt = "indisponível"
    upside_txt = "indisponível"
    veredito = "indisponível (ROE/payout ausente)"
else:
    preco_alvo_txt = fmt_rs(pa.preco_alvo)
    upside_txt = fmt_pct(pa.upside) if pa.upside is not None else "—"
    veredito = "Subavaliada ✅" if pa.subavaliada else "Cara 🔺"
    if pa.payout_fora_faixa:
        veredito += " ⚠️ payout ajustado"
```
e usar `preco_alvo_txt`/`upside_txt` no dict em vez das expressões inline.

**Copy LOCKED (UI-SPEC Copywriting):** `indisponível` / `indisponível` / `indisponível (ROE/payout ausente)`.

**NÃO alterar `fmt_rs`/`fmt_pct`** (`app.py:48-57`) — a substituição é local no branch `if pa is None:`. "—" continua sendo o ausente genérico (inclusive Ano-base quando `ultimo_ano()` é None). Distinção textual, não cromática — renderizar como texto simples na célula, sem cor de erro (UI-SPEC Color).

**Não confundir** com o caso `n<4` (regressão inteira não roda), já tratado em `app.py:295` via `st.info(...)`.

---

### `app.py` — PAYOUT-02 dois payouts rotulados (view, aba Múltiplos)

**Analogon:** `app.py:125-132` (construção do dataframe de múltiplos na aba "📈 Múltiplos & Crescimento").

**Padrão atual** (`app.py:125-132`):
```python
rows = []
for k, val in a.multiplos.items():
    if k in ("ML", "ROE", "DP (payout)", "DY", "EY"):
        rows.append((k, fmt_pct(val)))
    else:
        rows.append((k, fmt_num(val)))
st.dataframe(pd.DataFrame(rows, columns=["Múltiplo", "Valor"]),
             hide_index=True, use_container_width=True)
```

Hoje a linha `"DP (payout)"` mostra **só** `a.multiplos["DP (payout)"]` = `c.payout(ult)` (último ano cru — confirmado `report.py:56`). O payout do DDM (`c.payout_valuation()`, média 3a + clamp, `fundamentals.py:73-86`) **não aparece**.

**Mudança (PAYOUT-02):** desdobrar `"DP (payout)"` em DUAS linhas rotuladas. Ler ambos os campos da engine (sem recalcular):
```python
payout_ult  = a.multiplos.get("DP (payout)")  # = c.payout(ult), último ano cru
payout_proj = c.payout_valuation()            # média 3a + clamp 1.0 (usado no DDM)
```
Default LOCKED (UI-SPEC Copywriting PAYOUT-02 + Open Question #1/#2): **sempre** exibir as duas linhas, rotuladas:
- `Payout (último ano)` → `fmt_pct(payout_ult)`
- `Payout p/ valuation (média 3a)` → `fmt_pct(payout_proj)`

Recomendação de implementação: no loop, ao encontrar `k == "DP (payout)"`, emitir a primeira linha rotulada e logo após a segunda (lendo `c.payout_valuation()`), em vez da linha genérica `"DP (payout)"`. Manter o resto do loop intacto. O `c` (`CompanyData`) está em escopo no bloco Analisar (`app.py:87`).

**`fmt_pct`** (`app.py:48-49`) já trata `None → "—"` — reusar para ambas as linhas.

**NÃO inflar `AnaliseAcao`** (Pitfall 4 / Assumption A1): ler `c.payout_valuation()` direto na UI é o caminho recomendado (zero risco de quebrar golden TEST-02). Só adicionar campo ao dataclass se o planner quiser simetria com `vmin/vmax` — nesse caso `default None` (aditivo).

---

### `src/analista/glossario.py` — 3 tooltips novos (config, lookup)

**Analogon:** entradas existentes no dict `G` (`glossario.py:11-99`), p.ex. `"roe"` (34-38) e `"tab_multiplos"` (45-53).

**Padrão a espelhar** (chave curta → string markdown; pt-BR; fiel ao tom do livro; chama capítulo quando cabível):
```python
"roe": (
    "**ROE — Retorno sobre o Patrimônio Líquido** — lucro líquido recorrente ÷ patrimônio líquido. "
    "Quanto de lucro a empresa gera para cada R$ 1 de capital próprio. Usa-se o PL médio "
    "(inicial+final)/2; indisponível no 1º ano sem histórico. (Cap. 10)"
),
```
- Strings multi-linha = parênteses + concatenação implícita de literais (não `\n` no fim de cada física, exceto quando o conteúdo quer quebra de parágrafo via `"\n\n"` / lista `"- ...\n"`).
- Markdown renderiza no tooltip do Streamlit (negrito `**`, listas `- `).
- Acesso via `h("chave")` — `h` já importado em `app.py:17`.

**Mudança (aditiva):** acrescentar 3 chaves ao dict `G` (textos LOCKED no UI-SPEC Copywriting Contract):

| Chave | Usada em | Conteúdo (UI-SPEC, verbatim) |
|-------|----------|------------------------------|
| `ano_base` | coluna Ano-base (Garimpo + Ranking) | "**Ano-base** — último exercício (ano) com lucro coletado para esta empresa, vindo das demonstrações da CVM. Empresas diferentes podem ter ano-base diferente conforme o que já foi divulgado; quando os anos divergem, a comparação mistura períodos — fique atento a isso." |
| `payout_dual` | aba Múltiplos (Analisar) | "**Por que dois payouts?** O *Payout (último ano)* é a fatia do lucro distribuída no exercício mais recente. O *Payout p/ valuation (média 3a)* é a média projetada dos últimos 3 anos (com teto de 100%), e é esse que o modelo de valuation (DDM) usa para estimar o valor justo. Quando os dois divergem, o app mostra ambos para você entender de onde vem o preço-alvo." |
| `indisponivel` | Ranking (opcional) | "**indisponível** — esta empresa foi deixada de fora da regressão de preço-alvo porque faltou ROE ou payout para estimá-la. Não é 'cara' nem 'barata': simplesmente não há dado suficiente para o cálculo." |

Inserir antes do fechamento `}` (`glossario.py:99`), seguindo a organização por seções comentadas (`# ---- Modo Garimpar ----` etc.); sugerido criar um bloco `# ---- Fase 2: ano-base, dual-payout, indisponível ----`. **Não tocar** em `h()` (102-104) — já resolve qualquer chave nova.

**Wiring no app:** usar `help=h("ano_base")` no cabeçalho/coluna do bloco Garimpo/Ranking; `help=h("payout_dual")` no `st.markdown("**Múltiplos...**", help=...)` ou numa caption da aba; `help=h("indisponivel")` opcional.

---

### `tests/test_consistencia_modos.py` (NOVO) — TEST-01 cross-modo

**Analogon:** `tests/test_screening.py` — fixture `_empresa_solida` (linhas 7-26) + estilo de asserção (linhas 29-49).

**Imports a espelhar** (`test_screening.py:1-4`):
```python
from analista.core import screening as sc
from analista.core.fundamentals import CompanyData
```
Para TEST-01 cross-modo, adicionar conforme o caminho exercido:
```python
from analista.core import comparables as cmp
from analista.core import multiples as mult
from analista.report import report
```
(`pythonpath=["src"]` no `pyproject.toml` — imports são `analista.*`, sem `src.`).

**Fixture a espelhar/reusar** (`test_screening.py:7-26`) — `CompanyData` construído à mão, sem rede:
```python
def _empresa_solida(ticker="TAEE11"):
    anos = list(range(2015, 2025))
    c = CompanyData(ticker=ticker, nome="Empresa Sólida", setor="Energia Elétrica", anos=anos)
    for a in anos:
        c.lucro_liquido[a] = 1000 + (a - 2015) * 50
        c.patrimonio_liquido[a] = 4000 + (a - 2015) * 100
        c.dividendos[a] = 600 + (a - 2015) * 30
        c.num_acoes[a] = 1000
        c.vendas_liquidas[a] = 1800
        c.fco[a] = 1200
        c.ativo_circulante[a] = 2000
        c.passivo_circulante[a] = 800
        c.divida_lp[a] = 500
        c.despesa_juros[a] = 100
        c.ativo_intangivel[a] = 200
    c.preco_atual = 30.0
    c.volume_financeiro_diario = 40_000_000
    c.desempenho_relativo_6m = 0.10
    c.beta = 0.8
    return c
```
Reusar este molde (copiar a fixture ou inspirar-se). É a mais completa do harness (10 anos, todos os campos), suficiente para `analisar_acao` rodar até o DDM.

**Carregar `CFG` no teste** — `analisar_acao(c, cfg)` exige `cfg` dict, e **nenhum teste atual carrega cfg** (verificado). Espelhar o loader do `cli.py:27-32` (NÃO o do `app.py`, que tem `@st.cache_data`):
```python
# Source: cli.py:27-32
import os, yaml
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raiz do projeto
def _cfg():
    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)
```
(Alternativa aceitável: cfg mínimo dict inline — ver RESEARCH "Cuidado para o planner". Preferir carregar `config.yaml` real para fidelidade.)

**Asserções de coerência a espelhar** (estilo `test_screening.py:29-49` — `assert <campo> == <esperado>`):
- ROE: `c.roe(c.ultimo_ano())` (caminho Ranking, `app.py:261`) == `report.analisar_acao(c, cfg).multiplos["ROE"]` (caminho Analisar, `report.py:53`). Ambos são `c.roe(ult)` → igualdade exata.
- Payout valuation: `c.payout_valuation()` (Ranking, `app.py:264`) == o usado pelo DDM do Analisar (`report.py:97`). Igualdade exata (mesma função canônica).
- Payout último ano: `c.payout(c.ultimo_ano())` == `analisar_acao(...).multiplos["DP (payout)"]` (`report.py:56`).
- Direção do veredito (Assumption A2): afirmar **sinal** barato/caro coerente entre DDM (`a.veredito` em `report.py:120-124`) e regressão (`PrecoAlvo.subavaliada`), **não** igualdade numérica. O modo Ranking exige ≥4 fixtures para `ajustar_regressao_pl` (`comparables.py:94`) — TEST-01 mínimo pode afirmar só payout/ROE (sem regressão); estendido monta ≥4 empresas.

**Run command** (RESEARCH/pyproject): `.venv/bin/pytest tests/test_consistencia_modos.py -x` e `.venv/bin/pytest tests/ -q` (TEST-02: manter os 44 verdes). Sem `conftest.py` (não existe — não criar).

---

## Shared Patterns (cross-cutting)

### Tooltip via `help=h("chave")`
**Source:** `app.py:17` (`from analista.glossario import h`) + `app.py:68,71,109-113,124,...` + `glossario.py:102-104`.
**Apply to:** ANO-01 (coluna/cabeçalho), PAYOUT-02 (aba Múltiplos), RANK-01 (opcional).
```python
m4.metric("ROE", fmt_pct(a.multiplos.get("ROE")), help=h("roe"))
st.markdown("**Múltiplos (Cap. 10)**", help=h("tab_multiplos"))
```

### Formatação tolerante a None
**Source:** `app.py:48-57`.
**Apply to:** todas as células novas. `fmt_pct`/`fmt_num`/`fmt_rs` devolvem `"—"` para None.
```python
def fmt_pct(x, casas=1): return "—" if x is None else f"{x*100:.{casas}f}%"
def fmt_rs(x, casas=2):  return "—" if x is None else f"R$ {x:,.{casas}f}"...
```
**Exceção LOCKED (RANK-01):** NÃO alterar esses helpers para devolver "indisponível" — a substituição é local no branch `if pa is None:` do Ranking.

### Tabela = `st.dataframe` + dict `rows`
**Source:** `app.py:131,147,177,226,290`.
**Apply to:** ANO-01 (Garimpo/Ranking), PAYOUT-02 (aba Múltiplos).
```python
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
```
Sempre `st.dataframe` (nunca `st.table`); colunas entram pela ordem de inserção no dict. Não introduzir `column_config` que altere larguras/ordem (Pitfall 5).

### Leitura de campo da engine (LOCKED — Fase 1)
**Source:** `app.py:107` (`a.vmin/vmax`), `app.py:264` (`c.payout_valuation()`), `fundamentals.py:54-86`.
**Apply to:** ANO-01 (`c.ultimo_ano()`), PAYOUT-02 (`c.payout(ult)` + `c.payout_valuation()`), RANK-01 (`pa is None`).
A UI **só formata** campos já calculados. Qualquer aritmética de payout/ROE/min-max em `app.py` é bug de regressão.

---

## No Analog Found

Nenhum. Todos os arquivos têm analogon interno (fase deliberadamente aditiva). O único padrão "novo" no repo é carregar `config.yaml` dentro de um teste — mas isso espelha `cli.py:27-32` (loader sem cache), então também tem analogon.

| Item | Observação |
|------|------------|
| `column_config` em tabela | Não usado hoje (Streamlit 1.58.0 suporta). OPCIONAL e só para tooltip/rótulo de coluna — não há analogon no app, seguir padrão `st.dataframe` simples por default. |

---

## Metadata

**Escopo de busca de analogons:** `app.py`, `src/analista/glossario.py`, `src/analista/core/fundamentals.py`, `src/analista/core/comparables.py`, `src/analista/report/report.py`, `src/analista/cli.py`, `tests/` (todos), `pyproject.toml`.
**Arquivos lidos:** 8 (app.py integral; fundamentals 1-100; report 1-60 + grep; glossario integral; test_screening integral; cli via grep; RESEARCH + UI-SPEC integrais).
**Caminho do glossário confirmado:** `src/analista/glossario.py` (dict `G`, acessor `h`).
**Data de extração:** 2026-06-05
