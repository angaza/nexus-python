import math
import sys

import bitstring
import siphash


def compute_uart_security_key(secret_key):
    """Use a given secret key to generate a UART security key
    :param secret_key: secret key used to generate UART security key
    :type secret_key: int
    """
    # use pythons default hashing algorithm to replicate already existing logic
    # present in documentation on github - split the secret key in half
    # then hash each half using the dev key (all 0s) as the key
    # then put them back together 

    key_part_a = secret_key[0:len(secret_key)//2]
    key_part_b = secret_key[len(secret_key)//2:]
    dev_key =b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    hash_part_a = siphash.SipHash_2_4(dev_key, key_part_a).hash()
    hash_part_b = siphash.SipHash_2_4(dev_key, key_part_b).hash()

    return hash_part_a + hash_part_b
