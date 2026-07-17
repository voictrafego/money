"""Indicadores macro do Banco Central (API SGS) — grátis.

Usado para: Selic (corte do DY nos filtros, Cap. 8) e IPCA (inflação BR para o CAPM).
API pública: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados
"""

from __future__ import annotations

import datetime
import os
import statistics
import time
from typing import Dict, List, Optional

import requests
import yaml

SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/{n}?formato=json"

# Códigos das séries no SGS
SELIC_META = 432       # Meta Selic definida pelo Copom (% a.a.)
IPCA_12M = 13522       # IPCA acumulado em 12 meses (%)


def _ultimo_valor(codigo: int, n: int = 1, timeout: int = 20) -> Optional[float]:
    url = SGS_URL.format(codigo=codigo, n=n)
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        dados = resp.json()
        if not dados:
            return None
        return float(dados[-1]["valor"].replace(",", "."))
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def selic_meta() -> Optional[float]:
    """Meta Selic atual em fração (ex.: 0.105 para 10,5%). None se indisponível."""
    v = _ultimo_valor(SELIC_META)
    return v / 100.0 if v is not None else None


def ipca_12m() -> Optional[float]:
    """IPCA acumulado 12 meses em fração. None se indisponível."""
    v = _ultimo_valor(IPCA_12M)
    return v / 100.0 if v is not None else None


def selic_para_capm(fallback: float) -> float:
    """rf do CAPM local (Cap. 16/17): Selic ao vivo do BCB quando disponível, senão o
    fallback de config. Puro e sem exceção — espelha o padrão `selic_meta() or 0.105` já
    usado p/ o corte de DY nos entry points.

    Pureza da engine (FIX-03): isto é chamado SÓ nos pontos de entrada (cli/app), que
    resolvem o rf uma única vez e o injetam em `cfg['capm']['rf_local']`. `analisar_acao`
    NÃO chama esta função — permanece offline/determinística lendo o rf já resolvido.
    """
    return selic_meta() or fallback


def _selic_historico(anos: int = 10) -> List[float]:
    """Meta Selic diária dos últimos `anos` anos, em fração (lista). [] em qualquer falha.

    Consulta por intervalo de datas: a série diária 432 do SGS limita `/ultimos` a 20 pontos
    e a janela diária a 10 anos — por isso usamos dataInicial/dataFinal logo abaixo de 10 anos.
    """
    hoje = datetime.date.today()
    ini = hoje - datetime.timedelta(days=anos * 365)  # < 10 anos exatos (respeita a trava do BCB)
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{SELIC_META}/dados"
        f"?formato=json&dataInicial={ini.strftime('%d/%m/%Y')}&dataFinal={hoje.strftime('%d/%m/%Y')}"
    )
    # O SGS é intermitente (timeouts esporádicos por IP); re-tenta antes de degradar p/ a Selic
    # spot — assim uma falha pontual não congela o rf no pico de ciclo (a sidebar cacheia 1h).
    for tentativa in range(3):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            dados = resp.json()
            if isinstance(dados, list) and dados:
                return [float(d["valor"].replace(",", ".")) / 100.0 for d in dados]
        except (requests.RequestException, ValueError, KeyError, TypeError):
            pass
        if tentativa < 2:
            time.sleep(0.5 * (tentativa + 1))
    return []


def _compor_deflatores(ipca_por_ano: Dict[int, float]) -> Dict[int, float]:
    """Compõe os deflatores anuais a partir do IPCA anual em fração (função PURA, sem rede).

    Devolve `{ano: fator para o último ano T}` = `prod(1 + ipca[y]) para y in (ano+1..T)`,
    com `defl[T] = 1.0` (D-03: reais do ÚLTIMO ano, NÃO ano-base fixo). Para IPCA positivo,
    quanto mais antigo o ano, MAIOR o fator. Série vazia → {} (never-raise; espelha o
    `_selic_historico → []`). É esta a matemática que o teste OFFLINE trava — independente de
    qual série legítima do SGS alimentou (a escolha da série só afeta a precisão numérica).
    """
    if not ipca_por_ano:
        return {}
    anos = sorted(ipca_por_ano)
    T = anos[-1]
    defl: Dict[int, float] = {}
    for ano in anos:
        fator = 1.0
        for y in range(ano + 1, T + 1):
            fator *= 1.0 + ipca_por_ano.get(y, 0.0)
        defl[ano] = fator
    return defl


