---
phase: quick
plan: 260720-kuc
type: execute
wave: 1
depends_on: []
files_modified: [app.py]
autonomous: true
requirements: [UI-RELABEL-RIM]

must_haves:
  truths:
    - "A manchete do intrínseco na aba Analisar exibe 'Intrínseco (RIM)', nunca 'Intrínseco (DDM)'."
    - "Nenhum bloco morto do ensemble (gated por campo REMOVIDO do dataclass) permanece em app.py."
    - "A copy visível ao usuário reflete RIM como motor único; 'DDM' só sobrevive onde nomeia a lente/fórmula que ainda existe (sub-tab Valuation (DDM), guarda ddm_inaplicavel, config key)."
    - "A fronteira config.yaml/calibracao.lock.yaml permanece VAZIA no diff; nenhum número/knob/engine tocado; pytest verde (0 failed)."
  artifacts:
    - path: "app.py"
      provides: "Aba Analisar com rótulo honesto (RIM) e sem código morto do ensemble"
  key_links:
    - from: "app.py m2.metric"
      to: "a.motor (sempre 'rim')"
      via: "rótulo estático 'Intrínseco (RIM)'"
      pattern: "Intrínseco \\(RIM\\)"
---

<objective>
Relabel "DDM"→RIM na aba Analisar do app.py e subtrair os blocos mortos do ensemble
(gated por campos já REMOVIDOS de `AnaliseAcao` na Fase 13 — RIM único).

Purpose: O rótulo da manchete do intrínseco MENTE hoje ("Intrínseco (DDM)") enquanto o
número exibido é a região do RIM (motor único). O projeto zela por rótulos que não mentem —
o DDM morreu como MOTOR (virou lente/fórmula de referência) e a copy precisa refletir isso.
Output: app.py corrigido — só UI/copy + subtração de código morto. Zero mudança de número,
knob, engine ou config.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md

<hard_boundary>
FRONTEIRA INVIOLÁVEL desta task (constraint do usuário):
- NÃO tocar em NENHUM número, knob, engine, `config.yaml`, `calibracao.lock.yaml`.
- `git diff config.yaml calibracao.lock.yaml` DEVE ficar VAZIO ao fim.
- Único arquivo modificado: `app.py`.
- NÃO tocar `src/analista/glossario.py` (glossário de help é compartilhado com CLI/report — fora de escopo).
- NÃO mexer em `CFG["ddm"]["sensibilidade"]` (é chave de config — leitura, não copy).
</hard_boundary>

<estado_confirmado>
Confirmei lendo report.py e app.py (NÃO confie cego no STATE.md — foi validado):

CAMPOS QUE EXISTEM em `AnaliseAcao` (report.py) — NÃO deletar quem os lê:
- `motor` (sempre "rim"), `motor_rotulo`, `intrinseco_motor`, `selo`, `ddm_inaplicavel`,
  `ddm_constante`, `ddm_h`, `pb_justo`, `v_ponte`, `payout_terminal`.

CAMPOS REMOVIDOS do dataclass (todo `getattr(a, X, False)` é sempre-False → código morto):
- `banda_do_motor`, `contraponto_valor`, `divergencia_ativa`, `divergencia_razao`,
  `divergencia_hipotese`, `arquetipo_incerto`, `candidatos_intrinsecos`,
  `veredito_range`, `san01_reetiquetado`.

Variáveis `_motor` e `_usa_motor` são usadas SÓ dentro da região 1015–1050 (grep confirmou).
`_usa_motor` é SEMPRE False (depende de `banda_do_motor`) → `_valor_intr` sempre cai em `intervalo`.

A lente DDM AINDA EXISTE como fórmula: o sub-tab "Valuation (DDM)" (~1448) renderiza
`a.ddm_constante`/`a.ddm_h` de verdade. Relabelar esse sub-tab para RIM MENTIRIA (mostra
números DDM, não RIM) → esse rótulo FICA "DDM". Idem a guarda `ddm_inaplicavel`: o campo
existe e a nota descreve a lente DDM — mantém o bloco, só ajusta a copy stale.
</estado_confirmado>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Corrigir o bug da manchete (Intrínseco RIM) e deletar o código morto do ensemble</name>
  <files>app.py</files>
  <action>
Região alvo: ~925–1055 da aba Analisar. Apenas subtração + correção do rótulo. NÃO mexer
fora dessa região (a copy dos outros sites é da Task 2).

1) DELETAR o comentário 925–935 e o bloco `if getattr(a,"san01_reetiquetado",False) or
   getattr(a,"divergencia_ativa",False):` inteiro (~936–954). Lê san01_reetiquetado,
   divergencia_ativa/razao/hipotese, contraponto_valor, intrinseco_motor, motor_rotulo —
   todos os gates são campos REMOVIDOS → bloco nunca renderiza.

