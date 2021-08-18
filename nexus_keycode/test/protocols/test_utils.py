from unittest import TestCase

import bitstring

from nexus_keycode.protocols.utils import (
    full_deobscure,
    full_obscure,
    generate_mac,
    pseudorandom_bits
)


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

    def test_full_obscure__spec_values__ok(self):
        def assert_full_obscure_ok(message, obscured_digit_count, output):
            self.assertEqual(full_obscure(message, obscured_digit_count=obscured_digit_count), output)

        cases = [
            ["12345678901250", 8, "57458927901250"],
            ["12345678901241", 8, "05094833901241"],
            ["00000000524232", 8, "57396884524232"],
            ["00000000445755", 8, "03605158445755"],
            ["0000000793477", 7, "0043384793477"],
            ["000000693466", 6, "701319693466"],
            ["00000593455", 5, "29244593455"],
            ["0000493444", 4, "7284493444"],
            ["000393433", 3, "119393433"],
            ["00293422", 2, "45293422"],
            ["0193411", 1, "8193411"],
        ]

        for case in cases:
            assert_full_obscure_ok(*case)

    def test_full_deobscure__spec_values__ok(self):
        def assert_full_deobscure_ok(message, obscured_digit_count, output):
            self.assertEqual(full_deobscure(message, obscured_digit_count=obscured_digit_count), output)

        cases = [
            ["57458927901250", 8, "12345678901250"],
            ["05094833901241", 8, "12345678901241"],
            ["57396884524232", 8, "00000000524232"],
            ["03605158445755", 8, "00000000445755"],
            ["0043384793477", 7, "0000000793477"],
            ["701319693466", 6, "000000693466"],
            ["29244593455", 5, "00000593455"],
            ["7284493444", 4, "0000493444"],
            ["119393433", 3, "000393433"],
            ["45293422", 2, "00293422"],
            ["8193411", 1, "0193411"],
        ]

        for case in cases:
            assert_full_deobscure_ok(*case)

    def test_generate_mac__standard_input__output_expected(self):
        input_val = b"\x00"
        secret_key = b"\x38\x79\x2f\xfc\x24\x1c\x2b\xc7\xc8\xcb\xf6\x24\x59\x3b\x57\x63"
        mac = generate_mac(input_val, secret_key)

        self.assertEqual(mac, "875838")
