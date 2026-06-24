# Phase 4: Encanamento de dados + série correta - Pattern Map

**Mapped:** 2026-06-24
**Files analyzed:** 4 modified + 1 new test
**Analogs found:** 5 / 5 (todos exatos — o fluxo `serie_precos` da v1.1 é o blueprint 1:1)

## Resumo

Esta fase é **aditiva e puramente mecânica**: replica o fluxo já existente de `serie_precos`
(`DadosMercado` → `montar_empresa` → `CompanyData` → leitura read-only em `app.py`) para um
novo campo `ohlc` (frame OHLCV nominal completo) + uma série/frame **split-adjusted** derivada
por função pura. Não há analog "parecido mas diferente" a buscar: o próprio `serie_precos` é o
template exato. Toda a degradação graciosa (`None` quando `hist` vazio/curto) já está modelada.

## File Classification

| Modified/New File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/analista/ingest/prices.py` | ingest (edge/source) | file-I/O → transform | o próprio `serie_precos` em `coletar_mercado` (mesmo arquivo) | exact (self) |
| `src/analista/ingest/build.py` | builder/assembler | transform (copy field) | `c.serie_precos = dm.serie_precos` (mesmo arquivo) | exact (self) |
| `src/analista/core/fundamentals.py` | model (dataclass) | data carrier | campo `serie_precos` em `CompanyData` (mesmo arquivo) | exact (self) |
| `app.py` | view (Streamlit) | request-response (read-only) | bloco GRAF-03/D-05 `serie = c.serie_precos` (mesmo arquivo) | exact (self) — **só se a fase tocar UI; CONTEXT diz UI é Phase 7** |
| `tests/test_ingest_resolucao.py` (ou novo `tests/test_ingest_ohlc.py`) | test | offline fixture/monkeypatch | `test_serie_precos_*` em `test_ingest_resolucao.py` | exact |

> **Nota de escopo para o planner:** `app.py` aparece nos canonical_refs como *modelo* de
> degradação (`ohlc=None`), mas o `<domain>` do CONTEXT marca UI/overlays como **fora de escopo
> (Phase 7)**. O bloco de `app.py` abaixo é blueprint de **como ler o campo sem quebrar**, não
> um arquivo a editar nesta fase. Editar `app.py` só se o planner decidir um teste de fumaça
> mínimo; caso contrário, deixar intacto.

## Pattern Assignments

### `src/analista/ingest/prices.py` (ingest, source → transform) — onde `ohlc` nasce

**Analog:** o campo `serie_precos` no mesmo arquivo (declaração + atribuição).

**Declaração do campo no dataclass** (`prices.py` linha 58) — replicar para `ohlc` (+ campo ajustado):
```python
    serie_precos: Optional["pd.Series"] = None  # close diário 5a (índice = datas) p/ o gráfico
```
Novo (espelhar a forma `Optional[...] = None` com comentário do mesmo estilo):
```python
    ohlc: Optional["pd.DataFrame"] = None           # frame OHLCV nominal 5a (Yahoo cru, auto_adjust=False)
    ohlc_ajustado: Optional["pd.DataFrame"] = None  # OHLCV split-only-adjusted p/ indicadores (Phase 5)
```
> Nome dos campos é discrição do planner (D-09/Claude's Discretion no CONTEXT). Manter nominal
> e split-adjusted ambos acessíveis e o padrão `Optional[...] = None`.

**Onde o `hist` já está em memória + atribuição atual** (`prices.py` linhas 100-112):
```python
    try:
        hist = tk.history(period="5y", auto_adjust=False)
    except Exception:
        hist = None

    if hist is not None and not hist.empty:
        nominal = hist["Close"].dropna()
        ajustado = hist["Adj Close"] if "Adj Close" in hist else hist["Close"]
        dm.serie_precos = nominal
        if dm.preco_atual is None and len(nominal):
            dm.preco_atual = float(nominal.iloc[-1])
        ult_ano = hist.tail(252)
        dm.volume_financeiro_diario = float((ult_ano["Close"] * ult_ano["Volume"]).mean())
