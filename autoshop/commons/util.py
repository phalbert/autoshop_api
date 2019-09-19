import string
from random import choice, randint

def random_tran_id():
    min_char = 7
    max_char = 7
    allchar = string.digits
    tranid = "".join(choice(allchar) for x in range(randint(min_char, max_char)))
    return tranid

def commas(value):
    if value is not None:
        return "{:,}".format(float(value))