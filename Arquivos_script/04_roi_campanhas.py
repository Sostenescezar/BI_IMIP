"""
SAD IMIP - Marketing Digital
Script 04: ROI e Performance de Campanhas por Público
Métricas: ROAS, CPA, funil de conversão, custo por público,
          análise de atribuição e recomendações de investimento

Depende de: imip_sad.db (gerado pelo script 01)
"""

import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "./imip_sad.db"

def conectar():
    return sqlite3.connect(DB_PATH)

# ═══════════════════════════════════════════════
# BLOCO 1 — PERFORMANCE GERAL DAS CAMPANHAS
# ═══════════════════════════════════════════════
def performance_geral():
    conn = conectar()
    query = """
        SELECT
            canal,
            publico_alvo,
            COUNT(*)                                     AS total_campanhas,
            SUM(impressoes)                              AS total_impressoes,
            SUM(cliques)                                 AS total_cliques,
            SUM(conversoes)                              AS total_conversoes,
            ROUND(SUM(custo_total), 2)                   AS investimento_total,
            ROUND(SUM(receita_gerada), 2)                AS receita_total,
            ROUND(AVG(ctr) * 100, 2)                     AS ctr_medio_pct,
            ROUND(AVG(cpa), 2)                           AS cpa_medio,
            ROUND(SUM(receita_gerada) / NULLIF(SUM(custo_total), 0), 2) AS roas
        FROM campanhas
        GROUP BY canal, publico_alvo
        ORDER BY roas DESC
    """
    try:
        df = pd.read_sql(query, conn)
        # Classifica eficiência da campanha
        df["eficiencia"] = pd.cut(
            df["roas"],
            bins=[-np.inf, 1, 2, 4, np.inf],
            labels=["Deficitária", "Abaixo do alvo", "Adequada", "Alto desempenho"]
        )
        print("\n[PERFORMANCE] Campanhas por canal e público-alvo:")
        print(df.to_string(index=False))
        df.to_sql("performance_campanhas", conn, if_exists="replace", index=False)
    except Exception as e:
        print(f"[PERFORMANCE] Erro: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


# ═══════════════════════════════════════════════
# BLOCO 2 — FUNIL DE CONVERSÃO POR PÚBLICO
# Mostra onde cada público abandona o funil
# ═══════════════════════════════════════════════
def funil_conversao():
    conn = conectar()
    query = """
        SELECT
            publico_alvo,
            SUM(impressoes)    AS impressoes,
            SUM(cliques)       AS cliques,
            SUM(leads)         AS leads,
            SUM(conversoes)    AS conversoes
        FROM campanhas
        WHERE publico_alvo IS NOT NULL
        GROUP BY publico_alvo
    """
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"[FUNIL] Erro: {e}")
        conn.close()
        return pd.DataFrame()
    conn.close()

    if df.empty:
        return df

    # Taxas de passagem em cada etapa do funil
    df["tx_clique"]    = (df["cliques"]    / df["impressoes"].replace(0, np.nan) * 100).round(2)
    df["tx_lead"]      = (df["leads"]      / df["cliques"].replace(0, np.nan)    * 100).round(2)
    df["tx_conversao"] = (df["conversoes"] / df["leads"].replace(0, np.nan)      * 100).round(2)
    df["tx_geral"]     = (df["conversoes"] / df["impressoes"].replace(0, np.nan) * 100).round(4)

    # Identifica gargalo principal de cada público
    def gargalo(row):
        etapas = {
            "Impressão → Clique": row["tx_clique"],
            "Clique → Lead":      row["tx_lead"],
            "Lead → Conversão":   row["tx_conversao"]
        }
        return min(etapas, key=etapas.get) if not pd.isna(list(etapas.values())[0]) else "N/D"

    df["gargalo_funil"] = df.apply(gargalo, axis=1)

    print("\n[FUNIL] Funil de conversão por público-alvo:")
    cols = ["publico_alvo", "impressoes", "cliques", "leads", "conversoes",
            "tx_clique", "tx_lead", "tx_conversao", "gargalo_funil"]
    print(df[[c for c in cols if c in df.columns]].to_string(index=False))

    conn = conectar()
    df.to_sql("funil_conversao", conn, if_exists="replace", index=False)
    conn.close()
    return df


