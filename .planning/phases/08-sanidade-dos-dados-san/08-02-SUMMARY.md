---
phase: 08-sanidade-dos-dados-san
plan: 02
subsystem: planning
tags: [san-07, spike, contabil, bancos, rim, jcp, composicao-capital, planejamento]

# Dependency graph
requires:
  - phase: 08-sanidade-dos-dados-san
    plan: 01
    provides: "cvm.py já lê 3.11.01 + minoritários + proventos_filtro_amplo; comentário BUG-JCP corrigido"
provides:
  - "spike SAN-07 respondido por escrito: as duas perguntas são NÃO; o terceiro bug de dados não existe; nenhum knob se move"
  - "scripts/spike_san07_bancos.py re-emite offline (cache CVM) o PL real, a composição do PL (sem AT1) e a razão OCI/PL dos 4 bancos"
  - "REQUIREMENTS/ROADMAP sem o número fantasma '1.131×'; SAN-02 com limiar simétrico max(r,1/r) >= 3×"
  - "DATA-01 carrega a direção INVERTIDA do BUG-JCP (a CVM perde o JCP; o Yahoo o tem) — a Fase 9 não conserta o lado errado"
  - "DATA-03 herda o composicao_capital com as 2 armadilhas (chave por CNPJ_CIA; escala MILHARES×unidades)"
affects: [09-ingestao-correta-data, 13-motores-contrato-eng]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Spike contábil como evidência re-executável offline: doc + script que re-emite os números do cache (T-08-05)"
    - "Refutar por medição uma suspeita travada do CONTEXT sem mover knob (D-15; Armadilha 3)"

key-files:
  created:
    - "scripts/spike_san07_bancos.py"
    - ".planning/spikes/san-07-ihcd-at1-fvoci.md"
  modified:
    - ".planning/spikes/MANIFEST.md"
    - ".planning/REQUIREMENTS.md"
    - ".planning/ROADMAP.md"

key-decisions:
  - "O terceiro bug de dados NÃO existe: IHCD/AT1 não estão no PL da DFP da CVM; dirty surplus FVOCI imaterial (OCI/PL 0,03%–0,59%)"
  - "A premissa do requisito estava errada: 2.03 não é PL de banco nenhum; o PL é 2.08 (ITUB4) / 2.07 (demais), casado pelo nome"
  - "SAN-02 usa limiar simétrico max(r,1/r) >= 3× — robusto por construção; a isenção por .splits (D-12) fica mantida mas deixa de ser load-bearing"

requirements-completed: [SAN-07]

# Metrics
duration: 15min
completed: 2026-07-14
---

# Phase 8 Plan 02: SAN-07 (spike contábil) + morte dos números fantasma Summary

**Fecha o SAN-07 medindo os 4 bancos contra o cache CVM: as duas perguntas (IHCD/AT1 no PL? dirty surplus FVOCI material?) são NÃO — o terceiro bug de dados não existe e nenhum knob se move — e corrige os números errados escritos no planejamento (o fantasma '1.131×', a conta '2.03'), registrando para a Fase 9 a direção INVERTIDA do BUG-JCP e o `composicao_capital` com suas duas armadilhas.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-07-14
- **Tasks:** 2
- **Files:** 5 (2 criados + 3 modificados)

## Accomplishments

- **`scripts/spike_san07_bancos.py`** — script standalone 100% offline (`sys.path.insert` do `src`, sem `pip install -e`) que, do cache CVM 2025, imprime por banco: (1) o que `2.03` **realmente** é × onde o PL de fato está; (2) a composição do bloco do PL, provando a ausência de IHCD/AT1; (3) o dirty surplus da **DRA** (`4.01`/`4.02` — arquivo que o parser nunca abriu) e a razão OCI/PL. Sai 0; nada escreve em disco; nenhum knob é lido.
- **`.planning/spikes/san-07-ihcd-at1-fvoci.md`** — o documento do D-15 com veredito **NÃO+NÃO**, a correção da premissa (`2.03` não é PL; PL é `2.08`/`2.07` casado pelo nome), a composição medida do PL do ITUB4, a tabela OCI/PL dos 4 bancos (−0,03% / +0,04% / +0,59% / −0,21%), a ressalva honesta do AT1-em-equity nas IFRS próprias do Itaú, e a anomalia declarada do `Ajustes de Avaliação Patrimonial = 0,00`.
- **REQUIREMENTS/ROADMAP** — o número fantasma "ITUB4 2019 = 1.131×" **saiu dos dois arquivos** (é o salto real 2024→2025 = 1,1286×, mal-rotulado); SAN-02 ganhou o limiar **simétrico** `max(r,1/r) ≥ 3×`; SAN-07 marcado **[x]** apontando para o spike; a conta do PL corrigida de `2.03` para `2.08`/`2.07`.
- **Legado para a Fase 9** — DATA-01 registra a **direção invertida do BUG-JCP** (a CVM perde o JCP, 18× no BRSR6; o DPA do Yahoo o inclui, erro <5% em 4 anos — a correção é **ampliar o filtro**, não trocar de fonte); DATA-03 registra o **`composicao_capital`** como o insumo oficial de contagem de ações, com as 2 armadilhas (chave por `CNPJ_CIA`, escala inconsistente MILHARES×unidades — usá-lo cru reintroduziria a doença do ×1000).
- **Zero movimento de knob:** `config.yaml` e `calibracao.lock.yaml` **não aparecem no diff**. Suíte intocada: **430 passed, 1 skipped, 38 deselected, 2 xfailed, 0 failed**.

## Task Commits

1. **Task 1: spike SAN-07 (script + doc + MANIFEST)** — `ced68ed` (docs)
2. **Task 2: números fantasma no REQUIREMENTS/ROADMAP + SAN-07 fechado** — `9e54adb` (docs)

