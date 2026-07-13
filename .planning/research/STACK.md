# Stack Research

**Domain:** Fidelidade do valuation — correção de ingestão, primitivas, `g`/`Ke` e motores
**Researched:** 2026-07-13
**Confidence:** HIGH — séries do BCB e chaves do Yahoo verificadas ao vivo, não de memória

## Headline

**Nenhuma dependência nova é necessária.** O marco se resolve com `requests`, `yfinance`,
`pandas` e `numpy` — tudo já instalado. A tentação de adicionar uma biblioteca de validação de
dados (`pandera` / `great-expectations`) deve ser **rejeitada** (ver "O que NÃO adicionar").

O único componente novo é uma função: `macro.ipca_ciclo(anos=10)`, irmã simétrica da
`macro.selic_ciclo_para_capm` que já existe.

---

## 1. IPCA-ciclo (BCB SGS) — série confirmada ao vivo

O marco precisa de `π_ciclo` (média 10a do IPCA) para derivar o `g_cap` nominal.

| Série | O que é | Valor (jun/2026) | Uso |
|-------|---------|------------------|-----|
| **SGS 13522** | **IPCA acumulado 12 meses (%)** | 4,64 | ✅ **usar esta** |
| SGS 433 | IPCA variação mensal (%) | 0,16 | precisaria compor 12 a 12 |
| SGS 432 | Selic meta (% a.a.) | 14,25 | já usada (`rf_ciclo`) |
| SGS 4389 | Selic efetiva (% a.a.) | 14,15 | — |

**Por que 13522 e não 433:** a 13522 já entrega a taxa anualizada, então a média simples da série
É o `π_ciclo`. Com a 433 seria preciso compor janelas móveis de 12 meses — mais código, mesmo
resultado. E a 13522 **espelha exatamente o padrão que o projeto já usa** para a Selic
(`ingest/macro.py:87-100`): puxar a série, tirar a média da janela.

**Medido (jul/2016 – jun/2026, n=120 meses):**

```
π_ciclo  = 5,18%     (SGS 13522, média simples)
rf_ciclo = 9,58%     (SGS 432, via macro.selic_ciclo_para_capm — a função que o app já usa)
```

**Integração:** `macro.ipca_ciclo(anos=10)` como irmã simétrica de `selic_ciclo_para_capm` —
mesmo padrão de degradação (série → fallback constante), mesmo tratamento de erro, mesma janela.

**O ponto crítico do desenho: a janela do IPCA DEVE ser a mesma do `rf`.** É isso que torna o
valuation invariante à inflação — se a inflação cair, `rf` e `g_cap` caem juntos e o spread
`(Ke − g)` fica estável. Hoje a inflação entra no `Ke` e não entra no `g`, e o modelo "vê"
inflação como destruição de valor. Esse é literalmente o bug de ~5 pontos.

**Risco/fallback:** a API do BCB responde bem para séries mensais (0,6s medido), mas a série
**diária** da Selic com janela de 10 anos **estoura timeout** — o `macro.py` já contorna isso.
Fallback: constante em `config.yaml` (`ipca_fallback: 0.052`), espelhando o `selic_fallback`.

---

## 2. PIB real de longo prazo — **constante, não série**

**Recomendação: constante documentada de 2,0%.**

É um parâmetro de *regime*, não uma medição. Puxar o PIB corrente (ou a expectativa Focus)
introduz volatilidade cíclica num número que deveria ser estrutural. A decomposição explícita
(`inflação + PIB real`) é mais auditável para o usuário do que a alternativa de Damodaran (usar
o `rf` como proxy do crescimento nominal), e o PIB real é o único termo que fica fixo.

**Sensibilidade medida** (π_ciclo = 5,18%; Ke = rf + 1,0 × ERP 4,5%):

| PIB real | g_cap | spread (rf − g) | teto de P/L |
|----------|-------|-----------------|-------------|
| 1,5% | 6,76% | 2,82% | 13,7x |
| **2,0%** | **7,28%** | **2,29%** | **14,7x** |
| 2,5% | 7,81% | 1,77% | 16,0x |

O **P/L mediano de mercado do universo é 9,9x**. Com o `g` de hoje (2,5% *real* descontado contra
um Ke *nominal*), o teto é **7,8x** — abaixo da mediana de mercado. É exatamente por isso que o
motor carimba "caro" em 4 de cada 5 ações: ele é *matematicamente incapaz* de justificar a ação
mediana da bolsa. Qualquer PIB real entre 1,5% e 2,5% resolve; 2,0% é o meio defensável.

Este é **1 dos 3 graus de liberdade** do modelo-alvo. Não deve virar knob calibrável.

---

## 3. Reconciliação de dados — **asserts puros, sem biblioteca**

**Rejeitar `pandera` e `great-expectations`:**

- O pipeline tem 104 tickers e um punhado de invariantes. As checagens que teriam pego 4 dos 5
  bugs são aritmética de uma linha cada.
- Ambas adicionam peso, um DSL para aprender, e uma camada de indireção entre o bug e a mensagem
  de erro — num projeto cujo constraint declarado é **custo zero e sem backend**.
