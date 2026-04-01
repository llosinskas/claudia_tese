#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar a Análise 3 com venda de energia para a rede
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.Microrrede import Microrrede
from models.CRUD import Ler
from analises.PrioridadeMicro import Analise3

def test_analise3_venda():
    """Testa se a Análise 3 retorna corretamente os dados de venda"""
    
    print("=" * 80)
    print("TESTE: Validação da Análise 3 com Venda de Energia")
    print("=" * 80)
    
    # Carrega as microrredes
    microrredes = Ler(Microrrede)
    
    if not microrredes:
        print("❌ Erro: Nenhuma microrrede encontrada no banco de dados")
        return
    
    # Testa com a primeira microrrede
    microrrede = microrredes[0]
    print(f"\n✓ Testando com microrrede: {microrrede}")
    
    # Executa Análise 3
    print("\n⏳ Executando Análise 3...")
    resultado = Analise3.analise_3(microrrede)
    
    # Extrai resultados otimizados
    print("\n📊 Extraindo resultados otimizados...")
    resultado_ot = resultado['otimizado']
    
    # Verifica o número de elementos na tupla
    num_elementos = len(resultado_ot)
    print(f"  - Número de elementos retornados: {num_elementos}")
    
    # Desempacota com segurança
    if num_elementos >= 23:
        (custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria, 
         total_uso_biogas, total_uso_solar, total_sobra, total_carga, uso_solar, 
         uso_bateria, uso_biogas, uso_diesel, uso_concessionaria, curva_carga, 
         nivel_bateria, nivel_biogas, nivel_diesel, custo_total_instantaneo, carga_bateria,
         venda, receita_venda, total_venda, total_receita_venda) = resultado_ot
        
        print("\n✅ Desempacotamento bem-sucedido!")
        print("\n📈 RESULTADOS DA ANÁLISE 3 (OTIMIZADA):")
        print(f"  ☀️  Solar utilizado:           {total_uso_solar:,.2f} kWh")
        print(f"  🔋 Bateria utilizada:         {total_uso_bateria:,.2f} kWh")
        print(f"  💨 Biogas utilizado:          {total_uso_biogas:,.2f} kWh")
        print(f"  🔥 Diesel utilizado:          {total_uso_diesel:,.2f} kWh")
        print(f"  🏢 Concessionária (compra):   {total_uso_concessionaria:,.2f} kWh")
        print(f"  📤 VENDA PARA REDE:           {total_venda:,.2f} kWh ✨ NOVO!")
        print(f"  💵 Receita de Venda:          R$ {total_receita_venda:,.2f} ✨ NOVO!")
        print(f"  📦 Demanda total:             {total_carga:,.2f} kWh")
        print(f"  💰 Custo total (com venda):   R$ {custo_total_instantaneo.sum():,.2f}")
        
        # Verifica se há venda real
        if total_venda > 0:
            print(f"\n✅ SUCESSO! A Análise 3 está vendendo energia para a rede!")
            print(f"   Quantidade de períodos com venda: {(venda > 0).sum()} em {len(venda)}")
            print(f"   Máxima venda em um período: {venda.max():,.2f} kW")
            print(f"   Mínima venda em um período: {venda.min():,.2f} kW")
        else:
            print(f"\n⚠️  AVISO: Nenhuma venda de energia foi registrada.")
            print(f"   Pode indicar que o solar não está gerando excedente ou")
            print(f"   a bateria está sempre sendo carregada.")
        
        # Comparação antes/depois
        print("\n📊 COMPARAÇÃO - ORIGINAL vs OTIMIZADO:")
        resultado_or = resultado['original']
        
        if len(resultado_or) >= 23:
            (_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, 
             custo_total_instantaneo_or, _, venda_or, receita_venda_or, 
             total_venda_or, total_receita_venda_or) = resultado_or
            
            custo_or = custo_total_instantaneo_or.sum()
            custo_ot = custo_total_instantaneo.sum()
            economia = custo_or - custo_ot
            
            print(f"  Custo (ORIGINAL):      R$ {custo_or:,.2f}")
            print(f"  Custo (OTIMIZADO):     R$ {custo_ot:,.2f}")
            print(f"  Diferença:             R$ {economia:,.2f} ({economia/custo_or*100:.1f}%)")
            print(f"  Venda Original:        {total_venda_or:,.2f} kWh")
            print(f"  Venda Otimizada:       {total_venda:,.2f} kWh")
        
    else:
        print(f"\n❌ ERRO: Número de elementos inesperado ({num_elementos})")
        print("   Verifique se a função _executar_simulacao_otimizacao retorna todos os valores")
        
        # Mostra quais elementos foram retornados
        if isinstance(resultado_ot, tuple):
            print(f"\n   Primeiros 5 elementos: {[type(x).__name__ for x in resultado_ot[:5]]}")

if __name__ == "__main__":
    test_analise3_venda()
