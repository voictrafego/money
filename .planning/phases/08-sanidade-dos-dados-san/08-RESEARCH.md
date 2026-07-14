# Phase 08: Sanidade dos dados (SAN) — Research

**Researched:** 2026-07-14
**Domain:** Validação de dados financeiros (CVM DFP + Yahoo/yfinance), detecção sem correção
**Confidence:** HIGH (quase tudo foi **medido** contra os dados reais do projeto, não lembrado)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01..D-15 — NÃO re-litigar)

**Onde o diagnóstico mora**
- **D-01:** Os avisos viram **campos no `CompanyData`** (`src/analista/core/fundamentals.py:20`): `c.avisos` (lista de flags disparadas) + `c.confianca` (síntese).
- **D-02:** Quem popula é uma **função explícita `aplicar_sanidade(c)`** — a lógica dos 7 checks vive isolada e testável, e **não** roda automaticamente dentro de `montar_empresa`.
- **D-03:** O default de `c.confianca` é **`nao_avaliada`**, nunca `alta`.
- **D-04:** A chamada é **provada por execução**: um teste roda o pipeline real de ponta a ponta e exige que a saída **não** esteja `nao_avaliada`.

**O baseline dos sujos**
- **D-05:** Um **baseline versionado** congela, por ticker, **quais flags disparam hoje** — nunca um R$, nunca um preço. Golden de **detecção**, não de nível.
- **D-06:** **Regra da monotonicidade**: a lista de sujos só pode **encolher**.
- **D-07:** O baseline registra **flag + ordem de grandeza (bucket)**, não a magnitude exata.
- **D-08:** Baseline e checks rodam sobre um **snapshot congelado dos 104 tickers, capturado nesta fase com o dado SUJO**, versionado. Determinístico e offline.

**Limiares**
- **D-09:** Limiares **folgados**. SAN-01 dispara com desvio **> 50%** (fator ≥ 1,5×).
- **D-10:** Limiares são **constantes no módulo de sanidade** — **não** vão para `config.yaml`, **não** entram no `calibracao.lock.yaml`.
- **D-11:** Um teste **congela os valores dos limiares**.
- **D-12:** SAN-02 usa **limiar alto + os `.splits` do Yahoo como isenção**.

**Veredito**
- **D-13:** `c.confianca` é escala discreta: `alta` / `media` / `baixa` / `nao_avaliada`. **Nada de score numérico 0-100.**
- **D-14:** O veredito é **interno nesta fase**. Nada muda na tela do app.

**SAN-07**
- **D-15:** Entregável = **documento em `.planning/spikes/` + a medição nos dados reais dos bancos**. Nenhum knob é movido.

### Claude's Discretion
- Nome e localização exatos do módulo de sanidade, formato de serialização do baseline e do snapshot, estrutura interna do objeto de aviso.
- Os limiares específicos de **SAN-02..SAN-05** (o de SAN-01 está fixado em >50% por D-09).

### Deferred Ideas (OUT OF SCOPE)
- Exibir o selo de confiança na tela — Fase 13.
- Cindir as 19 funções mistas restantes (gap WR-04) — antes da Fase 10, não agora.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Descrição (REQUIREMENTS.md:84-96) | Suporte da pesquisa |
|----|-----------------------------------|---------------------|
| SAN-01 | `num_acoes × preço ≈ market cap`; pega GOAU4 (3×) e CGRA4 (1000×) | **MEDIDO e CONFIRMADO** — GOAU4 = 2,969× / CGRA4 = 0,001×. Referência (`marketCap/preço`) validada contra a CVM com erro < 0,3%. §Achado 3 |
| SAN-02 | Salto de `num_acoes` ano-a-ano sem evento societário; pega ITUB4 2019 (1.131×) e BRSR6 (205.000×) | **PARCIALMENTE CONTRADITO** — BRSR6 confirmado (205.099×); **o "1.131×" do ITUB4 2019 NÃO EXISTE**: o salto real é **0,0010× (÷1000)**. §Achado 2 e §Risco R-01 |
| SAN-03 | `dividendos_CVM ≈ DPA_yahoo × num_acoes`; pega o JCP perdido | Insumos existem (`cvm.py:245` + `prices.py:198`). §Achado 8 |
| SAN-04 | `PL` e `lucro` na mesma base; pega MRFG3, CSNA3, ALUP11, EQTL3 | **MECÂNICA PROVADA** (minoritários) — mas exige **ler contas novas na CVM** (`3.11.01`, `2.0X.0X`). §Achado 4 |
| SAN-05 | Clean surplus (`ΔB ≈ LL − DIV`) reportado como dado | Insumos existem. A DRA quantifica o resíduo. §Achado 7 |
| SAN-06 | Nenhum assert levanta exceção (never-raise) | **Caso real vivo**: MRFG3 dá **404 no Yahoo hoje**. §Risco R-03 |
| SAN-07 | IHCD/AT1 no PL dos bancos (`2.03`)? Dirty surplus FVOCI material? | **PREMISSA FALSA** — `2.03` **não é o PL de nenhum banco**. Spike respondido com medição. §Achado 6 e §Risco R-02 |
</phase_requirements>

---

## Summary

A pesquisa foi feita **rodando código contra os dados reais do projeto** (cache CVM 2015-2025 completo em `data/cvm/`, yfinance 1.4.1, 104 tickers em `data/ticker_map.json`). Quase nada aqui é lembrado; quase tudo é medido.

O resultado central é que **a doença dos 41 tickers tem uma causa-raiz única e agora está completamente caracterizada**: `cvm.py:242` extrai a conta `3.99.01.01` ("Lucro Básico por Ação — ON") sem validar escala nem base, e `build.py:87` divide `lucro_liquido / lpa` para inventar `num_acoes`. Três patologias distintas saem daí, e cada uma explica exatamente um dos tickers que o ROADMAP nomeia. **Três premissas travadas do CONTEXT/ROADMAP não sobrevivem à medição** — estão em §Riscos, e o planner precisa encará-las antes de escrever a primeira task.

A boa notícia: **a decisão D-12 (isenção por `.splits`) sobrevive** — foi a pergunta que mais me pediram para verificar, e a resposta é que a isenção **não** mata o SAN-02. E o SAN-01, como especificado, é um detector genuinamente confiável: sua referência (`marketCap/preço` do Yahoo) concorda com a contagem oficial da CVM com erro **< 0,3% em 5 de 5 tickers testados**.

**Primary recommendation:** Implemente os 7 checks como funções puras sobre `CompanyData` num módulo novo (`src/analista/core/sanidade.py`), rodando sobre um snapshot congelado que **precisa incluir 3 campos que hoje não existem no pipeline** (`marketCap`, `impliedSharesOutstanding`, `splits` de histórico completo) e **2 contas CVM que hoje não são lidas** (`3.11.01` lucro do controlador, `2.0X.0X` participação de não-controladores). Sem esses 5 insumos, SAN-01/SAN-02/SAN-04 não são implementáveis.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Os 7 checks (aritmética pura) | `core/sanidade.py` (novo) | — | Funções puras sobre `CompanyData`; testáveis sem rede. Espelha `core/normalizacao.py`. |
| Campos `avisos` / `confianca` | `core/fundamentals.py` (`CompanyData`) | — | D-01. O objeto que já atravessa ingest→motores→app carrega o diagnóstico. |
| Chamada de `aplicar_sanidade(c)` | `ingest/build.py` (`montar_empresa`) | — | D-02/D-04: ponto único, provado por execução. |
| Insumos novos da CVM (`3.11.01`, minoritários) | `ingest/cvm.py` (`fundamentos_do_ano`) | — | **Leitura nova**, não conserto. SAN-04 é impossível sem ela. |
| Insumos novos do Yahoo (`marketCap`, `impliedSO`, `splits`) | `ingest/prices.py` (`coletar_mercado` / `DadosMercado`) | — | **Leitura nova**, não conserto. SAN-01/SAN-02 impossíveis sem ela. |
| Snapshot congelado dos 104 | `scripts/capturar_snapshot_sujo.py` (novo) | `tests/fixtures/` | D-08. Reaproveita a FORMA de `capturar_snapshot_bancos.py`. |
| Baseline `ticker → flags` | `tests/fixtures/baseline_sanidade.yaml` | `tests/test_sanidade_baseline.py` | D-05/D-06/D-07. **Fora do .py** para não acordar o BLIND-04a — §Achado 9. |
| Relatório CLI | `scripts/` ou `cli.py` | — | D-14. Ferramenta de trabalho da Fase 9. |
| Spike contábil | `.planning/spikes/` | — | D-15. Documento + medição. |

---

## Environment Availability

Medido em 2026-07-14 na máquina do projeto.

| Dependência | Requerida por | Disponível | Versão | Observação |
|-------------|--------------|-----------|--------|------------|
| Python | tudo | ✓ | **3.14.5** | |
| yfinance | SAN-01/02/03 | ✓ | **1.4.1** | `requirements.txt` pede `>=0.2.40`; a instalada é muito mais nova |
| pandas | tudo | ✓ | **3.0.3** | |
| PyYAML | snapshot/baseline | ✓ | — | já usado por `capturar_snapshot_bancos.py:23` |
| pytest | malha de testes | ✓ | — | config em `pyproject.toml` |
| Cache CVM | SAN-03/04/05/07 | ✓ | 2015–2025 | `data/cvm/dfp_cia_aberta_{2015..2025}.zip` + `cad_cia_aberta.csv` — **todos os 11 anos presentes; a fase roda 100% offline no lado CVM** |
| Rede Yahoo | captura do snapshot | ✓ (parcial) | — | **MRFG3.SA retorna 404** — ver §Risco R-03 |

