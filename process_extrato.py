# -*- coding: utf-8 -*-
"""
FinanceAgent - Motor de Domínio, Categorização, Parsing Estrito e Validação Contábil
Arquitetura: Domain Layer Centralizada (Fail-Fast, Anti-Silent-Coercion, Idempotência)
"""

import os
import re
import sys
import hashlib
from datetime import date, datetime
from pathlib import Path
import pandas as pd

# ==============================================================================
# 1. DICIONÁRIOS CANÔNICOS DE CATEGORIAS E REGRAS DE NEGÓCIO
# ==============================================================================
REGRAS_CATEGORIAS = {
    "Transporte & Mobilidade": [
        r"movida", r"posto", r"combustivel", r"gasolina", r"uber", 
        r"99app", r"estacionamento", r"brasil park", r"ipiranga", r"shell"
    ],
    "Alimentação - Padarias": [
        r"peter p[aã]o", r"celeiro do p[aã]o", r"padaria", 
        r"caf[eé] com baguete", r"cacau show", r"confeitaria"
    ],
    "Alimentação - Supermercados": [
        r"super mini", r"hortifruti", r"carrefour", r"atacadao", 
        r"extra", r"supermercado", r"fiorotti", r"p[aã]o de a[cç][uú]car"
    ],
    "Alimentação - Restaurantes": [
        r"espetinho", r"sorveteria", r"restaurante", r"ifood", 
        r"burger", r"rocon", r"lanchonete", r"pizzaria"
    ],
    "Compras & Varejo": [
        r"mercado livre", r"americanas", r"tiktok shop", 
        r"ponto sports", r"amazon", r"shopee", r"magalu"
    ],
    "Assinaturas & Apps": [
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

TETOS_ORCAMENTARIOS = {
    "Transporte & Mobilidade": 2500.00,
    "Alimentação - Padarias": 150.00,
    "Alimentação - Restaurantes": 200.00,
    "Alimentação - Supermercados": 400.00,
    "Compras & Varejo": 400.00,
    "Assinaturas & Apps": 150.00,
    "Saúde & Farmácia": 200.00,
    "Educação": 200.00,
    "Tarifas Bancárias": 0.00
}

# ==============================================================================
# 2. SANITIZAÇÃO E TRATAMENTO DE STRINGS (ANTI-INJECTION)
# ==============================================================================
def sanitizar_texto(texto: str) -> str:
    """
    Remove caracteres perigosos no início de strings para prevenir Formula Injection (CSV/Excel).
    """
    if texto is None:
        return ""
    t = str(texto).strip()
    while t.startswith(('=', '+', '-', '@', '\t', '\r')):
        t = t[1:].strip()
    return t

# ==============================================================================
# 3. VALIDAÇÃO ESTRITA NA BORDA (POLÍTICA FAIL-FAST / ANTI-CONVERSÃO SILENCIOSA)
# ==============================================================================
def validar_e_formatar_data_estrita(data_raw: str) -> str:
    """
    Valida e converte formatos de datas suportados (YYYYMMDD, DD/MM/YYYY, YYYY-MM-DD) para DD/MM/YYYY.
    Lança ValueError se a data for nula, vazia ou inválida (Sem fallback silencioso).
    """
    if not data_raw:
        raise ValueError("Data ausente ou nula.")
    
    d_str = str(data_raw).strip()
    if not d_str:
        raise ValueError("Data em branco.")

    # Formato OFX puro: YYYYMMDD ou YYYYMMDDHHMMSS
    if re.match(r"^\d{8}", d_str):
        try:
            dt = datetime.strptime(d_str[:8], "%Y%m%d")
            return dt.strftime("%d/%m/%Y")
        except Exception as e:
            raise ValueError(f"Data OFX inválida '{d_str[:8]}': {e}")

    # Formato DD/MM/YYYY
    if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", d_str):
        try:
            dt = datetime.strptime(d_str, "%d/%m/%Y")
            return dt.strftime("%d/%m/%Y")
        except Exception as e:
            raise ValueError(f"Data DD/MM/YYYY inválida '{d_str}': {e}")

    # Formato ISO YYYY-MM-DD
    if re.match(r"^\d{4}-\d{1,2}-\d{1,2}", d_str):
        try:
            dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except Exception as e:
            raise ValueError(f"Data ISO inválida '{d_str[:10]}': {e}")

    raise ValueError(f"Formato de data não reconhecido: '{d_str}'")

def limpar_valor_monetario_estrito(val_raw) -> float:
    """
    Converte valores monetários numéricos ou em string (R$ 1.234,56 ou -150.00).
    Lança ValueError se o valor for inválido, vazio ou não-numérico (Sem coerção para 0.0 silencioso).
    """
    if val_raw is None:
        raise ValueError("Valor financeiro nulo.")

    if isinstance(val_raw, (int, float)):
        v = float(val_raw)
        if pd.isna(v):
            raise ValueError("Valor financeiro NaN/nulo.")
        return v

    s = str(val_raw).strip()
    if not s:
        raise ValueError("Valor financeiro em branco.")

    s = s.replace("R$", "").replace("r$", "").replace(" ", "").strip()

    # Tratamento de padrão brasileiro 1.250,50 vs padrão internacional 1250.50
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        val_float = float(s)
    except ValueError:
        raise ValueError(f"Valor monetário ilegível: '{val_raw}'")

    if pd.isna(val_float):
        raise ValueError("Valor financeiro inválido (NaN).")

    return val_float

# ==============================================================================
# 4. HASHING E IDENTIFICADOR DE IDEMPOTÊNCIA (DEDUPLICAÇÃO)
# ==============================================================================
def gerar_hash_deduplicacao(data: str, origem: str, descricao: str, valor: float, responsavel: str, fitid: str = "") -> str:
    """
    Gera uma chave determinística SHA-256 única para prevenir duplicidades no banco de dados.
    Prioriza o FITID bancário se disponível, ou a assinatura canônica normalizada.
    """
    if fitid and fitid.strip():
        chave_base = f"FITID:{fitid.strip()}"
    else:
        # Assinatura canônica: data_normalizada + origem + descricao_limpa + valor_formatado + responsavel
        chave_base = f"CANONICAL:{data.strip()}|{origem.strip()}|{descricao.strip().upper()}|{valor:.2f}|{responsavel.strip().upper()}"
    
    return hashlib.sha256(chave_base.encode("utf-8")).hexdigest()

def calcular_checksum_arquivo(caminho: Path) -> str:
    """
    Calcula o hash SHA-256 do arquivo físico para controle de auditoria e lotes.
    """
    sha = hashlib.sha256()
    with open(caminho, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()

# ==============================================================================
# 5. PARSERS ESTRITOS (OFX E CSV COM RELATÓRIO DE CONSISTÊNCIA)
# ==============================================================================
def parse_ofx_estrito(conteudo_texto: str, nome_origem: str = "Extrato OFX") -> dict:
    """
    Processa arquivo OFX com validação estrita.
    Retorna dicionário com transações válidas e lista de rejeições estruturadas.
    """
    transacoes_validas = []
    linhas_rejeitadas = []

    blocos = re.findall(
        r'<STMTTRN>(.*?)(?:</STMTTRN>|(?=<STMTTRN>)|(?=</BANKTRANLIST>)|$)', 
        conteudo_texto, 
        re.DOTALL | re.IGNORECASE
    )

    total_blocos = len(blocos)

    for idx, bloco in enumerate(blocos, start=1):
        identificador_bloco = f"STMTTRN #{idx}"
        
        # 1. Extração do FITID
        m_fitid = re.search(r'<FITID>([^\r\n<]+)', bloco, re.IGNORECASE)
        fitid = m_fitid.group(1).strip() if m_fitid else ""

        # 2. Extração e Validação Estrita da Data
        m_dt = re.search(r'<DTPOSTED>([^\r\n<]+)', bloco, re.IGNORECASE)
        if not m_dt:
            linhas_rejeitadas.append({
                "bloco": identificador_bloco,
                "fitid": fitid,
                "motivo": "Tag <DTPOSTED> ausente no extrato OFX."
            })
            continue

        try:
            data_formatada = validar_e_formatar_data_estrita(m_dt.group(1).strip())
        except ValueError as err_dt:
            linhas_rejeitadas.append({
                "bloco": identificador_bloco,
                "fitid": fitid,
                "motivo": f"Data inválida: {err_dt}"
            })
            continue

        # 3. Extração e Validação Estrita do Valor Monetário
        m_val = re.search(r'<TRNAMT>([^\r\n<]+)', bloco, re.IGNORECASE)
        if not m_val:
            linhas_rejeitadas.append({
                "bloco": identificador_bloco,
                "fitid": fitid,
                "motivo": "Tag <TRNAMT> ausente no extrato OFX."
            })
            continue

        try:
            valor_num = limpar_valor_monetario_estrito(m_val.group(1).strip())
        except ValueError as err_val:
            linhas_rejeitadas.append({
                "bloco": identificador_bloco,
                "fitid": fitid,
                "motivo": f"Valor monetário corrompido: {err_val}"
            })
            continue

        # 4. Extração da Descrição
        m_memo = re.search(r'<MEMO>([^\r\n<]+)', bloco, re.IGNORECASE)
        m_name = re.search(r'<NAME>([^\r\n<]+)', bloco, re.IGNORECASE)
        memo = m_memo.group(1).strip() if m_memo else ""
        name = m_name.group(1).strip() if m_name else ""
        descricao_bruta = memo or name or "Lançamento OFX"
        descricao = sanitizar_texto(descricao_bruta)

        # 5. Tipo OFX
        m_type = re.search(r'<TRNTYPE>([^\r\n<]+)', bloco, re.IGNORECASE)
        trntype = m_type.group(1).strip().upper() if m_type else "OTHER"

        transacoes_validas.append({
            "data": data_formatada,
            "origem": nome_origem,
            "descricao": descricao,
            "valor": valor_num,
            "tipo_ofx": trntype,
            "fitid": fitid
        })

    return {
        "total_encontradas": total_blocos,
        "total_validas": len(transacoes_validas),
        "total_rejeitadas": len(linhas_rejeitadas),
        "transacoes": transacoes_validas,
        "rejeitadas": linhas_rejeitadas
    }

def parse_csv_estrito(caminho_csv: Path, titular_padrao: str = "Usuário Titular", nome_origem: str = "Extrato CSV") -> dict:
    """
    Processa arquivo CSV com detecção de cabeçalho e validação estrita por linha.
    """
    transacoes_validas = []
    linhas_rejeitadas = []

    try:
        df = pd.read_csv(caminho_csv)
    except Exception as e:
        return {
            "total_encontradas": 0,
            "total_validas": 0,
            "total_rejeitadas": 1,
            "transacoes": [],
            "rejeitadas": [{"linha": 0, "motivo": f"Falha estrutural ao ler CSV: {e}"}]
        }

    total_linhas = len(df)
    col_desc = next((c for c in df.columns if c.lower() in ["descricao", "estabelecimento", "historico", "lancamento", "memo", "description"]), None)
    col_val = next((c for c in df.columns if c.lower() in ["valor_brl", "valor", "montante", "quantia", "amount", "value"]), None)
    col_data = next((c for c in df.columns if c.lower() in ["data", "dt", "date", "data_lancamento"]), None)
    col_resp = next((c for c in df.columns if c.lower() in ["responsavel", "titular", "owner"]), None)
    col_fitid = next((c for c in df.columns if c.lower() in ["fitid", "id", "identificador", "uuid"]), None)

    if not col_desc or not col_val:
        return {
            "total_encontradas": total_linhas,
            "total_validas": 0,
            "total_rejeitadas": total_linhas,
            "transacoes": [],
            "rejeitadas": [{"linha": 0, "motivo": f"CSV inválido: colunas obrigatórias de descrição/valor ausentes. Colunas detectadas: {list(df.columns)}"}]
        }

    for idx, row in df.iterrows():
        num_linha = idx + 2  # Considera cabeçalho linha 1
        
        # 1. Validação de Descrição
        desc_raw = row.get(col_desc)
        if pd.isna(desc_raw) or not str(desc_raw).strip():
            linhas_rejeitadas.append({
                "linha": num_linha,
                "motivo": "Descrição em branco ou nula."
            })
            continue
        descricao = sanitizar_texto(str(desc_raw))

        # 2. Validação Estrita de Valor
        val_raw = row.get(col_val)
        try:
            valor_num = limpar_valor_monetario_estrito(val_raw)
        except ValueError as err_v:
            linhas_rejeitadas.append({
                "linha": num_linha,
                "descricao": descricao,
                "motivo": f"Valor inválido: {err_v}"
            })
            continue

        # 3. Validação Estrita de Data
        data_raw = row.get(col_data) if col_data else None
        if data_raw is None or pd.isna(data_raw):
            linhas_rejeitadas.append({
                "linha": num_linha,
                "descricao": descricao,
                "motivo": "Coluna de data ausente ou nula."
            })
            continue

        try:
            data_formatada = validar_e_formatar_data_estrita(str(data_raw))
        except ValueError as err_d:
            linhas_rejeitadas.append({
                "linha": num_linha,
                "descricao": descricao,
                "motivo": f"Data inválida: {err_d}"
            })
            continue

        # 4. Titular e FITID
        resp_val = str(row[col_resp]).strip() if col_resp and not pd.isna(row[col_resp]) else titular_padrao
        fitid_val = str(row[col_fitid]).strip() if col_fitid and not pd.isna(row[col_fitid]) else ""

        transacoes_validas.append({
            "data": data_formatada,
            "origem": nome_origem,
            "descricao": descricao,
            "valor": valor_num,
            "responsavel": resp_val,
            "fitid": fitid_val
        })

    return {
        "total_encontradas": total_linhas,
        "total_validas": len(transacoes_validas),
        "total_rejeitadas": len(linhas_rejeitadas),
        "transacoes": transacoes_validas,
        "rejeitadas": linhas_rejeitadas
    }

# ==============================================================================
# 6. CLASSIFICAÇÃO HEURÍSTICA DE TRANSAÇÕES (REGEX UNIFICADO)
# ==============================================================================
def classificar_transacao(descricao: str, valor: float) -> tuple:
    """
    Classifica a transação por regex unificado e determina sua categoria e tipo contábil.
    Retorna tupla: (Categoria, Tipo_Movimentacao).
    """
    desc = str(descricao).lower()

    # 1. Regra de Fluxo Interno (Mesma Titularidade)
    if "transferencia mesma titularidade" in desc or "fluxo interno" in desc or "aporte proprio" in desc:
        return "Fluxo Interno", "Neutro"

    # 2. Rendimentos Financeiros / Saldo CDI
    if "rendimento" in desc or "cdi" in desc:
        return "Receitas Externas", "Receita"

    # 3. Varredura por Regras Regex
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

# ==============================================================================
# 7. ANÁLISE DE TETOS ORÇAMENTÁRIOS E ALERTAS
# ==============================================================================
def verificar_alertas_orcamentarios(df: pd.DataFrame):
    """
    Verifica e exibe alertas contábeis com base nos tetos orçamentários cadastrados.
    """
    print("\n-------------------------------------------------------------")
    print("           ANALISE DE METAS E ALERTAS ORCAMENTARIOS          ")
    print("-------------------------------------------------------------")
    
    col_cat = "categoria" if "categoria" in df.columns else ("Categoria_Classificada" if "Categoria_Classificada" in df.columns else "Categoria")
    col_val = "valor_brl" if "valor_brl" in df.columns else ("Valor_BRL" if "Valor_BRL" in df.columns else "Valor (R$)")
    col_tipo = "tipo_movimentacao" if "tipo_movimentacao" in df.columns else ("Tipo_Movimentacao" if "Tipo_Movimentacao" in df.columns else "Tipo Movimentação")

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
