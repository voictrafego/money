---
phase: quick-260713-hoo
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [app.py]
autonomous: true
requirements: [UX-CARD-INTRINSECO, UX-DECLUTTER-BANNERS]
must_haves:
  truths:
    - "Na tela do ITUB4 (motor RIM, banda_do_motor True), o card lidera com 'Intrínseco (RIM) R$ 32,88' — não com a faixa '16,13 – 32,88'"
    - "O valor R$ 32,88 (a.intrinseco_motor) permanece intacto — nenhuma lógica de cálculo muda"
    - "Casos motor=='ddm', banda_do_motor False e arquetipo_incerto mantêm o comportamento atual exato (faixa vmin–vmax ou '—' com rótulo 'Intrínseco (DDM)')"
    - "O bloco de sinais tem no máximo 1 caixa principal (veredito) + 1 expander opcional, em vez das 3 caixas de hoje"
    - "Banner 'Classificação incerta', selo, e alertas de dado ('Verificar dados' / Payout>100%) permanecem fora do expander, intactos"
    - "python -m pytest -q continua verde (~448 passed)"
  artifacts:
    - path: "app.py"
      provides: "Camada de render Streamlit da tela Analisar — card intrínseco e bloco de banners consolidados"
      contains: "st.expander"
  key_links:
    - from: "app.py m2.metric"
      to: "a.intrinseco_motor / a.banda_do_motor / a.motor"
      via: "leitura read-only dos campos derivados na engine"
      pattern: "intrinseco_motor"
    - from: "app.py st.expander"
      to: "a.san01_reetiquetado / a.divergencia_ativa"
      via: "condição de exibição do expander consolidado"
      pattern: "st\\.expander"
---

<objective>
Limpar a tela de análise de ação (app.py) — mudança 100% de APRESENTAÇÃO. Dois ajustes:
1. O card INTRÍNSECO (`m2.metric`) deve liderar com o valor do motor primário (ex.: ITUB4 → "Intrínseco (RIM) R$ 32,88") quando o motor não é o DDM e a banda vem de fato do motor, rebaixando a faixa/contraponto DDM para um caption discreto.
2. Consolidar os 3 banners repetitivos ("é RIM, o DDM é conservador") em 1 caixa principal (veredito) + 1 `st.expander` opcional.

Purpose: O número R$ 32,88 está correto; o problema é de leitura — o usuário lê "16,13" (piso do contraponto DDM) como o intrínseco, e três caixas empilhadas repetem a mesma explicação. Fiel ao Core Value do CLAUDE.md (consistência da apresentação dos números entre views).
Output: app.py editado, suíte verde. Sem deploy.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@./CLAUDE.md

<constraints>
RESTRIÇÕES DURAS (do CLAUDE.md — não negociáveis):
- NÃO alterar `src/analista/report/report.py`, a engine, nem qualquer lógica de cálculo. SÓ a camada de render de app.py (e `presentation.py` apenas se precisar de um helper de formatação PURO — provavelmente não).
- NÃO mudar strings que os testes em `tests/` assertam. As asserções `"Bandeira de divergência"` / `"conservador demais"` vivem em report.py (markdown `md` / `a.veredito`), NÃO em app.py — não confundir. Nenhum teste importa a camada de render de app.py.
- Gate do projeto: `python -m pytest -q` VERDE (~448 passed). A suíte DEVE continuar verde.
- Escopo mínimo: nenhuma feature nova; não redesenhar o resto da tela.
- NÃO fazer deploy. Só implementar + commitar; preview local é passo manual posterior.
</constraints>