## Files Created/Modified

- `scripts/spike_san07_bancos.py` — evidência re-executável offline dos números do spike (T-08-05)
- `.planning/spikes/san-07-ihcd-at1-fvoci.md` — o documento do D-15
- `.planning/spikes/MANIFEST.md` — linha do spike (❌ REFUTADO)
- `.planning/REQUIREMENTS.md` — SAN-02 (limiar simétrico), SAN-07 ([x] + spike + conta correta), DATA-01 (BUG-JCP invertido), DATA-03 (composicao_capital), traceability SAN-07 → Complete
- `.planning/ROADMAP.md` — Phase 8 critérios 1 (fantasma) e 5 (spike + conta)

## Decisions Made

- **O terceiro bug de dados não existe** — a suspeita aberta do CONTEXT/ROADMAP (clean surplus violado em bancos por FVOCI → `B0` deprimido → RIM subvaloriza banco de qualidade) está **refutada por medição**. A Fase 9 herda um "não" fundamentado, não uma dúvida.
- **SAN-02 = limiar simétrico `max(r,1/r) ≥ 3×`** — o bug aparece 2 vezes (na queda e na recuperação); um check só de aumento pegaria o ano são. Um limiar calibrado para 1,13× dispararia em toda bonificação de 10% da B3. A isenção por `.splits` (D-12) fica mantida, mas deixa de ser load-bearing.
- **A conta `2.03` do requisito estava errada, não o parser** — o `cvm.py` casa o PL pelo **nome** (`nome_primeiro=True`), por isso sobrevive à variação de código entre bancos (`2.08` ITUB4 vs `2.07` demais).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] O literal do número fantasma sobrevivia à própria prosa que o explicava (e ao bloco Plans)**
- **Found during:** Task 2 (verificação do acceptance `grep -c "1.131"`)
- **Issue:** A prosa que o plano mandava escrever citava `"1.131×"` entre aspas para explicá-lo como fantasma — mas o acceptance `grep -c "1.131"` (o `.` do grep casa qualquer char, inclusive a vírgula) exige **0** ocorrências nos dois arquivos, e o próprio critério de sucesso do plano diz "os arquivos **não contêm mais** o '1.131×'". Além da minha prosa (REQ §SAN-02 e ROADMAP crit. 1), o literal também vivia na **linha do bloco `Plans:`** do ROADMAP que descreve este próprio plano (`... (1.131× e a conta 2.03) ...`).
- **Fix:** Reescrevi as três ocorrências para descrever o fantasma sem grafar os dígitos ("o salto que antes se atribuía ao ITUB4 2019", "o salto fantasma do ITUB4 2019"). O salto real informativo (**1,1286×**) permanece — não casa o padrão `1.131`. A edição na linha do bloco `Plans:` removeu **só o token fantasma**, sem tocar no checkbox/estrutura (que o orquestrador gerencia).
- **Files modified:** .planning/REQUIREMENTS.md, .planning/ROADMAP.md
- **Verification:** `grep -c "1.131"` = 0 nos dois arquivos; suíte 430 passed / 0 failed
- **Committed in:** `9e54adb` (Task 2 commit)

**2. [Descoberta registrada, não desvio] O instrumento subordinado do BRSR6 aparece em duas linhas do passivo**
- **Found during:** Task 1 (varredura do script)
- **Detalhe:** Além do `2.01.01 "Dívida Subordinada" = R$ 1,69 bi` que a pesquisa já citava, o script mediu também `2.02.04.05 "Letras Financeiras Subordinadas" = R$ 2,41 bi` — ambas no **passivo**, nenhuma no PL. Reforça a Pergunta 1 (o instrumento vive no passivo, não no equity da DFP). Registrado no output do script; o doc cita a `2.01.01` como exemplo canônico.

---

**Total deviations:** 1 auto-fix (Rule 1) + 1 descoberta registrada
**Impact on plan:** O auto-fix foi necessário para o plano cumprir seu próprio critério de aceite (grep=0) e critério de sucesso. Sem scope creep — nenhum knob movido, nenhum motor tocado.

## Issues Encountered

None além do desvio acima. O cache CVM (2015–2025) estava completo; o spike rodou 100% offline. `state.record-metric` e `state.add-decision` do SDK exigiram flags/headers específicos (a decisão foi adicionada direto na seção `### Decisions (v2.4)` do STATE.md, que não bate com o header que o handler procura).

## Known Stubs

None. O spike é evidência, não pipeline; os números são medidos do cache CVM real. Nenhum dado foi consertado (de propósito — os asserts SAN-01..05 são o teste de regressão da Fase 9).

## Next Phase Readiness

- **SAN-07 fechado.** Restam nesta fase os planos 08-03 (snapshot sujo dos 104), 08-04 (`core/sanidade.py` + os 5 checks), 08-05 (`aplicar_sanidade` + never-raise) e 08-06 (baseline dos sujos).
- A Fase 9 (DATA) tem, escrito no REQUIREMENTS, o que precisa para **não** consertar o lado errado: a direção do BUG-JCP (ampliar filtro, não trocar de fonte) e o `composicao_capital` com as armadilhas que impedem o re-×1000.
- **Nada consertado, de propósito.** O `B0` dos bancos não é ajustado; o `resultado abrangente` não substitui o LL no RIM — o spike provou que não precisa.

## Self-Check: PASSED

Arquivos criados existem (`scripts/spike_san07_bancos.py`, `.planning/spikes/san-07-ihcd-at1-fvoci.md`); commits `ced68ed` e `9e54adb` no histórico; `grep -c "1.131"` = 0 nos dois arquivos; suíte 430 passed / 0 failed.

---
*Phase: 08-sanidade-dos-dados-san*
*Completed: 2026-07-14*
