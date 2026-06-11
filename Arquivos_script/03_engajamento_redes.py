"""
SAD IMIP - Marketing Digital
Script 03: Análise de Engajamento em Redes Sociais
Métricas: taxa de engajamento, melhores horários, tipos de conteúdo,
          comparativo por rede e por público-alvo

Depende de: imip_sad.db (gerado pelo script 01)
"""

import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "./imip_sad.db"

def conectar():
    return sqlite3.connect(DB_PATH)

# ═══════════════════════════════════════════════
# BLOCO 1 — MÉTRICAS GERAIS POR REDE SOCIAL
# ═══════════════════════════════════════════════
def metricas_por_rede():
    conn = conectar()
    query = """
        SELECT
            rede_social,
            COUNT(*)                                    AS total_posts,
            ROUND(AVG(taxa_engajamento) * 100, 2)       AS engajamento_medio_pct,
            ROUND(AVG(alcance), 0)                      AS alcance_medio,
            SUM(curtidas)                               AS total_curtidas,
            SUM(comentarios)                            AS total_comentarios,
            SUM(compartilhamentos)                      AS total_compartilhamentos,
            ROUND(AVG(impressoes_post), 0)              AS impressoes_medias
        FROM engajamento_redes
        GROUP BY rede_social
        ORDER BY engajamento_medio_pct DESC
    """
    try:
        df = pd.read_sql(query, conn)
        print("\n[REDE SOCIAL] Métricas gerais por plataforma:")
        print(df.to_string(index=False))
        df.to_sql("metricas_por_rede", conn, if_exists="replace", index=False)
    except Exception as e:
        print(f"[REDE SOCIAL] Erro: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


# ═══════════════════════════════════════════════
# BLOCO 2 — MELHORES HORÁRIOS E DIAS DE POSTAGEM
# ═══════════════════════════════════════════════
def melhores_horarios():
    conn = conectar()
    query = """
        SELECT
            rede_social,
            data_hora_post
        FROM engajamento_redes
        WHERE data_hora_post IS NOT NULL
          AND taxa_engajamento IS NOT NULL
    """
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"[HORÁRIOS] Erro: {e}")
        conn.close()
        return pd.DataFrame()
    conn.close()

    if df.empty:
        return df

    df["data_hora_post"] = pd.to_datetime(df["data_hora_post"], errors="coerce")
    df = df.dropna(subset=["data_hora_post"])

    # Necessita da coluna taxa_engajamento — faz join se necessário
    conn = conectar()
    df_full = pd.read_sql("SELECT * FROM engajamento_redes", conn)
    conn.close()

    df_full["data_hora_post"] = pd.to_datetime(df_full["data_hora_post"], errors="coerce")
    df_full["hora"]            = df_full["data_hora_post"].dt.hour
    df_full["dia_semana"]      = df_full["data_hora_post"].dt.day_name()
    df_full["taxa_engajamento"] = pd.to_numeric(df_full.get("taxa_engajamento", 0), errors="coerce")

    # Média de engajamento por hora
    por_hora = (
        df_full.groupby(["rede_social", "hora"])["taxa_engajamento"]
        .mean()
        .reset_index()
        .rename(columns={"taxa_engajamento": "eng_medio"})
        .sort_values(["rede_social", "eng_medio"], ascending=[True, False])
    )
    print("\n[HORÁRIOS] Top 3 horários por rede social:")
    print(por_hora.groupby("rede_social").head(3).to_string(index=False))

    # Média por dia da semana
    ordem_dias = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    por_dia = (
        df_full.groupby(["rede_social", "dia_semana"])["taxa_engajamento"]
        .mean()
        .reset_index()
        .rename(columns={"taxa_engajamento": "eng_medio"})
    )
    por_dia["dia_semana"] = pd.Categorical(por_dia["dia_semana"], categories=ordem_dias, ordered=True)
    por_dia = por_dia.sort_values(["rede_social", "eng_medio"], ascending=[True, False])
    print("\n[HORÁRIOS] Melhores dias da semana:")
    print(por_dia.groupby("rede_social").head(2).to_string(index=False))

    conn = conectar()
    por_hora.to_sql("melhores_horarios", conn, if_exists="replace", index=False)
    por_dia.to_sql("melhores_dias",      conn, if_exists="replace", index=False)
    conn.close()
    return por_hora


