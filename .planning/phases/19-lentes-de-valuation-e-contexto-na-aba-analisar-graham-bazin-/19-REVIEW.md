---
phase: 19-lentes-de-valuation-e-contexto-na-aba-analisar-graham-bazin-
reviewed: 2026-07-02T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/analista/core/lentes.py
  - src/analista/ingest/prices.py
  - src/analista/core/fundamentals.py
  - src/analista/ingest/build.py
  - app.py
  - tests/test_lentes.py
findings:
  critical: 0
  warning: 2
  info: 4
  total: 6
status: issues_found
---

# Phase 19: Code Review Report

**Reviewed:** 2026-07-02
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Revisadas as 4 lentes de valuation/contexto (Graham, Bazin, "quanto teria rendido",
comparador de pares) mais a persistência de Adj Close e o render read-only na aba Analisar.

Avaliação geral: implementação sólida. As lentes puras em `lentes.py` honram o contrato
never-raise (retornam `None` em `None`/≤0/série curta), as fórmulas financeiras conferem
(Graham √(22,5×LPA×VPA), Bazin DPA÷0.06, retorno via Adj Close), e os 11 testes golden
passam no venv (`.venv/bin/python -m pytest tests/test_lentes.py` → 11 passed). O
invariante read-only da UI é majoritariamente respeitado: `app.py` só consome `lentes.*`,
sem recálculo de método. `montar()` degrada para `None` em ticker não resolvível e
`coletar_mercado()` envolve o fetch em `try/except`, então o loop de pares não derruba a aba.

Nenhum Critical. Dois Warnings dizem respeito à FIDELIDADE ao método (Core Value do projeto):
(1) a janela do Bazin pode extrapolar 5 anos-calendário quando há anos faltantes num
histórico de 10 anos; (2) o retorno pode ser rotulado como "com dividendos reinvestidos"
mesmo quando cai no fallback de Close nominal. Os Info são pontos menores de robustez/estilo.

## Warnings

### WR-01: Janela do Bazin pode extrapolar 5 anos-calendário (histórico de 10 anos)

**File:** `src/analista/core/lentes.py:59-69` (integrado em `app.py:838-839`)
**Issue:** `config.yaml` define `anos_historico: 10`, e `app.py` alimenta a lente com TODOS
os anos: `_dpas = [c.dpa(ano) for ano in c.anos_ordenados()]` (até 10 valores). `dpa_medio`
filtra os `None` PRIMEIRO e só então aplica `validos[-n:]` (últimos 5 não-None). Quando há
anos recentes ausentes do dicionário `dividendos` (→ `dpa()` = `None`), a média "dos últimos
5" alcança anos bem mais antigos que 5 anos-calendário, inflando/distorcendo o Preço-Teto de
Bazin — um número que o usuário vê e pode usar. O método clássico é "média dos últimos 5
ANOS". (Anos com dividendo zero vêm como `0.0` e são corretamente incluídos; o risco é só
para anos totalmente ausentes.) O comportamento bate com a docstring/golden, mas diverge da
semântica de Bazin agora que a janela do projeto é 10 anos.
**Fix:** Fatiar por anos-calendário antes de mediar — passar só a janela de 5 anos e então
tratar faltantes, ou no chamador limitar a entrada aos últimos `n` anos:
```python
# app.py — restringir a janela ANTES de chamar a lente
_anos = c.anos_ordenados()[-5:]
_dpas = [c.dpa(ano) for ano in _anos]
_dpa_med = lentes.dpa_medio(_dpas, n=5)
```
Alternativa: `dpa_medio` receber a série alinhada por ano e cortar `[-n:]` sobre os anos
(não sobre os não-None), preservando `None` como "sem dado no ano" dentro da janela.

### WR-02: RET-01 rotulado "com dividendos reinvestidos" mesmo no fallback de Close nominal

**File:** `src/analista/ingest/prices.py:153-155` + rótulo em `app.py:857`
**Issue:** `ajustado = hist["Adj Close"] if "Adj Close" in hist else hist["Close"]`. Quando o
Yahoo não traz a coluna `Adj Close`, `serie_precos_ajustada` recebe o Close NOMINAL. A UI
(`app.py:857`) rotula o resultado como **"Quanto R$ 1.000 teriam rendido (com dividendos
reinvestidos)"**. No fallback, o número é retorno SOMENTE de preço (sem proventos), exibido
sob um rótulo que afirma reinvestimento — mislabel de um número financeiro. Baixa
probabilidade (com `auto_adjust=False` o Yahoo normalmente retorna `Adj Close`), mas a Fase
19 deu a esse fallback um novo significado visível ao usuário.
**Fix:** Não silenciar a ausência de Adj Close para RET-01 — deixar `serie_precos_ajustada`
como `None` quando não houver `Adj Close` real, para a lente degradar (caption neutra) em vez
de exibir retorno price-only rotulado como total:
```python
dm.serie_precos_ajustada = hist["Adj Close"].dropna() if "Adj Close" in hist else None
```
(O fallback para `hist["Close"]` pode continuar servindo beta/desempenho, mas não a RET-01.)

## Info

### IN-01: Aritmética de escala na view fere levemente o invariante read-only

**File:** `app.py:849`
**Issue:** `fmt_rs(p.valor_mercado / 1e9, casas=1) + " B"` faz aritmética (`/1e9`) na camada
de view. É conversão de unidade para display, não fórmula de método, mas o invariante da fase
é "a UI só LÊ". Manter a conversão fora da view reduz ambiguidade.
**Fix:** Encapsular em um helper de formatação (ex.: `fmt_bilhoes(x)`) ou expor o valor já em
bilhões pela engine.

### IN-02: Comparador de pares aceita lista de tickers sem limite nem sanitização

**File:** `app.py:869-878`
**Issue:** O `text_input` de comparáveis é dividido por vírgula/espaço e cada token vira uma
chamada `montar(_t, ...)` (fetch de rede quando não cacheado). Não há teto de quantidade nem
validação de formato de ticker. Um input longo dispara muitas chamadas de rede. Risco de
segurança baixo (tickers vão ao yfinance/CVM, sem uso em path/SQL) e performance está fora do
escopo v1, mas validação de borda é a convenção do projeto.
**Fix:** Limitar a N tickers (ex.: `[:8]`) e descartar tokens fora de um padrão simples de
ticker B3 (`^[A-Z]{4}\d{1,2}$`) antes do loop de `montar`.

### IN-03: Delta do metric exibe "— vs preço" quando o preço atual falta

**File:** `app.py:824-827` e `838-843`
**Issue:** `delta=fmt_pct(lentes.upside(...)) + " vs preço"` — com `preco_atual` `None`,
`upside` retorna `None`, `fmt_pct` retorna "—", produzindo o texto "— vs preço". Sem crash
(`delta_color="off"`), apenas cosmético.
**Fix:** Omitir o `delta` quando `upside(...) is None` para não exibir "— vs preço".

### IN-04: `import pandas as pd` dentro do corpo de `retorno_periodo`

**File:** `src/analista/core/lentes.py:113`
**Issue:** Import tardio de pandas no meio da função. Funciona (e está sob `try/except`), mas
o padrão do módulo é anotar tipos como string e importar no topo/`TYPE_CHECKING`.
**Fix:** Mover o import para o topo do módulo (ou `TYPE_CHECKING` + import local só se
realmente necessário para evitar dependência dura no import da engine).

---

_Reviewed: 2026-07-02_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
