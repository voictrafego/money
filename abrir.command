#!/bin/bash
# Dê duplo-clique neste arquivo (ou rode no terminal) para abrir o Analista de Dividendos no navegador.
cd "$(dirname "$0")"
./.venv/bin/streamlit run app.py