**Nenhuma dependência nova é necessária.** Os 7 checks são aritmética sobre dicts `{ano: float}`. Confirma a proibição do CONTEXT de instalar `pandera`/`great-expectations`.

---

## Achados Medidos

Todos os blocos abaixo são **saída real de execução**, não memória. Comandos rodados com `PYTHONPATH=src` contra o cache CVM e o yfinance instalado.

### Achado 1 — A causa-raiz única: a conta `3.99.01.01` da CVM

`cvm.py:242-243` extrai o LPA assim:

```python
"lpa": _valor_conta(dre, cd_cvm, ["3.99.01.01", "3.99.01"],
                    ["Lucro por Ação"], aplicar_escala=False),
```

E `build.py:87` faz:

```python
contagem_cvm[ano] = abs(f["lucro_liquido"] / lpa_cvm)
```

Dump real das contas `3.99*` da DRE (**medido**):

| ticker/ano | `3.99.01.01` (o que o parser pega) | LPA real | patologia |
|---|---|---|---|
| ITUB4 2019 | **2780.0** | ≈ 2,78 | **×1000** — o filer expressou o LPA por LOTE DE MIL AÇÕES |
| ITUB4 2018 | 2.56 | 2,56 | saudável |
| CGRA4 2025 | **4032.0** | ≈ 4,03 | **×1000** |
| BRSR6 2020 | **310665.0** | ≈ 1,51 | **semântica errada** — ver abaixo |

O caso BRSR6 2020 é o mais grave e **não é um erro de escala**:

```
  CD_CONTA     DS_CONTA                   VL_CONTA
  3.99         Lucro por Ação (R$/Ação)   1239344.0
  3.99.01      Lucro Básico por Ação       619672.0    <- = LL em R$ MIL (!)
  3.99.01.01   ON                          310665.0    <- lucro ALOCADO à classe ON, em R$ mil
  3.99.01.02   PNA                           2184.0
  3.99.01.03   PNB                         306823.0
```

`310.665 + 2.184 + 306.823 = 619.672` — que é o **lucro líquido em R$ mil** (LL real = R$ 619.864 mil). O BRSR6 **não preencheu LPA nenhum**: preencheu o *lucro atribuído a cada classe de ação*, em milhares, sob o cabeçalho "Lucro por Ação". O parser lê `3.99.01.01` como se fosse R$/ação.

**Quatro patologias, todas nascendo da mesma linha:**
1. **Escala ×1000** (ITUB4 2019, CGRA4 2025) — LPA multiplicado por mil.
2. **Semântica trocada** (BRSR6 2020) — a subconta contém lucro alocado, não LPA.
3. **Zero/ausente** (CGRA4 2016-2019, EQTL3 2018-2024, ALUP11 2016-2018) — `3.99.01.01 = 0.0` → `if lpa_cvm and ...` (build.py:86) é **falsy** → cai para `acoes_atual` do Yahoo (`build.py:101-102`) → **a série mistura bases dentro do mesmo ticker**.
4. **Base cruzada** (GOAU4, CSNA3, EQTL3, ALUP11, MRFG3) — LL consolidado ÷ LPA do controlador. §Achado 4.

> **Para o planner:** esta fase **não conserta nada disso** (ROADMAP, inegociável). Mas conhecer a causa-raiz muda o desenho dos checks: SAN-01 e SAN-02 são detectores *do mesmo bug visto de dois ângulos* (nível vs. série temporal). Documente isso no módulo — é o que impede a Fase 9 de "consertar" um e achar que consertou os dois.

---

### Achado 2 — A série real de `num_acoes` (o que o SAN-02 tem que enxergar)

`contagem_cvm = |LL/LPA|` por ano, **medido** (janela 2016-2025, `ano_base=2025`, `config.yaml:6`):

**ITUB4** (CD_CVM 19348):
```
  2016: n=      6.605.602.241  LPA=      3,5700
  2017: n=      6.594.565.217  LPA=      3,6800   salto=      0,9983x
  2018: n=     10.015.234.375  LPA=      2,5600   salto=      1,5187x  <<<<
  2019: n=         10.004.676  LPA=   2780,0000   salto=      0,0010x  <<<< (÷1000)
  2020: n=      7.805.181.347  LPA=      1,9300   salto=    780,1533x  <<<<
  2021: n=     10.359.124.088  LPA=      2,7400   salto=      1,3272x
  2022: n=     10.144.224.422  LPA=      3,0300   salto=      0,9793x
  2023: n=     10.022.781.065  LPA=      3,3800   salto=      0,9880x
  2024: n=     10.030.476.190  LPA=      4,2000   salto=      1,0008x
  2025: n=     11.320.740.741  LPA=      4,0500   salto=      1,1286x
```

**BRSR6** (CD_CVM 1210):
```
  2019: n=        409.660.323  LPA=      3,1000   salto=      1,0009x
  2020: n=              1.995  LPA= 310665,0000   salto=      0,0000x  <<<<
  2021: n=        409.232.075  LPA=      2,6500   salto= 205.099,9618x  <<<<
  2022..2025: ~409M, saltos ≈ 1,00x
```

**CGRA4** (CD_CVM 4537):
```
  2016-2019: LPA=0.0 -> SEM contagem (cai p/ acoes_atual do Yahoo)
  2020: n=         20.147.582  LPA=      3,5239
  2024: n=         20.858.880  LPA=      5,0170   salto=      1,0386x
  2025: n=             20.797  LPA=   4032,0000   salto=      0,0010x  <<<< (÷1000)
```

**Três consequências de desenho que o planner PRECISA saber:**

**(a) O salto aparece DUAS vezes — na entrada e na saída do ano quebrado.** BRSR6: `0,0000×` em 2020 (a queda) e `205.099×` em 2021 (a recuperação). ITUB4: `0,0010×` em 2019 e `780×` em 2020. **O SAN-02 tem que ser SIMÉTRICO** — `max(n_t/n_{t-1}, n_{t-1}/n_t) > limiar` — senão um check que só olha *aumento* pega o ano errado (o ano são, seguinte) e deixa o ano doente passar.

**(b) O ano quebrado do CGRA4 é 2025 = `ultimo_ano()`.** É exatamente o ano que `lpa_valuation()` (`fundamentals.py:135`) e `num_acoes.get(ultimo_ano)` consomem. O bug está no ano que mais importa.

**(c) A série do EQTL3 mistura TRÊS bases:** 2016-2017 da CVM (~240M), 2018-2024 do Yahoo (constante, via fallback do `build.py:102`), 2025 da CVM (1,877bn). Um check de salto sobre essa série produz um salto artificial na fronteira do fallback. **O SAN-02 precisa saber DE ONDE veio cada ano** (CVM vs. fallback Yahoo) para não confundir "salto de dado" com "troca de fonte". Sugestão: `montar_empresa` já sabe (`if ano in contagem_cvm` vs `elif acoes_atual`, build.py:99-102) — basta carimbar a origem.

---

### Achado 3 — SAN-01 medido: a referência é sólida, e os dois alvos caem certinho

**`marketCap` do Yahoo = `preço × impliedSharesOutstanding`** (verificado exato para ITUB4: 479.671.877.632 / 43,52 = 11.021.872.542 = `impliedSharesOutstanding` na casa da unidade).

Fator SAN-01 medido = `n_cvm(2025) × preço / marketCap`:

| ticker | preço | sharesOutstanding | impliedSharesOut. | marketCap | n=LL/LPA (2025) | **fator SAN-01** |
|---|---|---|---|---|---|---|
| ITUB4 | 43,52 | 5.404.129.565 | 11.021.872.542 | 479.671.877.632 | 11.320.740.741 | **1,027** |
| BRSR6 | 14,41 | 202.536.545 | 408.974.477 | 5.893.321.728 | 409.200.716 | **1,001** |
| **GOAU4** | 10,12 | 836.071.784 | 1.322.874.548 | 13.387.489.280 | 3.927.011.111 | **2,969** ✅ |
| **CGRA4** | 24,41 | 14.690.757 | 25.450.092 | 621.236.736 | 20.797 | **0,001** ✅ |
| CSNA3 | 5,24 | 1.326.093.947 | 1.326.093.947 | 6.948.731.904 | 997.845.005 | **0,752** |
| EQTL3 | 40,21 | 1.254.916.065 | 1.254.916.065 | 50.460.176.384 | 1.876.995.675 | **1,496** ⚠️ |
| ALUP11 | 33,71 | 329.626.866 | 475.656.000 | 16.034.363.392 | 1.394.236.754 | 2,931 (pré-unit) |
| MRFG3 | — | — | — | — | 2.139.941.077 | **404 no Yahoo** ⚠️ |

**GOAU4 = 2,969× e CGRA4 = 0,001× — o SAN-01, exatamente como especificado no REQUIREMENTS, pega os dois alvos com folga enorme.** E ITUB4/BRSR6 (saudáveis em 2025) ficam em 1,03 e 1,00 — **zero falso positivo**. O limiar de D-09 (fator ≥ 1,5) está bem colocado para o que o SAN-01 promete.

