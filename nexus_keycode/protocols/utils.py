import math
import sys

import bitstring
import siphash


def int_to_bytes(int):
    py_ver = sys.version_info
    if py_ver < (3, 0):
        return chr(int)
    else:
        return bytes([int])


def ints_to_bytes(ints):
    py_ver = sys.version_info
    if py_ver < (3, 0):
        return "".join([chr(i) for i in ints])
    else:
        return bytes(ints)


def pseudorandom_bits(seed_bits, output_len):
    """Given some bits, compute arbitrarily many new pseudorandom bits.

    This routine provides a deterministic source of pseudorandom bits from a
    seed, which is useful in obscuring the structure of a keycode message.

    Given the same seed, the same bits will be provided in the same order on
    every call. The approach taken is a lot like key derivation in standard
    crypto: we use SipHash and apply a simplified HKDF approach akin to:

    http://tools.ietf.org/html/draft-krawczyk-hkdf-01

    :param seed_bits: arbitrary input bits
    :type seed_bits: :class:`bitstring.Bits`
    :param output_len: number of pseudorandom output bits to return
    :type output_len: `int`
    :return: deterministically computed pseudorandom bits
    :rtype: :class:`bitstring.Bits`
    """

    # prepare seed bytes
    full_seed_len = int(math.ceil(seed_bits.len / 8.0) * 8)
    pad_bits = bitstring.Bits("0b0") * (full_seed_len - seed_bits.len)
    seed = (pad_bits + seed_bits).bytes

    # compute random bits
    fixed_key = b"\x00" * 16  # arbitrary, but affects output

    def chunk(iteration):
        hash_function = siphash.SipHash_2_4(fixed_key, int_to_bytes(iteration) + seed)

        return bitstring.pack("uintle:64", hash_function.hash())

    iterations = int(math.ceil(output_len / 64.0) * 64)
    output_bits = bitstring.Bits().join(chunk(i) for i in range(iterations))

    return output_bits[:output_len]


def full_obscure(digits, sign=1, obscured_digit_count=8):
    """Given a sequence of digits (0-9), obscure their ordering.

    Assumes that the sequence of digits is at least 6 long, and the last
    6 digits are the MAC. These digits will not be perturbed.

    Uses a known set of pseudorandom bits to perform the operation
    deterministically. This does not add any security to the sequence of
    digits, but hides visually-identifiable patterns/structure within
    the sequence."""
    perturbed = list(map(int, list(digits)))

    assert len(digits) >= 6
    assert len(digits) == obscured_digit_count + 6

    # MAC digits are last 6 of perturbed, use uint32_t value as seed
    packed_check = bitstring.pack("uintle:32", int(digits[-6:]))

    # [0, 255] values; one for each body digit
    # 8 body digits, 8 bytes (8 bits each), so 64 bits of output required
    pr_bits = pseudorandom_bits(packed_check, 64)

    for (i, d) in enumerate(perturbed[:obscured_digit_count]):
        # value [0, 255]
        pr_value = pr_bits[i * 8 : (i * 8 + 8)].uint * sign
        perturbed[i] += pr_value
        perturbed[i] %= 10

    return "".join(map(str, perturbed))


def full_deobscure(digits, obscured_digit_count=8):
    """Reverse a previous `full_obscure` pass performed on `digits`."""
    return full_obscure(digits, sign=-1, obscured_digit_count=obscured_digit_count)


def generate_mac(input_val, secret_key):
    """
    :type input_val: 'byte'
    :type secret_key: 'byte'
    """
    # Mask lower 32 bits of siphash then return the last 6 digits
    function = siphash.SipHash_2_4(secret_key, input_val)
    return u"{:06d}".format(function.hash() & 0xFFFFFFFF)[-6:]
