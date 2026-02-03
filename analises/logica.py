

# Logica interna das microrredes 
def definir_fonte_mais_barata(fontes):
    """
    Define a fonte de energia mais barata entre as disponíveis.

    Parâmetros:
    fontes (list of dict): Lista de dicionários contendo informações das fontes de energia.
                           Cada dicionário deve ter as chaves 'nome' e 'custo_kwh'.

    Retorna:
    dict: Dicionário da fonte de energia mais barata.
    """
    if not fontes:
        return None

    #fonte_mais_barata = min(fontes, key=lambda fonte: fonte['custo_kwh'])
    fontes_ordenadas = sorted(fontes, key=lambda fonte: fonte['custo_kwh'])
    return fontes_ordenadas

def escolher_fonte_energia(demanda_kwh, fontes):
    """
    Escolhe a fonte de energia mais barata que pode suprir a demanda.

    Parâmetros:
    demanda_kwh (float): Demanda de energia em kWh.
    fontes (list of dict): Lista de dicionários contendo informações das fontes de energia.
                           Cada dicionário deve ter as chaves 'nome', 'custo_kwh' e 'capacidade_kwh'.

    Retorna:
    dict ou None: Dicionário da fonte de energia escolhida ou None se nenhuma fonte puder suprir a demanda.
    """


def define_quantidade_energia_necessaria(demanda_kwh, fonte):
    """
    Define a quantidade de energia necessária a ser fornecida por uma fonte específica.

    Parâmetros:
    demanda_kwh (float): Demanda de energia em kWh.
    fonte (dict): Dicionário contendo informações da fonte de energia.
                  Deve ter as chaves 'nome' e 'capacidade_kwh'.

    Retorna:
    float: Quantidade de energia que a fonte fornecerá (em kWh).
    """
    capacidade = fonte.get('capacidade_kwh', 0)
    if capacidade >= demanda_kwh:
        return demanda_kwh
    else:
        return capacidade