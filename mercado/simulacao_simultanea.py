"""
Simulação Simultânea do Mercado de Energia P2P.

Todas as microrredes rodam ao mesmo tempo, minuto a minuto.
Se uma MG precisa de energia, compra de outra — a vendedora pode ligar
geradores para suprir, impactando seu consumo de combustível.

Após o dia, roda-se otimização de deslize de cargas e seleção de geradores.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
import json
import copy

from models.Microrrede import Microrrede
from models.schemas import MicrorredeSchema
from Tools.GerarCurvaCarga import CurvaCarga
from Tools.Bateria.Ferramentas_bateria import gerenciar_bateria
from Tools.Biogas.Ferramentas_biogas import Geracao_biogas_instantanea
from Tools.Diesel.Ferramentas_diesel import Consumo_diesel
from Tools.Biogas.Ferramentas_biogas import Consumo_biogas
from Tools.distancia import distancia_haversine
from analises.config import ConfigAnalise


# ============================================================
# Dataclasses de Resultado
# ============================================================

@dataclass
class TradeRecord:
    """Registro de uma transação P2P no mercado."""
    periodo: int                     # minuto (0-1439)
    vendedor_nome: str
    comprador_nome: str
    energia_kw: float                # kW fornecidos ao comprador
    energia_enviada_kw: float        # kW enviados pelo vendedor (antes da perda)
    perda_kw: float                  # kW perdidos na transmissão
    distancia_km: float
    preco_kwh: float                 # preço cobrado (R$/kWh)
    valor_total: float               # R$ total pago pelo comprador
    gerador_acionado: str            # '' se usou excesso natural, 'Diesel'/'Biogas' se ligou gerador
    custo_combustivel: float         # R$ gasto pelo vendedor em combustível extra

@dataclass
class EstadoMG:
    """Estado interno de uma microrrede durante a simulação."""
    microrrede: object               # Microrrede ou MicrorredeSchema
    nome: str
    
    # Curvas de entrada
    curva_carga: np.ndarray          # kW (1440)
    curva_solar: np.ndarray          # kW (1440)
    
    # Níveis de tanque/bateria
    nivel_bateria: float = 0.0
    nivel_diesel: float = 0.0
    nivel_biogas: float = 0.0
    geracao_biogas_inst: float = 0.0 # produção de biogás por minuto
    
    # Séries temporais de resultado (preenchidas minuto a minuto)
    uso_solar: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    uso_bateria: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    uso_diesel: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    uso_biogas: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    uso_concessionaria: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    recarga_bateria: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    energia_vendida: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    energia_comprada: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    
    # Custos acumulados
    custo_solar: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    custo_bateria: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    custo_diesel: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    custo_biogas: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    custo_concessionaria: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    receita_vendas: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    gasto_compras: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    
    # Histórico de níveis
    hist_nivel_bateria: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    hist_nivel_diesel: np.ndarray = field(default_factory=lambda: np.zeros(1440))
    hist_nivel_biogas: np.ndarray = field(default_factory=lambda: np.zeros(1440))


@dataclass
class ResultadoSimulacao:
    """Resultado completo da simulação do dia."""
    estados: Dict[str, EstadoMG]
    trades: List[TradeRecord]
    
    # Resumo financeiro por MG
    custo_total_por_mg: Dict[str, float] = field(default_factory=dict)
    custo_isolado_por_mg: Dict[str, float] = field(default_factory=dict)
    receita_por_mg: Dict[str, float] = field(default_factory=dict)
    gasto_compras_por_mg: Dict[str, float] = field(default_factory=dict)
    economia_por_mg: Dict[str, float] = field(default_factory=dict)
    economia_total: float = 0.0
    volume_total_kwh: float = 0.0
    perdas_totais_kwh: float = 0.0
    num_transacoes: int = 0


# ============================================================
# Simulador Principal
# ============================================================

class SimuladorMercado:
    """
    Motor de simulação simultânea de microrredes com mercado P2P.
    
    Fluxo:
    1. Inicializa estado de cada MG (curva de carga, solar, níveis)
    2. Para cada minuto (0..1439):
       a) Cada MG usa fontes em cascata: Solar → Bateria → local
       b) Calcula excesso/déficit
       c) Matching P2P: compradores compram de vendedores
       d) Se vendedor não tem excesso suficiente, liga gerador
       e) Residual vai para concessionária
    3. Consolida resultados
    """
    
    def __init__(self, microrredes: List, config: ConfigAnalise, 
                 margem_venda: float = 0.05, coef_perda_km: float = 0.004):
        self.microrredes = microrredes
        self.config = config
        self.margem_venda = margem_venda
        self.coef_perda_km = coef_perda_km
        self.trades: List[TradeRecord] = []
        self.cache_distancias: Dict[Tuple[str, str], float] = {}
        
    def _inicializar_estado(self, mg) -> EstadoMG:
        """Cria o estado inicial de uma microrrede."""
        nome = f"Microrrede: {mg.nome}"
        
        # Curva de carga
        if mg.carga:
            curva_carga = np.array(CurvaCarga(mg.carga), dtype=float)
        else:
            curva_carga = np.zeros(1440)
        
        # Curva solar
        curva_solar = np.zeros(1440)
        if mg.solar and self.config.fonte_disponivel('Solar', mg):
            if isinstance(mg.solar.curva_geracao, str):
                curva_solar_raw = json.loads(mg.solar.curva_geracao)
            else:
                curva_solar_raw = mg.solar.curva_geracao
            curva_solar = np.array([min(float(v), mg.solar.potencia) for v in curva_solar_raw])
        
        # Níveis iniciais
        nivel_bateria = 0.0
        if mg.bateria and self.config.fonte_disponivel('Bateria', mg):
            nivel_bateria = mg.bateria.capacidade
        
        nivel_diesel = 0.0
        if mg.diesel and self.config.fonte_disponivel('Diesel', mg):
            nivel_diesel = mg.diesel.tanque
            
        nivel_biogas = 0.0
        geracao_biogas = 0.0
        if mg.biogas and self.config.fonte_disponivel('Biogas', mg):
            nivel_biogas = mg.biogas.tanque
            geracao_biogas = Geracao_biogas_instantanea(mg.biogas)
        
        estado = EstadoMG(
            microrrede=mg,
            nome=nome,
            curva_carga=curva_carga,
            curva_solar=curva_solar,
            nivel_bateria=nivel_bateria,
            nivel_diesel=nivel_diesel,
            nivel_biogas=nivel_biogas,
            geracao_biogas_inst=geracao_biogas,
            uso_solar=np.zeros(1440),
            uso_bateria=np.zeros(1440),
            uso_diesel=np.zeros(1440),
            uso_biogas=np.zeros(1440),
            uso_concessionaria=np.zeros(1440),
            recarga_bateria=np.zeros(1440),
            energia_vendida=np.zeros(1440),
            energia_comprada=np.zeros(1440),
            custo_solar=np.zeros(1440),
            custo_bateria=np.zeros(1440),
            custo_diesel=np.zeros(1440),
            custo_biogas=np.zeros(1440),
            custo_concessionaria=np.zeros(1440),
            receita_vendas=np.zeros(1440),
            gasto_compras=np.zeros(1440),
            hist_nivel_bateria=np.zeros(1440),
            hist_nivel_diesel=np.zeros(1440),
            hist_nivel_biogas=np.zeros(1440),
        )
        return estado
        
    def _calcular_distancia(self, mg1, mg2) -> float:
        """Distância em km entre duas microrredes."""
        n1, n2 = f"Microrrede: {mg1.nome}", f"Microrrede: {mg2.nome}"
        if n1 == n2:
            return 0.0
        key = tuple(sorted([n1, n2]))
        if key in self.cache_distancias:
            return self.cache_distancias[key]
        try:
            dist = distancia_haversine(
                float(mg1.coordenada_x), float(mg1.coordenada_y),
                float(mg2.coordenada_x), float(mg2.coordenada_y)
            )
        except (ValueError, TypeError, AttributeError):
            dist = 0.0
        self.cache_distancias[key] = dist
        return dist
    
    def _custo_medio_mg(self, estado: EstadoMG) -> float:
        """Calcula o custo médio ponderado das fontes da MG neste momento."""
        mg = estado.microrrede
        custos = []
        if mg.solar and self.config.fonte_disponivel('Solar', mg):
            custos.append(mg.solar.custo_kwh)
        if mg.bateria and self.config.fonte_disponivel('Bateria', mg):
            custos.append(mg.bateria.custo_kwh)
        if mg.diesel and self.config.fonte_disponivel('Diesel', mg):
            custos.append(mg.diesel.custo_por_kWh)
        if mg.biogas and self.config.fonte_disponivel('Biogas', mg):
            custos.append(mg.biogas.custo_por_kWh)
        return min(custos) if custos else 0.0
    
    def _despacho_local(self, estado: EstadoMG, t: int) -> float:
        """
        Despacha fontes locais em cascata para atender a demanda da MG no minuto t.
        Retorna o déficit residual (kW) que ainda precisa ser suprido.
        """
        mg = estado.microrrede
        carga = estado.curva_carga[t]
        restante = carga
        
        # Produção de biogás (regenera o tanque)
        if mg.biogas and self.config.fonte_disponivel('Biogas', mg):
            if estado.nivel_biogas < mg.biogas.tanque:
                estado.nivel_biogas += estado.geracao_biogas_inst
                estado.nivel_biogas = min(estado.nivel_biogas, mg.biogas.tanque)
        
        if restante <= 0:
            estado.hist_nivel_bateria[t] = estado.nivel_bateria
            estado.hist_nivel_diesel[t] = estado.nivel_diesel
            estado.hist_nivel_biogas[t] = estado.nivel_biogas
            return 0.0
        
        # Obtém fontes ordenadas por custo
        fontes_ordenadas = self.config.fontes_ordenadas_por_custo(mg)
        
        for fonte_nome, custo in fontes_ordenadas:
            if restante <= 0.001:
                break
                
            if fonte_nome == 'Solar' and mg.solar:
                solar_disp = estado.curva_solar[t]
                uso = min(solar_disp, restante)
                estado.uso_solar[t] = uso
                estado.custo_solar[t] = uso * mg.solar.custo_kwh / 60
                restante -= uso
                
                # Excesso solar carrega bateria
                if mg.bateria and self.config.fonte_disponivel('Bateria', mg):
                    excesso_solar = solar_disp - uso
                    if excesso_solar > 0:
                        estado.nivel_bateria, _, energia_arm, _, _ = gerenciar_bateria(
                            estado.nivel_bateria, mg.bateria, geracao_excedente_kw=excesso_solar
                        )
                        estado.recarga_bateria[t] = energia_arm
                        
            elif fonte_nome == 'Bateria' and mg.bateria:
                estado.nivel_bateria, energia_fornecida, _, _, _ = gerenciar_bateria(
                    estado.nivel_bateria, mg.bateria, carga_solicitada_kw=restante
                )
                estado.uso_bateria[t] = energia_fornecida
                estado.custo_bateria[t] = energia_fornecida * mg.bateria.custo_kwh / 60
                restante -= energia_fornecida
                
            elif fonte_nome == 'Diesel' and mg.diesel:
                if estado.nivel_diesel > 0:
                    uso = min(mg.diesel.potencia, restante)
                    estado.uso_diesel[t] = uso
                    estado.custo_diesel[t] = uso * mg.diesel.custo_por_kWh / 60
                    _, estado.nivel_diesel, _ = Consumo_diesel(estado.nivel_diesel, uso, mg.diesel)
                    restante -= uso
                    
            elif fonte_nome == 'Biogas' and mg.biogas:
                if estado.nivel_biogas > 0:
                    uso = min(mg.biogas.potencia, restante)
                    estado.uso_biogas[t] = uso
                    estado.custo_biogas[t] = uso * mg.biogas.custo_por_kWh / 60
                    _, estado.nivel_biogas, _ = Consumo_biogas(estado.nivel_biogas, uso, mg.biogas)
                    restante -= uso
        
        # Gravar históricos de nível
        estado.hist_nivel_bateria[t] = estado.nivel_bateria
        estado.hist_nivel_diesel[t] = estado.nivel_diesel
        estado.hist_nivel_biogas[t] = estado.nivel_biogas
        
        return max(0.0, restante)
    
    def _excesso_disponivel(self, estado: EstadoMG, t: int) -> float:
        """
        Calcula o excesso de energia disponível para venda neste minuto.
        Excesso = geração solar que sobrou (não usada e não armazenada na bateria).
        """
        mg = estado.microrrede
        if not mg.solar or not self.config.fonte_disponivel('Solar', mg):
            return 0.0
        excesso = estado.curva_solar[t] - estado.uso_solar[t] - estado.recarga_bateria[t]
        return max(0.0, excesso)
    
    def _capacidade_extra_geradores(self, estado: EstadoMG, t: int) -> List[Tuple[str, float, float]]:
        """
        Retorna a capacidade extra de geração que pode ser ligada para venda.
        Returns: lista de (tipo_gerador, kW_disponível, custo_kwh)
        """
        mg = estado.microrrede
        extras = []
        
        # Diesel: potência máxima - uso atual
        if mg.diesel and self.config.fonte_disponivel('Diesel', mg) and estado.nivel_diesel > 0:
            uso_atual = estado.uso_diesel[t]
            disponivel = mg.diesel.potencia - uso_atual
            if disponivel > 0.1:
                extras.append(('Diesel', disponivel, mg.diesel.custo_por_kWh))
        
        # Biogás: potência máxima - uso atual
        if mg.biogas and self.config.fonte_disponivel('Biogas', mg) and estado.nivel_biogas > 0:
            uso_atual = estado.uso_biogas[t]
            disponivel = mg.biogas.potencia - uso_atual
            if disponivel > 0.1:
                extras.append(('Biogas', disponivel, mg.biogas.custo_por_kWh))
        
        # Ordenar por custo (mais barato primeiro)
        extras.sort(key=lambda x: x[2])
        return extras
    
    def _matching_mercado(self, estados: Dict[str, EstadoMG], deficits: Dict[str, float], t: int):
        """
        Faz o matching P2P: MGs com déficit compram de MGs com excesso.
        Se não há excesso natural suficiente, vendedora liga geradores.
        """
        if not deficits:
            return
        
        # Lista de compradores ordenados pelo déficit (maior primeiro)
        compradores = sorted(deficits.items(), key=lambda x: x[1], reverse=True)
        
        for comp_nome, deficit in compradores:
            if deficit <= 0.001:
                continue
                
            estado_comp = estados[comp_nome]
            mg_comp = estado_comp.microrrede
            tarifa_rede = mg_comp.concessionaria.tarifa if mg_comp.concessionaria else float('inf')
            falta = deficit
            
            # Busca ofertas de todas as outras MGs
            ofertas = []
            for vend_nome, estado_vend in estados.items():
                if vend_nome == comp_nome:
                    continue
                
                mg_vend = estado_vend.microrrede
                dist = self._calcular_distancia(mg_comp, mg_vend)
                perda = min(dist * self.coef_perda_km, 0.99)
                
                # 1) Excesso natural (solar que sobrou)
                excesso_natural = self._excesso_disponivel(estado_vend, t)
                
                # 2) Capacidade extra de geradores
                extras = self._capacidade_extra_geradores(estado_vend, t)
                
                # Ofertas do excesso natural
                if excesso_natural > 0.1:
                    custo_base = self._custo_medio_mg(estado_vend)
                    preco = custo_base * (1 + self.margem_venda)
                    preco_efetivo = preco / (1 - perda) if perda < 1 else float('inf')
                    
                    if preco_efetivo < tarifa_rede:
                        ofertas.append({
                            'vendedor': vend_nome,
                            'tipo': 'excesso',
                            'gerador': '',
                            'kw_disp': excesso_natural,
                            'custo_base': custo_base,
                            'preco': preco,
                            'preco_efetivo': preco_efetivo,
                            'dist': dist,
                            'perda': perda,
                        })
                
                # Ofertas de geradores extras
                for tipo_ger, kw_disp, custo_ger in extras:
                    preco = custo_ger * (1 + self.margem_venda)
                    preco_efetivo = preco / (1 - perda) if perda < 1 else float('inf')
                    
                    if preco_efetivo < tarifa_rede:
                        ofertas.append({
                            'vendedor': vend_nome,
                            'tipo': 'gerador',
                            'gerador': tipo_ger,
                            'kw_disp': kw_disp,
                            'custo_base': custo_ger,
                            'preco': preco,
                            'preco_efetivo': preco_efetivo,
                            'dist': dist,
                            'perda': perda,
                        })
            
            # Ordena pelo preço efetivo mais barato
            ofertas.sort(key=lambda x: x['preco_efetivo'])
            
            # Executa trades
            for oferta in ofertas:
                if falta <= 0.001:
                    break
                if oferta['kw_disp'] <= 0.001:
                    continue
                    
                # Quanto o vendedor precisa enviar para o comprador receber `falta` kW
                enviar_necessario = falta / (1 - oferta['perda']) if oferta['perda'] < 1 else falta
                enviar = min(enviar_necessario, oferta['kw_disp'])
                receber = enviar * (1 - oferta['perda'])
                
                vend_nome = oferta['vendedor']
                estado_vend = estados[vend_nome]
                mg_vend = estado_vend.microrrede
                
                # Calcular custo de combustível (se ligou gerador)
                custo_combustivel = 0.0
                if oferta['tipo'] == 'gerador':
                    custo_combustivel = enviar * oferta['custo_base'] / 60
                    
                    # Impacta o tanque do vendedor
                    if oferta['gerador'] == 'Diesel' and mg_vend.diesel:
                        estado_vend.uso_diesel[t] += enviar
                        estado_vend.custo_diesel[t] += custo_combustivel
                        _, estado_vend.nivel_diesel, _ = Consumo_diesel(
                            estado_vend.nivel_diesel, enviar, mg_vend.diesel
                        )
                        estado_vend.hist_nivel_diesel[t] = estado_vend.nivel_diesel
                    elif oferta['gerador'] == 'Biogas' and mg_vend.biogas:
                        estado_vend.uso_biogas[t] += enviar
                        estado_vend.custo_biogas[t] += custo_combustivel
                        _, estado_vend.nivel_biogas, _ = Consumo_biogas(
                            estado_vend.nivel_biogas, enviar, mg_vend.biogas
                        )
                        estado_vend.hist_nivel_biogas[t] = estado_vend.nivel_biogas
                elif oferta['tipo'] == 'excesso':
                    # O excesso natural vendido vem da geração Solar
                    estado_vend.uso_solar[t] += enviar
                    if mg_vend.solar:
                        estado_vend.custo_solar[t] += enviar * mg_vend.solar.custo_kwh / 60
                
                # Valor pago pelo comprador
                valor_pago = enviar * oferta['preco'] / 60  # R$ neste minuto
                
                # Registrar trade
                perda_kw = enviar - receber
                trade = TradeRecord(
                    periodo=t,
                    vendedor_nome=vend_nome,
                    comprador_nome=comp_nome,
                    energia_kw=receber,
                    energia_enviada_kw=enviar,
                    perda_kw=perda_kw,
                    distancia_km=oferta['dist'],
                    preco_kwh=oferta['preco'],
                    valor_total=valor_pago,
                    gerador_acionado=oferta['gerador'],
                    custo_combustivel=custo_combustivel,
                )
                self.trades.append(trade)
                
                # Atualizar estados
                estado_vend.energia_vendida[t] += enviar
                estado_vend.receita_vendas[t] += valor_pago
                estado_comp.energia_comprada[t] += receber
                estado_comp.gasto_compras[t] += valor_pago
                
                # Reduzir disponibilidade da oferta
                oferta['kw_disp'] -= enviar
                falta -= receber
            
            # Residual vai para concessionária
            if falta > 0.001 and mg_comp.concessionaria:
                estado_comp.uso_concessionaria[t] += falta
                estado_comp.custo_concessionaria[t] += falta * mg_comp.concessionaria.tarifa / 60
    
    def simular(self, callback=None) -> ResultadoSimulacao:
        """
        Executa a simulação do dia inteiro (1440 minutos).
        
        Args:
            callback: função(t, total) chamada a cada minuto para progresso
            
        Returns:
            ResultadoSimulacao completo
        """
        # 1. Inicializar estados
        estados: Dict[str, EstadoMG] = {}
        for mg in self.microrredes:
            estado = self._inicializar_estado(mg)
            estados[estado.nome] = estado
        
        # 2. Simular minuto a minuto
        for t in range(1440):
            deficits = {}
            
            # a) Despacho local de cada MG
            for nome, estado in estados.items():
                deficit = self._despacho_local(estado, t)
                if deficit > 0.001:
                    deficits[nome] = deficit
            
            # b) Matching de mercado
            self._matching_mercado(estados, deficits, t)
            
            # c) Progresso
            if callback and t % 60 == 0:
                callback(t, 1440)
        
        # 3. Consolidar
        return self._consolidar(estados)
    
    def _consolidar(self, estados: Dict[str, EstadoMG]) -> ResultadoSimulacao:
        """Consolida os resultados da simulação."""
        custo_total = {}
        custo_isolado = {}
        receita = {}
        gasto_compras = {}
        
        for nome, est in estados.items():
            mg = est.microrrede
            
            # Custo total = custos internos + compras - vendas + concessionária
            c_interno = (est.custo_solar.sum() + est.custo_bateria.sum() + 
                        est.custo_diesel.sum() + est.custo_biogas.sum())
            c_conc = est.custo_concessionaria.sum()
            c_compras = est.gasto_compras.sum()
            r_vendas = est.receita_vendas.sum()
            
            custo_total[nome] = c_interno + c_conc + c_compras - r_vendas
            receita[nome] = r_vendas
            gasto_compras[nome] = c_compras
            
            # Custo isolado = como se toda a energia viesse de fontes internas + concessionária
            # (é o cenário sem mercado — o que a concessionária teria que suprir
            #  é o déficit original + o que o mercado supriu)
            energia_comprada_total = est.energia_comprada.sum()
            tarifa = mg.concessionaria.tarifa if mg.concessionaria else 0
            custo_conc_isolado = (est.uso_concessionaria.sum() + energia_comprada_total) * tarifa / 60
            custo_isolado[nome] = c_interno + custo_conc_isolado
        
        economia = {n: custo_isolado[n] - custo_total[n] for n in estados}
        
        vol_kwh = sum(t.energia_enviada_kw / 60 for t in self.trades)
        perdas_kwh = sum(t.perda_kw / 60 for t in self.trades)
        
        return ResultadoSimulacao(
            estados=estados,
            trades=self.trades,
            custo_total_por_mg=custo_total,
            custo_isolado_por_mg=custo_isolado,
            receita_por_mg=receita,
            gasto_compras_por_mg=gasto_compras,
            economia_por_mg=economia,
            economia_total=sum(economia.values()),
            volume_total_kwh=vol_kwh,
            perdas_totais_kwh=perdas_kwh,
            num_transacoes=len(self.trades),
        )


# ============================================================
# Otimizador Pós-Dia
# ============================================================

class OtimizadorPosDia:
    """
    Após a simulação do dia, otimiza:
    1. Deslize de cargas flexíveis (prioridade 2 e 4) para horários mais baratos
    2. Seleção otimizada de geradores
    
    Re-simula o dia com os ajustes e retorna comparação antes/depois.
    """
    
    def __init__(self, microrredes: List, config: ConfigAnalise,
                 margem_venda: float = 0.05, coef_perda_km: float = 0.004):
        self.microrredes = microrredes
        self.config = config
        self.margem_venda = margem_venda
        self.coef_perda_km = coef_perda_km
    
    def _copiar_microrredes(self) -> List:
        """Cria cópias Pydantic das microrredes para manipulação."""
        copias = []
        for mg in self.microrredes:
            schema = MicrorredeSchema.model_validate(mg)
            copias.append(schema)
        return copias
    
    def _custo_instantaneo_simulacao(self, resultado: ResultadoSimulacao) -> np.ndarray:
        """Calcula o custo total instantâneo (por minuto) de todo o mercado."""
        custo_inst = np.zeros(1440)
        for nome, est in resultado.estados.items():
            custo_inst += (est.custo_solar + est.custo_bateria + est.custo_diesel + 
                          est.custo_biogas + est.custo_concessionaria + 
                          est.gasto_compras - est.receita_vendas)
        return custo_inst
    
    def otimizar(self, resultado_original: ResultadoSimulacao, callback=None) -> Dict:
        """
        Executa a otimização pós-dia.
        
        Returns:
            Dict com 'original', 'otimizado', 'microrredes_otimizadas', 'cargas_movidas'
        """
        # 1. Copiar microrredes
        mgs_otimizadas = self._copiar_microrredes()
        
        # 2. Obter custo instantâneo original
        custo_inst_original = self._custo_instantaneo_simulacao(resultado_original)
        
        # 3. Deslize de cargas
        cargas_movidas = []
        
        for mg in mgs_otimizadas:
            if not mg.carga:
                continue
            cargas_flex = [c for c in mg.carga.cargaFixa if c.prioridade in [2, 4]]
            
            for carga in cargas_flex:
                duracao = carga.tempo_desliga - carga.tempo_liga
                if duracao <= 0:
                    continue
                
                inicio_original = carga.tempo_liga
                melhor_inicio = inicio_original
                
                # Simula com a posição atual para ter baseline
                sim_atual = SimuladorMercado(mgs_otimizadas, self.config, 
                                           self.margem_venda, self.coef_perda_km)
                res_atual = sim_atual.simular()
                menor_custo = sum(res_atual.custo_total_por_mg.values())
                
                # Testa cada possível início (de 30 em 30 min para performance)
                for inicio in range(0, 1440 - duracao + 1, 30):
                    carga.tempo_liga = inicio
                    carga.tempo_desliga = inicio + duracao
                    
                    sim_teste = SimuladorMercado(mgs_otimizadas, self.config,
                                               self.margem_venda, self.coef_perda_km)
                    res_teste = sim_teste.simular()
                    custo_teste = sum(res_teste.custo_total_por_mg.values())
                    
                    if custo_teste < menor_custo:
                        menor_custo = custo_teste
                        melhor_inicio = inicio
                
                # Aplica o melhor horário
                carga.tempo_liga = melhor_inicio
                carga.tempo_desliga = melhor_inicio + duracao
                
                if melhor_inicio != inicio_original:
                    cargas_movidas.append({
                        'microrrede': str(mg.nome),
                        'carga': carga.nome,
                        'de': f"{inicio_original//60:02d}:{inicio_original%60:02d}",
                        'para': f"{melhor_inicio//60:02d}:{melhor_inicio%60:02d}",
                        'duracao_min': duracao,
                    })
                    
                if callback:
                    callback(f"Otimizando: {mg.nome} - {carga.nome}")
        
        # 4. Re-simula com as cargas otimizadas
        sim_final = SimuladorMercado(mgs_otimizadas, self.config,
                                    self.margem_venda, self.coef_perda_km)
        resultado_otimizado = sim_final.simular()
        
        return {
            'original': resultado_original,
            'otimizado': resultado_otimizado,
            'microrredes_otimizadas': mgs_otimizadas,
            'cargas_movidas': cargas_movidas,
        }

class OtimizadorMILPPosDia:
    """
    Otimizador que usa MILP para encontrar os melhores horários de cargas flexíveis
    em cada microrrede individualmente (matematicamente ótimo), e depois re-simula 
    o mercado com os horários ótimos encontrados.
    """
    
    def __init__(self, microrredes: List, config: ConfigAnalise,
                 margem_venda: float = 0.05, coef_perda_km: float = 0.004):
        self.microrredes = microrredes
        self.config = config
        self.margem_venda = margem_venda
        self.coef_perda_km = coef_perda_km
    
    def _copiar_microrredes(self) -> List:
        copias = []
        for mg in self.microrredes:
            schema = MicrorredeSchema.model_validate(mg)
            copias.append(schema)
        return copias
        
    def otimizar(self, resultado_original: ResultadoSimulacao, callback=None) -> Dict:
        from otmizadores.milp_controle_microrrede import MILPMicrorredes_ComDeslizamento
        mgs_otimizadas = self._copiar_microrredes()
        cargas_movidas = []
        
        for mg in mgs_otimizadas:
            if not mg.carga:
                continue
                
            if callback:
                callback(f"MILP Otimizando: {mg.nome}...")
            
            # Instancia e resolve o modelo MILP para a microrrede
            otimizador = MILPMicrorredes_ComDeslizamento(mg, passo_deslizamento=15)
            otimizador.criar_modelo()
            otimizador.adicionar_restricoes()
            otimizador.adicionar_funcao_objetivo()
            
            sucesso = otimizador.resolver(verbose=False)
            
            if sucesso:
                solucao = otimizador.extrair_solucao()
                if solucao.get('Horarios_Cargas'):
                    for nome_carga, info in solucao['Horarios_Cargas'].items():
                        # Atualiza os horários das cargas
                        for carga in mg.carga.cargaFixa:
                            if carga.nome == nome_carga:
                                inicio_original = carga.tempo_liga
                                melhor_inicio = info['otimizado_inicio']
                                
                                carga.tempo_liga = melhor_inicio
                                carga.tempo_desliga = melhor_inicio + (info['original_fim'] - info['original_inicio'])
                                
                                if melhor_inicio != inicio_original:
                                    cargas_movidas.append({
                                        'microrrede': str(mg.nome),
                                        'carga': carga.nome,
                                        'de': f"{inicio_original//60:02d}:{inicio_original%60:02d}",
                                        'para': f"{melhor_inicio//60:02d}:{melhor_inicio%60:02d}",
                                        'duracao_min': info['original_fim'] - info['original_inicio'],
                                    })
                                break

        if callback:
            callback("Re-simulando o mercado com os horários MILP...")
            
        sim_final = SimuladorMercado(mgs_otimizadas, self.config,
                                    self.margem_venda, self.coef_perda_km)
        resultado_otimizado = sim_final.simular()
        
        return {
            'original': resultado_original,
            'otimizado': resultado_otimizado,
            'microrredes_otimizadas': mgs_otimizadas,
            'cargas_movidas': cargas_movidas,
        }

