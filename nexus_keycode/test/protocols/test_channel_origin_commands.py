from unittest import TestCase

import nexus_keycode.protocols.channel_origin_commands as protocol


class TestChannelOriginActions(TestCase):

    def setUp(self):
        self.controller_command_count = 15
        # equivalent to authority ID 0x0102, device ID 0x94837158
        # last 1 truncated digit of decimal device ID are '0'
        self.accessory_nexus_id = 0x010294837158
        self.controller_sym_key = b'\xfe' * 8 + b'\xa2' * 8
        self.controller_nexus_id = 0x120003827145  # '2' truncated
        self.accessory_sym_key = b'\xfa' * 8 + b'\x01' * 8
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

    def test_unlock_all_accessories_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.UNLOCK_ALL_ACCESSORIES.build(
                controller_command_count=self.controller_command_count,
                controller_sym_key=self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '001' obscured to '034'
        self.assertEqual(digits, '034906394')
        self.assertEqual(token.type_code, 0)
        self.assertEqual(token.body, '01')
        self.assertEqual(token.auth, '906394')

    def test_unlink_specific_accessory_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.UNLINK_ACCESSORY.build(
                accessory_nexus_id=self.accessory_nexus_id,
                controller_command_count=self.controller_command_count,
                controller_sym_key=self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '20' obscured to '21'
        self.assertEqual(digits, '21536545')
        self.assertEqual(token.type_code, 2)
        self.assertEqual(token.body, '0')
        self.assertEqual(token.auth, '536545')

    def test_unlock_specific_accessory_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.UNLOCK_ACCESSORY.build(
                accessory_nexus_id=self.accessory_nexus_id,
                controller_command_count=self.controller_command_count,
                controller_sym_key=self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '10' obscured to '56'
        self.assertEqual(digits, '56244210')
        self.assertEqual(token.type_code, 1)
        self.assertEqual(token.body, '0')
        self.assertEqual(token.auth, '244210')

    def test_link_challenge_mode_3_builder__ok(self):
        token = (
            protocol.ChannelOriginAction.LINK_ACCESSORY_MODE_3.build(
                accessory_nexus_id=self.accessory_nexus_id,
                controller_command_count=self.controller_command_count,
                accessory_command_count=self.accessory_command_count,
                accessory_sym_key=self.accessory_sym_key,
                controller_sym_key=self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '90445034' obscured to '18591548'
        self.assertEqual(digits, '18591548581275')
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
        # '212' obscured to '222'
        self.assertEqual(str(self.atoken), "222554433")

    def test_repr__simple_token__expected_snippets_present(self):
        repred = repr(self.atoken)

        self.assertIn("ChannelOriginCommandToken", repred)
        self.assertIn(repr(self.atoken.type_code), repred)
        self.assertIn(repr(self.atoken.body), repred)
        self.assertIn(repr(self.atoken.auth), repred)

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
                self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '001' obscured to '034'
        self.assertEqual(digits, '034906394')

        # Interpreted as 'command type' by the ASP module in FW.
        self.assertEqual(token.type_code, 0)

        # Command ID
        self.assertEqual(token.body, '01')

        # Origin authentication for this command
        self.assertEqual(token.auth, '906394')


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
                self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '23' obscured to '98'
        self.assertEqual(digits, '98228427')

        # Interpreted as 'command type' by the ASP module in FW.
        self.assertEqual(token.type_code, 2)

        # Truncated accessory ASP ID
        self.assertEqual(token.body, '3')

        # Origin authentication for this command
        self.assertEqual(token.auth, '228427')

    def test_unlock_specific_accessory_ok(self):
        token = (
            protocol.SpecificLinkedAccessoryToken.unlock_specific_accessory(
                self.accessory_nexus_id,
                self.controller_command_count,
                self.controller_sym_key
            )
        )
        digits = token.to_digits()
        # '13' obscured to '62'
        self.assertEqual(digits, '62046876')

        # Interpreted as 'command type' by the ASP module in FW.
        self.assertEqual(token.type_code, 1)

        # Truncated accessory ASP ID
        self.assertEqual(token.body, '3')

        # Origin authentication for this command
        self.assertEqual(token.auth, '046876')


class TestLinkCommandToken(TestCase):
    def setUp(self):
        self.accessory_sym_key = b'\xc4\xb8@H\xcf\x04$\xa2]\xc5\xe9\xd3\xf0g@6'
        self.controller_sym_key = b'\xfe' * 8 + b'\xa2' * 8
        self.accessory_nexus_id = 0x000200003322  # truncated device ID = 0
        self.controller_command_count = 15
        self.accessory_command_count = 2

    def test_challenge_mode_3__ok(self):
        token = protocol.LinkCommandToken.challenge_mode_3(
            accessory_nexus_id=self.accessory_nexus_id,
            controller_command_count=self.controller_command_count,
            accessory_command_count=self.accessory_command_count,
            accessory_sym_key=self.accessory_sym_key,
            controller_sym_key=self.controller_sym_key)

        digits = token.to_digits()
        # '90382847' obscured to '29311191'
        self.assertEqual(digits, '29311191429307')

        # Interpreted as 'command type' by the ASP module in FW.
        self.assertEqual(token.type_code, 9)

        # Truncated accessory ASP ID + challenge result
        self.assertEqual(token.body, '0382847')

        # Origin ASP module rejects token if this check doesn't match
        # Required for Angaza keycode implementation, since 'passthrough'
        # messages don't perform authentication/validation on contents.
        self.assertEqual(token.auth, '429307')
