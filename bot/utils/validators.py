import re
from decimal import Decimal, InvalidOperation

def instagram_valid(username: str) -> bool:
    pattern = r"^[a-zA-Z_](?!.*?\.{2})[\w.]{1,28}[\w]$"
    return re.fullmatch(pattern, username) is not None

def monobank_jar_valid(url: str) -> bool:
    return url.startswith("https://send.monobank.ua/jar/") and len(url) <= 40 and len(url) >= 37

def fundraising_goal_valid(value: str) -> bool:
    try:
        num = Decimal(value)
    except InvalidOperation:
        return False

    if num <= 0:
        return False

    if abs(num.as_tuple().exponent) > 2:
        return False

    return True