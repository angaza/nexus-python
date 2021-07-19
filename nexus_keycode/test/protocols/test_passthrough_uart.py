from unittest import TestCase

import nexus_keycode.protocols.passthrough_uart as uart


class TestPassthroughUart(TestCase):
    def test_passthrough_uart__expected_value_returned(self):
        """ Test standard input into passthrough_uart and check
            output"""
        # 'input_bytes' is actually the 'base key' we are deriving
        # the uart security key from
        input_bytes = "\x01" * 14 + "\x43\x51"
        uart_security_key = (
            "\x12\xe4\x87\x62\x5c\x6b\x88\xf4\x1e\xe4\x0b\x16\xb4\xc9\x84\xf2"
        )
        result = uart.compute_uart_security_key(input_bytes)
        self.assertEqual(result, uart_security_key)