> **Use `impliedSharesOutstanding`, nunca `sharesOutstanding`.** O `sharesOutstanding` é só a classe negociada (ITUB4: 5,4bn = só as PN); o `impliedSharesOutstanding` é ON+PN (11,02bn). A contagem da CVM (`LL/LPA`) é ON+PN. Comparar com `sharesOutstanding` produziria um falso positivo de ~2× em toda empresa com PN. O `prices.py:136` hoje só lê `sharesOutstanding`.

---

### Achado 4 — SAN-04: a mecânica dos minoritários, PROVADA, e a conta que falta

Dump real da DRE 2025 (**medido**):

| ticker | `3.11` LL consolidado | `3.11.01` **Atribuído ao Controlador** | `3.11.02` Não-controladores | `3.99.01.01` LPA | razão `3.11 / 3.11.01` |
|---|---|---|---|---|---|
| **GOAU4** | 1,4137 bi | **0,4765 bi** | 0,9372 bi | 0,36 | **2,967×** |
| **EQTL3** | 2,5039 bi | **1,6784 bi** | 0,8256 bi | 1,3340 | **1,492×** |
| **ALUP11** | 1,7332 bi | **1,2156 bi** | 0,5176 bi | 1,2431 | **1,426×** |
| **CSNA3** | −1,5067 bi | **−2,0024 bi** | +0,4956 bi | −1,5100 | **0,752×** (sinal invertido!) |

**A prova fecha em dois lugares independentes:**
- GOAU4: razão dos minoritários = **2,967×**; fator SAN-01 medido = **2,969×**. É o mesmo número. **O "3× do GOAU4" É o bug de minoritários** — a Metalúrgica Gerdau é uma holding que consolida a Gerdau S.A. e detém ~1/3 dela.
- CSNA3: razão = **0,752×**; fator SAN-01 medido = **0,752×**. Idem. E o CSNA3 é o **caso de sinal invertido**: os minoritários tiveram lucro (+0,496) enquanto o controlador teve prejuízo (−2,002) — então o LL consolidado é *menos negativo* que o do controlador e a contagem sai para **baixo**, não para cima.

**Validação cruzada contra a contagem oficial de ações da CVM** (`dfp_cia_aberta_composicao_capital_2025.csv`, dentro do próprio ZIP que o projeto já baixa — chaveado por **`CNPJ_CIA`**, não por `CD_CVM`):

| ticker | ON+PN em circulação (CVM) | `n = LL/LPA` (hoje) | **erro** |
|---|---|---|---|
| ITUB4 | 11.026.524 *(em MILHARES)* | 11.320.740.741 | 1026,7× |
| BRSR6 | 408.974 *(em MILHARES)* | 409.200.716 | 1000,6× |
| GOAU4 | 1.324.905.265 | 3.927.011.111 | **2,964×** |
| CGRA4 | 23.543.718 | 20.797 | **0,001×** |
| CSNA3 | 1.326.093.947 | 997.845.005 | **0,752×** |
| EQTL3 | 1.258.124.081 | 1.876.995.675 | **1,492×** |
| ALUP11 | 988.880.601 | 1.394.236.754 | 1,410× |
| MRFG3 | 1.408.793.018 | 2.139.941.077 | **1,519×** |

E o `impliedSharesOutstanding` do Yahoo bate com essa contagem oficial com erro **< 0,3% em 5 de 5**:
- BRSR6: 408.974.477 vs 408.974.000 → **0,0001%**
- CSNA3: 1.326.093.947 vs 1.326.093.947 → **exato**
- ITUB4: 11.021.872.542 vs 11.026.869.000 → 0,05%
- GOAU4: 1.322.874.548 vs 1.324.905.265 → 0,15%
- EQTL3: 1.254.916.065 vs 1.258.124.081 → 0,26%

> **A referência do SAN-01 é confiável.** Isso não é um palpite — é a concordância de duas fontes independentes (Yahoo e CVM) em cinco tickers.

**O que FALTA no parser:** `cvm.py:213-218` lê **só** `3.11`/`3.13`/`3.09` (o LL consolidado). **`3.11.01` (lucro do controlador) NÃO é lido.** Sem ele, **SAN-04 não é implementável**. Idem no lado do PL: a participação de não-controladores está em `2.03.09` (empresas), `2.07.02` (BBAS3/BBDC4/BRSR6) ou `2.08.09` (ITUB4) — **nenhuma é lida hoje**.

> Adicionar uma **leitura** não é consertar dado. `lucro_liquido` continua sendo o consolidado; o novo campo é insumo de diagnóstico. Isso respeita o "NÃO consertar nada" do ROADMAP. Mas é uma mudança real em `cvm.py` que o planner precisa orçar numa task.

**Limiar sugerido para SAN-04** (área de discricionariedade — D-09 só travou o SAN-01): `|3.11/3.11.01 − 1| > 10%`. Pega os 4 nomeados (26%..197%) e deixa os bancos limpos (ITUB4 minoritários = 4,9% do PL; BBAS3 = 2,3%; BBDC4 = 0,3%; BRSR6 = 0,04%).

---

### Achado 5 — `.splits` do yfinance: a resposta à pergunta do D-12

**yfinance 1.4.1**, medido ao vivo.

**Forma do retorno de `yfinance.Ticker(s).splits`:**
- Tipo: `pandas.Series`. **Nunca `None`** — quando não há split, vem uma **Series VAZIA**.
- Index: `DatetimeIndex`, **tz-aware** (`America/Sao_Paulo`).
- Valor: `float` (o fator). `name = "Stock Splits"`.
- ⚠️ **Pegadinha de dtype:** com splits, `dtype=float64`. **Sem splits (Series vazia), `dtype=object`.** Código que faça operação numérica direta na série vazia quebra. Trate o caso vazio explicitamente.

**Os dados reais:**

```
ITUB4.SA  (12 splits)
  2004-10-20 fator=0.001     2016-10-18 fator=1.1
  2005-10-03 fator=10.0      2018-11-21 fator=1.5     <-- REAL, e load-bearing
  2007-10-01 fator=2.0       2025-03-18 fator=1.1
  2008-06-02 fator=1.25      2025-12-26 fator=1.03
  2009-08-31 fator=1.1
  2013-05-21 fator=1.1       *** NENHUM SPLIT EM 2019 ***
  2014-06-06 fator=1.1
  2015-07-14 fator=1.1

BRSR6.SA  -> Series VAZIA (len 0). Nenhum split, nunca.

GOAU4.SA  (7 splits) ... 2008-06-13 fator=2.0 ; 2025-12-19 fator=1.3333
CGRA4.SA  (2 splits) 2008-09-25 fator=4.0 ; 2025-12-23 fator=1.163789271344117
```

**VEREDITO SOBRE O D-12 — a isenção NÃO mata o SAN-02:**
- **ITUB4 2019: o `.splits` NÃO registra nada em 2019.** A flag do salto `0,0010×` **dispara e não é isenta**. ✅
- **BRSR6: o `.splits` está VAZIO.** A flag do salto `205.099×` **dispara e não é isenta**. ✅

**A isenção do D-12 é NECESSÁRIA, e é load-bearing exatamente uma vez:**
- **ITUB4 2018 salta 1,5187×** — acima do limiar. E existe um split **real** em `2018-11-21 = 1,5` (a bonificação de 50% do Itaú). **Sem a isenção, o ITUB4 2018 seria um FALSO POSITIVO.** A isenção o suprime corretamente.
- Isso confirma o raciocínio por trás do D-12: **splits/bonificações realmente mexem na série da CVM**, porque `_ler_demonstracao` filtra `ORDEM_EXERC == "ÚLTIMO"` (`cvm.py:94`) — ou seja, cada ano vem do *próprio arquivo daquele ano*, na base de ações vigente naquele ano, e a reapresentação retroativa do LPA (exigida pelo CPC 41/IAS 33) **nunca é capturada**. Logo cada bonificação produz um degrau real na série.
- ⚠️ **A comparação de fator precisa de TOLERÂNCIA:** 1,5187 (salto medido) vs 1,5 (split registrado) = 1,2% de diferença. Um `==` exato não isentaria nada. Sugestão: isentar quando `|salto / Πfatores_do_ano − 1| < 20%`.

**⚠️ `dm.ohlc["Stock Splits"]` NÃO SERVE.** O `prices.py:147` busca `period="5y"` → janela medida: **2021-07-13 a 2026-07-13**. Splits dentro dela: só `2025-03-18` e `2025-12-26`. **O split de 2018-11-21 (o único que a isenção precisa) está FORA.** A janela de análise é de **10 anos** (`config.yaml:5`). → **É obrigatório buscar `tk.splits` (histórico completo) e carregá-lo em `DadosMercado`.** Isso é uma chamada de rede a mais em `coletar_mercado`.

**Comportamento offline:** `tk.splits` **é uma chamada de rede** (dispara um fetch de histórico completo). Não há modo offline. E é **mutável** — o Yahoo acrescentou `2025-12-26` ao ITUB4 e `2025-12-19` ao GOAU4 recentemente. **Um teste que chame `.splits` ao vivo é não-determinístico e vai piscar.** → **O snapshot do D-08 TEM que congelar os splits.** Formato recomendado: `{ticker: {"YYYY-MM-DD": fator}}` — datas como string ISO (o tz-aware não sobrevive ao `yaml.safe_dump` de forma limpa; e para o SAN-02 só o **ano** importa).

