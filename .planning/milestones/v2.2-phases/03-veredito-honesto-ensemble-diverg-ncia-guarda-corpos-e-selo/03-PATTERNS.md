# Phase 3: Veredito Honesto — Ensemble, Divergência, Guarda-corpos e Selo - Pattern Map

**Mapped:** 2026-07-12
**Files analyzed:** 5 (refator — nenhum arquivo novo)
**Analogs found:** 5 / 5 (todos analogs no MESMO codebase — refator puro)

> Fase de **refator**, não de features novas. Cada comportamento novo (VER-01, ENS-01, SAN-01,
> VER-02) tem um precedente exato no próprio funil — o mapa abaixo aponta o molde a copiar e as
> linhas a mexer. **Constraint travado em todos os mapeamentos:** `selo.py` NUNCA importa `report.py`
> (firewall testado em `tests/test_selo.py:136`). Toda mudança de comportamento acontece na borda do
> veredito em `report.py`; `selo.py` só pode ganhar, no máximo, um prefixo/faixa novo a reconhecer.

## File Classification

| Arquivo a modificar | Role | Data Flow | Analog (mesmo codebase) | Match |
|---------------------|------|-----------|--------------------------|-------|
| `src/analista/report/report.py` (VER-01 — subst. ramo `:296-319`) | veredito aggregation (funil) | transform | ramo DDM `report.py:320-343` (SUB/NO INTERVALO/SOBRE) | exact |
| `src/analista/report/report.py` (ENS-01 — ensemble + bandeira) | veredito aggregation (funil) | transform | `cli.py:243-247` (`divergencia_entre_lentes` + aviso) | exact |
| `src/analista/report/report.py` (SAN-01 — guarda-corpo reetiqueta) | guarda-corpo na borda | transform | `_guarda_faixa_ddm()` `report.py:65-93` | exact |
| `src/analista/report/report.py` (VER-02 — fronteiriço range) | veredito aggregation (funil) | transform | ramo de suspensão `report.py:296-319` (VERIFICAR + intrínseco exibido) | role-match |
| `src/analista/report/report.py` (novos campos + render) | dataclass + render markdown | transform | `AnaliseAcao` `:23-63` + bloco motor `relatorio_markdown:594-606` | exact |
| `src/analista/report/selo.py` (novo prefixo/faixa, se necessário) | selo derivation (firewall puro) | transform | `faixa_do_veredito()` `selo.py:88-102` + overlay VERIFICAR `:119-122` | exact |
| `src/analista/core/comparables.py` (SAN-01 fonte pares) | pure helper (core) | transform | `preco_alvo_por_regressao()` `:181-216` + `RegressaoPL` freios `:120-133` (REUSAR, s/ editar) | reuse |
| `src/analista/cli.py` (render — via markdown) | render surface (CLI) | transform | `cmd_analyze` `:104-125` (imprime `relatorio_markdown`) | exact |
| `app.py` (render bandeira/range/reetiqueta) | render surface (Streamlit) | transform | bloco veredito+selo `app.py:880-942` | exact |

---

## Pattern Assignments

### VER-01 — selo consome o motor do arquétipo (subst. ramo `report.py:296-319`)

**Analog primário:** ramo DDM `report.py:320-343` (a lógica SUB/NO INTERVALO/SOBRE que o motor
passará a alimentar). **Analog secundário:** o próprio ramo a substituir `:296-319`.

O ramo de suspensão D-06 hoje SEMPRE estampa `VERIFICAR` quando `a.motor != "ddm"` — é este `if`
que o VER-01 **substitui** por veredito real derivado de `a.intrinseco_motor` + banda do ensemble.
A banda (`vmin/vmax`) e a comparação `preço vs banda` já existem prontas no ramo DDM logo abaixo;
o VER-01 faz o motor do arquétipo alimentar `vmin/vmax` e reusa a MESMA árvore de comparação.

**Ramo a substituir** (`report.py:296-319`):
```python
    if a.motor != "ddm":
        # Suspensão D-06 ... o SELO ainda consome só o DDM até VER-01/Fase 3 ...
        if a.intrinseco_motor is not None:
            ref = f"intrínseco ≈ R$ {_br(a.intrinseco_motor)} ({a.motor_rotulo or a.motor})"
        else:
            ref = f"motor '{a.motor}' ({a.motor_rotulo or a.motor})"
        a.veredito = (
            f"VERIFICAR — arquétipo {a.arquetipo}: referência primária pelo {ref}; ..."
        )
```

