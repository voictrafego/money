# Phase 5: Motor de indicadores puro — Discussion Log

**Date:** 2026-06-26
**Mode:** discuss (default)

> Registro humano da discussão (auditoria/retrospectiva). Não é consumido por agentes downstream — o canônico é `05-CONTEXT.md`.

## Áreas selecionadas para discussão

O usuário selecionou todas as 4 zonas cinzentas apresentadas:
1. Formato do `SinaisTecnicos`
2. Definição do squeeze (CHAN-03)
3. EMA toggle + quais sinais seguem (TREND-04)
4. Inclinação da regressão (FORCE-02)

## Decisões

### Área 1 — Formato do `SinaisTecnicos`
- **Opções:** (a) Nested por família + sinais discretos [recomendado]; (b) Flat; (c) Só valores crus.
- **Escolha:** (a) Nested por família. Séries + sinais discretos em estados curtos/neutros; frases consultivas PT ficam para a Phase 6 (composite). → **D-01**

### Área 2 — Definição do Bollinger squeeze (CHAN-03)
- **Opções:** (a) Percentil da própria largura [recomendado]; (b) Mínimo de N períodos; (c) Limiar absoluto.
- **Escolha:** (a) Largura BB ≤ percentil 20 da própria largura em janela ~126 pregões; auto-normaliza por ticker. → **D-02**

### Área 3 — EMA toggle + base dos sinais (TREND-04)
- **Opções:** (a) Séries SMA+EMA, sinais sempre SMA [recomendado]; (b) Sinais seguem o toggle; (c) Só base selecionada por cfg.
- **Escolha:** (a) Computa séries SMA E EMA sempre; sinais discretos (cross, posição MM200) sempre sobre SMA; EMA = vista alternativa visual. Casa com UI-03. → **D-03**

### Área 4 — Inclinação da regressão (FORCE-02)
- **Opções:** (a) 90 pregões, slope %/ano + R² [recomendado]; (b) 120 pregões; (c) 60 pregões, ângulo em graus.
- **Escolha:** (a) Janela 90 pregões da série split-adjusted; força = slope anualizado normalizado (%/ano) + R². → **D-04**

## Scope creep / deferidos
- MOM-03 (divergências) e indicadores extras (Keltner/Ichimoku/VWAP) mantidos fora do escopo → seção Deferred do CONTEXT.

## Claude's Discretion
- Nomes exatos de campos/subdataclasses, tipagem dos sinais (str literal vs Enum), estrutura interna das funções puras, nomes/defaults das chaves de `cfg`, tratamento de histórico curto por indicador.
