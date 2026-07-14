---
phase: 07-blindagem-processual-blind
fixed_at: 2026-07-13
review_path: .planning/phases/07-blindagem-processual-blind/07-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 10
skipped: 15
status: partial
---

# Fase 7: Relatório de Correção do Code Review

**Escopo pedido:** os 5 BLOCKERs (CR-01..CR-05) + WR-04.
**Corrigidos:** 6 no escopo + 4 adjacentes de graça (WR-02, WR-03, WR-11, WR-13, IN-02, IN-04).

**Hard constraints (verificados):**
- `git diff -- src/` → **vazio**. Zero código de produção tocado.
- `config.yaml` → **byte-idêntico**. `yaml.safe_load(antes) == yaml.safe_load(depois)` → `True`.
- Nenhum número esperado de teste existente foi editado.
- Nenhum `--no-verify`. O hook estava ativo em todos os 6 commits.

**Suíte:** `422 passed, 1 skipped, 38 deselected, 2 xfailed` — 0 failed, 0 XPASS.
(Baseline era 420; +2 são os invariantes libertados pelo WR-04. Quarentena inalterada: 38.)

---

## Corrigidos

Cada fix foi validado **executando a evasão** que o reviewer descreveu, antes e depois.

### CR-01 — `xfail(condição_falsa, strict=True)` — commit `59d6c3a`
`tests/helpers_blindagem.py`. Qualquer condição (posicional ou `condition=`) e `run=False`
desqualificam o xfail da lista de tolerados do BLIND-04a.
**Evasão executada:** `@pytest.mark.xfail(False, strict=True)` + golden `ITUB4 == 32.88`
→ **antes: TOLERADO** (BLIND-04a verde) · **depois: OFENSOR não tolerado** (BLIND-04a vermelho).
**Sem falso positivo:** os 2 xfail legítimos (incondicionais) seguem tolerados.

### CR-02 + CR-03 — as duas cegueiras do detector — commit `cc25650`
`tests/helpers_blindagem.py`. Ticker em constante de módulo (rota simétrica a `nivel_modulo`)
e nível que chega ao assert **através de um helper** (nova rota (d): seguir a chamada).
**Evasões executadas:** `ALVOS = {"ITUB4": 32.88}` + `TICKERS=[...]`, e `_confere(v, 32.88)`
→ **antes: invisíveis** · **depois: as duas viram OFENSOR não tolerado.**
**Falsos positivos na suíte real: 0.**

> **Não apliquei o fix literal do review.** Ele propunha "qualquer constante numérica no corpo
> já é nível". Medido: isso arrasta as *factories* de fixture junto e produz **37 falsos
> positivos** — empurraria 37 testes bons (invariantes e contratos inclusive) para a quarentena.
> Um guarda-corpo assim é desinstalado por irritação antes de pegar o primeiro overfit (é a lição
> explícita do 07-04, o regex que casava `MACD12`). O critério correto é **"helper que CONFERE
> (tem `assert`)"**, não "helper que CONSTRÓI". Com ele: 0 falsos positivos.
>
> O snippet de CR-02 do review também tinha um bug: varria a árvore inteira, colhendo nomes de
> variáveis **locais de outras funções** → 4 falsos positivos. Corrigido para escopo de módulo.

**Adjacentes de graça:** WR-13 (`rglob` — criar uma pasta sumia com o golden) e IN-02
(identificador relativo à raiz do repo). Evasão em `tests/sub/` também executada e pega.

### CR-04 — o hook não cobria os arquivos que *governam* o golden — commit `f69d338`
`.githooks/commit-msg` + `tests/test_blindagem_hook.py`. O conjunto "golden" passa a incluir
`tests/classificacao.yaml`, `tests/conftest.py`, `tests/helpers_blindagem.py` e `pyproject.toml`.
**Evasão executada em repo limpo com hook instalado:** `config.yaml` + `tests/classificacao.yaml`
(mudar a categoria para `golden_nivel` deseleciona o teste que ficou vermelho)
→ **antes: rc=0, commit criado** · **depois: rc=1, BLOQUEADO.** 6/6 co-changes de governança bloqueiam.
**Sem falso positivo:** `config.yaml` + `calibracao.lock.yaml` (o caminho sancionado), `config.yaml`
sozinho, `tests/` sozinho e a justificativa econômica legítima seguem passando.

### WR-02 / WR-03 / WR-11 / IN-04 — commit `4c250ab` (adjacentes, mesmo hook)
Ticker minúsculo (`itub4`), ticker no **segundo** trailer, citação morta de `config.yaml:238` e
match do ticker em posição de valor no JSON. **Evasões executadas:** as 3 ofensivas iam rc=0;
agora rc=1. Harness final: **9/9 bloqueiam, 6/6 controles de falso positivo passam.**

