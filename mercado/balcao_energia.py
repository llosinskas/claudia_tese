"""
Motor principal do Balcão de Energia (Mercado Spot P2P entre microrredes).
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np

from models.Microrrede import Microrrede
from mercado.resultado_analise import ResultadoAnalise
from mercado.matriz_energetica import MatrizEnergetica, calcular_matriz_instantanea, preco_oferta
from Tools.distancia import distancia_haversine


@dataclass
class OfertaVenda:
    """Ordem de venda (excesso de energia) no balcão."""
    microrrede: Microrrede
    periodo: int
    potencia_kw: float
    preco_kwh: float
    matriz: MatrizEnergetica


@dataclass
class OrdemCompra:
    """Ordem de compra (déficit de energia) no balcão."""
    microrrede: Microrrede
    periodo: int
    potencia_kw: float


@dataclass
class Trade:
    """Transação executada no balcão (matching)."""
    periodo: int
    vendedor: Microrrede
    comprador: Microrrede
    potencia_enviada_kw: float      # energia que saiu da MG vendedora
    potencia_recebida_kw: float     # energia que chegou na MG compradora (após perda)
    perda_kw: float                 # energia perdida na linha
    distancia_km: float             # distância entre as duas
    fator_perda: float              # percentual de perda aplicado
    preco_kwh: float                # preço original cobrado pelo vendedor
    preco_efetivo_kwh: float        # preço pago pelo comprador por kWh útil que chegou
    valor_total: float              # custo pago pelo comprador
    matriz_vendedor: MatrizEnergetica


@dataclass
class ResultadoBalcao:
    """Resultado final consolidado do Balcão."""
    trades: List[Trade]
    custo_com_balcao: Dict[str, float]
    custo_sem_balcao: Dict[str, float]
    economia_por_microrrede: Dict[str, float]
    economia_total: float
    perdas_totais_kwh: float
    volume_total_negociado: float   # em kWh
    preco_medio_mercado: float
    distancia_media_trades: float
    num_transacoes: int
    fluxo_compras: pd.DataFrame     # histórico temporal
    fluxo_vendas: pd.DataFrame
    matrizes: Dict[str, MatrizEnergetica]


class BalcaoEnergia:
    """
    Motor do mercado spot de energia P2P.
    Recebe os resultados individuais de análise e faz o matching 
    entre microrredes (compra e venda) minimizando o custo.
    Inclui prioridade por proximidade (fator de perda na distância).
    """
    
    def __init__(self, resultados: List[ResultadoAnalise], 
                 margem_venda: float = 0.05, 
                 coef_perda_km: float = 0.004):
        """
        Args:
            resultados: Lista com a saída de análise de cada MG
            margem_venda: % de lucro adicionado ao custo da matriz do vendedor
            coef_perda_km: % de perda de energia a cada km de distância
        """
        self.resultados = {str(r.microrrede): r for r in resultados}
        self.margem_venda = margem_venda
        self.coef_perda_km = coef_perda_km
        self.trades: List[Trade] = []
        self.cache_distancias: Dict[Tuple[str, str], float] = {}
        
    def _calcular_distancia(self, mg1: Microrrede, mg2: Microrrede) -> float:
        """Calcula distância em km entre duas microrredes."""
        if mg1.nome == mg2.nome:
            return 0.0
            
        key = tuple(sorted([str(mg1), str(mg2)]))
        if key in self.cache_distancias:
            return self.cache_distancias[key]
            
        # Tenta usar as coordenadas, se não tiver, assume 0
        try:
            lat1 = float(mg1.coordenada_x)
            lon1 = float(mg1.coordenada_y)
            lat2 = float(mg2.coordenada_x)
            lon2 = float(mg2.coordenada_y)
            dist = distancia_haversine(lat1, lon1, lat2, lon2)
        except (ValueError, TypeError, AttributeError):
            dist = 0.0
            
        self.cache_distancias[key] = dist
        return dist
        
    def _fator_perda(self, dist_km: float) -> float:
        """Calcula o % de perda na linha por km."""
        perda = dist_km * self.coef_perda_km
        return min(perda, 0.99) # limite de sanidade: máx 99% de perda
        
    def publicar_ofertas(self, t: int) -> Tuple[List[OfertaVenda], List[OrdemCompra]]:
        """Lê os resultados no instante t e publica os excessos (venda) e déficits (compra)."""
        ofertas = []
        demandas = []
        
        for nome, res in self.resultados.items():
            excesso = res.excesso[t]
            deficit = res.deficit[t]
            
            # MG com excesso = Oferta de Venda
            if excesso > 0:
                matriz = calcular_matriz_instantanea(res, t)
                preco = preco_oferta(res, t, self.margem_venda)
                ofertas.append(OfertaVenda(
                    microrrede=res.microrrede,
                    periodo=t,
                    potencia_kw=excesso,
                    preco_kwh=preco,
                    matriz=matriz
                ))
                
            # MG com deficit = Ordem de Compra
            if deficit > 0:
                demandas.append(OrdemCompra(
                    microrrede=res.microrrede,
                    periodo=t,
                    potencia_kw=deficit
                ))
                
        return ofertas, demandas
        
    def matching_periodo(self, t: int):
        """
        Executa o order matching num período específico t.
        Regras:
        - Para cada comprador, calcula-se o preço EFETIVO de cada oferta (ajustado pelas perdas)
        - O comprador compra do vendedor com o menor preço efetivo (que geralmente é o mais próximo e barato)
        """
        ofertas, demandas = self.publicar_ofertas(t)
        
        # Ordenar demandas pela quantidade (quem precisa mais compra primeiro - heurística simples)
        demandas.sort(key=lambda x: x.potencia_kw, reverse=True)
        
        for compra in demandas:
            comprador = compra.microrrede
            tarifa_rede = comprador.concessionaria.tarifa if comprador.concessionaria else float('inf')
            
            # Filtra ofertas com energia disponível e calcula preço efetivo
            ofertas_viaveis = []
            for oferta in ofertas:
                if oferta.potencia_kw <= 0.001 or str(oferta.microrrede) == str(comprador):
                    continue
                    
                dist_km = self._calcular_distancia(comprador, oferta.microrrede)
                perda = self._fator_perda(dist_km)
                
                # Preço efetivo: como uma parte da energia é perdida, o comprador precisa 
                # pagar por mais energia do que a que efetivamente recebe.
                # Preço Efetivo = Preço Base / (1 - Perda)
                preco_efetivo = oferta.preco_kwh / (1 - perda)
                
                # Só é viável se o preço efetivo for menor que a concessionária local
                if preco_efetivo < tarifa_rede:
                    ofertas_viaveis.append({
                        'oferta': oferta,
                        'dist_km': dist_km,
                        'perda': perda,
                        'preco_efetivo': preco_efetivo
                    })
                    
            # Ordena ofertas viáveis pelo preço efetivo (do mais barato para o mais caro)
            ofertas_viaveis.sort(key=lambda x: x['preco_efetivo'])
            
            # Executa trades até suprir a demanda ou acabarem as ofertas
            falta_receber = compra.potencia_kw
            
            for item in ofertas_viaveis:
                if falta_receber <= 0.001:
                    break
                    
                oferta = item['oferta']
                if oferta.potencia_kw <= 0.001:
                    continue
                    
                # Calcula quanta energia o vendedor pode enviar
                # Se eu preciso de 10kW e a perda é de 10%, o vendedor precisa me mandar 10 / 0.9 = 11.1kW
                energia_necessaria_enviar = falta_receber / (1 - item['perda'])
                
                # Limita pelo quanto o vendedor tem
                energia_enviada = min(energia_necessaria_enviar, oferta.potencia_kw)
                
                # Calcula energia que efetivamente chega
                energia_recebida = energia_enviada * (1 - item['perda'])
                
                # Executa
                oferta.potencia_kw -= energia_enviada
                falta_receber -= energia_recebida
                
                # Custo: cobra-se pela energia que saiu do vendedor no preço do vendedor
                valor_pago = energia_enviada * oferta.preco_kwh / 60  # custo instantâneo de 1 min
                
                trade = Trade(
                    periodo=t,
                    vendedor=oferta.microrrede,
                    comprador=comprador,
                    potencia_enviada_kw=energia_enviada,
                    potencia_recebida_kw=energia_recebida,
                    perda_kw=energia_enviada - energia_recebida,
                    distancia_km=item['dist_km'],
                    fator_perda=item['perda'],
                    preco_kwh=oferta.preco_kwh,
                    preco_efetivo_kwh=item['preco_efetivo'],
                    valor_total=valor_pago,
                    matriz_vendedor=oferta.matriz
                )
                self.trades.append(trade)
                
    def executar(self) -> ResultadoBalcao:
        """Executa o mercado para os 1440 períodos e consolida os resultados."""
        # Se os resultados não contêm os 1440 períodos, usamos o max length encontrado
        periodos = max(res.periodos for res in self.resultados.values()) if self.resultados else 1440
        
        for t in range(periodos):
            self.matching_periodo(t)
            
        return self._consolidar_resultados()
        
    def _consolidar_resultados(self) -> ResultadoBalcao:
        nomes_mg = list(self.resultados.keys())
        
        # Custos originais (baseline sem balcão)
        custo_sem_balcao = {nome: res.custo_concessionaria.sum() for nome, res in self.resultados.items()}
        # Mais custos internos de operação (bateria, diesel, solar)
        for nome, res in self.resultados.items():
            custos_internos = res.custo_solar.sum() + res.custo_bateria.sum() + res.custo_diesel.sum() + res.custo_biogas.sum()
            custo_sem_balcao[nome] += custos_internos
            
        # Custos com balcão = (Baseline Interno) + Compras de outras MGs - Vendas para outras MGs + Residual Concessionária
        custo_com_balcao = {nome: 0.0 for nome in nomes_mg}
        compras_mg = {nome: 0.0 for nome in nomes_mg}   # R$ gastos no balcão
        vendas_mg = {nome: 0.0 for nome in nomes_mg}    # R$ recebidos no balcão
        energia_recebida_mg = {nome: np.zeros(1440) for nome in nomes_mg} # kW por periodo recebido
        
        # Processar trades
        volume_total_kwh = 0.0
        perdas_totais_kwh = 0.0
        soma_precos = 0.0
        soma_distancias = 0.0
        
        df_compras = pd.DataFrame(index=range(1440), columns=nomes_mg).fillna(0.0)
        df_vendas = pd.DataFrame(index=range(1440), columns=nomes_mg).fillna(0.0)
        
        for trade in self.trades:
            vendedor = str(trade.vendedor)
            comprador = str(trade.comprador)
            t = trade.periodo
            
            # Financeiro
            vendas_mg[vendedor] += trade.valor_total
            compras_mg[comprador] += trade.valor_total
            
            # Energético
            energia_recebida_mg[comprador][t] += trade.potencia_recebida_kw
            
            # Datasets temporais
            df_vendas.at[t, vendedor] += trade.potencia_enviada_kw
            df_compras.at[t, comprador] += trade.potencia_recebida_kw
            
            # Métricas Globais
            volume_trade = trade.potencia_enviada_kw / 60
            volume_total_kwh += volume_trade
            perdas_totais_kwh += trade.perda_kw / 60
            soma_precos += trade.preco_kwh * volume_trade
            soma_distancias += trade.distancia_km
            
        # Calcular custo final de cada MG
        for nome, res in self.resultados.items():
            custos_internos = res.custo_solar.sum() + res.custo_bateria.sum() + res.custo_diesel.sum() + res.custo_biogas.sum()
            
            # A concessionária residual é: o déficit original MENOS a energia comprada no balcão
            deficit_residual = res.deficit - energia_recebida_mg[nome]
            deficit_residual = np.maximum(0, deficit_residual) # garante não-negativo
            
            custo_conc_residual = (deficit_residual * (res.microrrede.concessionaria.tarifa if res.microrrede.concessionaria else 0) / 60).sum()
            
            custo_com_balcao[nome] = custos_internos + compras_mg[nome] - vendas_mg[nome] + custo_conc_residual
            
        economia_por_mg = {nome: custo_sem_balcao[nome] - custo_com_balcao[nome] for nome in nomes_mg}
        economia_total = sum(economia_por_mg.values())
        
        preco_medio = soma_precos / volume_total_kwh if volume_total_kwh > 0 else 0
        dist_media = soma_distancias / len(self.trades) if self.trades else 0
        
        matrizes_acumuladas = {nome: calcular_matriz_acumulada(res) for nome, res in self.resultados.items()}
        
        return ResultadoBalcao(
            trades=self.trades,
            custo_com_balcao=custo_com_balcao,
            custo_sem_balcao=custo_sem_balcao,
            economia_por_microrrede=economia_por_mg,
            economia_total=economia_total,
            perdas_totais_kwh=perdas_totais_kwh,
            volume_total_negociado=volume_total_kwh,
            preco_medio_mercado=preco_medio,
            distancia_media_trades=dist_media,
            num_transacoes=len(self.trades),
            fluxo_compras=df_compras,
            fluxo_vendas=df_vendas,
            matrizes=matrizes_acumuladas
        )
