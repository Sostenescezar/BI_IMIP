"""
SAD IMIP - Marketing Digital
Script 02: Segmentação e Perfilagem dos Públicos
Técnicas: RFM (pacientes), Clustering K-Means (médicos/investidores)

Depende de: imip_sad.db (gerado pelo script 01)
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings("ignore")

DB_PATH = "./imip_sad.db"

def conectar():
    return sqlite3.connect(DB_PATH)

# ═══════════════════════════════════════════════
# BLOCO 1 — SEGMENTAÇÃO RFM DE PACIENTES
# Recência (última consulta), Frequência (nº consultas),
# Monetary (valor gerado ou procedimentos)
# ═══════════════════════════════════════════════
def segmentar_pacientes_rfm():
    conn = conectar()

    # Adapte os nomes das colunas conforme sua planilha real
    query = """
        SELECT
            id_paciente,
            MAX(data_atendimento)            AS ultima_consulta,
            COUNT(*)                         AS frequencia,
            SUM(CAST(valor_procedimento AS REAL)) AS monetario
        FROM pacientes
        WHERE data_atendimento IS NOT NULL
        GROUP BY id_paciente
    """
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"[RFM] Erro na query: {e}. Verifique as colunas da tabela 'pacientes'.")
        conn.close()
        return pd.DataFrame()
    conn.close()

    if df.empty:
        print("[RFM] Sem dados de pacientes para segmentar.")
        return df

    # Calcula recência em dias
    df["ultima_consulta"] = pd.to_datetime(df["ultima_consulta"], errors="coerce")
    hoje = pd.Timestamp.today()
    df["recencia_dias"] = (hoje - df["ultima_consulta"]).dt.days

    # Scores de 1 a 5 por quintil (5 = melhor)
    df["score_R"] = pd.qcut(df["recencia_dias"],  q=5, labels=[5,4,3,2,1], duplicates="drop")
    df["score_F"] = pd.qcut(df["frequencia"],      q=5, labels=[1,2,3,4,5], duplicates="drop")
    df["score_M"] = pd.qcut(df["monetario"].fillna(0), q=5, labels=[1,2,3,4,5], duplicates="drop")

    df["rfm_total"] = (
        df["score_R"].astype(int) +
        df["score_F"].astype(int) +
        df["score_M"].astype(int)
    )

    # Segmentos de marketing
    def classificar_rfm(row):
        r, f, m = int(row["score_R"]), int(row["score_F"]), int(row["score_M"])
        if r >= 4 and f >= 4:
            return "Paciente Fiel"
        elif r >= 4 and f <= 2:
            return "Retorno Recente"
        elif r <= 2 and f >= 4:
            return "Em Risco"
        elif r <= 2 and f <= 2:
            return "Inativo"
        elif m >= 4:
            return "Alto Valor"
        else:
            return "Potencial"

    df["segmento_rfm"] = df.apply(classificar_rfm, axis=1)

    print("\n[RFM] Distribuição dos segmentos de pacientes:")
    print(df["segmento_rfm"].value_counts().to_string())

    # Salva resultado
    conn = conectar()
    df.to_sql("pacientes_rfm", conn, if_exists="replace", index=False)
    conn.close()
    print("[RFM] Tabela 'pacientes_rfm' salva no banco.")
    return df


# ═══════════════════════════════════════════════
# BLOCO 2 — CLUSTERING DE MÉDICOS
# Agrupa por perfil de engajamento digital
# (interações, seguidores, publicações)
# ═══════════════════════════════════════════════
def clusterizar_medicos(n_clusters=3):
    conn = conectar()
    query = """
        SELECT
            id_medico,
            tipo_medico,
            especialidade,
            CAST(seguidores_linkedin AS REAL)    AS seguidores_linkedin,
            CAST(publicacoes_mes AS REAL)         AS publicacoes_mes,
            CAST(interacoes_posts AS REAL)        AS interacoes_posts,
            CAST(participacoes_evento AS REAL)    AS participacoes_evento
        FROM medicos
    """
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"[CLUSTER MÉDICOS] Erro: {e}")
        conn.close()
        return pd.DataFrame()
    conn.close()

    features = ["seguidores_linkedin", "publicacoes_mes", "interacoes_posts", "participacoes_evento"]
    df_feat = df[features].fillna(0)

    if len(df_feat) < n_clusters:
        print("[CLUSTER MÉDICOS] Dados insuficientes para clustering.")
        return df

    # Normalização
    scaler = StandardScaler()
    X = scaler.fit_transform(df_feat)

    # Escolha automática do melhor K (2–6)
    melhor_k, melhor_score = n_clusters, -1
    for k in range(2, min(7, len(df_feat))):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        s = silhouette_score(X, labels)
        if s > melhor_score:
            melhor_score, melhor_k = s, k

    km_final = KMeans(n_clusters=melhor_k, random_state=42, n_init=10)
    df["cluster_medico"] = km_final.fit_predict(X)

    # Nomeia clusters por perfil de engajamento médio
    perfil = df.groupby("cluster_medico")[features].mean()
    perfil["engajamento_geral"] = perfil.mean(axis=1)
    ordem = perfil["engajamento_geral"].rank(ascending=False).astype(int)
    nomes = {idx: f"Perfil {n}" for idx, n in ordem.items()}
    df["perfil_digital_medico"] = df["cluster_medico"].map(nomes)

    print(f"\n[CLUSTER MÉDICOS] Melhor K={melhor_k} (silhouette={melhor_score:.3f})")
    print(df.groupby("perfil_digital_medico")["tipo_medico"].value_counts().to_string())

    conn = conectar()
    df.to_sql("medicos_clusters", conn, if_exists="replace", index=False)
    conn.close()
    print("[CLUSTER MÉDICOS] Tabela 'medicos_clusters' salva no banco.")
    return df


# ═══════════════════════════════════════════════
# BLOCO 3 — SEGMENTAÇÃO DE INVESTIDORES
# Classifica por potencial de comunicação/ROI
# ═══════════════════════════════════════════════
def segmentar_investidores():
    conn = conectar()
    query = """
        SELECT
            id_investidor,
            tipo_investidor,
            CAST(valor_investido AS REAL)     AS valor_investido,
            CAST(retorno_esperado AS REAL)     AS retorno_esperado,
            CAST(anos_relacionamento AS REAL)  AS anos_relacionamento,
            nivel_engajamento_comunicacao
        FROM investidores
    """
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"[INVESTIDORES] Erro: {e}")
        conn.close()
        return pd.DataFrame()
    conn.close()

    if df.empty:
        return df

    # Score de prioridade de comunicação
    df["score_valor"]   = pd.qcut(df["valor_investido"].fillna(0),  q=3, labels=[1,2,3], duplicates="drop").astype(int)
    df["score_retorno"] = pd.qcut(df["retorno_esperado"].fillna(0), q=3, labels=[1,2,3], duplicates="drop").astype(int)
    df["score_tempo"]   = pd.qcut(df["anos_relacionamento"].fillna(0), q=3, labels=[1,2,3], duplicates="drop").astype(int)
    df["score_total"]   = df["score_valor"] + df["score_retorno"] + df["score_tempo"]

    def tier_investidor(score):
        if score >= 8: return "Estratégico"
        elif score >= 6: return "Prioritário"
        elif score >= 4: return "Ativo"
        else: return "Potencial"

    df["tier_comunicacao"] = df["score_total"].apply(tier_investidor)

    print("\n[INVESTIDORES] Distribuição por tier de comunicação:")
    print(df["tier_comunicacao"].value_counts().to_string())

    conn = conectar()
    df.to_sql("investidores_segmentados", conn, if_exists="replace", index=False)
    conn.close()
    print("[INVESTIDORES] Tabela 'investidores_segmentados' salva no banco.")
    return df


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=== SEGMENTAÇÃO DE PÚBLICOS - SAD IMIP ===\n")
    df_pac  = segmentar_pacientes_rfm()
    df_med  = clusterizar_medicos()
    df_inv  = segmentar_investidores()
    print("\n=== SEGMENTAÇÃO CONCLUÍDA ===")
