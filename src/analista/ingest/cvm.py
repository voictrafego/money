"""Fundamentos oficiais via Dados Abertos da CVM — grátis.

Demonstrações Financeiras Padronizadas (DFP) em CSV, desde 2010:
  https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{ANO}.zip

Cada ZIP traz BPA, BPP, DRE e DFC (consolidado e individual). Extraímos as contas
padronizadas por código (CD_CONTA), com fallback por nome (DS_CONTA) para tolerar o
template diferente das instituições financeiras (bancos).

DATA-01 (Fase 9 / DATA — CONSERTO): `dividendos_distribuidos` passou a sair do filtro AMPLO
(`_distribuicoes_proventos_amplo`, casa "dividendo" OU "juros sobre capital"), capturando o
JCP que o filtro estreito perdia. As chaves `lucro_controlador` (`3.11.01`) e
`pl_nao_controladores` seguem como insumos que o build promove à base do controlador (DATA-02).
`proventos_filtro_amplo` continua populado como detector do SAN-03. A gêmea estreita
`_distribuicoes_proventos` fica no módulo só como referência do filtro estreito (testes).

DATA-03 (Fase 9 / DATA — CONSERTO): `contagem_oficial_do_ano` lê a contagem OFICIAL de ações
por ano do `dfp_cia_aberta_composicao_capital_{ano}.csv` (dentro do mesmo ZIP), casada por
CNPJ_CIA via `cad_cia_aberta.csv`. É a fonte que o `build` promove a `num_acoes`, aposentando a
derivação `LL/LPA` (a causa-raiz da dispersão em 41/104 tickers). A escala é decidida no build.
"""

from __future__ import annotations

import io
import os
import unicodedata
import zipfile
from functools import lru_cache
from typing import Dict, Optional

import pandas as pd
import requests

CVM_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{ano}.zip"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "cvm")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return s.strip()


def _cache_path(ano: int) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.abspath(os.path.join(CACHE_DIR, f"dfp_cia_aberta_{ano}.zip"))


def _zip_tem_ano(caminho: str, ano: int) -> bool:
    """True se o ZIP contém de fato dados do ano (e não o fallback do ano anterior).

    Quando a DFP de um ano ainda não saiu, a CVM responde 200 com o ZIP do ano
    anterior; os CSVs internos continuam com o sufixo do ano antigo. Conferimos
    pelo nome dos arquivos.
    """
    try:
        with zipfile.ZipFile(caminho) as z:
            return any(f"_{ano}.csv" in nome for nome in z.namelist())
    except (zipfile.BadZipFile, OSError):
        return False


def baixar_dfp(ano: int, timeout: int = 120) -> Optional[str]:
    """Baixa (e cacheia) o ZIP da DFP do ano. Retorna o caminho local ou None.

    Se o ano ainda não foi publicado, a CVM devolve o ZIP do ano anterior; detectamos
    pelos nomes dos CSVs e NÃO cacheamos — o ano fica corretamente indisponível.
    """
    destino = _cache_path(ano)
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return destino
    try:
        resp = requests.get(CVM_URL.format(ano=ano), timeout=timeout)
        resp.raise_for_status()
        with open(destino, "wb") as f:
            f.write(resp.content)
    except requests.RequestException:
        return None
    if not _zip_tem_ano(destino, ano):
        os.remove(destino)
        return None
    return destino


@lru_cache(maxsize=64)
def _ler_demonstracao(ano: int, prefixo: str) -> Optional[pd.DataFrame]:
    """Lê um CSV interno do ZIP (ex.: prefixo 'DRE_con', 'BPP_con', 'DFC_MI_con')."""
    caminho = baixar_dfp(ano)
    if not caminho:
        return None
    nome_csv = f"dfp_cia_aberta_{prefixo}_{ano}.csv"
    try:
        with zipfile.ZipFile(caminho) as z:
            if nome_csv not in z.namelist():
                return None
            with z.open(nome_csv) as fh:
                df = pd.read_csv(
                    io.TextIOWrapper(fh, encoding="latin-1"),
                    sep=";",
                    dtype={"CD_CVM": "Int64", "CD_CONTA": "string"},
                )
    except (zipfile.BadZipFile, ValueError, KeyError):
        return None
    # apenas o exercício corrente (ÚLTIMO) e contas em valor cheio
    if "ORDEM_EXERC" in df.columns:
        df = df[df["ORDEM_EXERC"] == "ÚLTIMO"]
    return df