---

### Achado 6 — SAN-07 (spike contábil): a premissa `2.03` é FALSA, e o spike está essencialmente respondido

**Pergunta 1 do SAN-07: "IHCD/AT1 entram no PL dos bancos (conta `2.03`)?"**

**A conta `2.03` NÃO é o Patrimônio Líquido de nenhum banco.** Dump real do BPP consolidado 2025:

| banco | o que é `2.03` de verdade | onde o PL realmente está |
|---|---|---|
| ITUB4 | `2.03` = **"Passivos Financeiros ao Custo Amortizado"** (R$ 2.350,90 bi) | **`2.08`** — "Patrimônio Líquido Consolidado" (R$ 215,08 bi) |
| BBAS3 | `2.03` = **"Provisões"** (R$ 38,69 bi) | **`2.07`** (R$ 193,57 bi) |
| BBDC4 | `2.03` = **"Provisões"** (R$ 443,36 bi) | **`2.07`** (R$ 178,95 bi) |
| BRSR6 | `2.03` = **"Provisões"** (R$ 2,52 bi) | **`2.07`** (R$ 11,47 bi) |

E note que **o código do PL varia entre os próprios bancos** (`2.08` no ITUB4, `2.07` nos outros três). O `cvm.py:224-228` só sobrevive porque usa `nome_primeiro=True` e casa pelo **nome** ("Patrimônio Líquido Consolidado"). O parser está certo; **o texto do requisito é que está errado.**

**Composição do PL do ITUB4 (`2.08.*`), medida:**
```
  2.08      Patrimônio Líquido Consolidado           215,08 bi
  2.08.01   Capital Social Realizado                 136,91 bi
  2.08.02   Reservas de Capital                        2,86 bi
  2.08.03   Reservas de Reavaliação                    0,00 bi
  2.08.04   Reservas de Lucros                        67,71 bi
  2.08.06   Ajustes de Avaliação Patrimonial           0,00 bi   <-- !!
  2.08.07   Ajustes Acumulados de Conversão            0,00 bi
  2.08.09   Participação dos Acionistas Não Contr.    10,57 bi
```

**NÃO EXISTE nenhuma linha de IHCD / AT1 / "Instrumentos Elegíveis ao Capital" / "dívida perpétua" dentro do bloco do PL de nenhum dos 4 bancos.** No BRSR6, o instrumento aparece do lado do **passivo**: `2.01.01 Dívida Subordinada = R$ 1,69 bi`.

> **RESPOSTA MEDIDA À PERGUNTA 1: NÃO.** Os IHCD/AT1 **não** aparecem como subconta do PL na DFP padronizada da CVM para ITUB4, BBAS3, BBDC4 e BRSR6. Consequência: **o `B0` que o RIM consome NÃO está inflado por AT1**, e a hipótese do "terceiro bug de dados" **não se confirma por esse caminho**. (Ressalva honesta: nas demonstrações IFRS *próprias* do Itaú, os perpétuos AT1 **são** classificados em equity. O que a medição prova é que **a DFP da CVM não os expõe assim** — e é a DFP que este pipeline lê. Para o efeito prático do projeto, é o que importa.)

**Pergunta 2 do SAN-07: "O dirty surplus por IFRS 9 FVOCI é material?"**

O OCI **não** está no BPP — está na **DRA** (`dfp_cia_aberta_DRA_con_2025.csv`, dentro do ZIP que o projeto já baixa; **o parser nunca abriu esse arquivo**). Dump real:

| banco | `4.01` LL | `4.02` Outros Result. Abrangentes (OCI) | PL | **OCI / PL** |
|---|---|---|---|---|
| ITUB4 | 45,849 bi | **−0,071 bi** | 215,08 bi | **0,03%** |
| BBAS3 | 16,782 bi | **+0,071 bi** | 193,57 bi | **0,04%** |
| BBDC4 | 23,925 bi | **+1,055 bi** | 178,95 bi | **0,59%** |
| BRSR6 | 1,715 bi | **−0,024 bi** | 11,47 bi | **0,21%** |

Componente FVOCI isolado (ITUB4, `4.02.01` "Ativos Financeiros ao Valor Justo por meio de Outros Resultados Abrangentes") = **+0,980 bi = 0,46% do PL**. As pernas individuais chegam a ser grandes (BBAS3 tem `4.02.01.01` "ganhos não realizados" = +4,713 bi bruto), mas **se cancelam no líquido** (efeito tributário −1,344 bi, conversão cambial −2,483 bi).

> **RESPOSTA MEDIDA À PERGUNTA 2: NÃO É MATERIAL.** O dirty surplus anual dos 4 bancos fica entre **0,03% e 0,59% do PL**. Contra o clean surplus (`ΔB ≈ LL − DIV`), é ruído. **Nenhum knob deve se mover por causa disso** — o que já era a instrução do D-15.

**⚠️ Anomalia a registrar no spike (honestidade > completude):** a conta de estoque `Ajustes de Avaliação Patrimonial` (`2.08.06` no ITUB4, `2.07.01.06` nos demais) lê **0,00 bi nos QUATRO bancos**, enquanto a DRA mostra um *fluxo* de OCI não-zero. Um estoque zerado com fluxo não-zero é **inconsistente**. Duas leituras possíveis: (i) os bancos não preenchem essa linha padronizada da CVM e alocam o acumulado dentro de "Reservas de Lucros"; (ii) o valor existe mas é < R$ 5 mi (abaixo da precisão do meu print). Em qualquer dos casos, **a conclusão de materialidade não muda** — o fluxo da DRA já limita o efeito a < 0,6% do PL/ano. Mas o spike deve **declarar essa inconsistência**, não escondê-la.

**Conclusão do spike (para o documento em `.planning/spikes/`):** as duas perguntas do SAN-07 têm resposta **negativa**, com medição. **O terceiro bug de dados não existe.** A Fase 9 não herda dúvida — herda um "não" fundamentado.

---

### Achado 7 — SAN-05 (clean surplus) e SAN-03 (JCP): insumos já existem

- **SAN-05** (`ΔB ≈ LL − DIV`): `patrimonio_liquido`, `lucro_liquido` e `dividendos` já estão no `CompanyData` (`fundamentals.py:27-31`). Aritmética pura, zero insumo novo. **Mas atenção:** o resíduo do clean surplus é justamente OCI + recompras + o próprio bug de base (Achado 4). Num ticker com `num_acoes` quebrado, o SAN-05 vai acusar violação por causa do bug de base, não por dirty surplus. **Isso é uma feature, não um bug** — o REQUIREMENTS já diz que o SAN-05 é "detector de bug **e** pré-condição de validade do RIM".
- **SAN-03** — 🔴 **CORRIGIDO EM 2026-07-14 (pós-review, MEDIDO): a direção deste achado estava INVERTIDA.**

  A versão original desta linha afirmava, seguindo o comentário de `build.py:104-107`, que
  `_distribuicoes_proventos` *"já inclui JCP"* e que o Yahoo *"perde o JCP"*. **É o contrário.**

  - **O lado CVM PERDE o JCP.** `cvm.py:169` casa `ds.str.contains("dividendo")`. O **BRSR6** fila o
    JCP em `6.03.04 "Juros sobre o Capital Próprio Pagos"` — **sem a substring "dividendo"** → o
    filtro **não casa**. Medido: `_distribuicoes_proventos()` devolve **R$ 36,0 M** em 2025 contra
    **R$ 620,0 M** de JCP fora do filtro (**18,2×** a menos); 19,1× / 24,1× / 25,3× / 5,4× em
    2021-2024.
  - **O lado Yahoo INCLUI o JCP.** `DPA_yahoo × contagem real de ações` bate com o provento real do
    BRSR6 (div + JCP) com erro **< 5% em 4 anos** (1,00× / 1,00× / 1,00× em 2022-2024).
  - Os 4 grandes bancos (ITUB4/BBAS3/BBDC4) **escapam por acidente**: filam numa linha
    `"Dividendos E Juros sobre o Capital Próprio Pagos"`, que casa o filtro. Por isso o bug atinge só
    as ~13 empresas do DATA-01.

  **Consequência de desenho (planos 08-01 + 08-04):** o SAN-03 ganha **dois sinais**. O bom é o
  **detector direto de JCP perdido**, 100% interno à CVM (`Σ proventos_filtro_amplo / Σ dividendos`,
  com o filtro amplo casando `"dividendo"` **OU** `"juros sobre capital"`) — **imune à contaminação do
  `num_acoes` (R-06)**. A razão `dividendos_CVM` vs `DPA × num_acoes` continua existindo, mas é sinal
  de **consistência**, não veredito de quem está certo: no BRSR6 (cujo `num_acoes` está quebrado em
  205.000×) ela dispararia **pelo motivo errado** e esvaziaria o teste de regressão do DATA-01.

  **O comentário `build.py:104-107` está factualmente errado e é corrigido no plano 08-01** (corrigir
  comentário não é consertar dado); `_distribuicoes_proventos` e `c.dividendos` ficam **intocados e
  sujos** — consertá-los é DATA-01, Fase 9.

