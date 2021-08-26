from unittest import TestCase

import nexus_keycode.protocols.channel_origin_commands as protocol


class TestChannelOriginActions(TestCase):

    def setUp(self):
        self.controller_command_count = 15
        # equivalent to authority ID 0x0102, device ID 0x2948372A4
        # last 1 truncated digit of decimal device ID is '2'
        self.accessory_nexus_id = 0x0102948372A4
        self.controller_sym_key = b'\xfe' * 8 + b'\xa2' * 8
        self.controller_nexus_id = 0x120003827145  # '5' truncated
        self.accessory_sym_key = b'\xc4\xb8@H\xcf\x04$\xa2]\xc5\xe9\xd3\xf0g@6'
        self.accessory_command_count = 312

    def test_unlink_all_accessories_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.UNLINK_ALL_ACCESSORIES.build(
                controller_command_count=self.controller_command_count,
                controller_sym_key=self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '000' obscured to '555'
        self.assertEqual(digits, '555018783')
        self.assertEqual(token.type_code, 0)
        self.assertEqual(token.body, '00')
        self.assertEqual(token.auth, '018783')

    def test_link_challenge_mode_3_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.LINK_ACCESSORY_MODE_3.build(
                controller_command_count=self.controller_command_count,
                accessory_command_count=self.accessory_command_count,
                accessory_sym_key=self.accessory_sym_key,
                controller_sym_key=self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '9707962' obscured to '0114964'
        self.assertEqual(digits, '4780123960006')
        self.assertEqual(token.type_code, 9)
        # body = auth for accessory
        self.assertEqual(token.body, '707962')
        self.assertEqual(token.auth, '960006')


class TestChannelOriginCommandToken(TestCase):
    atoken = protocol.ChannelOriginCommandToken(
        type_=protocol.OriginCommandType.UNLINK_ACCESSORY,  # 2
        body='12',
        auth='554433',
        controller_command_count=45321 # arbitrary here
    )

    def test_str__simple_token__expected_value_returned(self):
        # '212' obscured to '222'
        self.assertEqual(str(self.atoken), "222554433")

    def test_repr__simple_token__expected_snippets_present(self):
        repred = repr(self.atoken)

        self.assertIn("ChannelOriginCommandToken", repred)
        self.assertIn(repr(self.atoken.type_code), repred)
        self.assertIn(repr(self.atoken.body), repred)
        self.assertIn(repr(self.atoken.auth), repred)
        self.assertIn(repr(self.atoken.controller_command_count), repred)


    def test_to_digits__output_correct(self):
        # '212' obscured to '222'
        self.assertEqual('222554433', self.atoken.to_digits())

    def test_init__invalid_type__raises(self):
        self.assertRaises(
            TypeError,
            protocol.ChannelOriginCommandToken,
            type_=2,  # must supply valid type enum
            body='12',
            auth='554433'
        )


class TestGenericControllerActionToken(TestCase):
    def setUp(self):
        self.controller_command_count = 15
        self.controller_sym_key = b'\xfe' * 8 + b'\xa2' * 8

    def test_unlink_all_accessories__ok(self):
        token = (
            protocol.GenericControllerActionToken.unlink_all_accessories(
                self.controller_command_count,
                self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '000' obscured to '555'
        self.assertEqual(digits, '555018783')

        # Interpreted as 'command type' by the Nexus Channel module in FW.
        self.assertEqual(token.type_code, 0)

        # Command ID
        self.assertEqual(token.body, '00')

        # Origin authentication for this command
        self.assertEqual(token.auth, '018783')


class TestSpecificLinkedAccessoryToken(TestCase):
    def setUp(self):
        self.controller_command_count = 2000
        self.controller_sym_key = b'\x00' * 8 + b'\x17' * 8
        self.accessory_nexus_id = 0x120003827125  # truncated ID '3'

    def test_unlink_specific_accessory_ok(self):
        token = (
            protocol.SpecificLinkedAccessoryToken.unlink_specific_accessory(
                self.accessory_nexus_id,
                self.controller_command_count,
                self.controller_sym_key,
            )
        )
        digits = token.to_digits()
        # '23' obscured to '98'
        self.assertEqual(digits, '98228427')

        # Interpreted as 'command type' by the Nexus Channel module in FW.
        self.assertEqual(token.type_code, 2)

        # Truncated accessory Nexus Channel ID
        self.assertEqual(token.body, '3')

        # Origin authentication for this command
        self.assertEqual(token.auth, '228427')


class TestLinkCommandToken(TestCase):
    def setUp(self):
        self.accessory_sym_key = b'\xc4\xb8@H\xcf\x04$\xa2]\xc5\xe9\xd3\xf0g@6'
        self.controller_sym_key = b'\xfe' * 8 + b'\xa2' * 8
        self.controller_command_count = 15
        self.accessory_command_count = 2

    def test_challenge_mode_3__ok(self):
        token = protocol.LinkCommandToken.challenge_mode_3(
            controller_command_count=self.controller_command_count,
            accessory_command_count=self.accessory_command_count,
            accessory_sym_key=self.accessory_sym_key,
            controller_sym_key=self.controller_sym_key)

        digits = token.to_digits()
        # '9382847' obscured to '6815536'
        self.assertEqual(digits, '6815536632688')

        # Interpreted as 'command type' by the Nexus Channel module in FW.
        self.assertEqual(token.type_code, 9)

        # challenge result
        self.assertEqual(token.body, '382847')

        # Origin Nexus Channel module rejects token if this check doesn't match
        # Required for Angaza keycode implementation, since 'passthrough'
        # messages don't perform authentication/validation on contents.
        self.assertEqual(token.auth, '632688')
