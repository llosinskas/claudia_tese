#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import traceback

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.Microrrede import Microrrede
from models.CRUD import Ler
from analises.config import ConfigAnalise
from analises.PrioridadeMicro import Analise1, Analise2, Analise3
from analises.analise_pso import AnalisePSO
from analises.analise_milp import AnaliseMILP

def rodar_testes():
    print("=" * 80)
    print("TESTE DE INTEGRAÇÃO: Rodando todas as Análises")
    print("=" * 80)

    microrredes = Ler(Microrrede)
    if not microrredes:
        print("❌ Nenhuma microrrede encontrada no banco de dados!")
        return False

    microrrede = microrredes[0]
    print(f"\n✓ Microrrede selecionada para teste: {microrrede.nome} (ID: {microrrede.id})")

    config = ConfigAnalise(
        solar_ligado=True,
        bateria_ligada=True,
        diesel_ligado=True,
        biogas_ligado=True,
        concessionaria_ligada=True,
        deslizamento_habilitado=True
    )

    resultados = []

    # Teste Análise 1
    try:
        print("\n⏳ Executando Análise 1...")
        res1 = Analise1.executar(microrrede, config)
        print("  ✅ Sucesso! Concluída Análise 1")
        resultados.append(("Análise 1", True))
    except Exception as e:
        print(f"  ❌ Erro na Análise 1: {e}")
        traceback.print_exc()
        resultados.append(("Análise 1", False))

    # Teste Análise 2
    try:
        print("\n⏳ Executando Análise 2...")
        res2 = Analise2.executar(microrrede, config)
        print("  ✅ Sucesso! Concluída Análise 2")
        resultados.append(("Análise 2", True))
    except Exception as e:
        print(f"  ❌ Erro na Análise 2: {e}")
        traceback.print_exc()
        resultados.append(("Análise 2", False))

    # Teste Análise 3
    try:
        print("\n⏳ Executando Análise 3...")
        res3 = Analise3.analise_3(microrrede, config)
        print("  ✅ Sucesso! Concluída Análise 3")
        resultados.append(("Análise 3", True))
    except Exception as e:
        print(f"  ❌ Erro na Análise 3: {e}")
        traceback.print_exc()
        resultados.append(("Análise 3", False))

    # Teste Análise MILP
    try:
        print("\n⏳ Executando Análise MILP...")
        res_milp = AnaliseMILP.executar(microrrede, config)
        print("  ✅ Sucesso! Concluída Análise MILP")
        resultados.append(("Análise MILP", True))
    except Exception as e:
        print(f"  ❌ Erro na Análise MILP: {e}")
        traceback.print_exc()
        resultados.append(("Análise MILP", False))

    # Teste Análise PSO
    try:
        print("\n⏳ Executando Análise PSO...")
        res_pso = AnalisePSO.executar(microrrede, config)
        print("  ✅ Sucesso! Concluída Análise PSO")
        resultados.append(("Análise PSO", True))
    except Exception as e:
        print(f"  ❌ Erro na Análise PSO: {e}")
        traceback.print_exc()
        resultados.append(("Análise PSO", False))

    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES")
    print("=" * 80)
    erros = 0
    for nome, ok in resultados:
        if ok:
            print(f"  ✅ PASS - {nome}")
        else:
            print(f"  ❌ FAIL - {nome}")
            erros += 1

    print(f"\nTotal Aprovados: {len(resultados) - erros}/{len(resultados)}")
    
    if erros == 0:
        print("\n🚀 Todos os testes passaram! As alterações podem ser entregues.")
        return True
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os erros antes de entregar.")
        return False

if __name__ == "__main__":
    success = rodar_testes()
    if not success:
        sys.exit(1)
