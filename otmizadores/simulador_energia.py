"""
Simulador de Energia - Testa fontes ao longo do dia
"""

from datetime import datetime, timedelta
from gestor_energia import GestorEnergia
import matplotlib.pyplot as plt

class SimuladorEnergia:
    def __init__(self, demanda_por_minuto):
        """
        Inicializa o simulador com a demanda ao longo do dia.
        :param demanda_por_minuto: Lista com a demanda (kW) para cada minuto do dia (1440 valores).
        """
        self.demanda_por_minuto = demanda_por_minuto
        self.gestor = GestorEnergia()
        self.resultados = []

    def simular(self):
        """
        Executa a simulação ao longo do dia.
        """
        tempo_atual = datetime(2026, 1, 13, 0, 0)  # Início do dia
        for minuto, demanda in enumerate(self.demanda_por_minuto):
            fonte, custo, status = self.gestor.selecionar_fonte_otima(demanda)

            # Atualiza níveis de energia ou combustível
            if fonte == "Diesel":
                self.gestor.diesel.nivel -= self.gestor.diesel.consumo_100 / 60
            elif fonte == "Biogas":
                self.gestor.biogas.nivel -= self.gestor.biogas.consumo_100 / 60
            elif fonte == "Bateria":
                self.gestor.bateria.nivel -= demanda / 60

            # Registra o resultado
            self.resultados.append({
                "tempo": tempo_atual.strftime("%H:%M"),
                "demanda": demanda,
                "fonte": fonte,
                "custo": custo,
                "status": status
            })

            # Incrementa o tempo
            tempo_atual += timedelta(minutes=1)

    def gerar_relatorio(self):
        """
        Gera um relatório resumido da simulação.
        """
        print("\nRELATÓRIO DA SIMULAÇÃO")
        print("=" * 40)
        for resultado in self.resultados:
            print(f"{resultado['tempo']} - Demanda: {resultado['demanda']}kW - Fonte: {resultado['fonte']} - Custo: R${resultado['custo']:.2f} - Status: {resultado['status']}")

    def gerar_graficos(self):
        """
        Gera gráficos com os resultados da simulação.
        """
        tempos = [resultado['tempo'] for resultado in self.resultados]
        demandas = [resultado['demanda'] for resultado in self.resultados]
        custos = [resultado['custo'] for resultado in self.resultados]
        fontes = [resultado['fonte'] for resultado in self.resultados]

        # Gráfico de demanda ao longo do dia
        plt.figure(figsize=(10, 6))
        plt.plot(tempos, demandas, label='Demanda (kW)', color='blue')
        plt.xlabel('Tempo')
        plt.ylabel('Demanda (kW)')
        plt.title('Demanda ao longo do dia')
        plt.xticks(rotation=45, fontsize=8)
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Gráfico de custo por fonte ao longo do dia
        plt.figure(figsize=(10, 6))
        plt.plot(tempos, custos, label='Custo (R$/h)', color='green')
        plt.xlabel('Tempo')
        plt.ylabel('Custo (R$)')
        plt.title('Custo por fonte ao longo do dia')
        plt.xticks(rotation=45, fontsize=8)
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Gráfico de uso de fontes ao longo do dia
        plt.figure(figsize=(10, 6))
        plt.hist(fontes, bins=len(set(fontes)), color='orange', edgecolor='black')
        plt.xlabel('Fonte de Energia')
        plt.ylabel('Frequência de Uso')
        plt.title('Uso de Fontes ao longo do dia')
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # Exemplo de demanda ao longo do dia (1440 minutos)
    demanda_por_minuto = [1.0 if i % 60 < 30 else 2.5 for i in range(1440)]  # Alterna entre 1.0kW e 2.5kW

    simulador = SimuladorEnergia(demanda_por_minuto)
    simulador.simular()
    simulador.gerar_relatorio()
    simulador.gerar_graficos()