@lru_cache(maxsize=1)
def _mapa_cnpj_por_cd_cvm() -> Dict[int, str]:
    """CD_CVM → CNPJ_CIA, lido de cad_cia_aberta.csv.

    O `composicao_capital` (DATA-03) é chaveado por CNPJ_CIA, NÃO por CD_CVM (armadilha 2);
    este mapa é o join. `{}` quando o arquivo falta ou não lê (never-raise)."""
    caminho = os.path.abspath(os.path.join(CACHE_DIR, "cad_cia_aberta.csv"))
    if not os.path.exists(caminho):
        return {}
    try:
        df = pd.read_csv(caminho, sep=";", encoding="latin-1", dtype={"CD_CVM": "Int64"})
    except (ValueError, OSError, UnicodeDecodeError):
        return {}
    mapa: Dict[int, str] = {}
    for cnpj, cd in zip(df.get("CNPJ_CIA", []), df.get("CD_CVM", [])):
        if pd.notna(cd):
            mapa[int(cd)] = cnpj
    return mapa


@lru_cache(maxsize=32)
def _composicao_capital(ano: int) -> Optional[pd.DataFrame]:
    """Lê `dfp_cia_aberta_composicao_capital_{ano}.csv` de dentro do ZIP da DFP.

    Mesmo padrão de `_ler_demonstracao` (latin-1, sep=';'), mas chaveado por CNPJ_CIA. Traz a
    contagem oficial de ações do ano (QT_ACAO_*). None quando o ZIP ou o CSV faltam — o
    composicao_capital só passou a ser publicado a partir de ~2020 (never-raise)."""
    caminho = baixar_dfp(ano)
    if not caminho:
        return None
    nome_csv = f"dfp_cia_aberta_composicao_capital_{ano}.csv"
    try:
        with zipfile.ZipFile(caminho) as z:
            if nome_csv not in z.namelist():
                return None
            with z.open(nome_csv) as fh:
                df = pd.read_csv(io.TextIOWrapper(fh, encoding="latin-1"), sep=";")
    except (zipfile.BadZipFile, ValueError, KeyError):
        return None
    return df


def contagem_oficial_do_ano(cd_cvm: int, ano: int) -> Optional[float]:
    """Contagem OFICIAL de ações do ano (CVM `composicao_capital`), CRUA — sem escala.

    = `QT_ACAO_TOTAL_CAP_INTEGR − QT_ACAO_TOTAL_TESOURO` (ON+PN em circulação), casada por
    CNPJ_CIA via `cad_cia_aberta.csv` (o composicao_capital é chaveado por CNPJ, não CD_CVM —
    armadilha 2). Devolve o valor CRU: a escala (MILHARES para ITUB4/BRSR6 × UNIDADES para
    GOAU4/CGRA4/CSNA3/EQTL3/ALUP11/MRFG3 — armadilha 3) é decidida no `build`, onde o
    `impliedSharesOutstanding` está disponível como âncora. Aplicá-la aqui, às cegas,
    reintroduziria o ×1000 por outro caminho (Pitfall 4).

    None quando o CNPJ não casa, o arquivo/ano falta, ou a linha não existe (never-raise).
    Quando o mesmo CNPJ traz mais de um `DT_REFER`/`VERSAO` (período de transição), fica com o
    mais recente e a maior versão (a vigente)."""
    cnpj = _mapa_cnpj_por_cd_cvm().get(cd_cvm)
    if cnpj is None:
        return None
    df = _composicao_capital(ano)
    if df is None or "CNPJ_CIA" not in df.columns:
        return None
    sub = df[df["CNPJ_CIA"] == cnpj]
    if sub.empty:
        return None
    ordenar = [col for col in ("DT_REFER", "VERSAO") if col in sub.columns]
    if ordenar:
        sub = sub.sort_values(ordenar)
    r = sub.iloc[-1]  # mais recente DT_REFER + maior VERSAO
    try:
        total = float(r["QT_ACAO_TOTAL_CAP_INTEGR"])
        tesouro = float(r["QT_ACAO_TOTAL_TESOURO"])
    except (ValueError, TypeError, KeyError):
        return None
    contagem = total - tesouro
    return contagem if contagem > 0 else None