```
**Ponto de inserção do `ohlc`:** dentro do mesmo bloco `if hist is not None and not hist.empty:`,
logo após `dm.serie_precos = nominal`. O `hist` cru já tem todas as colunas — basta preservá-lo:
```python
        dm.serie_precos = nominal
        dm.ohlc = hist                          # frame OHLCV nominal completo (D-01: nada descartado)
        dm.ohlc_ajustado = _ajustar_por_split(hist)  # função pura derivada de "Stock Splits" (D-03/D-05)
```

**Função pura de ajuste por split** (NOVA — DATA-02/D-03/D-05; helper neste arquivo, à imagem
de `_retornos_mensais` linhas 61-65 que já é helper puro de transform sobre série de preços):
```python
def _retornos_mensais(precos) -> list:
    """Retornos mensais a partir de uma série de preços (ajustada p/ beta)."""
    mensal = precos.resample("ME").last()
    ret = mensal.pct_change().dropna()
    return list(ret.values)
```
Replicar esse contrato (função module-level, pura, mockável, `import pandas as pd` tardio como
nas linhas 136/146): assinatura `_ajustar_por_split(hist: "pd.DataFrame") -> "pd.DataFrame"`.
Regra de negócio (D-05): fator de split **cumulativo** a partir da coluna `Stock Splits`;
multiplica `Open/High/Low/Close`, divide `Volume`; fator = 1 após o último split (ponta recente
coincide com nominal). **NÃO** usar `Adj Close` (mistura proventos — anti-pattern explícito).

**Degradação (edge layer valida)** — o `try/except` + guard `if hist is not None and not hist.empty`
já cobrem `ohlc`/`ohlc_ajustado`: ficam `None` quando o fetch falha/vazio (linhas 100-105). Nada
a adicionar além de não atribuir dentro de hist vazio. Para "histórico curto", a função pura deve
tolerar frame curto sem estourar (retornar o frame ajustado mesmo curto, ou `None` se vazio).

---

### `src/analista/ingest/build.py` (builder, transform/copy)

**Analog:** `c.serie_precos = dm.serie_precos` no mesmo arquivo.

**Bloco de cópia de campos de mercado** (`build.py` linhas 35-42):
```python
    c.preco_atual = dm.preco_atual
    c.volume_financeiro_diario = dm.volume_financeiro_diario
    c.beta = dm.beta
    c.desempenho_relativo_6m = dm.desempenho_relativo_6m
    c.dpa_trailing_12m = dm.dpa_trailing_12m  # DY corrente trailing-12m (WR-04)
    c.ano_dpa = dm.ano_dpa
    c.serie_precos = dm.serie_precos
    c.eh_concessionaria = any(t.lower() in (c.setor or "").lower() for t in setores_concessionaria)
```
**Inserir** (após `c.serie_precos = dm.serie_precos`, mesma forma 1:1 — D-02):
```python
    c.serie_precos = dm.serie_precos
    c.ohlc = dm.ohlc
    c.ohlc_ajustado = dm.ohlc_ajustado
```
Sem lógica condicional: cópia direta (campos já são `None` quando ausentes na origem).

---

### `src/analista/core/fundamentals.py` (model, data carrier)

**Analog:** campo `serie_precos` no dataclass `CompanyData`.

**Declaração atual** (`fundamentals.py` linha 45, na seção "snapshot atual / mercado" linhas 38-49):
```python
    # snapshot atual / mercado
    preco_atual: Optional[float] = None
    volume_financeiro_diario: Optional[float] = None  # média R$/dia
    desempenho_relativo_6m: Optional[float] = None     # excesso de retorno vs Ibov
    g_lucro_esperado: Optional[float] = None           # crescimento esperado LP (analistas)
    beta: Optional[float] = None
    eh_concessionaria: bool = False
    serie_precos: Optional["pd.Series"] = None  # close diário 5a (índice = datas) p/ o gráfico