**Molde da faixa a copiar** — a árvore de comparação `preço vs vmin/vmax` do ramo DDM
(`report.py:320-343`), que o VER-01 passa a alimentar com a banda do motor/ensemble:
```python
    elif a.vmin is not None and a.vmax is not None and a.preco_atual:
        if a.preco_atual < a.vmin:
            ...
            a.veredito = f"SUBAVALIADA — preço R$ {_br(a.preco_atual)} abaixo do intervalo intrínseco R$ {_br(a.vmin)}–{_br(a.vmax)}"
        elif a.preco_atual > a.vmax:
            a.veredito = f"SOBREAVALIADA — preço R$ {_br(a.preco_atual)} acima do intervalo intrínseco R$ {_br(a.vmin)}–{_br(a.vmax)}"
        else:
            a.veredito = f"NO INTERVALO — preço R$ {_br(a.preco_atual)} dentro de R$ {_br(a.vmin)}–{_br(a.vmax)}"
```

**Regra de reuso (D-01):** os prefixos `SUBAVALIADA` / `NO INTERVALO` / `SOBREAVALIADA` já são casados
por `selo.faixa_do_veredito()` (`selo.py:96-102`) → o selo passa a consumir o motor **sem tocar
`selo.py`**. A banda `vmin/vmax` para o motor não-DDM vem do min/max entre motor primário e
contraponto (ENS-01, abaixo); fallback = `intrinseco_motor ± margem_seg` config-driven.

**Pitfall travado:** o precedente das flags de risco DDM (`report.py:325-337`, VULC3) que emite
`VERIFICAR — ... contradizem a tese de desconto` deve continuar disparando também no ramo do motor —
`test_vulc3_regressao` trava "veredito começa com VERIFICAR" por armadilha real (payout>100%), que é
distinto da suspensão D-06 por roteamento.

---

### ENS-01 — ensemble motor×contraponto + bandeira de divergência

**Analog:** `cli.py:243-247` — o único ponto do codebase que já pluga `divergencia_entre_lentes()`.

O helper PURO já existe e está testado; a Fase 3 o move do comparador multi-ticker para o funil
single-stock. **Não editar `comparables.py`** — só chamar.

**Analog de chamada** (`cli.py:243-247`):
```python
            divergiu, razao = cmp.divergencia_entre_lentes(ddm_mid[tk], pa.preco_alvo)
            if divergiu:
                avisos.append(
                    f"⚠ {tk}: lentes divergem ~{razao:.1f}× (DDM R$ {ddm_mid[tk]:.2f} × regressão "
                    ...
```

**Helper a reusar** (`comparables.py:87-107`, PURO, never-raise):
```python
def divergencia_entre_lentes(v_a, v_b, limiar=LIMIAR_DIVERGENCIA) -> tuple:
    """... devolve (divergiu: bool, razao = maior/menor). Limiar default 2.0.
    Dado ausente/inválido em QUALQUER lente → (False, 1.0)."""
    if v_a is None or v_b is None or v_a <= 0 or v_b <= 0:
        return (False, 1.0)
    maior, menor = max(v_a, v_b), min(v_a, v_b)
    razao = maior / menor
    return (razao >= limiar, razao)
```
`LIMIAR_DIVERGENCIA = 2.0` já é constante de módulo (`comparables.py:84`) — não inventar novo knob.

**Onde plugar no funil:** após o dispatch do motor (`report.py:192-230`, onde `a.intrinseco_motor`
fica gravado) e antes/junto do bloco de veredito (`:278-343`). O contraponto universal (D-02) é o
DDM que já roda sempre — usar o mid do DDM (ex.: `a.ddm_h`/`a.ddm_constante`, ou o mid de `vmin/vmax`
da matriz) como `v_b` contra `a.intrinseco_motor` como `v_a`.

