"""
SAD IMIP - Marketing Digital
Script PRINCIPAL — Orquestrador
Executa todos os scripts na sequência correta:
  01 → ETL (carga e limpeza)
  02 → Segmentação dos públicos
  03 → Análise de engajamento
  04 → ROI e performance
  05 → Relatório Excel consolidado

Como usar:
  python main_sad_imip.py

Pré-requisitos:
  pip install pandas numpy scikit-learn openpyxl xlsxwriter

Estrutura de pastas esperada:
  ./dados/
      pacientes.csv (ou .xlsx)
      medicos.csv
      campanhas.csv
      engajamento_redes.csv
      investidores.csv
  ./relatorios/    ← criado automaticamente
  ./logs/          ← criado automaticamente
"""

import subprocess
import sys
import os
from datetime import datetime

SCRIPTS = [
    ("01_etl_carga_dados.py",     "ETL — Carga e Limpeza"),
    ("02_segmentacao_publicos.py","Segmentação dos Públicos"),
    ("03_engajamento_redes.py",   "Análise de Engajamento"),
    ("04_roi_campanhas.py",       "ROI e Performance"),
    ("05_relatorio_excel.py",     "Relatório Excel Consolidado"),
]

def instalar_dependencias():
    pacotes = ["pandas", "numpy", "scikit-learn", "openpyxl", "xlsxwriter"]
    print("Verificando dependências...\n")
    for pkg in pacotes:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
    print("✓ Dependências OK\n")

def executar_script(nome_arquivo, descricao):
    inicio = datetime.now()
    print(f"\n{'='*60}")
    print(f"  Iniciando: {descricao}")
    print(f"{'='*60}")
    resultado = subprocess.run([sys.executable, nome_arquivo], capture_output=False)
    duracao = (datetime.now() - inicio).total_seconds()
    if resultado.returncode == 0:
        print(f"\n✓ {descricao} concluído em {duracao:.1f}s")
        return True
    else:
        print(f"\n✕ ERRO em '{nome_arquivo}' (código {resultado.returncode})")
        return False

def main():
    print("\n" + "="*60)
    print("  SAD IMIP — Sistema de Apoio à Decisão")
    print("  Módulo: Marketing Digital")
    print(f"  Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)

    instalar_dependencias()

    sucesso = 0
    for arquivo, descricao in SCRIPTS:
        if os.path.exists(arquivo):
            ok = executar_script(arquivo, descricao)
            if ok:
                sucesso += 1
        else:
            print(f"⚠  Arquivo '{arquivo}' não encontrado. Pulando...")

    print("\n" + "="*60)
    print(f"  Conclusão: {sucesso}/{len(SCRIPTS)} scripts executados com sucesso")
    print(f"  Relatório gerado em: ./relatorios/")
    print(f"  Banco de dados:      ./imip_sad.db")
    print(f"  Logs:                ./logs/etl_log.txt")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
