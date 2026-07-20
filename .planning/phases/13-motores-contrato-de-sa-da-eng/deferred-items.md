# Deferred Items — Phase 13

## 13-03 (RIM único + morte do ensemble)

- **`app.py` (Streamlit UI) tem blocos MORTOS do ensemble/divergência/fronteiriço.** O Plano 03
  removeu os campos de ensemble de `AnaliseAcao` (`banda_do_motor`, `divergencia_*`,
  `arquetipo_incerto`, `candidatos_intrinsecos`, `veredito_range`, `contraponto_valor`,
  `san01_reetiquetado`). `app.py` (raiz, ~L928-1055) ainda referencia esses campos, mas SEMPRE via
  `getattr(a, "campo", False)` (default) ou acesso direto protegido por short-circuit `and` — então
  os blocos de UI simplesmente **não renderizam** (as flags são sempre False) e **não há crash**
  (nenhum teste importa `app.py`; imports e parse OK). É dead-code seguro, não um bug de runtime.
  **Fora do escopo do Plano 03** (Task 2 = `report.py` apenas; `app.py` não está na lista de arquivos
  de nenhuma task). Limpar a UI do ensemble/divergência/fronteiriço é trabalho do Plano 04 (que
  formaliza a região da MS primária) ou de um plano de UI dedicado.
