"""
Gestor de Energia - Seleciona a fonte mais barata que pode atender a demanda
Testa: Diesel, Biogas, Solar, Bateria (nessa ordem de custo tipicamente)
"""
from models.Microrrede import Microrrede, Diesel, Carga, Biogas, Solar, Bateria, Concessionaria

from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()


# Microrrede única
def Custo_sem_otimizacao(microrrede: Microrrede):
    if microrrede is None:
        pass

def Gerenciamento_energia():
    pass 

# Gestor de multiplas microrredes
def Gestor_multiplas_microrredes():
    pass



class GestorEnergia:
    """Classe para gerenciar seleção de fontes de energia baseado em custo e disponibilidade"""
    
    def __init__(self):
        self.diesel = None
        self.biogas = None
        self.solar = None
        self.bateria = None
        self.carregar_fontes()
    
    def carregar_fontes(self):
        """Carrega todas as fontes de energia do banco de dados"""
        try:
            dieseis = session.query(Diesel).all()
            self.diesel = dieseis[0] if dieseis else None
            
            biogases = session.query(Biogas).all()
            self.biogas = biogases[0] if biogases else None
            
            solares = session.query(Solar).all()
            self.solar = solares[0] if solares else None
            
            baterias = session.query(BancoBateria).all()
            self.bateria = baterias[0] if baterias else None
        except Exception as e:
            print(f"Erro ao carregar fontes: {e}")
    
    def pode_diesel_atender(self, demanda_kw):
        """Verifica se Diesel pode atender a demanda"""
        if not self.diesel:
            return False, "Diesel não disponível"
        
        # Verifica potência
        if self.diesel.potencia < demanda_kw:
            return False, f"Diesel potência insuficiente: {self.diesel.potencia}kW < {demanda_kw}kW"
        
        # Verifica nível de combustível (tanque)
        if self.diesel.nivel <= 0:
            return False, f"Diesel sem combustível: nível={self.diesel.nivel}l"
        
        return True, "Diesel OK"
    
    def pode_biogas_atender(self, demanda_kw):
        """Verifica se Biogas pode atender a demanda"""
        if not self.biogas:
            return False, "Biogas não disponível"
        
        # Verifica potência
        if self.biogas.potencia < demanda_kw:
            return False, f"Biogas potência insuficiente: {self.biogas.potencia}kW < {demanda_kw}kW"
        
        # Verifica nível do tanque
        if self.biogas.nivel <= 0:
            return False, f"Biogas sem combustível: nível={self.biogas.nivel}m³"
        
        return True, "Biogas OK"
    
    def pode_solar_atender(self, demanda_kw, valor_geracao_atual=None):
        """Verifica se Solar pode atender a demanda"""
        if not self.solar:
            return False, "Solar não disponível"
        
        # Verifica potência instalada
        if self.solar.potencia < demanda_kw:
            return False, f"Solar potência insuficiente: {self.solar.potencia}kW < {demanda_kw}kW"
        
        # Se houver valor de geração atual (de curva), verifica
        if valor_geracao_atual is not None and valor_geracao_atual < demanda_kw:
            return False, f"Solar geração insuficiente neste momento: {valor_geracao_atual}kW < {demanda_kw}kW"
        
        return True, "Solar OK"
    
    def pode_bateria_atender(self, demanda_kw):
        """Verifica se Bateria pode atender a demanda"""
        if not self.bateria:
            return False, "Bateria não disponível"
        
        # Verifica potência
        if self.bateria.potencia < demanda_kw:
            return False, f"Bateria potência insuficiente: {self.bateria.potencia}kW < {demanda_kw}kW"
        
        # Verifica nível de carga acumulada
        if self.bateria.nivel <= self.bateria.capacidade_min:
            return False, f"Bateria nível crítico: {self.bateria.nivel}kWh <= mínimo {self.bateria.capacidade_min}kWh"
        
        # Verifica se tem energia suficiente para o tempo mínimo (1 hora)
        energia_disponivel = self.bateria.nivel - self.bateria.capacidade_min
        if energia_disponivel < demanda_kw:
            return False, f"Bateria energia insuficiente: {energia_disponivel}kWh < {demanda_kw}kW para 1 hora"
        
        return True, "Bateria OK"
    
    def custo_horario_diesel(self, demanda_kw):
        """Calcula custo horário do Diesel para uma demanda"""
        if not self.diesel:
            return float('inf')
        
        # Estima consumo baseado na demanda
        if demanda_kw <= self.diesel.potencia * 0.5:
            consumo = self.diesel.consumo_50
        elif demanda_kw <= self.diesel.potencia * 0.75:
            consumo = self.diesel.consumo_75
        else:
            consumo = self.diesel.consumo_100
        
        # custo por hora = consumo (l/h) * preço (R$/l)
        return consumo * self.diesel.custo
    
    def custo_horario_biogas(self, demanda_kw):
        """Calcula custo horário do Biogas para uma demanda"""
        if not self.biogas:
            return float('inf')
        
        # Estima consumo baseado na demanda
        if demanda_kw <= self.biogas.potencia * 0.5:
            consumo = self.biogas.consumo_50
        elif demanda_kw <= self.biogas.potencia * 0.75:
            consumo = self.biogas.consumo_75
        else:
            consumo = self.biogas.consumo_100
        
        # custo por hora = consumo (m³/h) * preço (R$/m³)
        return consumo * self.biogas.custo_m3
    
    def custo_horario_solar(self, demanda_kw):
        """Calcula custo horário da Solar (custo fixo de manutenção)"""
        if not self.solar:
            return float('inf')
        
        # Solar normalmente tem custo fixo diário/mensal
        # Aqui consideramos apenas o custo operacional (muito baixo)
        return self.solar.custo_kwh * demanda_kw
    
    def custo_horario_bateria(self, demanda_kw):
        """Calcula custo horário da Bateria"""
        if not self.bateria:
            return float('inf')
        
        # Bateria: custo é baseado no kWh utilizado
        return self.bateria.custo_kwh * demanda_kw
    
    def testar_fontes_ordenadas(self, demanda_kw):
        """
        Testa todas as fontes ordenadas por custo
        Retorna: (fonte_selecionada, custo, status_detalhado)
        """
        fontes = []
        
        # Coleta custo e status de cada fonte
        pode_diesel, msg_diesel = self.pode_diesel_atender(demanda_kw)
        if pode_diesel:
            custo_d = self.custo_horario_diesel(demanda_kw)
            fontes.append(('Diesel', custo_d, msg_diesel))
        else:
            fontes.append(('Diesel', float('inf'), msg_diesel))
        
        pode_biogas, msg_biogas = self.pode_biogas_atender(demanda_kw)
        if pode_biogas:
            custo_b = self.custo_horario_biogas(demanda_kw)
            fontes.append(('Biogas', custo_b, msg_biogas))
        else:
            fontes.append(('Biogas', float('inf'), msg_biogas))
        
        pode_solar, msg_solar = self.pode_solar_atender(demanda_kw)
        if pode_solar:
            custo_s = self.custo_horario_solar(demanda_kw)
            fontes.append(('Solar', custo_s, msg_solar))
        else:
            fontes.append(('Solar', float('inf'), msg_solar))
        
        pode_bateria, msg_bateria = self.pode_bateria_atender(demanda_kw)
        if pode_bateria:
            custo_bat = self.custo_horario_bateria(demanda_kw)
            fontes.append(('Bateria', custo_bat, msg_bateria))
        else:
            fontes.append(('Bateria', float('inf'), msg_bateria))
        
        # Ordena por custo (crescente)
        fontes_ordenadas = sorted(fontes, key=lambda x: x[1])
        
        # Retorna relatório completo
        return fontes_ordenadas
    
    def selecionar_fonte_otima(self, demanda_kw):
        """
        Seleciona a fonte mais barata que pode atender a demanda
        Retorna: (fonte_selecionada, custo, disponibilidade)
        """
        fontes_ordenadas = self.testar_fontes_ordenadas(demanda_kw)
        
        # Encontra a primeira fonte viável (custo != inf)
        for fonte, custo, status in fontes_ordenadas:
            if custo != float('inf'):
                return fonte, custo, status
        
        # Se nenhuma fonte viável
        return None, float('inf'), "Nenhuma fonte disponível!"


def exemplo_uso():
    """Exemplo de uso do Gestor de Energia"""
    gestor = GestorEnergia()
    
    # Testa diferentes demandas
    demandas = [1.0, 2.5, 5.0]
    
    for demanda in demandas:
        print(f"\n{'='*60}")
        print(f"DEMANDA: {demanda} kW")
        print('='*60)
        
        # Mostra todas as fontes ordenadas por custo
        fontes = gestor.testar_fontes_ordenadas(demanda)
        
        for i, (fonte, custo, status) in enumerate(fontes, 1):
            if custo == float('inf'):
                print(f"{i}. {fonte}: ❌ INDISPONÍVEL - {status}")
            else:
                print(f"{i}. {fonte}: R${custo:.2f}/hora - {status} ✓")
        
        # Seleciona a fonte ótima
        fonte_selecionada, custo_otimo, mensagem = gestor.selecionar_fonte_otima(demanda)
        
        print(f"\n🏆 SELEÇÃO ÓTIMA: {fonte_selecionada}")
        print(f"   Custo: R${custo_otimo:.2f}/hora")
        print(f"   Status: {mensagem}")


if __name__ == "__main__":
    exemplo_uso()
