from unittest import TestCase

import nexus_keycode.protocols.passthrough_uart as uart


class TestPassthroughUart(TestCase):
    def test_passthrough_uart__expected_value_returned(self):
        """ Test standard input into passthrough_uart and check
            output"""
        input_bytes = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
        uart_security_key = (
            "\x38\x79\x2f\xfc\x24\x1c\x2b\xc7\xc8\xcb\xf6\x24\x59\x3b\x57\x63"
        )
        result = uart.compute_uart_security_key(input_bytes)
        self.assertEqual(result, uart_security_key)