---

### Achado 8 — 🔴 `_fator_unit` está CORROMPIDO pelo bug dos minoritários

**Medido:**
```
ALUP11 — _fator_unit(contagem_cvm, acoes_yahoo=329.626.866)
  fator calculado pelo código (build.py:24-37) : 5
  fator VERDADEIRO (composicao_capital 988.880.601 / 329.626.866) : 3,0000000091
  _eh_unit('ALUP11') = True
```

`_fator_unit` (`build.py:24-37`) calcula a mediana de `contagem_cvm[ano] / acoes_yahoo` e arredonda. Mas `contagem_cvm` **já vem inflada 1,41× pelos minoritários** (Achado 4), e `acoes_yahoo` é `sharesOutstanding` = 329,6M (units). A mediana das razões dá ≈ 4,88 → arredonda para **5**. A ALUP11 é uma unit de **1 ON + 2 PN = 3 ações/unit** (a contagem oficial da CVM confirma: 988.880.601 / 329.626.866 = **exatamente 3,000**).

**Dois bugs se compondo — o padrão assinatura deste projeto.** E o efeito é perverso: `build.py:100` faz `c.num_acoes[ano] = contagem_cvm[ano] / fator` → divide por **5** em vez de 3 → o erro de minoritários (1,41×) é **parcialmente mascarado** pela divisão excessiva. Resultado medido: o fator SAN-01 da ALUP11 **pós-unit** cai para ≈ **0,98** → **o SAN-01 NÃO vai flagar a ALUP11**, apesar de a base estar quebrada.

**Implicações diretas para o plano:**
1. **O SAN-01 tem que rodar sobre `c.num_acoes` (pós-`_fator_unit`)** — é o campo que os motores consomem, e é onde o mascaramento acontece. Rodar sobre `contagem_cvm` cru mostraria um número que o resto do app não usa.
2. **A ALUP11 será pega pelo SAN-04, não pelo SAN-01** — que é exatamente o que o REQUIREMENTS:89 já manda ("SAN-04 ... Pega MRFG3, CSNA3, ALUP11, EQTL3"). O desenho do ROADMAP está certo; mas **o motivo** é este, e o planner não podia saber sem a medição.
3. **Não conserte `_fator_unit` nesta fase.** É Fase 9 (DATA-03). Mas **registre-o** — e considere que o baseline do D-05 vai congelar a ALUP11 com a flag SAN-04 e **sem** a SAN-01, e isso está **correto**.

---

## Runtime State Inventory

Fase de detecção (não é rename/refactor), mas há **estado congelado** relevante:

| Categoria | Encontrado | Ação |
|---|---|---|
| Snapshot existente | `tests/fixtures/snapshot_bancos_2026-07-12.yaml` — 4 bancos, **contaminado** (ITUB4 com contagem doente) e consumido por `helpers_blindagem.py:34` + `test_backtest_bancos.py` | **NÃO tocar** nesta fase. O ROADMAP da Fase 9 prevê a regeneração. Um snapshot NOVO e separado nasce aqui. |
| Cache CVM | `data/cvm/*.zip` (2015-2025) + `cad_cia_aberta.csv` — **completo** | Nenhuma. É o que torna a fase offline no lado CVM. |
| `data/ticker_map.json` | 104 tickers (`CD_CVM` por ticker) | Fonte do universo do snapshot D-08. Também é o que alimenta `tickers_conhecidos()` do BLIND-04a. |
| Hook do BLIND-05 | `core.hooksPath` é estado **local por clone** | `git config core.hooksPath .githooks` — o teste `-k hook_do_blind05_esta_instalado` avisa. |
| Dado vivo do Yahoo | `.splits` **mudou recentemente** (ITUB4 ganhou `2025-12-26`; GOAU4 `2025-12-19`; CGRA4 `2025-12-23`) | Confirma D-08: congelar. |

---

## Validation Architecture

`workflow.nyquist_validation` está **`false`** em `.planning/config.json`. Esta seção existe porque o objetivo da fase a exigiu — e porque **nesta fase os testes SÃO o entregável** (os asserts são o teste de regressão da Fase 9).

### Framework

| Propriedade | Valor |
|---|---|
| Framework | pytest, config em `pyproject.toml` `[tool.pytest.ini_options]` |
| `pythonpath` | `["src"]` |
| `testpaths` | `["tests"]` |
| `xfail_strict` | **`true`** (BLIND-02: XPASS = FAILED) |
| `addopts` | **`-m 'not golden_nivel' --strict-markers`** |
| Marks válidos | `invariante`, `golden_nivel`, `contrato` (`helpers_blindagem.py:41` `CATEGORIAS`) |
| Rodar | `pytest -k <expr>`. **`pytest tests/arquivo.py` NÃO funciona** (dispara `CLASSIFICACAO ORFA`). |

### 🔴 O mecanismo de classificação (todo teste novo passa por aqui)

`tests/conftest.py:49-83` (`pytest_collection_modifyitems`):
- Lê `tests/classificacao.yaml` (466 entradas hoje: **320 `contrato`, 108 `invariante`, 38 `golden_nivel`**).
- **Teste sem entrada → `pytest.UsageError("TESTE NAO CLASSIFICADO (BLIND-01)")` → QUEBRA A COLETA.**
- **Entrada órfã (teste deletado, linha esquecida) → `CLASSIFICACAO ORFA` → QUEBRA A COLETA.**
- Categoria inválida → `CATEGORIA INVALIDA`.

**Forma exata da entrada** (`tests/classificacao.yaml`), chave = nodeid completo **com `[param]` se houver**, valor = categoria:
```yaml
'tests/test_sanidade.py::test_san01_flag_dispara_acima_do_limiar': contrato
'tests/test_sanidade_baseline.py::test_baseline_de_sujos_so_encolhe': invariante
```
O caminho é **relativo à raiz do repo** (`helpers_blindagem.py:87-97`, `_rel`), estilo posix. Aspas simples são o padrão do arquivo.

E `tests/conftest.py:32-38` (`pytest_configure`) roda `violacoes_da_blindagem()` **antes de qualquer coleta**, seja qual for o `-m` — é o backstop indesligável do BLIND-07.

### 🔴 BLIND-04a: a proibição de `ticker == R$` e como o baseline do D-05 passa por ela

O meta-teste é **`tests/test_blindagem_meta.py:47`** (`test_nenhum_teste_de_calibracao_crava_ticker_em_reais`), e o detector é **`helpers_blindagem.py:271-325`** (`detectar_ticker_com_valor_cravado`).

**A regra exata** (`helpers_blindagem.py:277-282`) — um teste é OFENSOR quando o corpo contém **AMBOS**:
- **(i) um TICKER:** literal string que é chave de `data/ticker_map.json`, **OU** um nome de constante de MÓDULO cujo valor contém um (`_tickers_por_nome`, linha 150) — ou seja, `TICKERS = ["GOAU4"]` no topo do arquivo **contamina toda função que usar o nome `TICKERS`**;
- **E (ii) uma constante numérica NÃO-trivial** (∉ `{0.0, 1.0, 0.5, 2.0}` — `TRIVIAIS`, linha 45) que **chega a um assert** por 4 rotas (`_tem_nivel_cravado`, linha 240): direto num `Compare`/`Assert`, via variável local, via constante de módulo, ou **via helper que confere** (uma função não-teste que contenha um `assert`).

**⚠️ ARMADILHAS CONCRETAS PARA O BASELINE DO D-05:**

| Padrão | Passa no BLIND-04a? | Por quê |
|---|---|---|
| `assert flags("GOAU4") == ["SAN-01"]` | ✅ **SIM** | Tem ticker, **nenhuma constante numérica**. |
| `assert len(sujos) == 41` **no mesmo teste que cita um ticker** | ❌ **NÃO — OFENSOR** | `41` é não-trivial e está num `Assert`; o ticker está no corpo. **Vai quebrar a suíte.** |
| `LIMIAR_SAN01 = 1.5` + `assert limiar == LIMIAR_SAN01` (teste do D-11) | ✅ **SIM** — **desde que o teste NÃO contenha nenhum literal de ticker** | Sem ticker → a condição (i) falha → não é ofensor. |
| `BASELINE = {"GOAU4": ...}` como dict **no .py** | ⚠️ **PERIGOSO** | `_tickers_por_nome` marca `BASELINE`; qualquer teste que use o nome + qualquer número não-trivial num assert = ofensor. |
| Baseline num **YAML** carregado por fixture | ✅ **SIM** | O AST não vê literal de ticker nenhum (`helpers_blindagem.py:286-292` diz isso explicitamente: "goldens ancorados em FIXTURE de ticker real... nenhum literal de ticker aparece no corpo"). |

