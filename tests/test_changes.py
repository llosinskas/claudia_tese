#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar:
1. Análise 3 - Novo método _gerenciar_bateria (carga/descarga com limites)
2. Análise 5 - MILP com variáveis binárias para deslizamento de cargas (prioridade 2 e 4)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from models.Microrrede import Microrrede
from models.CRUD import Ler
from analises.PrioridadeMicro import Analise3
from otmizadores.milp_controle_microrrede import analise_milp_com_deslizamento, MILPMicrorredes_ComDeslizamento


def test_analise3_bateria():
    """Testa se o método _gerenciar_bateria respeita todos os limites"""
    
    print("=" * 80)
    print("TESTE 1: Análise 3 - Método _gerenciar_bateria")
    print("=" * 80)
    
    microrredes = Ler(Microrrede)
    if not microrredes:
        print("❌ Nenhuma microrrede encontrada")
        return False
    
    microrrede = microrredes[0]
    print(f"\n✓ Testando com microrrede: {microrrede}")
    
    # Executa Análise 3
    print("\n⏳ Executando Análise 3...")
    resultado = Analise3.analise_3(microrrede)
    
    resultado_ot = resultado['otimizado']
    num_elementos = len(resultado_ot)
    print(f"  - Elementos retornados: {num_elementos}")
    
    if num_elementos < 19:
        print(f"❌ Número de elementos insuficiente ({num_elementos} < 19)")
        return False
    
    (custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria,
     total_uso_biogas, total_uso_solar, total_sobra, total_carga, uso_solar,
     uso_bateria, uso_biogas, uso_diesel, uso_concessionaria, curva_carga,
     nivel_bateria, nivel_biogas, nivel_diesel, custo_total_instantaneo, recarga_bateria) = resultado_ot
    
    print("\n📈 RESULTADOS DA ANÁLISE 3 (OTIMIZADA):")
    print(f"  ☀️  Solar:          {total_uso_solar:,.2f} kWh")
    print(f"  🔋 Bateria:        {total_uso_bateria:,.2f} kWh")
    print(f"  💨 Biogas:         {total_uso_biogas:,.2f} kWh")
    print(f"  🔥 Diesel:         {total_uso_diesel:,.2f} kWh")
    print(f"  🏢 Concessionária: {total_uso_concessionaria:,.2f} kWh")
    print(f"  📦 Carga Total:    {total_carga:,.2f} kWh")
    print(f"  💰 Custo Total:    R$ {custo_total_instantaneo.sum():,.2f}")
    
    # ===== VALIDAÇÕES DA BATERIA =====
    erros = 0
    bateria = microrrede.bateria
    
    if bateria:
        nivel_min = bateria.capacidade * bateria.capacidade_min / 100
        nivel_max = bateria.capacidade * bateria.capacidade_max / 100
        
        print(f"\n🔋 VALIDAÇÃO DA BATERIA:")
        print(f"  Potência máx: {bateria.potencia} kW")
        print(f"  Nível mín (SOC {bateria.capacidade_min}%): {nivel_min:.1f} kWh")
        print(f"  Nível máx (SOC {bateria.capacidade_max}%): {nivel_max:.1f} kWh")
        print(f"  Capacidade:   {bateria.capacidade} kWh")
        print(f"  Eficiência:   {bateria.eficiencia}%")
        
        # 1. Descarga nunca excede potência
        max_descarga = uso_bateria.max()
        if max_descarga > bateria.potencia + 0.01:
            print(f"  ❌ Descarga excede potência: {max_descarga:.2f} > {bateria.potencia}")
            erros += 1
        else:
            print(f"  ✅ Descarga máx: {max_descarga:.2f} kW (limite: {bateria.potencia} kW)")
        
        # 2. Recarga nunca excede potência
        max_recarga = recarga_bateria.max()
        if max_recarga > bateria.potencia + 0.01:
            print(f"  ❌ Recarga excede potência: {max_recarga:.2f} > {bateria.potencia}")
            erros += 1
        else:
            print(f"  ✅ Recarga máx: {max_recarga:.2f} kW (limite: {bateria.potencia} kW)")
        
        # 3. Nível nunca abaixo do mínimo operacional
        min_nivel = nivel_bateria[nivel_bateria > 0].min() if (nivel_bateria > 0).any() else 0
        if min_nivel < nivel_min - 0.01 and min_nivel > 0:
            print(f"  ❌ Nível abaixo do mínimo: {min_nivel:.2f} < {nivel_min:.1f}")
            erros += 1
        else:
            print(f"  ✅ Nível mín: {min_nivel:.2f} kWh (limite: {nivel_min:.1f} kWh)")
        
        # 4. Nível nunca acima do máximo operacional (exceto nível inicial)
        # O nível pode começar acima de nivel_max (bateria cheia)
        # Mas a recarga nunca deve elevar acima de nivel_max
        niveis_apos_recarga = nivel_bateria[recarga_bateria > 0]
        if len(niveis_apos_recarga) > 0:
            max_nivel_recarga = niveis_apos_recarga.max()
            if max_nivel_recarga > nivel_max + 0.01:
                print(f"  ❌ Recarga elevou acima do máximo: {max_nivel_recarga:.2f} > {nivel_max:.1f}")
                erros += 1
            else:
                print(f"  ✅ Nível máx após recarga: {max_nivel_recarga:.2f} kWh (limite: {nivel_max:.1f} kWh)")
        else:
            print(f"  ℹ️  Nenhuma recarga realizada")
        
        max_nivel = nivel_bateria.max()
        print(f"  ℹ️  Nível máx geral: {max_nivel:.2f} kWh (inclui nível inicial)")
    
    if erros == 0:
        print(f"\n✅ TESTE 1 APROVADO - Todos os limites da bateria respeitados!")
    else:
        print(f"\n❌ TESTE 1 FALHOU - {erros} violação(ões) encontrada(s)")
    
    return erros == 0


