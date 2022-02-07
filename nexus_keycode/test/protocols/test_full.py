from unittest import TestCase
import nexus_keycode.protocols.full as protocol
from nexus_keycode.protocols.channel_origin_commands import ChannelOriginAction


class TestBaseFullMessage(TestCase):
    amessage = protocol.BaseFullMessage(
        full_id=1223,  # LSB 6 Message ID = Dec 7
        message_type=protocol.FullMessageType.ADD_CREDIT,
        body="00993",
        secret_key=b"\xab" * 16,
        is_factory=False,
    )
    fmessage = protocol.BaseFullMessage(
        full_id=0,
        message_type=protocol.FullMessageType.FACTORY_ALLOW_TEST,
        body="",
        secret_key=b"\x00" * 16,
        is_factory=True,
    )

    def test_init__long_key_inputs_accepted__uses_siphash_required_bytes(self):
        xmessage = protocol.BaseFullMessage(
            full_id=343,
            message_type=protocol.FullMessageType.ADD_CREDIT,
            body="00993",
            secret_key=b"\xfb\x00\xa5\x98" * 4,
            is_factory=False,
        )
        ymessage = protocol.BaseFullMessage(
            full_id=343,
            message_type=protocol.FullMessageType.ADD_CREDIT,
            body="00993",
            secret_key=b"\xfb\x00\xa5\x98" * 4 + b"\x02\x03\x04\x05" * 4,
            is_factory=False,
        )

        self.assertEqual(str(xmessage), str(ymessage))
        self.assertEqual(repr(xmessage), repr(ymessage))
        self.assertEqual(xmessage.to_keycode(), ymessage.to_keycode())

    def test_str__simple_message__expected_value_returned(self):
        self.assertEqual("*007 009 936 639 04#", str(self.amessage))

    def test_repr__simple_message__expected_snippets_present(self):
        repred = repr(self.amessage)

        self.assertIn("BaseFullMessage", repred)
        self.assertIn(repr(self.amessage.header), repred)
        self.assertIn(repr(self.amessage.body), repred)
        self.assertIn(repr(self.amessage.secret_key), repred)
        self.assertIn("is_factory", repred)

    def test_obscure__spec_values__ok(self):
        def assert_obscure_ok(message, output):
            self.assertEqual(protocol.BaseFullMessage.obscure(message), output)

        cases = [
            ["12345678901250", "57458927901250"],
            ["12345678901241", "05094833901241"],
            ["00000000524232", "57396884524232"],
            ["00000000445755", "03605158445755"],
        ]

        for case in cases:
            assert_obscure_ok(*case)

    def test_deobscure__spec_values__ok(self):
        def assert_deobscure_ok(message, output):
            self.assertEqual(protocol.BaseFullMessage.deobscure(message), output)

        cases = [
            ["57458927901250", "12345678901250"],
            ["05094833901241", "12345678901241"],
            ["57396884524232", "00000000524232"],
            ["03605158445755", "00000000445755"],
        ]

        for case in cases:
            assert_deobscure_ok(*case)

    def test_to_keycode__various_cases__output_correct(self):
        def assert_keycode_ok(message, prefix, suffix, sep, grlen, expected):
            generated = message.to_keycode(
                prefix=prefix, suffix=suffix, separator=sep, group_len=grlen
            )

            self.assertEqual(generated, expected)

        cases = [
            [self.amessage, "", "", "", 3, "88519055663904"],
            [self.amessage, "*", "#", "-", 3, "*885-190-556-639-04#"],
            [self.amessage, "*", "#", "-", 4, "*8851-9055-6639-04#"],
            [self.fmessage, "@", ";", "", 3, "@4064983;"],
            [self.fmessage, "*", "#", "-", 3, "*406-498-3#"],
            [self.fmessage, "*", "#", "-", 2, "*40-64-98-3#"],
        ]

        for case in cases:
            assert_keycode_ok(*case)

    def test_to_keycode__obscuring_forced__output_matches(self):
        self.assertEqual(
            self.amessage.to_keycode(prefix="", suffix="", separator="", obscured=True),
            self.amessage.to_keycode(prefix="", suffix="", separator=""),
        )
        self.assertEqual(
            self.amessage.to_keycode(
                prefix="", suffix="", separator="", obscured=False
            ),
            protocol.BaseFullMessage.deobscure(
                self.amessage.to_keycode(prefix="", suffix="", separator="")
            ),
        )


