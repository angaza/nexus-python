import siphash

NEXUS_INTEGRITY_CHECK_FIXED_00_KEY = "\x00" * 16


def compute_uart_security_key(secret_key):
    """Use a given secret key to generate a UART security key
    :param secret_key: secret key used to generate UART security key
    :type secret_key: str
    """

    # Only 16 bit keys are accepted
    assert len(secret_key) == 16
    # Split given key in half
    key_part_a = secret_key[0 : len(secret_key) // 2]
    key_part_b = secret_key[len(secret_key) // 2 :]

    # Hash both parts of the key - digest into hex strings
    hash_part_a = siphash.SipHash_2_4(
        NEXUS_INTEGRITY_CHECK_FIXED_00_KEY, key_part_a
    ).digest()
    hash_part_b = siphash.SipHash_2_4(
        NEXUS_INTEGRITY_CHECK_FIXED_00_KEY, key_part_b
    ).digest()

    # Return hashed halves as completed uart_security_key
    return hash_part_a + hash_part_b
