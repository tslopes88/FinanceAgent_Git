# -*- coding: utf-8 -*-
"""
FinanceAgent - Motor de Processamento, Categorização e Gestão de Metas Orçamentárias
Arquitetura: Motor Heurístico de Classificação e Tetos Orçamentários
"""

import os
import re
import sys
from pathlib import Path
import pandas as pd

# 1. Mapeamento de Regras e Padrões de Busca (Regex)
REGRAS_CATEGORIAS = {
    "Transporte & Mobilidade": [
        r"movida", r"posto", r"combustivel", r"gasolina", r"uber", 
        r"99app", r"estacionamento", r"brasil park"
    ],
    "Alimentação - Padarias & Doces": [
        r"peter p[aã]o", r"celeiro do p[aã]o", r"padaria", 
        r"caf[eé] com baguete", r"cacau show", r"confeitaria"
    ],
    "Alimentação - Supermercados": [
        r"super mini", r"hortifruti", r"carrefour", r"atacadao", 
        r"extra", r"supermercado", r"fiorotti"
    ],
    "Alimentação - Restaurantes": [
        r"espetinho", r"sorveteria", r"restaurante", r"ifood", 
        r"burger", r"rocon", r"lanchonete"
    ],
    "Compras & Varejo": [
        r"mercado livre", r"americanas", r"tiktok shop", 
        r"ponto sports", r"amazon", r"shopee", r"magalu"
    ],
    "Assinaturas & Streaming": [
        r"apple\.com", r"deezer", r"google play", r"meli\+", 
        r"xbox", r"compra e volta", r"netflix", r"spotify", r"punko"
    ],
    "Educação": [
        r"unintese", r"faculdade", r"curso", r"escola", r"universidade"
    ],
    "Saúde & Farmácia": [
        r"drogasil", r"raia", r"drogaria", r"farmacia", r"pacheco"
    ],
    "Tarifas Bancárias": [
        r"tarifa", r"iof", r"encargos", r"limite emergencial", r"anuidade"
    ],
    "Família & Pessoal": [
        r"parente", r"familiar", r"repasse", r"ajuda familiar"
    ],
    "Investimentos & Reserva": [
        r"cofrinho", r"reserva por gastos", r"dizimo", r"dízimo", r"cdi"
    ]
}

# 2. Metas e Tetos Orçamentários Mensais (Configurável)
TETOS_ORCAMENTARIOS = {
    "Transporte & Mobilidade": 2500.00,
    "Alimentação - Padarias & Doces": 150.00,
    "Alimentação - Restaurantes": 200.00,
    "Alimentação - Supermercados": 400.00,
    "Compras & Varejo": 400.00,
    "Assinaturas & Streaming": 150.00,
    "Saúde & Farmácia": 200.00,
    "Educação": 200.00,
    "Tarifas Bancárias": 0.00
}

def classificar_transacao(descricao: str, valor: float) -> tuple:
    desc = str(descricao).lower()

    # 1. Regra de Fluxo Interno (Mesma Titularidade)
    if "transferencia mesma titularidade" in desc or "fluxo interno" in desc:
        return "Fluxo Interno", "Neutro"

    # 2. Rendimentos de Saldo / CDI
    if "rendimento" in desc or "cdi" in desc:
        return "Receitas Externas", "Receita"

    # 3. Varredura por Regex
    for categoria, patterns in REGRAS_CATEGORIAS.items():
        for pattern in patterns:
            if re.search(pattern, desc):
                if categoria == "Família & Pessoal":
                    tipo = "Receita" if valor > 0 else "Despesa"
                elif categoria == "Investimentos & Reserva":
                    tipo = "Reserva"
                else:
                    tipo = "Receita" if valor > 0 else "Despesa"
                return categoria, tipo

    tipo = "Receita" if valor > 0 else "Despesa"
    return "Outros / Diversos", tipo

def verificar_alertas_orcamentarios(df: pd.DataFrame):
    print("\n-------------------------------------------------------------")
    print("           ANALISE DE METAS E ALERTAS ORCAMENTARIOS          ")
    print("-------------------------------------------------------------")
    
    col_cat = "Categoria_Classificada" if "Categoria_Classificada" in df.columns else "Categoria"
    col_val = "Valor_BRL" if "Valor_BRL" in df.columns else "Valor (R$)"
    col_tipo = "Tipo_Movimentacao" if "Tipo_Movimentacao" in df.columns else "Tipo Movimentação"

    # Apenas Despesas Operacionais (excluindo Receitas e Reservas)
    df_desp = df[df[col_tipo] == "Despesa"].copy()
    if df_desp.empty:
        print("Nenhuma despesa registrada para o período.")
        return

    gastos_por_cat = df_desp.groupby(col_cat)[col_val].sum().abs()

    for categoria, teto in TETOS_ORCAMENTARIOS.items():
        gasto_real = gastos_por_cat.get(categoria, 0.0)
        pct = (gasto_real / teto * 100) if teto > 0 else 0.0

        if teto == 0.0:
            if gasto_real > 0:
                print(f"[ALERTA CRÍTICO] {categoria}: Gasto de R$ {gasto_real:.2f} (Meta: R$ 0,00 - Custo Indesejado)")
            else:
                print(f"[OK] {categoria}: R$ 0,00")
        elif gasto_real > teto:
            excesso = gasto_real - teto
            print(f"[ESTOURO] {categoria}: R$ {gasto_real:.2f} / R$ {teto:.2f} ({pct:.1f}%) -> Excedente de R$ {excesso:.2f}")
        elif pct >= 80.0:
            print(f"[ATENÇÃO] {categoria}: R$ {gasto_real:.2f} / R$ {teto:.2f} ({pct:.1f}% da meta atingida)")
        else:
            print(f"[DENTRO DA META] {categoria}: R$ {gasto_real:.2f} / R$ {teto:.2f} ({pct:.1f}%)")

    print("-------------------------------------------------------------\n")