```
**Inserir** (após `serie_precos`, mesmo estilo de comentário/typing — D-02):
```python
    serie_precos: Optional["pd.Series"] = None  # close diário 5a (índice = datas) p/ o gráfico
    ohlc: Optional["pd.DataFrame"] = None           # frame OHLCV nominal 5a (Yahoo cru)
    ohlc_ajustado: Optional["pd.DataFrame"] = None  # OHLCV split-only-adjusted p/ indicadores (Phase 5)
```
Nenhum método de `CompanyData` precisa mudar — o campo é só carregado e lido downstream.

---

### `app.py` (view, read-only) — BLUEPRINT de leitura, NÃO necessariamente editar nesta fase

**Analog:** bloco GRAF-03/D-05 de degradação graciosa.

**Padrão a espelhar quando alguém ler `ohlc`** (`app.py` linhas 135-141):
```python
            serie = c.serie_precos
            if serie is None or len(serie) == 0:
                # D-05/GRAF-03: série indisponível → aviso sem quebrar a aba (espelha o aviso de preço atual)
                st.info(
                    "📉 Gráfico de preço indisponível agora (fonte Yahoo instável). Os fundamentos e o "
                    "valor intrínseco (DDM, dados CVM) abaixo seguem válidos."
                )
            else:
                ...  # usa a série
```
Modelo direto para `ohlc=None` (D-06): `frame = c.ohlc; if frame is None or frame.empty: <aviso
neutro / pular>; else: <usar>`. **Reforço de escopo:** o consumo real de `ohlc` na UI é Phase 7;
aqui este excerto é só o contrato de degradação que a fase precisa honrar (campo ausente não estoura).

---

### `tests/test_ingest_ohlc.py` (novo) ou anexar a `tests/test_ingest_resolucao.py` (test, offline)

**Analog:** `test_serie_precos_usa_close_nominal` + `test_serie_precos_none_quando_hist_vazio`
(`test_ingest_resolucao.py` linhas 91-132).

**Fixture de hist falso + stub do Ticker** (linhas 91-104) — estender com `Stock Splits` p/ exercitar D-05:
```python
def _hist_fake():
    idx = pd.date_range("2021-01-01", periods=300, freq="D")
    close = pd.Series(range(100, 400), index=idx, dtype=float)   # nominal
    adj = close * 0.5                                            # retroajustado != nominal
    return pd.DataFrame({"Close": close, "Adj Close": adj, "Volume": 1000.0})


class _TkComHist:
    def history(self, *a, **k):
        return _hist_fake()

    @property
    def dividends(self):
        return pd.Series(dtype=float)
```
Para os testes de `ohlc`: adicionar colunas `Open/High/Low` e uma `Stock Splits` com 1 evento
(ex.: fator 2.0 numa data intermediária) para validar que a ponta recente da série ajustada
coincide com a nominal (fator=1 pós-último split) e que datas anteriores ficam escaladas pelo
fator cumulativo, sem saltos espúrios.

**Padrão de monkeypatch do yfinance** (linhas 109-116) — reutilizar tal qual:
```python
    class _YF:
        @staticmethod
        def Ticker(sym):
            return _TkComHist()

    monkeypatch.setattr(prices, "_yf", lambda: _YF())
    monkeypatch.setattr(prices.time, "sleep", lambda *_: None)
    monkeypatch.setattr(prices, "_fetch_info", lambda tk: {})
```

**Padrão de asserção de degradação** (linhas 126-132) — replicar para `ohlc`:
```python
def test_serie_precos_none_quando_hist_vazio(monkeypatch):
    """Sem histórico (Yahoo falha/vazio), serie_precos fica None — fallback da Tela 1."""
    _stub_yf(monkeypatch)  # _TkStub.history retorna DataFrame vazio
    monkeypatch.setattr(prices.time, "sleep", lambda *_: None)
    monkeypatch.setattr(prices, "_fetch_info", lambda tk: {"shortName": "Z", "regularMarketPrice": 5.0})
    dm = prices.coletar_mercado("ZZZ3")
    assert dm.serie_precos is None
