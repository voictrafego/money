# Phase 1: Classificador de Arquétipo + Roteamento - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-11
**Phase:** 1-Classificador de Arquétipo + Roteamento
**Areas discussed:** Calibração do fallback honesto, Confiar no setor vs. sempre refinar, Taxonomia dos arquétipos, O que a Fase 1 mostra sem os motores novos

---

## Calibração do fallback honesto (ARQ-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Só em conflito real de sinais | Crava quando setor + quantitativo concordam; fronteiriço quando discordam ou métricas se contradizem. Mira ~85/15. | ✓ |
| Conservador (mais bandeiras) | Qualquer ambiguidade marca fronteiriço (~30–40%). Erra menos, duvida mais. | |
| Agressivo (quase sempre crava) | Só fronteiriço se nenhum arquétipo pontuar. Poucas bandeiras, mais risco. | |

**User's choice:** Só em conflito real de sinais
**Notes:** Alinha com a meta do brief (~85% cravados / ~15% dúvida honesta).

---

## Confiar no setor vs. sempre refinar (ARQ-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Híbrido: setor forte roteia, resto refina | Banco (CVM)/seguradora/regulada (eh_concessionaria) hard-route; resto vai ao refino quantitativo. | ✓ |
| Sempre refinar quantitativamente | Setor é só sinal de entrada; quantitativo sempre decide. Robusto a rótulo errado, pode errar banco atípico. | |
| Setor primeiro sempre | Confia no rótulo CVM como corte primário. Simples, herda erros de rótulo. | |

**User's choice:** Híbrido: setor forte roteia, resto refina
**Notes:** `eh_concessionaria` e detecção de banco na CVM já são confiáveis; rótulo genérico da CVM não (VULC3 → 'Têxtil').

---

## Taxonomia dos arquétipos (chaves do registry — ENG-01)

| Option | Description | Selected |
|--------|-------------|----------|
| 5 chaves = 1:1 com os motores | financeira→RIM, regulada→DDM, cíclica→normalizado, crescimento→DCF, holding→SOTP. | ✓ |
| 6 chaves: separar banco de seguradora | Classificação separada (mesmo motor RIM) para transparência; mais lógica. | |
| 6 chaves: separar compounder de crescimento | 'Crescimento capital-light' (DCF) vs 'compounder alta retenção' (RIM/DCF). Mais nuance, mais fronteira. | |

**User's choice:** 5 chaves = 1:1 com os motores
**Notes:** Mapa arquétipo↔motor limpo. Separações recusadas ficam em Deferred para eventual revisão na Fase 2.

---

## O que a Fase 1 mostra sem os motores novos

| Option | Description | Selected |
|--------|-------------|----------|
| Suspende o veredito primário + rebaixa DDM | Não roda DDM como motor certo; exibe 'arquétipo→motor (Fase 2)', mostra Graham/Bazin, não estampa 'evitar'. Mata metade do bug do ITUB4 já na Fase 1. TAEE11 (DDM existe) fica idêntica. | ✓ |
| DDM provisório com aviso forte | Roda DDM com rótulo 'motor provisório — o correto (RIM) chega na Fase 2'. Mantém número com ressalva. | |
| Só registra o roteamento (output inalterado) | Classifica e loga o motor-alvo; valuation segue DDM atual até a Fase 2. Menor risco, mas ITUB4 continua 'evitar'. | |

**User's choice:** Suspende o veredito primário + rebaixa DDM
**Notes:** Zero aberração silenciosa desde a Fase 1; consistente com o "veredito honesto" do milestone.

---

## Claude's Discretion

- Nomes exatos das chaves do registry e assinatura da função classificadora.
- Thresholds numéricos do refino quantitativo (ROE "alto e estável", oscilação que caracteriza cíclica, retenção de compounder).
- Forma exata da exposição em `AnaliseAcao` (arquétipo, motor, flag fronteiriço, candidatos) e a renderização mínima no report/CLI.
- Estrutura do registry (dict módulo-nível / dataclass).

## Deferred Ideas

- Thresholds finos + validação empírica (backtesting é BACKTEST-01, fora de escopo do milestone).
- Exposição rica do "porquê" da classificação na UI → Fase 3.
- Separar banco↔seguradora e compounder↔crescimento como chaves distintas → recusado agora (5 chaves), revisitar se a Fase 2 mostrar que RIM não serve igual para seguradora.
