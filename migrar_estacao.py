"""
Script de migração: Adiciona coluna 'estacao' à tabela 'microrrede'.
Microrredes existentes recebem 'Verão' como valor padrão.

Executar uma única vez: python migrar_estacao.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "meu_banco.db")

def migrar():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(microrrede)")
    colunas = [col[1] for col in cursor.fetchall()]

    if "estacao" in colunas:
        print("[OK] Coluna 'estacao' ja existe na tabela 'microrrede'. Nada a fazer.")
        conn.close()
        return

    # Adicionar coluna
    cursor.execute("ALTER TABLE microrrede ADD COLUMN estacao TEXT DEFAULT 'Verão'")
    
    # Setar registros existentes
    cursor.execute("UPDATE microrrede SET estacao = 'Verão' WHERE estacao IS NULL")
    
    conn.commit()
    
    # Verificar
    cursor.execute("SELECT id, nome, estacao FROM microrrede")
    registros = cursor.fetchall()
    print(f"[OK] Coluna 'estacao' adicionada com sucesso!")
    print(f"   {len(registros)} microrrede(s) atualizada(s) para 'Verao':")
    for r in registros:
        print(f"   - ID={r[0]}, Nome={r[1]}, Estacao={r[2]}")

    conn.close()

if __name__ == "__main__":
    migrar()
