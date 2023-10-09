"""
Portuguese VATIN - NIF validator

Reference: https://gist.github.com/dreispt/024dd11c160af58268e2b44019080bbf
"""
import string

LEN_NIF = 9

def _toIntList(numstr, acceptX=0):
    """
    Converte string passada para lista de inteiros,
    eliminando todos os caracteres inválidos.
    Recebe string com nmero a converter.
    Segundo parÃ¢metro indica se 'X' e 'x' devem ser
    convertidos para '10' ou não.
    """
    res = []

    # converter todos os dígitos
    for i in numstr:
        if i in string.digits:
            res.append(int(i))
    return res

def controlNIF(nif):
    """
    Verifica validade de número de contribuinte.
    Recebe string com NIF.
    """

    # verificar tamanho do número passado
    if len(nif) != LEN_NIF:
        return False

    # verificar validade do carácter inicial do NIF
    if nif[0] not in "125689":
        return False

    # verificar validade
    return _valN(nif)

def _valN(num):
    """
    Algoritmo para verificar validade de NBI e NIF.
    Recebe string com número a validar.
    """

    # converter num (string) para lista de inteiros
    num = _toIntList(num)

    # computar soma de controlo
    sum = 0
    for pos, dig in enumerate(num[:-1]):
        sum += dig * (9 - pos)

    # verificar soma de controlo
    return (sum % 11 and (11 - sum % 11) % 10) == num[-1]
