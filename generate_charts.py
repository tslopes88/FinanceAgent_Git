# -*- coding: utf-8 -*-
"""
FinanceAgent - Gerador de Gráficos e Painel Visual
Gera gráficos em PNG de alta resolução para acompanhamento visual do mês.
"""

import matplotlib.pyplot as plt

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

def gerar_graficos_agosto():
    # 1. Dados de Consumo Operacional Fechados de Agosto/2026
    categorias = [
        "Transporte & Mobilidade",
        "Compras & Varejo",
        "Alimentação Total",
        "Serviços & Terceiros",
        "Assinaturas & Apps",
        "Educação",
        "Saúde & Farmácia",
        "Tarifas Bancárias"
    ]
    valores = [2234.12, 392.62, 318.13, 177.00, 132.05, 130.05, 20.07, 14.90]
    cores = ["#1F4E79", "#2F5597", "#5B9BD5", "#41719C", "#ED7D31", "#A5A5A5", "#FFC000", "#C00000"]

    # Gráfico de Rosca (Donut)
    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw=dict(aspect="equal"))
    wedges, texts, autotexts = ax.pie(
        valores, 
        autopct='%1.1f%%',
        startangle=140,
        pctdistance=0.82,
        colors=cores,
        textprops=dict(color="black", fontsize=9, weight="bold")
    )

    centro = plt.Circle((0, 0), 0.65, fc='white')
    fig.gca().add_artist(centro)

    ax.legend(
        wedges, 
        [f"{c}: R$ {v:,.2f}" for c, v in zip(categorias, valores)],
        title="Centros de Custo (Agosto/2026)",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=10
    )

    plt.title("Distribuição do Consumo Operacional - Agosto/2026\nTotal: R$ 3.418,94", fontsize=13, weight="bold", pad=20)
    plt.tight_layout()
    plt.savefig("grafico_categorias_agosto_2026.png", dpi=300, bbox_inches="tight")
    print("Grafico 'grafico_categorias_agosto_2026.png' gerado com sucesso!")

    # 2. Gráfico de Barras Horizontais: Subdivisão de Alimentação
    sub_alimentacao = ["Padarias & Docerias", "Restaurantes & Lanches", "Supermercados & Hortifruti"]
    valores_alim = [185.51, 80.00, 52.62]

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    bars = ax2.barh(sub_alimentacao, valores_alim, color=["#ED7D31", "#F19E65", "#F8CBAD"])
    ax2.set_xlabel("Gasto Total (R$)", fontsize=11, weight="bold")
    ax2.set_title("Raio-X de Gastos com Alimentação (R$ 318,13)", fontsize=12, weight="bold")

    for bar in bars:
        width = bar.get_width()
        ax2.text(width + 2, bar.get_y() + bar.get_height()/2, f"R$ {width:,.2f}", va="center", ha="left", fontsize=10, weight="bold")

    ax2.set_xlim(0, 220)
    plt.tight_layout()
    plt.savefig("grafico_alimentacao_agosto_2026.png", dpi=300, bbox_inches="tight")
    print("Grafico 'grafico_alimentacao_agosto_2026.png' gerado com sucesso!")

if __name__ == "__main__":
    gerar_graficos_agosto()
