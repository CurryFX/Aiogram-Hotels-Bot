"""
    This file includes optional funcs.
"""


def str_to_float(text: str) -> float:
    """
    Func for replacement ',' to '.' in the floating numbers

    :param text: floating number separated with ','
    :return: float
    """
    match = text.replace(',', '.')
    return float(match)


def is_float(number: str) -> bool:
    try:
        float(number)
    except ValueError:
        return False
    else:
        return True