def _ipca_anual_dezembro(anos: int = 10) -> Dict[int, float]:
    """IPCA acumulado 12m no fechamento de DEZEMBRO de cada ano, em fração — `{ano: ipca}`.

    Esqueleto copiado de `_selic_historico`: consulta por intervalo de datas (dataInicial/
    dataFinal), 3 retries com backoff, degradação graciosa para {} em qualquer falha. Usa a
    série TRAVADA SGS 13522 (`IPCA_12M`): o acumulado 12m no fechamento de dezembro É, por
    definição, o IPCA do ano-calendário — sem escolha livre de ano-base (RESEARCH Open Q2
    RESOLVED/LOCKED; A1). Filtra os pontos de dezembro (mês 12) da série mensal 13522.
    """
    hoje = datetime.date.today()
    ini = hoje - datetime.timedelta(days=anos * 365)  # < 10 anos exatos (trava do BCB)
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{IPCA_12M}/dados"
        f"?formato=json&dataInicial={ini.strftime('%d/%m/%Y')}&dataFinal={hoje.strftime('%d/%m/%Y')}"
    )
    for tentativa in range(3):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            dados = resp.json()
            if isinstance(dados, list) and dados:
                por_ano: Dict[int, float] = {}
                for d in dados:
                    _dia, mes, ano = d["data"].split("/")
                    if int(mes) == 12:
                        por_ano[int(ano)] = float(d["valor"].replace(",", ".")) / 100.0
                return por_ano
        except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
            pass
        if tentativa < 2:
            time.sleep(0.5 * (tentativa + 1))
    return {}


def ipca_deflatores_anuais(anos: int = 10) -> Dict[int, float]:
    """Deflatores anuais do IPCA (BCB SGS 13522) → `{ano: fator para o último ano}`.

    Traz cada ano da série de lucro a **reais do último ano** (D-03), para o motor CÍCLICO
    parar de somar reais nominais de anos diferentes (PRIM-04). Dado macro OBJETIVO do BCB
    (como o `rf`), NÃO um knob de valuation — sem escolha livre de ano-base, sem grau de
    liberdade novo. Degradação graciosa: rede falha → {} (a engine cai na série nominal).

    Pureza da engine (FIX-03, espelha `selic_ciclo_para_capm`): chamado SÓ nos entry points
    (cli/app), que resolvem os deflatores UMA vez e os carimbam em `cfg["macro"]
    ["ipca_deflatores"]`. `analisar_acao` NÃO chama esta função — lê o valor já carimbado e
    permanece offline/determinística. A rede vive só em `_ipca_anual_dezembro`; a composição
    (`_compor_deflatores`) é pura e testável sem rede.
    """
    return _compor_deflatores(_ipca_anual_dezembro(anos))


def ipca_ciclo_para_g(fallback: float, anos: int = 10) -> float:
    """π_ciclo do `g_cap` = IPCA MÉDIO dos últimos `anos` anos (through-the-cycle).

    Irmão EXATO de `selic_ciclo_para_capm`: média ARITMÉTICA (`sum/len`) da série anual do
    IPCA (BCB SGS 13522), medida na MESMA janela do `rf` (`capm.rf_ciclo_anos`). É essa
    simetria de janela rf↔π_ciclo — e nada mais — que torna o valuation invariante à
    inflação (GROW-02): o `g_cap = (1+π_ciclo)(1+PIB_real)−1` cresce com a inflação na mesma
    medida em que o `rf` do Ke cresce. Reusa a MESMA série SGS 13522 já usada pelos deflatores
    (PRIM-04) — zero fonte de rede nova, zero grau de liberdade novo (dado objetivo do BCB,
    NÃO knob de valuation).

    Pureza da engine (FIX-03, espelha `selic_ciclo_para_capm`/`ipca_deflatores_anuais`):
    chamado SÓ nos entry points (cli/app), que resolvem o π_ciclo UMA vez e o carimbam em
    `cfg["macro"]["pi_ciclo"]`. `analisar_acao` NÃO chama esta função — lê o valor já
    carimbado e permanece offline/determinística. Degradação graciosa: rede falha → fallback
    (o default `macro.pi_ciclo` do config); a engine ainda deriva um `g_cap` determinístico.
    """
    por_ano = _ipca_anual_dezembro(anos)
    if por_ano:
        return sum(por_ano.values()) / len(por_ano)  # aritmética, = rf (sum(hist)/len(hist))
    return fallback


def selic_ciclo_para_capm(fallback: float, anos: int = 10) -> float:
    """rf do CAPM/DDM = Selic MÉDIA dos últimos `anos` anos (through-the-cycle).

    Numa perpetuidade (DDM), a taxa de desconto deve refletir o juro de LONGO PRAZO, não o
    pico de ciclo: a Selic spot (ex.: 14,25%) infla o Ke e subavalia todo o mercado de
    dividendos. A média de ~10 anos da meta Selic (BCB) é um rf "through-the-cycle" objetivo
    e auto-atualizável. Degradação graciosa: sem a série histórica → Selic spot
    (`selic_para_capm`) → fallback de config. Chamado SÓ nos entry points (a engine lê cfg e
    permanece determinística).
    """
    hist = _selic_historico(anos)
    if hist:
        return sum(hist) / len(hist)
    return selic_para_capm(fallback)