def _valor_conta(
    df: Optional[pd.DataFrame],
    cd_cvm: int,
    codigos: list,
    nomes: list,
    nome_primeiro: bool = False,
    aplicar_escala: bool = True,
) -> Optional[float]:
    """Extrai VL_CONTA por CD_CONTA e/ou nome (DS_CONTA).

    - `nome_primeiro`: tenta o casamento exato por nome ANTES do código (útil quando o
      código varia entre templates, como o PL em 2.03 para empresas e 2.08 para bancos).
    - `aplicar_escala`: aplica ESCALA_MOEDA (MIL -> *1000); deve ser False para contas
      por ação (LPA), que já vêm em R$/ação.
    """
    if df is None:
        return None
    sub = df[df["CD_CVM"] == cd_cvm]
    if sub.empty:
        return None
    escala = 1000 if (aplicar_escala and sub["ESCALA_MOEDA"].iloc[0] == "MIL") else 1
    sub = sub.copy()
    sub["_ds"] = sub["DS_CONTA"].map(_norm)
    nomes_norm = [_norm(n) for n in nomes]

    def por_codigo():
        for cod in codigos:
            achou = sub[sub["CD_CONTA"] == cod]
            if not achou.empty:
                return float(achou["VL_CONTA"].iloc[0]) * escala
        return None

    def por_nome():
        for alvo in nomes_norm:  # exato
            achou = sub[sub["_ds"] == alvo]
            if not achou.empty:
                return float(achou["VL_CONTA"].iloc[0]) * escala
        for alvo in nomes_norm:  # contém
            achou = sub[sub["_ds"].str.contains(alvo, na=False)]
            if not achou.empty:
                return float(achou["VL_CONTA"].iloc[0]) * escala
        return None

    ordem = (por_nome, por_codigo) if nome_primeiro else (por_codigo, por_nome)
    for fn in ordem:
        v = fn()
        if v is not None:
            return v
    return None


def _distribuicoes_proventos(df: Optional[pd.DataFrame], cd_cvm: int) -> Optional[float]:
    """Proventos PAGOS no ano (dividendos + JCP) na seção de financiamento da DFC (6.03.*).

    Casado por NOME (DS_CONTA contém "dividendo"), porque os códigos 6.03.NN NÃO são
    padronizados entre empresas (em TAEE 6.03.04 é "Debêntures - Juros"; o provento está em
    6.03.09). Inclui o JCP — que o Yahoo historicamente NÃO captura para bancos, subestimando
    o payout e, por consequência, o DDM. Exclui pagamentos a minoritários e proventos
    RECEBIDOS. Soma as linhas casadas (algumas empresas separam div e JCP) e devolve o valor
    absoluto (a saída de caixa vem negativa). None quando não há linha de provento na DFC.
    """
    if df is None:
        return None
    sub = df[df["CD_CVM"] == cd_cvm]
    if sub.empty:
        return None
    escala = 1000 if sub["ESCALA_MOEDA"].iloc[0] == "MIL" else 1
    fin = sub[sub["CD_CONTA"].astype("string").str.startswith("6.03", na=False)]
    if fin.empty:
        return None
    ds = fin["DS_CONTA"].map(_norm)
    incluir = ds.str.contains("dividendo", na=False)
    excluir = ds.str.contains("nao control|minoritar|recebid", na=False, regex=True)
    rows = fin[(incluir & ~excluir).values]
    if rows.empty:
        return None
    return abs(float(rows["VL_CONTA"].astype(float).sum())) * escala