2) DELETAR o bloco "Classificação incerta" `if getattr(a,"arquetipo_incerto",False):`
   (~956–986), incluindo seu comentário 956–958. Lê arquetipo_incerto, candidatos_intrinsecos,
   veredito_range — todos REMOVIDOS.

3) MANTER o bloco do Selo (~988–1005): `a.selo` EXISTE. Não tocar.

4) MANTER `intervalo = ...` (linha ~1008). DELETAR a supressão morta logo abaixo
   (comentário 1009–1012 + `if getattr(a,"arquetipo_incerto",False): intervalo = "—"` ~1013–1014).

5) SIMPLIFICAR a máquina `_motor`/`_usa_motor` (~1015–1039). Remover:
   - `_motor = a.motor or "ddm"` (o fallback "ddm" é stale; `a.motor` é sempre "rim").
   - o bloco `_usa_motor = (...)` (~1020–1025) e seus comentários — é sempre False.
   Substituir o cálculo de rótulo/valor (1028–1039) por:
   - rótulo ESTÁTICO `_label_intr = "Intrínseco (RIM)"` (curto — NÃO usar `a.motor_rotulo`,
     que é longo demais para um label de `st.metric`). Este é o CONSERTO do bug: hoje é sempre
     "Intrínseco (DDM)" porque a condição pende de `banda_do_motor` (removido → sempre False).
   - `_valor_intr = esc_md(intervalo)` (o `_usa_motor` sumiu; `intervalo` = faixa vmin–vmax do
     cálculo único do veredito/RIM — NÃO trocar o número exibido).
   Manter `m1..m5 = st.columns(5)` e todas as chamadas `m1.metric/.../m5.metric` intactas,
   inclusive `m2.metric(_label_intr, _valor_intr, help=h("valor_intrinseco"))`.

6) DELETAR o caption do contraponto (~1047–1055): `if _usa_motor and a.contraponto_valor is
   not None:` — `_usa_motor` sumiu e `contraponto_valor` foi removido → morto.

NÃO tocar do bloco da Margem de Segurança em diante (~1057+): é da Task 2 / intocado.
  </action>
  <verify>
    <automated>python3 -c "import ast; ast.parse(open('app.py').read())"</automated>
    Além disso rodar (todos devem retornar 0 linhas):
    `grep -nE "banda_do_motor|arquetipo_incerto|san01_reetiquetado|divergencia_|contraponto_valor|candidatos_intrinsecos|veredito_range|_usa_motor" app.py`
    E confirmar o conserto: `grep -c 'Intrínseco (RIM)' app.py` retorna >= 1.
  </verify>
  <done>
ast.parse OK; nenhum símbolo morto do ensemble restante em app.py; a manchete m2 exibe
"Intrínseco (RIM)"; nenhum número/coluna de métrica alterado; região 1057+ intocada.
  </done>
</task>

<task type="auto">
  <name>Task 2: Relabel de copy DDM→RIM (onde DDM nomeia o motor atual)</name>
  <files>app.py</files>
  <action>
Regra de julgamento (project core value: rótulo não pode mentir):
- Onde "DDM" nomeia o MOTOR/valuation ATUAL ou a manchete do intrínseco → vira "RIM"
  (ou "valor intrínseco" genérico). O número exibido acima é o RIM.
- Onde "DDM" nomeia a LENTE/fórmula que AINDA existe → PERMANECE "DDM" (é honesto).

RELABELAR (motor atual → RIM):
- ~606 (intro, fluxo passo 3): "valuation por Desconto de Dividendos (DDM)" →
  "valuation por Renda Residual (RIM)". (Passo 3 descreve o motor atual.)
- ~900 (spinner): "Calculando valuation (DDM + múltiplos)…" →
  "Calculando valuation (RIM + múltiplos)…".
- ~998 (caption do selo): "Selo = qualidade do dividendo (BSD) × preço (DDM)." →
  "...× preço (RIM)." (o veredito de preço vem do RIM.)
- ~1105 (aviso preço indisponível): "valor intrínseco (DDM, dados CVM)" →
  "valor intrínseco (RIM, dados CVM)".
- ~1114/1118 (comentário + header): "Lentes de referência (Fase 19) ... além do DDM." e
  `#### Lentes de referência (além do DDM)` → "(além do RIM)" (a análise principal agora é o RIM).
- ~1120 (caption): "o valor intrínseco (DDM) acima segue sendo a análise principal" →
  "o valor intrínseco (RIM) acima segue sendo a análise principal".
