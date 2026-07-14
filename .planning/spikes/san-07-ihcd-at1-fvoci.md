# Spike SAN-07 — IHCD/AT1 no PL dos bancos? Dirty surplus FVOCI material?

**Tipo:** contábil (D-15) · **Cesta:** ITUB4, BBAS3, BBDC4, BRSR6 · **Ano-base:** 2025
**Fonte:** cache CVM 2015–2025 (`data/cvm/`), 100% offline · **Medido em:** 2026-07-14
**Re-emissão:** `PYTHONPATH=src .venv/bin/python scripts/spike_san07_bancos.py`

---

## Veredito

> **As duas respostas são NÃO. O terceiro bug de dados NÃO existe. Nenhum knob se move.**

1. **IHCD/AT1 entram no PL dos bancos?** **NÃO.** Não há nenhuma subconta de instrumento
   perpétuo/híbrido dentro do bloco do PL de nenhum dos 4 bancos na DFP padronizada da CVM.
2. **O dirty surplus por IFRS 9 FVOCI é material?** **NÃO.** O OCI anual (DRA, conta `4.02`) fica
   entre **0,03% e 0,59% do PL** nos 4 bancos. Contra o clean surplus, é ruído.

A Fase 9 não herda dúvida — herda um "não" fundamentado. **Nenhum `B0` é corrigido, nenhum knob é
movido, o `resultado abrangente` NÃO substitui o LL no RIM** (D-15; Armadilha 3 do ROADMAP).

---

## Correção da premissa — `2.03` não é o PL de banco nenhum

O texto do requisito SAN-07 afirma que os IHCD/AT1 entrariam "no PL dos bancos (`2.03`)". **A conta
`2.03` não é o Patrimônio Líquido de nenhum banco.** Medido no BPP consolidado 2025:

| banco | o que `2.03` **realmente** é | onde o PL de fato está |
|-------|------------------------------|------------------------|
| ITUB4 | `2.03` = **"Passivos Financeiros ao Custo Amortizado"** (R$ 2.350,90 bi) | **`2.08`** — "Patrimônio Líquido Consolidado" (R$ 215,08 bi) |
| BBAS3 | `2.03` = **"Provisões"** (R$ 38,69 bi) | **`2.07`** (R$ 193,57 bi) |
| BBDC4 | `2.03` = **"Provisões"** (R$ 443,36 bi) | **`2.07`** (R$ 178,95 bi) |
| BRSR6 | `2.03` = **"Provisões"** (R$ 2,52 bi) | **`2.07`** (R$ 11,47 bi) |

Note que o código do PL **varia entre os próprios bancos** (`2.08` no ITUB4, `2.07` nos outros três).
O parser (`src/analista/ingest/cvm.py:264-268`) só sobrevive a isso porque casa o PL pelo **nome**
("Patrimônio Líquido Consolidado", `nome_primeiro=True`), não pelo código. **O parser está certo; o
texto do requisito é que estava errado.**

---

## Pergunta 1 — IHCD/AT1 dentro do PL?

Composição medida do PL do **ITUB4** (`2.08.*`):

```
  2.08.01   Capital Social Realizado                        136,91 bi
  2.08.02   Reservas de Capital                               2,86 bi
  2.08.03   Reservas de Reavaliação                           0,00 bi
  2.08.04   Reservas de Lucros                               67,71 bi
  2.08.05   Lucros/Prejuízos Acumulados                       0,00 bi
  2.08.06   Ajustes de Avaliação Patrimonial                  0,00 bi   <-- ver anomalia
  2.08.07   Ajustes Acumulados de Conversão                   0,00 bi
  2.08.08   Outros Resultados Abrangentes                    -2,98 bi
  2.08.09   Participação dos Acionistas Não Controladores    10,57 bi
```