> **Recomendação forte (fecha o D-05 + D-07 + BLIND-04a de uma vez):**
> 1. O baseline vive em **`tests/fixtures/baseline_sanidade.yaml`** — nunca como dict Python num `test_*.py`.
> 2. O conteúdo é `ticker → lista de {check, bucket}` — **nunca um R$, nunca uma magnitude exata** (D-07). Bucket como **string**: `"~1e0"`, `"~1e3"`, `"~1e-3"`. String não é constante numérica → o detector nem se aproxima.
> 3. O teste da monotonicidade (D-06) compara **conjuntos de flags**, não números. `assert flags_hoje <= flags_baseline` — sem constante numérica alguma.
> 4. O teste dos limiares (D-11) fica num arquivo **sem nenhum ticker** — só números. Aí `LIMIAR_SAN01 = 1.5` é seguro.
>
> Esse desenho não é "fugir do detector": um mapa `ticker → flag` **genuinamente não é** um golden de nível — não trava um método, trava uma *detecção*. Documente essa distinção no cabeçalho do arquivo, para o próximo leitor e para a auditoria do BLIND-01 (que é um **superset** do que o AST acha — `helpers_blindagem.py:292`).

### Requisitos → mapa de teste

| Req | Comportamento | Tipo | Comando | Existe? |
|---|---|---|---|---|
| SAN-01 | fator > 1,5 → flag; GOAU4/CGRA4 no baseline | contrato | `pytest -k san01` | ❌ Wave 0 |
| SAN-02 | salto **simétrico** > limiar, isento por split; ITUB4 2019 + BRSR6 2020/21 | contrato | `pytest -k san02` | ❌ Wave 0 |
| SAN-03 | `div_CVM` vs `DPA×n` | contrato | `pytest -k san03` | ❌ Wave 0 |
| SAN-04 | `3.11` vs `3.11.01` divergem > 10% | contrato | `pytest -k san04` | ❌ Wave 0 |
| SAN-05 | clean surplus reportado como dado | contrato | `pytest -k san05` | ❌ Wave 0 |
| SAN-06 | **never-raise** — ticker sem preço/sem Yahoo (MRFG3!) não estoura | contrato | `pytest -k never_raise` | ❌ Wave 0 |
| SAN-07 | (spike — doc, não teste) | — | — | — |
| D-03 | default de `confianca` é `nao_avaliada` | contrato | `pytest -k confianca_default` | ❌ Wave 0 |
| D-04 | **`aplicar_sanidade` provada por execução** ponta-a-ponta | contrato | `pytest -k sanidade_e_chamada` | ❌ Wave 0 |
| D-06 | **monotonicidade** — lista de sujos só encolhe | **invariante** | `pytest -k baseline` | ❌ Wave 0 |
| D-11 | limiares congelados (sem ticker no arquivo!) | **invariante** | `pytest -k limiares` | ❌ Wave 0 |

### Como o teste do D-04 roda offline e determinístico

`montar_empresa` (`build.py:40`) chama `prices.coletar_mercado` (rede) e `cvm.fundamentos_do_ano` (cache local, **já presente**). Duas rotas:
- **(A) Recomendada:** o teste monta um `CompanyData` **a partir do snapshot congelado** e chama `aplicar_sanidade` — mas isso **não prova a chamada dentro de `montar_empresa`**, que é exatamente o que o D-04 exige.
- **(B) A que satisfaz o D-04:** o teste roda `montar_empresa` de verdade, com `prices.coletar_mercado` **monkeypatchado** para devolver um `DadosMercado` reconstruído do snapshot. O CVM vem do cache real (offline). Assert: `c.confianca != "nao_avaliada"`. **Remover a chamada de `aplicar_sanidade` de `montar_empresa` → vermelho na hora.** É a rota correta: exercita o pipeline real, sem tocar a rede.

`prices.py:27-38` já tem `_yf()` e `_fetch_info` como pontos de injeção — o monkeypatch é limpo.

### Wave 0 (gaps a criar antes de qualquer check)

- [ ] `src/analista/core/sanidade.py` — os 7 checks + limiares (D-10) + `aplicar_sanidade`
- [ ] Campos `avisos` / `confianca` em `CompanyData` (`fundamentals.py:20`), default `nao_avaliada` (D-03)
- [ ] **`cvm.py`: ler `3.11.01` (lucro do controlador) + participação de não-controladores** — sem isso SAN-04 não existe
- [ ] **`prices.py`: ler `marketCap`, `impliedSharesOutstanding`, `splits` (histórico completo)** — sem isso SAN-01/SAN-02 não existem
- [ ] `scripts/capturar_snapshot_sujo.py` — 104 tickers, dado sujo (D-08)
- [ ] `tests/fixtures/snapshot_sanidade_2026-07-XX.yaml`
- [ ] `tests/fixtures/baseline_sanidade.yaml` (D-05/D-07 — **YAML, não .py**)
- [ ] `tests/test_sanidade.py` + `tests/test_sanidade_baseline.py` + `tests/test_sanidade_limiares.py`
- [ ] **Entradas em `tests/classificacao.yaml` para CADA teste novo** — senão a coleta quebra
- [ ] `.planning/spikes/san-07-ihcd-at1-fvoci.md` (D-15)

---

## Formato recomendado do snapshot (D-08)

`capturar_snapshot_bancos.py` serve de **referência de forma**, e o que ele faz bem:
- roda como script standalone (`sys.path.insert`, linhas 26-27);
- coage tudo para tipos nativos antes do `yaml.safe_dump` (`_f`/`_serie`, linhas 42-49) — **crítico**: tipos numpy quebram o dump;
- **falha ruidosamente** com `return 1` quando um campo obrigatório vem vazio (linhas 96-112);
- `yaml.safe_dump(..., allow_unicode=True, sort_keys=True)` (linha 123) — `sort_keys=True` deixa o diff estável.

**O que nele NÃO serve:**
- `BANCOS = ["ITUB4","BBAS3","BBSE3","BBDC4"]` (linha 32) — só 4 tickers. Precisa dos **104** de `data/ticker_map.json`.
- Chama `report.analisar_acao` e carimba `intrinseco_motor_observado` (linhas 76-87) — **isso é um R$ por ticker**. O snapshot desta fase **não pode ter isso** (D-05/D-07). Corte.
- **Não captura**: `marketCap`, `impliedSharesOutstanding`, `splits`, `lpa` cru, `contagem_cvm` pré-unit, origem de cada ano (CVM vs fallback Yahoo). Todos necessários.
- O guarda-corpo `return 1` em qualquer falha (linha 104) **é errado aqui**: com 104 tickers e o MRFG3 dando 404, abortar tudo por um ticker torna o snapshot incapturável. **Degrade por ticker** e registre a ausência — que é, aliás, o próprio contrato never-raise do SAN-06.

**Conteúdo mínimo por ticker:**
```yaml
GOAU4:
  nome: ...
  setor: ...
  anos: [2016, ..., 2025]
  # CVM (séries por ano)
  lucro_liquido:            {2016: ..., ...}
  lucro_controlador:        {2016: ..., ...}   # NOVO — 3.11.01 (SAN-04)
  patrimonio_liquido:       {2016: ..., ...}
  pl_nao_controladores:     {2016: ..., ...}   # NOVO (SAN-04)
  lpa_cvm:                  {2016: ..., ...}   # NOVO — o valor CRU, pré-divisão
  dividendos:               {2016: ..., ...}
  num_acoes:                {2016: ..., ...}   # pós-_fator_unit (o que os motores usam)
  origem_num_acoes:         {2016: cvm, 2017: yahoo_fallback, ...}  # NOVO (Achado 2c)
  # Yahoo (snapshot atual)
  preco_atual:              10.12
  shares_outstanding:       836071784
  implied_shares_out:       1322874548          # NOVO (SAN-01)
  market_cap:               13387489280         # NOVO (SAN-01)
  beta:                     ...
  dpa_por_ano:              {2016: ..., ...}
  splits:                   {"2008-06-13": 2.0, "2025-12-19": 1.3333}  # NOVO (D-12)
```

**Tamanho estimado:** ~40-60 linhas × 104 tickers ≈ **250-400 KB** em YAML. Perfeitamente versionável. (O `snapshot_bancos` atual tem 4 tickers.) Se incomodar, `yaml.safe_dump(default_flow_style=None)` compacta os dicts curtos.

**Tempo de captura:** ~104 chamadas ao Yahoo com o retry de `prices.py:122-133` + `tk.splits` (mais 104 fetches de histórico completo). Estime **10-20 min**, e trate rate-limit. O lado CVM é instantâneo (cache).

---

## 🔴 Riscos e Armadilhas

### R-01 — 🚨 O "ITUB4 2019 = 1.131×" do ROADMAP **NÃO EXISTE**. O número está errado.

`REQUIREMENTS.md:86-87` e o CONTEXT (`D-12`, `specifics`) afirmam: *"Pega ITUB4 2019 (1.131×)"*.

**Medido:** o salto de `num_acoes` do ITUB4 em 2019 é **0,0010× (uma queda de mil vezes)**, não 1,131×. A série mostra `2018: 10.015.234.375 → 2019: 10.004.676`. O ano de 2019 tem `LPA = 2780,00` — a doença do ×1000, a mesma do CGRA4.

**De onde veio o "1,131"?** Reconstrução com alta confiança: o salto **2024→2025 do ITUB4 é 1,1286×**, e o `.splits` registra dois splits em 2025 (`2025-03-18 = 1,1` e `2025-12-26 = 1,03`) cujo produto é **1,133**. Ou seja, "1,131×" é quase certamente o salto de **2025**, causado por uma **bonificação real e legítima** — mal-rotulado como "2019" em algum ponto da cadeia de documentos.