### CR-05 — `veredito.margem_seguranca` sem dente — commit `20160c7`
`tests/test_blindagem_orcamento.py`. `user_control` entra na comparação de valores; os blocos dele
entram na varredura de ticker; o caminho declarado tem que existir no config.
**Evasão executada:** `margem_seguranca: 0.15 → 0.30` (muda a escala do `V` da carteira inteira)
→ **antes: 420 passed, suíte VERDE** · **depois: `test_knobs_batem_com_o_lock` VERMELHO.**
Segunda evasão (comentário com ticker no bloco `veredito`) → agora vermelha também.
**Sem falso positivo:** config intacto → verde.

### WR-04 — funções mistas — commit `3dc2082` (**parcial — ver abaixo**)
`tests/test_motores.py`, `tests/test_capm_local.py`, `tests/classificacao.yaml`.
As 2 funções nomeadas pelo review foram cindidas: o assert relacional virou função `invariante`
(volta ao run default), a banda de nível ficou na função `golden_nivel`. Os asserts são os
**mesmos** — só mudaram de função. Os 4 testes registrados no `classificacao.yaml` no mesmo commit.

---

## ABERTO — WR-04 é maior do que o review afirmou

O review nomeou **2** funções mistas. A auditoria por AST (feita nesta sessão) encontra **20**
funções quarentenadas com invariantes estruturais presos — que hoje **já não rodam** e que a
Fase 10/12 vai **deletar junto com o golden**, em silêncio. Amostra:

| Função quarentenada | Invariante preso que morre junto |
|---|---|
| `test_arquetipo_roteamento::test_financeira_rim_destrava_vs_ddm...` | `a.motor == 'rim'`, `a.intrinseco_motor > vpa` |
| `test_growth_reconciliacao::test_trava_ke_quando_g_fund_supera_ke` | `a.g_alto == a.ke` |
| `test_growth_reconciliacao::test_g_fund_menor_que_cagr_vira_teto...` | `a.g_alto == a.g_fundamentos` |
| `test_guardrails_ddm::test_san01_reetiqueta_aberracao_itub4_like` | `a.san01_reetiquetado is True`, `'Evitar' not in a.veredito` |
| `test_motores::test_rota_seguradora_nao_pega_banco` | `a.motor == 'rim'` |
| `test_home_feed::test_cotacoes_contrato_e_variacao_do_dia` | contrato de chaves da cotação |
| ... (mais 14) | roteamento, contratos, degradação |

**Não cindi as outras 18 nesta passada, deliberadamente:** é um refactor de ~18 funções com
duplicação de fixture, e algumas das metades "invariante" carregariam ticker + constante de módulo
(ex.: `ANO_EXTRAORDINARIO` em `test_vulc3_regressao`) e seriam **pegas pelo BLIND-04a agora
endurecido** — ou seja, exigem decisão de classificação, não recorte mecânico. Fazer isso às cegas
dentro de um fix pass é exatamente o tipo de deriva semântica que esta fase existe para impedir.
**Recomendação: task própria, antes da Fase 10.**

O fix sistêmico correto (e que fecha a classe inteira) é um teste `contrato` que **proíbe
quarentenar uma função mista** — ele só pode ser escrito depois das 18 cisões, senão nasce vermelho.

---

## Skipped (documentados, fora do escopo pedido)

WR-01 (comentário órfão acima da chave de bloco), WR-05 (`BLIND_BOOTSTRAP=1` mudo),
WR-06 (completude quebra `--lf`/`--sw`), WR-07 (gerador interpola YAML), WR-08 (gerador ignora
`returncode`), WR-09 (`# REVISAR` apagado pelo próprio ciclo), WR-10 (`choque_nominal` pula a perna
do lucro em silêncio), WR-12 (`pyproject.toml` não se auto-protege), IN-01, IN-03, IN-05, IN-06, IN-07.

Nenhum é BLOCKER e nenhum é adjacente aos fixes feitos. **WR-10 e WR-12 são os mais graves da lista**
e merecem ser puxados a seguir: WR-10 pode fabricar o veredito "doença curada"; WR-12 permite
deselecionar as invariantes pelo `addopts` em silêncio (o CR-04 já protege o `pyproject.toml` contra
co-change com knob, mas não contra a edição isolada).

---

_Fixed: 2026-07-13 · Fixer: Claude (gsd-code-fixer) · Iteration: 1_
