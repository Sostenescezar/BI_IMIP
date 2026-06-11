# SAD IMIP — Scripts de Mineração de Dados
## Marketing Digital | Hospital IMIP, Recife-PE

---

## Como usar

### 1. Instalar dependências
```
pip install pandas numpy scikit-learn openpyxl xlsxwriter
```

### 2. Preparar os dados
Coloque seus arquivos CSV ou XLSX dentro da pasta `./dados/` com os nomes abaixo.

### 3. Executar
```
python main_sad_imip.py
```

---

## Estrutura esperada dos arquivos

### `pacientes.csv`
| Coluna                | Exemplo           | Obrigatório |
|-----------------------|-------------------|-------------|
| id_paciente           | PAC001            | Sim         |
| data_nascimento       | 15/03/1985        | Sim         |
| genero                | F ou Feminino     | Não         |
| data_atendimento      | 10/06/2025        | Sim (RFM)   |
| valor_procedimento    | 250.00            | Não (RFM)   |
| origem                | Google / Indicação| Não         |

### `medicos.csv`
| Coluna                  | Exemplo        | Obrigatório |
|-------------------------|----------------|-------------|
| id_medico               | MED001         | Sim         |
| categoria               | Residente / Staff | Sim      |
| especialidade           | Cardiologia    | Não         |
| seguidores_linkedin     | 1200           | Não         |
| publicacoes_mes         | 4              | Não         |
| interacoes_posts        | 320            | Não         |
| participacoes_evento    | 2              | Não         |

### `campanhas.csv`
| Coluna          | Exemplo          | Obrigatório |
|-----------------|------------------|-------------|
| canal           | Meta Ads / Google| Sim         |
| publico_alvo    | Pacientes        | Sim         |
| data_inicio     | 01/05/2025       | Não         |
| impressoes      | 50000            | Sim         |
| cliques         | 1500             | Sim         |
| leads           | 300              | Não         |
| conversoes      | 80               | Sim         |
| custo_total     | 2000.00          | Sim         |
| receita_gerada  | 8500.00          | Não         |

### `engajamento_redes.csv`
| Coluna              | Exemplo           | Obrigatório |
|---------------------|-------------------|-------------|
| rede_social         | Instagram         | Sim         |
| data_hora_post      | 2025-05-10 14:00  | Sim         |
| tipo_conteudo       | Vídeo / Imagem    | Não         |
| publico_alvo_post   | Pacientes         | Não         |
| curtidas            | 480               | Sim         |
| comentarios         | 32                | Sim         |
| compartilhamentos   | 15                | Sim         |
| alcance             | 12000             | Sim         |
| impressoes_post     | 18000             | Não         |
| seguidores_pagina   | 45000             | Não         |
| descricao_post      | Texto do post...  | Não         |

### `investidores.csv`
| Coluna                          | Exemplo     | Obrigatório |
|---------------------------------|-------------|-------------|
| id_investidor                   | INV001      | Sim         |
| tipo_investidor                 | Institucional| Não        |
| valor_investido                 | 500000.00   | Sim         |
| retorno_esperado                | 750000.00   | Não         |
| anos_relacionamento             | 5           | Não         |
| nivel_engajamento_comunicacao   | Alto        | Não         |

---

## O que cada script faz

| Script | O que gera |
|--------|-----------|
| `01_etl_carga_dados.py`     | Lê, limpa e normaliza todos os CSVs → salva no banco `imip_sad.db` |
| `02_segmentacao_publicos.py`| RFM de pacientes, clusters de médicos, tiers de investidores |
| `03_engajamento_redes.py`   | Métricas por rede, melhores horários, tipos de conteúdo, top posts |
| `04_roi_campanhas.py`       | ROAS, CPA, funil de conversão, recomendações de verba |
| `05_relatorio_excel.py`     | Excel com 10 abas + gráfico + resumo executivo |

---

## Públicos cobertos

- **Pacientes** — Segmentação RFM (Fiel, Em Risco, Inativo, Alto Valor, Potencial)
- **Médicos Residentes** — Clustering de perfil digital e engajamento
- **Médicos Staff** — Idem, com distinção de categoria
- **Investidores** — Tiers Estratégico / Prioritário / Ativo / Potencial

---

## Saídas geradas

```
./imip_sad.db              ← banco SQLite com todas as tabelas mineradas
./relatorios/
    SAD_IMIP_Marketing_YYYYMMDD.xlsx
./logs/
    etl_log.txt
```