- Os asserts devem **emitir aviso e marcar confiança baixa**, não levantar exceção. Isso é
  política de produto (o contrato `never-raise` que o ingest já tem), não algo que uma lib de
  validação genérica faça bem.

**Os 4 asserts — a instalar ANTES de consertar qualquer bug (eles SÃO o teste de regressão):**

| Assert | Pega |
|--------|------|
| `num_acoes × preço ≈ market_cap` (Yahoo) | GOAU4 (3× errado), CGRA4 (escala 1000×) |
| `num_acoes` estável ano-a-ano salvo evento societário | ITUB4 2019 (salto de 1.131×), BRSR6 (205.000×) |
| `dividendos_CVM ≈ DPA_yahoo × num_acoes` | BRSR6, SBSP3, BPAC11 (JCP perdido) |
| `PL` e `lucro` na mesma base (controlador ou total) | MRFG3, CSNA3, ALUP11, EQTL3 |

---

## 4. Beta setorial + Blume — **nada novo, só aritmética**

O projeto já coleta tudo: `beta` individual (`prices.py:178-182`, Cov/Var 60m) e `setor` da CVM
(`cad_cia_aberta.csv`). Beta setorial = `mediana(betas dos pares do mesmo setor)`; Blume =
`β_ajustado = 0,33 + 0,67 × β`.

**Nota crítica:** o `config.yaml:235` justifica o `ke_teto: 0.13` dizendo *"beta ajustado (Blume
puxa betas para 1,0)"* — mas **Blume não está implementado** (`grep -rni blume` → zero ocorrências)
e a justificativa é **aritmeticamente falsa**: Blume daria `ke_rim` de 15,9% para o ITUB4, não 13%.
Para o CAPM dar 13,00% seria preciso `β = 0,556`, e Blume empurra betas *para cima* de 0,556.

Implementar Blume de verdade **não muda nada** nos bancos hoje, porque o clamp absorve tudo. Ele só
passa a importar depois que o clamp sair — e o clamp só pode sair depois que o `g` for consertado.

---

## 5. Número de ações — trocar a chave do Yahoo

Verificado ao vivo:

```
ITUB4   sharesOutstanding        =  5.404.129.565   ← só a classe PN (o app usa ESTA)
        impliedSharesOutstanding = 11.021.872.542   ← total ON+PN (a correta)
ITUB3   impliedSharesOutstanding = 11.021.358.928   ← bate com ITUB4 ✓
PETR4   sharesOutstanding        =  5.446.501.379
        impliedSharesOutstanding = 13.663.485.771
```

`build.py:102` usa `sharesOutstanding` no fallback → sempre que o LPA da CVM falta num ano, o
LPA/DPA/VPA daquele ano ficam **~2× inflados** para qualquer ação com ON+PN. Só funciona por acaso
em BBAS3 (classe única).

**Correção:** trocar por `impliedSharesOutstanding`, com fallback para *abortar o ano* (nunca usar
a contagem de uma classe só). E a fonte primária (`num_acoes = lucro/LPA`, `build.py:87`) precisa
usar o **lucro do controlador** (`3.11.01`/`3.09.01`), não o consolidado — é a raiz do erro de 3×
no GOAU4.

**Alternativa gratuita mais confiável?** Não há. A CVM publica o número de ações no formulário
cadastral, mas não no dataset DFP que o projeto consome. `impliedSharesOutstanding` + os asserts de
reconciliação é o melhor custo-benefício.

---

## O que NÃO adicionar

| Tentação | Por que não |
|----------|-------------|
| `pandera` / `great-expectations` | Peso e indireção para 4 asserts aritméticos. Ver §3. |
| Série de PIB (IBGE / Focus) | Volatilidade cíclica num parâmetro estrutural. Ver §2. |
| `statsmodels` para a regressão de pares | A regressão vai ser **aposentada** — é cega ao nível de preço (R² = 0,037; multiplicar todos os preços por 1,5 não muda um único upside). Não invista nela. |
| Provedor pago (Economatica, Bloomberg) | Viola o constraint de custo zero, que É o posicionamento do produto. |
| NTN-B + Focus como `rf` | "Mais correto" na teoria, mas acopla o app a duas séries frágeis, e o juro real longo BR carrega prêmio fiscal que mean-reverte. A Selic-ciclo é uma série, uma média, auto-atualizável e suave por construção — metade do argumento de "sem clamp". |

---

## Graus de liberdade do modelo-alvo: **3**

```
ERP      = 4,5%    (Damodaran mature market, SEM prêmio small-cap)
n_fade   = 5       (horizonte de convergência do ROE)
PIB_real = 2,0%    (constante estrutural)
```

Todo o resto é **derivado de dado ou de fonte externa**: `rf_ciclo` (SGS 432), `π_ciclo` (SGS 13522),
`β_setorial` (Yahoo + setor CVM), `ROE_T` e `retenção` (série da CVM).

Os ~20 knobs do bloco `motores:` (`config.yaml:229-264`) são o problema, não a solução — foram eles
que permitiram calibrar 4 parâmetros contra 4 observações. Com uma cesta de calibração de 20 tickers,
**3 graus de liberdade é o máximo defensável** (~7 observações por parâmetro).
