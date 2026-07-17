# Phase 12: Custo de capital / `Ke` (KE) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-17
**Phase:** 12-custo-de-capital-ke-ke
**Areas discussed:** Beta setorial (método), Onde o β setorial é computado (pureza da engine), Unificação dos dois Ke (fonte única), Validação sem clamp + Ke exibido

---

## Beta setorial — método de agregação (KE-03)

### Chave de agrupamento
| Option | Description | Selected |
|--------|-------------|----------|
| Setor CVM (`c.setor`) | Industry beta Damodaran; disponível no ingest antes do Ke; BB×Bradesco = mesmo grupo | ✓ |
| Arquetipo (banco/seguradora/regulada) | Casa o exemplo BB×Bradesco, mas computado DEPOIS do Ke — exigiria reordenar | |
| Subsetor/segmento CVM | Granularidade intermediária, se o dado existir | |

### Estatística de agregação
| Option | Description | Selected |
|--------|-------------|----------|
| Mediana | Robusta a outliers; padrão para betas setoriais ruidosos da B3 | ✓ |
| Média aritmética | Espelha a simetria com rf/pi_ciclo, mas sensível a outliers | |

### Fallback (grupo com poucos pares / sem setor)
| Option | Description | Selected |
|--------|-------------|----------|
| β individual Blume-ajustado | Pares < limiar estrutural → próprio c.beta com Blume; never-raise | ✓ |
| β = 1,0 (Blume no limite) | Assume beta de mercado; conservador mas ignora sinal individual | |
| Você decide | Deixar limiar/critério ao planner a partir do mapa de 104 tickers | |

**User's choice:** Setor CVM · Mediana · β individual Blume-ajustado.
**Notes:** Ordem Blume×agregação tratada como discricionária (linear/monotônica → equivalente); aplicar Blume uma vez sobre o β agregado.

---

## Onde o β setorial é computado — pureza da engine (KE-03/integração)

### Fonte do mapa setor→β
| Option | Description | Selected |
|--------|-------------|----------|
| Artefato pré-computado e versionado | Gerador offline a partir dos betas crus do universo ("derivado, não digitado"); carimbado em cfg | ✓ |
| Tabela estática no config.yaml | Mais simples, mas hand-maintained e viola "derivado, não digitado" | |
| Dinâmico por run no entry point | REJEITADO — anti-padrão WR-03 (analyze tem 1 ticker; só rank tem pares → drift) | |

### Invariante analyze==rank
| Option | Description | Selected |
|--------|-------------|----------|
| Sim — fonte única carimbada + teste | Espelha WR-03/_carimbar_macro; teste garante analyze e rank leem o mesmo mapa (KE-05 na prática) | ✓ |
| Confiança na construção, sem teste dedicado | Invariante por construção; deixa o teste para a blindagem geral | |

### β setorial conta no lock (3 graus)?
| Option | Description | Selected |
|--------|-------------|----------|
| Não — é DADO, como rf/pi_ciclo | β vem do mercado (medido, auto-atualiza); fora do orçamento de 3 graus; não mexe no lock | ✓ |
| Sim — tratar como knob | Estouraria o orçamento de 3 e deixaria a suíte vermelha; provavelmente errado | |

**User's choice:** Artefato pré-computado versionado · fonte única carimbada + teste · β setorial é DADO (fora do lock).

---

## Unificação dos dois Ke — fonte única (KE-01/KE-05)

### Como unificar
| Option | Description | Selected |
|--------|-------------|----------|
| Deletar ke_rim; RIM consome a.ke | ke_rim colapsa exatamente no ke_local com ERP=0,045 + clamp fora; apaga a Doença 3 | ✓ |
| Neutralizar ke_rim como passthrough | Deixa 2ª porta de Ke viva — contra "um único Ke" e o corte de knobs da Fase 13 | |

### O RIM recebe a.ke ou recomputa
| Option | Description | Selected |
|--------|-------------|----------|
| Recebe a.ke pronto (não recomputa) | Ke computado 1 vez, carimbado; todos os consumidores leem o mesmo a.ke (KE-05 literal) | ✓ |
| RIM recomputa com a fórmula única | Idêntico por construção, mas duplica o ponto de cálculo (risco de drift) | |

### Limpeza config + lock
| Option | Description | Selected |
|--------|-------------|----------|
| Remover leaves + atualizar partição do lock no mesmo diff | erp_banco/ke_piso/ke_teto saem do config e da partição do lock no mesmo commit; sem clamp com outro nome | ✓ |
| Você decide | Deixar as linhas exatas ao planner | |

**User's choice:** Deletar ke_rim (RIM consome a.ke) · RIM recebe a.ke pronto · remover leaves + partição do lock no mesmo diff.

---

## Validação sem clamp + Ke exibido (KE-04/KE-05)

### Postura de validação "nada explode"
| Option | Description | Selected |
|--------|-------------|----------|
| Regressão 104 tickers + invariante Ke_min>g_cap | Varredura do mapa REAL + teste do invariante estrutural; SEM novo guard (P/B é Fase 13) | ✓ |
| Só o invariante algébrico | Dispensa a varredura, deixa a regressão ampla para a Fase 14 | |

### Mecânica do lock + golden
| Option | Description | Selected |
|--------|-------------|----------|
| ERP→0,045 no grau + remover leaves + DELETAR golden 32,88 | Tudo no mesmo commit; golden quebra e é deletado (critério de saída, não regressão) | ✓ |
| Você decide | Deixar linhas do lock/config e ordem dos commits ao planner | |

### BLIND-02b (xfail strict)
| Option | Description | Selected |
|--------|-------------|----------|
| Destravar — remover xfail, vira teste normal que passa | Código satisfaz (Ke reage ao rf); xfail_estritos() cai 2→1; NÃO afrouxar limiar | ✓ |
| Deixar como está (vira XPASS) | Quebra a suíte de propósito para forçar atenção; mais ruidoso | |

### Ke exibido + matriz
| Option | Description | Selected |
|--------|-------------|----------|
| Exibir a.ke único; matriz Ke×g em torno dele em todo menu | report mostra a.ke como O Ke (nunca ke_rim); matriz idêntica entre analyze/rank | ✓ |
| Você decide | Deixar rótulos exatos ao planner | |

**User's choice:** Regressão 104 tickers + invariante · ERP→0,045 + deletar golden + remover leaves · destravar BLIND-02b · exibir a.ke único.

---

## Claude's Discretion

Nenhum "Você decide" foi acionado — o usuário escolheu a opção recomendada em todas as perguntas.
Detalhes deixados ao researcher/planner (dentro das decisões travadas): nome/formato do arquivo do
artefato de betas setoriais e sua chave em cfg; valor exato do limiar de pares do fallback; assinatura
do gerador offline e do helper de carimbo; ordem dos commits atômicos do diff de knob sancionado;
rótulos exatos do report/matriz; reescrita da partição de folhas do lock.

## Deferred Ideas

- Guarda-corpo sobre a razão P/B justo (`0 < P/B < 6`) — Fase 13 (ENG).
- Colapso dos 4 motores num RIM único + contrato de saída do livro + corte final de knobs `motores:` — Fase 13.
- Validação honesta / hold-out / caso do livro (ITUB4 = R$ 37,22) — Fase 14 (VAL).
- Reforma de UI do contrato de saída (tríade, matriz, MS do usuário) — Fase 13.