**O que isso muda no plano:**
- ✅ **O SAN-02 continua pegando o ITUB4** — e com folga muito maior (fator 1000 vs. o 1,131 esperado). O critério de sucesso do SAN-02 **é atingível**.
- ⚠️ **Mas se alguém escrever o teste esperando um fator ≈1,131, ele vai falhar.** E se o limiar do SAN-02 for calibrado para pegar 1,131×, ele será **absurdamente apertado** (1,13!) e vai gerar falso positivo em **toda bonificação de 10%** da B3 — exatamente o cenário que o D-09 diz que desinstala a guarda.
- 🔴 **Se o limiar do SAN-02 for ~1,13, o próprio ITUB4 2025 (1,1286×, um evento LEGÍTIMO) dispararia** — e só não vira falso positivo porque a isenção do `.splits` o cobre. Isso deixa a guarda inteira dependendo da qualidade do `.splits` do Yahoo para **não** gritar em dezenas de tickers.

> **Recomendação:** limiar do SAN-02 **folgado** (sugestão: **fator simétrico ≥ 3×**, i.e. `max(r, 1/r) ≥ 3`). Pega ITUB4 2019 (1000×), ITUB4 2020 (780×), BRSR6 2020/21 (205.000×), CGRA4 2025 (1000×), MRFG3 (4,7×) — e **ignora toda bonificação real da B3** (que raramente passa de 2×). Com 3×, a isenção por `.splits` deixa de ser load-bearing para o caso comum e passa a ser um seguro para o caso raro (ex.: ITUB4 2018 = 1,52× — já fica abaixo de 3×, nem precisa da isenção). **Isso torna o SAN-02 robusto por construção, não por dependência do Yahoo.** Mas o D-12 travou a isenção — então **mantenha-a**, ela só fica menos crítica. Confirme com o usuário se o limiar de 3× é aceitável.

### R-02 — 🚨 O SAN-07 pergunta sobre a conta `2.03`, que **não é o PL de banco nenhum**

`REQUIREMENTS.md:94-96` e `D-15` dizem: *"Verificar se IHCD/AT1 entram no PL dos bancos (`2.03`)"*.

**Medido:** `2.03` é "Passivos Financeiros ao Custo Amortizado" (ITUB4) ou "Provisões" (BBAS3/BBDC4/BRSR6). O PL do ITUB4 é **`2.08`**; o dos outros três é **`2.07`**. E não há linha de AT1/IHCD em nenhum deles.

**O que isso muda:** o spike do D-15 **não pode** ser escrito contra `2.03` — sairia uma resposta sem sentido. Escreva-o contra `2.07`/`2.08` (ou, melhor, contra o **nome** "Patrimônio Líquido Consolidado", que é o que `cvm.py:227` já faz com `nome_primeiro=True`). **A resposta do spike já está no Achado 6 e é NÃO para as duas perguntas** — o "terceiro bug de dados" não se confirma.

### R-03 — 🚨 MRFG3 (alvo nomeado do SAN-04) está **404 no Yahoo**

```
HTTP Error 404: Quote not found for symbol: MRFG3.SA
```

Sem preço, sem `marketCap`, sem `sharesOutstanding`, sem `.splits`. (Causa provável: a Marfrig virou **MBRF** após a fusão com a BRF — o ticker mudou.) O lado **CVM funciona normalmente** (CD_CVM 20788, dados até 2025).

**Impacto:**
- **SAN-01 é INCOMPUTÁVEL para MRFG3.** O check tem que devolver "não avaliável", **não** uma flag, e **não** uma exceção. → **Este é o caso de teste vivo e real do SAN-06 (never-raise).** Use-o.
- **SAN-04 funciona** (é 100% CVM) → o MRFG3 continua sendo pego, como o REQUIREMENTS manda. ✅
- **O snapshot do D-08 vai congelar o MRFG3 sem dado de mercado.** O script **não pode abortar** por isso (`capturar_snapshot_bancos.py:104` aborta — não copie esse comportamento).
- **Decisão pendente para o usuário:** o MRFG3 deve sair de `data/ticker_map.json`? Isso é **fora do escopo** desta fase (é dado, não detecção) — mas o planner precisa registrar. Note que `ticker_map.json` também alimenta o `tickers_conhecidos()` do BLIND-04a; mexer nele tem efeito colateral na blindagem.

### R-04 — 🔴 `_fator_unit` corrompido (Achado 8): o SAN-01 **não** vai pegar a ALUP11

`_fator_unit('ALUP11')` devolve **5**; o verdadeiro é **3**. A divisão excessiva **mascara** o erro de minoritários e o fator SAN-01 pós-unit cai para ≈0,98 → sem flag.

Isso **não quebra** o critério de sucesso (o REQUIREMENTS atribui ALUP11 ao **SAN-04**, não ao SAN-01). Mas: **não "conserte" o `_fator_unit` para fazer o SAN-01 flagar a ALUP11.** Isso seria consertar dado na Fase 8 — proibido, e destruiria o teste de regressão da Fase 9. Registre a flag SAN-04 no baseline e siga.

### R-05 — ⚠️ EQTL3 fica a **0,5% do limiar** do SAN-01

Fator medido: **1,492×** (contra a CVM) / **1,496×** (contra o `marketCap`). Limiar do D-09: **1,5×**. **Um bug REAL e conhecido passa 0,5% abaixo da linha.**

Isso não é falso positivo — é **falso negativo por um fio**. E num run **ao vivo**, qualquer oscilação de preço faz o EQTL3 piscar entre flagado e não-flagado, o que envenenaria o baseline (viola o espírito do D-07: *"um re-download do Yahoo mexendo no terceiro decimal não pode deixar o teste vermelho"*).

**Mitigação (já prevista pelo CONTEXT):** o **snapshot congelado do D-08 resolve isso** — o baseline roda sobre preço/`marketCap` congelados → determinístico → sem piscar. **Mas o snapshot PRECISA congelar `marketCap`**, não só o preço. Se congelar só o preço e buscar o `marketCap` ao vivo, o EQTL3 volta a piscar.
E o **relatório CLI da Fase 9, que roda ao vivo**, vai ver o EQTL3 oscilar. Documente.
**Não mexa no limiar do D-09** (está travado, e afrouxá-lo para 1,4 pegaria a ALUP11 pós-unit? não — 0,98. Não ajudaria). O EQTL3 é do SAN-04. Deixe.

### R-06 — ⚠️ Dependência circular de detecção: os checks se contaminam

`num_acoes` quebrado envenena **SAN-01, SAN-03 (DPA×n) e SAN-05 (via dividendos/PL)** ao mesmo tempo. Um ticker sujo vai acender **várias** flags. **Isso é correto** (o dado *está* inconsistente em várias dimensões), mas:
- O baseline (D-05) vai ter **múltiplas flags por ticker** — não uma.
- A monotonicidade (D-06) precisa ser por **par (ticker, check)**, não por ticker. Senão o conserto de um bug em Fase 9 apaga um ticker inteiro do baseline e a regra perde granularidade.
- O `c.confianca` (D-13) precisa de uma regra de agregação. Sugestão: `baixa` se qualquer flag de **escala** (SAN-01 ou SAN-02) disparar; `media` se só flags de base/consistência (SAN-03/04/05); `alta` se nenhuma; `nao_avaliada` se não checado (D-03).

### R-07 — ⚠️ `.splits` vazio tem `dtype=object`

`BRSR6.SA.splits` → `Series` vazia com **`dtype: object`** (não `float64`). Operação numérica direta quebra. E o index é **tz-aware** (`America/Sao_Paulo`) — comparação com `datetime` naive levanta `TypeError`. Para o SAN-02 só o **ano** importa: use `d.year` no `.items()` (é o que `prices.py:197` já faz para dividendos) e serialize como string ISO no snapshot.

### R-08 — ⚠️ `tk.splits` é uma chamada de rede EXTRA e o dado é MUTÁVEL

Não vem de graça junto do `tk.history(period="5y")` que o `prices.py:147` já faz — e **a janela de 5y não cobre o split de 2018 do ITUB4** (medido: janela = 2021-07-13 a 2026-07-13). Precisa de `tk.splits` (histórico completo) → +104 fetches na captura do snapshot.
E o Yahoo **acrescentou splits recentemente** (ITUB4 `2025-12-26`, GOAU4 `2025-12-19`, CGRA4 `2025-12-23`). **Um teste que leia `.splits` ao vivo vai piscar.** Congele.

### R-09 — ⚠️ `composicao_capital` (a contagem oficial de ações) tem **escala inconsistente**

`dfp_cia_aberta_composicao_capital_{ano}.csv` existe **dentro do ZIP que o projeto já baixa** e traz a contagem oficial de ações (`QT_ACAO_TOTAL_CAP_INTEGR`, `QT_ACAO_TOTAL_TESOURO`). **É o insumo que resolve o DATA-03 da Fase 9.**

**Mas cuidado:** ele é chaveado por **`CNPJ_CIA`, não por `CD_CVM`** (precisa de join via `cad_cia_aberta.csv`), e **a escala é inconsistente entre empresas**: ITUB4 e BRSR6 vêm em **MILHARES de ações**; GOAU4/CGRA4/CSNA3/EQTL3/ALUP11/MRFG3 vêm em **unidades**. Usá-lo cru reintroduziria a doença do ×1000 por outro caminho.