# ═══════════════════════════════════════════════
# BLOCO 3 — ROI POR PÚBLICO-ALVO E CANAL
# Com recomendação de redistribuição de verba
# ═══════════════════════════════════════════════
def roi_por_publico_canal():
    conn = conectar()
    query = """
        SELECT
            publico_alvo,
            canal,
            ROUND(SUM(custo_total), 2)                                 AS custo,
            ROUND(SUM(receita_gerada), 2)                              AS receita,
            ROUND((SUM(receita_gerada) - SUM(custo_total))
                  / NULLIF(SUM(custo_total), 0) * 100, 1)              AS roi_pct,
            ROUND(SUM(custo_total) / NULLIF(SUM(conversoes), 0), 2)    AS cpa,
            SUM(conversoes)                                            AS conversoes
        FROM campanhas
        GROUP BY publico_alvo, canal
        ORDER BY roi_pct DESC
    """
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"[ROI] Erro: {e}")
        conn.close()
        return pd.DataFrame()
    conn.close()

    if df.empty:
        return df

    # Recomendação automática de realocação de verba
    def recomendar(roi):
        if pd.isna(roi): return "Sem dados"
        if roi > 300:    return "✦ Aumentar investimento"
        elif roi > 100:  return "→ Manter"
        elif roi > 0:    return "↓ Otimizar criativos"
        else:            return "✕ Revisar ou pausar"

    df["recomendacao"] = df["roi_pct"].apply(recomendar)

    print("\n[ROI] ROI por público e canal com recomendações:")
    print(df.to_string(index=False))

    # Resumo por público (soma todos os canais)
    resumo = (
        df.groupby("publico_alvo")
        .apply(lambda x: pd.Series({
            "custo_total":    x["custo"].sum(),
            "receita_total":  x["receita"].sum(),
            "roi_medio_pct":  ((x["receita"].sum() - x["custo"].sum()) / x["custo"].sum() * 100
                               if x["custo"].sum() > 0 else np.nan),
            "conversoes_total": x["conversoes"].sum()
        }))
        .reset_index()
    )
    print("\n[ROI] Resumo de ROI por público-alvo:")
    print(resumo.round(1).to_string(index=False))

    conn = conectar()
    df.to_sql("roi_por_publico_canal",    conn, if_exists="replace", index=False)
    resumo.to_sql("roi_resumo_publico",   conn, if_exists="replace", index=False)
    conn.close()
    return df


# ═══════════════════════════════════════════════
# BLOCO 4 — EVOLUÇÃO MENSAL DO INVESTIMENTO
# ═══════════════════════════════════════════════
def evolucao_mensal():
    conn = conectar()
    query = """
        SELECT
            strftime('%Y-%m', data_inicio) AS mes,
            publico_alvo,
            canal,
            ROUND(SUM(custo_total), 2)           AS investimento,
            ROUND(SUM(receita_gerada), 2)         AS receita,
            SUM(conversoes)                       AS conversoes
        FROM campanhas
        WHERE data_inicio IS NOT NULL
        GROUP BY mes, publico_alvo, canal
        ORDER BY mes, publico_alvo
    """
    try:
        df = pd.read_sql(query, conn)
        # Taxa de crescimento MoM
        df = df.sort_values(["publico_alvo", "canal", "mes"])
        df["investimento_anterior"] = df.groupby(["publico_alvo", "canal"])["investimento"].shift(1)
        df["crescimento_mom_pct"]   = (
            (df["investimento"] - df["investimento_anterior"])
            / df["investimento_anterior"].replace(0, np.nan) * 100
        ).round(1)
        print("\n[EVOLUÇÃO] Investimento mensal por público:")
        print(df.tail(20).to_string(index=False))
        df.to_sql("evolucao_mensal_campanhas", conn, if_exists="replace", index=False)
    except Exception as e:
        print(f"[EVOLUÇÃO] Erro: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


# ═══════════════════════════════════════════════
# BLOCO 5 — COMPARATIVO DE CANAIS (ATRIBUIÇÃO)
# Qual canal mais contribui para conversão final
# ═══════════════════════════════════════════════
def atribuicao_canais():
    conn = conectar()
    query = """
        SELECT
            canal,
            COUNT(*)                                         AS campanhas,
            ROUND(SUM(conversoes), 0)                        AS conversoes,
            ROUND(SUM(custo_total), 2)                       AS custo,
            ROUND(SUM(custo_total) / NULLIF(SUM(conversoes),0), 2) AS cpa,
            ROUND(AVG(ctr) * 100, 2)                         AS ctr_medio_pct,
            ROUND(SUM(receita_gerada) / NULLIF(SUM(custo_total),0), 2) AS roas
        FROM campanhas
        GROUP BY canal
        ORDER BY conversoes DESC
    """
    try:
        df = pd.read_sql(query, conn)
        total_conv = df["conversoes"].sum()
        df["participacao_conversao_pct"] = (df["conversoes"] / total_conv * 100).round(1)
        print("\n[ATRIBUIÇÃO] Contribuição por canal:")
        print(df.to_string(index=False))
        df.to_sql("atribuicao_canais", conn, if_exists="replace", index=False)
    except Exception as e:
        print(f"[ATRIBUIÇÃO] Erro: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=== ROI E PERFORMANCE DE CAMPANHAS - SAD IMIP ===")
    performance_geral()
    funil_conversao()
    roi_por_publico_canal()
    evolucao_mensal()
    atribuicao_canais()
    print("\n=== ANÁLISE DE ROI CONCLUÍDA ===")