# ═══════════════════════════════════════════════
# BLOCO 3 — ANÁLISE POR TIPO DE CONTEÚDO
# ═══════════════════════════════════════════════
def analise_tipo_conteudo():
    conn = conectar()
    query = """
        SELECT
            tipo_conteudo,
            publico_alvo_post,
            COUNT(*)                                AS total_posts,
            ROUND(AVG(taxa_engajamento) * 100, 2)   AS engajamento_medio_pct,
            ROUND(AVG(alcance), 0)                  AS alcance_medio,
            ROUND(AVG(compartilhamentos), 1)        AS compartilhamentos_medios
        FROM engajamento_redes
        WHERE tipo_conteudo IS NOT NULL
        GROUP BY tipo_conteudo, publico_alvo_post
        ORDER BY engajamento_medio_pct DESC
    """
    try:
        df = pd.read_sql(query, conn)
        print("\n[CONTEÚDO] Performance por tipo de conteúdo e público:")
        print(df.head(15).to_string(index=False))
        df.to_sql("analise_conteudo", conn, if_exists="replace", index=False)
    except Exception as e:
        print(f"[CONTEÚDO] Erro: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


# ═══════════════════════════════════════════════
# BLOCO 4 — RANKING DE POSTS DE MAIOR IMPACTO
# ═══════════════════════════════════════════════
def top_posts(top_n=10):
    conn = conectar()
    query = f"""
        SELECT
            rede_social,
            data_hora_post,
            tipo_conteudo,
            publico_alvo_post,
            alcance,
            curtidas,
            comentarios,
            compartilhamentos,
            ROUND(taxa_engajamento * 100, 2) AS engajamento_pct,
            descricao_post
        FROM engajamento_redes
        ORDER BY taxa_engajamento DESC
        LIMIT {top_n}
    """
    try:
        df = pd.read_sql(query, conn)
        print(f"\n[TOP POSTS] Top {top_n} posts por engajamento:")
        print(df.to_string(index=False))
        df.to_sql("top_posts", conn, if_exists="replace", index=False)
    except Exception as e:
        print(f"[TOP POSTS] Erro: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


# ═══════════════════════════════════════════════
# BLOCO 5 — CRESCIMENTO MENSAL DE SEGUIDORES
# ═══════════════════════════════════════════════
def crescimento_seguidores():
    conn = conectar()
    query = """
        SELECT
            rede_social,
            strftime('%Y-%m', data_hora_post) AS mes,
            MAX(CAST(seguidores_pagina AS REAL)) AS seguidores_fim_mes,
            MIN(CAST(seguidores_pagina AS REAL)) AS seguidores_inicio_mes
        FROM engajamento_redes
        WHERE seguidores_pagina IS NOT NULL
        GROUP BY rede_social, mes
        ORDER BY rede_social, mes
    """
    try:
        df = pd.read_sql(query, conn)
        df["crescimento_abs"]  = df["seguidores_fim_mes"] - df["seguidores_inicio_mes"]
        df["crescimento_pct"]  = (
            (df["crescimento_abs"] / df["seguidores_inicio_mes"].replace(0, np.nan)) * 100
        ).round(2)
        print("\n[CRESCIMENTO] Crescimento mensal de seguidores:")
        print(df.to_string(index=False))
        df.to_sql("crescimento_seguidores", conn, if_exists="replace", index=False)
    except Exception as e:
        print(f"[CRESCIMENTO] Erro: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=== ANÁLISE DE ENGAJAMENTO - SAD IMIP ===")
    metricas_por_rede()
    melhores_horarios()
    analise_tipo_conteudo()
    top_posts(10)
    crescimento_seguidores()
    print("\n=== ANÁLISE CONCLUÍDA ===")
