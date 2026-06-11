"""
SAD IMIP - Marketing Digital
Script 01: ETL - Carga e Limpeza de Dados
Público-alvo: Pacientes, Médicos Residentes, Médicos Staff, Investidores

Fontes esperadas (CSV/XLSX):
  - pacientes.csv
  - medicos.csv
  - campanhas.csv
  - engajamento_redes.csv
  - investidores.csv
"""

import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────
PASTA_DADOS   = "./dados/"          # pasta com os arquivos CSV/XLSX
DB_PATH       = "./imip_sad.db"     # banco SQLite local gerado pelo script
LOG_PATH      = "./logs/etl_log.txt"

os.makedirs("./logs", exist_ok=True)

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}"
    print(linha)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

# ─────────────────────────────────────────────
# FUNÇÕES DE LEITURA FLEXÍVEL (CSV ou XLSX)
# ─────────────────────────────────────────────
def ler_arquivo(nome_base):
    """Tenta ler .xlsx primeiro, depois .csv."""
    for ext in [".xlsx", ".csv"]:
        caminho = os.path.join(PASTA_DADOS, nome_base + ext)
        if os.path.exists(caminho):
            log(f"Lendo: {caminho}")
            if ext == ".xlsx":
                return pd.read_excel(caminho, dtype=str)
            else:
                return pd.read_csv(caminho, dtype=str, encoding="utf-8-sig", sep=None, engine="python")
    log(f"AVISO: arquivo '{nome_base}' não encontrado. Gerando DataFrame vazio.")
    return pd.DataFrame()

# ─────────────────────────────────────────────
# LIMPEZA GENÉRICA
# ─────────────────────────────────────────────
def limpar(df, nome):
    if df.empty:
        return df
    # normaliza nomes de colunas
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    antes = len(df)
    df = df.drop_duplicates()
    df = df.replace(r'^\s*$', np.nan, regex=True)   # strings vazias → NaN
    depois = len(df)
    log(f"[{nome}] Linhas: {antes} → {depois} após limpeza ({antes - depois} duplicatas removidas)")
    return df

# ─────────────────────────────────────────────
# LIMPEZA ESPECÍFICA POR PÚBLICO
# ─────────────────────────────────────────────
def processar_pacientes(df):
    df = limpar(df, "pacientes")
    if df.empty:
        return df
    # padroniza faixa etária
    if "data_nascimento" in df.columns:
        df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce", dayfirst=True)
        hoje = pd.Timestamp.today()
        df["idade"] = ((hoje - df["data_nascimento"]).dt.days / 365.25).astype("Int64")
        df["faixa_etaria"] = pd.cut(
            df["idade"],
            bins=[0, 12, 17, 29, 59, 120],
            labels=["Criança", "Adolescente", "Adulto jovem", "Adulto", "Idoso"]
        )
    # normaliza gênero
    if "genero" in df.columns:
        df["genero"] = df["genero"].str.strip().str.upper().map(
            {"M": "Masculino", "F": "Feminino", "MASCULINO": "Masculino",
             "FEMININO": "Feminino", "O": "Outro", "OUTRO": "Outro"}
        )
    # categoriza origem do lead
    if "origem" in df.columns:
        df["origem"] = df["origem"].str.strip().str.title()
    return df

def processar_medicos(df):
    df = limpar(df, "medicos")
    if df.empty:
        return df
    # classifica tipo de médico
    if "categoria" in df.columns:
        cat_map = {
            "RESIDENTE": "Residente", "R1": "Residente", "R2": "Residente", "R3": "Residente",
            "STAFF": "Staff", "EFETIVO": "Staff", "CONTRATADO": "Staff",
            "VISITING": "Visiting", "EXTERNO": "Visiting"
        }
        df["tipo_medico"] = df["categoria"].str.upper().map(cat_map).fillna("Outros")
    # normaliza especialidade
    if "especialidade" in df.columns:
        df["especialidade"] = df["especialidade"].str.strip().str.title()
    return df

def processar_campanhas(df):
    df = limpar(df, "campanhas")
    if df.empty:
        return df
    cols_num = ["impressoes", "cliques", "conversoes", "custo_total", "receita_gerada"]
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")
    # CTR e CPC calculados
    if {"impressoes", "cliques"}.issubset(df.columns):
        df["ctr"] = (df["cliques"] / df["impressoes"]).round(4)
    if {"custo_total", "cliques"}.issubset(df.columns):
        df["cpc"] = (df["custo_total"] / df["cliques"]).round(2)
    if {"custo_total", "conversoes"}.issubset(df.columns):
        df["cpa"] = (df["custo_total"] / df["conversoes"]).round(2)
    # classifica público-alvo da campanha
    if "publico_alvo" in df.columns:
        df["publico_alvo"] = df["publico_alvo"].str.strip().str.title()
    return df

def processar_engajamento(df):
    df = limpar(df, "engajamento_redes")
    if df.empty:
        return df
    cols_num = ["curtidas", "comentarios", "compartilhamentos", "alcance", "impressoes_post"]
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")
    # taxa de engajamento
    if {"curtidas", "comentarios", "compartilhamentos", "alcance"}.issubset(df.columns):
        interacoes = df["curtidas"] + df["comentarios"] + df["compartilhamentos"]
        df["taxa_engajamento"] = (interacoes / df["alcance"]).round(4)
    # normaliza rede social
    if "rede_social" in df.columns:
        df["rede_social"] = df["rede_social"].str.strip().str.title()
    return df

def processar_investidores(df):
    df = limpar(df, "investidores")
    if df.empty:
        return df
    if "tipo_investidor" in df.columns:
        df["tipo_investidor"] = df["tipo_investidor"].str.strip().str.title()
    cols_num = ["valor_investido", "retorno_esperado"]
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")
    return df

# ─────────────────────────────────────────────
# CARGA NO BANCO SQLite
# ─────────────────────────────────────────────
def salvar_sqlite(dfs: dict):
    conn = sqlite3.connect(DB_PATH)
    for tabela, df in dfs.items():
        if not df.empty:
            df.to_sql(tabela, conn, if_exists="replace", index=False)
            log(f"Tabela '{tabela}' salva no banco com {len(df)} registros.")
    conn.close()
    log(f"Banco SQLite gerado em: {DB_PATH}")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    log("=== INÍCIO DO ETL - SAD IMIP ===")

    dados = {
        "pacientes":         processar_pacientes(ler_arquivo("pacientes")),
        "medicos":           processar_medicos(ler_arquivo("medicos")),
        "campanhas":         processar_campanhas(ler_arquivo("campanhas")),
        "engajamento_redes": processar_engajamento(ler_arquivo("engajamento_redes")),
        "investidores":      processar_investidores(ler_arquivo("investidores")),
    }

    salvar_sqlite(dados)
    log("=== ETL CONCLUÍDO COM SUCESSO ===")
