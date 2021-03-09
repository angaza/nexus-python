from unittest import TestCase
import nexus_keycode.protocols.nexus_channel_origin_commands as protocol


class TestChannelOriginActions(TestCase):
    controller_command_count = 15
    # equivalent to authority ID 0x0102, device ID 0x94837158
    # last 1 truncated digit of decimal device ID are '0'
    accessory_asp_id = 0x010294837158
    controller_asp_key = b'\xfe' * 8 + b'\xa2' * 8
    controller_asp_id = 0x120003827145  # '2' truncated
    accessory_asp_key = b'\xfa' * 8 + b'\x01' * 8
    accessory_command_count = 312

    def test_unlink_all_accessories_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.UNLINK_ALL_ACCESSORIES.build(
                controller_command_count=self.controller_command_count,
                controller_sym_key=self.controller_asp_key
            )
        )
        digits = token.to_digits()
        self.assertEqual(digits, '000018783')
        self.assertEqual(token.type_code, 0)
        self.assertEqual(token.body, '00')
        self.assertEqual(token.auth, '018783')

    def test_unlock_all_accessories_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.UNLOCK_ALL_ACCESSORIES.build(
                controller_command_count=self.controller_command_count,
                controller_sym_key=self.controller_asp_key
            )
        )
        digits = token.to_digits()
        self.assertEqual(digits, '001906394')
        self.assertEqual(token.type_code, 0)
        self.assertEqual(token.body, '01')
        self.assertEqual(token.auth, '906394')

    def test_keycode_set_credit_wipe_restricted_flag__various_days_to_set__ok(self):
        token = (
            protocol.ChannelOriginAction.KEYCODE_SET_CREDIT_WIPE_RESTRICTED_FLAG.build(
                set_credit_increment_id=0,
                controller_command_count=self.controller_command_count,
                controller_sym_key=self.controller_asp_key
            )
        )
        # Requires smallpad passthrough implementation as well as exposing
        # common MAC/auth logic, so that we can:
        # 1) Compute the MAC bits
        # 2) Pass the raw bits + MAC to the smallpad passthrough message ctor
        # 3) Return the 'passthrough' command message
        self.assertRaises(
            NotImplementedError,
            token.to_digits,
        )

    def test_unlink_specific_accessory_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.UNLINK_ACCESSORY.build(
                accessory_asp_id=self.accessory_asp_id,
                controller_command_count=self.controller_command_count,
                controller_sym_key=self.controller_asp_key
            )
        )
        digits = token.to_digits()
        self.assertEqual(digits, '20536545')
        self.assertEqual(token.type_code, 2)
        self.assertEqual(token.body, '0')
        self.assertEqual(token.auth, '536545')

    def test_unlock_specific_accessory_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.UNLOCK_ACCESSORY.build(
                accessory_asp_id=self.accessory_asp_id,
                controller_command_count=self.controller_command_count,
                controller_sym_key=self.controller_asp_key
            )
        )
        digits = token.to_digits()
        self.assertEqual(digits, '10244210')
        self.assertEqual(token.type_code, 1)
        self.assertEqual(token.body, '0')
        self.assertEqual(token.auth, '244210')

    def test_link_challenge_mode_3_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.LINK_ACCESSORY_MODE_3.build(
                accessory_asp_id=self.accessory_asp_id,
                controller_command_count=self.controller_command_count,
                accessory_command_count=self.accessory_command_count,
                accessory_sym_key=self.accessory_asp_key,
                controller_sym_key=self.controller_asp_key
            )
        )
        digits = token.to_digits()
        self.assertEqual(digits, '90445034581275')
        self.assertEqual(token.type_code, 9)
        # body = truncated ASP ID + auth for accessory
        self.assertEqual(token.body, '0445034')
        self.assertEqual(token.auth, '581275')


class TestChannelOriginCommandToken(TestCase):
    atoken = protocol.ChannelOriginCommandToken(
        type_=protocol.OriginCommandType.UNLINK_ACCESSORY,  # 2
        body='12',
        auth='554433'
    )

    def test_str__simple_token__expected_value_returned(self):
        self.assertEqual(str(self.atoken), "212554433")

    def test_repr__simple_token__expected_snippets_present(self):
        repred = repr(self.atoken)

        self.assertIn("ChannelOriginCommandToken", repred)
        self.assertIn(repr(self.atoken.type_code), repred)
        self.assertIn(repr(self.atoken.body), repred)
        self.assertIn(repr(self.atoken.auth), repred)

    def test_to_digits__output_correct(self):
        self.assertEqual('212554433', self.atoken.to_digits())

    def test_init__invalid_type__raises(self):
        self.assertRaises(
            TypeError,
            protocol.ChannelOriginCommandToken,
            type_=2,  # must supply valid type enum
            body='12',
            auth='554433'
        )


