def sumar(data, coluna):
    total = 0
    for linha in data:
        total += linha[coluna]
    return total