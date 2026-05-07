#!/usr/bin/env python3
"""
Script de teste para a integração do PSO
Testa se o otimizador PSO funciona corretamente com as microrredes
"""

import sys
import numpy as np
import pandas as pd
from models.Microrrede import Microrrede
from models.CRUD import Ler
from database.database_config import Configure
from otmizadores.pso import analise_pso

# Configuração do banco de dados
DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

def test_pso():
    """Testa a otimização PSO com microrredes existentes"""
    print("=" * 80)
    print("TESTE DE INTEGRAÇÃO PSO")
    print("=" * 80)
    
    # Carregar microrredes do banco de dados
    microrredes = Ler(Microrrede)
    
    if not microrredes:
        print("❌ Nenhuma microrrede encontrada no banco de dados!")
        print("   Execute a Análise de Exemplo primeiro para gerar dados.")
        return False
    
    print(f"\n✓ {len(microrredes)} microrrede(s) carregada(s) do banco de dados\n")
    
    # Testar cada microrrede
    for i, microrrede in enumerate(microrredes, 1):
        print(f"\n{'='*80}")
        print(f"TESTE {i}: Microrrede '{microrrede.nome}'")
        print(f"{'='*80}")
        
        try:
            # Executar otimização PSO
            print(f"\n⏳ Executando otimização PSO para {microrrede.nome}...")
            print("   Parâmetros: iterações=30, tamanho_enxame=15")
            
            df_resultado, custos, solucao = analise_pso(
                microrrede,
                iteracoes=30,
                tamanho_enxame=15
            )
            
            if df_resultado is None:
                print(f"❌ Erro: DataFrame resultado é None")
                return False
            
            # Verificar resultados
            print("\n✓ Otimização concluída com sucesso!")
            
            print("\n📊 RESUMO DE CUSTOS:")
            print(f"  - Solar:          R$ {custos['Solar']:>10,.2f}")
            print(f"  - Diesel:         R$ {custos['Diesel']:>10,.2f}")
            print(f"  - Biogas:         R$ {custos['Biogas']:>10,.2f}")
            print(f"  - Bateria:        R$ {custos['Bateria']:>10,.2f}")
            print(f"  - Concessionária: R$ {custos['Concessionaria']:>10,.2f}")
            print(f"  {'─'*40}")
            print(f"  - TOTAL:          R$ {custos['Total']:>10,.2f}")
            
            # Verificar DataFrame
            print("\n📈 CARACTERÍSTICAS DO DATAFRAME:")
            print(f"  - Linhas: {len(df_resultado)}")
            print(f"  - Colunas: {list(df_resultado.columns)}")
            
            # Estatísticas de energia
            print("\n⚡ USO DE ENERGIA:")
            total_carga = df_resultado['Carga'].sum()
            solar = df_resultado['Solar'].sum()
            bateria = df_resultado['Bateria'].sum()
            diesel = df_resultado['Diesel'].sum()
            biogas = df_resultado['Biogas'].sum()
            concessionaria = df_resultado['Concessionaria'].sum()
            
            print(f"  - Demanda total:     {total_carga:>10,.2f} kWh")
            print(f"  - Solar:             {solar:>10,.2f} kWh ({solar/total_carga*100:>5.1f}%)")
            print(f"  - Bateria:           {bateria:>10,.2f} kWh ({bateria/total_carga*100:>5.1f}%)")
            print(f"  - Diesel:            {diesel:>10,.2f} kWh ({diesel/total_carga*100:>5.1f}%)")
            print(f"  - Biogas:            {biogas:>10,.2f} kWh ({biogas/total_carga*100:>5.1f}%)")
            print(f"  - Concessionária:    {concessionaria:>10,.2f} kWh ({concessionaria/total_carga*100:>5.1f}%)")
            
            # Validar convergência
            if 'Convergencia' in solucao:
                conv = solucao['Convergencia']
                print(f"\n📉 CONVERGÊNCIA PSO:")
                print(f"  - Iterações: {len(conv)}")
                print(f"  - Melhor custo inicial: R$ {conv[0]:,.2f}")
                print(f"  - Melhor custo final:   R$ {conv[-1]:,.2f}")
                melhoria = (conv[0] - conv[-1]) / conv[0] * 100
                print(f"  - Melhoria: {melhoria:.1f}%")
            
            print("\n✓ Teste PASSADO para esta microrrede\n")
            
        except Exception as e:
            print(f"\n❌ ERRO durante otimização: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "="*80)
    print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
    print("="*80)
    print("\n🎉 A integração do PSO foi bem-sucedida!")
    print("   A análise 6 do botão PSO está pronta para uso.")
    print("\nPróximos passos:")
    print("  1. Abra o Streamlit: streamlit run Home.py")
    print("  2. Navegue para a página 'Analises'")
    print("  3. Clique no botão 'Análise 6 - PSO'")
    print("  4. Ajuste os parâmetros (iterações, tamanho do enxame)")
    print("  5. Veja os resultados de otimização!\n")
    
    return True


if __name__ == "__main__":
    try:
        sucesso = test_pso()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