- ~1219 (comentário): "banda do valor intrínseco (DDM)" → "(RIM)".
- ~1280 (st.info gráfico): "valor intrínseco (DDM, dados CVM)" → "(RIM, dados CVM)".
- ~1297 (comentário) "alinha com a banda DDM" e ~1303 (comentário) "só se o DDM calculou" →
  trocar "DDM" por "RIM".
- ~1307 (annotation_text VISÍVEL do gráfico): "Valor intrínseco (DDM)" → "Valor intrínseco (RIM)".
- ~1269 (comentário) "banda DDM" → "banda RIM".
- ~243 (docstring interna) "rf do CAPM/DDM" → "rf do CAPM/RIM".

REESCREVER (copy stale, sem afirmar qual número é suprimido) — bloco `ddm_inaplicavel`
(~1092–1100), MANTÉM o bloco (campo existe), remove a cláusula que nomeia a manchete:
- Reescrever para: descreve que a LENTE por Desconto de Dividendos (DDM) ficou negativa/zero
  para este perfil (payout baixo / alto capex ou lucro negativo) e por isso não é preço-alvo —
  a lente DDM é estruturalmente inaplicável aqui. NÃO mencionar "o Intrínseco (DDM) não é
  exibido" (cláusula stale — a manchete agora é RIM, independente da lente DDM).

CASO-A-CASO (dropar o nome do motor por ambiguidade payout DDM vs RIM):
- ~1423 e ~1426 (sub-tab Múltiplos): "o sustentável usado no valuation (DDM)" e "usado no DDM"
  → "o sustentável usado no valuation" / "usado no valuation" (genérico; não afirma DDM nem RIM).

NÃO RELABELAR (DDM honesto — a lente/fórmula existe de fato ou é config):
- ~1413/~1448/~1450: sub-tab "Valuation (DDM)" e header "Valor intrínseco por Desconto de
  Dividendos" — renderiza `a.ddm_constante`/`a.ddm_h` DE VERDADE. Relabelar mentiria. FICA DDM.
- ~1466: `CFG["ddm"]["sensibilidade"]` e ~1474 "DDM não calculado..." (mensagem do sub-tab DDM). FICAM.

Confirme por grep que as menções restantes de "DDM" em app.py são só: sub-tab Valuation (DDM),
guarda ddm_inaplicavel (reescrita), e a chave CFG["ddm"]. Se sobrar alguma que nomeia o motor
atual, aplique a regra acima.
  </action>
  <verify>
    <automated>python3 -c "import ast; ast.parse(open('app.py').read())"</automated>
    Gates:
    - `grep -c 'Intrínseco (DDM)' app.py` retorna 0 (a manchete stale já saiu na T1; a nota
      ddm_inaplicavel foi reescrita).
    - `grep -n 'DDM' app.py` mostra APENAS: sub-tab "Valuation (DDM)"/"Desconto de Dividendos",
      guarda ddm_inaplicavel reescrita, e `CFG["ddm"]`. Nenhuma nomeando o motor/manchete atual.
    - Fronteira intocada: `git diff --name-only` lista SOMENTE `app.py`;
      `git diff config.yaml calibracao.lock.yaml` VAZIO.
  </automated>
  <done>
ast.parse OK; nenhuma copy visível chama o motor atual de "DDM"; sub-tab DDM e guarda
ddm_inaplicavel permanecem (honestos); só app.py no diff; config/lock intocados.
  </done>
</task>

</tasks>

<verification>
Rede de segurança final (nenhum teste toca app.py, mas confirma que nada colateral quebrou):
- `python3 -c "import ast; ast.parse(open('app.py').read())"` — sintaxe.
- `pytest -q` — DEVE ficar verde (0 failed). Se ficar vermelho, o que mudou foi o sistema
  (regra CLAUDE.md): investigar, NUNCA afrouxar/xfail/skip para "ficar verde".
- `git diff config.yaml calibracao.lock.yaml` — VAZIO (fronteira inviolável).
- `git diff --name-only` — só `app.py`.
</verification>

<success_criteria>
- Manchete da aba Analisar: "Intrínseco (RIM)" (bug do rótulo corrigido).
- Zero código morto do ensemble (gates de campos removidos) em app.py.
- Copy visível reflete RIM como motor único; "DDM" só onde nomeia a lente/fórmula que existe.
- Nenhum número, knob, engine ou config alterado; pytest verde; diff só em app.py.
</success_criteria>

<output>
After completion, create `.planning/quick/260720-kuc-relabel-ddm-para-rim-na-aba-analisar-do-/260720-kuc-SUMMARY.md`
</output>