class TestGenericControllerActionToken(TestCase):
    controller_command_count = 15
    controller_asp_key = b'\xfe' * 8 + b'\xa2' * 8

    def test_unlink_all_accessories__ok(self):
        token = (
            protocol.GenericControllerActionToken.unlink_all_accessories(
                self.controller_command_count,
                self.controller_asp_key
            )
        )
        digits = token.to_digits()
        self.assertEqual(digits, '000018783')

        # Interpreted as 'command type' by the ASP module in FW.
        self.assertEqual(token.type_code, 0)

        # Command ID
        self.assertEqual(token.body, '00')

        # Origin authentication for this command
        self.assertEqual(token.auth, '018783')

    def test_unlock_all_accessories__ok(self):
        token = (
            protocol.GenericControllerActionToken.unlock_all_accessories(
                self.controller_command_count,
                self.controller_asp_key
            )
        )
        digits = token.to_digits()
        self.assertEqual(digits, '001906394')

        # Interpreted as 'command type' by the ASP module in FW.
        self.assertEqual(token.type_code, 0)

        # Command ID
        self.assertEqual(token.body, '01')

        # Origin authentication for this command
        self.assertEqual(token.auth, '906394')


class TestSpecificLinkedAccessoryToken(TestCase):
    controller_command_count = 2000
    controller_asp_key = b'\x00' * 8 + b'\x17' * 8
    accessory_asp_id = 0x120003827125  # truncated ID '3'

    def test_unlink_specific_accessory_ok(self):
        token = (
            protocol.SpecificLinkedAccessoryToken.unlink_specific_accessory(
                self.accessory_asp_id,
                self.controller_command_count,
                self.controller_asp_key
            )
        )
        digits = token.to_digits()
        self.assertEqual(digits, '23228427')

        # Interpreted as 'command type' by the ASP module in FW.
        self.assertEqual(token.type_code, 2)

        # Truncated accessory ASP ID
        self.assertEqual(token.body, '3')

        # Origin authentication for this command
        self.assertEqual(token.auth, '228427')

    def test_unlock_specific_accessory_ok(self):
        token = (
            protocol.SpecificLinkedAccessoryToken.unlock_specific_accessory(
                self.accessory_asp_id,
                self.controller_command_count,
                self.controller_asp_key
            )
        )
        digits = token.to_digits()
        self.assertEqual(digits, '13046876')

        # Interpreted as 'command type' by the ASP module in FW.
        self.assertEqual(token.type_code, 1)

        # Truncated accessory ASP ID
        self.assertEqual(token.body, '3')

        # Origin authentication for this command
        self.assertEqual(token.auth, '046876')


class TestLinkCommandToken(TestCase):
    accessory_asp_key = b'\xc4\xb8@H\xcf\x04$\xa2]\xc5\xe9\xd3\xf0g@6'
    controller_asp_key = b'\xfe' * 8 + b'\xa2' * 8
    accessory_asp_id = 0x000200003322  # truncated device ID = 0
    controller_command_count = 15
    accessory_command_count = 2

    def test_challenge_mode_3__ok(self):
        token = protocol.LinkCommandToken.challenge_mode_3(
            accessory_asp_id=self.accessory_asp_id,
            controller_command_count=self.controller_command_count,
            accessory_command_count=self.accessory_command_count,
            accessory_sym_key=self.accessory_asp_key,
            controller_sym_key=self.controller_asp_key)

        digits = token.to_digits()
        self.assertEqual(digits, '90382847429307')

        # Interpreted as 'command type' by the ASP module in FW.
        self.assertEqual(token.type_code, 9)

        # Truncated accessory ASP ID + challenge result
        self.assertEqual(token.body, '0382847')

        # Origin ASP module rejects token if this check doesn't match
        # Required for Angaza keycode implementation, since 'passthrough'
        # messages don't perform authentication/validation on contents.
        self.assertEqual(token.auth, '429307')
