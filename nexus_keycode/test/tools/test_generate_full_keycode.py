from unittest import TestCase

import nexus_keycode.protocols.full as protocol
from nexus_keycode.tools.generate_full_keycode import (
    create_full_channel_message,
    create_full_credit_message,
)


class TestCreateFullCreditMessage(TestCase):
    def test_invalid_msg_type__raises(self):
        self.assertRaises(
            ValueError,
            create_full_credit_message,
            15,
            "INVALID_TYPE",
            b"\x12\xab" * 8,
            hours=168,
        )

    def test_valid_add_credit__returns_expected(self):
        msg = create_full_credit_message(15, "ADD", b"\x12\xab" * 8, hours=168)
        self.assertEqual(15, msg.full_id)
        self.assertEqual(protocol.FullMessageType.ADD_CREDIT, msg.message_type)
        self.assertEqual(u"*867 149 009 381 22#", msg.to_keycode())

    def test_valid_set_credit__returns_expected(self):
        msg = create_full_credit_message(15, "SET", b"\x12\xab" * 8, hours=168)
        self.assertEqual(15, msg.full_id)
        self.assertEqual(protocol.FullMessageType.SET_CREDIT, msg.message_type)
        self.assertEqual(u"*624 231 140 313 45#", msg.to_keycode())

    def test_valid_unlock__returns_expected(self):
        msg = create_full_credit_message(15, "UNLOCK", b"\x12\xab" * 8)
        self.assertEqual(15, msg.full_id)
        # 'unlock' is a special case of set credit for full protocol
        self.assertEqual(protocol.FullMessageType.SET_CREDIT, msg.message_type)
        self.assertEqual(u"*425 687 269 124 32#", msg.to_keycode())


class TestCreateFullChannelMessage(TestCase):
    def test_invalid_msg_type__raises(self):
        self.assertRaises(
            ValueError,
            create_full_channel_message,
            "INVALID_TYPE",
            b"\x12\xab" * 8,
            15,
            b"\xab\x12" * 8,
            3,
        )

    def test_valid_unlink__returns_expected(self):
        msg = create_full_channel_message("UNLINK", b"\x12\xab" * 8, 15)
        self.assertEqual(protocol.FullMessageType.PASSTHROUGH_COMMAND, msg.message_type)
        self.assertEqual(u"*815 310 472 88#", msg.to_keycode())

    def test_valid_link__returns_expected(self):
        msg = create_full_channel_message(
            "LINK", b"\x12\xab" * 8, 15, b"\xab\x12" * 8, 3
        )
        self.assertEqual(protocol.FullMessageType.PASSTHROUGH_COMMAND, msg.message_type)
        self.assertEqual(u"*819 501 596 413 845#", msg.to_keycode())

    def test_invalid_link__no_accessory_key__raises(self):
        self.assertRaises(
            ValueError,
            create_full_channel_message,
            "LINK",
            b"\x12\xab" * 8,
            15,
            accessory_command_count=3,
        )

    def test_invalid_link__no_accessory_count__raises(self):
        self.assertRaises(
            ValueError,
            create_full_channel_message,
            "LINK",
            b"\x12\xab" * 8,
            15,
            b"\xab\x12" * 8,
        )