def test_analise5_milp_deslizamento():
    """Testa o MILP com variáveis binárias para deslizamento"""
    
    print("\n" + "=" * 80)
    print("TESTE 2: Análise 5 - MILP com Deslizamento Integrado")
    print("=" * 80)
    
    microrredes = Ler(Microrrede)
    if not microrredes:
        print("❌ Nenhuma microrrede encontrada")
        return False
    
    microrrede = microrredes[0]
    print(f"\n✓ Testando com microrrede: {microrrede}")
    
    # Lista cargas flexíveis
    cargas_flex = [cf for cf in microrrede.carga.cargaFixa if cf.prioridade in [2, 4]]
    print(f"\n📋 Cargas flexíveis (prioridade 2 e 4):")
    for cf in cargas_flex:
        h_liga = f"{int(cf.tempo_liga)//60:02d}:{int(cf.tempo_liga)%60:02d}"
        h_desl = f"{int(cf.tempo_desliga)//60:02d}:{int(cf.tempo_desliga)%60:02d}"
        print(f"  - {cf.nome} (P{cf.prioridade}): {h_liga}-{h_desl}, {cf.potencia:.1f} kW")
    
    if not cargas_flex:
        print("⚠️  Nenhuma carga flexível encontrada - teste será pulado")
        return True
    
    # Executa MILP com deslizamento
    print("\n⏳ Executando MILP com deslizamento integrado...")
    df_resultado, custos, solucao = analise_milp_com_deslizamento(microrrede, passo=15)
    
    if df_resultado is None:
        print("❌ MILP não encontrou solução")
        return False
    
    print(f"\n✅ Solução encontrada!")
    print(f"  💰 Custo total: R$ {custos.get('Total', 0):,.2f}")
    print(f"  📦 Carga total: {df_resultado['Carga'].sum():,.2f} kWh")
    
    # Verificar horários das cargas
    horarios = solucao.get('Horarios_Cargas', {})
    erros = 0
    
    if horarios:
        print(f"\n📋 CARGAS DESLOCADAS ({len(horarios)}):")
        for nome, info in horarios.items():
            h_orig = f"{info['original_inicio']//60:02d}:{info['original_inicio']%60:02d}"
            h_otim = f"{info['otimizado_inicio']//60:02d}:{info['otimizado_inicio']%60:02d}"
            duracao = info['otimizado_fim'] - info['otimizado_inicio']
            print(f"  - {nome} (P{info['prioridade']}): {h_orig} → {h_otim} ({duracao} min, {info['potencia']:.1f} kW)")
            
            # Verificar que a duração é preservada
            duracao_original = info['original_fim'] - info['original_inicio']
            if duracao != duracao_original:
                print(f"    ❌ Duração alterada: {duracao_original} → {duracao}")
                erros += 1
            else:
                print(f"    ✅ Duração preservada: {duracao} min")
    else:
        print("\n⚠️  Nenhuma carga foi deslocada (pode ser que o horário original já seja ótimo)")
    
    # Verificar balanço de energia
    print(f"\n🔍 VALIDAÇÃO DO BALANÇO DE ENERGIA:")
    carga = df_resultado['Carga'].values
    oferta = (df_resultado['Solar'].values + df_resultado['Bateria'].values +
              df_resultado['Diesel'].values + df_resultado['Concessionaria'].values)
    carga_bat = df_resultado['Carga_Bateria'].values
    
    desequilibrio = np.abs(oferta - carga - carga_bat)
    max_deseq = desequilibrio.max()
    if max_deseq > 0.1:
        print(f"  ❌ Desequilíbrio máximo: {max_deseq:.4f} kW")
        erros += 1
    else:
        print(f"  ✅ Balanço de energia OK (desvio máx: {max_deseq:.6f} kW)")
    
    # Verificar limites da bateria no MILP
    bateria = microrrede.bateria
    if bateria and 'Nivel_Bateria' in solucao:
        nivel_bat = np.array(solucao['Nivel_Bateria'])
        min_nivel = nivel_bat.min()
        max_nivel = nivel_bat.max()
        print(f"\n🔋 BATERIA MILP:")
        print(f"  Nível mín: {min_nivel:.2f} (limite: {bateria.capacidade_min})")
        print(f"  Nível máx: {max_nivel:.2f} (limite: {bateria.capacidade})")
        
        if min_nivel < bateria.capacidade_min - 0.1:
            print(f"  ❌ Nível abaixo do mínimo!")
            erros += 1
        else:
            print(f"  ✅ Mínimo respeitado")
            
        if max_nivel > bateria.capacidade + 0.1:
            print(f"  ❌ Nível acima do máximo!")
            erros += 1
        else:
            print(f"  ✅ Máximo respeitado")
    
    if erros == 0:
        print(f"\n✅ TESTE 2 APROVADO - MILP com deslizamento funcionando!")
    else:
        print(f"\n❌ TESTE 2 FALHOU - {erros} erro(s)")
    
    return erros == 0