# ---------------------------------------------------------------------------
# Beta setorial + Blume (KE-03) — DADO derivado do mercado, FORA do lock (D-07).
# Fonte unica offline (D-05/D-06): gerado por scripts/gerar_beta_setorial.py,
# versionado em data/beta_setorial.yaml, carimbado em cfg["capm"]["beta_setorial"]
# nos entry points. A engine LE o mapa e aplica Blume (capm.beta_blume) — nunca
# recomputa a mediana (analyze monta 1 ticker, sem pares: seria o anti-padrao WR-03).
# ---------------------------------------------------------------------------

_PREFIXO_HOLDING = "Emp. Adm. Part. - "

_RAIZ_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CAMINHO_BETA_SETORIAL = os.path.join(_RAIZ_REPO, "data", "beta_setorial.yaml")


def _normalizar_setor(setor: Optional[str]) -> str:
    """Higieniza a string de setor da CVM para a chave de agrupamento (D-01).

    Remove o prefixo de holding "Emp. Adm. Part. - " para que a holding e a operadora do
    MESMO negocio (mesmo risco de negocio, premissa do KE-03) caiam no mesmo grupo — ex.:
    "Emp. Adm. Part. - Energia Eletrica" e "Energia Eletrica". So higieniza a representacao;
    NAO troca a chave `c.setor` da empresa (D-01). Never-raise: None/"" -> "".
    """
    if not setor:
        return ""
    s = str(setor).strip()
    if s.startswith(_PREFIXO_HOLDING):
        s = s[len(_PREFIXO_HOLDING):].strip()
    return s


def mapa_beta_setorial(empresas, limiar: int = 3) -> Dict[str, float]:
    """Mapa `setor_normalizado -> mediana(beta cru)` do universo (D-02); so setores n>=limiar.

    Agrupa por `_normalizar_setor(c.setor)`, coleta os `c.beta` NAO-None e emite a mediana
    apenas para setores com pelo menos `limiar` betas disponiveis. O limiar default 3 e'
    ESTRUTURAL: e' o menor n em que a mediana rejeita 1 outlier — a propriedade pela qual o
    D-02 escolheu a mediana (uma propriedade da mediana amostral, NAO um alvo de ticker).
    Beta None nao entra na mediana nem conta para o limiar. Universo vazio -> {} (never-raise).
    O valor e' o beta CRU de proposito: o Blume (`0,33 + 0,67 x base`) e' aplicado UMA vez
    depois, sobre este agregado, por `capm.beta_blume` (D-03).
    """
    por_setor: Dict[str, List[float]] = {}
    for c in empresas or []:
        beta_cru = getattr(c, "beta", None)
        if beta_cru is None:
            continue
        chave = _normalizar_setor(getattr(c, "setor", ""))
        if not chave:
            continue
        por_setor.setdefault(chave, []).append(float(beta_cru))
    return {
        setor: float(statistics.median(betas))
        for setor, betas in por_setor.items()
        if len(betas) >= limiar
    }


def carregar_beta_setorial(path: Optional[str] = None) -> Dict[str, float]:
    """Le o artefato versionado `data/beta_setorial.yaml` -> `{setor: mediana_beta}`.

    Fonte unica carimbada em `cfg["capm"]["beta_setorial"]` pelos entry points (irmao de
    `ipca_deflatores_anuais`). Arquivo ausente/vazio/malformado -> {} (degradacao graciosa;
    a engine cai no fallback do beta individual Blume, D-04). Sempre `safe_load`.
    """
    caminho = path or CAMINHO_BETA_SETORIAL
    try:
        with open(caminho, encoding="utf-8") as fh:
            dados = yaml.safe_load(fh) or {}
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(dados, dict):
        return {}
    return {str(k): float(v) for k, v in dados.items() if v is not None}


def carimbar_beta_setorial(cfg: dict) -> None:
    """Carimba o mapa `setor -> mediana(beta)` em `cfg["capm"]["beta_setorial"]` (D-05/D-06).

    Irmao de `cli._carimbar_macro`: resolve a FONTE ÚNICA (o artefato versionado) UMA vez no
    entry point e a grava em `cfg`, para `analyze` e `rank` lerem o MESMO mapa — sem isso a
    mesma acao mostraria beta setorial (logo Ke) diferente entre os menus (anti-padrao WR-03,
    D-06). Leitura de arquivo local (sem rede); ausente/vazio -> {} (degradacao graciosa).
    Muta `cfg` in-place; cria o bloco `capm` se ausente.
    """
    cfg.setdefault("capm", {})
    cfg["capm"]["beta_setorial"] = carregar_beta_setorial()