class TestFullMessage(TestCase):
    def setUp(self):
        self.secret_key = b"\xc4\xb8@H\xcf\x04$\xa2]\xc5\xe9\xd3\xf0g@6"

    def test_add_credit__ok(self):
        msg = protocol.FullMessage.add_credit(42, 24 * 7, self.secret_key)
        keycode = msg.to_keycode()

        self.assertEqual(self.secret_key, msg.secret_key)
        self.assertTrue(
            msg.header.startswith(str(protocol.FullMessageType.ADD_CREDIT.value))
        )
        self.assertEqual(msg.header, "042")

        self.assertEqual(msg.body, "00168")
        self.assertTrue(msg.body.endswith("168"))

        self.assertEqual(keycode[-6:], str(msg)[-6:])
        self.assertEqual("*186 261 012 193 03#", keycode)

    def test_add_credit__with_suffix_prefix__ok(self):
        msg = protocol.FullMessage.add_credit(42, 24 * 7, self.secret_key)
        prefix = "*"
        suffix = "#"
        keycode = msg.to_keycode(prefix=prefix, suffix=suffix, separator="")

        self.assertEqual(self.secret_key, msg.secret_key)
        self.assertTrue(
            msg.header.startswith(str(protocol.FullMessageType.ADD_CREDIT.value))
        )
        self.assertEqual(msg.header, "042")

        self.assertEqual(msg.body, "00168")
        self.assertTrue(msg.body.endswith("168"))

        self.assertEqual(keycode[-7:], str(msg)[-9:].replace(" ", ""))
        self.assertEqual(keycode, prefix + "18626101219303" + suffix)

    def test_set_credit__ok(self):
        msg = protocol.FullMessage.set_credit(242, 24 * 7, self.secret_key)
        keycode = msg.to_keycode()

        self.assertEqual(self.secret_key, msg.secret_key)
        self.assertTrue(
            msg.header.startswith(str(protocol.FullMessageType.SET_CREDIT.value))
        )
        self.assertEqual(msg.header, "150")  # LSB 242 == dec 50

        self.assertEqual(msg.body, "00168")
        self.assertTrue(msg.body.endswith("168"))

        self.assertEqual(keycode[-6:], str(msg)[-6:])
        self.assertEqual("*849 165 746 502 52#", keycode)

    def test_set_unlock__ok(self):
        msg = protocol.FullMessage.unlock(243, self.secret_key)
        keycode = msg.to_keycode()

        self.assertEqual(self.secret_key, msg.secret_key)
        self.assertTrue(
            msg.header.startswith(str(protocol.FullMessageType.SET_CREDIT.value))
        )
        self.assertEqual(msg.header, "151")

        self.assertEqual(msg.body, "99999")
        self.assertTrue(msg.body.endswith("999"))

        self.assertEqual(keycode[-6:], str(msg)[-6:])
        self.assertEqual("*594 193 807 353 96#", keycode)

    def test_reserved__raises(self):
        self.assertRaises(
            ValueError, protocol.FullMessage.reserved, 15, 10, self.secret_key
        )

    def test_wipe_state__ok(self):
        msg = protocol.FullMessage.wipe_state(
            666, protocol.FullMessageWipeFlags.TARGET_FLAGS_0, self.secret_key
        )
        keycode = msg.to_keycode()

        self.assertEqual(self.secret_key, msg.secret_key)
        self.assertTrue(
            msg.header.startswith(str(protocol.FullMessageType.WIPE_STATE.value))
        )
        self.assertEqual(msg.header, "226")  # LSB 666 = dec 26

        self.assertTrue(msg.body.startswith("0"))
        self.assertTrue(
            msg.body.endswith(str(protocol.FullMessageWipeFlags.TARGET_FLAGS_0.value))
        )
        self.assertTrue(msg.body.endswith("000"))

        self.assertEqual(keycode[-6:], str(msg)[-6:])
        self.assertEqual("*991 845 863 956 46#", keycode)

    def test_wipe_state__restricted_flag__ok(self):
        msg = protocol.FullMessage.wipe_state(
            30, protocol.FullMessageWipeFlags.WIPE_RESTRICTED_FLAG, self.secret_key
        )
        keycode = msg.to_keycode()

        self.assertEqual(self.secret_key, msg.secret_key)
        self.assertTrue(
            msg.header.startswith(str(protocol.FullMessageType.WIPE_STATE.value))
        )
        self.assertEqual(msg.header, "230")

        self.assertTrue(msg.body.startswith("0"))
        self.assertTrue(
            msg.body.endswith(
                str(protocol.FullMessageWipeFlags.WIPE_RESTRICTED_FLAG.value)
            )
        )
        self.assertTrue(msg.body.endswith("003"))

        self.assertEqual(keycode[-6:], str(msg)[-6:])
        self.assertEqual("*862 585 829 300 05#", keycode)