<interfaces>
<!-- Campos read-only já derivados na engine (report.analisar_acao → `a`). NÃO recalcular. -->
- a.motor            : str | None   — motor primário do arquétipo ("ddm", "rim", "normalizado", "dcf", "nav", "seguradora"...)
- a.motor_rotulo     : str | None   — rótulo humano do motor (ex.: "RIM")
- a.banda_do_motor   : bool         — True quando a faixa vmin/vmax vem DE FATO do motor (não 100% DDM degradado)
- a.intrinseco_motor : float | None — valor do motor primário (ITUB4 ≈ 32.88)
- a.contraponto_valor: float | None — valor do DDM como contraponto conservador
- a.vmin, a.vmax     : float | None — faixa do ensemble (min/max entre motor e mid do DDM)
- a.arquetipo_incerto: bool         — caso-fronteira (VER-02); intervalo já cai em "—"
- a.san01_reetiquetado: bool        — guarda-corpo SAN-01 disparou
- a.divergencia_ativa: bool         — lentes divergem > 2× (ENS-01)
- a.divergencia_razao / a.divergencia_hipotese — detalhes da divergência

Helpers de render existentes em app.py (usar, não recriar): fmt_rs(x), fmt_num(x,n), fmt_pct(x), esc_md(s), h(chave).
Estado atual do trecho: veredito colorido (~884-892) → SAN-01 st.info (~903-908) → arquetipo_incerto st.warning (~913-940) → divergência st.warning (~945-955) → selo (~962-974) → m2.metric intrínseco (~977-998) → legenda "A faixa combina..." (~1005-1018) → nota ddm_inaplicavel (~1020-1028).
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Card INTRÍNSECO lidera com o valor do motor primário</name>
  <files>app.py</files>
  <action>
No bloco do `m2.metric` (~linhas 976-998) e na legenda logo abaixo (~linhas 1005-1018):

1. Definir uma condição `_usa_motor` = `a.motor` existe e != "ddm" E `getattr(a, "banda_do_motor", False)` True E NÃO `getattr(a, "arquetipo_incerto", False)` E `a.intrinseco_motor is not None`.

2. Quando `_usa_motor` for True: a MANCHETE do `m2.metric` passa a ser `esc_md(fmt_rs(a.intrinseco_motor))` (ex.: "R$ 32,88") e o rótulo continua `f"Intrínseco ({a.motor_rotulo or _motor})"` (ex.: "Intrínseco (RIM)"). NÃO exibir a faixa vmin–vmax na manchete.

3. Quando `_usa_motor` for False: manter EXATAMENTE o comportamento atual — manchete = `intervalo` (faixa "vmin – vmax", ou "—" no caso `arquetipo_incerto` já tratado nas linhas 982-983) e rótulo pela lógica atual `_label_intr` ("Intrínseco (DDM)" quando `_motor == "ddm"` ou não `banda_do_motor`, senão "Intrínseco ({rotulo})"). Preservar o `help=h("valor_intrinseco")`.

4. Rebaixar o contraponto DDM + a faixa para um `st.caption` DISCRETO logo abaixo do bloco de métricas, exibido SÓ quando `_usa_motor` e `a.contraponto_valor is not None` — algo como: "Faixa com o DDM como contraponto conservador: {fmt_rs(a.vmin)} – {fmt_rs(a.vmax)} · DDM {fmt_rs(a.contraponto_valor)}." (usar esc_md nos valores). Isto SUBSTITUI a legenda atual "A faixa combina o motor do arquétipo..." (~1005-1018), que fica redundante com a manchete limpa — REMOVER essa legenda antiga para não duplicar.

5. NÃO tocar na nota `ddm_inaplicavel` (~1020-1028) nem nos demais metrics (m1/m3/m4/m5). NÃO fazer fenced code / lógica de cálculo — só leitura dos campos já derivados.

Objetivo verificável: na tela do ITUB4 (motor RIM, banda_do_motor True), o card mostra "Intrínseco (RIM)" com manchete "R$ 32,88", e a faixa/DDM aparece só no caption discreto abaixo.
  </action>
  <verify>
    <automated>cd "/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos" && python -c "import ast; ast.parse(open('app.py').read()); print('syntax ok')" && grep -n "intrinseco_motor" app.py | head</automated>
  </verify>
  <done>m2.metric lidera com fmt_rs(a.intrinseco_motor) quando _usa_motor True; caso ddm/banda_do_motor False/arquetipo_incerto inalterado; legenda antiga "A faixa combina..." substituída por caption discreto; app.py compila (ast.parse ok).</done>