def _distribuicoes_proventos_amplo(df: Optional[pd.DataFrame], cd_cvm: int) -> Optional[float]:
    """DIAGNÓSTICO (SAN-03) — irmã de `_distribuicoes_proventos`, com o filtro de inclusão AMPLO.

    Idêntica em tudo à função estreita (mesma varredura da DFC `6.03.*`, mesmas exclusões,
    mesmo `abs()`, mesma escala) EXCETO no filtro de inclusão, que passa a casar
    "dividendo" OU "juros sobre capital". Mede o JCP que o filtro estreito PERDE, sem depender
    de `num_acoes`.

    Existe como função separada — e NÃO como parâmetro de `_distribuicoes_proventos` — de
    propósito: a função estreita alimenta `c.dividendos` (que os motores consomem) e precisa
    continuar devolvendo o mesmo número SUJO de hoje, que é o teste de regressão do DATA-01
    (Fase 9). Um parâmetro com default seria um convite a "só ligar" o filtro amplo e apagar
    a prova. Este valor alimenta SÓ o detector do SAN-03.
    """
    if df is None:
        return None
    sub = df[df["CD_CVM"] == cd_cvm]
    if sub.empty:
        return None
    escala = 1000 if sub["ESCALA_MOEDA"].iloc[0] == "MIL" else 1
    fin = sub[sub["CD_CONTA"].astype("string").str.startswith("6.03", na=False)]
    if fin.empty:
        return None
    ds = fin["DS_CONTA"].map(_norm)
    # "juros sobre.*capital proprio": a DFC do BRSR6 fila em "Juros sobre O Capital Próprio
    # Pagos" — o literal "juros sobre capital proprio" não casaria por causa do "o"; o `.*`
    # tolera o artigo. A âncora "proprio" (WR-01) impede que o `.*` case linhas de
    # financiamento que NÃO são JCP ("juros sobre capital de giro/terceiros", "juros sobre
    # empréstimos ... capital") e inflem os proventos — JCP é "juros sobre o capital PRÓPRIO".
    # `ds` já vem NFKD/ascii-folded por `_norm` (próprio → proprio).
    incluir = ds.str.contains("dividendo|juros sobre.*capital proprio", na=False, regex=True)
    excluir = ds.str.contains("nao control|minoritar|recebid", na=False, regex=True)
    rows = fin[(incluir & ~excluir).values]
    if rows.empty:
        return None
    return abs(float(rows["VL_CONTA"].astype(float).sum())) * escala


def _tem_empresa(df: Optional[pd.DataFrame], cd_cvm: int) -> bool:
    return df is not None and not df.empty and (df["CD_CVM"] == cd_cvm).any()


def _consolidado_ou_individual(ano: int, base: str, cd_cvm: int):
    """Consolidado quando a EMPRESA está nele; senão o individual.

    Antes caía para o individual só quando o frame consolidado estava GLOBALMENTE vazio — o
    que ignorava empresas single-entity (sem subsidiárias para consolidar, ex.: SANEPAR), que
    publicam SÓ o individual e somem do consolidado (cheio de outras empresas). Resultado: a
    análise não achava lucro e abortava com "não encontrei dados". Agora a escolha é POR
    EMPRESA: usa o consolidado se o CD_CVM estiver nele, senão o individual.
    """
    con = _ler_demonstracao(ano, f"{base}_con")
    if _tem_empresa(con, cd_cvm):
        return con
    ind = _ler_demonstracao(ano, f"{base}_ind")
    if _tem_empresa(ind, cd_cvm):
        return ind
    # nenhum contém a empresa: devolve o que existir (mantém o comportamento de _valor_conta→None)
    return con if (con is not None and not con.empty) else ind