**Bandeira/hipótese por template (D-03)** — copiar o padrão de dicionário-curado de
`report._MATRIZ_LEITURA` (`report.py:458-488`), chaveado por `(arquétipo, sinal)`:
```python
_MATRIZ_LEITURA: Dict[tuple, str] = {
    ("SUBAVALIADA", "atencao"):
        "Fundamentalmente descontada, porém o preço perdeu a tendência — ...",
    ...
}
```
(Espelha também o `_MATRIZ` de `selo.py:48-55` — quadrante por tupla-chave, copy estável testável
por golden.) A hipótese ENS-01 vira `_HIPOTESE_DIVERGENCIA[(arquetipo, sinal_da_divergencia)]` com
fallback genérico "modelos divergem ~Nx" quando a tupla não resolve frase.

**Precedente de bandeira já emitida no funil** (`report.py:333-337`) — ponto natural de extensão:
```python
                a.veredito = (
                    f"VERIFICAR — preço R$ {_br(a.preco_atual)} abaixo do intervalo intrínseco "
                    f"R$ {_br(a.vmin)}–{_br(a.vmax)}, mas sinais de risco ({', '.join(motivos)}) "
                    f"contradizem a tese de desconto: possível divergência de modelo."
                )
```

---

### SAN-01 — guarda-corpo anti-aberração (reetiqueta "evitar")

**Analog EXATO:** `_guarda_faixa_ddm()` (`report.py:65-93`) — precedente literal de guarda-corpo na
borda do veredito: marca uma flag, mexe só em `vmin/vmax`/veredito, adiciona alerta honesto, NÃO toca
`core/` nem o firewall. Chamado em `report.py:295`, logo antes do bloco de veredito.

**Molde a copiar** (`report.py:81-93`):
```python
    if a.vmax is None:
        return
    faixa_negativa = a.vmax <= 0
    faixa_degenerada = a.vmin == 0 and a.vmax == 0
    if faixa_negativa or faixa_degenerada:
        a.ddm_inaplicavel = True
        a.vmin = None
        a.vmax = None
        a.alertas.append(
            "DDM estruturalmente inaplicável a este perfil (payout baixo / alto capex ou "
            "lucro negativo): a faixa por dividendos resultou negativa ou zero e NÃO é "
            "preço-alvo — por isso não é exibida como intrínseco."
        )
```

**Nova função `_guarda_san01(a, c, cfg)`** com a mesma assinatura/estilo (novo campo-flag em
`AnaliseAcao` à la `ddm_inaplicavel`, alerta honesto, reetiqueta na borda). Regra literal do SAN-01
(D-04/D-05): `intrínseco < 0,5 × valor-implicado-pelos-pares` **E** `ROE > 15%` **E**
`corte de payout > 40%` → troca "evitar" por texto literal *"DDM conservador demais para este perfil
— ver motor primário do arquétipo"*, mantendo o número visível. Chamar no mesmo ponto de
`_guarda_faixa_ddm` (perto de `:295`), sobre o veredito já montado.

**Fonte do "valor dos pares" (D-04)** — REUSAR (sem editar) `preco_alvo_por_regressao()` +
`RegressaoPL`, com os freios de degradação já prontos:
```python
# comparables.py:120-133
    @property
    def amostra_pequena(self) -> bool:   # n < 10 → regressão instável
        return self.n < LIMIAR_AMOSTRA
    @property
    def r2_baixo(self) -> bool:          # R² < 0,5 → preço-alvo pouco confiável
        return self.r2 < LIMIAR_R2
```
**Degradação (D-04):** quando a regressão não roda (`r2_baixo`/`amostra_pequena`), a condição de pares
**não é avaliada** e o guarda-corpo cai para as 2 restantes (`ROE > 15%` E `corte payout > 40%`).
NUNCA puxa rede. Os "sinais canônicos" ROE/payout vêm de `c.roe_valuation()` / `c.payout_valuation()`
(o `intrinseco_motor` já usa esses métodos em `report.py:206-207`).

**Config-driven na borda:** thresholds (`0.5`, `ROE 15%`, `payout 40%`) via `cfg["..."]` seguindo o
padrão dos limiares do projeto; expor em `config.yaml` quando fizer sentido.

---

### VER-02 — dúvida honesta no caso-fronteira (range + bandeira)

**Analog:** o ramo de suspensão `report.py:296-319` — mesma estrutura de "estampar VERIFICAR + exibir
número(s) do motor como conteúdo, sem faixa cravada". VER-02 roda o motor de cada candidato e monta o
range em vez do intrínseco único.