</task>

<task type="auto">
  <name>Task 2: Consolidar os 3 banners em veredito + 1 expander opcional</name>
  <files>app.py</files>
  <action>
No bloco de sinais do veredito (~linhas 884-955):

1. MANTER o veredito colorido `st.success/error/warning` (~886-892) como a ÚNICA caixa principal — não mexer.

2. MOVER o conteúdo do banner SAN-01 `st.info` (~903-908) e da Bandeira de divergência `st.warning` (~945-955) para DENTRO de UM único `st.expander`, exibido só quando `getattr(a, "san01_reetiquetado", False)` OU `getattr(a, "divergencia_ativa", False)`. Título dinâmico e honesto: `f"Por que {a.motor_rotulo or 'o motor do arquétipo'} e não DDM?"` (evita cravar "RIM" para arquétipos não-banco). Dentro do expander, renderizar condicionalmente: se `san01_reetiquetado`, o texto do SAN-01; se `divergencia_ativa`, o texto da divergência (com `divergencia_razao`, `intrinseco_motor` × `contraponto_valor` e `divergencia_hipotese`), preservando o conteúdo/valores exatos que estavam nos dois banners — só muda o container (de st.info/st.warning para dentro do expander).

3. MANTER INTACTOS e FORA do expander (não mover, não reordenar):
   - Banner "Classificação incerta" (`arquetipo_incerto`, ~913-940)
   - Selo de sustentabilidade (~962-968)
   - Alerta "Verificar dados" (~970-974) e qualquer alerta de Payout>100% — são bandeira de DADO real, não redundância.

4. Ordem final do bloco: veredito colorido → expander opcional (SAN-01 + divergência) → banner Classificação incerta → selo → alertas de dado → (métricas da Task 1).

Objetivo verificável: no máximo 1 caixa de banner principal (veredito) + 1 expander opcional, em vez das 3 caixas empilhadas de hoje.
  </action>
  <verify>
    <automated>cd "/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos" && python -c "import ast; ast.parse(open('app.py').read()); print('syntax ok')" && grep -n "st.expander" app.py</automated>
  </verify>
  <done>SAN-01 + divergência vivem dentro de um único st.expander condicional; veredito é a única caixa principal; "Classificação incerta", selo e alertas de dado permanecem fora e intactos; app.py compila.</done>
</task>

<task type="auto">
  <name>Task 3: Gate de testes verde</name>
  <files>app.py</files>
  <action>
Rodar a suíte completa e confirmar que nenhuma asserção quebrou. As mudanças são 100% de render de app.py (nenhum teste importa a camada de render), então a suíte deve continuar verde sem edições em tests/. Se algo falhar, investigar se um efeito colateral não-intencional tocou report/engine e reverter — NÃO alterar tests/ para "passar".
  </action>
  <verify>
    <automated>cd "/Users/giovanelazari/projects/Analista de Investimentos/analista_dividendos" && python -m pytest -q 2>&1 | tail -15</automated>
  </verify>
  <done>python -m pytest -q verde (~448 passed); firewall selo↛report intacto; nenhuma edição em tests/ nem em report.py/engine.</done>
</task>

</tasks>

<verification>
- app.py compila (ast.parse) após as duas edições.
- `python -m pytest -q` verde (~448 passed) — Core Value / firewall preservados.
- Inspeção manual do diff: apenas o intervalo ~884-1018 de app.py mudou; report.py e engine intocados.
</verification>

<success_criteria>
- Card ITUB4 lidera com "Intrínseco (RIM) R$ 32,88" (não "16,13 – 32,88"); faixa/DDM só em caption discreto.
- Bloco de sinais tem ≤ 1 caixa principal (veredito) + 1 expander opcional; SAN-01 e divergência consolidados dentro do expander.
- "Classificação incerta", selo e alertas de dado intactos e fora do expander.
- Suíte de testes verde. Sem deploy.
</success_criteria>

<output>
After completion, create `.planning/quick/260713-hoo-limpar-tela-de-analise-card-intrinseco-m/260713-hoo-SUMMARY.md`
</output>
