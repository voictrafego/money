# Phase 6: Integração na engine + composite + alerta + CLI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-26
**Phase:** 6-integra-o-na-engine-composite-alerta-cli
**Areas discussed:** Lógica do composite, Matriz fundamento×técnico, Alerta de reverificação, Base temporal diário/semanal

---

## Lógica do composite (TIMING-01 / TEST-06)

### Estado central do composite
| Option | Description | Selected |
|--------|-------------|----------|
| MM200 dá direção, ADX confirma força | Acima da MM200 = viés de alta, só vira "tendência de alta" se ADX confirmar; árvore explícita travável | ✓ |
| Voto ponderado das 4 famílias | Soma ponderada; mais contínuo, mais difícil de explicar/travar | |
| ADX primeiro (gate), depois direção | ADX fraco → "sem tendência" ignorando MM200 | |

**User's choice:** MM200 dá direção, ADX confirma força.

### Caso-limite (acima MM200 + ADX < 20)
| Option | Description | Selected |
|--------|-------------|----------|
| "Sem tendência" (lateral) | ADX fraco vence; sem força confirmada ≠ timing de entrada. Conservador | ✓ |
| "Alta fraca / em formação" | Quarto matiz entre alta e sem tendência | |

**User's choice:** "Sem tendência" (lateral) — caso-limite canônico do TEST-06.

### Papel do momentum (RSI/MACD)
| Option | Description | Selected |
|--------|-------------|----------|
| Matiz fino dentro do estado | Tendência define o estado; RSI/MACD refinam a frase, não o estado | ✓ |
| Entra no voto do estado | Momentum com peso igual às outras famílias | |
| Fica fora do composite | Só na listagem detalhada | |

**User's choice:** Matiz fino dentro do estado.

---

## Matriz fundamento×técnico (TIMING-02)

### Geração da mensagem
| Option | Description | Selected |
|--------|-------------|----------|
| Frase curada por célula | Frase consultiva pré-escrita por combinação; travável por golden | ✓ |
| Template composicional | "Fundamento: X. Timing: Y." montado das partes | |
| Fundamento primeiro + nota técnica | Lidera com DDM, técnico subordinado | |

**User's choice:** Frase curada por célula (com fundamento sempre primeiro).

### Célula barato + atenção (queda)
| Option | Description | Selected |
|--------|-------------|----------|
| Atrativa, mas reverifique antes | Liga ao alerta de reverificação (TIMING-03) | ✓ |
| Oportunidade, fundamento manda | Técnico é ruído de curto prazo | |

**User's choice:** Atrativa, mas reverifique antes.

### Célula caro + alta
| Option | Description | Selected |
|--------|-------------|----------|
| Em alta, mas o método não paga caro | Fundamento veta a euforia técnica | ✓ |
| Momento do mercado, com ressalva | Tom mais neutro/observador | |

**User's choice:** Em alta, mas o método não paga caro.

---

## Alerta de reverificação (TIMING-03)

### Gatilhos
| Option | Description | Selected |
|--------|-------------|----------|
| Qualquer um dos três (OR) | Perda MM200 / death cross / perda mínima Donchian | ✓ |
| Só perda da MM200 | Menos ruído, perde sinais antecipados | |
| Exigir confirmação (2 de 3) | Menos falsos positivos, alerta mais tarde | |

**User's choice:** Qualquer um dos três (OR).

### Condição
| Option | Description | Selected |
|--------|-------------|----------|
| Sempre que rompe | Independe do veredito; simples e travável | ✓ |
| Só se era atrativa/justa | Condicionado ao veredito barato/no intervalo | |

**User's choice:** Sempre que rompe.

### Formato (múltiplos gatilhos)
| Option | Description | Selected |
|--------|-------------|----------|
| Alerta único consolidado | Uma mensagem listando os gatilhos acionados | ✓ |
| Um alerta por gatilho | Granular, mas pode poluir | |

**User's choice:** Alerta único consolidado.

---

## Base temporal diário/semanal (TIMING-04)

### Cálculo do "semanal"
| Option | Description | Selected |
|--------|-------------|----------|
| Resample OHLC → indicadores semanais | Reamostra para candles semanais e recalcula; menos ruído | ✓ |
| Indicadores diários, checa só na sexta | Mesma matemática, só muda a frequência de avaliação | |

**User's choice:** Resample OHLC → indicadores semanais.

### Escopo
| Option | Description | Selected |
|--------|-------------|----------|
| Resumo de timing + alerta | Todo o read técnico usa a base; só o gráfico fica diário | ✓ |
| Só o alerta de reverificação | Composite continua diário | |

**User's choice:** Resumo de timing + alerta.

### Onde mora a escolha
| Option | Description | Selected |
|--------|-------------|----------|
| Em cfg, ponto único CLI/UI | Default "semanal"; UI Phase 7 sobrescreve via session_state | ✓ |
| Argumento de analisar_acao | Mais explícito na assinatura, foge do padrão | |

**User's choice:** Em cfg, ponto único CLI/UI (default semanal).

---

## Claude's Discretion

- Nomes exatos dos campos novos de `AnaliseAcao` e dataclasses do composite.
- Limiares de ADX no composite (reusar `indicators._forca`).
- Texto das células não-conflitantes da matriz.
- Chaves/defaults de `cfg` para base temporal (ex.: `base_temporal`, regra de resample `W-FRI`).
- Formato exato da seção CLI e tratamento de histórico curto/`ohlc=None`.

## Deferred Ideas

None — discussão permaneceu no escopo da fase. (Overlays/subpainéis/toggles → Phase 7; MOM-03 e outros indicadores já deferidos no marco.)