```
Novos testes a escrever: (1) `ohlc` é o frame cru completo quando há hist; (2) `ohlc is None` /
`ohlc_ajustado is None` quando hist vazio (D-06); (3) `_ajustar_por_split` é pura e produz ponta
recente == nominal e fator cumulativo correto nas datas pré-split (D-05); (4) sem coluna
`Stock Splits` ou 0 eventos → ajustado == nominal.

## Shared Patterns

### Degradação na borda (edge layer valida; engine não)
**Source:** `src/analista/ingest/prices.py` linhas 100-105 (`try/except` + guard `if hist is not
None and not hist.empty`).
**Apply to:** `prices.py` (`ohlc`, `ohlc_ajustado`), `build.py` (cópia direta de campos `None`),
`app.py` (leitura `if frame is None or frame.empty`).
```python
    try:
        hist = tk.history(period="5y", auto_adjust=False)
    except Exception:
        hist = None
    if hist is not None and not hist.empty:
        ...
```

### Campo `Optional[...] = None` com comentário curto explicando origem/uso
**Source:** `prices.py:58` e `fundamentals.py:45` (`serie_precos`).
**Apply to:** declarações de `ohlc` / `ohlc_ajustado` em ambos os dataclasses. Manter o estilo:
tipo entre aspas para forward-ref de pandas (`Optional["pd.DataFrame"]`), comentário inline em PT.

### Helper puro module-level para transform sobre preços
**Source:** `prices.py:61-65` (`_retornos_mensais`) — função pura, recebe série/frame, retorna
estrutura derivada, sem efeitos colaterais, `import pandas as pd` tardio dentro do escopo que usa.
**Apply to:** `_ajustar_por_split(hist) -> pd.DataFrame`. Mantém testabilidade offline (D-03 "função
pura e testável").

### Import tardio de pandas (dependência pesada)
**Source:** `prices.py:136` e `:146` (`import pandas as pd` dentro da função).
**Apply to:** qualquer uso de pandas em `_ajustar_por_split` se precisar de API pandas explícita;
caso a manipulação seja só sobre o `hist` já recebido, o `import` pode ficar local ao helper.

### Testes offline via monkeypatch (zero rede)
**Source:** `test_ingest_resolucao.py:25-31, 109-116` (`monkeypatch.setattr(prices, "_yf", ...)`,
`_fetch_info`, `time.sleep`).
**Apply to:** todos os novos testes de `ohlc` / `_ajustar_por_split`.

## No Analog Found

Nenhum. Todo arquivo desta fase tem analog **exato** no próprio fluxo `serie_precos` da v1.1.
A única peça genuinamente nova — a função `_ajustar_por_split` — não tem analog idêntico, mas
herda o **contrato** do helper puro `_retornos_mensais` (assinatura, pureza, testabilidade,
import tardio de pandas). O planner deve tratá-la como nova lógica de negócio (regra de split
cumulativo, D-05), não como cópia mecânica.

## Invariante (TEST-07)

**Source:** suíte em `tests/` (7 arquivos; 64 golden tests de valuation).
**Apply to:** verificação final da fase — rodar `pytest` ao final. Como `ohlc`/`ohlc_ajustado`
são campos aditivos e nenhuma fórmula do livro muda, a suíte deve permanecer verde sem alteração
(D-07).

## Metadata

**Analog search scope:** `src/analista/ingest/`, `src/analista/core/`, `app.py`, `tests/`
**Files scanned:** 5 (prices.py, build.py, fundamentals.py, app.py [linhas 110-160], test_ingest_resolucao.py) + listagem de `tests/`
**Pattern extraction date:** 2026-06-24
