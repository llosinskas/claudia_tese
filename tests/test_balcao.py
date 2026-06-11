import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH para os imports funcionarem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.CRUD import Ler
from models.Microrrede import Microrrede
from analises.config import ConfigAnalise

from analises.analise1 import Analise1
from analises.analise2 import Analise2
from analises.analise3 import Analise3
from analises.analise_milp import AnaliseMILP
from analises.analise_pso import AnalisePSO

from mercado.resultado_analise import ResultadoAnalise
from mercado.balcao_energia import BalcaoEnergia

def run_test():
    microrredes = Ler(Microrrede)
    if not microrredes:
        print("Nenhuma microrrede cadastrada.")
        sys.exit(1)
        
    config = ConfigAnalise()
    
    print("\n" + "="*80)
    print("TESTE DO BALCÃO DE ENERGIA COM VÁRIOS MÉTODOS")
    print("="*80)
    
    for metodo_nome, metodo_call in [
        ("Análise 2 (Heurística Base)", lambda mr: ResultadoAnalise.from_analise2_ou_3(mr, Analise2.executar(mr, config), "heuristico")),
        ("Análise 3 (Deslizamento)", lambda mr: ResultadoAnalise.from_analise2_ou_3(mr, Analise3.analise_3(mr, config)["otimizado"], "heuristico_deslize")),
        ("Análise MILP (Otimização Matemática)", lambda mr: ResultadoAnalise.from_milp(mr, AnaliseMILP.executar(mr, config)["resultado_df"])),
    ]:
        print(f"\n[+] Testando Balcão usando como fonte: {metodo_nome}...")
        
        resultados_individuais = []
        for mr in microrredes:
            res = metodo_call(mr)
            resultados_individuais.append(res)
            
        balcao = BalcaoEnergia(resultados_individuais)
        resultado_balcao = balcao.executar()
        
        print(f"  [OK] Mercado rodado com sucesso!")
        print(f"  - Transacoes realizadas: {resultado_balcao.num_transacoes}")
        print(f"  - Volume negociado: {resultado_balcao.volume_total_negociado:.2f} kWh")
        print(f"  - Economia global: R$ {resultado_balcao.economia_total:.2f}")
        print(f"  - Perdas na rede: {resultado_balcao.perdas_totais_kwh:.2f} kWh")

if __name__ == "__main__":
    run_test()
