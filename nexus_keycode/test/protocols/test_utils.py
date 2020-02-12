from unittest import TestCase

import bitstring

from nexus_keycode.protocols.utils import pseudorandom_bits


class TestModule(TestCase):
    def test_pseudorandom_bits__varied_seeds__output_bits_are_expected(self):
        scenarios = [
            ("0b0111", "0b111010100010110"),
            ("0b0110", "0b000100001011100"),
            ("", "0b100011011100010"),
            ("0x8a91abff01", "0b000111010100001"),
            ("0x6fa", "0b0000000010111001"),
            ("0x06fa", "0b0000000010111001"),
        ]

        for (seed_bin, expected_bin) in scenarios:
            seed = bitstring.Bits(seed_bin)
            expected = bitstring.Bits(expected_bin)
            output = pseudorandom_bits(seed, expected.len)

            self.assertEqual(output, expected)
