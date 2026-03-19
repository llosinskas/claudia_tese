"""
Script de exemplo para testar otimização MILP de microrredes
"""

import sys
import pandas as pd
import numpy as np

# Adicionar diretório ao path
sys.path.append('.')

from otmizadores.milp_controle_microrrede import MILPMicrorredes, analise_milp
from models.Microrrede import Microrrede
from models.CRUD import Ler, Ler_Objeto


def exemplo_1_microrrede_unica():
    """
    Exemplo 1: Otimização de uma única microrrede
    """
    print("\n" + "="*70)
    print("EXEMPLO 1: Otimização MILP de Uma Única Microrrede")
    print("="*70)
    
    try:
        # Carregar uma microrrede do banco de dados
        microrrede = Ler_Objeto(Microrrede, 1)
        
        print(f"\n📡 Microrrede: {microrrede}")
        print(f"   - Solar: {'✓' if microrrede.solar else '✗'}")
        print(f"   - Bateria: {'✓' if microrrede.bateria else '✗'}")
        print(f"   - Diesel: {'✓' if microrrede.diesel else '✗'}")
        print(f"   - Biogas: {'✓' if microrrede.biogas else '✗'}")
        
        # Criar otimizador
        print("\n⚙️  Criando modelo MILP...")
        otimizador = MILPMicrorredes(microrrede)
        
        # Construir modelo
        otimizador.criar_modelo(verbose=True)
        otimizador.adicionar_restricoes(verbose=True)
        otimizador.adicionar_funcao_objetivo(verbose=True)
        
        # Resolver
        print("\n🔍 Resolvendo modelo...")
        sucesso = otimizador.resolver(verbose=True)
        
        if sucesso:
            # Extrair solução
            solucao = otimizador.extrair_solucao()
            
            # Gerar resultados
            df_resultado = otimizador.gerar_dataframe_resultado()
            custos = otimizador.calcular_custos_totais()
            
            # Exibir informações
            print("\n" + "-"*70)
            print("RESULTADOS DA OTIMIZAÇÃO")
            print("-"*70)
            
            print("\n📊 Distribuição de Energia:")
            print(f"   Solar:          {df_resultado['Solar'].sum():>10.2f} kWh")
            print(f"   Bateria:        {df_resultado['Bateria'].sum():>10.2f} kWh")
            print(f"   Diesel:         {df_resultado['Diesel'].sum():>10.2f} kWh")
            print(f"   Biogas:         {df_resultado['Biogas'].sum():>10.2f} kWh")
            print(f"   Concessionária: {df_resultado['Concessionaria'].sum():>10.2f} kWh")
            print(f"   Venda:          {df_resultado['Venda'].sum():>10.2f} kWh")
            print(f"   {'─'*50}")
            print(f"   Carga Total:    {df_resultado['Carga'].sum():>10.2f} kWh")
            
            print("\n💰 Custos Operacionais:")
            for fonte, custo in custos.items():
                if fonte != 'Total':
                    print(f"   {fonte:20s}: R$ {custo:>10,.2f}")
            print(f"   {'─'*50}")
            print(f"   {'CUSTO TOTAL':20s}: R$ {custos['Total']:>10,.2f}")
            
            print("\n📈 Estatísticas:")
            carga_total = df_resultado['Carga'].sum()
            autossuficiencia = ((carga_total - df_resultado['Concessionaria'].sum()) / carga_total * 100)
            print(f"   Autossuficiência: {autossuficiencia:.2f}%")
            print(f"   Custo por kWh: R$ {custos['Total'] / carga_total:.4f}")
            
            # Primeiras e últimas linhas do resultado
            print("\n📋 Amostra dos Resultados (primeiras 10 linhas):")
            print(df_resultado.head(10).to_string())
            
            return df_resultado, custos, solucao
        
        else:
            print("✗ Não foi possível resolver o modelo")
            return None, None, None
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None


