"""Substrato do snapshot de sanidade (v2.4 / Fase 8 / plano 08-03).

NAO tem prefixo `test_` de proposito: o pytest nao o coleta (e nao precisa de entrada no
`classificacao.yaml`). Como `tests/` nao tem `__init__.py`, o pytest poe `tests/` no
`sys.path` -> os testes fazem `import helpers_sanidade` direto.

Carrega o snapshot congelado dos 104 tickers (`snapshot_sanidade_2026-07-14.yaml`) OFFLINE
e reconstroi um `CompanyData` por ticker, sem tocar a rede.

**Este modulo NAO pode conter nenhuma verificacao (a palavra reservada de checagem do
Python).** O detector do BLIND-04a (`helpers_blindagem.py:_helpers_conferidores`) trata
"funcao nao-teste que confere" como HELPER QUE CONFERE e passa a rastrear constantes numericas
atraves dela. Um helper limpo (que so' CONSTROI, nunca confere) mantem o detector longe.
"""

from __future__ import annotations

import pathlib
from typing import Dict, Optional

import yaml

from analista.core.fundamentals import CompanyData

RAIZ_REPO = pathlib.Path(__file__).resolve().parent.parent
# O SUJO (evidencia congelada) — a regua e os detectores (test_sanidade_checks) leem daqui.
CAMINHO_SNAPSHOT = RAIZ_REPO / "tests" / "fixtures" / "snapshot_sanidade_2026-07-14.yaml"
# O LIMPO (produto do codigo consertado, DATA-06) — SO a medicao de "hoje"
# (_pares_e_buckets_de_hoje) le daqui, para a monotonicidade enxergar o progresso. Regenravel
# pelo scripts/capturar_snapshot_limpo.py; nao e evidencia congelada como o sujo.
CAMINHO_SNAPSHOT_LIMPO = (
    RAIZ_REPO / "tests" / "fixtures" / "snapshot_sanidade_limpo_2026-07-15.yaml"
)

# chaves globais do YAML (nao sao tickers) — puladas na reconstrucao.
_CHAVES_GLOBAIS = {"data_base", "falhas"}

# series {ano: float} congeladas por ticker (mesmos nomes dos campos de CompanyData).
_SERIES_NUM = (
    "lucro_liquido",
    "lucro_controlador",
    "patrimonio_liquido",
    "pl_nao_controladores",
    "lpa_cvm",
    "dividendos",
    "proventos_filtro_amplo",
    "num_acoes",
    "dpa_por_ano",
)


def carregar_snapshot_bruto(path: Optional[str] = None) -> dict:
    """Le o YAML congelado como dict cru. `safe_load`, NUNCA `load`."""
    caminho = pathlib.Path(path) if path else CAMINHO_SNAPSHOT
    return yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}


def tickers_do_snapshot(path: Optional[str] = None) -> set:
    """Conjunto dos tickers presentes no snapshot (exclui as chaves globais)."""
    bruto = carregar_snapshot_bruto(path)
    return {k for k in bruto if k not in _CHAVES_GLOBAIS}


def falhas_do_snapshot(path: Optional[str] = None) -> dict:
    """O bloco `falhas:` (ticker -> motivo da degradacao). {} se ausente."""
    return dict(carregar_snapshot_bruto(path).get("falhas") or {})


def carregar_snapshot_sanidade(path: Optional[str] = None) -> Dict[str, CompanyData]:
    """Reconstroi um `CompanyData` por ticker a partir do YAML congelado, OFFLINE.

    `avisos` e `confianca` ficam com o default do dataclass — ou seja, `nao_avaliada`
    (D-03): um CompanyData reconstruido a mao NAO nasce parecendo limpo.
    """
    bruto = carregar_snapshot_bruto(path)
    empresas: Dict[str, CompanyData] = {}
    for tk, dados in bruto.items():
        if tk in _CHAVES_GLOBAIS or not isinstance(dados, dict):
            continue
        c = CompanyData(
            ticker=tk,
            nome=dados.get("nome", "") or "",
            setor=dados.get("setor", "") or "",
            anos=[int(a) for a in dados.get("anos", [])],
        )
        c.preco_atual = dados.get("preco_atual")
        c.beta = dados.get("beta")
        c.market_cap = dados.get("market_cap")
        c.implied_shares_outstanding = dados.get("implied_shares_out")
        c.splits = {str(k): float(v) for k, v in (dados.get("splits") or {}).items()}
        c.origem_num_acoes = {
            int(a): str(v) for a, v in (dados.get("origem_num_acoes") or {}).items()
        }
        for serie in _SERIES_NUM:
            destino = getattr(c, serie)
            for ano, valor in (dados.get(serie) or {}).items():
                destino[int(ano)] = float(valor)
        empresas[tk] = c
    return empresas
