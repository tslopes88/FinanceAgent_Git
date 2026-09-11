# -*- coding: utf-8 -*-
"""
FinanceAgent - Gerador Autônomo de Gráficos e Painel Visual
Gera gráficos em PNG de alta resolução para acompanhamento visual do mês.
Alinhado com as categorias canônicas de process_extrato.py.
"""

import matplotlib.pyplot as plt
from process_extrato import REGRAS_CATEGORIAS

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

def gerar_graficos_demonstracao():
    # 1. Dados de Consumo Operacional Canônicos
    categorias = [
        "Transporte & Mobilidade",
        "Alimentação - Supermercados",
        "Compras & Varejo",
        "Alimentação - Restaurantes",
        "Assinaturas & Apps",
        "Educação",
        "Alimentação - Padarias",
        "Saúde & Farmácia",
        "Tarifas Bancárias"
    ]
    valores = [464.30, 680.75, 448.90, 197.00, 90.80, 130.05, 45.90, 125.60, 50.45]
    cores = ["#1F4E79", "#2F5597", "#5B9BD5", "#41719C", "#ED7D31", "#A5A5A5", "#F8CBAD", "#FFC000", "#C00000"]

    # Gráfico Donut
    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw=dict(aspect="equal"))
    wedges, texts, autotexts = ax.pie(
        valores, 
        autopct='%1.1f%%',
        startangle=140,
        pctdistance=0.82,
        colors=cores,
        textprops=dict(color="black", fontsize=8.5, weight="bold")
    )

    centro = plt.Circle((0, 0), 0.65, fc='white')
    fig.gca().add_artist(centro)

    ax.legend(
        wedges, 
        [f"{c}: R$ {v:,.2f}" for c, v in zip(categorias, valores)],
        title="Categorias de Gastos (Consumo)",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=9.5
    )

    total_desp = sum(valores)
    plt.title(f"Distribuição do Consumo Operacional\nTotal: R$ {total_desp:,.2f}", fontsize=13, weight="bold", pad=20)
    plt.tight_layout()
    plt.savefig("saida/grafico_categorias_consolidado.png", dpi=300, bbox_inches="tight")
    print("Grafico 'saida/grafico_categorias_consolidado.png' gerado com sucesso!")

    # 2. Gráfico de Barras Horizontais: Subdivisão de Alimentação
    sub_alimentacao = ["Padarias", "Restaurantes & Delivery", "Supermercados & Hortifrúti"]
    valores_alim = [45.90, 197.00, 680.75]

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    bars = ax2.barh(sub_alimentacao, valores_alim, color=["#F8CBAD", "#ED7D31", "#2F5597"])
    ax2.set_xlabel("Gasto Total (R$)", fontsize=11, weight="bold")
    ax2.set_title(f"Raio-X de Gastos com Alimentação (Total: R$ {sum(valores_alim):,.2f})", fontsize=12, weight="bold")

    for bar in bars:
        width = bar.get_width()
        ax2.text(width + 10, bar.get_y() + bar.get_height()/2, f"R$ {width:,.2f}", va="center", ha="left", fontsize=9.5, weight="bold")

    ax2.set_xlim(0, max(valores_alim) * 1.25)
    plt.tight_layout()
    plt.savefig("saida/grafico_alimentacao_detalhado.png", dpi=300, bbox_inches="tight")
    print("Grafico 'saida/grafico_alimentacao_detalhado.png' gerado com sucesso!")

if __name__ == "__main__":
    gerar_graficos_demonstracao()
