from unittest import TestCase

import bitstring

from nexus_keycode.protocols.utils import generate_mac, pseudorandom_bits


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

    def test_generate_mac__standard_input__output_expected(self):
        input_val = b"\x00"
        secret_key = b"\x38\x79\x2f\xfc\x24\x1c\x2b\xc7\xc8\xcb\xf6\x24\x59\x3b\x57\x63"
        mac = generate_mac(input_val, secret_key)

        self.assertEqual(mac, "875838")