**Entrada pronta** (`report.py:55-56`, populada na Fase 1):
```python
    arquetipo_fronteirico: bool = False                    # conflito real de sinais (ARQ-02)
    arquetipo_candidatos: List[str] = field(default_factory=list)
```

**Dispatch a reaproveitar por candidato** (`report.py:202-229`) — o mesmo `if a.motor == "rim"/…`
que já mapeia motor→intrínseco; VER-02 chama esse dispatch para cada `arquetipo_candidatos`, coleta os
intrínsecos que resolveram e monta `range [menor..maior]` + bandeira "classificação incerta entre X e Y".

**Supressão de faixa no selo (D-06):** reusar o overlay VERIFICAR já existente — o prefixo `VERIFICAR`
faz `selo.montar_selo` suprimir faixa/rótulo sem tocar o firewall:
```python
# selo.py:119-122
    verificar = bool(veredito) and veredito.startswith("VERIFICAR")
    if verificar:
        return Selo(bsd=bsd, cor=cor, qualidade=qualidade,
                    faixa_preco=None, rotulo=None, verificar=True)
```
O selo **não estampa** faixa/rótulo no fronteiriço; o range/candidatos aparecem como conteúdo exibido.
**Degradação:** se um motor candidato falha (None), listar só os que resolveram lado a lado, sem forçar
um range de 1 ponto.

---

### Novos campos em `AnaliseAcao` + render

**Analog:** o próprio dataclass `AnaliseAcao` (`report.py:23-63`) já tem o padrão de blocos aditivos
comentados por fase (`# --- Fase X v2.2: ... (aditivo, read-only) ---`). Adicionar os campos do ENS-01
(ex.: `divergencia_ativa: bool`, `divergencia_razao: Optional[float]`, `divergencia_hipotese: str`),
SAN-01 (flag de reetiqueta) e VER-02 (ex.: `veredito_range: Optional[tuple]`) seguindo esse padrão,
com defaults degradáveis.

**Render markdown** — analog exato: o bloco "Valuation pelo motor do arquétipo"
(`relatorio_markdown`, `report.py:594-606`), que já exibe `intrinseco_motor` condicionalmente:
```python
    ddm_e_lente = a.motor != "ddm"
    if ddm_e_lente and a.intrinseco_motor is not None:
        L.append(f"## Valuation pelo motor do arquétipo ({a.arquetipo})")
        L.append(f"- **{a.motor_rotulo or a.motor}: R$ {_num(a.intrinseco_motor)}** (motor do arquétipo)")
        L.append("")
```
A bandeira de divergência e o range fronteiriço entram como novos blocos `L.append(...)` na mesma
seção de Veredito (`report.py:645-653`). Formatação ptBR pelo helper `_br()` (`report.py:539-543`)
no banner e `_num()` (`:535`) na CLI.

---

## Shared Patterns

### Firewall selo↛report (INEGOCIÁVEL)
**Source:** `selo.py:10-13` (docstring) + `tests/test_selo.py:136` (`test_firewall_selo_nao_importa_report`)
**Apply to:** TODA mudança de comportamento — acontece na borda do veredito em `report.py` ou como
novos primitivos passados a `montar_selo`. `selo.py` só recebe `(bsd, veredito str, cfg)` e, no máximo,
ganha um prefixo/faixa novo a reconhecer em `faixa_do_veredito` — nunca importa `report`.
```python
# selo.py:11
- FIREWALL: este módulo NUNCA importa `report.py`. Recebe só PRIMITIVOS (bsd float,
  veredito str, cfg dict). É `report.py` quem chama `montar_selo` — nunca o contrário.
```

### Guarda-corpo config-driven na borda
**Source:** `_guarda_faixa_ddm()` `report.py:65-93` (molde do SAN-01)
**Apply to:** SAN-01 e qualquer supressão/reetiqueta. Padrão: flag em `AnaliseAcao` + mexer só em
`vmin/vmax`/veredito + `a.alertas.append(<motivo honesto>)`. NÃO tocar `core/`. Chamar perto de `:295`.