> **NÃO use isso na Fase 8 para consertar `num_acoes`** — seria consertar dado, o que está proibido e destruiria o teste de regressão da Fase 9. **Mas registre-o com destaque para a Fase 9.** É o achado mais valioso desta pesquisa para o bloco DATA. (Usei-o aqui apenas como **referência de validação** — e ele confirmou o `impliedSharesOutstanding` do Yahoo com erro < 0,3%.)

### R-10 — ⚠️ Um teste novo sem entrada em `classificacao.yaml` **quebra a coleta inteira**

Não é um erro no teste — é `pytest.UsageError` na coleta: **a suíte inteira não roda**. Com ~10 testes novos nesta fase, cada um precisa de sua linha. E se um teste for renomeado/deletado sem atualizar o YAML → `CLASSIFICACAO ORFA`, mesmo efeito. **Coloque a atualização do `classificacao.yaml` na MESMA task que cria cada teste**, nunca numa task "de limpeza" no fim.

---

## Don't Hand-Roll

| Problema | Não construa | Use | Por quê |
|---|---|---|---|
| Validação de schema/dados | `pandera`, `great-expectations` | 4 asserts aritméticos em `core/sanidade.py` | **Proibido pelo CONTEXT/ROADMAP.** Custo zero é constraint; peso e indireção para aritmética trivial. |
| Detecção de split | parser de eventos societários próprio | `yfinance.Ticker(t).splits` (D-12) | Já existe, é grátis, e o `prices.py:96-103` já usa a coluna `Stock Splits` para outro fim. |
| Contagem de ações "correta" | derivar de `LL/LPA` melhor | **NADA nesta fase.** (Fase 9: `composicao_capital` + `impliedSharesOutstanding`) | Consertar aqui destrói o teste de regressão da Fase 9. |
| Score de qualidade | score numérico 0-100 | escala discreta `alta/media/baixa/nao_avaliada` (D-13) | Todo número por ticker convida a virar knob. |
| Snapshot/fixture | mock manual de yfinance | reaproveitar a FORMA de `capturar_snapshot_bancos.py` | Padrão já provado no repo (`backtest.carregar_snapshot`). |

**Key insight:** nesta fase, a tentação não é hand-rollar uma lib — é **consertar o dado**. Os 3 bugs estão diagnosticados a nível de conta CVM e o conserto parece trivial. **Resista.** O ROADMAP é explícito, e o motivo é que os asserts *são* o teste de regressão da Fase 9: sem vê-los falhar primeiro, não há como provar, ticker a ticker, que o conserto funcionou.

---

## Assumptions Log

| # | Claim | Seção | Risco se errado |
|---|---|---|---|
| A1 | O "1,131×" do ROADMAP é o salto de **2025** (bonificação real), mal-rotulado como 2019 | R-01 | Baixo — a reconstrução (1,1×1,03 = 1,133 vs 1,1286 medido) é forte, e o SAN-02 pega o ITUB4 de qualquer jeito. Mas **confirme com o usuário** antes de escrever o teste. |
| A2 | Limiar sugerido do SAN-02 = **3× simétrico** | R-01 | Médio — é discricionário (D-09 só travou o SAN-01), mas mexe no critério de sucesso. **Confirme.** |
| A3 | Limiar sugerido do SAN-04 = **10%** de divergência `3.11`/`3.11.01` | Achado 4 | Baixo — pega os 4 nomeados (26%–197%) e deixa os bancos (0,04%–4,9%) limpos, com margem enorme. |
| A4 | MRFG3 saiu do Yahoo por virar **MBRF** (fusão Marfrig/BRF) | R-03 | Baixo — o 404 é fato medido; a *causa* é inferência. Não muda o plano (o SAN-06 precisa lidar com o 404 seja qual for a causa). |
| A5 | O `Ajustes de Avaliação Patrimonial = 0,00` é o filer não preenchendo a linha padronizada | Achado 6 | Baixo — a materialidade já é limitada pelo **fluxo** da DRA (< 0,6% do PL), que é medição direta. |
| A6 | Regra de agregação de `c.confianca` (escala→`baixa`, base→`media`) | R-06 | Baixo — é discricionário (D-13 só travou a escala discreta). |

---

## Open Questions (RESOLVED)

**Todas as três foram decididas pelo usuário em 2026-07-14, durante o planejamento da fase.**

1. **O limiar do SAN-02.** ✅ **RESOLVED: 3× simétrico (`max(r, 1/r) >= 3`), confirmado pelo usuário em
   2026-07-14.** O valor "1.131×" do REQUIREMENTS é um **número fantasma** (R-01) e é **corrigido no
   plano 08-02** (REQUIREMENTS + ROADMAP, no mesmo diff, com a nota de que o valor foi **medido, não
   lembrado**). O 3× pega todos os alvos reais com folga (ITUB4 2019 = ÷1000, ITUB4 2020 = ×780,
   BRSR6 = ×205.000, CGRA4 = ÷1000, MRFG3 = 4,7×) e **ignora toda bonificação real da B3**. A isenção
   por `.splits` (D-12) **fica MANTIDA** — apenas deixa de ser load-bearing.
2. **MRFG3 no `ticker_map.json`.** ✅ **RESOLVED: MANTER, confirmado pelo usuário em 2026-07-14.**
   `ticker_map.json` **não é tocado** (é dado = Fase 9, e alimenta o `tickers_conhecidos()` do
   BLIND-04a). O MRFG3 é o **caso de teste vivo do SAN-06**: o SAN-01 é INCOMPUTÁVEL para ele → o check
   devolve **"não avaliável"**, nem flag, nem exceção.
3. **O spike SAN-07.** ✅ **RESOLVED: formalizar o documento, confirmado pelo usuário em 2026-07-14.**
   A pesquisa **já respondeu** as duas perguntas com medição nos 4 bancos (§Achado 6): **as duas
   respostas são NÃO — o terceiro bug de dados NÃO existe.** O plano 08-02 escreve o doc em
   `.planning/spikes/`, com a **correção da conta** (o PL dos bancos é `2.07`/`2.08`, **não** `2.03`) e
   os números por banco. **Nenhum knob se move.**

### Nota técnica (não é pergunta aberta)

**`c.confianca` no `CompanyData` e o snapshot dos bancos.** O `snapshot_bancos_2026-07-12.yaml` reconstrói `CompanyData` via `backtest.carregar_snapshot`. Adicionar campos com default (`field(default_factory=list)` / `= "nao_avaliada"`) **não quebra** a reconstrução. ✅ Verificado por inspeção de `helpers_blindagem.py:627-638`. Mas o D-03 diz que o default é `nao_avaliada` — então os `CompanyData` do snapshot de bancos nascerão `nao_avaliada`, e **isso é exatamente o comportamento desejado** (D-03: "um `CompanyData` construído à mão não pode nascer parecendo limpo").

---

## Sources

### Primária (HIGH — medido nesta sessão)
- Execução de `analista.ingest.cvm.fundamentos_do_ano` contra `data/cvm/dfp_cia_aberta_{2016..2025}.zip` — séries de `num_acoes`, contas `3.99*`, `3.11*`, `2.0X*`, DRA
- Execução de `yfinance.Ticker(...).splits` / `.info` / `.history()` — yfinance **1.4.1**, 2026-07-14
- `dfp_cia_aberta_composicao_capital_2025.csv` + `cad_cia_aberta.csv` (join por CNPJ)
- `src/analista/ingest/cvm.py`, `build.py`, `prices.py`, `core/fundamentals.py`
- `tests/conftest.py`, `tests/helpers_blindagem.py`, `tests/test_blindagem_meta.py`, `tests/classificacao.yaml`, `pyproject.toml`
- `scripts/capturar_snapshot_bancos.py`

### Secundária (MEDIUM)
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `08-CONTEXT.md`, `CLAUDE.md`, `calibracao.lock.yaml`

### Não usado
- Context7 / WebSearch — desnecessários. Todas as perguntas foram respondidas por medição direta contra o código e os dados do projeto, que é uma fonte estritamente mais forte.

---

## Metadata

**Confidence breakdown:**
- **Standard stack:** HIGH — nenhuma dependência nova; versões medidas na máquina.
- **Arquitetura / onde o código vai:** HIGH — os pontos de integração foram lidos linha a linha.
- **Causa-raiz dos bugs:** **HIGH** — reproduzida contra os dados reais, com concordância cruzada de duas fontes independentes (CVM `composicao_capital` × Yahoo `impliedSharesOutstanding`, erro < 0,3% em 5/5).
- **`.splits` / D-12:** **HIGH** — medido ao vivo contra os 4 tickers relevantes.
- **SAN-07 (spike):** **HIGH** para as duas respostas (ambas NÃO), **MEDIUM** para a anomalia do `Ajustes de Avaliação Patrimonial = 0` (a causa é inferida; o efeito, não).
- **Malha de testes / BLIND:** HIGH — o detector AST foi lido função a função.
- **Limiares de SAN-02..SAN-05:** **MEDIUM** — são discricionários (D-09 só travou o SAN-01) e as sugestões estão fundamentadas em medição, mas **A2 precisa de confirmação do usuário**.

**Research date:** 2026-07-14
**Valid until:** ~2026-08-14 (30 dias). O `.splits` e o `marketCap` do Yahoo são **móveis** — daí o D-08. Os dados da CVM (cache local) são imutáveis.
