import re

def chave_ordenacao(valor):
    texto = str(valor)

    prefixo = re.search(r'^[A-Za-z]+', texto)
    numero = re.search(r'(\d+)', texto)

    prefixo = prefixo.group(0) if prefixo else texto
    numero = int(numero.group(1)) if numero else -1

    return (prefixo, numero, texto)