### Overlay/prefixo VERIFICAR como "válvula" de supressão de faixa
**Source:** `selo.py:119-122` + `faixa_do_veredito()` `:88-102`
**Apply to:** VER-02 (fronteiriço) e ramo residual de VER-01 sem preço-alvo. O prefixo já suprime
faixa/rótulo sem acoplar `selo`↔`report`. Se um prefixo/rótulo mudar deliberadamente, atualizar
`faixa_do_veredito` (`selo.py:88`) **e** `report._veredito_token` (`report.py:491`) JUNTOS e
rebaselinar `test_selo`/`test_vulc3_regressao` com intenção declarada.

### Copy curada por tupla-chave (template ENS-01 hipótese)
**Source:** `report._MATRIZ_LEITURA` `report.py:458-488` + `selo._MATRIZ` `selo.py:48-55`
**Apply to:** hipótese da bandeira ENS-01, chaveada por `(arquétipo, sinal_da_divergência)`, copy
estável no código, testável por golden, com fallback genérico.

### Helper puro reutilizado no funil
**Source:** `divergencia_entre_lentes()` `comparables.py:87-107` (já usado em `cli.py:243`)
**Apply to:** ENS-01 — chamar no funil single-stock; NÃO editar o helper (never-raise, limiar 2.0 já
travado). `preco_alvo_por_regressao()`/`RegressaoPL` idem para o SAN-01: reusar, não editar.

### Consistência cross-modo (Core Value)
**Source:** `test_consistencia_modos.py` + métodos canônicos `*_valuation()` de `fundamentals.py`
**Apply to:** o ensemble/veredito novo deve sair dos MESMOS números-síntese (`roe_valuation`,
`payout_valuation`, `lpa_valuation`, `intrinseco_motor`) que Analisar/Garimpo/Ranking consomem — nunca
o cru de 1 ano. O `intrinseco_motor` já obedece isso (`report.py:195`, "NUNCA o cru — Pitfall 2/FIX-04").

---

## No Analog Found

Nenhum. Fase de refator — todos os comportamentos têm precedente exato no próprio codebase. As
constantes/campos genuinamente novos (margem de segurança fixa do fallback D-01, thresholds do SAN-01,
campos de divergência/range em `AnaliseAcao`) seguem os padrões locais de `cfg[...]` config-driven,
constantes de módulo `LIMIAR_*` (`comparables.py:72-84`) e blocos aditivos comentados por fase no
dataclass — não exigem padrão externo de RESEARCH.md.

---

## Testes que travam comportamento (não quebrar sem intenção declarada)

| Teste | Invariante | Impacto da Fase 3 |
|-------|-----------|--------------------|
| `tests/test_selo.py` | cores + rótulos `_MATRIZ` + **firewall selo↛report** (`:136`); prefixos SUB/NO INTERVALO/SOBRE→Barato/Justo/Caro (`:69-75`) | verde se firewall preservado; rebaselinar SÓ se prefixo/faixa mudar deliberadamente (`faixa_do_veredito` + `_veredito_token` juntos) |
| `tests/test_vulc3_regressao.py` | veredito começa com "VERIFICAR" por armadilha real (payout>100%) — NÃO a suspensão D-06 | preservar o ramo de flags de risco (`report.py:325-337`) também no caminho do motor |
| `tests/test_guardrails_fix06.py` / `test_guardrails_ddm.py` | banda `vmin/vmax` = min/max da matriz; guarda-corpo DDM | não regredir `_guarda_faixa_ddm`; o SAN-01 é aditivo (novo guarda-corpo) |
| `tests/test_consistencia_modos.py` | mesmo número entre Analisar/Garimpo/Ranking | ensemble/veredito novo não pode divergir os 3 modos |
| `tests/test_ddm.py` | DDM Itaú ≈ R$37,22 (input fixo) | `core/ddm.py` INTOCADO |
| `tests/test_ranking_freio.py` / `test_report.py` / `test_arquetipo*.py` | roteamento + freio do Ranking (01-08) | preservar |

---

## Metadata

**Analog search scope:** `src/analista/report/` (report.py, selo.py, presentation.py), `src/analista/core/`
(comparables.py, motores.py, lentes.py, arquetipo.py), `src/analista/cli.py`, `app.py`, `tests/`
**Files scanned:** 9 lidos na íntegra/targeted + grep em tests
**Pattern extraction date:** 2026-07-12
</content>
</invoke>
