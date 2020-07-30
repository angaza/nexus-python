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