def exemplo_2_multiplas_microrredes():
    """
    Exemplo 2: Otimização de múltiplas microrredes
    """
    print("\n" + "="*70)
    print("EXEMPLO 2: Comparação de Múltiplas Microrredes")
    print("="*70)
    
    try:
        # Carregar todas as microrredes
        microrredes = Ler(Microrrede)
        
        if not microrredes:
            print("⚠️  Nenhuma microrrede encontrada no banco de dados")
            return None
        
        print(f"\n🔍 Encontradas {len(microrredes)} microrredes")
        
        resultados = {}
        
        # Otimizar cada uma
        for i, microrrede in enumerate(microrredes, 1):
            print(f"\n[{i}/{len(microrredes)}] Otimizando: {microrrede}")
            
            try:
                df_resultado, custos, solucao = analise_milp(microrrede)
                
                if df_resultado is not None:
                    resultados[str(microrrede)] = {
                        'custos': custos,
                        'df': df_resultado,
                        'solucao': solucao
                    }
                else:
                    print(f"   ⚠️  Não foi possível otimizar")
            
            except Exception as e:
                print(f"   ❌ Erro: {str(e)}")
        
        # Comparação
        if resultados:
            print("\n" + "="*70)
            print("COMPARAÇÃO DAS MICRORREDES OTIMIZADAS")
            print("="*70)
            
            dados_comparacao = []
            for nome, resultado in resultados.items():
                custos = resultado['custos']
                df = resultado['df']
                carga_total = df['Carga'].sum()
                autossuf = ((carga_total - df['Concessionaria'].sum()) / carga_total * 100) if carga_total > 0 else 0
                
                dados_comparacao.append({
                    'Microrrede': nome,
                    'Custo Total (R$)': custos.get('Total', 0),
                    'Carga (kWh)': carga_total,
                    'Autossuficiência (%)': autossuf,
                    'Custo/kWh': custos.get('Total', 0) / carga_total if carga_total > 0 else 0
                })
            
            df_comparacao = pd.DataFrame(dados_comparacao)
            df_comparacao = df_comparacao.sort_values('Custo Total (R$)')
            
            print("\n" + df_comparacao.to_string(index=False))
            
            # Resumo
            print("\n📊 Resumo Geral:")
            print(f"   Custo Total Consolidado: R$ {df_comparacao['Custo Total (R$)'].sum():,.2f}")
            print(f"   Carga Total Atendida: {df_comparacao['Carga (kWh)'].sum():,.2f} kWh")
            print(f"   Autossuficiência Média: {df_comparacao['Autossuficiência (%)'].mean():.2f}%")
            
            return df_comparacao
        
        else:
            print("\n⚠️  Nenhuma microrrede foi otimizada com sucesso")
            return None
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def exemplo_3_analise_sensibilidade():
    """
    Exemplo 3: Análise de sensibilidade (variando custos)
    """
    print("\n" + "="*70)
    print("EXEMPLO 3: Análise de Sensibilidade")
    print("="*70)
    
    try:
        # Carregar uma microrrede
        microrrede = Ler_Objeto(Microrrede, 1)
        
        if not microrrede:
            print("⚠️  Nenhuma microrrede encontrada")
            return None
        
        print(f"\n📡 Microrrede: {microrrede}")
        print("\n🔄 Variando custo do diesel...")
        
        resultados_sensibilidade = []
        
        # Variar custo do diesel (50% a 200%)
        custos_diesel = [microrrede.diesel.custo_por_kWh * fator for fator in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]]
        
        for i, custo in enumerate(custos_diesel, 1):
            print(f"\n[{i}/{len(custos_diesel)}] Testando diesel@R${custo:.2f}/kWh...")
            
            # Modificar custo (temporário)
            custo_original = microrrede.diesel.custo_por_kWh
            microrrede.diesel.custo_por_kWh = custo
            
            # Otimizar
            try:
                otimizador = MILPMicrorredes(microrrede)
                otimizador.criar_modelo(verbose=False)
                otimizador.adicionar_restricoes(verbose=False)
                otimizador.adicionar_funcao_objetivo(verbose=False)
                
                if otimizador.resolver(verbose=False):
                    df_resultado, custos, solucao = analise_milp(microrrede)
                    
                    resultados_sensibilidade.append({
                        'Custo Diesel (R$/kWh)': custo,
                        'Custo Total (R$)': custos.get('Total', 0),
                        'Uso Diesel (kWh)': df_resultado['Diesel'].sum(),
                        'Uso Bateria (kWh)': df_resultado['Bateria'].sum(),
                        'Uso Solar (kWh)': df_resultado['Solar'].sum(),
                    })
            
            except Exception as e:
                print(f"   ❌ Erro: {str(e)}")
            
            # Restaurar custo original
            microrrede.diesel.custo_por_kWh = custo_original
        
        if resultados_sensibilidade:
            df_sens = pd.DataFrame(resultados_sensibilidade)
            
            print("\n" + "="*70)
            print("RESULTADOS DA ANÁLISE DE SENSIBILIDADE")
            print("="*70)
            print("\n" + df_sens.to_string(index=False))
            
            # Insights
            print("\n💡 Insights:")
            min_custo_diesel = df_sens.loc[df_sens['Custo Total (R$)'].idxmin(), 'Custo Diesel (R$/kWh)']
            print(f"   - Custo mínimo quando diesel = R$ {min_custo_diesel:.2f}/kWh")
            
            mudanca_uso_diesel = df_sens['Uso Diesel (kWh)'].max() - df_sens['Uso Diesel (kWh)'].min()
            print(f"   - Variação no uso de diesel: {mudanca_uso_diesel:.2f} kWh")
            
            return df_sens
        
        else:
            print("\n⚠️  Nenhum resultado foi gerado")
            return None
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Função principal - executa exemplos
    """
    print("\n" + "="*70)
    print("EXEMPLOS DE OTIMIZAÇÃO MILP PARA MICRORREDES")
    print("="*70)
    
    # Menu
    opcoes = {
        '1': ('Uma Única Microrrede', exemplo_1_microrrede_unica),
        '2': ('Múltiplas Microrredes Comparação', exemplo_2_multiplas_microrredes),
        '3': ('Análise de Sensibilidade', exemplo_3_analise_sensibilidade),
        '0': ('Sair', None)
    }
    
    while True:
        print("\n" + "-"*70)
        print("MENU DE EXEMPLOS")
        print("-"*70)
        
        for key, (descricao, _) in opcoes.items():
            print(f"  {key}. {descricao}")
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha not in opcoes:
            print("❌ Opção inválida!")
            continue
        
        if escolha == '0':
            print("\n👋 Encerrando...")
            break
        
        descricao, funcao = opcoes[escolha]
        
        try:
            resultado = funcao()
            
            if resultado is not None and escolha in ['1', '2', '3']:
                salvar = input("\n💾 Salvar resultados? (s/n): ").strip().lower()
                
                if salvar == 's':
                    nome_arquivo = f"resultado_milp_exemplo{escolha}.csv"
                    
                    if isinstance(resultado, pd.DataFrame):
                        resultado.to_csv(nome_arquivo, index=False)
                        print(f"✓ Resultados salvos em: {nome_arquivo}")
                    else:
                        print("⚠️  Resultado não é um DataFrame")
        
        except Exception as e:
            print(f"\n❌ Erro durante execução: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