def fundamentos_do_ano(cd_cvm: int, ano: int) -> Dict[str, Optional[float]]:
    """Extrai as contas-chave de uma empresa em um ano."""
    dre = _consolidado_ou_individual(ano, "DRE", cd_cvm)
    bpa = _consolidado_ou_individual(ano, "BPA", cd_cvm)
    bpp = _consolidado_ou_individual(ano, "BPP", cd_cvm)
    dfc = None
    for prefixo in ("DFC_MI_con", "DFC_MD_con", "DFC_MI_ind", "DFC_MD_ind"):
        cand = _ler_demonstracao(ano, prefixo)
        if _tem_empresa(cand, cd_cvm):  # POR EMPRESA (single-entity some do _con global cheio)
            dfc = cand
            break

    return {
        "lucro_liquido": _valor_conta(
            dre, cd_cvm,
            ["3.11", "3.13", "3.09"],
            ["Lucro/Prejuízo Consolidado do Período", "Lucro/Prejuízo do Período",
             "Lucro Líquido do Período", "Lucro Líquido das Operações Continuadas"],
        ),
        "vendas_liquidas": _valor_conta(
            dre, cd_cvm, ["3.01"],
            ["Receita de Venda de Bens e/ou Serviços", "Receitas da Intermediação Financeira",
             "Receita de Venda"],
        ),
        "patrimonio_liquido": _valor_conta(
            bpp, cd_cvm, ["2.03", "2.08"],
            ["Patrimônio Líquido Consolidado", "Patrimônio Líquido"],
            nome_primeiro=True,
        ),
        "ativo_circulante": _valor_conta(bpa, cd_cvm, ["1.01"], ["Ativo Circulante"]),
        "passivo_circulante": _valor_conta(bpp, cd_cvm, ["2.01"], ["Passivo Circulante"]),
        "divida_lp": _valor_conta(
            bpp, cd_cvm, ["2.02.01"],
            ["Empréstimos e Financiamentos", "Passivo Não Circulante"],
        ),
        "ativo_intangivel": _valor_conta(bpa, cd_cvm, ["1.02.04"], ["Intangível"]),
        "fco": _valor_conta(
            dfc, cd_cvm, ["6.01"],
            ["Caixa Líquido Atividades Operacionais",
             "Caixa Líquido Gerado pelas Atividades Operacionais"],
        ),
        # LPA básico por ação ON (R$/ação) — NÃO aplicar escala MIL.
        "lpa": _valor_conta(dre, cd_cvm, ["3.99.01.01", "3.99.01"],
                            ["Lucro por Ação"], aplicar_escala=False),
        # Proventos pagos no ano — FILTRO AMPLO (casa "dividendo" OU "juros sobre capital").
        # DATA-01 (Fase 9): promove o filtro amplo a fonte de `c.dividendos`, capturando o JCP
        # que o filtro estreito perdia em ~13 empresas (BRSR6 payout 10,3% → ~55,9%). A correção
        # é ampliar o filtro DENTRO da CVM — NÃO trocar de fonte para o Yahoo. A gêmea estreita
        # `_distribuicoes_proventos` permanece no módulo como referência (teste do filtro estreito).
        "dividendos_distribuidos": _distribuicoes_proventos_amplo(dfc, cd_cvm),
        # DIAGNÓSTICO (SAN-04): lucro atribuído aos sócios da CONTROLADORA (3.11.01). NÃO é a
        # fonte de `lucro_liquido` (que segue o consolidado 3.11/3.13/3.09). None sem a linha.
        "lucro_controlador": _valor_conta(
            dre, cd_cvm, ["3.11.01"],
            ["Atribuído a Sócios da Empresa Controladora",
             "Atribuído a Sócios da Empresa Controlada"],
        ),
        # DIAGNÓSTICO (SAN-04): participação de não-controladores no PL. O código varia por
        # template (2.03.09 empresas, 2.07.02 BBAS3/BBDC4/BRSR6, 2.08.09 ITUB4) → passamos os
        # três, com nome_primeiro=True (mesma defesa do patrimonio_liquido). None sem a linha.
        "pl_nao_controladores": _valor_conta(
            bpp, cd_cvm, ["2.03.09", "2.07.02", "2.08.09"],
            ["Participação dos Acionistas Não Controladores",
             "Participação dos Não Controladores"],
            nome_primeiro=True,
        ),
        # DIAGNÓSTICO (SAN-03): proventos por FILTRO AMPLO (dividendo OU JCP) — mede o JCP que
        # o filtro estreito perde, sem depender de num_acoes. Alimenta SÓ o detector.
        "proventos_filtro_amplo": _distribuicoes_proventos_amplo(dfc, cd_cvm),
    }