Nos 4 bancos, o bloco do PL contém apenas capital social, reservas, lucros acumulados, OCI e
minoritários. **NÃO existe nenhuma linha de IHCD / AT1 / "Instrumentos Elegíveis ao Capital" /
"dívida perpétua" dentro do PL de nenhum deles.** No **BRSR6**, o instrumento subordinado aparece
do lado do **passivo**, não do PL: `2.01.01 "Dívida Subordinada" = R$ 1,69 bi` e
`2.02.04.05 "Letras Financeiras Subordinadas" = R$ 2,41 bi`.

**Ressalva honesta (obrigatória):** nas demonstrações IFRS *próprias* do Itaú, os perpétuos AT1
**são** classificados em equity. O que a medição prova é que **a DFP padronizada da CVM não os
expõe assim** — e é a DFP que este pipeline lê. Para o efeito prático do projeto, é o que importa.

> **Consequência para a Fase 9: o `B0` que o RIM consome NÃO está inflado por AT1.** A hipótese do
> "terceiro bug de dados" não se confirma por esse caminho.

---

## Pergunta 2 — Dirty surplus FVOCI é material?

O OCI **não** está no BPP — está na **DRA** (`dfp_cia_aberta_DRA_con_2025.csv`, dentro do ZIP que o
projeto já baixa; **o parser nunca abriu esse arquivo**). Medido:

| banco | `4.01` LL | `4.02` OCI (Outros Result. Abrangentes) | PL | **OCI / PL** |
|-------|-----------|------------------------------------------|----|--------------|
| ITUB4 | 45,85 bi  | **−0,071 bi** | 215,08 bi | **−0,03%** |
| BBAS3 | 16,78 bi  | **+0,071 bi** | 193,57 bi | **+0,04%** |
| BBDC4 | 23,92 bi  | **+1,055 bi** | 178,95 bi | **+0,59%** |
| BRSR6 |  1,71 bi  | **−0,024 bi** |  11,47 bi | **−0,21%** |

As pernas individuais do OCI chegam a ser grandes (o BBAS3 tem +4,713 bi de ganhos não realizados
brutos em FVOCI), mas **se cancelam no líquido** — efeito tributário e conversão cambial de
investimentos no exterior. O maior `|OCI/PL|` da cesta é **0,59% do PL/ano** (BBDC4).

> **Consequência: nenhum knob se move.** Contra o clean surplus (`ΔB ≈ LL − DIV`), 0,6%/ano é ruído.

---

## Anomalia declarada (honestidade > completude)

A conta de **estoque** `Ajustes de Avaliação Patrimonial` (`2.08.06` no ITUB4, `2.07.01.06` nos
demais) lê **0,00 nos quatro bancos**, enquanto a DRA mostra um **fluxo** de OCI não-zero. Um estoque
zerado com fluxo não-zero é **inconsistente**. Duas leituras possíveis:

1. os bancos não preenchem essa linha padronizada da CVM e alocam o OCI acumulado em outra conta
   (ITUB4/BBDC4 carregam o acumulado em `2.08.08` / `2.07.01.08` "Outros Resultados Abrangentes",
   que é não-zero — −2,98 bi no ITUB4, +0,80 bi no BBDC4);
2. o valor existe mas é pequeno demais para a precisão do print.

**Em qualquer dos casos a conclusão de materialidade não muda** — o fluxo da DRA já limita o efeito a
< 0,6% do PL/ano. Declarar, não esconder.

---

## Como reproduzir

```
PYTHONPATH=src .venv/bin/python scripts/spike_san07_bancos.py
```

Offline (só o cache CVM), sai 0, imprime os 4 bancos, nada escreve em disco, nenhum knob é lido.

## O que a Fase 9 consome

Um "não" fundamentado. **Sem knob movido, sem `B0` corrigido, sem `resultado abrangente`
substituindo o LL no RIM.** A suspeita aberta do CONTEXT/ROADMAP (clean surplus violado em bancos
por FVOCI → `B0` deprimido → RIM subvaloriza banco de qualidade) está **refutada por medição**: o
dirty surplus é imaterial e não há AT1 dentro do PL da DFP.