class TestFactoryFullMessage(TestCase):
    def setUp(self):
        self.secret_key = b"\xc4\xb8@H\xcf\x04$\xa2]\xc5\xe9\xd3\xf0g@6"

    def test_allow_test__verify_output__ok(self):
        msg = protocol.FactoryFullMessage.allow_test()
        keycode = msg.to_keycode()

        self.assertEqual(
            msg.header,
            u"{:01d}".format(protocol.FullMessageType.FACTORY_ALLOW_TEST.value),
        )
        self.assertEqual(msg.body, "")
        self.assertEqual("*406 498 3#", keycode)

    def test_oqc_test__verify_output__ok(self):
        msg = protocol.FactoryFullMessage.oqc_test()
        keycode = msg.to_keycode()

        self.assertEqual(
            msg.header,
            u"{:01d}".format(protocol.FullMessageType.FACTORY_OQC_TEST.value),
        )
        self.assertEqual(msg.body, "00060")
        self.assertEqual("*500 060 694 509#", keycode)

    def test_display_payg_id__verify_output__ok(self):
        msg = protocol.FactoryFullMessage.display_payg_id()
        keycode = msg.to_keycode()

        self.assertEqual(
            msg.header,
            u"{:01d}".format(protocol.FullMessageType.FACTORY_DISPLAY_PAYG_ID.value),
        )
        self.assertEqual(msg.body, "")
        self.assertEqual("*634 776 5#", keycode)

    def test_passthrough_channel_origin_command__link_command__result_matches(self):
        msg = protocol.FactoryFullMessage.passthrough_channel_origin_command(
            ChannelOriginAction.LINK_ACCESSORY_MODE_3,
            controller_command_count=15,
            accessory_command_count=2,
            accessory_sym_key=b'\xc4\xb8@H\xcf\x04$\xa2]\xc5\xe9\xd3\xf0g@6',
            controller_sym_key=b'\xfe' * 8 + b'\xa2' * 8
        )
        self.assertEqual(
            msg.header,
            "{:01d}".format(
                protocol.FullMessageType.PASSTHROUGH_COMMAND.value))
        # passthrough "Application ID" = 1 for Nexus Channel Origin Command
        self.assertEqual(msg.body, '16815536632688')
        # Adds leading '8' to indicate 'passthrough command'
        self.assertEqual(msg.to_keycode(), "*816 815 536 632 688#")

    def test_passthrough_command__channel_command__expected(self):
        # Send an arbitrary PAYG_UART_PASSTHROUGH message
        msg = protocol.FactoryFullMessage.passthrough_command(
            protocol.PassthroughApplicationId.TO_PAYG_UART_PASSTHROUGH,
            passthrough_digits="9238284782879",
        )
        self.assertEqual(msg.full_id, 0)
        self.assertEqual(len(msg.body), 14)
        self.assertEqual(
            msg.header,
            u"{:01d}".format(protocol.FullMessageType.PASSTHROUGH_COMMAND.value),
        )
        # passthrough "Application ID" = 0
        self.assertEqual(msg.body, "09238284782879")
        self.assertEqual(msg.to_keycode(), "*809 238 284 782 879#")

    def test_passthrough_command__body_length_error__value_error_expected(self):
        self.assertRaises(
            ValueError,
            protocol.FactoryFullMessage.passthrough_command,
            protocol.PassthroughApplicationId.TO_PAYG_UART_PASSTHROUGH,
            passthrough_digits="238284782879",
        )

    def test_passthrough_command__application_id_error__type_error_expected(self):
        self.assertRaises(
            TypeError,
            protocol.FactoryFullMessage.passthrough_command,
            2,
            passthrough_digits="09238284782879",
        )

    def test_passthrough_uart_keycode_numeric_body_and_mac__standard_input__ok(self):
        input_bytes = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
        passthrough_keycode = protocol.FactoryFullMessage.passthrough_uart_keycode_numeric_body_and_mac(input_bytes)
        self.assertEqual(passthrough_keycode.to_keycode(), u"*800 875 838#")