def test_comparacao_custos():
    """Compara custos entre Análise 3 e Análise 5"""
    
    print("\n" + "=" * 80)
    print("TESTE 3: Comparação Análise 3 vs Análise 5")
    print("=" * 80)
    
    microrredes = Ler(Microrrede)
    if not microrredes:
        print("❌ Nenhuma microrrede encontrada")
        return False
    
    microrrede = microrredes[0]
    print(f"\n✓ Comparando com: {microrrede}")
    
    # Análise 3
    print("\n⏳ Análise 3...")
    resultado_a3 = Analise3.analise_3(microrrede)
    custo_a3_or = resultado_a3['original'][17].sum()
    custo_a3_ot = resultado_a3['otimizado'][17].sum()
    
    # Análise 5
    print("⏳ Análise 5 MILP...")
    df_a5, custos_a5, sol_a5 = analise_milp_com_deslizamento(microrrede)
    custo_a5 = custos_a5.get('Total', 0) if custos_a5 else float('inf')
    
    print(f"\n📊 COMPARAÇÃO DE CUSTOS:")
    print(f"  Análise 3 (original):   R$ {custo_a3_or:,.2f}")
    print(f"  Análise 3 (otimizada):  R$ {custo_a3_ot:,.2f}")
    print(f"  Análise 5 (MILP):       R$ {custo_a5:,.2f}")
    
    economia_a3 = custo_a3_or - custo_a3_ot
    print(f"\n  Economia A3: R$ {economia_a3:,.2f} ({economia_a3/custo_a3_or*100:.1f}%)")
    
    if custo_a5 < float('inf'):
        economia_a5 = custo_a3_or - custo_a5
        print(f"  Economia A5: R$ {economia_a5:,.2f} ({economia_a5/custo_a3_or*100:.1f}%)")
    
    print(f"\n✅ TESTE 3 CONCLUÍDO")
    return True


if __name__ == "__main__":
    print("\n" + "#" * 80)
    print("# TESTES: Análise 3 (Bateria) + Análise 5 (MILP Deslizamento)")
    print("#" * 80)
    
    resultados = []
    
    # Teste 1: Bateria
    try:
        r1 = test_analise3_bateria()
        resultados.append(("Análise 3 - Bateria", r1))
    except Exception as e:
        print(f"\n❌ ERRO no Teste 1: {e}")
        import traceback
        traceback.print_exc()
        resultados.append(("Análise 3 - Bateria", False))
    
    # Teste 2: MILP Deslizamento
    try:
        r2 = test_analise5_milp_deslizamento()
        resultados.append(("Análise 5 - MILP Deslizamento", r2))
    except Exception as e:
        print(f"\n❌ ERRO no Teste 2: {e}")
        import traceback
        traceback.print_exc()
        resultados.append(("Análise 5 - MILP Deslizamento", False))
    
    # Teste 3: Comparação
    try:
        r3 = test_comparacao_custos()
        resultados.append(("Comparação Custos", r3))
    except Exception as e:
        print(f"\n❌ ERRO no Teste 3: {e}")
        import traceback
        traceback.print_exc()
        resultados.append(("Comparação Custos", False))
    
    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES")
    print("=" * 80)
    for nome, ok in resultados:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status} - {nome}")
    
    total_ok = sum(1 for _, ok in resultados if ok)
    print(f"\n  {total_ok}/{len(resultados)} testes aprovados")
